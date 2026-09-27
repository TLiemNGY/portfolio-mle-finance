# infra/cloud_run.tf

resource "google_cloud_run_v2_service" "api" {
  name     = "portfolio-mle-finance-api"
  location = "us-central1"

  template {
    service_account = google_service_account.mle_portfolio_sa.email

    containers {
      image = "us-central1-docker.pkg.dev/portfolio-mle-finance/portfolio-mle-finance-repo/api:latest"

      env {
        name = "GOOGLE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "GOOGLE_API_KEY"
            version = "latest"
          }
        }
      }

      env {
        name = "MARKETAUX_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "MARKETAUX_API_KEY"
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "weekly_refresh" {
  name     = "portfolio-weekly-refresh-job"
  location = "us-central1"

  template {
    template {
      service_account = google_service_account.mle_portfolio_sa.email
      max_retries      = 1
      timeout          = "600s"

      containers {
        image   = "us-central1-docker.pkg.dev/portfolio-mle-finance/portfolio-mle-finance-repo/api:latest"
        command = ["uv"]
        args    = ["run", "python", "-m", "ingestion.run_weekly"]

        env {
          name = "MARKETAUX_API_KEY"
          value_source {
            secret_key_ref {
              secret  = "MARKETAUX_API_KEY"
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "biweekly_refresh" {
  name     = "portfolio-biweekly-refresh-job"
  location = "us-central1"

  template {
    template {
      service_account = google_service_account.mle_portfolio_sa.email
      max_retries      = 1
      timeout          = "600s"

      containers {
        image   = "us-central1-docker.pkg.dev/portfolio-mle-finance/portfolio-mle-finance-repo/api:latest"
        command = ["uv"]
        args    = ["run", "python", "-m", "ingestion.run_biweekly"]
      }
    }
  }
}