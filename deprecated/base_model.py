"""
Base SQLAlchemy configuration and session management for the Manufacturing Model.

This module provides the core database configuration and session management functionality
for the manufacturing expansion financial model. It sets up SQLAlchemy with SQLite as the
backend database.

Key Components:
    - Base: The declarative base class for all SQLAlchemy models
    - engine: The SQLAlchemy engine instance configured for SQLite
    - Session: Session factory for creating new database sessions
    - get_session: Function to create and return a new session

Database Location:
    The SQLite database file is stored in the 'manufacturing_model/data' directory
    with the name 'manufacturing_model.db'
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Setup database path
base_dir = Path('./manufacturing_model')
db_path = base_dir / 'data' / 'manufacturing_model.db'
engine = create_engine(f'sqlite:///{db_path}')

# Create declarative base class for models
Base = declarative_base()

# Create session factory
Session = sessionmaker(bind=engine)

def get_session():
    """
    Create and return a new database session.
    
    Returns:
        sqlalchemy.orm.Session: A new SQLAlchemy session instance
        
    Usage:
        session = get_session()
        try:
            # Use session for database operations
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    """
    return Session()












