#!/usr/bin/env python3
"""
Script to generate comprehensive model mapping documentation.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import engine
from src.utils.model_mapper import create_model_map

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Generate model map
        logger.info("Generating model map...")
        result = create_model_map(engine, str(project_root))
        
        # Log results
        logger.info(f"\nDocumentation generated at:")
        logger.info(f"- Markdown: {result['documentation']['markdown']}")
        logger.info(f"- JSON: {result['documentation']['json']}")
        
        # Log statistics
        model_map = result['map']
        logger.info("\nStatistics:")
        logger.info(f"- Tables mapped: {len(model_map['tables'])}")
        logger.info(f"- Models mapped: {len(model_map['models'])}")
        logger.info(f"- Services mapped: {len(model_map['services'])}")
        logger.info(f"- Relationships mapped: {len(model_map['relationships'])}")
        
        # Log errors if any
        if result['errors']:
            logger.warning("\nValidation errors found:")
            for error in result['errors']:
                logger.warning(f"- {error}")
        else:
            logger.info("\nNo validation errors found.")
            
    except Exception as e:
        logger.error(f"Error generating model map: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 