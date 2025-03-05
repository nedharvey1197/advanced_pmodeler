"""
Equipment service module for the manufacturing expansion financial model.

This module provides comprehensive equipment management capabilities including:
- Equipment capacity planning and analysis
- Utilization analysis and optimization
- Shift operations modeling
- Equipment purchase optimization
- Capacity constraint identification
- Production capacity calculation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_
from datetime import datetime

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
    
    def calculate_production_capacity(self, equipment_id: int, year: int = None) -> Dict[str, Any]:
        """
        Calculate the maximum production capacity for a piece of equipment.
        
        Args:
            equipment_id: ID of the equipment
            year: Optional year to check capacity
            
        Returns:
            Dictionary with capacity details including:
            - Maximum capacity
            - Available capacity
            - Equipment status
        """
        equipment = self.session.query(Equipment).filter(Equipment.id == equipment_id).first()
        
        if not equipment:
            return {"error": f"Equipment with ID {equipment_id} not found"}
        
        # Skip if equipment hasn't been purchased yet
        if year and equipment.purchase_year > year:
            return {
                "equipment_id": equipment_id,
                "equipment_name": equipment.name,
                "max_capacity": 0,
                "available_capacity": 0,
                "status": "not purchased"
            }
        
        # Calculate available capacity adjusted for availability percentage
        max_capacity = equipment.max_capacity
        available_capacity = max_capacity * equipment.availability_pct
        
        return {
            "equipment_id": equipment_id,
            "equipment_name": equipment.name,
            "max_capacity": max_capacity,
            "available_capacity": available_capacity,
            "status": "active"
        }
    
    def calculate_equipment_utilization_by_product(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Calculate detailed equipment utilization broken down by product.
        
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
            "used_capacity": 0,
            "bottlenecks": [],
            "unutilized_capacity": []
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
            utilization_pct = (used_capacity / available_capacity * 100) if available_capacity > 0 else 0
            result["equipment_utilization"][equipment.id]["utilization_pct"] = utilization_pct
            result["used_capacity"] += used_capacity
            
            # Check for bottlenecks
            if utilization_pct > 85:
                result["bottlenecks"].append({
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "utilization_pct": utilization_pct,
                    "severity": "high" if utilization_pct > 95 else "medium"
                })
            
            # Check for unutilized capacity
            if utilization_pct < 50:
                result["unutilized_capacity"].append({
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "utilization_pct": utilization_pct,
                    "unused_hours": available_capacity - used_capacity
                })
        
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
    
    def identify_capacity_constraints(self, scenario_id: int, start_year: int, end_year: int) -> Dict[str, Any]:
        """
        Identify capacity constraints and bottlenecks over a time period.
        
        Args:
            scenario_id: ID of the scenario to analyze
            start_year: First year of analysis
            end_year: Last year of analysis
            
        Returns:
            Dictionary containing comprehensive capacity constraints analysis
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Initialize result
        result = {
            "bottlenecks_by_year": {},
            "equipment_utilization_trend": {},
            "capacity_expansion_recommendations": []
        }
        
        # Get all equipment
        equipment_list = self.session.query(Equipment).filter(
            Equipment.scenario_id == scenario_id
        ).all()
        
        # Track utilization trends for each equipment over the years
        utilization_trends = {e.id: {
            "equipment_name": e.name,
            "years": [],
            "utilization": []
        } for e in equipment_list}
        
        # Analyze each year
        for year in range(start_year, end_year + 1):
            # Calculate utilization for this year
            utilization = self.calculate_equipment_utilization_by_product(scenario_id, year)
            
            # Store bottlenecks
            if utilization["bottlenecks"]:
                result["bottlenecks_by_year"][year] = utilization["bottlenecks"]
            
            # Update utilization trends
            for eq_id, eq_data in utilization["equipment_utilization"].items():
                if eq_id in utilization_trends:
                    utilization_trends[eq_id]["years"].append(year)
                    utilization_trends[eq_id]["utilization"].append(eq_data["utilization_pct"])
        
        # Store utilization trends in result
        result["equipment_utilization_trend"] = utilization_trends
        
        # Generate capacity expansion recommendations
        for eq_id, trend in utilization_trends.items():
            if not trend["utilization"]:
                continue
                
            # Look for consistently high utilization
            if any(util >= 85 for util in trend["utilization"]):
                years_over_threshold = [
                    trend["years"][i] for i, util in enumerate(trend["utilization"]) 
                    if util >= 85
                ]
                
                if years_over_threshold:
                    first_year_over = min(years_over_threshold)
                    
                    # Get equipment details
                    equipment = self.session.query(Equipment).filter(Equipment.id == eq_id).first()
                    
                    # Add recommendation
                    result["capacity_expansion_recommendations"].append({
                        "equipment_id": eq_id,
                        "equipment_name": trend["equipment_name"],
                        "constraint_year": first_year_over,
                        "recommendation": "Add additional capacity",
                        "details": f"Utilization exceeds 85% in year {first_year_over}. Consider purchasing additional {trend['equipment_name']} equipment.",
                        "estimated_cost": equipment.cost if equipment else "Unknown"
                    })
        
        return result
    
    def model_shift_operations(self, scenario_id: int, year: int, shift_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Model shift operations including overtime costs for a specific year.
        
        Args:
            scenario_id: ID of the scenario to analyze
            year: Year to model shifts for
            shift_config: Optional shift configuration
            
        Returns:
            Dictionary containing shift operation details including:
            - Required number of shifts
            - Labor requirements
            - Overtime estimates
            - Cost analysis
        """
        # Default shift configuration
        if shift_config is None:
            shift_config = {
                "shifts_per_day": 1,
                "hours_per_shift": 8,
                "days_per_week": 5,
                "weeks_per_year": 50,
                "overtime_multiplier": 1.5,
                "max_overtime_hours_per_week": 10
            }
        
        # Calculate available hours per year under this shift configuration
        standard_hours_per_year = (
            shift_config["shifts_per_day"] * 
            shift_config["hours_per_shift"] * 
            shift_config["days_per_week"] * 
            shift_config["weeks_per_year"]
        )
        
        max_overtime_hours_per_year = (
            shift_config["max_overtime_hours_per_week"] * 
            shift_config["weeks_per_year"]
        )
        
        # Get utilization data
        utilization = self.calculate_equipment_utilization_by_product(scenario_id, year)
        
        if "error" in utilization:
            return utilization
        
        result = {
            "equipment_shift_analysis": {},
            "labor_requirements": {},
            "overtime_estimates": {},
            "total_overtime_cost": 0,
            "shift_recommendations": []
        }
        
        # Analyze each piece of equipment
        total_overtime_cost = 0
        for eq_id, eq_data in utilization["equipment_utilization"].items():
            equipment = self.session.query(Equipment).filter(Equipment.id == eq_id).first()
            if not equipment:
                continue
            
            # Calculate required hours vs standard hours
            required_hours = eq_data["used_capacity"]
            overtime_hours = max(0, required_hours - standard_hours_per_year)
            
            # Calculate if we need multiple shifts
            required_shifts = required_hours / standard_hours_per_year
            
            # Limit overtime to maximum allowed
            overtime_hours = min(overtime_hours, max_overtime_hours_per_year)
            
            # Calculate overtime cost
            total_product_hours = 0
            total_cost = 0
            
            for prod_id, prod_data in eq_data["product_breakdown"].items():
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.product_id == prod_id,
                        CostDriver.equipment_id == eq_id
                    )
                ).first()
                
                if cost_driver:
                    hours = prod_data
                    hourly_cost = cost_driver.cost_per_hour
                    total_product_hours += hours
                    total_cost += hours * hourly_cost
            
            avg_hourly_cost = total_cost / total_product_hours if total_product_hours > 0 else 0
            overtime_cost = overtime_hours * avg_hourly_cost * shift_config["overtime_multiplier"]
            
            # Add to total overtime cost
            total_overtime_cost += overtime_cost
            
            # Store analysis for this equipment
            result["equipment_shift_analysis"][eq_id] = {
                "equipment_name": equipment.name,
                "standard_hours": standard_hours_per_year,
                "required_hours": required_hours,
                "overtime_hours": overtime_hours,
                "required_shifts": required_shifts,
                "overtime_cost": overtime_cost,
                "status": (
                    "overloaded" if required_hours > (standard_hours_per_year + max_overtime_hours_per_year)
                    else "overtime" if overtime_hours > 0
                    else "normal"
                )
            }
            
            # Generate shift recommendations
            if required_shifts > 1.1:  # If we need more than 1.1 shifts
                recommended_shifts = int(np.ceil(required_shifts))
                result["shift_recommendations"].append({
                    "equipment_id": eq_id,
                    "equipment_name": equipment.name,
                    "current_shifts": shift_config["shifts_per_day"],
                    "recommended_shifts": recommended_shifts,
                    "reason": f"Utilization requires {required_shifts:.2f} shifts"
                })
        
        # Store total overtime cost
        result["total_overtime_cost"] = total_overtime_cost
        
        return result
    
    def optimize_equipment_purchases(self, scenario_id: int, budget: float, 
                                  start_year: int = None, optimization_years: int = 5) -> Dict[str, Any]:
        """
        Optimize equipment purchases based on utilization and budget constraints.
        
        Args:
            scenario_id: ID of the scenario to optimize
            budget: Available budget for equipment purchases
            start_year: Optional start year for optimization
            optimization_years: Number of years to optimize
            
        Returns:
            Dictionary containing optimization results including:
            - Recommended equipment purchases
            - Cost breakdown
            - Expected utilization improvements
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Set default start year if not provided
        if start_year is None:
            start_year = datetime.now().year
        
        end_year = start_year + optimization_years - 1
        
        # Get capacity constraints analysis
        constraints = self.identify_capacity_constraints(scenario_id, start_year, end_year)
        
        if "error" in constraints:
            return constraints
        
        # Extract bottlenecked equipment and years
        bottlenecks = {}
        for year, bottleneck_list in constraints["bottlenecks_by_year"].items():
            for bottleneck in bottleneck_list:
                eq_id = bottleneck["equipment_id"]
                if eq_id not in bottlenecks or bottlenecks[eq_id]["year"] > year:
                    bottlenecks[eq_id] = {
                        "equipment_id": eq_id,
                        "equipment_name": bottleneck["equipment_name"],
                        "year": year,
                        "utilization_pct": bottleneck["utilization_pct"]
                    }
        
        # Sort bottlenecks by year and then by utilization percentage
        sorted_bottlenecks = sorted(
            bottlenecks.values(),
            key=lambda x: (x["year"], -x["utilization_pct"])
        )
        
        # Get current equipment information
        equipment_info = {}
        for eq_id in bottlenecks:
            equipment = self.session.query(Equipment).filter(Equipment.id == eq_id).first()
            if equipment:
                equipment_info[eq_id] = {
                    "equipment_id": eq_id,
                    "name": equipment.name,
                    "cost": equipment.cost,
                    "max_capacity": equipment.max_capacity
                }
        
        # Initialize optimization result
        result = {
            "budget_constraint": budget,
            "equipment_purchase_plan": {},
            "total_cost": 0,
            "bottlenecks_addressed": 0,
            "bottlenecks_remaining": [],
            "expected_improvements": {}
        }
        
        # Simulate equipment purchases with budget constraint
        remaining_budget = budget
        for bottleneck in sorted_bottlenecks:
            eq_id = bottleneck["equipment_id"]
            
            if eq_id not in equipment_info:
                continue
                
            equipment = equipment_info[eq_id]
            purchase_year = bottleneck["year"]
            
            # Check if we have budget for this equipment
            if equipment["cost"] <= remaining_budget:
                # We can purchase this equipment
                if purchase_year not in result["equipment_purchase_plan"]:
                    result["equipment_purchase_plan"][purchase_year] = []
                
                result["equipment_purchase_plan"][purchase_year].append({
                    "equipment_id": eq_id,
                    "equipment_name": equipment["name"],
                    "cost": equipment["cost"],
                    "capacity_added": equipment["max_capacity"]
                })
                
                result["total_cost"] += equipment["cost"]
                result["bottlenecks_addressed"] += 1
                remaining_budget -= equipment["cost"]
                
                # Estimate utilization improvement
                current_utilization = bottleneck["utilization_pct"]
                expected_utilization = current_utilization / 2  # Rough estimate
                result["expected_improvements"][eq_id] = {
                    "current_utilization": current_utilization,
                    "expected_utilization": expected_utilization,
                    "improvement": current_utilization - expected_utilization
                }
            else:
                # We don't have budget for this equipment
                result["bottlenecks_remaining"].append(bottleneck)
        
        return result

# Wrapper functions for easy access
def calculate_production_capacity(equipment_id: int, year: int = None) -> Dict[str, Any]:
    """Wrapper function for production capacity calculation."""
    session = get_session()
    service = EquipmentService(session)
    return service.calculate_production_capacity(equipment_id, year)

def calculate_equipment_utilization_by_product(scenario_id: int, year: int) -> Dict[str, Any]:
    """Wrapper function for equipment utilization calculation by product."""
    session = get_session()
    service = EquipmentService(session)
    return service.calculate_equipment_utilization_by_product(scenario_id, year)

def identify_capacity_constraints(scenario_id: int, start_year: int, end_year: int) -> Dict[str, Any]:
    """Wrapper function for capacity constraints identification."""
    session = get_session()
    service = EquipmentService(session)
    return service.identify_capacity_constraints(scenario_id, start_year, end_year)

def model_shift_operations(scenario_id: int, year: int, shift_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Wrapper function for shift operations modeling."""
    session = get_session()
    service = EquipmentService(session)
    return service.model_shift_operations(scenario_id, year, shift_config)

def optimize_equipment_purchases(scenario_id: int, budget: float, 
                              start_year: int = None, optimization_years: int = 5) -> Dict[str, Any]:
    """Wrapper function for equipment purchase optimization."""
    session = get_session()
    service = EquipmentService(session)
    return service.optimize_equipment_purchases(
        scenario_id, 
        budget, 
        start_year, 
        optimization_years
    ) 