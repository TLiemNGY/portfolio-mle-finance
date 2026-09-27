# infra/main.tf

terraform {
  backend "gcs" {
    bucket = "portfolio-mle-finance-tfstate"
    prefix = "state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project                = "portfolio-mle-finance"
  region                  = "us-central1"
  user_project_override  = true
  billing_project        = "portfolio-mle-finance"
}