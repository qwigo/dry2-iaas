"""Initialize a new project with PaaS-style deployment."""

import base64
import secrets
import sys
from pathlib import Path

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from ..utils.config import Config, REGIONS, NODE_SIZES
from ..utils.github import GitHub
from ..utils.templates import create_terraform_files, create_helm_values, create_github_workflow
from ..utils.terraform import Terraform

console = Console()


@click.command(name="init")
@click.option("--name", "-n", "project_name", default=None, help="Project name")
@click.option("--skip-deploy", is_flag=True, help="Skip initial deployment")
def init_command(project_name, skip_deploy):
    """
    Initialize a new project with PaaS-style deployments.

    This will:
    - Create infrastructure configuration
    - Set up automatic deployments (main -> production, develop -> dev)
    - Deploy initial dev environment (optional)
    - Configure GitHub secrets
    """
    console.print(Panel.fit(
        "[bold cyan]🚀 DRY2-IaaS PaaS Setup[/bold cyan]\n\n"
        "Deploy like Heroku: Setup once, push to deploy\n\n"
        "[dim]• Push to main → production\n"
        "• Push to develop → dev\n"
        "• Add staging/custom environments anytime[/dim]",
        border_style="cyan"
    ))
    console.print()

    config = Config()
    config.ensure_project_structure()

    # Project name
    if not project_name:
        project_name = questionary.text(
            "Project name (lowercase, alphanumeric with hyphens):",
            validate=lambda x: x and x.replace("-", "").isalnum() and x.islower(),
        ).ask()

    if not project_name:
        console.print("[red]Project name is required[/red]")
        sys.exit(1)

    # Check if project exists
    if project_name in config.list_projects():
        if not Confirm.ask(f"Project '{project_name}' exists. Overwrite?"):
            sys.exit(0)

    console.print(f"[green]✓[/green] Project: {project_name}\n")

    # Detect if in Django app directory
    cwd = Path.cwd()
    is_django_app = (cwd / "manage.py").exists() or (cwd / "requirements.txt").exists()

    if is_django_app:
        console.print(f"[green]✓[/green] Detected Django application in current directory\n")

    # GitHub repository
    github_repo = GitHub.get_current_repo()
    if github_repo:
        console.print(f"[dim]Detected GitHub repo: {github_repo}[/dim]")
        if not Confirm.ask("Use this repository?", default=True):
            github_repo = None

    if not github_repo:
        github_org = questionary.text("GitHub organization/username:").ask()
        app_repo = questionary.text(
            "Application repository name:",
            default=project_name
        ).ask()
        github_repo = f"{github_org}/{app_repo}"

    console.print(f"[green]✓[/green] GitHub: {github_repo}\n")

    # Cloud configuration
    region_choice = questionary.select(
        "Select cloud region:",
        choices=[
            f"{k} - {v['name']}" for k, v in REGIONS.items()
        ],
        default="NYC1 - New York"
    ).ask()
    region = region_choice.split(" - ")[0]
    upstash_region = REGIONS[region]["upstash"]

    console.print(f"[green]✓[/green] Region: {region}\n")

    # Domain configuration
    prod_domain = questionary.text(
        "Production domain:",
        default=f"{project_name}.example.com"
    ).ask()
    dev_domain = questionary.text(
        "Dev domain:",
        default=f"dev.{prod_domain}"
    ).ask()

    console.print(f"[green]✓[/green] Domains configured\n")

    # Credentials note - not prompting anymore
    console.print("[bold]🔐 Credentials & Secrets[/bold]")
    console.print("[yellow]This CLI will NOT ask for credentials.[/yellow]")
    console.print("[dim]All credentials must be set manually as GitHub Secrets.[/dim]\n")
    console.print("[dim]After setup completes, you'll need to set these GitHub Secrets:[/dim]")
    console.print("[dim]  • {ENV}_CIVO_TOKEN - Get from https://dashboard.civo.com/security[/dim]")
    console.print("[dim]  • {ENV}_UPSTASH_EMAIL - Your Upstash account email[/dim]")
    console.print("[dim]  • {ENV}_UPSTASH_API_KEY - Get from https://console.upstash.com/[/dim]")
    console.print("[dim]  • {ENV}_DJANGO_SECRET_KEY - Generate with Python[/dim]")
    console.print("[dim]  • {ENV}_DATABASE_URL - Your database connection string[/dim]")
    console.print("[dim]  (Replace {ENV} with DEV, STAGING, or PRODUCTION)[/dim]\n")
    
    if not Confirm.ask("Ready to continue without entering credentials now?", default=True):
        sys.exit(0)
    
    console.print("[green]✓[/green] Will use GitHub Secrets for all credentials\n")

    # Summary
    console.print(Panel.fit(
        f"[bold]Configuration Summary[/bold]\n\n"
        f"Project: {project_name}\n"
        f"GitHub: {github_repo}\n"
        f"Region: {region}\n"
        f"Production: {prod_domain}\n"
        f"Dev: {dev_domain}\n\n"
        f"[yellow]⚠ IMPORTANT: Set GitHub Secrets before deploying![/yellow]\n"
        f"See GITHUB_SECRETS_SETUP.md for instructions\n\n"
        f"[dim]Auto-deployments:\n"
        f"  • main branch → production\n"
        f"  • develop branch → dev[/dim]",
        border_style="blue"
    ))
    console.print()

    if not Confirm.ask("Continue with this configuration?"):
        sys.exit(0)

    # Create infrastructure
    console.print("\n[bold cyan]━━━ Creating Infrastructure ━━━[/bold cyan]\n")

    project_dir = config.projects_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save project configuration (without credentials - they're in GitHub Secrets)
    project_config = {
        "name": project_name,
        "github_repo": github_repo,
        "region": region,
        "upstash_region": upstash_region,
        "domains": {
            "production": prod_domain,
            "dev": dev_domain,
        },
        "environments": {
            "production": {"branch": "main", "profile": "large"},
            "dev": {"branch": "develop", "profile": "small"},
        }
    }
    config.save_project_config(project_name, project_config)

    # Create environments (dev and production)
    for env_name, env_config in [("dev", "small"), ("production", "large")]:
        console.print(f"[blue]Creating {env_name} environment...[/blue]")

        env_dir = project_dir / env_name
        env_dir.mkdir(exist_ok=True)

        profile = NODE_SIZES[env_config]
        domain = dev_domain if env_name == "dev" else prod_domain

        tf_config = {
            "region": region,
            "upstash_region": upstash_region,
            "node_size": profile["size"],
            "node_count": profile["count"],
            "media_bucket_size_gb": profile["media_gb"],
            "static_bucket_size_gb": profile["static_gb"],
            "redis_max_memory_mb": profile["redis_mb"],
            "redis_max_commands_per_second": 10000,
        }

        create_terraform_files(env_dir, project_name, env_name, tf_config)

        helm_config = {
            "github_repo": github_repo,
            "domain": domain,
            "min_replicas": profile["min_replicas"],
            "max_replicas": profile["max_replicas"],
        }

        create_helm_values(env_dir / "values.yaml", project_name, env_name, helm_config)

        console.print(f"[green]✓ {env_name} environment created[/green]")

    console.print()

    # Skip initial deployment - requires GitHub Secrets to be set first
    console.print("\n[yellow]📋 Note: Initial deployment skipped[/yellow]")
    console.print("[dim]Infrastructure deployment requires GitHub Secrets to be set first.[/dim]")
    console.print("[dim]After setting secrets, deploy via GitHub Actions or manually with Terraform.[/dim]\n")

    # Setup GitHub Actions
    console.print("\n[bold cyan]━━━ Setting Up GitHub Actions ━━━[/bold cyan]\n")

    # Define environments with their branches
    workflow_environments = [
        {"name": "dev", "branch": "develop"},
        {"name": "production", "branch": "main"}
    ]

    # Copy to app repo if in one
    if is_django_app:
        import shutil
        
        # Create workflow file directly in app repo
        app_workflow_dir = cwd / ".github" / "workflows"
        app_workflow_dir.mkdir(parents=True, exist_ok=True)
        
        create_github_workflow(
            app_workflow_dir / "deploy.yml",
            project_name,
            github_repo,
            workflow_environments
        )
        console.print(f"[green]✓ Workflow created in application repo[/green]")
        console.print(f"[dim]Location: {app_workflow_dir / 'deploy.yml'}[/dim]\n")
    else:
        # Create workflow file in project config directory (for standalone use)
        workflow_dir = project_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        create_github_workflow(
            workflow_dir / "deploy.yml",
            project_name,
            github_repo,
            workflow_environments
        )

        console.print("[green]✓ Workflow created[/green]")
        console.print(f"[dim]Location: {workflow_dir / 'deploy.yml'}[/dim]\n")
        
        # Copy terraform files for each environment
        app_terraform_dir = cwd / ".dry2" / "terraform" / "environments"
        for env_name in ["dev", "production"]:
            src_env_dir = project_dir / env_name
            dest_env_dir = app_terraform_dir / env_name
            dest_env_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy terraform configuration files
            for tf_file in ["main.tf", "variables.tf", "outputs.tf"]:
                if (src_env_dir / tf_file).exists():
                    shutil.copy(src_env_dir / tf_file, dest_env_dir / tf_file)
            
            # Copy terraform.tfvars as .example (don't commit actual values)
            if (src_env_dir / "terraform.tfvars").exists():
                shutil.copy(src_env_dir / "terraform.tfvars", dest_env_dir / "terraform.tfvars.example")
            
            console.print(f"[green]✓ Terraform files copied for {env_name}[/green]")
        
        # Copy helm chart from dry2-iaas repo to app repo
        dry2_repo_root = Path(__file__).parent.parent.parent
        helm_src = dry2_repo_root / "helm" / "django-app"
        helm_dest = cwd / ".dry2" / "helm" / "django-app"
        
        if helm_src.exists():
            if helm_dest.exists():
                shutil.rmtree(helm_dest)
            shutil.copytree(helm_src, helm_dest)
            console.print(f"[green]✓ Helm chart copied to application repo[/green]")
        else:
            console.print(f"[yellow]⚠ Warning: Helm chart not found at {helm_src}[/yellow]")
        
        # Copy terraform modules from dry2-iaas repo to app repo
        modules_src = dry2_repo_root / "terraform" / "modules"
        modules_dest = cwd / ".dry2" / "terraform" / "modules"
        
        if modules_src.exists():
            if modules_dest.exists():
                shutil.rmtree(modules_dest)
            shutil.copytree(modules_src, modules_dest)
            console.print(f"[green]✓ Terraform modules copied to application repo[/green]")
        else:
            console.print(f"[yellow]⚠ Warning: Terraform modules not found at {modules_src}[/yellow]")
        
        # Create/update .gitignore to exclude sensitive terraform files
        gitignore_path = cwd / ".gitignore"
        gitignore_entries = [
            "\n# DRY2-IaaS - Terraform state and variables",
            ".dry2/terraform/.terraform/",
            ".dry2/terraform/**/.terraform/",
            ".dry2/terraform/**/*.tfstate",
            ".dry2/terraform/**/*.tfstate.backup",
            ".dry2/terraform/**/terraform.tfvars",
            ".dry2/terraform/**/.terraform.lock.hcl",
        ]
        
        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text()
        
        # Only add if not already present
        if "# DRY2-IaaS" not in existing_content:
            with gitignore_path.open("a") as f:
                f.write("\n".join(gitignore_entries) + "\n")
            console.print(f"[green]✓ Updated .gitignore with terraform exclusions[/green]\n")
        else:
            console.print(f"[dim]✓ .gitignore already configured[/dim]\n")

    # GitHub secrets instructions (not setting them automatically)
    console.print("\n[bold cyan]━━━ GitHub Secrets Setup Required ━━━[/bold cyan]\n")
    console.print("[yellow]⚠ You must manually set GitHub Secrets before deploying![/yellow]\n")
    
    console.print("[bold]Required secrets for each environment:[/bold]")
    console.print("  • {ENV}_CIVO_TOKEN")
    console.print("  • {ENV}_UPSTASH_EMAIL")
    console.print("  • {ENV}_UPSTASH_API_KEY")
    console.print("  • {ENV}_DJANGO_SECRET_KEY")
    console.print("  • {ENV}_DATABASE_URL\n")
    
    console.print("[dim]Quick setup example (for DEV environment):[/dim]")
    console.print("[cyan]gh secret set DEV_CIVO_TOKEN --body \"your-token\"[/cyan]")
    console.print("[cyan]gh secret set DEV_UPSTASH_EMAIL --body \"your-email\"[/cyan]")
    console.print("[cyan]gh secret set DEV_UPSTASH_API_KEY --body \"your-key\"[/cyan]")
    console.print("[cyan]gh secret set DEV_DJANGO_SECRET_KEY --body \"$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')\"[/cyan]")
    console.print("[cyan]gh secret set DEV_DATABASE_URL --body \"postgresql://...\"[/cyan]\n")
    
    console.print(f"[dim]📖 See detailed instructions: {project_dir / 'QUICK-REFERENCE.md'}[/dim]\n")

    # Final summary
    next_steps = (
        "[bold green]🎉 Setup Complete![/bold green]\n\n"
        "[bold]What's Next:[/bold]\n\n"
        "[yellow]1. Set up GitHub Secrets (REQUIRED BEFORE DEPLOYING):[/yellow]\n"
        f"   📖 Read: GITHUB_SECRETS_SETUP.md\n"
        f"   Or use GitHub UI: Settings → Secrets and variables → Actions\n\n"
        "2. Commit and push this configuration:\n"
        f"   [cyan]git add .[/cyan]\n"
        f"   [cyan]git commit -m \"Add DRY2-IaaS configuration\"[/cyan]\n"
        f"   [cyan]git push origin develop[/cyan]\n\n"
        "3. After setting secrets, push to deploy:\n"
        f"   [cyan]git push origin develop[/cyan] → Deploys to: {dev_domain}\n"
        f"   [cyan]git push origin main[/cyan] → Deploys to: {prod_domain}\n\n"
        "4. Check deployment status:\n"
        f"   GitHub Actions: https://github.com/{github_repo}/actions\n"
        f"   Or: [cyan]dry2 status {project_name}[/cyan]\n\n"
        "5. Add staging environment (optional):\n"
        f"   [cyan]dry2 env add {project_name} staging[/cyan]"
    )
    
    console.print(Panel.fit(
        next_steps,
        border_style="green",
        title="🚀 Configuration Created",
    ))

    # Create quick reference file
    quick_ref = project_dir / "QUICK-REFERENCE.md"
    quick_ref.write_text(f"""# {project_name} - Quick Reference

## 🔐 GitHub Secrets Required

Before deploying, ensure these secrets are set in your GitHub repository:

### Dev Environment
- `DEV_CIVO_TOKEN` - Civo API token
- `DEV_UPSTASH_EMAIL` - Upstash account email
- `DEV_UPSTASH_API_KEY` - Upstash API key
- `DEV_DJANGO_SECRET_KEY` - Django secret key
- `DEV_DATABASE_URL` - Database connection string

### Production Environment
- `PRODUCTION_CIVO_TOKEN` - Civo API token
- `PRODUCTION_UPSTASH_EMAIL` - Upstash account email
- `PRODUCTION_UPSTASH_API_KEY` - Upstash API key
- `PRODUCTION_DJANGO_SECRET_KEY` - Django secret key
- `PRODUCTION_DATABASE_URL` - Database connection string

**Quick setup:**
```bash
gh secret set DEV_CIVO_TOKEN --body "your-token"
gh secret set DEV_UPSTASH_EMAIL --body "your-email"
gh secret set DEV_UPSTASH_API_KEY --body "your-key"
gh secret set DEV_DJANGO_SECRET_KEY --body "$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
gh secret set DEV_DATABASE_URL --body "postgresql://..."
```

See [GITHUB_SECRETS_SETUP.md](../GITHUB_SECRETS_SETUP.md) for detailed instructions.

## 🚀 Deploy

```bash
# Deploy to dev
git push origin develop

# Deploy to production
git push origin main
```

## 📊 Status

```bash
# Check deployment status
dry2 status {project_name}

# View in GitHub
https://github.com/{github_repo}/actions
```

## 🔍 Access

- **Dev**: https://{dev_domain}
- **Production**: https://{prod_domain}

## 🐳 Kubernetes Access

```bash
# Dev
export KUBECONFIG=~/.kube/config-{project_name}-dev
kubectl get pods -n dev

# Production
export KUBECONFIG=~/.kube/config-{project_name}-production
kubectl get pods -n production
```

## ➕ Add Environment

```bash
dry2 env add {project_name} staging
```

## 🔧 Infrastructure

```bash
# Deploy infrastructure
dry2 deploy infra {project_name} dev

# View outputs
dry2 status infra {project_name} dev

# Destroy
dry2 destroy {project_name} dev
```
""")

    console.print(f"\n[dim]📖 Quick reference: {quick_ref}[/dim]\n")
