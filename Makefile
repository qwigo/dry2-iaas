.PHONY: help init plan apply destroy fmt validate lint test clean

# Default environment
ENV ?= dev

# Colors for output
CYAN := \033[0;36m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)dry2-iaas Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target] ENV=[dev|staging|production]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

init: ## Initialize Terraform
	@echo "$(CYAN)Initializing Terraform for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform init

plan: ## Run Terraform plan
	@echo "$(CYAN)Planning infrastructure for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform plan

apply: ## Apply Terraform changes
	@echo "$(CYAN)Applying infrastructure for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform apply

destroy: ## Destroy Terraform resources
	@echo "$(CYAN)Destroying infrastructure for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform destroy

fmt: ## Format Terraform files
	@echo "$(CYAN)Formatting Terraform files...$(NC)"
	terraform fmt -recursive terraform/

validate: ## Validate Terraform configuration
	@echo "$(CYAN)Validating Terraform configuration for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform validate

outputs: ## Show Terraform outputs
	@echo "$(CYAN)Terraform outputs for $(ENV):$(NC)"
	cd terraform/environments/$(ENV) && terraform output

kubeconfig: ## Save kubeconfig
	@echo "$(CYAN)Saving kubeconfig for $(ENV)...$(NC)"
	cd terraform/environments/$(ENV) && terraform output -raw kubeconfig > ~/.kube/config-$(ENV)
	@echo "Set KUBECONFIG=~/.kube/config-$(ENV)"

helm-lint: ## Lint Helm chart
	@echo "$(CYAN)Linting Helm chart...$(NC)"
	helm lint helm/django-app

helm-template: ## Template Helm chart
	@echo "$(CYAN)Templating Helm chart for $(ENV)...$(NC)"
	helm template django-app helm/django-app --values helm/django-app/values-$(ENV).yaml

helm-install: ## Install Helm chart
	@echo "$(CYAN)Installing Helm chart for $(ENV)...$(NC)"
	helm upgrade --install django-app helm/django-app \
		--namespace $(ENV) \
		--values helm/django-app/values-$(ENV).yaml \
		--create-namespace \
		--wait

helm-uninstall: ## Uninstall Helm chart
	@echo "$(CYAN)Uninstalling Helm chart for $(ENV)...$(NC)"
	helm uninstall django-app --namespace $(ENV)

k8s-status: ## Show Kubernetes status
	@echo "$(CYAN)Kubernetes status for $(ENV):$(NC)"
	kubectl get all -n $(ENV)

k8s-logs: ## Show application logs
	@echo "$(CYAN)Application logs for $(ENV):$(NC)"
	kubectl logs -n $(ENV) -l app.kubernetes.io/name=django-app --tail=100 -f

k8s-shell: ## Open shell in pod
	@echo "$(CYAN)Opening shell in pod...$(NC)"
	kubectl exec -it -n $(ENV) deployment/django-app -- /bin/bash

k8s-migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations for $(ENV)...$(NC)"
	kubectl exec -n $(ENV) deployment/django-app -- python manage.py migrate

k8s-shell-worker: ## Open shell in worker pod
	@echo "$(CYAN)Opening shell in worker pod...$(NC)"
	kubectl exec -it -n $(ENV) deployment/django-app-worker -- /bin/bash

docs: ## Generate documentation
	@echo "$(CYAN)Documentation available in docs/$(NC)"
	@ls -la docs/

test: ## Run tests
	@echo "$(CYAN)Running tests...$(NC)"
	$(MAKE) fmt
	$(MAKE) validate ENV=dev
	$(MAKE) helm-lint

clean: ## Clean temporary files
	@echo "$(CYAN)Cleaning temporary files...$(NC)"
	find . -name "*.tfstate" -type f -delete
	find . -name "*.tfstate.backup" -type f -delete
	find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".terraform.lock.hcl" -type f -delete
	rm -f terraform/environments/*/outputs.json

check-env: ## Check required environment variables
	@echo "$(CYAN)Checking environment variables...$(NC)"
	@if [ -z "$(TF_VAR_civo_token)" ]; then echo "❌ TF_VAR_civo_token not set"; else echo "✅ TF_VAR_civo_token set"; fi
	@if [ -z "$(TF_VAR_upstash_email)" ]; then echo "❌ TF_VAR_upstash_email not set"; else echo "✅ TF_VAR_upstash_email set"; fi
	@if [ -z "$(TF_VAR_upstash_api_key)" ]; then echo "❌ TF_VAR_upstash_api_key not set"; else echo "✅ TF_VAR_upstash_api_key set"; fi

setup-dev: ## Setup development environment
	@echo "$(CYAN)Setting up development environment...$(NC)"
	cp terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars
	@echo "📝 Edit terraform/environments/dev/terraform.tfvars with your credentials"

# Quick deployment shortcuts
dev-deploy: ## Quick deploy to dev
	$(MAKE) init ENV=dev
	$(MAKE) apply ENV=dev
	$(MAKE) kubeconfig ENV=dev

staging-deploy: ## Quick deploy to staging
	$(MAKE) init ENV=staging
	$(MAKE) apply ENV=staging
	$(MAKE) kubeconfig ENV=staging

prod-deploy: ## Quick deploy to production
	$(MAKE) init ENV=production
	$(MAKE) apply ENV=production
	$(MAKE) kubeconfig ENV=production




