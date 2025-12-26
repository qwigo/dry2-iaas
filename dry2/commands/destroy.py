"""Destroy infrastructure commands."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm

from ..utils.config import Config
from ..utils.terraform import Terraform

console = Console()


@click.group(name="destroy")
def destroy_group():
    """Destroy infrastructure."""
    pass


@destroy_group.command(name="env")
@click.argument("project_name")
@click.argument("environment")
@click.option("--auto-approve", "-y", is_flag=True, help="Skip confirmation")
@click.option("--keep-config/--no-keep-config", default=True, help="Keep configuration files")
def destroy_environment(project_name, environment, auto_approve, keep_config):
    """
    Destroy infrastructure for an environment.

    This will delete all cloud resources but can optionally keep the configuration.

    WARNING: This action cannot be undone!
    """
    config = Config()

    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        sys.exit(1)

    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        sys.exit(1)

    env_dir = config.get_env_dir(project_name, environment)

    # Check if infrastructure exists
    if not (env_dir / "terraform.tfstate").exists():
        console.print(f"[yellow]No infrastructure deployed for {environment}[/yellow]")
        return

    console.print(f"\n[bold red]⚠️  DESTROY INFRASTRUCTURE[/bold red]\n")
    console.print(f"Project: {project_name}")
    console.print(f"Environment: {environment}")
    console.print(f"Location: {env_dir}\n")

    console.print("[red]This will DELETE:[/red]")
    console.print("  • Kubernetes cluster and all workloads")
    console.print("  • Storage buckets and data")
    console.print("  • Redis database")
    console.print("  • Load balancers")
    console.print("\n[bold red]This action CANNOT be undone![/bold red]\n")

    if not auto_approve:
        # Extra confirmation for production
        if environment == "production":
            console.print("[bold red]You are about to destroy PRODUCTION![/bold red]\n")
            typed = click.prompt("Type 'destroy production' to confirm")
            if typed != "destroy production":
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(0)
        else:
            if not Confirm.ask(f"Are you sure you want to destroy {environment}?"):
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(0)

    tf = Terraform(env_dir)

    try:
        console.print("\n[red]Destroying infrastructure...[/red]\n")
        tf.destroy(auto_approve=True)

        # Remove kubeconfig
        kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-{environment}"
        if kubeconfig_path.exists():
            kubeconfig_path.unlink()
            console.print(f"[dim]Removed kubeconfig: {kubeconfig_path}[/dim]")

        if not keep_config:
            # Remove terraform state files
            for file in ["terraform.tfstate", "terraform.tfstate.backup", ".terraform", ".terraform.lock.hcl"]:
                path = env_dir / file
                if path.exists():
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        console.print("\n[green]✅ Infrastructure destroyed[/green]")

        if keep_config:
            console.print(f"\n[dim]Configuration files kept in: {env_dir}[/dim]")
            console.print(f"[dim]Redeploy anytime with: dry2 deploy infra {project_name} {environment}[/dim]\n")
        else:
            console.print("\n[dim]Configuration files can be regenerated with:[/dim]")
            console.print(f"[cyan]dry2 env add {project_name} {environment}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Destroy failed: {e}[/red]")
        console.print("\n[yellow]Manual cleanup may be required[/yellow]")
        console.print("[dim]Check Civo dashboard: https://dashboard.civo.com/[/dim]")
        sys.exit(1)


@destroy_group.command(name="project")
@click.argument("project_name")
@click.option("--auto-approve", "-y", is_flag=True, help="Skip confirmation")
def destroy_project(project_name, auto_approve):
    """
    Destroy ALL infrastructure for a project (all environments).

    WARNING: This will destroy EVERYTHING!
    """
    config = Config()

    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        sys.exit(1)

    environments = config.list_environments(project_name)

    console.print(f"\n[bold red]⚠️  DESTROY ENTIRE PROJECT[/bold red]\n")
    console.print(f"Project: {project_name}")
    console.print(f"Environments: {', '.join(environments)}\n")

    console.print("[red]This will DELETE ALL infrastructure for:[/red]")
    for env in environments:
        deployed = (config.get_env_dir(project_name, env) / "terraform.tfstate").exists()
        status = "🟢 Deployed" if deployed else "🔴 Not deployed"
        console.print(f"  • {env}: {status}")

    console.print("\n[bold red]This action CANNOT be undone![/bold red]\n")

    if not auto_approve:
        typed = click.prompt(f"Type '{project_name}' to confirm deletion")
        if typed != project_name:
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)

    # Destroy each environment
    for env in environments:
        env_dir = config.get_env_dir(project_name, env)

        if not (env_dir / "terraform.tfstate").exists():
            console.print(f"[dim]Skipping {env} (not deployed)[/dim]")
            continue

        console.print(f"\n[red]Destroying {env}...[/red]")

        try:
            tf = Terraform(env_dir)
            tf.destroy(auto_approve=True)
            console.print(f"[green]✓ {env} destroyed[/green]")
        except Exception as e:
            console.print(f"[red]Failed to destroy {env}: {e}[/red]")
            console.print("[yellow]Continuing with other environments...[/yellow]")

    console.print("\n[green]✅ Project infrastructure destroyed[/green]")
    console.print(f"\n[dim]Project configuration still exists at:[/dim]")
    console.print(f"[dim]{config.projects_dir / project_name}[/dim]\n")
