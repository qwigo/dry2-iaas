# Shared outputs that can be used across modules

output "resource_prefix" {
  description = "Standard prefix for resource naming"
  value       = "${var.project_name}-${var.environment}"
}

output "common_tags" {
  description = "Common tags merged with environment-specific tags"
  value = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  )
}




