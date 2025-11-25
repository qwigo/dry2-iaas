variable "database_name" {
  description = "Name of the Redis database"
  type        = string
}

variable "region" {
  description = "Upstash region"
  type        = string
  default     = "us-east-1"
}

variable "tls_enabled" {
  description = "Enable TLS for Redis connection"
  type        = bool
  default     = true
}

variable "max_memory_mb" {
  description = "Maximum memory in MB (free tier: 256MB)"
  type        = number
  default     = 256
}

variable "max_commands_per_second" {
  description = "Maximum commands per second (free tier: 10000)"
  type        = number
  default     = 10000
}

variable "max_request_size_mb" {
  description = "Maximum request size in MB"
  type        = number
  default     = 1
}

variable "max_clients" {
  description = "Maximum number of concurrent clients"
  type        = number
  default     = 1000
}

variable "tags" {
  description = "Tags to apply to the database"
  type        = map(string)
  default     = {}
}



