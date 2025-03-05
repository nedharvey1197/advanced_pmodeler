from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .base_models import Base

class IndustryStandard(Base):
    __tablename__ = 'industry_standards'
    
    id = Column(Integer, primary_key=True)
    industry_type = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    display_name = Column(String(200))
    description = Column(String(500))
    min_value = Column(Float)
    max_value = Column(Float)
    typical_value = Column(Float)
    is_percentage = Column(Boolean, default=False)
    created_at = Column(String, default=datetime.now().isoformat())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ScenarioAssumption(Base):
    __tablename__ = 'scenario_assumptions'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='CASCADE'))
    industry_standard_id = Column(Integer, ForeignKey('industry_standards.id'))
    value = Column(Float)
    notes = Column(String(500))
    is_validated = Column(Boolean, default=False)
    validation_message = Column(String(500))
    created_at = Column(String, default=datetime.now().isoformat())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    scenario = relationship("Scenario", back_populates="assumptions")
    industry_standard = relationship("IndustryStandard") 