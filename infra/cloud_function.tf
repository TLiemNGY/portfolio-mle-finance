resource "google_cloudfunctions2_function" "stop_billing" {
  name     = "stop-billing"
  location = "us-central1"

  build_config {
    runtime     = "python312"
    entry_point = "stop_billing"

    source {
      storage_source {
        bucket = "gcf-v2-sources-1045349921876-us-central1"
        object = "stop-billing/function-source.zip"
      }
    }
  }

  service_config {
    available_memory                 = "256M"
    available_cpu                    = "0.1666"
    timeout_seconds                  = 60
    max_instance_request_concurrency = 1
    ingress_settings                 = "ALLOW_ALL"
    service_account_email            = google_service_account.stop_billing_sa.email

    environment_variables = {
      LOG_EXECUTION_ID = "true"
    }
  }

  event_trigger {
    trigger_region         = "us-central1"
    event_type              = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic            = google_pubsub_topic.billing_alerts.id
    retry_policy            = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email  = google_service_account.stop_billing_sa.email
  }
}