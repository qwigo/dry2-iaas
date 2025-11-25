output "database_id" {
  description = "The ID of the Redis database"
  value       = upstash_redis_database.main.database_id
}

output "database_name" {
  description = "The name of the Redis database"
  value       = upstash_redis_database.main.database_name
}

output "endpoint" {
  description = "The endpoint of the Redis database"
  value       = upstash_redis_database.main.endpoint
}

output "port" {
  description = "The port of the Redis database"
  value       = upstash_redis_database.main.port
}

output "password" {
  description = "The password for the Redis database"
  value       = upstash_redis_database.main.password
  sensitive   = true
}

output "tls_enabled" {
  description = "Whether TLS is enabled"
  value       = upstash_redis_database.main.tls
}

output "region" {
  description = "The region of the Redis database"
  value       = upstash_redis_database.main.region
}

output "creation_time" {
  description = "Creation timestamp"
  value       = upstash_redis_database.main.creation_time
}

output "state" {
  description = "State of the database"
  value       = upstash_redis_database.main.state
}

output "redis_url" {
  description = "Full Redis connection URL"
  value       = "rediss://:${upstash_redis_database.main.password}@${upstash_redis_database.main.endpoint}:${upstash_redis_database.main.port}"
  sensitive   = true
}

output "django_redis_config" {
  description = "Redis configuration for Django RQ"
  value = {
    host     = upstash_redis_database.main.endpoint
    port     = upstash_redis_database.main.port
    password = upstash_redis_database.main.password
    ssl      = upstash_redis_database.main.tls
    db       = 0
  }
  sensitive = true
}




