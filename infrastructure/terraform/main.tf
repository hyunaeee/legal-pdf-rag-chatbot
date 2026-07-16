locals {
  required_services = toset([
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "telemetry.googleapis.com",
  ])

  runtime_roles = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/telemetry.tracesWriter",
  ])
}

resource "google_project_service" "required" {
  for_each = local.required_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "application" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  description   = "Container images for the enterprise policy agent"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "enterprise-policy-agent"
  display_name = "Enterprise Policy Agent runtime"
}

resource "google_project_iam_member" "runtime_roles" {
  for_each = local.runtime_roles

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service" "api" {
  project             = var.project_id
  name                = var.service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }

      env {
        name  = "EPA_ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "EPA_MODEL_BACKEND"
        value = "vertex"
      }

      env {
        name  = "EPA_GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "EPA_GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "EPA_VERTEX_MODEL"
        value = var.vertex_model
      }

      env {
        name  = "EPA_REQUIRE_TENANT_HEADER"
        value = "true"
      }

      env {
        name  = "EPA_OTEL_ENABLED"
        value = tostring(var.otel_enabled)
      }

      env {
        name  = "EPA_OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }

      startup_probe {
        initial_delay_seconds = 2
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 6

        http_get {
          path = "/health"
          port = 8080
        }
      }

      liveness_probe {
        timeout_seconds   = 3
        period_seconds    = 30
        failure_threshold = 3

        http_get {
          path = "/health"
          port = 8080
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_artifact_registry_repository.application,
    google_project_iam_member.runtime_roles,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
