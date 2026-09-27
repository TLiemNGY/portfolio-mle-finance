resource "google_cloud_scheduler_job" "weekly_trigger" {
  name      = "portfolio-weekly-refresh-trigger"
  region    = "us-central1"
  schedule  = "0 20 * * 0"
  time_zone = "Europe/Paris"

  http_target {
    uri         = "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/portfolio-mle-finance/jobs/portfolio-weekly-refresh-job:run"
    http_method = "POST"

    oauth_token {
      service_account_email = google_service_account.mle_portfolio_sa.email
    }
  }
}

resource "google_cloud_scheduler_job" "biweekly_trigger" {
  name      = "portfolio-biweekly-refresh-trigger"
  region    = "us-central1"
  schedule  = "0 20 1,15 * *"
  time_zone = "Europe/Paris"

  http_target {
    uri         = "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/portfolio-mle-finance/jobs/portfolio-biweekly-refresh-job:run"
    http_method = "POST"

    oauth_token {
      service_account_email = google_service_account.mle_portfolio_sa.email
    }
  }
}