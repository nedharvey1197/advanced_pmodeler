"""
Product and cost driver models for the manufacturing expansion financial model.

This module defines the Product and CostDriver SQLAlchemy models which represent
products and their associated manufacturing costs.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base_models import Base

class Product(Base):
    """
    SQLAlchemy model representing a product.
    
    This class defines the core attributes of a product, including its specifications,
    pricing, and production parameters.
    """
    
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(String, default=datetime.now().isoformat())
    
    # Product specifications
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    target_margin = Column(Float, default=0.3)  # 30% default margin
    
    # Production parameters
    production_rate = Column(Float, nullable=False)  # units per hour
    setup_time = Column(Float, default=0.0)  # hours
    quality_rate = Column(Float, default=0.98)  # 98% default quality rate
    
    # Relationships
    scenario_id = Column(Integer, ForeignKey('scenarios.id'), nullable=False)
    scenario = relationship("Scenario", back_populates="products")
    cost_drivers = relationship("CostDriver", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(name='{self.name}', unit_price=${self.unit_price:,.2f})>"

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