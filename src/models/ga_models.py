from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GAExpense(Base):
    __tablename__ = 'ga_expenses'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='CASCADE'))
    year = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float)
    percent_of_revenue = Column(Float)
    headcount = Column(Integer)
    calculation_basis = Column(String(500))
    calculation_formula = Column(String(500))
    additional_details = Column(JSON)  # For storing any additional category-specific details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    scenario = relationship("Scenario", back_populates="ga_expenses") 