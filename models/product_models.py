"""
Cost driver model for the manufacturing expansion financial model.

This module defines the CostDriver SQLAlchemy model which represents the cost factors
associated with manufacturing products using specific equipment. It captures both
equipment-specific costs and various labor costs involved in the manufacturing process.

The CostDriver model maintains relationships with:
    - Product: The product being manufactured
    - Equipment: The equipment used in manufacturing
"""

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class CostDriver(Base):
    """
    SQLAlchemy model representing manufacturing cost drivers.
    
    This class defines all cost factors involved in manufacturing a product using
    specific equipment, including equipment costs, materials costs, and various
    types of labor costs (machinist, design, supervision).
    """
    
    __tablename__ = 'cost_drivers'
    
    # Primary key and foreign key relationships
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    equipment_id = Column(Integer, ForeignKey('equipment.id'))
    
    # Equipment utilization costs
    cost_per_hour = Column(Float, nullable=False)
    hours_per_unit = Column(Float, nullable=False)
    
    # Material and labor costs
    materials_cost_per_unit = Column(Float, default=0.0)
    machinist_labor_cost_per_hour = Column(Float, default=30.0)
    machinist_hours_per_unit = Column(Float, default=2.0)
    design_labor_cost_per_hour = Column(Float, default=40.0)
    design_hours_per_unit = Column(Float, default=1.0)
    supervision_cost_per_hour = Column(Float, default=20.0)
    supervision_hours_per_unit = Column(Float, default=0.5)
    
    # Relationships
    product = relationship("Product", back_populates="cost_drivers")
    equipment = relationship("Equipment", back_populates="cost_drivers")
    
    def __repr__(self):
        """String representation of the CostDriver instance."""
        return f"<CostDriver(product_id={self.product_id}, equipment_id={self.equipment_id})>"
        
    def calculate_total_cost_per_unit(self) -> float:
        """
        Calculate the total cost to produce one unit of the product.
        
        Returns:
            float: Total cost per unit including equipment, materials, and labor costs
        """
        # Equipment cost
        equipment_cost = self.cost_per_hour * self.hours_per_unit
        
        # Labor costs
        machinist_cost = self.machinist_labor_cost_per_hour * self.machinist_hours_per_unit
        design_cost = self.design_labor_cost_per_hour * self.design_hours_per_unit
        supervision_cost = self.supervision_cost_per_hour * self.supervision_hours_per_unit
        
        return (equipment_cost + self.materials_cost_per_unit + 
                machinist_cost + design_cost + supervision_cost)