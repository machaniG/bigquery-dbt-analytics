"""Unit and chaos tests proving schema normalization and Pandera pre-Bronze quality gates."""

import pandas as pd
import pandera.pandas as pa
import pytest

from src.ingest_gcs import _log_batch_anomalies, preprocess_batch
from src.schema import OnlineRetailBronzeSchema


@pytest.fixture
def valid_raw_batch() -> pd.DataFrame:
  """Create a realistic sample batch including C-cancellations and A-adjustments."""
  return pd.DataFrame({
      "InvoiceNo": ["536365", "C536379", "A563185", "536367", "536368"],
      "StockCode": ["85123A", "D", "B", "84879", "22752"],
      "Description": [
          "WHITE HANGING HEART T-LIGHT HOLDER",
          "Discount",
          "Adjust bad debt",
          "ASSORTED COLOUR BIRD ORNAMENT",
          "SET 7 BABUSHKA NESTING BOXES",
      ],
      "Quantity": [6, -1, 1, 32, 3],
      "InvoiceDate": [
          "2026-11-10 08:26:00",
          "2026-11-10 09:41:00",
          "2026-11-10 14:15:00",
          "2026-11-10 08:34:00",
          "2026-11-10 08:35:00",
      ],
      "Price": [2.55, 27.50, 11062.06, 1.69, 7.65],
      "Customer ID": ["17850", "14527", None, "13047", None],
      "Country": [
          "United Kingdom",
          "United Kingdom",
          "United Kingdom",
          "France",
          "Germany",
      ],
  })


def test_happy_path_preprocessing_and_pandera_pass(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Verify column alias normalization and Pandera validation pass on clean data."""
  processed = preprocess_batch(valid_raw_batch, source_name="valid_batch.csv")
  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)

  expected_core_cols = {
      "invoice",
      "stock_code",
      "description",
      "quantity",
      "invoice_date",
      "unit_price",
      "customer_id",
      "country",
  }

  assert len(validated) == 5
  # Use issubset so metadata columns (like ingested_at, batch_id) don't break the test
  assert expected_core_cols.issubset(set(validated.columns))
  assert str(validated["invoice_date"].dt.tz) == "UTC"


def test_happy_path_allows_zero_price_standard_writeoff(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Verify $0.00 damaged/write-off rows with negative quantity on standard invoices pass Bronze."""
  # Expand to 20 rows so 1 zero-price row still satisfies the >= 95% positive price ratio (19/20 = 95%)
  batch = pd.concat([valid_raw_batch] * 4, ignore_index=True)
  batch.loc[0, "InvoiceNo"] = "599999"
  batch.loc[0, "Quantity"] = -5
  batch.loc[0, "Price"] = 0.0

  processed = preprocess_batch(batch, source_name="writeoff_batch.csv")
  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)

  assert len(validated) == 20


# ==============================================================================
# CHAOS TESTS: Simulate Upstream Data Corruption & Drift
# ==============================================================================


