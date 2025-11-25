output "bucket_id" {
  description = "The ID of the object store"
  value       = civo_object_store.bucket.id
}

output "bucket_name" {
  description = "The name of the bucket"
  value       = civo_object_store.bucket.name
}

output "bucket_url" {
  description = "The URL of the bucket"
  value       = civo_object_store.bucket.bucket_url
}

output "access_key_id" {
  description = "Access key ID for the bucket"
  value       = civo_object_store_credential.bucket_creds.access_key_id
  sensitive   = true
}

output "secret_access_key" {
  description = "Secret access key for the bucket"
  value       = civo_object_store_credential.bucket_creds.secret_access_key
  sensitive   = true
}

output "region" {
  description = "Region of the bucket"
  value       = civo_object_store.bucket.region
}

output "endpoint" {
  description = "S3-compatible endpoint for the bucket"
  value       = "https://objectstore.${var.region}.civo.com"
}

output "max_size_gb" {
  description = "Maximum size of the bucket in GB"
  value       = civo_object_store.bucket.max_size_gb
}




