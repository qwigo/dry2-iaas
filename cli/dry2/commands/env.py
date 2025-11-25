"""Environment management commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
import questionary

from ..utils.config import Config, NODE_SIZES
from ..utils.terraform import Terraform
from ..utils.github import GitHub
from ..utils.templates import create_terraform_files, create_helm_values

console = Console()
app = typer.Typer()


@app.command("list")
def list_environments(project_name: str = typer.Argument(..., help="Project name")):
    """List all environments for a project."""
    config = Config()
    
    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        raise typer.Exit(1)
    
    environments = config.list_environments(project_name)
    
    if not environments:
        console.print(f"[yellow]No environments found for project '{project_name}'[/yellow]")
        return
    
    table = Table(title=f"Environments for {project_name}")
    table.add_column("Environment", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Domain", style="blue")
    
    project_config = config.load_project_config(project_name)
    
    for env in sorted(environments):
        env_dir = config.get_env_dir(project_name, env)
        
        # Check if deployed
        status = "🟢 Deployed" if (env_dir / "terraform.tfstate").exists() else "🔴 Not deployed"
        
        # Get domain
        domain = project_config.get("domains", {}).get(env, f"{env}.example.com")
        
        table.add_row(env, status, domain)
    
    console.print(table)


@app.command("add")
def add_environment(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name (e.g., staging, demo)"),
    size: str = typer.Option("medium", "--size", "-s", help="Size profile: small, medium, or large"),
    branch: str = typer.Option(None, "--branch", "-b", help="Git branch name"),
    domain: str = typer.Option(None, "--domain", "-d", help="Domain for this environment"),
    deploy: bool = typer.Option(False, "--deploy", help="Deploy infrastructure immediately"),
):
    """
    Add a new environment to an existing project.
    
    Examples:
        dry2 env add myapp staging --size medium --branch staging
        dry2 env add myapp demo --size small --domain demo.example.com
    """
    config = Config()
    
    # Validate project exists
    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        console.print("[dim]Create it first with: dry2 init project[/dim]")
        raise typer.Exit(1)
    
    # Validate environment doesn't exist
    if environment in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' already exists[/red]")
        raise typer.Exit(1)
    
    # Validate size
    if size not in NODE_SIZES:
        console.print(f"[red]Invalid size: {size}[/red]")
        console.print(f"[dim]Available sizes: {', '.join(NODE_SIZES.keys())}[/dim]")
        raise typer.Exit(1)
    
    console.print(f"[bold cyan]➕ Adding Environment[/bold cyan]\n")
    console.print(f"Project: {project_name}")
    console.print(f"Environment: {environment}")
    console.print(f"Size: {size}\n")
    
    # Load project configuration
    project_config = config.load_project_config(project_name)
    
    # Prompt for missing info
    if not branch:
        branch = questionary.text(
            "Git branch name:",
            default=environment
        ).ask()
    
    if not domain:
        base_domain = project_config.get("domains", {}).get("production", "example.com")
        domain = questionary.text(
            "Domain:",
            default=f"{environment}.{base_domain}"
        ).ask()
    
    console.print(f"[green]✓[/green] Branch: {branch}")
    console.print(f"[green]✓[/green] Domain: {domain}\n")
    
    if not Confirm.ask("Create this environment?"):
        raise typer.Exit(0)
    
    # Create environment directory
    env_dir = config.get_env_dir(project_name, environment)
    env_dir.mkdir(parents=True, exist_ok=True)
    
    # Get size profile
    profile = NODE_SIZES[size]
    
    # Load credentials from existing environment
    source_env = "dev" if "dev" in config.list_environments(project_name) else config.list_environments(project_name)[0]
    source_config = config.load_project_config(project_name)
    credentials = source_config.get("credentials", {})
    
    # Create Terraform files
    console.print("[blue]Creating Terraform configuration...[/blue]")
    
    tf_config = {
        "civo_token": credentials.get("civo_token"),
        "upstash_email": credentials.get("upstash_email"),
        "upstash_api_key": credentials.get("upstash_api_key"),
        "region": project_config.get("region", "NYC1"),
        "upstash_region": project_config.get("upstash_region", "us-east-1"),
        "node_size": profile["size"],
        "node_count": profile["count"],
        "media_bucket_size_gb": profile["media_gb"],
        "static_bucket_size_gb": profile["static_gb"],
        "redis_max_memory_mb": profile["redis_mb"],
        "redis_max_commands_per_second": 10000,
    }
    
    create_terraform_files(env_dir, project_name, environment, tf_config)
    console.print("[green]✓ Terraform files created[/green]")
    
    # Create Helm values
    console.print("[blue]Creating Helm values...[/blue]")
    
    helm_config = {
        "github_repo": project_config.get("github_repo"),
        "domain": domain,
        "min_replicas": profile["min_replicas"],
        "max_replicas": profile["max_replicas"],
    }
    
    create_helm_values(env_dir / "values.yaml", project_name, environment, helm_config)
    console.print("[green]✓ Helm values created[/green]\n")
    
    # Update project config
    if "environments" not in project_config:
        project_config["environments"] = {}
    
    project_config["environments"][environment] = {
        "branch": branch,
        "profile": size,
    }
    
    if "domains" not in project_config:
        project_config["domains"] = {}
    project_config["domains"][environment] = domain
    
    config.save_project_config(project_name, project_config)
    
    # Deploy if requested
    if deploy:
        console.print("[bold cyan]━━━ Deploying Infrastructure ━━━[/bold cyan]\n")
        
        tf = Terraform(env_dir)
        
        try:
            tf.init()
            console.print()
            
            console.print("[yellow]Review the plan:[/yellow]\n")
            tf.plan()
            console.print()
            
            if Confirm.ask("Apply this plan?"):
                tf.apply(auto_approve=True)
                
                # Save kubeconfig
                outputs = tf.get_outputs()
                if "kubeconfig" in outputs:
                    kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-{environment}"
                    kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
                    kubeconfig_path.write_text(outputs["kubeconfig"])
                    console.print(f"\n[green]✓ Kubeconfig saved: {kubeconfig_path}[/green]")
                
                console.print("\n[green]✅ Infrastructure deployed![/green]\n")
        except Exception as e:
            console.print(f"[red]Deployment failed: {e}[/red]")
            console.print(f"[yellow]Deploy later with: dry2 deploy infra {project_name} {environment}[/yellow]\n")
    
    # Provide next steps
    console.print("[bold green]✅ Environment created![/bold green]\n")
    console.print("[bold]Next steps:[/bold]\n")
    console.print(f"1. Update your GitHub workflow to include the '{branch}' branch")
    console.print(f"2. Set GitHub secrets for '{environment}' environment")
    console.print(f"3. Create and push the '{branch}' branch:")
    console.print(f"   [cyan]git checkout -b {branch}[/cyan]")
    console.print(f"   [cyan]git push origin {branch}[/cyan]")
    console.print()


@app.command("remove")
def remove_environment(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove an environment (does not destroy infrastructure)."""
    config = Config()
    
    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        raise typer.Exit(1)
    
    # Prevent removing core environments
    if environment in ["dev", "production"]:
        console.print(f"[red]Cannot remove core environment: {environment}[/red]")
        console.print("[dim]Use 'dry2 destroy' to remove infrastructure[/dim]")
        raise typer.Exit(1)
    
    env_dir = config.get_env_dir(project_name, environment)
    
    # Check if infrastructure exists
    has_infra = (env_dir / "terraform.tfstate").exists()
    
    if has_infra:
        console.print(f"[yellow]⚠ Environment '{environment}' has deployed infrastructure[/yellow]")
        console.print(f"[dim]Destroy it first with: dry2 destroy {project_name} {environment}[/dim]\n")
    
    if not force:
        if not Confirm.ask(f"Remove environment '{environment}'?"):
            raise typer.Exit(0)
    
    # Remove directory
    import shutil
    shutil.rmtree(env_dir)
    
    # Update project config
    project_config = config.load_project_config(project_name)
    if "environments" in project_config and environment in project_config["environments"]:
        del project_config["environments"][environment]
    if "domains" in project_config and environment in project_config["domains"]:
        del project_config["domains"][environment]
    config.save_project_config(project_name, project_config)
    
    console.print(f"[green]✓ Environment '{environment}' removed[/green]")


