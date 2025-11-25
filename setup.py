from setuptools import setup, find_packages

setup(
    name="dry2-cli",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]>=0.12.0,<0.13.0",
        "click>=8.1.0,<8.1.8",
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "gitpython>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "dry2=dry2.cli:app",
        ],
    },
    python_requires=">=3.8",
    author="DRY2-IaaS",
    description="PaaS-style CLI for DRY2 Infrastructure as Code",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)

