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
  description = "Personal access token for Git authentication. Leave empty for public repositories."
  type        = string
  sensitive   = true
  default     = ""
}

variable "flux_path" {
  description = "Path inside the repository where FluxCD cluster manifests are stored"
  type        = string
  default     = "flux/clusters/single-node"
}


variable "base_domain" {
  description = "Base domain for Zenith ingresses (e.g. 1.2.3.4.sslip.io)"
  type        = string
}

variable "zenith_token_signing_key" {
  description = "Secret key (≥32 chars) for signing Zenith subdomain tokens"
  type        = string
  sensitive   = true
}

variable "azimuth_django_secret_key" {
  description = "Django SECRET_KEY for the Azimuth API (≥50 chars recommended)"
  type        = string
  sensitive   = true
}

variable "flux_namespace" {
  description = "Namespace where FluxCD components are installed"
  type        = string
  default     = "flux-system"
}

