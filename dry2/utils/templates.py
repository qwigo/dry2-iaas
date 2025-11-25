"""Template generation utilities."""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import yaml

# Get templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class TemplateEngine:
    """Template rendering engine."""
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def render_to_file(self, template_name: str, output_path: Path, context: Dict[str, Any]):
        """Render a template and write to file."""
        content = self.render(template_name, context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)


def create_terraform_files(
    env_dir: Path,
    project_name: str,
    environment: str,
    config: Dict[str, Any],
):
    """Create Terraform configuration files."""
    engine = TemplateEngine()
    
    context = {
        "project_name": project_name,
        "environment": environment,
        **config,
    }
    
    # Create main.tf
    engine.render_to_file("terraform/main.tf.j2", env_dir / "main.tf", context)
    
    # Create variables.tf
    engine.render_to_file("terraform/variables.tf.j2", env_dir / "variables.tf", context)
    
    # Create outputs.tf
    engine.render_to_file("terraform/outputs.tf.j2", env_dir / "outputs.tf", context)
    
    # Create terraform.tfvars
    engine.render_to_file("terraform/terraform.tfvars.j2", env_dir / "terraform.tfvars", context)


def create_helm_values(
    output_path: Path,
    project_name: str,
    environment: str,
    config: Dict[str, Any],
):
    """Create Helm values file."""
    values = {
        "django": {
            "image": {
                "repository": f"ghcr.io/{config.get('github_repo', 'org/repo')}",
                "tag": "latest",
                "pullPolicy": "Always",
            },
            "replicas": {
                "min": config.get("min_replicas", 1),
                "max": config.get("max_replicas", 3),
            },
            "env": {
                "DJANGO_SETTINGS_MODULE": "config.settings.production",
                "ENVIRONMENT": environment,
                "ALLOWED_HOSTS": config.get("domain", f"{environment}.example.com"),
            },
            "ingress": {
                "enabled": True,
                "host": config.get("domain", f"{environment}.example.com"),
                "tls": {
                    "enabled": True,
                },
            },
        },
        "worker": {
            "replicas": {
                "min": config.get("min_replicas", 1),
                "max": config.get("max_replicas", 3),
            },
        },
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(values, f, default_flow_style=False, sort_keys=False)


def create_github_workflow(
    output_path: Path,
    project_name: str,
    github_repo: str,
    environments: list[str],
):
    """Create GitHub Actions workflow."""
    engine = TemplateEngine()
    
    context = {
        "project_name": project_name,
        "github_repo": github_repo,
        "environments": environments,
    }
    
    engine.render_to_file("github/deploy.yml.j2", output_path, context)


