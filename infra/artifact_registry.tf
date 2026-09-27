# infra/artifact_registry.tf

resource "google_artifact_registry_repository" "portfolio_repo" {
  repository_id = "portfolio-mle-finance-repo"
  location      = "us-central1"
  format        = "DOCKER"
}