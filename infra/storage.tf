# infra/storage.tf

resource "google_storage_bucket" "models" {
  name     = "portfolio-mle-finance-models"
  location = "us-central1"
}