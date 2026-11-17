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

# Enable Vertex AI API via Infrastructure-as-Code
resource "google_project_service" "vertex_ai" {
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false # true so destroy actually turns off the API
}

# Grant Vertex AI User permission to the pipeline service account
resource "google_project_iam_member" "vertex_ai_user" {
  project    = var.project_id
  role       = "roles/aiplatform.user"
  member     = "serviceAccount:${google_service_account.pipeline_runner.email}"
  depends_on = [google_project_service.vertex_ai]
}
