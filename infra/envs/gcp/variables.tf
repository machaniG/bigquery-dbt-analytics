# Input variable declaration

variable "project_id" {
  description = "project-f5f18574-c0c4-44e2-b60" # GCP project where BigQuery datasets will be created.
  type        = string
}

variable "region" {
  description = "GCP Region / BigQuery dataset location"
  type        = string
  default     = "europe-west3"
}

variable "bronze_bucket_name" {
  description = "Existing GCS bucket for Bronze Parquet files"
  type        = string
  default     = "raw-online-retail"
}

variable "landing_bucket_name" {
  description = "New GCS bucket for raw CSV landing drop zone"
  type        = string
  default     = "retail-landing-zone" # note: GCS bucket names are globally unique
}

# GCS bucket names must be globally unique across all Google Cloud users. 
# If retail-landing-zone is already taken globally by someone else, modify with project ID or initials, e.g., retail-landing-zone-eu