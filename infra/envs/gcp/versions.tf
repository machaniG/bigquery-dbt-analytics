# Terraform & Google provider version constraints
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0.0"
    }
  }

  backend "gcs" {
    bucket = "tf-runs-state-bucket"
    prefix = "gcp/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}