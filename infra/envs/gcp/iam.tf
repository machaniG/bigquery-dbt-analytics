# should create an IAM service account with list permissions
# EXISTING: Service Account for dbt, Ingestion & CI/CD add permission to landing zone reader
resource "google_service_account" "pipeline_runner" {
  account_id   = "dbt-cloud-runner"
  display_name = "dbt Cloud & Pipeline Runner"
}

resource "google_storage_bucket_iam_member" "landing_reader" {
  bucket = google_storage_bucket.landing_zone.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_runner.email}"
}

resource "google_storage_bucket_iam_member" "bronze_writer" {
  bucket = google_storage_bucket.bronze_zone.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_runner.email}"
}

resource "google_project_iam_member" "bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.pipeline_runner.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline_runner.email}"
}
