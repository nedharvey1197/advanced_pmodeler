# models/financial_projection.py
from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class FinancialProjection(Base):
    __tablename__ = 'financial_projections'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    year = Column(Integer, nullable=False)
    
    # Income Statement
    revenue = Column(Float, default=0.0)
    cogs = Column(Float, default=0.0)
    gross_profit = Column(Float, default=0.0)
    operating_expenses = Column(Float, default=0.0)
    ebitda = Column(Float, default=0.0)
    depreciation = Column(Float, default=0.0)
    ebit = Column(Float, default=0.0)
    interest = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    net_income = Column(Float, default=0.0)
    
    # Balance Sheet
    cash = Column(Float, default=0.0)
    accounts_receivable = Column(Float, default=0.0)
    inventory = Column(Float, default=0.0)
    fixed_assets = Column(Float, default=0.0)
    accumulated_depreciation = Column(Float, default=0.0)
    total_assets = Column(Float, default=0.0)
    accounts_payable = Column(Float, default=0.0)
    short_term_debt = Column(Float, default=0.0)
    long_term_debt = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    total_liabilities_and_equity = Column(Float, default=0.0)
    
    # Cash Flow
    operating_cash_flow = Column(Float, default=0.0)
    investing_cash_flow = Column(Float, default=0.0)
    financing_cash_flow = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    
    # Production metrics
    total_production = Column(Float, default=0.0)
    capacity_utilization = Column(Float, default=0.0)  # percentage
    
    # Store product-specific projections
    product_details = Column(JSON)  # Store as JSON for flexibility
    
    # Relationships
    scenario = relationship("Scenario", back_populates="financials")
    
    def __repr__(self):
        return f"<FinancialProjection(scenario_id={self.scenario_id}, year={self.year})>"