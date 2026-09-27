data "google_billing_account" "account" {
  billing_account = "0137AB-246C93-D58832"
}

resource "google_billing_budget" "budget" {
  billing_account = data.google_billing_account.account.id
  display_name    = "Budget Portfolio MLE"

  amount {
    specified_amount {
      currency_code = "EUR"
      units         = "15"
    }
  }

  budget_filter {
    projects = ["projects/1045349921876"]
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.8
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    pubsub_topic = "projects/portfolio-mle-finance/topics/billing-alerts"
  }
}