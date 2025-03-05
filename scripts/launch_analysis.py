"""
Platform-agnostic launcher for the analysis script.
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def get_python_path():
    """Get the path to the Python executable."""
    return sys.executable

def get_script_path():
    """Get the path to the template interface script."""
    return str(Path(__file__).parent / "template_interface.py")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Launch analysis with options")
    parser.add_argument("template_file", help="Path to the template file")
    parser.add_argument("--optimize", action="store_true", help="Include optimization analysis")
    parser.add_argument("--monte-carlo", action="store_true", help="Include Monte Carlo simulation")
    parser.add_argument("--sensitivity", action="store_true", help="Include sensitivity analysis")
    parser.add_argument("--charts", action="store_true", help="Generate charts")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF report")
    parser.add_argument("--google-sheets", action="store_true", help="Export to Google Sheets")
    return parser.parse_args()

def run_analysis(args):
    """Run the analysis script with the given options."""
    try:
        # Get paths
        python_path = get_python_path()
        script_path = get_script_path()
        
        # Build command
        cmd = [
            python_path,
            script_path,
            "create",
            "--template-file",
            args.template_file
        ]
        
        # Add options
        if args.optimize:
            cmd.extend(["--optimize"])
        if args.monte_carlo:
            cmd.extend(["--monte-carlo"])
        if args.sensitivity:
            cmd.extend(["--sensitivity"])
        if args.charts:
            cmd.extend(["--charts"])
        if args.pdf:
            cmd.extend(["--pdf"])
        if args.google_sheets:
            cmd.extend(["--google-sheets"])
        
        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Return success/failure
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    args = parse_args()
    success = run_analysis(args)
    sys.exit(0 if success else 1) 