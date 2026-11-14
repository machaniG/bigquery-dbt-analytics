# for Bigquery datasets 
# Update dataset_id values if existing BigQuery datasets have different names
# Bronze Layer: Raw dataset holding BigQuery External Tables over GCS Parquet files
# (Downstream Silver & Gold datasets are dynamically provisioned and managed by dbt)

resource "google_bigquery_dataset" "bronze" {
  dataset_id  = "dbt_analytics26"
  location    = var.region
  description = "Bronze layer: External tables pointing to partitioned GCS Parquet files"
}
