terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "europe-west1"
  description = "Primary GCP Region"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Service Account for Cloud Run API
resource "google_service_account" "copilot_api" {
  account_id   = "narrative-copilot-api"
  display_name = "Narrative Continuity Copilot API Service Account"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "copilot_api" {
  name     = "narrative-continuity-copilot-api"
  location = var.region

  template {
    service_account = google_service_account.copilot_api.email
    containers {
      image = "gcr.io/${var.project_id}/narrative-copilot-api:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
    }
  }
}
