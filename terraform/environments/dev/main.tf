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
  #   key    = "dev/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Providers
provider "civo" {
  # Uses CIVO_TOKEN environment variable automatically
  region = var.region
}

provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}

# Local variables
locals {
  environment     = "dev"
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

# Application Load Balancer (Optional)
# Uncomment if you need explicit load balancer control
# Note: Kubernetes Ingress automatically provisions a load balancer
# This is only needed for advanced configurations or non-K8s workloads
#
# module "app_loadbalancer" {
#   source = "../../modules/civo-loadbalancer"
#
#   hostname          = var.app_hostname
#   protocol          = "http"  # or "https" with TLS certificates
#   port              = 80
#   max_request_size  = 50  # MB
#   algorithm         = "round_robin"
#   health_check_path = "/health/"
#   fail_timeout      = 30
#   max_conns         = 100
#
#   # Backends will be your Kubernetes nodes
#   # Get node IPs from: kubectl get nodes -o wide
#   backends = [
#     {
#       ip                = "10.0.0.10"  # Replace with actual node IP
#       protocol          = "http"
#       source_port       = 80
#       target_port       = 30080  # NodePort service
#       health_check_port = 30080
#     }
#   ]
#
#   firewall_id = module.k8s_cluster.firewall_id
#   cluster_id  = module.k8s_cluster.cluster_id
#
#   tags = merge(local.common_tags, {
#     Purpose = "application-loadbalancer"
#   })
# }



