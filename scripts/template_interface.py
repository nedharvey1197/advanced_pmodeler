"""
Command-line interface for template-based scenario management.
"""

import argparse
import os
from pathlib import Path
from models import get_session
from Services.template_service import TemplateService

def main():
    parser = argparse.ArgumentParser(description="Template-based scenario management")
    parser.add_argument("action", choices=["create", "update", "generate", "template"],
                      help="Action to perform")
    parser.add_argument("--scenario-id", type=int, help="Scenario ID for update/generate/template")
    parser.add_argument("--template-file", required=True, help="Path to template file")
    parser.add_argument("--output-file", help="Path to output file")
    
    args = parser.parse_args()
    
    # Get database session
    session = get_session()
    
    # Initialize template service
    template_service = TemplateService(session)
    
    try:
        if args.action == "create":
            # Create new scenario from template
            result = template_service.create_scenario_from_template(args.template_file)
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Created scenario {result['scenario_id']}")
                print(f"Analysis file: {result['analysis_file']}")
        
        elif args.action == "update":
            if not args.scenario_id:
                print("Error: --scenario-id required for update")
                return
            
            # Update existing scenario from template
            result = template_service.update_scenario_from_template(
                args.scenario_id, args.template_file
            )
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Updated scenario {args.scenario_id}")
        
        elif args.action == "generate":
            if not args.scenario_id:
                print("Error: --scenario-id required for generate")
                return
            
            if not args.output_file:
                print("Error: --output-file required for generate")
                return
            
            # Generate analysis for scenario
            result = template_service.spreadsheet_service.create_scenario_dashboard(
                scenario_id=args.scenario_id,
                output_file=args.output_file,
                include_optimization=True
            )
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Generated analysis: {result['file_path']}")
        
        elif args.action == "template":
            if not args.scenario_id:
                print("Error: --scenario-id required for template")
                return
            
            if not args.output_file:
                print("Error: --output-file required for template")
                return
            
            # Create template from scenario
            result = template_service.create_template_from_scenario(
                args.scenario_id, args.output_file
            )
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Created template: {result['file_path']}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main() 