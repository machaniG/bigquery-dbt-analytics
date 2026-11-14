output "landing_bucket_url" {
  value = google_storage_bucket.landing_zone.url
}

output "bronze_bucket_url" {
  value = google_storage_bucket.bronze_zone.url
}

output "pipeline_service_account_email" {
  value = google_service_account.pipeline_runner.email
}
