terraform {
  required_version = ">= 1.6"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

locals {
  kubeconfig_file = "${abspath(path.module)}/.work/kubeconfig.yaml"
}

resource "local_sensitive_file" "kubeconfig" {
  content         = var.kubeconfig_raw
  filename        = local.kubeconfig_file
  file_permission = "0600"
}

resource "null_resource" "flux_install" {
  depends_on = [local_sensitive_file.kubeconfig]

  triggers = {
    kubeconfig_hash = sha256(var.kubeconfig_raw)
  }

  provisioner "local-exec" {
    command = "flux install --kubeconfig=${local.kubeconfig_file}"
  }
}

resource "null_resource" "flux_create_source" {
  depends_on = [null_resource.flux_install]

  triggers = {
    kubeconfig_hash = sha256(var.kubeconfig_raw)
    git_url         = var.git_url
    git_branch      = var.git_branch
  }

  provisioner "local-exec" {
    command = <<-EOT
      flux create source git flux-system \
        --kubeconfig=${local.kubeconfig_file} \
        --url=${var.git_url} \
        --branch=${var.git_branch} \
        --interval=1m
    EOT
  }
}

resource "null_resource" "cluster_config" {
  depends_on = [null_resource.flux_install]

  triggers = {
    kubeconfig_hash = sha256(var.kubeconfig_raw)
    base_domain     = var.base_domain
  }

  provisioner "local-exec" {
    command = <<-EOT
      kubectl --kubeconfig=${local.kubeconfig_file} create configmap cluster-config \
        --namespace=flux-system \
        --from-literal=base_domain=${var.base_domain} \
        --dry-run=client -o yaml | \
        kubectl --kubeconfig=${local.kubeconfig_file} apply -f -
    EOT
  }
}

resource "null_resource" "cluster_secrets" {
  depends_on = [null_resource.flux_install]

  triggers = {
    kubeconfig_hash          = sha256(var.kubeconfig_raw)
    zenith_token_signing_key = sha256(var.zenith_token_signing_key)
  }

  provisioner "local-exec" {
    command = <<-EOT
      kubectl --kubeconfig=${local.kubeconfig_file} create secret generic cluster-secrets \
        --namespace=flux-system \
        --from-literal=zenith_token_signing_key=${var.zenith_token_signing_key} \
        --dry-run=client -o yaml | \
        kubectl --kubeconfig=${local.kubeconfig_file} apply -f -
    EOT
  }
}

resource "null_resource" "flux_create_kustomization" {
  depends_on = [null_resource.flux_create_source, null_resource.cluster_config]

  triggers = {
    kubeconfig_hash = sha256(var.kubeconfig_raw)
    flux_path       = var.flux_path
  }

  provisioner "local-exec" {
    command = <<-EOT
      flux create kustomization flux-system \
        --kubeconfig=${local.kubeconfig_file} \
        --source=GitRepository/flux-system \
        --path="./${var.flux_path}" \
        --prune=true \
        --interval=10m
    EOT
  }
}
