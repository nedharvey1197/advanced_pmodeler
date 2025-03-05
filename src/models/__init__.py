# models/__init__.py
# Import all models for easy access
from .base import Base, engine, get_session
from .scenario import Scenario
from .equipment import Equipment
from .product import Product
from .cost_driver import CostDriver
from .financial_projection import FinancialProjection
from .scenario_models import Scenario
from .equipment_models import Equipment
from .product_models import Product
from .financial_projections_model import FinancialProjection
from .sales_models import SalesParameter, SalesForecast, ProductForecast
from .ga_models import GAExpense
from .industry_models import IndustryStandard, ScenarioAssumption

# Create all tables
def create_tables():
    Base.metadata.create_all(engine)

__all__ = [
    'Scenario',
    'Equipment',
    'Product',
    'FinancialProjection',
    'SalesParameter',
    'SalesForecast',
    'ProductForecast',
    'GAExpense',
    'IndustryStandard',
    'ScenarioAssumption'
]