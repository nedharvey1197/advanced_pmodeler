#!/usr/bin/env python3
"""
Script to initialize and validate the database schema.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models.base_models import init_database, validate_schema

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_result = init_database()
        logger.info(f"Initialization {init_result['status']}: {init_result['message']}")
        
        # Validate schema
        logger.info("\nValidating database schema...")
        errors = validate_schema()
        
        if errors:
            logger.warning("Schema validation found issues:")
            for error in errors:
                logger.warning(f"- {error}")
        else:
            logger.info("Schema validation successful - no issues found")
            
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 