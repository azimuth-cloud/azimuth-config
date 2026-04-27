variable "cluster_name" {
  description = "Name of the Talos/Kubernetes cluster"
  type        = string
}

variable "cluster_endpoint_ip" {
  description = "Externally reachable IP of the control plane (floating IP)"
  type        = string
}

variable "talos_api_port" {
  description = "Port on which the Talos API listens"
  type        = number
  default     = 50000
}

variable "kubernetes_api_port" {
  description = "Port on which the Kubernetes API server listens"
  type        = number
  default     = 6443
}

variable "talos_version" {
  description = "Talos version string (e.g. v1.9.5)"
  type        = string
  default     = "v1.9.5"
}

variable "kubernetes_version" {
  description = "Kubernetes version to install (e.g. v1.32.0)"
  type        = string
  default     = "v1.32.0"
}

variable "data_volume_device" {
  description = "Block device path for the Talos data volume (e.g. /dev/vdb)"
  type        = string
  default     = "/dev/vdb"
}

variable "config_patches_extra" {
  description = "Additional Talos machine config patches (list of JSON-encoded patch objects)"
  type        = list(string)
  default     = []
}
