terraform {
  required_version = ">= 1.6"

  required_providers {
    talos = {
      source  = "siderolabs/talos"
      version = "~> 0.7"
    }
  }
}

# ── Cluster secrets (CA, tokens, etc.) ───────────────────────────────────────

resource "talos_machine_secrets" "this" {
  talos_version = var.talos_version
}

# ── Machine configuration for the single control-plane node ──────────────────

locals {
  # Allow scheduling workloads on the control-plane (single-node mode)
  base_patches = [
    jsonencode({
      cluster = {
        allowSchedulingOnControlPlanes = true
      }
    }),
    jsonencode({
      machine = {
        # Mount the data volume for etcd and kubelet state
        disks = [
          {
            device = var.data_volume_device
            partitions = [
              {
                mountpoint = "/var/lib/etcd"
                size       = "0"  # use remaining space
              }
            ]
          }
        ]
        # OpenStack cloud-provider integration
        features = {
          kubePrism = {
            enabled = true
            port    = 7445
          }
        }
      }
    })
  ]

  all_patches = concat(local.base_patches, var.config_patches_extra)
}

data "talos_machine_configuration" "controlplane" {
  cluster_name       = var.cluster_name
  machine_type       = "controlplane"
  cluster_endpoint   = "https://${var.cluster_endpoint_ip}:${var.kubernetes_api_port}"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  talos_version      = var.talos_version
  kubernetes_version = var.kubernetes_version
  config_patches     = local.all_patches
}

# ── Bootstrap the cluster once the node is reachable ─────────────────────────

resource "talos_machine_bootstrap" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = var.cluster_endpoint_ip
  endpoint             = var.cluster_endpoint_ip
}

# ── Retrieve kubeconfig ───────────────────────────────────────────────────────

# ── Retrieve kubeconfig (resource, not data source) ──────────────────────────

resource "talos_cluster_kubeconfig" "this" {
  depends_on           = [talos_machine_bootstrap.this]
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = var.cluster_endpoint_ip
  endpoint             = var.cluster_endpoint_ip
}

# ── Build talosconfig YAML ────────────────────────────────────────────────────

data "talos_client_configuration" "this" {
  cluster_name         = var.cluster_name
  client_configuration = talos_machine_secrets.this.client_configuration
  nodes                = [var.cluster_endpoint_ip]
  endpoints            = [var.cluster_endpoint_ip]
}
