# Application cluster in us-west3
resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.cluster_region

  # Enable Autopilot mode
  enable_autopilot = true

  # Network configuration
  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # Enable Multi-cluster Services
  fleet {
    project = var.project_id
  }

  # IP allocation policy for autopilot
  ip_allocation_policy {
    cluster_secondary_range_name  = "${var.cluster_name}-pods"
    services_secondary_range_name = "${var.cluster_name}-services"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = false
    enable_private_endpoint = false  # Allow public access to master
    master_ipv4_cidr_block = "172.16.0.0/28"  # Master IP range
  }

  # Release channel for auto-upgrades
  release_channel {
    channel = "REGULAR"
  }

  # Wait for APIs to be available
  depends_on = [
    google_project_service.services
  ]
}