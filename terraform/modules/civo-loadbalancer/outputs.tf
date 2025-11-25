output "id" {
  description = "The ID of the load balancer"
  value       = civo_loadbalancer.main.id
}

output "public_ip" {
  description = "The public IP address of the load balancer"
  value       = civo_loadbalancer.main.public_ip
}

output "private_ip" {
  description = "The private IP address of the load balancer"
  value       = civo_loadbalancer.main.private_ip
}

output "hostname" {
  description = "The hostname of the load balancer"
  value       = civo_loadbalancer.main.hostname
}

output "state" {
  description = "The state of the load balancer"
  value       = civo_loadbalancer.main.state
}

output "dns_entry" {
  description = "The DNS entry for the load balancer"
  value       = "${civo_loadbalancer.main.hostname} -> ${civo_loadbalancer.main.public_ip}"
}


