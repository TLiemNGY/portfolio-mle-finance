resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "GOOGLE_API_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "marketaux_api_key" {
  secret_id = "MARKETAUX_API_KEY"

  replication {
    auto {}
  }
}