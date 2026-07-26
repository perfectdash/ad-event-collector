# I did this to enable the Pub/Sub API
resource "google_project_service" "pubsub_api" {
  project            = var.project_id
  service            = "pubsub.googleapis.com"
  disable_on_destroy = false
}

# I did this to create the ad-events-raw Pub/Sub topic
resource "google_pubsub_topic" "ad_events" {
  name       = var.topic_name
  project    = var.project_id
  depends_on = [google_project_service.pubsub_api]
}

# I did this to create a subscription for raw analytics consumption/verification
resource "google_pubsub_subscription" "ad_events_sub" {
  name    = "${var.topic_name}-sub"
  topic   = google_pubsub_topic.ad_events.name
  project = var.project_id
}

# I did this to enable IAM and Artifact Registry APIs
resource "google_project_service" "iam_api" {
  project            = var.project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iamcredentials_api" {
  project            = var.project_id
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry_api" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# I did this to create the Artifact Registry repository
resource "google_artifact_registry_repository" "ad_gateway_repo" {
  location      = var.region
  repository_id = "ad-gateway-repo"
  description   = "Docker repository for Ad Event Gateway"
  format        = "DOCKER"
  project       = var.project_id
  depends_on    = [google_project_service.artifactregistry_api]
}

# I did this to create the Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "ad-github-actions-pool"
  display_name              = "Ad Gateway GitHub Actions Pool"
  description               = "Identity pool for keyless GitHub Actions authentication"
  project                   = var.project_id
  depends_on                = [google_project_service.iam_api]
}

# I did this to create the OIDC Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  project                            = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "attribute.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# I did this to create the GCP Service Account for GitHub Actions Impersonation
resource "google_service_account" "github_deployer" {
  account_id   = "ad-github-deployer"
  display_name = "Ad Gateway GitHub Actions Deployer"
  project      = var.project_id
  depends_on   = [google_project_service.iam_api]
}

# I did this to bind WIF impersonation rights to the GitHub repository
resource "google_service_account_iam_member" "wif_impersonation" {
  service_account_id = google_service_account.github_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"
}

# I did this to grant deployment permissions to the GitHub Deployer service account
locals {
  deployer_roles = [
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountUser"
  ]
}

resource "google_project_iam_member" "deployer_permissions" {
  for_each = toset(local.deployer_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.github_deployer.email}"
}

# I did this to create the GCP Service Account for Cloud Run Application Runtime
resource "google_service_account" "app_runner" {
  account_id   = "ad-event-collector-runner"
  display_name = "Ad Event Collector App Runner"
  project      = var.project_id
  depends_on   = [google_project_service.iam_api]
}

# I did this to grant Pub/Sub Publisher rights to the App Runner Service Account
resource "google_pubsub_topic_iam_member" "runner_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.ad_events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.app_runner.email}"
}
