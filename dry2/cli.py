#!/usr/bin/env python3
"""
DRY2-IaaS CLI - PaaS-style infrastructure management
"""

import click
from rich.console import Console

from . import __version__
from .commands import init, env, deploy, status, destroy

console = Console()


@click.group()
@click.version_option(__version__, "-v", "--version", message="DRY2-IaaS CLI version %(version)s")
@click.pass_context
def app(ctx):
    """
    DRY2-IaaS PaaS CLI

    Deploy your Django applications like a PaaS:
    - Setup once with CLI
    - Push to deploy automatically
    - Add environments on demand
    """
    ctx.ensure_object(dict)


# Add commands and command groups
app.add_command(init.init_command, name="init")
app.add_command(env.env_group, name="env")
app.add_command(deploy.deploy_group, name="deploy")
app.add_command(status.status_group, name="status")
app.add_command(destroy.destroy_group, name="destroy")


def main():
    app()


if __name__ == "__main__":
    main()
