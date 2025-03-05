import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.models.scenario import Scenario
from src.models.equipment import Equipment
from src.models.financial_projection import FinancialProjection
from src.models.product_models import Product, CostDriver
from src.models.scenario import Base

def test_database_connection():
    """Test database connection and basic operations"""
    # Create test database engine
    engine = create_engine('sqlite:///test.db')
    
    # Create all tables
    from src.models.scenario import Base
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Test Scenario creation
        scenario = Scenario(
            name="Test Scenario",
            description="Test scenario for setup verification"
        )
        session.add(scenario)
        session.commit()
        
        # Test Equipment creation
        equipment = Equipment(
            scenario_id=scenario.id,
            name="Test Equipment",
            purchase_cost=100000.0,
            operating_cost=1000.0,
            capacity=1000.0,
            utilization=0.0
        )
        session.add(equipment)
        session.commit()
        
        # Test Product creation
        product = Product(
            scenario_id=scenario.id,
            name="Test Product",
            initial_units=100.0,
            unit_price=100.0,
            growth_rate=0.1,
            introduction_year=2024,
            market_size=1000.0,
            price_elasticity=-1.0
        )
        session.add(product)
        session.commit()
        
        # Test CostDriver creation
        cost_driver = CostDriver(
            product_id=product.id,
            equipment_id=equipment.id,
            cost_per_hour=50.0,
            hours_per_unit=0.5,
            materials_cost_per_unit=20.0,
            machinist_labor_cost_per_hour=30.0,
            machinist_hours_per_unit=0.5,
            design_labor_cost_per_hour=40.0,
            design_hours_per_unit=0.25,
            supervision_cost_per_hour=50.0,
            supervision_hours_per_unit=0.1
        )
        session.add(cost_driver)
        session.commit()
        
        # Test FinancialProjection creation
        projection = FinancialProjection(
            scenario_id=scenario.id,
            period=1,
            revenue=10000.0,
            costs=8000.0
        )
        session.add(projection)
        session.commit()
        
        # Test optimization metadata
        scenario.update_optimization_metadata(
            "equipment_optimization",
            {
                "recommended_purchases": [{"equipment_id": equipment.id, "quantity": 1}],
                "expected_improvement": 0.15
            }
        )
        session.commit()
        
        # Verify optimization metadata
        assert scenario.optimization_metadata is not None
        assert "equipment_optimization" in scenario.optimization_metadata
        assert scenario.last_optimized is not None
        
        # Test optimization impacts on financial projection
        projection.update_optimization_impacts({
            "revenue_impact": 1000.0,
            "cost_impact": 500.0
        })
        session.commit()
        
        # Verify optimization impacts
        assert projection.optimization_impacts is not None
        assert projection.net_income == 3500.0  # 10000 - 8000 + 1000 - 500
        
    finally:
        # Clean up
        session.close()

def test_imports():
    """Test that all required packages are installed"""
    try:
        import numpy
        import pandas
        import sqlalchemy
        import streamlit
        import plotly
        import tensorflow
        import torch
        import pulp
        import cvxopt
        import pyomo
        import scikit_opt
        import scikit_learn
        import optuna
        import ray
        import dask
    except ImportError as e:
        pytest.fail(f"Missing required package: {str(e)}") 