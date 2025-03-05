#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python launcher
python3 "$SCRIPT_DIR/launch_analysis.py" "$1"

if [ $? -eq 0 ]; then
    echo "Analysis completed successfully"
    exit 0
else
    echo "Error running analysis"
    exit 1
fi 