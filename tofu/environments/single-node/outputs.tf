output "seed_ip" {
  description = "Externally reachable IP of the seed node"
  value       = local.seed_ip
}

output "kubernetes_api_url" {
  description = "URL of the Kubernetes API server"
  value       = module.talos.host
}

output "kubeconfig_path" {
  description = "Local path where the kubeconfig was written"
  value       = local_sensitive_file.kubeconfig.filename
}

output "talosconfig_path" {
  description = "Local path where the talosconfig was written"
  value       = local_sensitive_file.talosconfig.filename
}

output "internal_network_id" {
  description = "Network ID created to host the seed VM"
  value = module.infra.network_id
}