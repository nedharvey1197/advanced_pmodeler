"""
Script to reorganize the current repository structure.
"""

import os
import shutil
from pathlib import Path

def reorganize_repository():
    """Reorganize the current repository structure."""
    # Get current directory
    root = Path.cwd()
    
    # Create new directory structure
    new_structure = {
        "src": {
            "models": {},
            "services": {},
            "utils": {},
            "web": {}  # For Streamlit apps
        },
        "config": {},
        "data": {
            "templates": {},
            "output": {
                "analysis": {},
                "reports": {},
                "charts": {}
            }
        },
        "docs": {},
        "tests": {},
        "scripts": {},
        "requirements": {}
    }
    
    # Create directories
    for dir_name, substructure in new_structure.items():
        dir_path = root / dir_name
        dir_path.mkdir(exist_ok=True)
        
        if substructure:
            for subdir_name, subsubstructure in substructure.items():
                subdir_path = dir_path / subdir_name
                subdir_path.mkdir(exist_ok=True)
                
                if subsubstructure:
                    for subsubdir_name in subsubstructure:
                        subsubdir_path = subdir_path / subsubdir_name
                        subsubdir_path.mkdir(exist_ok=True)
    
    # Move files to their new locations
    moves = [
        # Models
        (root / "models.py", root / "src" / "models" / "base_models.py"),
        (root / "models", root / "src" / "models"),
        
        # Services
        (root / "Services", root / "src" / "services"),
        
        # Utils
        (root / "Utils", root / "src" / "utils"),
        
        # Web apps
        (root / "streamlit_app.py", root / "src" / "web" / "streamlit_app.py"),
        (root / "streamlit_appII.py", root / "src" / "web" / "streamlit_appII.py"),
        (root / "main-app.py", root / "src" / "web" / "main_app.py"),
        
        # Templates
        (root / "templates", root / "data" / "templates"),
        
        # Scripts
        (root / "scripts", root / "scripts"),
        (root / "bin", root / "scripts" / "bin"),
        
        # Documentation
        (root / "readme.md", root / "docs" / "README.md"),
        (root / "INDEX.md", root / "docs" / "INDEX.md"),
        (root / "complete_architecture.md", root / "docs" / "architecture.md"),
        (root / "requirements.md", root / "docs" / "requirements.md"),
        
        # Requirements
        (root / "requirements.txt", root / "requirements" / "base.txt"),
        (root / "requirements_spreadsheet.txt", root / "requirements" / "spreadsheet.txt")
    ]
    
    # Perform moves
    for src, dst in moves:
        try:
            if src.exists():
                if src.is_dir():
                    # If destination exists and is a directory, merge contents
                    if dst.exists() and dst.is_dir():
                        for item in src.glob("*"):
                            shutil.move(str(item), str(dst / item.name))
                        src.rmdir()
                    else:
                        shutil.move(str(src), str(dst))
                else:
                    shutil.move(str(src), str(dst))
                print(f"Moved {src} to {dst}")
        except Exception as e:
            print(f"Error moving {src} to {dst}: {str(e)}")
    
    # Create new .gitignore
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

# Database
*.db

# Platform specific
.DS_Store
Thumbs.db
.specstory/
"""
    
    # Write .gitignore
    with open(root / ".gitignore", "w") as f:
        f.write(gitignore_content)
    
    # Create README.md if it doesn't exist in root
    if not (root / "README.md").exists():
        readme_content = """# Advanced Process Modeler

A comprehensive financial modeling and optimization tool for manufacturing expansion scenarios.

## Directory Structure

- `src/`: Source code
  - `models/`: Data models
  - `services/`: Business logic services
  - `utils/`: Utility functions
  - `web/`: Web applications (Streamlit)
- `config/`: Configuration files
- `data/`: Data files
  - `templates/`: Excel templates
  - `output/`: Generated files
- `docs/`: Documentation
- `tests/`: Test files
- `scripts/`: Scripts and tools
- `requirements/`: Python package requirements

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/spreadsheet.txt
   ```

2. Run the web application:
   ```bash
   streamlit run src/web/streamlit_app.py
   ```

## Development

1. Install all dependencies:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/spreadsheet.txt
   ```

2. Run tests:
   ```bash
   python -m pytest tests/
   ```
"""
        with open(root / "README.md", "w") as f:
            f.write(readme_content)
    
    print("Repository reorganization completed successfully!")

if __name__ == "__main__":
    reorganize_repository() 