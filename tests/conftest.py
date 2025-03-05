"""
Test configuration and fixtures.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.models.base_models import Base

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def session(engine):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data") 