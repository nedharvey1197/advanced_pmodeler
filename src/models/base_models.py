"""
Base models and session management for the manufacturing model.
"""

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Type, List
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get project root and data directory
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"

# Create database engine with correct path
engine = create_engine(f'sqlite:///{data_dir}/manufacturing_model.db')

# Create declarative base class for models
Base = declarative_base()

# Create session factory
Session = sessionmaker(bind=engine)

class ServiceMixin:
    """Mixin to add service management capabilities to any service class."""
    
    def _get_service(self, service_class: Type) -> Any:
        """
        Get or create a service instance.
        
        Args:
            service_class: The service class to instantiate
            
        Returns:
            Service instance
        """
        if not hasattr(self.session, '_services'):
            self.session._services = {}
            
        service_name = service_class.__name__.lower()
        if service_name not in self.session._services:
            self.session._services[service_name] = service_class(self.session)
        return self.session._services[service_name]

def validate_schema() -> List[str]:
    """
    Validate database schema against models.
    
    Returns:
        List of validation errors/warnings
    """
    inspector = inspect(engine)
    errors = []
    
    # Get all tables from models
    model_tables = Base.metadata.tables
    
    # Get all tables from database
    db_tables = inspector.get_table_names()
    
    # Check for missing tables
    for table_name in model_tables:
        if table_name not in db_tables:
            errors.append(f"Table '{table_name}' defined in models but missing from database")
    
    # Check for extra tables
    for table_name in db_tables:
        if table_name not in model_tables:
            errors.append(f"Table '{table_name}' exists in database but not defined in models")
    
    # Check table schemas
    for table_name in model_tables:
        if table_name not in db_tables:
            continue
            
        model_columns = {c.name: c for c in model_tables[table_name].columns}
        db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
        
        # Check for missing columns
        for col_name in model_columns:
            if col_name not in db_columns:
                errors.append(f"Column '{col_name}' of table '{table_name}' missing from database")
        
        # Check for extra columns
        for col_name in db_columns:
            if col_name not in model_columns:
                errors.append(f"Column '{col_name}' exists in table '{table_name}' but not defined in models")
    
    return errors

def init_database(check_first: bool = True) -> Dict[str, Any]:
    """
    Initialize database schema.
    
    Args:
        check_first: Whether to check if tables exist first
        
    Returns:
        Dictionary with initialization status
    """
    try:
        if check_first:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            if existing_tables:
                return {
                    "status": "skipped",
                    "message": f"Database already contains tables: {', '.join(existing_tables)}"
                }
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        return {
            "status": "success",
            "message": "Database schema created successfully"
        }
        
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Failed to create database schema: {str(e)}"
        }

def get_session():
    """Get a new database session."""
    session = Session()
    session._services = {}  # Initialize services dict for new sessions
    return session

# Add session cleanup event handler
@event.listens_for(Session, 'after_begin')
def receive_after_begin(session, transaction, connection):
    """Initialize services dict when session begins."""
    session._services = {}

@event.listens_for(Session, 'after_commit')
def receive_after_commit(session):
    """Clean up services after commit."""
    if hasattr(session, '_services'):
        session._services.clear()

@event.listens_for(Session, 'after_rollback')
def receive_after_rollback(session):
    """Clean up services after rollback."""
    if hasattr(session, '_services'):
        session._services.clear()

@event.listens_for(Session, 'after_soft_rollback')
def receive_after_soft_rollback(session, previous_transaction):
    """Clean up services after soft rollback."""
    if hasattr(session, '_services'):
        session._services.clear() 