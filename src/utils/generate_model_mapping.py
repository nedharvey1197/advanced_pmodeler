"""
Script to generate model-service and model-database mapping reports.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine
from ..models import Base, engine
from .model_mapping import ModelMapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_model_imports(models_dir: str) -> Dict[str, List[str]]:
    """
    Analyze model imports and dependencies.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        Dictionary mapping model names to their import issues
    """
    import_issues = {}
    model_files = [f for f in os.listdir(models_dir) 
                  if f.endswith('.py') and not f.startswith('__')]
    
    for model_file in model_files:
        model_name = model_file.replace('.py', '')
        import_issues[model_name] = []
        
        try:
            with open(os.path.join(models_dir, model_file), 'r') as f:
                content = f.read()
                
                # Check for base import
                if "from .base import Base" in content:
                    import_issues[model_name].append(
                        "Using deprecated '.base' import instead of '.base_models'"
                    )
                
                # Check for other potential import issues
                if "from ..models import" in content:
                    import_issues[model_name].append(
                        "Using relative import from parent directory"
                    )
        except Exception as e:
            import_issues[model_name].append(f"Error reading file: {str(e)}")
    
    return import_issues

def analyze_service_imports(services_dir: str) -> Dict[str, List[str]]:
    """
    Analyze service imports and dependencies.
    
    Args:
        services_dir: Directory containing service files
        
    Returns:
        Dictionary mapping service names to their import issues
    """
    import_issues = {}
    service_files = [f for f in os.listdir(services_dir) 
                    if f.endswith('.py') and not f.startswith('__')]
    
    for service_file in service_files:
        service_name = service_file.replace('.py', '')
        import_issues[service_name] = []
        
        try:
            with open(os.path.join(services_dir, service_file), 'r') as f:
                content = f.read()
                
                # Check for model imports
                if "from ..models import" in content:
                    import_issues[service_name].append(
                        "Using relative import from parent directory"
                    )
                
                # Check for circular imports
                if "from ." in content:
                    import_issues[service_name].append(
                        "Potential circular import detected"
                    )
        except Exception as e:
            import_issues[service_name].append(f"Error reading file: {str(e)}")
    
    return import_issues

def generate_report(import_issues: Dict[str, List[str]], 
                   service_issues: Dict[str, List[str]]) -> str:
    """
    Generate a detailed report of the issues found.
    
    Args:
        import_issues: Dictionary of model import issues
        service_issues: Dictionary of service import issues
        
    Returns:
        String containing the formatted report
    """
    report = []
    report.append("# Model and Service Analysis Report")
    report.append("=" * 50)
    
    # Model Issues
    report.append("\n## Model Import Issues")
    report.append("-" * 20)
    for model, issues in import_issues.items():
        if issues:
            report.append(f"\n### {model}")
            for issue in issues:
                report.append(f"- {issue}")
        else:
            report.append(f"\n### {model}")
            report.append("- No issues found")
    
    # Service Issues
    report.append("\n## Service Import Issues")
    report.append("-" * 20)
    for service, issues in service_issues.items():
        if issues:
            report.append(f"\n### {service}")
            for issue in issues:
                report.append(f"- {issue}")
        else:
            report.append(f"\n### {service}")
            report.append("- No issues found")
    
    return "\n".join(report)

def main():
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Analyze model imports
        logger.info("Analyzing model imports...")
        model_issues = analyze_model_imports(str(project_root / "src" / "models"))
        
        # Analyze service imports
        logger.info("Analyzing service imports...")
        service_issues = analyze_service_imports(str(project_root / "src" / "services"))
        
        # Generate report
        logger.info("Generating report...")
        report = generate_report(model_issues, service_issues)
        
        # Save report to file
        report_path = project_root / "docs" / "model_analysis_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Report generated at: {report_path}")
        
        # Log summary
        total_model_issues = sum(len(issues) for issues in model_issues.values())
        total_service_issues = sum(len(issues) for issues in service_issues.values())
        
        logger.info(f"\nSummary:")
        logger.info(f"- Total model issues found: {total_model_issues}")
        logger.info(f"- Total service issues found: {total_service_issues}")
        
        if total_model_issues + total_service_issues > 0:
            logger.warning("Issues were found. Please check the report for details.")
        else:
            logger.info("No issues found. All imports are correct.")
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 