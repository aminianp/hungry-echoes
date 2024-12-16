variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "tailscale-tests-and-demos"
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

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "hungry-echoes-vpc"
}

# For PostgreSQL credentials
variable "postgres_db_schema" {
  description = "PostgreSQL database schema name"
  type        = string
  default     = "corporate"
}

variable "postgres_db_table" {
  description = "PostgreSQL table name"
  type        = string
  default     = "jargons"
}