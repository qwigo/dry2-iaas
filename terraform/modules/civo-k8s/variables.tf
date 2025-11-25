variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
}

variable "region" {
  description = "Civo region"
  type        = string
  default     = "NYC1"
}

variable "node_pools" {
  description = "Configuration for Kubernetes node pools"
  type = list(object({
    label      = string
    size       = string
    node_count = number
  }))
  default = [{
    label      = "default"
    size       = "g4s.kube.medium"
    node_count = 3
  }]
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = null # Uses latest stable version
}

variable "cni" {
  description = "CNI plugin (flannel or cilium)"
  type        = string
  default     = "flannel"
  validation {
    condition     = contains(["flannel", "cilium"], var.cni)
    error_message = "CNI must be either flannel or cilium."
  }
}

variable "firewall_enabled" {
  description = "Enable firewall for the cluster"
  type        = bool
  default     = true
}

variable "applications" {
  description = "Marketplace applications to install"
  type        = list(string)
  default     = ["metrics-server"]
}

variable "tags" {
  description = "Tags to apply to the cluster"
  type        = map(string)
  default     = {}
}




