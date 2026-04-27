variable "kubeconfig_raw" {
  description = "Raw kubeconfig content for the target cluster"
  type        = string
  sensitive   = true
}

variable "git_url" {
  description = "HTTPS URL of the Git repository holding the FluxCD manifests"
  type        = string
}

variable "git_branch" {
  description = "Branch to use in the Git repository"
  type        = string
  default     = "main"
}

variable "git_token" {
  description = "Personal access token (or app password) for Git authentication"
  type        = string
  sensitive   = true
}

variable "git_username" {
  description = "Git username for authentication"
  type        = string
  default     = "git"
}

variable "flux_path" {
  description = "Path inside the repository where FluxCD cluster manifests are stored"
  type        = string
  default     = "flux/clusters/single-node"
}

variable "flux_version" {
  description = "FluxCD version to bootstrap (e.g. v2.4.0)"
  type        = string
  default     = "v2.4.0"
}

variable "flux_namespace" {
  description = "Namespace where FluxCD components are installed"
  type        = string
  default     = "flux-system"
}

variable "components_extra" {
  description = "Additional FluxCD components to install (e.g. image-reflector-controller)"
  type        = list(string)
  default     = []
}
