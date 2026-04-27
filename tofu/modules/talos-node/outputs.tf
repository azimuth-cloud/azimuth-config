output "machine_config" {
  description = "Talos machine configuration to inject as user_data into the VM"
  value       = data.talos_machine_configuration.controlplane.machine_configuration
  sensitive   = true
}


output "kubeconfig_raw" {
  description = "Kubeconfig for the provisioned cluster"
  value       = resource.talos_cluster_kubeconfig.this.kubeconfig_raw
  sensitive   = true
}

output "talosconfig" {
  description = "Talosconfig YAML"
  value       = data.talos_client_configuration.this.talos_config
  sensitive   = true
}

output "host" {
  description = "Kubernetes API server URL"
  value       = "https://${var.cluster_endpoint_ip}:${var.kubernetes_api_port}"
}
