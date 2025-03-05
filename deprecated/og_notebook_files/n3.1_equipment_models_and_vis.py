##The comprehensive equipment service provides a robust implementation for:

# Production Capacity Calculation
# Equipment Utilization Analysis
# Capacity Constraint Identification
# Shift Operations Modeling
# Equipment Purchase Optimization

##  Key Features:

# Flexible configuration
# Detailed analysis of equipment performance
# Budget-constrained optimization
# Multi-year planning support
# Wrapper functions for easy use

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from sqlalchemy import and_
from datetime import datetime

class EquipmentService:
    """
    Comprehensive service for equipment capacity planning, 
    utilization analysis, and optimization
    """
    def __init__(self, session):
        """
        Initialize EquipmentService with a database session
        
        :param session: SQLAlchemy database session
        """
        self.session = session
    
    def calculate_production_capacity(self, equipment_id: int, year: int = None) -> Dict[str, Any]:
        """
        Calculate the maximum production capacity for a piece of equipment
        
        :param equipment_id: ID of the equipment
        :param year: Optional year to check capacity
        :return: Dictionary with capacity details
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
        Calculate detailed equipment utilization broken down by product
        
        :param scenario_id: ID of the scenario
        :param year: Year to analyze
        :return: Detailed utilization analysis
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get all equipment for this scenario
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
        # Get all products for this scenario
        products = self.session.query(Product).filter(Product.scenario_id == scenario_id).all()
        
        # Initialize result structure
        result = {
            "equipment": {},
            "bottlenecks": [],
            "unutilized_capacity": []
        }
        
        # Calculate production volume for each product in this year
        product_volumes = {}
        for product in products:
            # Skip if product hasn't been introduced yet
            if product.introduction_year > year:
                continue
                
            # Calculate years since introduction
            years_since_intro = year - product.introduction_year
            
            # Calculate production volume using compound growth
            volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
            product_volumes[product.id] = {
                "product_name": product.name,
                "volume": volume
            }
        
        # Calculate utilization for each equipment
        for equipment in equipment_list:
            # Skip if equipment hasn't been purchased yet
            if equipment.purchase_year > year:
                continue
                
            equipment_capacity = self.calculate_production_capacity(equipment.id, year)
            available_hours = equipment_capacity["available_capacity"]
            
            # Initialize equipment data in result
            result["equipment"][equipment.id] = {
                "equipment_name": equipment.name,
                "max_capacity": equipment_capacity["max_capacity"],
                "available_capacity": available_hours,
                "used_capacity": 0,
                "utilization_pct": 0,
                "products": {}
            }
            
            # Calculate hours used by each product on this equipment
            for product_id, product_data in product_volumes.items():
                product_name = product_data["product_name"]
                volume = product_data["volume"]
                
                # Get cost driver for this product-equipment combination
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.product_id == product_id,
                        CostDriver.equipment_id == equipment.id
                    )
                ).first()
                
                if cost_driver:
                    hours_used = volume * cost_driver.hours_per_unit
                    
                    # Add to total used capacity
                    result["equipment"][equipment.id]["used_capacity"] += hours_used
                    
                    # Add product-specific usage data
                    result["equipment"][equipment.id]["products"][product_id] = {
                        "product_name": product_name,
                        "volume": volume,
                        "hours_per_unit": cost_driver.hours_per_unit,
                        "hours_used": hours_used,
                        "capacity_pct": (hours_used / available_hours) * 100 if available_hours > 0 else 0
                    }
            
            # Calculate overall utilization percentage for this equipment
            used_hours = result["equipment"][equipment.id]["used_capacity"]
            utilization_pct = (used_hours / available_hours) * 100 if available_hours > 0 else 0
            result["equipment"][equipment.id]["utilization_pct"] = utilization_pct
            
            # Check if this is a bottleneck
            if utilization_pct > 85:
                result["bottlenecks"].append({
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "utilization_pct": utilization_pct,
                    "severity": "high" if utilization_pct > 95 else "medium"
                })
            
            # Check if this has significant unutilized capacity
            if utilization_pct < 50:
                result["unutilized_capacity"].append({
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "utilization_pct": utilization_pct,
                    "unused_hours": available_hours - used_hours
                })
        
        return result
    
    def identify_capacity_constraints(self, scenario_id: int, start_year: int, end_year: int) -> Dict[str, Any]:
        """
        Identify capacity constraints and bottlenecks over a time period
        
        :param scenario_id: ID of the scenario
        :param start_year: First year of analysis
        :param end_year: Last year of analysis
        :return: Comprehensive capacity constraints analysis
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
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
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
            for eq_id, eq_data in utilization["equipment"].items():
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
        Model shift operations including overtime costs for a specific year
        
        :param scenario_id: ID of the scenario
        :param year: Year to analyze
        :param shift_config: Optional shift configuration
        :return: Shift operations analysis
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
        
        # Get equipment utilization
        utilization = self.calculate_equipment_utilization_by_product(scenario_id, year)
        
        if "error" in utilization:
            return utilization
        
        # Initialize result
        result = {
            "standard_hours_per_year": standard_hours_per_year,
            "max_overtime_hours_per_year": max_overtime_hours_per_year,
            "equipment_shift_analysis": {},
            "total_overtime_cost": 0,
            "shift_recommendations": []
        }
        
        # Analyze each equipment
        total_overtime_cost = 0
        for eq_id, eq_data in utilization["equipment"].items():
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
            # Get the average hourly cost for this equipment
            total_product_hours = 0
            total_cost = 0
            
            for prod_id, prod_data in eq_data["products"].items():
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.product_id == prod_id,
                        CostDriver.equipment_id == eq_id
                    )
                ).first()
                
                if cost_driver:
                    hours = prod_data["hours_used"]
                    hourly_cost = cost_driver.cost_per_hour
                    total_product_hours += hours
                    total_cost += hours * hourly_cost
            
            avg_hourly_cost = total_cost / total_product_hours if total_product_hours > 0 else 0
            overtime_cost = overtime_hours * avg_hourly_cost * shift_config["overtime_multiplier"]
            
            # Add to total overtime cost
            total_overtime_cost += overtime_cost
            
            # Store analysis for this equipment
            result["equipment_shift_analysis"][eq_id] = {
                "equipment_name": eq_data["equipment_name"],
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
                    "equipment_name": eq_data["equipment_name"],
                    "current_shifts": shift_config["shifts_per_day"],
                    "recommended_shifts": recommended_shifts,
                    "reason": f"Utilization requires {required_shifts:.2f} shifts"
                })
        
        # Store total overtime cost
        result["total_overtime_cost"] = total_overtime_cost
        
        return result
    
    def optimize_equipment_purchases(self, scenario_id: int, budget_constraint: float = None, 
                                     start_year: int = None, optimization_years: int = 5) -> Dict[str, Any]:
        """
        Optimize equipment purchases under budget constraints
        
        :param scenario_id: ID of the scenario
        :param budget_constraint: Optional total budget for equipment purchases
        :param start_year: Optional start year for optimization
        :param optimization_years: Number of years to optimize
        :return: Optimized equipment purchase plan
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Set default start year if not provided
        if start_year is None:
            start_year = 2025
        
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
            "budget_constraint": budget_constraint,
            "equipment_purchase_plan": {},
            "total_cost": 0,
            "bottlenecks_addressed": 0,
            "bottlenecks_remaining": []
        }
        
        # Simulate equipment purchases with budget constraint
        remaining_budget = budget_constraint
        for bottleneck in sorted_bottlenecks:
            eq_id = bottleneck["equipment_id"]
            
            if eq_id not in equipment_info:
                continue
                
            equipment = equipment_info[eq_id]
            purchase_year = bottleneck["year"]
            
            # Check if we have budget for this equipment
            if budget_constraint is None or equipment["cost"] <= remaining_budget:
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
                
                if budget_constraint is not None:
                    remaining_budget -= equipment["cost"]
            else:
                # We don't have budget for this equipment
                result["bottlenecks_remaining"].append(bottleneck)
        
        return result

def get_equipment_service(session):
    """
    Factory method to create EquipmentService
    
    :param session: SQLAlchemy database session
    :return: EquipmentService instance
    """
    return EquipmentService(session)

# Wrapper functions for ease of use
def calculate_production_capacity(equipment_id, year=None):
    """
    Wrapper for production capacity calculation
    
    :param equipment_id: ID of the equipment
    :param year: Optional year to check capacity
    :return: Capacity details
    """
    session = get_session()
    service = EquipmentService(session)
    return service.calculate_production_capacity(equipment_id, year)

def calculate_equipment_utilization(scenario_id, year):
    """
    Wrapper for equipment utilization calculation
    
    :param scenario_id: ID of the scenario
    :param year: Year to analyze
    :return: Utilization details
    """
    session = get_session()
    service = EquipmentService(session)
    return service.calculate_equipment_utilization_by_product(scenario_id, year)

def identify_capacity_constraints(scenario_id, start_year, end_year):
    """
    Wrapper for capacity constraints identification
    
    :param scenario_id: ID of the scenario
    :param start_year: First year of analysis
    :param end_year: Last year of analysis
    :return: Capacity constraints analysis
    """
    session = get_session()
    service = EquipmentService(session)
    return service.identify_capacity_constraints(scenario_id, start_year, end_year)

def model_shift_operations(scenario_id, year, shift_config=None):
    """
    Wrapper for shift operations modeling
    
    :param scenario_id: ID of the scenario
    :param year: Year to analyze
    :param shift_config: Optional shift configuration
    :return: Shift operations analysis
    """
    session = get_session()
    service = EquipmentService(session)
    return service.model_shift_operations(scenario_id, year, shift_config)

def optimize_equipment_purchases(scenario_id, budget_constraint=None, start_year=None, optimization_years=5):
    """
    Wrapper for equipment purchase optimization
    
    :param scenario_id: ID of the scenario
    :param budget_constraint: Optional total budget for equipment purchases
    :param start_year: Optional start year for optimization
    :param optimization_years: Number of years to optimize
    :return: Optimized equipment purchase plan
    """
    session = get_session()
    service = EquipmentService(session)
    return service.optimize_equipment_purchases(
        scenario_id, 
        budget_constraint, 
        start_year, 
        optimization_years
    )