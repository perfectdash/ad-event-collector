variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The target region for GCP resources"
  type        = string
  default     = "us-central1"
}

variable "topic_name" {
  description = "The name of the Pub/Sub topic for ad events"
  type        = string
  default     = "ad-events-raw"
}

variable "subscription_name" {
  description = "The name of the Pub/Sub subscription for ad events"
  type        = string
  default     = "ad-events-raw-sub"
}

variable "github_repository" {

  description = "The GitHub repository in 'owner/repo' format allowed to assume the WIF deployer role"
  type        = string
  default     = "perfectdash/ad-event-collector"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", var.github_repository))
    error_message = "The github_repository must be in the format 'owner/repo'."
  }

}

