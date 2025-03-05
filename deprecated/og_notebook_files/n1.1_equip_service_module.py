##Equipment Service Module - This core module contains all the functionality for:

# Calculating production capacity
# Analyzing equipment utilization by product
# Identifying capacity constraints and bottlenecks
# Modeling shift operations with overtime calculations
# Optimizing equipment purchases within budget constraints


# Equipment capacity and utilization service
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import and_

def calculate_production_capacity(equipment_id, year=None):
    """Calculate the maximum production capacity for a piece of equipment"""
    session = get_session()
    equipment = session.query(Equipment).filter(Equipment.id == equipment_id).first()
    
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
        
     def calculate_lease_costs(equipment_id, year):
    """Calculate lease costs for a piece of equipment for a specific year
    
    :param equipment_id: ID of the equipment
    :param year: Year to calculate costs for
    :return: Dictionary with lease cost details
    """
    session = get_session()
    equipment = session.query(Equipment).filter(Equipment.id == equipment_id).first()
    
    if not equipment or not equipment.is_leased:
        return {"annual_lease_cost": 0, "tax_deductible_amount": 0, "book_asset_value": 0}
    
    # Calculate years since purchase
    years_since_purchase = year - equipment.purchase_year
    
    # If not yet purchased or lease term ended
    if years_since_purchase < 0 or years_since_purchase >= (equipment.lease_term // 12):
        return {"annual_lease_cost": 0, "tax_deductible_amount": 0, "book_asset_value": 0}
    
    # Calculate annual lease cost
    annual_lease_cost = equipment.lease_payment * 12
    
    # Different accounting treatment based on lease type
    if equipment.lease_type == "standard":
        # Operating lease - fully tax deductible
        tax_deductible_amount = annual_lease_cost
        # No asset value on books
        book_asset_value = 0
    elif equipment.lease_type == "fmv_buyout":
        # Capital lease - treated more like a purchase
        # Calculate implicit asset value (present value of lease payments)
        total_payments = equipment.lease_payment * equipment.lease_term
        implicit_asset_value = total_payments * 0.9  # Approximate PV calculation
        
        # Calculate depreciation
        years_to_depreciate = max(5, equipment.lease_term // 12)  # Min 5 years or lease term
        annual_depreciation = implicit_asset_value / years_to_depreciate
        
        # Interest portion is deductible
        # Simplified calculation - in reality would use amortization schedule
        remaining_term = equipment.lease_term - (years_since_purchase * 12)
        interest_portion = annual_lease_cost * (remaining_term / equipment.lease_term) * 0.3  # Rough estimate
        
        tax_deductible_amount = interest_portion + annual_depreciation
        book_asset_value = implicit_asset_value - (annual_depreciation * years_since_purchase)
        if book_asset_value < 0:
            book_asset_value = 0
    else:
        # Default case
        tax_deductible_amount = annual_lease_cost
        book_asset_value = 0
    
    return {
        "annual_lease_cost": annual_lease_cost,
        "tax_deductible_amount": tax_deductible_amount,
        "book_asset_value": book_asset_value
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

def calculate_equipment_utilization_by_product(scenario_id, year):
    """Calculate detailed equipment utilization broken down by product"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get all equipment for this scenario
    equipment_list = session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
    
    # Get all products for this scenario
    products = session.query(Product).filter(Product.scenario_id == scenario_id).all()
    
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
            
        equipment_capacity = calculate_production_capacity(equipment.id, year)
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
            cost_driver = session.query(CostDriver).filter(
                CostDriver.product_id == product_id,
                CostDriver.equipment_id == equipment.id
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

def identify_capacity_constraints(scenario_id, start_year, end_year):
    """Identify capacity constraints and bottlenecks over a time period"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Initialize result
    result = {
        "bottlenecks_by_year": {},
        "equipment_utilization_trend": {},
        "capacity_expansion_recommendations": []
    }
    
    # Get all equipment
    equipment_list = session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
    equipment_ids = [e.id for e in equipment_list]
    
    # Track utilization trends for each equipment over the years
    utilization_trends = {e.id: {
        "equipment_name": e.name,
        "years": [],
        "utilization": []
    } for e in equipment_list}
    
    # Analyze each year
    for year in range(start_year, end_year + 1):
        # Calculate utilization for this year
        utilization = calculate_equipment_utilization_by_product(scenario_id, year)
        
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
                equipment = session.query(Equipment).filter(Equipment.id == eq_id).first()
                
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

def model_shift_operations(scenario_id, year, shift_config=None):
    """Model shift operations including overtime costs for a specific year"""
    session = get_session()
    
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
    utilization = calculate_equipment_utilization_by_product(scenario_id, year)
    
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
        equipment = session.query(Equipment).filter(Equipment.id == eq_id).first()
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
            cost_driver = session.query(CostDriver).filter(
                CostDriver.product_id == prod_id,
                CostDriver.equipment_id == eq_id
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

def optimize_equipment_purchases(scenario_id, budget_constraint=None, start_year=None, optimization_years=5):
    """Optimize equipment purchases under budget constraints"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Set default start year if not provided
    if start_year is None:
        start_year = 2025
    
    end_year = start_year + optimization_years - 1
    
    # Get capacity constraints analysis
    constraints = identify_capacity_constraints(scenario_id, start_year, end_year)
    
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
    
    # After sorting bottlenecks, before equipment purchase simulation
    # Add this code to consider lease vs. buy options
    lease_vs_buy_analysis = {}
    for bottleneck in sorted_bottlenecks:
        eq_id = bottleneck["equipment_id"]
        if eq_id in equipment_info:
            equipment = equipment_info[eq_id]
            
            # Calculate traditional purchase costs
            purchase_cost = equipment["cost"]
            annual_maintenance = purchase_cost * 0.05  # Assume 5% annual maintenance
            
            # Estimate lease costs (simplified)
            estimated_monthly_lease = purchase_cost / 60  # Rough estimate: cost/60 months
            annual_lease_cost = estimated_monthly_lease * 12
            
            # Calculate 5-year TCO for both options
            purchase_tco = purchase_cost + (annual_maintenance * 5)
            lease_tco = annual_lease_cost * 5
            
            # Store analysis
            lease_vs_buy_analysis[eq_id] = {
                "purchase_cost": purchase_cost,
                "purchase_tco": purchase_tco,
                "annual_lease_cost": annual_lease_cost,
                "lease_tco": lease_tco,
                "recommendation": "lease" if lease_tco < purchase_tco else "purchase"
            }
        
    # Get current equipment information
    equipment_info = {}
    for eq_id in bottlenecks:
        equipment = session.query(Equipment).filter(Equipment.id == eq_id).first()
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