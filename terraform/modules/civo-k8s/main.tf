terraform {
  required_providers {
    civo = {
      source  = "civo/civo"
      version = "~> 1.0"
    }
  }
}

# Firewall for the cluster
resource "civo_firewall" "cluster_firewall" {
  count = var.firewall_enabled ? 1 : 0

  name                 = "${var.cluster_name}-firewall"
  region               = var.region
  create_default_rules = false

  ingress_rule {
    label      = "kubernetes-api"
    protocol   = "tcp"
    port_range = "6443"
    cidr       = ["0.0.0.0/0"]
    action     = "allow"
  }

  ingress_rule {
    label      = "http"
    protocol   = "tcp"
    port_range = "80"
    cidr       = ["0.0.0.0/0"]
    action     = "allow"
  }

  ingress_rule {
    label      = "https"
    protocol   = "tcp"
    port_range = "443"
    cidr       = ["0.0.0.0/0"]
    action     = "allow"
  }

  egress_rule {
    label      = "all"
    protocol   = "tcp"
    port_range = "1-65535"
    cidr       = ["0.0.0.0/0"]
    action     = "allow"
  }
}

# Kubernetes cluster
resource "civo_kubernetes_cluster" "main" {
  name        = var.cluster_name
  region      = var.region
  cni         = var.cni
  firewall_id = var.firewall_enabled ? civo_firewall.cluster_firewall[0].id : null
  
  # Use kubernetes_version only if specified
  kubernetes_version = var.kubernetes_version

  dynamic "pools" {
    for_each = var.node_pools
    content {
      label      = pools.value.label
      size       = pools.value.size
      node_count = pools.value.node_count
    }
  }

  applications = join(",", var.applications)

  tags = join(",", [for k, v in var.tags : "${k}:${v}"])
  
  lifecycle {
    ignore_changes = [tags]
  }
}



