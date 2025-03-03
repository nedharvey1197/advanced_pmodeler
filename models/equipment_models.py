# models/equipment.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Equipment(Base):
    __tablename__ = 'equipment'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    name = Column(String(100), nullable=False)
    cost = Column(Float, nullable=False)
    useful_life = Column(Integer, nullable=False)  # in years
    max_capacity = Column(Float, nullable=False)   # units per year
    maintenance_cost_pct = Column(Float, default=0.05)  # 5% of cost per year
    availability_pct = Column(Float, default=0.95)      # 95% uptime
    purchase_year = Column(Integer, default=2025)
    is_leased = Column(Boolean, default=False)
    lease_rate = Column(Float, default=0.0)             # annual lease rate
    lease_type = Column(String, default="none")         # Values: "none", "standard", "fmv_buyout"
    lease_term = Column(Integer, default=0)             # Term length in months
    lease_payment = Column(Float, default=0.0)          # Monthly payment amount
    
    # Relationships
    scenario = relationship("Scenario", back_populates="equipment")
    cost_drivers = relationship("CostDriver", back_populates="equipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Equipment(name='{self.name}', cost=${self.cost:,.2f})>"