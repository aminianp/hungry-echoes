variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "tailscale-tests-and-demos"
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "hungry-echoes-vpc"
}

variable "cluster_name" {
  description = "Name for the application cluster"
  type        = string
  default     = "hungry-echoes"    
}

variable "cluster_region" {
  description = "Region for the application cluster"
  type        = string
  default     = "us-west3"
}

variable "nginx_controller" {
  description = "Name for the nginx controller"
  type        = string
  default     = "ingress-nginx-controller"
}

variable "nginx_namespace" {
  description = "Namespace for the nginx controller deployment"
  type        = string
  default     = "ingress-nginx"
}

variable "public_dns_zone_name" {
  description = "Public DNS zone name"
  type        = string
  default     = "hungryechoes-public-zone"
}

variable "app_cluster_dns_name" {
  description = "DNS record for the app cluster"
  type        = string
  default     = "hungryechoes.com."
}

variable "monitoring_cluster_dns_name" {
  description = "DNS record for the monitoring cluster"
  type        = string
  default     = "metrics.hungryechoes.com."
}

variable "private_dns_zone_name" {
  description = "Public DNS zone name"
  type        = string
  default     = "hungryechoes-private-zone"
}