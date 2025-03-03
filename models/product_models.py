# models/cost_driver.py
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class CostDriver(Base):
    __tablename__ = 'cost_drivers'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    equipment_id = Column(Integer, ForeignKey('equipment.id'))
    cost_per_hour = Column(Float, nullable=False)
    hours_per_unit = Column(Float, nullable=False)
    
    # Additional costs
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
        return f"<CostDriver(product_id={self.product_id}, equipment_id={self.equipment_id})>"