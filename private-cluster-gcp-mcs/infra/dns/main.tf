# Get cluster info
data "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.cluster_region
}

# Get Google client config
data "google_client_config" "default" {}

# Get existing VPC information
data "google_compute_network" "vpc" {
  name = var.network_name
}

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

# Create namespace for monitoring
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

# Create service import for Prometheus
resource "kubernetes_service" "prometheus" {
  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    annotations = {
      "net.gke.io/multi-cluster-service-name" = "prometheus"
    }
  }
  spec {
    port {
      name        = "http"
      port        = 9090
      target_port = 9090
    }
    type = "ClusterIP"
  }
}

# Create public DNS zone for application
resource "google_dns_managed_zone" "public_zone" {
  name        = var.public_dns_zone_name
  dns_name    = var.app_cluster_dns_name
  description = "Public DNS zone for Hungry Echoes application"

  visibility = "public"
}

# Create private DNS zone with same domain
resource "google_dns_managed_zone" "private_zone" {
  name        = var.private_dns_zone_name
  dns_name    = var.app_cluster_dns_name
  description = "Private DNS zone for Hungry Echoes internal services"
  
  visibility = "private"
  
  private_visibility_config {
    networks {
      network_url = data.google_compute_network.vpc.id
    }
  }
}

# Get the ingress service IP
data "kubernetes_service" "ingress_nginx" {
  metadata {
    name      = var.nginx_controller
    namespace = var.nginx_namespace
  }
}

# Create A record for app in public zone
resource "google_dns_record_set" "app" {
  name         = var.app_cluster_dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.public_zone.name
  rrdatas      = [data.kubernetes_service.ingress_nginx.status[0].load_balancer[0].ingress[0].ip]
}

# Create A record for metrics in private zone
resource "google_dns_record_set" "metrics_private" {
  name         = var.monitoring_cluster_dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.private_zone.name
  rrdatas      = [kubernetes_service.prometheus.spec[0].cluster_ip]

  depends_on = [
    kubernetes_service.prometheus
  ]
}