@app.command("info")
def environment_info(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name"),
):
    """Show detailed information about an environment."""
    config = Config()
    
    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        raise typer.Exit(1)
    
    env_dir = config.get_env_dir(project_name, environment)
    project_config = config.load_project_config(project_name)
    env_config = project_config.get("environments", {}).get(environment, {})
    
    console.print(f"\n[bold cyan]{project_name} / {environment}[/bold cyan]\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Branch", env_config.get("branch", "N/A"))
    table.add_row("Profile", env_config.get("profile", "N/A"))
    table.add_row("Domain", project_config.get("domains", {}).get(environment, "N/A"))
    table.add_row("Directory", str(env_dir))
    
    # Check deployment status
    has_state = (env_dir / "terraform.tfstate").exists()
    table.add_row("Status", "🟢 Deployed" if has_state else "🔴 Not deployed")
    
    # Get terraform outputs if deployed
    if has_state:
        try:
            tf = Terraform(env_dir)
            outputs = tf.get_outputs()
            
            if outputs:
                table.add_row("", "")
                table.add_row("[bold]Outputs[/bold]", "")
                
                for key, value in outputs.items():
                    # Don't show sensitive values in full
                    if any(s in key.lower() for s in ["password", "key", "secret", "token"]):
                        display_value = "***"
                    else:
                        display_value = str(value)[:60]
                    table.add_row(f"  {key}", display_value)
        except:
            pass
    
    console.print(table)
    console.print()


