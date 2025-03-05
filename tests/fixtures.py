"""
Test fixtures and sample data.
"""

from decimal import Decimal
import pytest
from datetime import datetime, date

from src.models.scenario import Scenario
from src.models.equipment import Equipment
from src.models.product import Product
from src.models.financial_projection import FinancialProjection

@pytest.fixture
def sample_scenario(session):
    """Create a sample scenario with basic data."""
    scenario = Scenario(
        name="Test Manufacturing Scenario",
        description="A test scenario for manufacturing expansion",
        initial_revenue=Decimal("1000000"),
        initial_costs=Decimal("800000"),
        annual_revenue_growth=Decimal("0.05"),
        annual_cost_growth=Decimal("0.03"),
        debt_ratio=Decimal("0.4"),
        interest_rate=Decimal("0.05"),
        tax_rate=Decimal("0.21"),
        created_at=datetime.now(),
        is_base_case=True
    )
    session.add(scenario)
    session.commit()
    return scenario

@pytest.fixture
def sample_equipment(session, sample_scenario):
    """Create sample equipment data."""
    equipment = [
        Equipment(
            scenario_id=sample_scenario.id,
            name="Machine A",
            cost=Decimal("500000"),
            useful_life=10,
            max_capacity=1000,
            maintenance_cost_pct=Decimal("0.05"),
            availability_pct=Decimal("0.95"),
            purchase_year=2024,
            is_leased=False
        ),
        Equipment(
            scenario_id=sample_scenario.id,
            name="Machine B",
            cost=Decimal("750000"),
            useful_life=8,
            max_capacity=1500,
            maintenance_cost_pct=Decimal("0.06"),
            availability_pct=Decimal("0.93"),
            purchase_year=2024,
            is_leased=True,
            lease_rate=Decimal("0.08"),
            lease_type="Operating"
        ),
        Equipment(
            scenario_id=sample_scenario.id,
            name="Machine C",
            cost=Decimal("1000000"),
            useful_life=12,
            max_capacity=2000,
            maintenance_cost_pct=Decimal("0.04"),
            availability_pct=Decimal("0.97"),
            purchase_year=2025,
            is_leased=False
        )
    ]
    session.add_all(equipment)
    session.commit()
    return equipment

@pytest.fixture
def sample_products(session, sample_scenario):
    """Create sample product data."""
    products = [
        Product(
            scenario_id=sample_scenario.id,
            name="Product X",
            initial_units=5000,
            unit_price=Decimal("100"),
            growth_rate=Decimal("0.03"),
            introduction_year=2024,
            market_size=10000,
            price_elasticity=Decimal("-1.2")
        ),
        Product(
            scenario_id=sample_scenario.id,
            name="Product Y",
            initial_units=3000,
            unit_price=Decimal("150"),
            growth_rate=Decimal("0.04"),
            introduction_year=2024,
            market_size=6000,
            price_elasticity=Decimal("-1.5")
        ),
        Product(
            scenario_id=sample_scenario.id,
            name="Product Z",
            initial_units=2000,
            unit_price=Decimal("200"),
            growth_rate=Decimal("0.05"),
            introduction_year=2025,
            market_size=4000,
            price_elasticity=Decimal("-1.8")
        )
    ]
    session.add_all(products)
    session.commit()
    return products

@pytest.fixture
def sample_financial_projections(session, sample_scenario):
    """Create sample financial projections."""
    projections = [
        FinancialProjection(
            scenario_id=sample_scenario.id,
            year=2024,
            revenue=Decimal("1000000"),
            costs=Decimal("800000"),
            gross_profit=Decimal("200000"),
            operating_expenses=Decimal("100000"),
            ebitda=Decimal("100000"),
            depreciation=Decimal("20000"),
            ebit=Decimal("80000"),
            interest=Decimal("10000"),
            tax=Decimal("14700"),
            net_income=Decimal("55300")
        ),
        FinancialProjection(
            scenario_id=sample_scenario.id,
            year=2025,
            revenue=Decimal("1050000"),
            costs=Decimal("824000"),
            gross_profit=Decimal("226000"),
            operating_expenses=Decimal("103000"),
            ebitda=Decimal("123000"),
            depreciation=Decimal("20000"),
            ebit=Decimal("103000"),
            interest=Decimal("9500"),
            tax=Decimal("19635"),
            net_income=Decimal("73865")
        ),
        FinancialProjection(
            scenario_id=sample_scenario.id,
            year=2026,
            revenue=Decimal("1102500"),
            costs=Decimal("848720"),
            gross_profit=Decimal("253780"),
            operating_expenses=Decimal("106090"),
            ebitda=Decimal("147690"),
            depreciation=Decimal("20000"),
            ebit=Decimal("127690"),
            interest=Decimal("9000"),
            tax=Decimal("24905"),
            net_income=Decimal("93785")
        )
    ]
    session.add_all(projections)
    session.commit()
    return projections

@pytest.fixture
def sample_optimization_results(sample_scenario):
    """Create sample optimization results."""
    return {
        "equipment_purchase_plan": {
            2024: [
                {"equipment_name": "Machine A", "cost": 500000, "capacity_added": 1000},
                {"equipment_name": "Machine B", "cost": 750000, "capacity_added": 1500}
            ],
            2025: [
                {"equipment_name": "Machine C", "cost": 1000000, "capacity_added": 2000}
            ]
        },
        "expected_improvements": {
            "Machine A": {
                "current_utilization": 75,
                "expected_utilization": 85,
                "improvement": 10
            },
            "Machine B": {
                "current_utilization": 70,
                "expected_utilization": 88,
                "improvement": 18
            },
            "Machine C": {
                "current_utilization": 65,
                "expected_utilization": 90,
                "improvement": 25
            }
        },
        "financial_impact": {
            "npv": Decimal("1500000"),
            "irr": Decimal("0.15"),
            "payback_period": 3.5,
            "roi": Decimal("0.25")
        }
    }

@pytest.fixture
def sample_monte_carlo_results(sample_scenario):
    """Create sample Monte Carlo simulation results."""
    return {
        "summary_statistics": {
            "npv": {
                "mean": 1500000,
                "std": 250000,
                "percentiles": {
                    "5": 1100000,
                    "25": 1300000,
                    "50": 1500000,
                    "75": 1700000,
                    "95": 1900000
                }
            },
            "irr": {
                "mean": 0.15,
                "std": 0.03,
                "percentiles": {
                    "5": 0.10,
                    "25": 0.13,
                    "50": 0.15,
                    "75": 0.17,
                    "95": 0.20
                }
            }
        },
        "risk_factors": [
            {"factor": "Revenue Growth", "correlation": 0.8, "impact": "High"},
            {"factor": "Operating Costs", "correlation": -0.6, "impact": "Medium"},
            {"factor": "Equipment Utilization", "correlation": 0.5, "impact": "Medium"}
        ],
        "iterations": 1000,
        "confidence_level": 0.95
    } 