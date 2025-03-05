"""
Initialize models package and ensure all models are imported.
"""

from .base_models import Base, engine, Session, get_session
from .product_models import Product, CostDriver
from .equipment_models import Equipment
from .financial_projections_model import FinancialProjection
from .sales_models import SalesParameter, SalesForecast, ProductForecast
from .ga_models import GAExpense
from .scenario_models import Scenario
from .industry_models import IndustryStandard, ScenarioAssumption

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(engine)

__all__ = [
    'Scenario',
    'Equipment',
    'Product',
    'CostDriver',
    'FinancialProjection',
    'SalesParameter',
    'SalesForecast',
    'ProductForecast',
    'GAExpense',
    'IndustryStandard',
    'ScenarioAssumption',
    'create_tables',
    'get_session'
]