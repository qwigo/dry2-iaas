variable "bucket_name" {
  description = "Name of the object storage bucket"
  type        = string
}

variable "region" {
  description = "Civo region"
  type        = string
  default     = "NYC1"
}

variable "access_key_id" {
  description = "Access key ID for the bucket (leave empty to generate)"
  type        = string
  default     = ""
}

variable "max_size_gb" {
  description = "Maximum size of the bucket in GB"
  type        = number
  default     = 500
}

variable "enable_versioning" {
  description = "Enable object versioning (simulated via lifecycle)"
  type        = bool
  default     = false
}

variable "lifecycle_rules" {
  description = "Lifecycle rules for the bucket"
  type = list(object({
    id                      = string
    enabled                 = bool
    prefix                  = string
    expiration_days         = number
    transition_days         = number
    transition_storage_class = string
  }))
  default = []
}

variable "cors_rules" {
  description = "CORS rules for the bucket"
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to the bucket"
  type        = map(string)
  default     = {}
}




