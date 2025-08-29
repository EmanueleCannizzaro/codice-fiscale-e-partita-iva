#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml for cloud deployment.

This script reads the dependencies from pyproject.toml and creates a requirements.txt
file compatible with cloud deployment platforms.
"""

import tomllib
from pathlib import Path


def generate_requirements():
    """Generate requirements.txt from pyproject.toml."""
    
    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    
    # Extract dependencies
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    
    # Cloud Run specific dependencies
    cloud_run_deps = [
        "functions-framework>=3.9.2",
        "gunicorn>=22.0.0",
        "uvicorn[standard]>=0.35.0",
    ]
    
    # Generate requirements.txt content
    content = [
        "# Requirements for Cloud Run deployment",
        "# Auto-generated from pyproject.toml",
        "",
        "# Core dependencies from pyproject.toml",
    ]
    
    for dep in dependencies:
        content.append(dep)
    
    content.extend([
        "",
        "# Cloud Run specific dependencies",
    ])
    
    for dep in cloud_run_deps:
        content.append(dep)
    
    # Write requirements.txt
    with open(requirements_path, "w") as f:
        f.write("\n".join(content))
        f.write("\n")
    
    print(f"✅ Generated {requirements_path}")
    print(f"📦 Found {len(dependencies)} core dependencies")
    print(f"☁️  Added {len(cloud_run_deps)} Cloud Run dependencies")


if __name__ == "__main__":
    generate_requirements()