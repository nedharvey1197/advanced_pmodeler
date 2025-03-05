"""
Database models for the manufacturing expansion financial model.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Scenario(Base):
    """
    Model representing a business scenario.
    
    This model stores the core parameters and assumptions for a business scenario,
    including financial assumptions, growth rates, and optimization metadata.
    """
    
    __tablename__ = 'scenarios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    is_base_case = Column(Boolean, default=False)
    
    # Financial assumptions
    initial_revenue = Column(Float, nullable=False)
    initial_costs = Column(Float, nullable=False)
    annual_revenue_growth = Column(Float, nullable=False)
    annual_cost_growth = Column(Float, nullable=False)
    debt_ratio = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False)
    
    # Optimization metadata
    optimization_metadata = Column(JSON)
    last_optimized = Column(DateTime)
    
    # Relationships
    products = relationship("Product", back_populates="scenario")
    equipment = relationship("Equipment", back_populates="scenario")
    financial_projections = relationship("FinancialProjection", back_populates="scenario")
    
    def __repr__(self):
        return f"<Scenario(name='{self.name}', id={self.id})>" 