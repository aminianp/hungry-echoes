output "cluster_endpoint" {
  description = "Cluster endpoint"
  value       = google_container_cluster.monitoring_cluster.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate"
  value       = base64decode(google_container_cluster.monitoring_cluster.master_auth[0].cluster_ca_certificate)
  sensitive   = true
}

output "network_name" {
  description = "The name of the VPC"
  value       = data.google_compute_network.vpc.name
}

output "subnet_name" {
  description = "The name of the monitoring subnet"
  value       = google_compute_subnetwork.monitoring_subnet.name
}