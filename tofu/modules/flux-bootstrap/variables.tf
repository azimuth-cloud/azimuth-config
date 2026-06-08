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

variable "openstack_auth_url" {
  description = "OpenStack Keystone authentication URL"
  type        = string
}

variable "openstack_region_name" {
  description = "OpenStack region name"
  type        = string
}

variable "openstack_tenant_name" {
  description = "OpenStack project / tenant name (used in clouds.yaml for the workload cluster)"
  type        = string
  default     = ""
}

variable "openstack_application_credential_id" {
  description = "OpenStack application credential ID"
  type        = string
  sensitive   = true
}

variable "openstack_application_credential_secret" {
  description = "OpenStack application credential secret"
  type        = string
  sensitive   = true
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

# ── Workload cluster (propagated to cluster-config) ───────────────────────────

variable "external_network_id" {
  description = "OpenStack external network ID (passed to cluster-config for CAPO)"
  type        = string
  default     = ""
}

variable "talos_image_id" {
  description = "Glance image ID of the Talos image (passed to cluster-config for CAPO)"
  type        = string
  default     = ""
}

variable "kubernetes_version" {
  description = "Kubernetes version (passed to cluster-config for TalosControlPlane)"
  type        = string
  default     = "v1.32.0"
}

variable "azimuth_cluster_machine_name" {
  description = "Hostname Talos du nœud de contrôle du cluster applicatif Azimuth"
  type        = string
  default     = "azimuth-apps"
}

# ── Dex OIDC ─────────────────────────────────────────────────────────────────

variable "dex_harbor_client_secret" {
  description = "OAuth2 client secret for Harbor → Dex"
  type        = string
  sensitive   = true
}

variable "dex_grafana_client_secret" {
  description = "OAuth2 client secret for Grafana → Dex"
  type        = string
  sensitive   = true
}

variable "harbor_admin_password" {
  description = "Harbor admin password (also used by the OIDC config Job)"
  type        = string
  sensitive   = true
}

# ── Keycloak ──────────────────────────────────────────────────────────────────

variable "keycloak_admin_password" {
  description = "Keycloak admin password (master realm)"
  type        = string
  sensitive   = true
}

variable "keycloak_db_password" {
  description = "Keycloak PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "keycloak_dex_client_secret" {
  description = "OIDC client secret for Dex → Keycloak (realm azimuth, client dex)"
  type        = string
  sensitive   = true
}

