"""Deployment commands."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm

from ..utils.config import Config
from ..utils.terraform import Terraform

console = Console()


@click.group(name="deploy")
def deploy_group():
    """Deploy infrastructure and applications."""
    pass


@deploy_group.command(name="infra")
@click.argument("project_name")
@click.argument("environment")
@click.option("--auto-approve", "-y", is_flag=True, help="Skip confirmation")
@click.option("--upgrade", is_flag=True, help="Upgrade provider plugins")
def deploy_infrastructure(project_name, environment, auto_approve, upgrade):
    """
    Deploy infrastructure for an environment.

    This runs terraform init, plan, and apply.
    """
    config = Config()

    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        sys.exit(1)

    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        sys.exit(1)

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
        sys.exit(1)


@deploy_group.command(name="validate")
@click.argument("project_name")
@click.argument("environment")
def validate_configuration(project_name, environment):
    """Validate Terraform configuration."""
    config = Config()

    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        sys.exit(1)

    env_dir = config.get_env_dir(project_name, environment)

    console.print(f"[blue]Validating configuration for {project_name}/{environment}...[/blue]\n")

    tf = Terraform(env_dir)

    try:
        tf.init()
        tf.validate()
        console.print("\n[green]✅ Configuration is valid[/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Validation failed: {e}[/red]")
        sys.exit(1)


@deploy_group.command(name="plan")
@click.argument("project_name")
@click.argument("environment")
@click.option("--save", "-s", is_flag=True, help="Save plan to file")
def plan_infrastructure(project_name, environment, save):
    """Show what would be deployed without applying changes."""
    config = Config()

    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        sys.exit(1)

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
        sys.exit(1)
