output "cluster_id" {
  description = "Kubernetes cluster ID"
  value       = module.k8s_cluster.cluster_id
}

output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = module.k8s_cluster.cluster_name
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint"
  value       = module.k8s_cluster.api_endpoint
}

output "kubeconfig" {
  description = "Kubernetes config for kubectl access"
  value       = module.k8s_cluster.kubeconfig
  sensitive   = true
}

output "media_bucket_name" {
  description = "Media storage bucket name"
  value       = module.media_storage.bucket_name
}

output "media_bucket_url" {
  description = "Media storage bucket URL"
  value       = module.media_storage.bucket_url
}

output "static_bucket_name" {
  description = "Static files storage bucket name"
  value       = module.static_storage.bucket_name
}

output "static_bucket_url" {
  description = "Static files storage bucket URL"
  value       = module.static_storage.bucket_url
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis_cache.endpoint
}

output "redis_port" {
  description = "Redis port"
  value       = module.redis_cache.port
}

output "redis_url" {
  description = "Full Redis connection URL"
  value       = module.redis_cache.redis_url
  sensitive   = true
}

output "s3_credentials" {
  description = "S3 credentials for Django storage"
  value = {
    media_access_key_id      = module.media_storage.access_key_id
    media_secret_access_key  = module.media_storage.secret_access_key
    static_access_key_id     = module.static_storage.access_key_id
    static_secret_access_key = module.static_storage.secret_access_key
    endpoint_url             = module.media_storage.endpoint
    region                   = var.region
  }
  sensitive = true
}

output "redis_credentials" {
  description = "Redis credentials for Django"
  value       = module.redis_cache.django_redis_config
  sensitive   = true
}




