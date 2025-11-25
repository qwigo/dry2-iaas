"""GitHub utilities."""

import subprocess
from typing import Optional
from rich.console import Console

console = Console()


class GitHubError(Exception):
    """GitHub operation failed."""
    pass


class GitHub:
    """GitHub CLI wrapper."""
    
    @staticmethod
    def is_installed() -> bool:
        """Check if GitHub CLI is installed."""
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if authenticated with GitHub."""
        try:
            subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def authenticate():
        """Authenticate with GitHub."""
        console.print("[blue]Authenticating with GitHub...[/blue]")
        try:
            subprocess.run(["gh", "auth", "login"], check=True)
            console.print("[green]✓ Authenticated with GitHub[/green]")
        except subprocess.CalledProcessError as e:
            raise GitHubError(f"GitHub authentication failed: {e}")
    
    @staticmethod
    def set_secret(name: str, value: str, repo: Optional[str] = None):
        """Set a GitHub secret."""
        cmd = ["gh", "secret", "set", name]
        if repo:
            cmd.extend(["-R", repo])
        
        try:
            subprocess.run(
                cmd,
                input=value,
                text=True,
                check=True,
                capture_output=True,
            )
            console.print(f"[green]✓ Set secret: {name}[/green]")
        except subprocess.CalledProcessError as e:
            raise GitHubError(f"Failed to set secret {name}: {e}")
    
    @staticmethod
    def get_current_repo() -> Optional[str]:
        """Get current repository in format owner/repo."""
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
            
            # Parse GitHub URL
            if "github.com" in url:
                # Handle both HTTPS and SSH URLs
                if url.startswith("https://"):
                    # https://github.com/owner/repo.git
                    parts = url.replace("https://github.com/", "").replace(".git", "")
                else:
                    # git@github.com:owner/repo.git
                    parts = url.split(":")[-1].replace(".git", "")
                return parts
        except:
            pass
        return None
    
    @staticmethod
    def create_workflow_dispatch(repo: str, workflow: str, ref: str = "main"):
        """Trigger a workflow dispatch event."""
        try:
            subprocess.run(
                [
                    "gh", "workflow", "run", workflow,
                    "-R", repo,
                    "--ref", ref,
                ],
                check=True,
            )
            console.print(f"[green]✓ Triggered workflow: {workflow}[/green]")
        except subprocess.CalledProcessError as e:
            raise GitHubError(f"Failed to trigger workflow: {e}")


