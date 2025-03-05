# models/scenario.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base_models import Base

class Scenario(Base):
    __tablename__ = 'scenarios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(String, default=datetime.now().isoformat())
    is_base_case = Column(Boolean, default=False)
    
    # Financial assumptions
    initial_revenue = Column(Float, default=0.0)
    initial_costs = Column(Float, default=0.0)
    annual_revenue_growth = Column(Float, default=0.15)  # 15% default
    annual_cost_growth = Column(Float, default=0.10)     # 10% default
    debt_ratio = Column(Float, default=0.50)             # 50% default
    interest_rate = Column(Float, default=0.10)          # 10% default
    tax_rate = Column(Float, default=0.25)               # 25% default
    
    # Relationships
    equipment = relationship("Equipment", back_populates="scenario", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="scenario", cascade="all, delete-orphan")
    financials = relationship("FinancialProjection", back_populates="scenario", cascade="all, delete-orphan")
    
    # New relationships for sales, G&A, and assumptions
    sales_parameters = relationship("SalesParameter", back_populates="scenario", cascade="all, delete-orphan")
    sales_forecasts = relationship("SalesForecast", back_populates="scenario", cascade="all, delete-orphan")
    ga_expenses = relationship("GAExpense", back_populates="scenario", cascade="all, delete-orphan")
    assumptions = relationship("ScenarioAssumption", back_populates="scenario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Scenario(name='{self.name}', is_base_case={self.is_base_case})>"