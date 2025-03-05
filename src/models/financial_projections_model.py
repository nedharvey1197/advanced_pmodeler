"""
Financial projections model for the manufacturing expansion financial model.

This module defines the FinancialProjection SQLAlchemy model which represents the
calculated financial metrics for a specific scenario and year. It captures income
statement, balance sheet, and cash flow metrics, as well as production metrics.

The FinancialProjection model maintains relationships with:
    - Scenario: The business scenario these projections belong to
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class FinancialProjection(Base):
    """
    SQLAlchemy model representing financial projections.
    
    This class defines all financial metrics calculated for a specific scenario
    and year, organized into income statement, balance sheet, and cash flow
    categories. It also tracks production metrics and product-specific details.
    """
    
    __tablename__ = 'financial_projections'
    
    # Primary key and foreign key relationships
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    year = Column(Integer, nullable=False)
    
    # Income Statement metrics
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
    
    # Balance Sheet metrics
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
    
    # Cash Flow metrics
    operating_cash_flow = Column(Float, default=0.0)
    investing_cash_flow = Column(Float, default=0.0)
    financing_cash_flow = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    
    # Production metrics
    total_production = Column(Float, default=0.0)
    capacity_utilization = Column(Float, default=0.0)  # percentage
    
    # Product-specific projections stored as JSON
    product_details = Column(JSON)  # Store as JSON for flexibility
    
    # Relationships
    scenario = relationship("Scenario", back_populates="financials")
    
    def __repr__(self):
        """String representation of the FinancialProjection instance."""
        return f"<FinancialProjection(scenario_id={self.scenario_id}, year={self.year})>"
        
    def calculate_gross_margin(self) -> float:
        """
        Calculate the gross margin percentage.
        
        Returns:
            float: Gross margin as a percentage
        """
        return (self.gross_profit / self.revenue * 100) if self.revenue > 0 else 0.0
        
    def calculate_net_margin(self) -> float:
        """
        Calculate the net margin percentage.
        
        Returns:
            float: Net margin as a percentage
        """
        return (self.net_income / self.revenue * 100) if self.revenue > 0 else 0.0