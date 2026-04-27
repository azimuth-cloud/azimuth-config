# ── OpenStack ─────────────────────────────────────────────────────────────────

variable "openstack_auth_url" {
  type = string
}

variable "openstack_application_credential_id" {
  type      = string
  sensitive = true
}

variable "openstack_application_credential_secret" {
  type      = string
  sensitive = true
}

variable "openstack_region_name" {
  type    = string
  default = "RegionOne"
}

# ── Infrastructure ────────────────────────────────────────────────────────────

variable "name" {
  description = "Unique name prefix for all resources (e.g. azimuth-aio)"
  type        = string
  default     = "azimuth"
}

variable "external_network_id" {
  description = "OpenStack external network ID for the router and floating IP"
  type        = string
}

variable "flavor_id" {
  description = "OpenStack flavor ID for the seed node"
  type        = string
  default     = ""
}

variable "flavor_name" {
  description = "OpenStack flavor name (alternative to flavor_id)"
  type        = string
  default     = ""
}

variable "talos_image_id" {
  description = "Glance image ID of the Talos RAW image (platform: openstack, generated at https://factory.talos.dev/)"
  type        = string
}

variable "data_volume_size" {
  description = "Size in GB of the data volume"
  type        = number
  default     = 100
}

variable "root_volume_enabled" {
  description = "Boot from a Cinder root volume"
  type        = bool
  default     = false
}

variable "root_volume_size" {
  type    = number
  default = 40
}

# ── Talos ─────────────────────────────────────────────────────────────────────

variable "talos_version" {
  type    = string
  default = "v1.9.5"
}

variable "kubernetes_version" {
  type    = string
  default = "v1.32.0"
}

# ── FluxCD / Git ──────────────────────────────────────────────────────────────

variable "git_url" {
  description = "HTTPS URL of the azimuth-config Git repository"
  type        = string
}

variable "git_token" {
  description = "Personal access token for Git authentication. Leave empty for public repositories."
  type        = string
  sensitive   = true
  default     = ""
}

variable "git_branch" {
  type    = string
  default = "main"
}

variable "floatingip_pool" {
  description = "Name of the floating IP pool. If empty, the external network name is used."
  type        = string
  default     = ""
}

variable "base_domain" {
  description = "Base domain for Zenith ingresses. Defaults to <floating-ip>.sslip.io if empty."
  type        = string
  default     = ""
}
