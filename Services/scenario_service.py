"""
Scenario service module for the manufacturing expansion financial model.

This module provides comprehensive scenario management capabilities including:
- Scenario creation and management
- Scenario comparison
- Scenario cloning
- Scenario analysis and reporting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)
from .financial_service import (
    calculate_financial_projections,
    calculate_key_financial_metrics
)

class ScenarioManager:
    """
    Service class for scenario management and analysis.
    
    This class provides methods for managing different business scenarios,
    including creation, comparison, and analysis of scenarios.
    """
    
    def __init__(self, session=None):
        """
        Initialize ScenarioManager with a database session.
        
        Args:
            session: SQLAlchemy database session (optional)
        """
        self.session = session if session else get_session()
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List all available scenarios.
        
        Returns:
            List of dictionaries containing basic scenario information
        """
        scenarios = self.session.query(Scenario).all()
        
        result = []
        for s in scenarios:
            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "is_base_case": s.is_base_case,
                "annual_revenue_growth": s.annual_revenue_growth,
                "annual_cost_growth": s.annual_cost_growth
            })
        
        return result
    
    def create_scenario(self, name: str, description: str, **kwargs) -> Scenario:
        """
        Create a new scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            **kwargs: Additional scenario parameters
            
        Returns:
            Created scenario object
        """
        scenario = Scenario(
            name=name,
            description=description,
            **kwargs
        )
        self.session.add(scenario)
        self.session.commit()
        return scenario
    
    def get_scenario(self, scenario_id: int) -> Optional[Scenario]:
        """
        Get a specific scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to retrieve
            
        Returns:
            Scenario object if found, None otherwise
        """
        return self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    def update_scenario(self, scenario_id: int, **kwargs) -> Optional[Scenario]:
        """
        Update a scenario's parameters.
        
        Args:
            scenario_id: ID of the scenario to update
            **kwargs: Parameters to update
            
        Returns:
            Updated scenario object if found, None otherwise
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)
        
        self.session.commit()
        return scenario
    
    def delete_scenario(self, scenario_id: int) -> bool:
        """
        Delete a scenario and all associated data.
        
        Args:
            scenario_id: ID of the scenario to delete
            
        Returns:
            True if successful, False otherwise
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        self.session.delete(scenario)
        self.session.commit()
        return True
    
    def clone_scenario(self, source_scenario_id: int, new_name: str, new_description: str) -> Optional[Scenario]:
        """
        Clone an existing scenario with all its data.
        
        Args:
            source_scenario_id: ID of the original scenario
            new_name: Name for the new scenario
            new_description: Description for the new scenario
            
        Returns:
            Newly created scenario if successful, None otherwise
        """
        # Get the original scenario
        original = self.get_scenario(source_scenario_id)
        if not original:
            return None
        
        # Create a new scenario with the same financial assumptions
        new_scenario = Scenario(
            name=new_name,
            description=new_description,
            initial_revenue=original.initial_revenue,
            initial_costs=original.initial_costs,
            annual_revenue_growth=original.annual_revenue_growth,
            annual_cost_growth=original.annual_cost_growth,
            debt_ratio=original.debt_ratio,
            interest_rate=original.interest_rate,
            tax_rate=original.tax_rate
        )
        self.session.add(new_scenario)
        self.session.commit()
        
        # Clone equipment
        equipment_map = {}  # Map old equipment IDs to new equipment IDs
        for old_equipment in original.equipment:
            new_equipment = Equipment(
                scenario_id=new_scenario.id,
                name=old_equipment.name,
                cost=old_equipment.cost,
                useful_life=old_equipment.useful_life,
                max_capacity=old_equipment.max_capacity,
                maintenance_cost_pct=old_equipment.maintenance_cost_pct,
                availability_pct=old_equipment.availability_pct,
                purchase_year=old_equipment.purchase_year,
                is_leased=old_equipment.is_leased,
                lease_rate=old_equipment.lease_rate,
                lease_type=old_equipment.lease_type,
                lease_term=old_equipment.lease_term,
                lease_payment=old_equipment.lease_payment
            )
            self.session.add(new_equipment)
            self.session.commit()
            equipment_map[old_equipment.id] = new_equipment.id
        
        # Clone products
        product_map = {}  # Map old product IDs to new product IDs
        for old_product in original.products:
            new_product = Product(
                scenario_id=new_scenario.id,
                name=old_product.name,
                initial_units=old_product.initial_units,
                unit_price=old_product.unit_price,
                growth_rate=old_product.growth_rate,
                introduction_year=old_product.introduction_year,
                market_size=old_product.market_size,
                price_elasticity=old_product.price_elasticity
            )
            self.session.add(new_product)
            self.session.commit()
            product_map[old_product.id] = new_product.id
        
        # Clone cost drivers
        for old_driver in self.session.query(CostDriver).filter(
            CostDriver.product_id.in_(product_map.keys())
        ).all():
            new_driver = CostDriver(
                product_id=product_map[old_driver.product_id],
                equipment_id=equipment_map[old_driver.equipment_id],
                cost_per_hour=old_driver.cost_per_hour,
                hours_per_unit=old_driver.hours_per_unit,
                materials_cost_per_unit=old_driver.materials_cost_per_unit,
                machinist_labor_cost_per_hour=old_driver.machinist_labor_cost_per_hour,
                machinist_hours_per_unit=old_driver.machinist_hours_per_unit,
                design_labor_cost_per_hour=old_driver.design_labor_cost_per_hour,
                design_hours_per_unit=old_driver.design_hours_per_unit,
                supervision_cost_per_hour=old_driver.supervision_cost_per_hour,
                supervision_hours_per_unit=old_driver.supervision_hours_per_unit
            )
            self.session.add(new_driver)
        
        self.session.commit()
        return new_scenario
    
    def get_summary(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a scenario.
        
        Args:
            scenario_id: ID of the scenario to summarize
            
        Returns:
            Dictionary containing scenario details and key metrics
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Count products and equipment
        product_count = self.session.query(Product).filter(
            Product.scenario_id == scenario_id
        ).count()
        equipment_count = self.session.query(Equipment).filter(
            Equipment.scenario_id == scenario_id
        ).count()
        
        # Get financial projections
        projections = self.session.query(FinancialProjection).filter(
            FinancialProjection.scenario_id == scenario_id
        ).order_by(FinancialProjection.year).all()
        
        # Calculate metrics
        metrics = calculate_key_financial_metrics(scenario_id)
        
        # Prepare summary
        summary = {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "is_base_case": scenario.is_base_case,
            "annual_revenue_growth": scenario.annual_revenue_growth,
            "annual_cost_growth": scenario.annual_cost_growth,
            "debt_ratio": scenario.debt_ratio,
            "interest_rate": scenario.interest_rate,
            "tax_rate": scenario.tax_rate,
            "product_count": product_count,
            "equipment_count": equipment_count,
            "has_projections": len(projections) > 0,
            "projection_years": [p.year for p in projections] if projections else [],
            "key_metrics": metrics if "error" not in metrics else None
        }
        
        return summary
    
    def compare_scenarios(self, scenario_ids: List[int]) -> Dict[str, Any]:
        """
        Compare multiple scenarios.
        
        Args:
            scenario_ids: List of scenario IDs to compare
            
        Returns:
            Dictionary containing comparison metrics
        """
        result = {
            "scenarios": {},
            "comparison_metrics": {}
        }
        
        # Get summaries for each scenario
        for scenario_id in scenario_ids:
            summary = self.get_summary(scenario_id)
            if "error" not in summary:
                result["scenarios"][scenario_id] = summary
        
        # Compare key metrics
        if len(result["scenarios"]) > 1:
            # Compare revenue growth
            result["comparison_metrics"]["revenue_growth"] = {
                scenario_id: summary["annual_revenue_growth"]
                for scenario_id, summary in result["scenarios"].items()
            }
            
            # Compare cost growth
            result["comparison_metrics"]["cost_growth"] = {
                scenario_id: summary["annual_cost_growth"]
                for scenario_id, summary in result["scenarios"].items()
            }
            
            # Compare financial metrics if available
            for scenario_id, summary in result["scenarios"].items():
                if summary.get("key_metrics"):
                    metrics = summary["key_metrics"]
                    result["comparison_metrics"][scenario_id] = {
                        "roi": metrics.get("roi", 0),
                        "payback_period": metrics.get("payback_period"),
                        "revenue_cagr": metrics.get("revenue_cagr", 0)
                    }
        
        return result

# Wrapper functions for easy access
def list_scenarios() -> List[Dict[str, Any]]:
    """Wrapper function for listing scenarios."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.list_scenarios()

def create_scenario(name: str, description: str, **kwargs) -> Scenario:
    """Wrapper function for creating a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.create_scenario(name, description, **kwargs)

def get_scenario(scenario_id: int) -> Optional[Scenario]:
    """Wrapper function for getting a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.get_scenario(scenario_id)

def update_scenario(scenario_id: int, **kwargs) -> Optional[Scenario]:
    """Wrapper function for updating a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.update_scenario(scenario_id, **kwargs)

def delete_scenario(scenario_id: int) -> bool:
    """Wrapper function for deleting a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.delete_scenario(scenario_id)

def clone_scenario(source_scenario_id: int, new_name: str, new_description: str) -> Optional[Scenario]:
    """Wrapper function for cloning a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.clone_scenario(source_scenario_id, new_name, new_description)

def get_scenario_summary(scenario_id: int) -> Dict[str, Any]:
    """Wrapper function for getting a scenario summary."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.get_summary(scenario_id)

def compare_scenarios(scenario_ids: List[int]) -> Dict[str, Any]:
    """Wrapper function for comparing scenarios."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.compare_scenarios(scenario_ids) 