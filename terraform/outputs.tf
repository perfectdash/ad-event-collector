output "pubsub_topic_id" {
  description = "The fully qualified path of the Pub/Sub topic"
  value       = google_pubsub_topic.ad_events.id
}

output "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic"
  value       = google_pubsub_topic.ad_events.name
}

output "pubsub_subscription_name" {
  description = "The name of the Pub/Sub subscription for raw events"
  value       = google_pubsub_subscription.ad_events_sub.name
}

output "project_id" {
  description = "The GCP Project ID used"
  value       = var.project_id
}

output "wif_provider_id" {
  description = "The Workload Identity Provider ID to set as WIF_PROVIDER in GitHub Secrets"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "wif_service_account_email" {
  description = "The Service Account email to set as WIF_SERVICE_ACCOUNT in GitHub Secrets"
  value       = google_service_account.github_deployer.email
}

output "artifact_registry_repo_url" {
  description = "The url of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ad_gateway_repo.repository_id}"
}
