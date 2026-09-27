resource "google_project_iam_member" "mle_portfolio_bigquery_job_user" {
  project = "portfolio-mle-finance"
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.mle_portfolio_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "google_api_key_accessor" {
  secret_id = google_secret_manager_secret.google_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mle_portfolio_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "marketaux_api_key_accessor" {
  secret_id = google_secret_manager_secret.marketaux_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mle_portfolio_sa.email}"
}

resource "google_cloud_run_v2_job_iam_member" "weekly_invoker" {
  name     = google_cloud_run_v2_job.weekly_refresh.name
  location = "us-central1"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.mle_portfolio_sa.email}"
}

resource "google_cloud_run_v2_job_iam_member" "biweekly_invoker" {
  name     = google_cloud_run_v2_job.biweekly_refresh.name
  location = "us-central1"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.mle_portfolio_sa.email}"
}