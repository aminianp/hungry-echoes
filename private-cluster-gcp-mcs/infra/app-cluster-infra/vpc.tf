# Create VPC network
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false  # Custom subnet mode
}

# Create subnet for app cluster
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.cluster_name}-subnet"
  network       = google_compute_network.vpc.id
  region        = var.cluster_region
  ip_cidr_range = "10.0.0.0/20"  # Allows up to 4096 IPs

  # Define secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "${var.cluster_name}-pods"
    ip_cidr_range = "10.100.0.0/16"  # Pod IP range
  }

  secondary_ip_range {
    range_name    = "${var.cluster_name}-services"
    ip_cidr_range = "10.101.0.0/20"  # Service IP range
  }

  # Enable flow logs for better network monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata           = "INCLUDE_ALL_METADATA"
  }
}

# Firewall rule for HTTP/HTTPS access
resource "google_compute_firewall" "allow_http_https" {
  name    = "${var.cluster_name}-allow-http-https"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  # Allow from any source (restrict this in production)
  source_ranges = ["0.0.0.0/0"]
  
  # Target only app cluster nodes
  target_tags = ["${var.cluster_name}-nodes"]
}

# Firewall rule to allow egress for image pull and cluster config
resource "google_compute_firewall" "allow_egress" {
  name    = "${var.cluster_name}-allow-egress"
  network = google_compute_network.vpc.id

  allow {
    protocol = "all"
  }

  direction      = "EGRESS"
  destination_ranges = ["0.0.0.0/0"]
}

# Firewall rule for metrics port
resource "google_compute_firewall" "allow_metrics" {
  name    = "${var.cluster_name}-allow-metrics"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["8081"]  # Metrics port
  }

  # Allow from any source within the VPC (we'll restrict this later)
  source_ranges = ["10.0.0.0/8"]
  
  # Target only app cluster nodes
  target_tags = ["${var.cluster_name}-nodes"]
}