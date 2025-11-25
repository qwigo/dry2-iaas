"""Deployment commands."""

import typer
from rich.console import Console
from rich.prompt import Confirm
from pathlib import Path

from ..utils.config import Config
from ..utils.terraform import Terraform

console = Console()
app = typer.Typer()


@app.command("infra")
def deploy_infrastructure(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="Skip confirmation"),
    upgrade: bool = typer.Option(False, "--upgrade", help="Upgrade provider plugins"),
):
    """
    Deploy infrastructure for an environment.
    
    This runs terraform init, plan, and apply.
    """
    config = Config()
    
    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        raise typer.Exit(1)
    
    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        raise typer.Exit(1)
    
    env_dir = config.get_env_dir(project_name, environment)
    
    console.print(f"[bold cyan]🚀 Deploying Infrastructure[/bold cyan]\n")
    console.print(f"Project: {project_name}")
    console.print(f"Environment: {environment}")
    console.print(f"Location: {env_dir}\n")
    
    tf = Terraform(env_dir)
    
    try:
        # Initialize
        tf.init(upgrade=upgrade)
        console.print()
        
        # Plan
        console.print("[yellow]Review the infrastructure plan:[/yellow]\n")
        plan_output = tf.plan()
        console.print(plan_output)
        console.print()
        
        # Apply
        if auto_approve or Confirm.ask("Apply this plan?"):
            tf.apply(auto_approve=True)
            
            # Save kubeconfig
            try:
                kubeconfig = tf.output("kubeconfig")
                if kubeconfig:
                    kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-{environment}"
                    kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
                    kubeconfig_path.write_text(kubeconfig)
                    console.print(f"\n[green]✓ Kubeconfig saved: {kubeconfig_path}[/green]")
            except:
                pass
            
            console.print("\n[bold green]✅ Infrastructure deployed successfully![/bold green]\n")
            console.print("[dim]View outputs with:[/dim]")
            console.print(f"[cyan]dry2 status infra {project_name} {environment}[/cyan]\n")
        else:
            console.print("[yellow]Deployment cancelled[/yellow]")
    
    except Exception as e:
        console.print(f"\n[red]❌ Deployment failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
def validate_configuration(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name"),
):
    """Validate Terraform configuration."""
    config = Config()
    
    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        raise typer.Exit(1)
    
    env_dir = config.get_env_dir(project_name, environment)
    
    console.print(f"[blue]Validating configuration for {project_name}/{environment}...[/blue]\n")
    
    tf = Terraform(env_dir)
    
    try:
        tf.init()
        tf.validate()
        console.print("\n[green]✅ Configuration is valid[/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("plan")
def plan_infrastructure(
    project_name: str = typer.Argument(..., help="Project name"),
    environment: str = typer.Argument(..., help="Environment name"),
    save: bool = typer.Option(False, "--save", "-s", help="Save plan to file"),
):
    """Show what would be deployed without applying changes."""
    config = Config()
    
    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        raise typer.Exit(1)
    
    env_dir = config.get_env_dir(project_name, environment)
    
    console.print(f"[blue]Planning infrastructure for {project_name}/{environment}...[/blue]\n")
    
    tf = Terraform(env_dir)
    
    try:
        tf.init()
        
        out_file = "tfplan" if save else None
        plan_output = tf.plan(out_file=out_file)
        
        console.print(plan_output)
        
        if save:
            console.print(f"\n[green]✓ Plan saved to: {env_dir}/tfplan[/green]")
            console.print(f"[dim]Apply with: dry2 deploy infra {project_name} {environment} --auto-approve[/dim]")
    
    except Exception as e:
        console.print(f"\n[red]❌ Planning failed: {e}[/red]")
        raise typer.Exit(1)


