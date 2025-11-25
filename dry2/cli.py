#!/usr/bin/env python3
"""
DRY2-IaaS CLI - PaaS-style infrastructure management
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

from .commands import init, env, deploy, status, destroy

console = Console()
app = typer.Typer(
    name="dry2",
    help="🚀 DRY2-IaaS PaaS CLI - Deploy like Heroku",
    add_completion=True,
)

# Add command groups
app.add_typer(init.app, name="init", help="Initialize a new project")
app.add_typer(env.app, name="env", help="Manage environments")
app.add_typer(deploy.app, name="deploy", help="Deploy infrastructure and applications")
app.add_typer(status.app, name="status", help="Check deployment status")
app.add_typer(destroy.app, name="destroy", help="Destroy infrastructure")


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """
    DRY2-IaaS PaaS CLI
    
    Deploy your Django applications like a PaaS:
    - Setup once with CLI
    - Push to deploy automatically
    - Add environments on demand
    """
    if version:
        from . import __version__
        console.print(f"DRY2-IaaS CLI version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()


