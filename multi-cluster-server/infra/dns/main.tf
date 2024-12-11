# Get cluster info
data "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.cluster_region
}

# Get Google client config
data "google_client_config" "default" {}

# Configure providers
provider "google" {
  project = var.project_id
  region  = var.cluster_region
}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
  )
}

# Get the ingress service IP
data "kubernetes_service" "ingress_nginx" {
  metadata {
    name      = var.nginx_controller
    namespace = var.nginx_namespace
  }
}

# Create DNS zone
resource "google_dns_managed_zone" "app_zone" {
  name        = var.dns_zone_name
  dns_name    = var.app_cluster_dns_name
  description = "DNS zone for Hungry Echoes application"
}

# Create A record for the app cluster
resource "google_dns_record_set" "app" {
  name         = var.app_cluster_dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.app_zone.name
  rrdatas      = [data.kubernetes_service.ingress_nginx.status.0.load_balancer.0.ingress.0.ip]
}

# Create A record for the monitoring
resource "google_dns_record_set" "monitoring" {
  name         = var.monitoring_cluster_dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.app_zone.name
  rrdatas      = [data.kubernetes_service.ingress_nginx.status.0.load_balancer.0.ingress.0.ip]
}