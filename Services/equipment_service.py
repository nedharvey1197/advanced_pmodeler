"""
Equipment service module for the manufacturing expansion financial model.

This module provides comprehensive equipment management capabilities including:
- Equipment capacity planning
- Utilization analysis
- Shift operations modeling
- Equipment purchase optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_

from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)

class EquipmentService:
    """
    Service class for equipment management and analysis.
    
    This class provides methods for analyzing equipment capacity, utilization,
    and operational efficiency, as well as optimizing equipment purchases.
    """
    
    def __init__(self, session):
        """
        Initialize EquipmentService with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def calculate_equipment_utilization_by_product(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Calculate equipment utilization broken down by product.
        
        Args:
            scenario_id: ID of the scenario to analyze
            year: Year to calculate utilization for
            
        Returns:
            Dictionary containing utilization metrics by product and equipment
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get all equipment and products for this scenario
        equipment_list = self.session.query(Equipment).filter(
            Equipment.scenario_id == scenario_id
        ).all()
        products = self.session.query(Product).filter(
            Product.scenario_id == scenario_id
        ).all()
        
        result = {
            "equipment_utilization": {},
            "product_utilization": {},
            "total_capacity": 0,
            "used_capacity": 0
        }
        
        # Calculate production volume for each product
        product_volumes = {}
        for product in products:
            years_since_intro = year - product.introduction_year
            if years_since_intro < 0:
                continue
            volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
            product_volumes[product.id] = volume
        
        # Calculate utilization for each piece of equipment
        for equipment in equipment_list:
            if equipment.purchase_year > year:
                continue
                
            # Calculate available capacity
            available_capacity = equipment.calculate_effective_capacity()
            result["total_capacity"] += available_capacity
            
            # Initialize equipment utilization tracking
            result["equipment_utilization"][equipment.id] = {
                "equipment_name": equipment.name,
                "available_capacity": available_capacity,
                "used_capacity": 0,
                "utilization_pct": 0,
                "product_breakdown": {}
            }
            
            # Calculate used capacity by product
            for product_id, volume in product_volumes.items():
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.equipment_id == equipment.id,
                        CostDriver.product_id == product_id
                    )
                ).first()
                
                if cost_driver:
                    used_capacity = volume * cost_driver.hours_per_unit
                    result["equipment_utilization"][equipment.id]["used_capacity"] += used_capacity
                    result["equipment_utilization"][equipment.id]["product_breakdown"][product_id] = used_capacity
            
            # Calculate equipment utilization percentage
            used_capacity = result["equipment_utilization"][equipment.id]["used_capacity"]
            result["equipment_utilization"][equipment.id]["utilization_pct"] = (
                (used_capacity / available_capacity * 100) if available_capacity > 0 else 0
            )
            result["used_capacity"] += used_capacity
        
        # Calculate product utilization
        for product_id, volume in product_volumes.items():
            product = next(p for p in products if p.id == product_id)
            result["product_utilization"][product_id] = {
                "product_name": product.name,
                "volume": volume,
                "equipment_requirements": {}
            }
            
            # Calculate equipment requirements for this product
            for equipment in equipment_list:
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.equipment_id == equipment.id,
                        CostDriver.product_id == product_id
                    )
                ).first()
                
                if cost_driver:
                    required_hours = volume * cost_driver.hours_per_unit
                    result["product_utilization"][product_id]["equipment_requirements"][equipment.id] = {
                        "equipment_name": equipment.name,
                        "required_hours": required_hours,
                        "utilization_pct": (
                            (required_hours / equipment.calculate_effective_capacity() * 100)
                            if equipment.calculate_effective_capacity() > 0 else 0
                        )
                    }
        
        # Calculate overall utilization
        result["overall_utilization_pct"] = (
            (result["used_capacity"] / result["total_capacity"] * 100)
            if result["total_capacity"] > 0 else 0
        )
        
        return result
    
    def model_shift_operations(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Model shift operations for equipment in a given scenario and year.
        
        Args:
            scenario_id: ID of the scenario to analyze
            year: Year to model shifts for
            
        Returns:
            Dictionary containing shift operation details including:
            - Required number of shifts
            - Labor requirements
            - Overtime estimates
        """
        # Get utilization data
        utilization = self.calculate_equipment_utilization_by_product(scenario_id, year)
        
        if "error" in utilization:
            return utilization
        
        result = {
            "equipment_shift_analysis": {},
            "labor_requirements": {},
            "overtime_estimates": {}
        }
        
        # Analyze each piece of equipment
        for equipment_id, eq_data in utilization["equipment_utilization"].items():
            equipment = self.session.query(Equipment).filter(Equipment.id == equipment_id).first()
            if not equipment:
                continue
            
            # Calculate required shifts based on utilization
            utilization_pct = eq_data["utilization_pct"]
            required_shifts = 1  # Start with one shift
            
            if utilization_pct > 85:
                required_shifts = 3  # Three shifts needed
            elif utilization_pct > 60:
                required_shifts = 2  # Two shifts needed
            
            # Calculate labor requirements
            operators_per_shift = 1.5  # Average operators per machine per shift
            total_operators = required_shifts * operators_per_shift
            
            # Estimate overtime
            overtime_hours = 0
            if utilization_pct > 90:
                overtime_hours = 200  # Estimated overtime hours per year
            
            result["equipment_shift_analysis"][equipment_id] = {
                "equipment_name": equipment.name,
                "required_shifts": required_shifts,
                "utilization_pct": utilization_pct,
                "operators_per_shift": operators_per_shift,
                "total_operators": total_operators,
                "overtime_hours": overtime_hours
            }
            
            # Aggregate labor requirements
            result["labor_requirements"][equipment_id] = {
                "total_operators": total_operators,
                "shifts": required_shifts,
                "overtime_hours": overtime_hours
            }
            
            # Calculate overtime costs
            if overtime_hours > 0:
                hourly_rate = 30  # Base hourly rate
                overtime_rate = hourly_rate * 1.5  # Overtime rate
                result["overtime_estimates"][equipment_id] = {
                    "hours": overtime_hours,
                    "cost": overtime_hours * (overtime_rate - hourly_rate)
                }
        
        return result
    
    def optimize_equipment_purchases(self, scenario_id: int, budget: float) -> Dict[str, Any]:
        """
        Optimize equipment purchases based on utilization and budget constraints.
        
        Args:
            scenario_id: ID of the scenario to optimize
            budget: Available budget for equipment purchases
            
        Returns:
            Dictionary containing optimization results including:
            - Recommended equipment purchases
            - Cost breakdown
            - Expected utilization improvements
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get current equipment and utilization
        equipment_list = self.session.query(Equipment).filter(
            Equipment.scenario_id == scenario_id
        ).all()
        
        # Calculate current utilization
        current_year = datetime.now().year
        utilization = self.calculate_equipment_utilization_by_product(scenario_id, current_year)
        
        if "error" in utilization:
            return utilization
        
        # Identify equipment with high utilization
        high_utilization_equipment = []
        for equipment_id, eq_data in utilization["equipment_utilization"].items():
            if eq_data["utilization_pct"] > 80:  # High utilization threshold
                equipment = next(e for e in equipment_list if e.id == equipment_id)
                high_utilization_equipment.append({
                    "equipment": equipment,
                    "utilization": eq_data["utilization_pct"],
                    "cost": equipment.cost
                })
        
        # Sort by utilization (highest first)
        high_utilization_equipment.sort(key=lambda x: x["utilization"], reverse=True)
        
        # Optimize purchases within budget
        result = {
            "recommended_purchases": [],
            "total_cost": 0,
            "remaining_budget": budget,
            "expected_improvements": {}
        }
        
        for eq_data in high_utilization_equipment:
            equipment = eq_data["equipment"]
            if result["remaining_budget"] >= equipment.cost:
                result["recommended_purchases"].append({
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "cost": equipment.cost,
                    "current_utilization": eq_data["utilization"]
                })
                result["total_cost"] += equipment.cost
                result["remaining_budget"] -= equipment.cost
                
                # Estimate utilization improvement
                current_utilization = eq_data["utilization"]
                expected_utilization = current_utilization / 2  # Rough estimate
                result["expected_improvements"][equipment.id] = {
                    "current_utilization": current_utilization,
                    "expected_utilization": expected_utilization,
                    "improvement": current_utilization - expected_utilization
                }
        
        return result

# Wrapper functions for easy access
def calculate_equipment_utilization_by_product(scenario_id: int, year: int) -> Dict[str, Any]:
    """Wrapper function for equipment utilization calculation by product."""
    session = get_session()
    service = EquipmentService(session)
    return service.calculate_equipment_utilization_by_product(scenario_id, year)

def model_shift_operations(scenario_id: int, year: int) -> Dict[str, Any]:
    """Wrapper function for shift operations modeling."""
    session = get_session()
    service = EquipmentService(session)
    return service.model_shift_operations(scenario_id, year)

def optimize_equipment_purchases(scenario_id: int, budget: float) -> Dict[str, Any]:
    """Wrapper function for equipment purchase optimization."""
    session = get_session()
    service = EquipmentService(session)
    return service.optimize_equipment_purchases(scenario_id, budget) 