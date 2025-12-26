"""Configuration management utilities."""

from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Project configuration manager."""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Find project root by looking for .git or specific markers
            current = Path.cwd()
            while current != current.parent:
                if (current / ".git").exists() or (current / ".dry2").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                project_root = Path.cwd()
        
        self.project_root = Path(project_root)
        self.dry2_dir = self.project_root / ".dry2"
        self.projects_dir = self.dry2_dir / "projects"
        self.helm_dir = self.project_root / "helm"
        self.config_file = self.project_root / ".dry2.yaml"
    
    def load_project_config(self, project_name: str) -> dict:
        """Load configuration for a specific project."""
        project_dir = self.projects_dir / project_name
        config_file = project_dir / "config.yaml"
        
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return {}
    
    def save_project_config(self, project_name: str, config: dict):
        """Save project configuration."""
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        config_file = project_dir / "config.yaml"
        
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def list_projects(self) -> list[str]:
        """List all configured projects."""
        if not self.projects_dir.exists():
            return []
        
        return [
            d.name for d in self.projects_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
    
    def list_environments(self, project_name: str) -> list[str]:
        """List all environments for a project."""
        project_dir = self.projects_dir / project_name
        if not project_dir.exists():
            return []
        
        return [
            d.name for d in project_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and (d / "main.tf").exists()
        ]
    
    def get_env_dir(self, project_name: str, environment: str) -> Path:
        """Get the directory for a specific environment."""
        return self.projects_dir / project_name / environment
    
    def ensure_project_structure(self):
        """Ensure basic project structure exists."""
        self.dry2_dir.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)
        self.helm_dir.mkdir(exist_ok=True)


REGIONS = {
    "NYC1": {"name": "New York", "upstash": "us-east-1"},
    "LON1": {"name": "London", "upstash": "eu-west-1"},
    "FRA1": {"name": "Frankfurt", "upstash": "eu-central-1"},
    "PHX1": {"name": "Phoenix", "upstash": "us-west-1"},
}

NODE_SIZES = {
    "small": {
        "size": "g4s.kube.small",
        "count": 2,
        "media_gb": 50,
        "static_gb": 20,
        "redis_mb": 256,
        "min_replicas": 1,
        "max_replicas": 3,
    },
    "medium": {
        "size": "g4s.kube.medium",
        "count": 3,
        "media_gb": 100,
        "static_gb": 30,
        "redis_mb": 512,
        "min_replicas": 2,
        "max_replicas": 5,
    },
    "large": {
        "size": "g4s.kube.large",
        "count": 5,
        "media_gb": 500,
        "static_gb": 100,
        "redis_mb": 1024,
        "min_replicas": 3,
        "max_replicas": 15,
    },
}

ENVIRONMENT_PROFILES = {
    "dev": "small",
    "staging": "medium",
    "production": "large",
}


