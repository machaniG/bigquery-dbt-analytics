# GCS Landing & Bronze buckets + lifecycle rules
# Landing Zone Bucket (Dirty Drop Zone for Raw CSVs)
resource "google_storage_bucket" "landing_zone" {
  name                        = var.landing_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# EXISTING: Bronze Zone Bucket (Immutable Partitioned Parquet System of Record)
resource "google_storage_bucket" "bronze_zone" {
  name                        = var.bronze_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true

  lifecycle {
    prevent_destroy = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}
