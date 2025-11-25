terraform {
  required_version = ">= 1.5.0"

  required_providers {
    civo = {
      source  = "civo/civo"
      version = "~> 1.0"
    }
    upstash = {
      source  = "upstash/upstash"
      version = "~> 1.0"
    }
  }

  # Backend configuration - uncomment and configure for your setup
  # backend "s3" {
  #   bucket = "my-terraform-state"
  #   key    = "staging/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Providers
provider "civo" {
  token  = var.civo_token
  region = var.region
}

provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}

# Local variables
locals {
  environment     = "staging"
  project_name    = var.project_name
  resource_prefix = "${local.project_name}-${local.environment}"
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "Terraform"
    Workspace   = terraform.workspace
  }
}

# Kubernetes Cluster
module "k8s_cluster" {
  source = "../../modules/civo-k8s"

  cluster_name       = "${local.resource_prefix}-cluster"
  region             = var.region
  kubernetes_version = var.kubernetes_version
  cni                = "flannel"
  firewall_enabled   = true

  node_pools = var.node_pools

  applications = [
    "metrics-server",
    "cert-manager"
  ]

  tags = local.common_tags
}

# Media Storage Bucket
module "media_storage" {
  source = "../../modules/civo-storage"

  bucket_name = "${local.resource_prefix}-media"
  region      = var.region
  max_size_gb = var.media_bucket_size_gb

  tags = merge(local.common_tags, {
    Purpose = "media-files"
  })
}

# Static Files Storage Bucket
module "static_storage" {
  source = "../../modules/civo-storage"

  bucket_name = "${local.resource_prefix}-static"
  region      = var.region
  max_size_gb = var.static_bucket_size_gb

  tags = merge(local.common_tags, {
    Purpose = "static-files"
  })
}

# Redis Cache Database
module "redis_cache" {
  source = "../../modules/upstash-redis"

  database_name           = "${local.resource_prefix}-cache"
  region                  = var.upstash_region
  tls_enabled             = true
  max_memory_mb           = var.redis_max_memory_mb
  max_commands_per_second = var.redis_max_commands_per_second

  tags = merge(local.common_tags, {
    Purpose = "cache-rq"
  })
}



