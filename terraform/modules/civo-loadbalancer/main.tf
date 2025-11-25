terraform {
  required_providers {
    civo = {
      source  = "civo/civo"
      version = "~> 1.0"
    }
  }
}

# Load Balancer for the application
resource "civo_loadbalancer" "main" {
  hostname                   = var.hostname
  protocol                   = var.protocol
  tls_certificate            = var.tls_certificate
  tls_key                    = var.tls_key
  port                       = var.port
  max_request_size           = var.max_request_size
  algorithm                  = var.algorithm
  enable_proxy_protocol      = var.enable_proxy_protocol
  health_check_path          = var.health_check_path
  fail_timeout               = var.fail_timeout
  max_conns                  = var.max_conns
  ignore_invalid_backend_tls = var.ignore_invalid_backend_tls

  dynamic "backend" {
    for_each = var.backends
    content {
      ip               = backend.value.ip
      protocol         = backend.value.protocol
      source_port      = backend.value.source_port
      target_port      = backend.value.target_port
      health_check_port = backend.value.health_check_port
    }
  }

  firewall_id = var.firewall_id

  # Optional cluster association
  cluster_id = var.cluster_id
}


