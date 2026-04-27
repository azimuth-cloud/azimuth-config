terraform {
  required_version = ">= 1.6"

  required_providers {
    flux = {
      source  = "fluxcd/flux"
      version = "~> 1.4"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

provider "flux" {
  kubernetes = {
    config_raw = var.kubeconfig_raw
  }
  git = {
    url    = var.git_url
    branch = var.git_branch
    http = {
      username = var.git_username
      password = var.git_token
    }
  }
}

provider "kubernetes" {
  config_raw = var.kubeconfig_raw
}

# ── FluxCD bootstrap ──────────────────────────────────────────────────────────
#
# This commits the FluxCD install manifests into the Git repo at `var.flux_path`
# and creates the flux-system namespace + resources in the cluster.
# From that point on, FluxCD self-manages and reconciles everything else from Git.

resource "flux_bootstrap_git" "this" {
  path             = var.flux_path
  version          = var.flux_version
  namespace        = var.flux_namespace
  components_extra = var.components_extra

  # Tolerate the control-plane taint so FluxCD controllers can run on a single-node cluster
  toleration_keys = ["node-role.kubernetes.io/control-plane"]
}
