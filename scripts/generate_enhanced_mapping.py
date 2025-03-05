#!/usr/bin/env python3
"""
Command-line script to generate enhanced model-service and model-database mapping reports.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import engine
from src.utils.enhanced_model_mapping import create_model_map

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Run enhanced analysis
        logger.info("Starting enhanced model analysis...")
        results = create_model_map(str(project_root), engine)
        
        # Log summary
        logger.info(f"\nAnalysis complete!")
        logger.info(f"Report generated at: {results['report_path']}")
        
        # Log statistics
        logger.info("\nStatistics:")
        logger.info(f"- Models analyzed: {len(results['models']['models'])}")
        logger.info(f"- Services analyzed: {len(results['services']['services'])}")
        logger.info(f"- Database tables analyzed: {len(results['schema']['tables'])}")
        logger.info(f"- Circular dependencies found: {len(results['services']['circular_deps'])}")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 