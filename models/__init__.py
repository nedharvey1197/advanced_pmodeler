# models/__init__.py
# Import all models for easy access
from .base import Base, engine, get_session
from .scenario import Scenario
from .equipment import Equipment
from .product import Product
from .cost_driver import CostDriver
from .financial_projection import FinancialProjection

# Create all tables
def create_tables():
    Base.metadata.create_all(engine)