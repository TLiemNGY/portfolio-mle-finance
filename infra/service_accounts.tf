# infra/service_accounts.tf

resource "google_service_account" "mle_portfolio_sa" {
  account_id   = "mle-portfolio-sa"
  display_name = "Service account principal - Portfolio MLE"
}

resource "google_service_account" "stop_billing_sa" {
  account_id   = "stop-billing-sa"
  display_name = "Service account pour coupe-circuit budget"
}