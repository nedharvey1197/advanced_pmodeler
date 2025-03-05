"""
Tests for the financial service.
"""

import pytest
from decimal import Decimal

from src.services.financial_service import FinancialService
from src.models.scenario_models import Scenario

def test_calculate_financial_projections(session):
    """Test calculating financial projections."""
    # Create test scenario
    scenario = Scenario(
        name="Test Scenario",
        description="Test scenario for financial projections",
        initial_revenue=Decimal("1000000"),
        initial_costs=Decimal("800000"),
        annual_revenue_growth=Decimal("0.05"),
        annual_cost_growth=Decimal("0.03"),
        debt_ratio=Decimal("0.4"),
        interest_rate=Decimal("0.05"),
        tax_rate=Decimal("0.21")
    )
    session.add(scenario)
    session.commit()
    
    # Create service
    service = FinancialService(session)
    
    # Calculate projections
    projections = service.calculate_financial_projections(scenario.id)
    
    # Verify results
    assert len(projections) > 0
    assert projections[0].revenue == Decimal("1000000")
    assert projections[0].costs == Decimal("800000")
    assert projections[0].gross_profit == Decimal("200000")

def test_calculate_npv(session):
    """Test calculating NPV."""
    # Create test scenario
    scenario = Scenario(
        name="Test NPV",
        description="Test scenario for NPV calculation",
        initial_revenue=Decimal("1000000"),
        initial_costs=Decimal("800000"),
        annual_revenue_growth=Decimal("0.05"),
        annual_cost_growth=Decimal("0.03"),
        debt_ratio=Decimal("0.4"),
        interest_rate=Decimal("0.05"),
        tax_rate=Decimal("0.21")
    )
    session.add(scenario)
    session.commit()
    
    # Create service
    service = FinancialService(session)
    
    # Calculate NPV
    npv = service.calculate_npv(scenario.id, discount_rate=Decimal("0.1"))
    
    # Verify results
    assert npv > 0 