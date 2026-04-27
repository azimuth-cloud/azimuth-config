output "machine_config" {
  description = "Talos machine configuration to inject as user_data into the VM"
  value       = data.talos_machine_configuration.controlplane.machine_configuration
  sensitive   = true
}

output "client_configuration" {
  description = "Talos client configuration (talosconfig)"
  value       = talos_machine_secrets.this.client_configuration
  sensitive   = true
}

output "kubeconfig_raw" {
  description = "Kubeconfig for the provisioned cluster"
  value       = data.talos_cluster_kubeconfig.this.kubeconfig_raw
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Kubernetes cluster CA certificate (PEM)"
  value       = data.talos_cluster_kubeconfig.this.kubernetes_client_configuration.ca_certificate
  sensitive   = true
}

output "client_certificate" {
  description = "Kubernetes client certificate (PEM)"
  value       = data.talos_cluster_kubeconfig.this.kubernetes_client_configuration.client_certificate
  sensitive   = true
}

output "client_key" {
  description = "Kubernetes client key (PEM)"
  value       = data.talos_cluster_kubeconfig.this.kubernetes_client_configuration.client_key
  sensitive   = true
}

output "host" {
  description = "Kubernetes API server URL"
  value       = "https://${var.cluster_endpoint_ip}:${var.kubernetes_api_port}"
}
