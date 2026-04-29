terraform {
  required_version = ">= 1.6"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1"
    }
    talos = {
      source  = "siderolabs/talos"
      version = "~> 0.7"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_password" "zenith_token_signing_key" {
  length  = 32
  special = false
}

resource "random_password" "azimuth_django_secret_key" {
  length  = 64
  special = false
}

provider "openstack" {
  auth_url                        = var.openstack_auth_url
  application_credential_id       = var.openstack_application_credential_id
  application_credential_secret   = var.openstack_application_credential_secret
  region                          = var.openstack_region_name
}

# ── Step 1: Generate Talos machine config ─────────────────────────────────────

resource "openstack_networking_floatingip_v2" "seed" {
  pool = local.floatingip_pool
}

data "openstack_networking_network_v2" "external" {
  network_id = var.external_network_id
}

locals {
  floatingip_pool = var.floatingip_pool != "" ? var.floatingip_pool : data.openstack_networking_network_v2.external.name
  seed_ip         = openstack_networking_floatingip_v2.seed.address
  base_domain     = var.base_domain != "" ? var.base_domain : "${local.seed_ip}.sslip.io"

  exposed_ports = [
    { name = "http",        min = 80,   max = 80 },
    { name = "https",       min = 443,  max = 443 },
    { name = "zenith_sshd", min = 32222, max = 32222 },
  ]
}

# ── Step 2: Generate machine config ──────────────────────────────────────────

module "talos" {
  source = "../../modules/talos-node"

  cluster_name        = var.name
  machine_name        = "azimuth-aoi"
  cluster_endpoint_ip = local.seed_ip
  talos_version       = var.talos_version
  kubernetes_version  = var.kubernetes_version
}

# ── Step 3: Provision OpenStack infrastructure ────────────────────────────────

module "infra" {
  source = "../../modules/openstack-infra"

  name                = var.name
  machine_name        = "azimuth-aoi"
  image_id            = var.talos_image_id
  flavor_id           = var.flavor_id
  flavor_name         = var.flavor_name
  external_network_id = var.external_network_id
  floatingip_pool     = local.floatingip_pool
  fixed_floatingip    = local.seed_ip
  data_volume_size    = var.data_volume_size
  root_volume_enabled = var.root_volume_enabled
  root_volume_size    = var.root_volume_size
  exposed_port_ranges = local.exposed_ports

  user_data = module.talos.machine_config
}

# ── Step 4: Validate cluster health ──────────────────────────────────────────

resource "null_resource" "talos_health" {
  depends_on = [local_sensitive_file.talosconfig, module.infra]

  triggers = {
    cluster_endpoint = local.seed_ip
  }

  provisioner "local-exec" {
    command = <<-EOT
      while ! talosctl health --talosconfig=${abspath(path.module)}/.work/talosconfig -n ${module.infra.internal_ip} -e ${local.seed_ip}; do
        sleep 10
      done
    EOT
  }
}

# ── Step 5: Bootstrap FluxCD ──────────────────────────────────────────────────

module "flux" {
  source = "../../modules/flux-bootstrap"

  depends_on = [null_resource.talos_health]

  kubeconfig_raw             = module.talos.kubeconfig_raw
  git_url                    = var.git_url
  git_branch                 = var.git_branch
  git_token                  = var.git_token
  flux_path                               = "flux/clusters/all-in-one"
  base_domain                             = local.base_domain
  openstack_auth_url                      = var.openstack_auth_url
  openstack_region_name                   = var.openstack_region_name
  openstack_application_credential_id     = var.openstack_application_credential_id
  openstack_application_credential_secret = var.openstack_application_credential_secret
  zenith_token_signing_key                = random_password.zenith_token_signing_key.result
  azimuth_django_secret_key               = random_password.azimuth_django_secret_key.result
}

# ── Persist kubeconfig locally ────────────────────────────────────────────────

resource "local_sensitive_file" "kubeconfig" {
  content         = module.talos.kubeconfig_raw
  filename        = "${path.module}/.work/kubeconfig.yaml"
  file_permission = "0600"
}

resource "local_sensitive_file" "talosconfig" {
  content         = module.talos.talosconfig
  filename        = "${path.module}/.work/talosconfig"
  file_permission = "0600"
}
