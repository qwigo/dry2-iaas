terraform {
  required_providers {
    upstash = {
      source  = "upstash/upstash"
      version = "~> 1.0"
    }
  }
}

resource "upstash_redis_database" "main" {
  database_name  = var.database_name
  region         = "global"
  primary_region = var.region
  tls            = var.tls_enabled
  eviction       = true
}

