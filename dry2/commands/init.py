"""Initialize a new project with PaaS-style deployment."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import secrets
import base64
import questionary

from ..utils.config import Config, REGIONS, NODE_SIZES, ENVIRONMENT_PROFILES
from ..utils.terraform import Terraform
from ..utils.github import GitHub
from ..utils.templates import create_terraform_files, create_helm_values, create_github_workflow

console = Console()
app = typer.Typer()


@app.command()
def project(
    project_name: str = typer.Option(None, "--name", "-n", help="Project name"),
    skip_deploy: bool = typer.Option(False, "--skip-deploy", help="Skip initial deployment"),
):
    """
    Initialize a new project with PaaS-style deployments.
    
    This will:
    - Create infrastructure configuration
    - Set up automatic deployments (main → production, develop → dev)
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
        raise typer.Exit(1)
    
    # Check if project exists
    if project_name in config.list_projects():
        if not Confirm.ask(f"Project '{project_name}' exists. Overwrite?"):
            raise typer.Exit(0)
    
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
    
    # Credentials
    console.print("[bold]🔐 Cloud Credentials[/bold]")
    console.print("[dim]Get your credentials from:[/dim]")
    console.print("[dim]  • Civo: https://dashboard.civo.com/security[/dim]")
    console.print("[dim]  • Upstash: https://console.upstash.com/[/dim]\n")
    
    civo_token = questionary.password("Civo API Token:").ask()
    upstash_email = questionary.text("Upstash Email:").ask()
    upstash_api_key = questionary.password("Upstash API Key:").ask()
    
    if not all([civo_token, upstash_email, upstash_api_key]):
        console.print("[red]All credentials are required[/red]")
        raise typer.Exit(1)
    
    console.print("[green]✓[/green] Credentials collected\n")
    
    # Database configuration
    console.print("[bold]💾 Database Configuration[/bold]")
    db_type = questionary.select(
        "Database type:",
        choices=[
            "PlanetScale (recommended)",
            "Other PostgreSQL",
            "Skip (configure later)"
        ]
    ).ask()
    
    db_url = None
    if "PlanetScale" in db_type or "PostgreSQL" in db_type:
        db_host = questionary.text("Database host:").ask()
        db_port = questionary.text("Database port:", default="3306" if "PlanetScale" in db_type else "5432").ask()
        db_name = questionary.text("Database name:").ask()
        db_user = questionary.text("Database username:").ask()
        db_pass = questionary.password("Database password:").ask()
        
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        console.print("[green]✓[/green] Database configured\n")
    else:
        console.print("[yellow]⚠[/yellow] Database skipped (configure later)\n")
    
    # Summary
    console.print(Panel.fit(
        f"[bold]Configuration Summary[/bold]\n\n"
        f"Project: {project_name}\n"
        f"GitHub: {github_repo}\n"
        f"Region: {region}\n"
        f"Production: {prod_domain}\n"
        f"Dev: {dev_domain}\n\n"
        f"[dim]Auto-deployments:\n"
        f"  • main branch → production\n"
        f"  • develop branch → dev[/dim]",
        border_style="blue"
    ))
    console.print()
    
    if not Confirm.ask("Continue with this configuration?"):
        raise typer.Exit(0)
    
    # Create infrastructure
    console.print("\n[bold cyan]━━━ Creating Infrastructure ━━━[/bold cyan]\n")
    
    project_dir = config.projects_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Save project configuration
    project_config = {
        "name": project_name,
        "github_repo": github_repo,
        "region": region,
        "upstash_region": upstash_region,
        "domains": {
            "production": prod_domain,
            "dev": dev_domain,
        },
        "credentials": {
            "civo_token": civo_token,
            "upstash_email": upstash_email,
            "upstash_api_key": upstash_api_key,
        },
        "database_url": db_url,
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
            "civo_token": civo_token,
            "upstash_email": upstash_email,
            "upstash_api_key": upstash_api_key,
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
    
    # Deploy dev environment
    if not skip_deploy:
        if Confirm.ask("Deploy dev environment now?"):
            console.print("\n[bold cyan]━━━ Deploying Dev Infrastructure ━━━[/bold cyan]\n")
            
            dev_dir = project_dir / "dev"
            tf = Terraform(dev_dir)
            
            try:
                tf.init()
                console.print()
                
                # Show plan
                console.print("[yellow]Review the infrastructure plan:[/yellow]\n")
                tf.plan()
                console.print()
                
                if Confirm.ask("Apply this plan?"):
                    tf.apply(auto_approve=True)
                    
                    # Save outputs
                    outputs = tf.get_outputs()
                    
                    # Save kubeconfig
                    if "kubeconfig" in outputs:
                        kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-dev"
                        kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
                        kubeconfig_path.write_text(outputs["kubeconfig"])
                        console.print(f"\n[green]✓ Kubeconfig saved: {kubeconfig_path}[/green]")
                    
                    console.print("\n[green]✅ Dev infrastructure deployed![/green]\n")
            except Exception as e:
                console.print(f"[red]Deployment failed: {e}[/red]")
                console.print("[yellow]You can deploy later with: dry2 deploy infra dev[/yellow]")
    
    # Setup GitHub Actions
    console.print("\n[bold cyan]━━━ Setting Up GitHub Actions ━━━[/bold cyan]\n")
    
    # Create workflow file
    workflow_dir = project_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    create_github_workflow(
        workflow_dir / "deploy.yml",
        project_name,
        github_repo,
        ["dev", "production"]
    )
    
    console.print("[green]✓ Workflow created[/green]")
    console.print(f"[dim]Location: {workflow_dir / 'deploy.yml'}[/dim]\n")
    
    # Copy to app repo if in one
    if is_django_app:
        app_workflow_dir = cwd / ".github" / "workflows"
        app_workflow_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(workflow_dir / "deploy.yml", app_workflow_dir / "deploy.yml")
        console.print(f"[green]✓ Workflow copied to application repo[/green]\n")
    
    # GitHub secrets setup
    if GitHub.is_installed():
        if not GitHub.is_authenticated():
            if Confirm.ask("Authenticate with GitHub to set secrets automatically?"):
                GitHub.authenticate()
        
        if GitHub.is_authenticated():
            console.print("[blue]Setting GitHub secrets...[/blue]\n")
            
            try:
                # Generate Django secret keys
                def generate_secret_key():
                    return secrets.token_urlsafe(50)
                
                # Set secrets for each environment
                for env_name in ["dev", "production"]:
                    console.print(f"[dim]Setting secrets for {env_name}...[/dim]")
                    
                    # Django secret key
                    secret_key = generate_secret_key()
                    GitHub.set_secret(f"{env_name}_DJANGO_SECRET_KEY", secret_key, github_repo)
                    
                    # Database URL
                    if db_url:
                        GitHub.set_secret(f"{env_name}_DATABASE_URL", db_url, github_repo)
                    
                    # Kubeconfig (if deployed)
                    kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-{env_name}"
                    if kubeconfig_path.exists():
                        kubeconfig_b64 = base64.b64encode(kubeconfig_path.read_bytes()).decode()
                        GitHub.set_secret(f"{env_name}_KUBECONFIG", kubeconfig_b64, github_repo)
                    
                    # Redis URL (from terraform outputs)
                    env_dir = project_dir / env_name
                    try:
                        tf = Terraform(env_dir)
                        redis_url = tf.output("redis_url")
                        if redis_url:
                            GitHub.set_secret(f"{env_name}_REDIS_URL", redis_url, github_repo)
                    except:
                        pass
                
                console.print("\n[green]✅ GitHub secrets configured![/green]\n")
            except Exception as e:
                console.print(f"[yellow]⚠ Could not set all secrets: {e}[/yellow]")
                console.print("[dim]Set them manually if needed[/dim]\n")
    else:
        console.print("[yellow]⚠ GitHub CLI not installed[/yellow]")
        console.print("[dim]Install from: https://cli.github.com/[/dim]\n")
    
    # Final summary
    console.print(Panel.fit(
        "[bold green]🎉 Setup Complete![/bold green]\n\n"
        "[bold]What's Next:[/bold]\n\n"
        "1. Push to develop branch:\n"
        f"   [cyan]git push origin develop[/cyan]\n"
        f"   → Deploys to: {dev_domain}\n\n"
        "2. Push to main for production:\n"
        f"   [cyan]git push origin main[/cyan]\n"
        f"   → Deploys to: {prod_domain}\n\n"
        "3. Check deployment status:\n"
        f"   [cyan]dry2 status {project_name}[/cyan]\n\n"
        "4. Add staging environment:\n"
        f"   [cyan]dry2 env add {project_name} staging[/cyan]",
        border_style="green",
        title="🚀 Ready to Deploy",
    ))
    
    # Create quick reference file
    quick_ref = project_dir / "QUICK-REFERENCE.md"
    quick_ref.write_text(f"""# {project_name} - Quick Reference

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


