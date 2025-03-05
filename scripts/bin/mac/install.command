#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"

# Make script executable
chmod +x "$SCRIPT_DIR/run_analysis.command"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$PROJECT_ROOT/venv"
source "$PROJECT_ROOT/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -r "$PROJECT_ROOT/requirements/base.txt"
pip install -r "$PROJECT_ROOT/requirements/spreadsheet.txt"
pip install -r "$PROJECT_ROOT/requirements/visualization.txt"

# Create output directories
echo "Creating output directories..."
mkdir -p "$PROJECT_ROOT/data/output/analysis"
mkdir -p "$PROJECT_ROOT/data/output/reports"
mkdir -p "$PROJECT_ROOT/data/output/charts"

# Set up Excel integration
echo "Setting up Excel integration..."
python "$PROJECT_ROOT/src/utils/setup_excel.py"

echo "Installation completed successfully!"
echo
echo "To use the tool:"
echo "1. Open data/templates/scenario_template.xlsx"
echo "2. Fill in your scenario data"
echo "3. Click 'Generate Analysis'"
echo "4. Find results in data/output/"
echo
read -p "Press Enter to continue..." 