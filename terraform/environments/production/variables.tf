variable "civo_token" {
  description = "Civo API token"
  type        = string
  sensitive   = true
}

variable "upstash_email" {
  description = "Upstash account email"
  type        = string
  sensitive   = true
}

variable "upstash_api_key" {
  description = "Upstash API key"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "region" {
  description = "Civo region"
  type        = string
  default     = "NYC1"
}

variable "upstash_region" {
  description = "Upstash region"
  type        = string
  default     = "us-east-1"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = null
}

variable "node_pools" {
  description = "Kubernetes node pool configuration"
  type = list(object({
    label      = string
    size       = string
    node_count = number
  }))
  default = [
    {
      label      = "apps"
      size       = "g4s.kube.large"
      node_count = 3
    },
    {
      label      = "workers"
      size       = "g4s.kube.medium"
      node_count = 2
    }
  ]
}

variable "media_bucket_size_gb" {
  description = "Maximum size for media bucket in GB"
  type        = number
  default     = 500
}

variable "static_bucket_size_gb" {
  description = "Maximum size for static bucket in GB"
  type        = number
  default     = 100
}

variable "redis_max_memory_mb" {
  description = "Maximum memory for Redis in MB"
  type        = number
  default     = 1024
}

variable "redis_max_commands_per_second" {
  description = "Maximum Redis commands per second"
  type        = number
  default     = 100000
}