def test_chaos_missing_required_column_raises_error(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Chaos Test 1: Upstream vendor drops 'StockCode' column -> must fail immediately."""
  corrupted = valid_raw_batch.drop(columns=["StockCode"])

  with pytest.raises(ValueError, match="missing required columns: stock_code"):
    preprocess_batch(corrupted, source_name="broken_schema.csv")


def test_negative_prices_and_quantities_are_reported_not_blocked(
    valid_raw_batch: pd.DataFrame, caplog: pytest.LogCaptureFixture
) -> None:
  """High positive prices warn; negative prices and quantities are informational only."""
  import logging

  caplog.set_level(logging.INFO)
  corrupted = valid_raw_batch.copy()
  corrupted["Price"] = [10.0, 10.01, 9.99, 1.69, 7.65]
  corrupted.loc[0, "Price"] = -53594.36
  corrupted.loc[0, "Quantity"] = -6

  processed = preprocess_batch(corrupted, source_name="negative_price.csv")
  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)
  _log_batch_anomalies(processed, "negative_price.csv")

  assert len(validated) == len(corrupted)
  assert "1 unit_price rows above GBP 10.00" in caplog.text
  assert "1 negative unit_price rows (retained" in caplog.text
  assert "2 negative quantity rows (retained" in caplog.text


def test_chaos_zero_quantity_blocked_by_pandera(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Chaos Test 3: Zero-quantity ghost transaction -> blocked by Pandera ne=0 rule."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[1, "Quantity"] = 0

  processed = preprocess_batch(corrupted, source_name="zero_qty.csv")

  with pytest.raises(pa.errors.SchemaErrors) as exc_info:
    OnlineRetailBronzeSchema.validate(processed, lazy=True)

  assert "quantity" in exc_info.value.failure_cases["column"].values


def test_zero_prices_do_not_block_ingestion(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Zero prices are retained for review rather than blocking a batch."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[[0, 1], "Price"] = 0.0

  processed = preprocess_batch(corrupted, source_name="price_drift.csv")
  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)
  assert len(validated) == len(corrupted)


@pytest.mark.parametrize(
    "bad_invoice", ["ERROR", "53636", "5363659", "X536365", "c536365"]
)
def test_chaos_malformed_invoice_regex_blocked(
    valid_raw_batch: pd.DataFrame, bad_invoice: str
) -> None:
  """Chaos Test 5: Corrupted or wrong-prefix invoice IDs -> blocked by ^[CA]?\\d{6}$ regex."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[0, "InvoiceNo"] = bad_invoice

  processed = preprocess_batch(corrupted, source_name="bad_invoice.csv")

  with pytest.raises(pa.errors.SchemaErrors) as exc_info:
    OnlineRetailBronzeSchema.validate(processed, lazy=True)

  failures = exc_info.value.failure_cases
  assert "invoice" in failures["column"].values
  assert any("str_matches" in str(c) for c in failures["check"].values)


def test_cancellation_with_positive_quantity_is_not_blocked(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Positive cancellation quantities are retained for review."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[1, "Quantity"] = 5  # Row 1 is C536379

  processed = preprocess_batch(corrupted, source_name="bad_cancellation.csv")

  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)
  assert len(validated) == len(corrupted)


def test_standard_invoice_with_negative_quantity_is_not_blocked(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Negative quantities on standard invoices are retained for review."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[0, "Quantity"] = -6  # Row 0 is 536365 with Price=2.55

  processed = preprocess_batch(corrupted, source_name="bad_standard_qty.csv")

  validated = OnlineRetailBronzeSchema.validate(processed, lazy=True)
  assert len(validated) == len(corrupted)


@pytest.mark.parametrize(
    "bad_stock,bad_cust",
    [
        ("85123A", None),  # Wrong StockCode for an A-adjustment (must be 'B')
        ("B", "17850"),  # Non-null Customer ID on an A-adjustment
    ],
)
def test_chaos_invalid_adjustment_invoice_blocked(
    valid_raw_batch: pd.DataFrame, bad_stock: str, bad_cust: str | None
) -> None:
  """Chaos Test 8: A-prefixed adjustment violates StockCode=='B' or null Customer ID -> blocked."""
  corrupted = valid_raw_batch.copy()
  corrupted.loc[2, "StockCode"] = bad_stock  # Row 2 is A563185
  corrupted.loc[2, "Customer ID"] = bad_cust

  processed = preprocess_batch(corrupted, source_name="bad_adjustment.csv")

  with pytest.raises(pa.errors.SchemaErrors) as exc_info:
    OnlineRetailBronzeSchema.validate(processed, lazy=True)

  assert (
      "check_adjustment_invoice_rules"
      in exc_info.value.failure_cases["check"].values
  )

def test_chaos_single_negative_price_passes(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Negative adjustment prices and batches with negative prices pass validation."""
  # Add a single A-adjustment row with negative price
  single_adjustment = pd.DataFrame({
      "InvoiceNo": ["A999999"],
      "StockCode": ["B"],
      "Description": ["Adjust bad debt"],
      "Quantity": [1],
      "InvoiceDate": ["2026-11-10 14:15:00"],
      "Price": [-53594.36],
      "Customer ID": [None],
      "Country": ["United Kingdom"],
  })
  batch_with_single_adjustment = pd.concat([valid_raw_batch, single_adjustment], ignore_index=True)

  processed_single = preprocess_batch(batch_with_single_adjustment, source_name="single_adjustment.csv")
  validated_single = OnlineRetailBronzeSchema.validate(processed_single, lazy=True)
  assert len(validated_single) == len(batch_with_single_adjustment)

  # Include additional negative prices; monitoring reports them without blocking.
  batch_with_negative_prices = batch_with_single_adjustment.copy()
  num_negative = max(1, len(batch_with_negative_prices) // 10)
  batch_with_negative_prices.loc[:num_negative - 1, "Price"] = -99.99

  processed_negative = preprocess_batch(batch_with_negative_prices, source_name="negative_price_batch.csv")

  validated_negative = OnlineRetailBronzeSchema.validate(processed_negative, lazy=True)
  assert len(validated_negative) == len(batch_with_negative_prices)

def test_chaos_cancellation_with_stock_code_M_passes(
    valid_raw_batch: pd.DataFrame,
) -> None:
  """Chaos Test 10: C-prefixed cancellation with stock_code='M' and positive quantity passes."""
  # Add a C-prefixed cancellation row with stock_code='M' and quantity=1
  cancellation_row = pd.DataFrame({
      "InvoiceNo": ["C496350"],
      "StockCode": ["M"],
      "Description": ["Cancellation of order"],
      "Quantity": [1],
      "InvoiceDate": ["2026-11-10 09:41:00"],
      "Price": [27.50],
      "Customer ID": ["14527"],
      "Country": ["United Kingdom"],
  })
  batch_with_cancellation = pd.concat([valid_raw_batch, cancellation_row], ignore_index=True)

  processed_cancellation = preprocess_batch(batch_with_cancellation, source_name="cancellation_M.csv")
  validated_cancellation = OnlineRetailBronzeSchema.validate(processed_cancellation, lazy=True)
  assert len(validated_cancellation) == len(batch_with_cancellation)