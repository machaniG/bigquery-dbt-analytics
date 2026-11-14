# GCS Landing -> Pandera Gate -> GCS Bronze pipeline

"""Process all newly arrived CSV files in GCS Landing, validate via Pandera, and land Parquet in Bronze."""

import io
import logging
import re
from datetime import datetime, timezone

import pandas as pd
import pandera.pandas as pa
from google.cloud import storage

from src.config import PipelineConfig
from src.schema import OnlineRetailBronzeSchema

LOGGER = logging.getLogger(__name__)
HIGH_UNIT_PRICE_THRESHOLD = 10.0
ANOMALY_EXAMPLE_LIMIT = 5

CANONICAL_COLUMNS = (
    "invoice",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "unit_price",
    "customer_id",
    "country",
)

COLUMN_ALIASES = {
    "invoice": {"invoice", "invoiceno"},
    "stock_code": {"stockcode"},
    "description": {"description"},
    "quantity": {"quantity"},
    "invoice_date": {"invoicedate"},
    "unit_price": {"price", "unitprice"},
    "customer_id": {"customerid"},
    "country": {"country"},
}


def preprocess_batch(batch: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Normalize source columns and cast types to match the canonical Bronze schema."""
    rename_map = {}
    for column in batch.columns:
        normalized = re.sub(r"[^a-z0-9]", "", str(column).lower())
        for canonical, aliases in COLUMN_ALIASES.items():
            if normalized in aliases:
                rename_map[column] = canonical
                break

    batch = batch.rename(columns=rename_map)

    missing = [col for col in CANONICAL_COLUMNS if col not in batch.columns]
    if missing:
        raise ValueError(f"{source_name} is missing required columns: {', '.join(missing)}")

    df = batch.loc[:, CANONICAL_COLUMNS].copy()
    df["invoice"] = df["invoice"].astype("string")
    df["stock_code"] = df["stock_code"].astype("string")
    df["description"] = df["description"].astype("string")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce", utc=True)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").astype("float64")
    df["customer_id"] = df["customer_id"].astype("string")
    df["country"] = df["country"].astype("string")
    return df


def _log_batch_anomalies(batch: pd.DataFrame, source_name: str) -> None:
    """Report unusually high prices and summarize negative values without rejecting the batch."""
    high_prices = batch.loc[batch["unit_price"] > HIGH_UNIT_PRICE_THRESHOLD]
    if not high_prices.empty:
        examples = high_prices.nlargest(ANOMALY_EXAMPLE_LIMIT, "unit_price")
        LOGGER.warning(
            "%s has %d unit_price rows above GBP %.2f. Highest examples: %s",
            source_name,
            len(high_prices),
            HIGH_UNIT_PRICE_THRESHOLD,
            examples[["invoice", "stock_code", "unit_price"]].to_dict("records"),
        )

    negative_prices = batch.loc[batch["unit_price"] < 0]
    if not negative_prices.empty:
        LOGGER.info(
            "%s has %d negative unit_price rows (retained; may be returns or adjustments).",
            source_name,
            len(negative_prices),
        )

    negative_quantities = batch.loc[batch["quantity"] < 0]
    if not negative_quantities.empty:
        LOGGER.info(
            "%s has %d negative quantity rows (retained; may be returns or cancellations).",
            source_name,
            len(negative_quantities),
        )


def _get_processed_files(client: storage.Client, bucket_name: str, prefix: str) -> set[str]:
    """Read manifest of already-ingested filenames to guarantee idempotency."""
    manifest_blob = client.bucket(bucket_name).blob(f"{prefix}/_processed_files.txt")
    if not manifest_blob.exists():
        return set()
    content = manifest_blob.download_as_text()
    return {line.strip() for line in content.splitlines() if line.strip()}


def _mark_file_processed(
    client: storage.Client, bucket_name: str, prefix: str, processed: set[str], filename: str
) -> None:
    """Append newly ingested filename to the GCS state manifest."""
    processed.add(filename)
    manifest_blob = client.bucket(bucket_name).blob(f"{prefix}/_processed_files.txt")
    manifest_blob.upload_from_string("\n".join(sorted(processed)) + "\n", content_type="text/plain")


def ingest_new_arrivals(config: PipelineConfig) -> list[str]:
    """Scan GCS Landing for any new CSVs, validate via Pandera, and write Parquet to Bronze."""
    client = storage.Client(project=config.gcp_project_id)
    landing_bucket = client.bucket(config.landing_bucket)

    blobs = sorted(
        [
            b
            for b in landing_bucket.list_blobs(prefix=f"{config.dataset_prefix}/")
            if b.name.endswith(".csv")
        ],
        key=lambda b: b.name,
    )

    processed_files = _get_processed_files(client, config.bronze_bucket, config.dataset_prefix)
    new_blobs = [b for b in blobs if b.name.split("/")[-1] not in processed_files]

    if not new_blobs:
        LOGGER.info("No new CSV arrivals in gs://%s/%s/. Pipeline up to date.", config.landing_bucket, config.dataset_prefix)
        return []

    landed_uris: list[str] = []

    for blob in new_blobs:
        filename = blob.name.split("/")[-1]
        batch_id = filename.replace(".csv", "")
        LOGGER.info("Ingesting new arrival: gs://%s/%s", config.landing_bucket, blob.name)

        # 1. Read raw CSV from Landing
        raw_df = pd.read_csv(io.BytesIO(blob.download_as_bytes()))
        clean_df = preprocess_batch(raw_df, source_name=filename)
        _log_batch_anomalies(clean_df, filename)

        # 2. Pandera validates required structure and domain constraints.
        try:
            validated_df = OnlineRetailBronzeSchema.validate(clean_df, lazy=True)
        except pa.errors.SchemaErrors as err:
            LOGGER.error("Pandera data quality gate FAILED for %s:\n%s", filename, err.failure_cases)
            raise

        # 3. Add lineage metadata
        run_at = datetime.now(timezone.utc)
        ingest_date = run_at.date().isoformat()
        validated_df["ingested_at"] = run_at
        validated_df["ingest_date"] = ingest_date
        validated_df["source_file_name"] = filename
        validated_df["batch_id"] = batch_id

        # 4. Write compressed Parquet to partitioned Bronze path
        parquet_buffer = io.BytesIO()
        validated_df.to_parquet(parquet_buffer, index=False, engine="pyarrow", compression="snappy")
        parquet_buffer.seek(0)

        target_path = f"{config.dataset_prefix}/ingest_date={ingest_date}/{batch_id}_{config.output_filename}"
        bronze_blob = client.bucket(config.bronze_bucket).blob(target_path)
        bronze_blob.upload_from_file(parquet_buffer, content_type="application/octet-stream")

        # 5. Update manifest immediately after successful Bronze landing
        _mark_file_processed(client, config.bronze_bucket, config.dataset_prefix, processed_files, filename)

        gcs_uri = f"gs://{config.bronze_bucket}/{target_path}"
        LOGGER.info("Landed %s rows -> %s", f"{len(validated_df):,}", gcs_uri)
        landed_uris.append(gcs_uri)

    return landed_uris


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    ingest_new_arrivals(PipelineConfig())
