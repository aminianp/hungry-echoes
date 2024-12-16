# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.cluster_region
}

# Enable required GCP APIs (if not already enabled)
resource "google_project_service" "services" {
  for_each = toset([
    "container.googleapis.com",     # GKE API
    "compute.googleapis.com",       # Compute Engine API
    "monitoring.googleapis.com",    # Cloud Monitoring API
    "logging.googleapis.com",       # Cloud Logging API
    "gkehub.googleapis.com",        # GKE Hub API for Multi-cluster features
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Get existing VPC information
data "google_compute_network" "vpc" {
  name = var.network_name
}

# Create subnet for monitoring cluster
resource "google_compute_subnetwork" "monitoring_subnet" {
  name          = "${var.cluster_name}-subnet"
  network       = data.google_compute_network.vpc.id
  region        = var.cluster_region
  ip_cidr_range = "10.1.0.0/20"  # Different range from app subnet

  # Define secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "${var.cluster_name}-pods"
    ip_cidr_range = "10.102.0.0/16"  # Pod IP range
  }

  secondary_ip_range {
    range_name    = "${var.cluster_name}-services"
    ip_cidr_range = "10.103.0.0/20"  # Service IP range
  }

  # Enable flow logs
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata           = "INCLUDE_ALL_METADATA"
  }
}

# Monitoring cluster in us-west4
resource "google_container_cluster" "monitoring_cluster" {
  name     = var.cluster_name
  location = var.cluster_region

  # Enable Autopilot mode
  enable_autopilot = true

  # Enable Multi-cluster Services
  fleet {
    project = var.project_id
  }

  # Network configuration
  network    = data.google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.monitoring_subnet.id

  # IP allocation policy
  ip_allocation_policy {
    cluster_secondary_range_name  = "${var.cluster_name}-pods"
    services_secondary_range_name = "${var.cluster_name}-services"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = false
    enable_private_endpoint = false  # Allow public access to master
    master_ipv4_cidr_block = "172.16.1.0/28"  # Different from app cluster
  }

  # Release channel
  release_channel {
    channel = "REGULAR"
  }

  depends_on = [
    google_project_service.services
  ]
}