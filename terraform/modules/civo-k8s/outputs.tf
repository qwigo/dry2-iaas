output "cluster_id" {
  description = "The ID of the Kubernetes cluster"
  value       = civo_kubernetes_cluster.main.id
}

output "cluster_name" {
  description = "The name of the Kubernetes cluster"
  value       = civo_kubernetes_cluster.main.name
}

output "api_endpoint" {
  description = "The API endpoint of the cluster"
  value       = civo_kubernetes_cluster.main.api_endpoint
}

output "kubeconfig" {
  description = "The kubeconfig for the cluster"
  value       = civo_kubernetes_cluster.main.kubeconfig
  sensitive   = true
}

output "master_ip" {
  description = "The master IP of the cluster"
  value       = civo_kubernetes_cluster.main.master_ip
}

output "dns_entry" {
  description = "The DNS entry for the cluster"
  value       = civo_kubernetes_cluster.main.dns_entry
}

output "status" {
  description = "Status of the cluster"
  value       = civo_kubernetes_cluster.main.status
}

output "firewall_id" {
  description = "The ID of the firewall"
  value       = var.firewall_enabled ? civo_firewall.cluster_firewall[0].id : null
}




