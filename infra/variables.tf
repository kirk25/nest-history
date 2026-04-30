variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-west1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-west1-b"
}

variable "ssh_user" {
  description = "SSH username for the VM"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key to authorize on the VM"
  type        = string
}

variable "compute_service_account" {
  description = "Service account email for the compute instance"
  type        = string
}
