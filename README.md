# DRY2-IaaS 🚀

**PaaS-style Infrastructure as Code for Django Applications**

Deploy your Django applications with a Heroku-like experience using modern cloud infrastructure. DRY2-IaaS combines Infrastructure as Code (Terraform), Kubernetes (Helm), and automated CI/CD workflows to give you a production-ready deployment platform.

## Features

- 🎯 **PaaS-like Experience** - Deploy Django apps with simple CLI commands
- ☁️ **Multi-Cloud Support** - Civo Kubernetes, Upstash Redis, and more
- 🔄 **GitOps Workflows** - Automated deployments via GitHub Actions
- 🌍 **Multi-Environment** - Dev, staging, and production environments out of the box
- 📦 **Helm Charts** - Pre-configured Kubernetes deployments with best practices
- 🔧 **Terraform Modules** - Reusable infrastructure components
- 📊 **Observability** - Built-in monitoring with Elastic Stack and Sentry
- 🔒 **Security** - Secrets management, RBAC, and network policies

## Prerequisites

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [Terraform](https://www.terraform.io/downloads) >= 1.0
- [Helm](https://helm.sh/docs/intro/install/) >= 3.0
- [kubectl](https://kubernetes.io/docs/tasks/tools/) for Kubernetes management
- A Civo account (for cloud infrastructure)
- A GitHub account (for CI/CD)

## Installation

### Install via Poetry from GitHub

You can install `dry2` directly from this GitHub repository using Poetry:

```bash
# Option 1: Install as a dependency in your project
poetry add git+https://github.com/qwigo/dry2-iaas.git

# Option 2: Clone and install for development
git clone https://github.com/qwigo/dry2-iaas.git
cd dry2-iaas
poetry install
poetry shell
```

### Install via pip from GitHub

Alternatively, you can use pip:

```bash
pip install git+https://github.com/qwigo/dry2-iaas.git
```

### Verify Installation

```bash
dry2 --version
dry2 --help
```

### Update Existing Installation

If you've already installed `dry2` and need to update to the latest version:

```bash
# Update with Poetry
poetry update dry2-cli

# Or reinstall
poetry remove dry2-cli
poetry add git+https://github.com/qwigo/dry2-iaas.git
```

## Quick Start

### 1. Initialize a New Project

```bash
# Navigate to your Django project directory
cd my-django-project

# Initialize DRY2-IaaS
dry2 init
```

This will guide you through an interactive setup process and create:
- `.dry2/` configuration directory
- Terraform configurations for your environments
- GitHub Actions workflows
- Helm values files

### 2. Create an Environment

```bash
# Create a development environment
dry2 env create dev

# Create staging and production environments
dry2 env create staging
dry2 env create production
```

### 3. Deploy Infrastructure

```bash
# Deploy the infrastructure for dev environment
dry2 deploy infra --env dev

# This provisions:
# - Kubernetes cluster on Civo
# - Redis on Upstash
# - Load balancers and storage
```

### 4. Deploy Your Application

```bash
# Deploy your Django application
dry2 deploy app --env dev

# This deploys:
# - Django web servers
# - Celery workers
# - Database migrations
# - Static file collection
```

### 5. Check Status

```bash
# Check the status of your deployment
dry2 status --env dev

# View specific components
dry2 status infra --env dev
dry2 status app --env dev
```

### 6. Automatic Deployments

Once set up, push to your repository to trigger automatic deployments:

```bash
# Push to dev branch -> deploys to dev environment
git push origin dev

# Push to staging branch -> deploys to staging
git push origin staging

# Push to main branch -> deploys to production
git push origin main
```

## CLI Commands

### `dry2 init`

Initialize a new DRY2-IaaS project. Creates configuration files and directory structure.

```bash
dry2 init [OPTIONS]
```

### `dry2 env`

Manage environments (dev, staging, production).

```bash
dry2 env create <environment>    # Create a new environment
dry2 env list                    # List all environments
dry2 env delete <environment>    # Delete an environment
```

### `dry2 deploy`

Deploy infrastructure or applications.

```bash
dry2 deploy infra --env <environment>    # Deploy infrastructure
dry2 deploy app --env <environment>      # Deploy application
dry2 deploy all --env <environment>      # Deploy everything
```

### `dry2 status`

Check deployment status.

```bash
dry2 status --env <environment>          # Overall status
dry2 status infra --env <environment>    # Infrastructure status
dry2 status app --env <environment>      # Application status
```

### `dry2 destroy`

Destroy infrastructure or applications.

```bash
dry2 destroy app --env <environment>     # Destroy application only
dry2 destroy infra --env <environment>   # Destroy infrastructure
dry2 destroy all --env <environment>     # Destroy everything
```

## Project Structure

```
dry2-iaas/
├── dry2/                         # DRY2 CLI Python package
│   ├── commands/                # CLI command implementations
│   ├── templates/               # Jinja2 templates
│   └── utils/                   # Utility functions
├── pyproject.toml               # Poetry configuration
├── setup.py                     # Setuptools configuration
├── requirements.txt             # Python dependencies
│
├── terraform/                    # Terraform configurations
│   ├── environments/            # Environment-specific configs
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   ├── modules/                 # Reusable Terraform modules
│   │   ├── civo-k8s/           # Civo Kubernetes cluster
│   │   ├── civo-loadbalancer/  # Load balancer configuration
│   │   ├── civo-storage/       # Persistent storage
│   │   └── upstash-redis/      # Upstash Redis instance
│   └── shared/                  # Shared configurations
│
└── helm/                         # Helm charts
    ├── django-app/              # Django application chart
    │   ├── templates/           # Kubernetes manifests
    │   └── values-*.yaml        # Environment-specific values
    └── observability/           # Monitoring stack
        ├── elastic-stack-values.yaml
        └── sentry-values.yaml
```

## Architecture

DRY2-IaaS provides a complete deployment pipeline:

1. **Infrastructure Layer** (Terraform)
   - Kubernetes cluster on Civo
   - Redis on Upstash
   - Load balancers and storage

2. **Application Layer** (Helm)
   - Django web servers with autoscaling
   - Celery workers for background tasks
   - PostgreSQL database
   - Redis cache

3. **Deployment Layer** (GitHub Actions)
   - Automated CI/CD pipelines
   - Environment-specific workflows
   - Automatic rollbacks on failure

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Civo Configuration
CIVO_API_KEY=your_civo_api_key
CIVO_REGION=NYC1

# Upstash Configuration
UPSTASH_EMAIL=your_email
UPSTASH_API_KEY=your_upstash_api_key

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# Django Configuration
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com
```

### Terraform Variables

Edit `terraform/environments/<env>/terraform.tfvars`:

```hcl
cluster_name = "my-app-dev"
cluster_nodes = 3
node_size = "g4s.kube.medium"
region = "NYC1"

redis_name = "my-app-redis-dev"
redis_region = "us-east-1"
```

### Helm Values

Customize `helm/django-app/values-<env>.yaml`:

```yaml
replicaCount: 3

image:
  repository: your-registry/your-app
  tag: latest

resources:
  limits:
    cpu: 1000m
    memory: 1024Mi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Support

- 📖 [Documentation](https://github.com/qwigo/dry2-iaas/wiki)
- 🐛 [Issue Tracker](https://github.com/qwigo/dry2-iaas/issues)
- 💬 [Discussions](https://github.com/qwigo/dry2-iaas/discussions)

## Roadmap

- [ ] AWS EKS support
- [ ] Google Cloud GKE support
- [ ] DigitalOcean Kubernetes support
- [ ] Built-in backup and restore
- [ ] Cost optimization recommendations
- [ ] Performance monitoring dashboard
- [ ] One-click SSL certificate management
- [ ] Database migration tooling

---

**Made with ❤️ by the DRY2-IaaS team**
