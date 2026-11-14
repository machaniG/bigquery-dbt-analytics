# Environment-driven GCS bucket & path settings
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "project-f5f18574-c0c4-44e2-b60")
    landing_bucket: str = os.getenv("LANDING_BUCKET", "retail-landing-zone")
    bronze_bucket: str = os.getenv("BRONZE_BUCKET", "raw-online-retail")
    dataset_prefix: str = os.getenv("DATASET_PREFIX", "transactions")
    output_filename: str = os.getenv("OUTPUT_FILENAME", "online_retail.parquet")
