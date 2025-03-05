from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .base_models import Base

class SalesParameter(Base):
    __tablename__ = 'sales_parameters'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    value = Column(Float)
    is_percentage = Column(Boolean, default=False)
    description = Column(String(500))
    created_at = Column(String, default=datetime.now().isoformat())

    scenario = relationship("Scenario", back_populates="sales_parameters")

class SalesForecast(Base):
    __tablename__ = 'sales_forecasts'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='CASCADE'))
    year = Column(Integer, nullable=False)
    is_market_driven = Column(Boolean, default=True)
    total_revenue = Column(Float)
    pipeline_metrics = Column(JSON)  # Stores prospects, leads, opportunities
    staffing_requirements = Column(JSON)  # Sales team staffing details
    channel_distribution = Column(JSON)  # Channel breakdown
    created_at = Column(String, default=datetime.now().isoformat())

    scenario = relationship("Scenario", back_populates="sales_forecasts")
    product_forecasts = relationship("ProductForecast", back_populates="sales_forecast")

class ProductForecast(Base):
    __tablename__ = 'product_forecasts'
    
    id = Column(Integer, primary_key=True)
    sales_forecast_id = Column(Integer, ForeignKey('sales_forecasts.id', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    unit_volume = Column(Integer)
    revenue = Column(Float)
    market_share = Column(Float)
    internal_capacity = Column(Integer)
    outsourcing_required = Column(Integer)
    created_at = Column(String, default=datetime.now().isoformat())

    sales_forecast = relationship("SalesForecast", back_populates="product_forecasts")
    product = relationship("Product") 