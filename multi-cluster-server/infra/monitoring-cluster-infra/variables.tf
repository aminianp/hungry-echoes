variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "tailscale-tests-and-demos"
}

variable "cluster_name" {
  description = "Name for the monitoring cluster"
  type        = string
  default     = "hungry-monitoring"    
}

variable "cluster_region" {
  description = "Region for the monitoring cluster"
  type        = string
  default     = "us-west2"
}

variable "network_name" {
  description = "Name of the VPC network to connect to"
  type        = string
  default     = "hungry-echoes-vpc"  # Using your existing VPC
}