# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.cluster_region
}

# Configure the Helm provider to install NGINX controller
provider "helm" {
  kubernetes {
    host                   = google_container_cluster.cluster.endpoint
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
  }
}

# Enable required GCP APIs
resource "google_project_service" "services" {
  for_each = toset([
    "container.googleapis.com",     # GKE API
    "compute.googleapis.com",       # Compute Engine API
    "monitoring.googleapis.com",    # Cloud Monitoring API
    "logging.googleapis.com",       # Cloud Logging API
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Get default Google client configuration
data "google_client_config" "default" {}