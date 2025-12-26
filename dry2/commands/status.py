"""Status and monitoring commands."""

import json
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..utils.config import Config
from ..utils.github import GitHub
from ..utils.terraform import Terraform

console = Console()


@click.group(name="status")
def status_group():
    """Check deployment status."""
    pass


@status_group.command(name="project")
@click.argument("project_name")
def show_status(project_name):
    """Show status overview for a project."""
    config = Config()

    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        sys.exit(1)

    project_config = config.load_project_config(project_name)
    environments = config.list_environments(project_name)

    console.print(f"\n[bold cyan]📊 Project Status: {project_name}[/bold cyan]\n")

    # Project info
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("GitHub", project_config.get("github_repo", "N/A"))
    info_table.add_row("Region", project_config.get("region", "N/A"))
    info_table.add_row("Environments", str(len(environments)))

    console.print(info_table)
    console.print()

    # Environments table
    env_table = Table(title="Environments")
    env_table.add_column("Environment", style="cyan")
    env_table.add_column("Status", style="white")
    env_table.add_column("Branch", style="yellow")
    env_table.add_column("Domain", style="blue")
    env_table.add_column("Resources", style="green")

    for env in sorted(environments):
        env_dir = config.get_env_dir(project_name, env)
        env_config = project_config.get("environments", {}).get(env, {})

        # Check deployment status
        if (env_dir / "terraform.tfstate").exists():
            status = "🟢 Deployed"

            # Count resources
            try:
                state_file = env_dir / "terraform.tfstate"
                with open(state_file) as f:
                    state = json.load(f)
                    resource_count = len(state.get("resources", []))
                resources = str(resource_count)
            except:
                resources = "?"
        else:
            status = "🔴 Not deployed"
            resources = "0"

        branch = env_config.get("branch", "N/A")
        domain = project_config.get("domains", {}).get(env, "N/A")

        env_table.add_row(env, status, branch, domain, resources)

    console.print(env_table)
    console.print()

    # Quick actions
    console.print("[bold]Quick Actions:[/bold]")
    console.print(f"  • View environment: [cyan]dry2 env info {project_name} <env>[/cyan]")
    console.print(f"  • Deploy: [cyan]dry2 deploy infra {project_name} <env>[/cyan]")
    console.print(f"  • Add environment: [cyan]dry2 env add {project_name} <name>[/cyan]")
    console.print()


@status_group.command(name="infra")
@click.argument("project_name")
@click.argument("environment")
def infrastructure_status(project_name, environment):
    """Show infrastructure status and outputs."""
    config = Config()

    if environment not in config.list_environments(project_name):
        console.print(f"[red]Environment '{environment}' not found[/red]")
        sys.exit(1)

    env_dir = config.get_env_dir(project_name, environment)

    console.print(f"\n[bold cyan]📊 Infrastructure Status[/bold cyan]\n")
    console.print(f"Project: {project_name}")
    console.print(f"Environment: {environment}\n")

    # Check if deployed
    if not (env_dir / "terraform.tfstate").exists():
        console.print("[yellow]⚠ Infrastructure not deployed yet[/yellow]")
        console.print(f"\n[dim]Deploy with:[/dim]")
        console.print(f"[cyan]dry2 deploy infra {project_name} {environment}[/cyan]\n")
        return

    tf = Terraform(env_dir)

    try:
        # Get outputs
        outputs = tf.get_outputs()

        if not outputs:
            console.print("[yellow]No outputs available[/yellow]")
            return

        # Create outputs table
        table = Table(title="Terraform Outputs")
        table.add_column("Output", style="cyan")
        table.add_column("Value", style="white")

        for key, value in sorted(outputs.items()):
            # Handle sensitive values
            if any(s in key.lower() for s in ["password", "key", "secret", "token", "kubeconfig"]):
                display_value = "[dim]<sensitive>[/dim]"
            else:
                display_value = str(value)
                # Truncate long values
                if len(display_value) > 60:
                    display_value = display_value[:57] + "..."

            table.add_row(key, display_value)

        console.print(table)
        console.print()

        # Show kubeconfig location
        kubeconfig_path = Path.home() / ".kube" / f"config-{project_name}-{environment}"
        if kubeconfig_path.exists():
            console.print(f"[green]✓ Kubeconfig: {kubeconfig_path}[/green]")
            console.print(f"[dim]Access cluster:[/dim]")
            console.print(f"[cyan]export KUBECONFIG={kubeconfig_path}[/cyan]")
            console.print(f"[cyan]kubectl get nodes[/cyan]\n")

    except Exception as e:
        console.print(f"[red]Failed to get outputs: {e}[/red]")
        sys.exit(1)


@status_group.command(name="github")
@click.argument("project_name")
def github_status(project_name):
    """Check GitHub Actions workflow status."""
    config = Config()

    if project_name not in config.list_projects():
        console.print(f"[red]Project '{project_name}' not found[/red]")
        sys.exit(1)

    project_config = config.load_project_config(project_name)
    github_repo = project_config.get("github_repo")

    if not github_repo:
        console.print("[yellow]No GitHub repository configured[/yellow]")
        return

    console.print(f"\n[bold cyan]GitHub Status[/bold cyan]\n")
    console.print(f"Repository: {github_repo}")
    console.print(f"Actions: https://github.com/{github_repo}/actions\n")

    # Check if gh CLI is available
    if not GitHub.is_installed():
        console.print("[yellow]Install GitHub CLI for detailed status:[/yellow]")
        console.print("[dim]https://cli.github.com/[/dim]\n")
        return

    if not GitHub.is_authenticated():
        console.print("[yellow]Authenticate with GitHub CLI:[/yellow]")
        console.print("[cyan]gh auth login[/cyan]\n")
        return

    try:
        # Get recent workflow runs
        result = subprocess.run(
            ["gh", "run", "list", "-R", github_repo, "-L", "10"],
            capture_output=True,
            text=True,
            check=True,
        )

        console.print("[bold]Recent Deployments:[/bold]\n")
        console.print(result.stdout)

    except subprocess.CalledProcessError:
        console.print("[yellow]Could not fetch workflow status[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@status_group.command(name="list")
def list_projects():
    """List all projects."""
    config = Config()
    projects = config.list_projects()

    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        console.print("\n[dim]Create one with:[/dim]")
        console.print("[cyan]dry2 init project[/cyan]\n")
        return

    table = Table(title="Projects")
    table.add_column("Project", style="cyan")
    table.add_column("Environments", style="green")
    table.add_column("GitHub", style="blue")
    table.add_column("Region", style="yellow")

    for project in sorted(projects):
        project_config = config.load_project_config(project)
        environments = config.list_environments(project)

        table.add_row(
            project,
            str(len(environments)),
            project_config.get("github_repo", "N/A"),
            project_config.get("region", "N/A"),
        )

    console.print()
    console.print(table)
    console.print()
