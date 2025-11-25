"""Terraform utilities."""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console

console = Console()


class TerraformError(Exception):
    """Terraform command failed."""
    pass


class Terraform:
    """Terraform command wrapper."""
    
    def __init__(self, working_dir: Path):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, *args, capture_output=False, check=True) -> subprocess.CompletedProcess:
        """Run a terraform command."""
        cmd = ["terraform"] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise TerraformError(f"Terraform command failed: {e}")
    
    def init(self, upgrade: bool = False):
        """Initialize terraform."""
        console.print("[blue]Initializing Terraform...[/blue]")
        args = ["init", "-input=false"]
        if upgrade:
            args.append("-upgrade")
        self.run(*args)
        console.print("[green]✓ Terraform initialized[/green]")
    
    def plan(self, out_file: Optional[str] = None) -> str:
        """Run terraform plan."""
        console.print("[blue]Running Terraform plan...[/blue]")
        args = ["plan"]
        if out_file:
            args.extend(["-out", out_file])
        result = self.run(*args, capture_output=True)
        return result.stdout
    
    def apply(self, auto_approve: bool = False, plan_file: Optional[str] = None):
        """Apply terraform changes."""
        console.print("[blue]Applying Terraform changes...[/blue]")
        args = ["apply"]
        if auto_approve:
            args.append("-auto-approve")
        if plan_file:
            args.append(plan_file)
        self.run(*args)
        console.print("[green]✓ Infrastructure deployed![/green]")
    
    def destroy(self, auto_approve: bool = False):
        """Destroy terraform resources."""
        console.print("[red]Destroying infrastructure...[/red]")
        args = ["destroy"]
        if auto_approve:
            args.append("-auto-approve")
        self.run(*args)
        console.print("[yellow]Infrastructure destroyed[/yellow]")
    
    def output(self, name: Optional[str] = None, json_format: bool = False) -> Any:
        """Get terraform outputs."""
        args = ["output"]
        if json_format:
            args.append("-json")
        if name:
            args.append(name)
        
        result = self.run(*args, capture_output=True)
        
        if json_format:
            return json.loads(result.stdout)
        return result.stdout.strip()
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get all outputs as a dictionary."""
        try:
            outputs = self.output(json_format=True)
            return {k: v["value"] for k, v in outputs.items()}
        except:
            return {}
    
    def validate(self):
        """Validate terraform configuration."""
        console.print("[blue]Validating configuration...[/blue]")
        self.run("validate")
        console.print("[green]✓ Configuration valid[/green]")
    
    def fmt(self, check: bool = False):
        """Format terraform files."""
        args = ["fmt"]
        if check:
            args.append("-check")
        self.run(*args)
    
    def workspace_list(self) -> list[str]:
        """List terraform workspaces."""
        result = self.run("workspace", "list", capture_output=True)
        workspaces = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                # Remove * prefix from current workspace
                ws = line.lstrip("* ").strip()
                if ws:
                    workspaces.append(ws)
        return workspaces
    
    def workspace_select(self, name: str):
        """Select a terraform workspace."""
        self.run("workspace", "select", name)
    
    def workspace_new(self, name: str):
        """Create a new terraform workspace."""
        self.run("workspace", "new", name)


