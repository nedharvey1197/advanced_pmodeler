"""
Equipment model for the manufacturing expansion financial model.

This module defines the Equipment SQLAlchemy model which represents manufacturing
equipment in the system. It tracks equipment specifications, costs, and operational
parameters needed for capacity planning and financial projections.

The Equipment model maintains relationships with:
    - Scenario: The business scenario this equipment belongs to
    - CostDriver: The cost factors associated with using this equipment for products
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Equipment(Base):
    """
    SQLAlchemy model representing manufacturing equipment.
    
    This class defines all attributes and relationships for tracking manufacturing
    equipment, including purchase/lease information, capacity, and maintenance details.
    """
    
    __tablename__ = 'equipment'
    
    # Primary key and foreign key relationships
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    
    # Basic equipment information
    name = Column(String(100), nullable=False)
    cost = Column(Float, nullable=False)
    useful_life = Column(Integer, nullable=False)  # in years
    max_capacity = Column(Float, nullable=False)   # units per year
    
    # Operational parameters
    maintenance_cost_pct = Column(Float, default=0.05)  # 5% of cost per year
    availability_pct = Column(Float, default=0.95)      # 95% uptime
    purchase_year = Column(Integer, default=2025)
    
    # Leasing information
    is_leased = Column(Boolean, default=False)
    lease_rate = Column(Float, default=0.0)             # annual lease rate
    lease_type = Column(String, default="none")         # Values: "none", "standard", "fmv_buyout"
    lease_term = Column(Integer, default=0)             # Term length in months
    lease_payment = Column(Float, default=0.0)          # Monthly payment amount
    
    # Relationships
    scenario = relationship("Scenario", back_populates="equipment")
    cost_drivers = relationship("CostDriver", back_populates="equipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        """String representation of the Equipment instance."""
        return f"<Equipment(name='{self.name}', cost=${self.cost:,.2f})>"
        
    def calculate_annual_maintenance_cost(self) -> float:
        """
        Calculate the annual maintenance cost for this equipment.
        
        Returns:
            float: Annual maintenance cost based on the equipment cost and maintenance percentage
        """
        return self.cost * self.maintenance_cost_pct
        
    def calculate_effective_capacity(self) -> float:
        """
        Calculate the effective annual capacity considering equipment availability.
        
        Returns:
            float: Effective annual capacity in units
        """
        return self.max_capacity * self.availability_pct