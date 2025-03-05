"""
Script to create the project directory structure.
"""

import os
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure."""
    # Define the base directory structure
    structure = {
        "advanced_pmodeler": {
            "bin": {
                "windows": {
                    "run_analysis.bat": "",
                    "install.bat": "",
                    "README.md": "Windows installation and usage instructions"
                },
                "mac": {
                    "run_analysis.command": "",
                    "install.command": "",
                    "README.md": "Mac installation and usage instructions"
                }
            },
            "config": {
                "default_settings.json": "{}",
                "logging_config.json": "{}"
            },
            "data": {
                "templates": {
                    "scenario_template.xlsx": "",
                    "example_data.xlsx": "",
                    "README.md": "Template and example data documentation"
                },
                "output": {
                    "analysis": {},
                    "reports": {},
                    "charts": {}
                }
            },
            "docs": {
                "user_guide.md": "",
                "api_documentation.md": "",
                "examples.md": "",
                "README.md": "Documentation index"
            },
            "src": {
                "models": {
                    "__init__.py": "",
                    "base_models.py": "",
                    "financial_models.py": "",
                    "optimization_models.py": ""
                },
                "services": {
                    "__init__.py": "",
                    "financial_service.py": "",
                    "optimization_service.py": "",
                    "scenario_service.py": "",
                    "spreadsheet_service.py": "",
                    "template_service.py": "",
                    "visualization_service.py": ""
                },
                "utils": {
                    "__init__.py": "",
                    "config.py": "",
                    "logging.py": "",
                    "validation.py": ""
                }
            },
            "tests": {
                "__init__.py": "",
                "test_financial_service.py": "",
                "test_optimization_service.py": "",
                "test_scenario_service.py": "",
                "test_spreadsheet_service.py": "",
                "test_template_service.py": ""
            },
            "requirements": {
                "base.txt": "",
                "dev.txt": "",
                "spreadsheet.txt": "",
                "visualization.txt": ""
            },
            ".gitignore": "",
            "README.md": "Project overview and setup instructions",
            "setup.py": "",
            "LICENSE": ""
        }
    }
    
    def create_structure(base_path, structure):
        """Recursively create the directory structure."""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # Create directory and recurse
                path.mkdir(parents=True, exist_ok=True)
                create_structure(path, content)
            else:
                # Create file with content
                path.write_text(content)
    
    # Create the structure in the current directory
    create_structure(Path.cwd(), structure)
    
    # Create README.md content
    readme_content = """# Advanced Process Modeler

A comprehensive financial modeling and optimization tool for manufacturing expansion scenarios.

## Directory Structure

- `bin/`: Platform-specific executables and scripts
  - `windows/`: Windows-specific scripts
  - `mac/`: Mac-specific scripts
- `config/`: Configuration files
- `data/`: Data files
  - `templates/`: Excel templates and example data
  - `output/`: Generated analysis files
- `docs/`: Documentation
- `src/`: Source code
  - `models/`: Data models
  - `services/`: Business logic services
  - `utils/`: Utility functions
- `tests/`: Test files
- `requirements/`: Python package requirements

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/spreadsheet.txt
   ```

2. Run platform-specific installation script:
   - Windows: `bin/windows/install.bat`
   - Mac: `bin/mac/install.command`

## Usage

1. Open the Excel template from `data/templates/scenario_template.xlsx`
2. Fill in your scenario data
3. Click "Generate Analysis"
4. Find results in `data/output/`

## Development

1. Install development dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

2. Run tests:
   ```bash
   python -m pytest tests/
   ```
"""
    
    # Create setup.py content
    setup_content = """from setuptools import setup, find_packages

setup(
    name="advanced_pmodeler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "openpyxl>=3.1.2",
        "xlwings>=0.30.12",
        "google-auth>=2.22.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.1.1",
        "google-api-python-client>=2.95.0"
    ],
    entry_points={
        "console_scripts": [
            "pmodeler=src.cli:main",
        ],
    },
)
"""
    
    # Create .gitignore content
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
data/output/*
!data/output/.gitkeep
*.log
*.xlsx
!data/templates/*.xlsx
!data/example_data.xlsx

# Platform specific
.DS_Store
Thumbs.db
"""
    
    # Write additional files
    (Path.cwd() / "advanced_pmodeler" / "README.md").write_text(readme_content)
    (Path.cwd() / "advanced_pmodeler" / "setup.py").write_text(setup_content)
    (Path.cwd() / "advanced_pmodeler" / ".gitignore").write_text(gitignore_content)
    
    print("Directory structure created successfully!")

if __name__ == "__main__":
    create_directory_structure() 