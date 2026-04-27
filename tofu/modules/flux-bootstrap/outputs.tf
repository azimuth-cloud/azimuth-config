output "kubeconfig_path" {
  description = "Path to the kubeconfig file written by this module"
  value       = local_sensitive_file.kubeconfig.filename
}
