output "repository_files" {
  description = "Files committed to the Git repository by flux bootstrap"
  value       = flux_bootstrap_git.this.repository_files
}
