output "service_uri" {
  description = "Cloud Run service URI."
  value       = google_cloud_run_v2_service.api.uri
}

output "runtime_service_account" {
  description = "Runtime service account email."
  value       = google_service_account.runtime.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository resource name."
  value       = google_artifact_registry_repository.application.name
}
