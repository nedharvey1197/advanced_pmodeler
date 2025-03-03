# models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Setup database
base_dir = Path('./manufacturing_model')
db_path = base_dir / 'data' / 'manufacturing_model.db'
engine = create_engine(f'sqlite:///{db_path}')
Base = declarative_base()

# Create session factory
Session = sessionmaker(bind=engine)

def get_session():
    """Create and return a new session"""
    return Session()












