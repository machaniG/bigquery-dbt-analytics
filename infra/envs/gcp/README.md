```plaintext
infra/envs/gcp/
├── versions.tf       # Terraform & Google provider version constraints
├── variables.tf      # Input variable declarations
├── terraform.tfvars  # Your actual local values (add to .gitignore if sensitive, or commit non-secret defaults)
├── storage.tf        # GCS Landing & Bronze buckets + lifecycle rules
├── bigquery.tf       # Medallion datasets (Bronze, Silver, Gold)
├── iam.tf            # Service account ('dbt-cloud-runner') & least-privilege IAM roles
└── outputs.tf        # Exported bucket URLs and service account email
```