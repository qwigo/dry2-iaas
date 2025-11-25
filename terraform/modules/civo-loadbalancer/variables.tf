variable "hostname" {
  description = "The hostname/domain for the load balancer"
  type        = string
}

variable "protocol" {
  description = "The protocol for the load balancer (http or https)"
  type        = string
  default     = "http"

  validation {
    condition     = contains(["http", "https", "tcp"], var.protocol)
    error_message = "Protocol must be either http, https, or tcp."
  }
}

variable "tls_certificate" {
  description = "TLS certificate content (required for https protocol)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "tls_key" {
  description = "TLS private key content (required for https protocol)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "port" {
  description = "The port the load balancer will listen on"
  type        = number
  default     = 80
}

variable "max_request_size" {
  description = "Maximum request size in MB"
  type        = number
  default     = 20
}

variable "algorithm" {
  description = "Load balancing algorithm (round_robin or least_conn)"
  type        = string
  default     = "round_robin"

  validation {
    condition     = contains(["round_robin", "least_conn"], var.algorithm)
    error_message = "Algorithm must be either round_robin or least_conn."
  }
}

variable "enable_proxy_protocol" {
  description = "Enable proxy protocol for backend connections"
  type        = bool
  default     = false
}

variable "health_check_path" {
  description = "Path for health checks"
  type        = string
  default     = "/"
}

variable "fail_timeout" {
  description = "Timeout in seconds for marking backend as failed"
  type        = number
  default     = 30
}

variable "max_conns" {
  description = "Maximum number of connections per backend"
  type        = number
  default     = 10
}

variable "ignore_invalid_backend_tls" {
  description = "Ignore invalid backend TLS certificates"
  type        = bool
  default     = false
}

variable "backends" {
  description = "List of backend configurations"
  type = list(object({
    ip                = string
    protocol          = string
    source_port       = number
    target_port       = number
    health_check_port = optional(number)
  }))
  default = []
}

variable "firewall_id" {
  description = "ID of the firewall to associate with the load balancer"
  type        = string
  default     = null
}

variable "cluster_id" {
  description = "ID of the Kubernetes cluster to associate with"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to the load balancer"
  type        = map(string)
  default     = {}
}


