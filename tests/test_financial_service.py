"""
Tests for the financial service.
"""

import pytest
from decimal import Decimal

from src.services.financial_service import FinancialService
from src.models.scenario import Scenario

def test_calculate_financial_projections(session, sample_scenario, sample_equipment, sample_products):
    """Test calculating financial projections."""
    # Create service
    service = FinancialService(session)
    
    # Calculate projections
    projections = service.calculate_financial_projections(sample_scenario.id)
    
    # Verify results
    assert len(projections) > 0
    assert projections[0].revenue == Decimal("1000000")
    assert projections[0].costs == Decimal("800000")
    assert projections[0].gross_profit == Decimal("200000")
    
    # Verify growth rates
    assert projections[1].revenue > projections[0].revenue
    assert projections[1].costs > projections[0].costs
    
    # Verify equipment costs are included
    total_equipment_cost = sum(e.cost for e in sample_equipment if not e.is_leased)
    assert projections[0].depreciation == total_equipment_cost / 10  # Assuming straight-line depreciation

def test_calculate_npv(session, sample_scenario, sample_financial_projections):
    """Test calculating NPV."""
    # Create service
    service = FinancialService(session)
    
    # Calculate NPV
    npv = service.calculate_npv(sample_scenario.id, discount_rate=Decimal("0.1"))
    
    # Verify results
    assert npv > 0
    
    # Verify higher discount rate leads to lower NPV
    higher_npv = service.calculate_npv(sample_scenario.id, discount_rate=Decimal("0.05"))
    assert higher_npv > npv

def test_calculate_irr(session, sample_scenario, sample_financial_projections):
    """Test calculating IRR."""
    # Create service
    service = FinancialService(session)
    
    # Calculate IRR
    irr = service.calculate_irr(sample_scenario.id)
    
    # Verify results
    assert irr > 0
    assert irr < 1  # IRR should be reasonable for a manufacturing project

def test_calculate_payback_period(session, sample_scenario, sample_financial_projections):
    """Test calculating payback period."""
    # Create service
    service = FinancialService(session)
    
    # Calculate payback period
    payback = service.calculate_payback_period(sample_scenario.id)
    
    # Verify results
    assert payback > 0
    assert payback < 10  # Payback should be reasonable for a manufacturing project

def test_scenario_comparison(session, sample_scenario, sample_financial_projections):
    """Test comparing scenarios."""
    # Create another scenario with different growth rates
    higher_growth_scenario = Scenario(
        name="High Growth Scenario",
        description="A test scenario with higher growth",
        initial_revenue=Decimal("1000000"),
        initial_costs=Decimal("800000"),
        annual_revenue_growth=Decimal("0.08"),  # Higher growth
        annual_cost_growth=Decimal("0.04"),
        debt_ratio=Decimal("0.4"),
        interest_rate=Decimal("0.05"),
        tax_rate=Decimal("0.21")
    )
    session.add(higher_growth_scenario)
    session.commit()
    
    # Create service
    service = FinancialService(session)
    
    # Compare scenarios
    comparison = service.compare_scenarios([sample_scenario.id, higher_growth_scenario.id])
    
    # Verify results
    assert len(comparison) > 0
    assert comparison[higher_growth_scenario.id]["npv"] > comparison[sample_scenario.id]["npv"]
    assert comparison[higher_growth_scenario.id]["irr"] > comparison[sample_scenario.id]["irr"] 