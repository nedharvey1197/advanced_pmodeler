"""
Database utilities module for the manufacturing expansion financial model.

This module provides essential database operations and data migration functionality:
- JSON data loading and database migration
- Scenario management (CRUD operations)
- Equipment management
- Product management
- Cost driver management
- Scenario cloning with related data
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)

def load_json_data(file_path="financial_model_data.json") -> Dict[str, Any]:
    """
    Load data from a JSON file containing financial model data.
    
    Args:
        file_path (str): Path to the JSON file containing model data
        
    Returns:
        Dict[str, Any]: Dictionary containing equipment, products, and cost drivers data
                       Returns empty structure if file not found
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {file_path} not found. Returning empty data structure.")
        return {"equipment": [], "products": [], "cost_drivers": {}}
        
def migrate_data_to_database(json_data: Dict[str, Any]) -> int:
    """
    Migrate data from JSON format to SQLite database.
    
    Args:
        json_data (Dict[str, Any]): Dictionary containing model data
        
    Returns:
        int: ID of the created base scenario
    """
    session = get_session()
    
    # Create a base scenario
    base_scenario = Scenario(
        name="Base Case",
        description="Initial scenario migrated from JSON data",
        is_base_case=True
    )
    session.add(base_scenario)
    session.commit()
    
    # Add equipment
    equipment_map = {}  # To map old equipment names to new IDs
    for eq_data in json_data.get("equipment", []):
        equipment = Equipment(
            scenario_id=base_scenario.id,
            name=eq_data.get("Name", "Unknown Equipment"),
            cost=eq_data.get("Cost", 0.0),
            useful_life=eq_data.get("Useful Life", 10),
            max_capacity=eq_data.get("Max Capacity", 1000),
            maintenance_cost_pct=eq_data.get("Maintenance Cost Pct", 0.05),
            availability_pct=eq_data.get("Availability Pct", 0.95),
            purchase_year=eq_data.get("Purchase Year", 2025),
            is_leased=eq_data.get("Is Leased", False),
            lease_rate=eq_data.get("Lease Rate", 0.0),
            lease_type=eq_data.get("Lease Type", "none"),
            lease_term=eq_data.get("Lease Term", 0),
            lease_payment=eq_data.get("Lease Payment", 0.0)
        )
        session.add(equipment)
        session.commit()
        equipment_map[equipment.name] = equipment.id
    
    # Add products
    product_map = {}
    for prod_data in json_data.get("products", []):
        product = Product(
            scenario_id=base_scenario.id,
            name=prod_data.get("Name", "Unknown Product"),
            initial_units=prod_data.get("Initial Units", 0),
            unit_price=prod_data.get("Unit Price", 0.0),
            growth_rate=prod_data.get("Growth Rate", 0.1),
            introduction_year=prod_data.get("Introduction Year", 2025),
            market_size=prod_data.get("Market Size", None),
            price_elasticity=prod_data.get("Price Elasticity", -1.0)
        )
        session.add(product)
        session.commit()
        product_map[product.name] = product.id
    
    # Add cost drivers
    for product_name, drivers in json_data.get("cost_drivers", {}).items():
        if product_name not in product_map:
            continue
            
        product_id = product_map[product_name]
        
        # Add equipment costs
        for eq_name, eq_costs in drivers.get("Equipment Costs", {}).items():
            if eq_name not in equipment_map:
                continue
                
            equipment_id = equipment_map[eq_name]
            cost_driver = CostDriver(
                product_id=product_id,
                equipment_id=equipment_id,
                cost_per_hour=eq_costs.get("Cost Per Hour", 0.0),
                hours_per_unit=eq_costs.get("Hours Per Unit", 0.0),
                materials_cost_per_unit=drivers.get("Materials Cost", {}).get("Cost Per Unit", 0.0)
            )
            
            # Add labor costs
            if "Machinist Labor" in drivers:
                cost_driver.machinist_labor_cost_per_hour = drivers["Machinist Labor"].get("Cost Per Hour", 30.0)
                cost_driver.machinist_hours_per_unit = drivers["Machinist Labor"].get("Hours Per Unit", 2.0)
                
            if "Design Labor" in drivers:
                cost_driver.design_labor_cost_per_hour = drivers["Design Labor"].get("Cost Per Hour", 40.0)
                cost_driver.design_hours_per_unit = drivers["Design Labor"].get("Hours Per Unit", 1.0)
                
            if "Supervision" in drivers:
                cost_driver.supervision_cost_per_hour = drivers["Supervision"].get("Cost Per Hour", 20.0)
                cost_driver.supervision_hours_per_unit = drivers["Supervision"].get("Hours Per Unit", 0.5)
                
            session.add(cost_driver)
    
    session.commit()
    return base_scenario.id

def export_scenario_to_json(scenario_id, file_path="exported_scenario.json"):
    """Export a scenario with all related data to JSON"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Build JSON structure
    data = {
        "scenario": {
            "name": scenario.name,
            "description": scenario.description,
            "financial_assumptions": {
                "initial_revenue": scenario.initial_revenue,
                "initial_costs": scenario.initial_costs,
                "annual_revenue_growth": scenario.annual_revenue_growth,
                "annual_cost_growth": scenario.annual_cost_growth,
                "debt_ratio": scenario.debt_ratio,
                "interest_rate": scenario.interest_rate,
                "tax_rate": scenario.tax_rate
            }
        },
        "equipment": [],
        "products": [],
        "cost_drivers": {},
        "financial_projections": []
    }
    
    # Add equipment
    for eq in scenario.equipment:
        data["equipment"].append({
            "id": eq.id,
            "name": eq.name,
            "cost": eq.cost,
            "useful_life": eq.useful_life,
            "max_capacity": eq.max_capacity,
            "maintenance_cost_pct": eq.maintenance_cost_pct,
            "availability_pct": eq.availability_pct,
            "purchase_year": eq.purchase_year,
            "is_leased": eq.is_leased,
            "lease_rate": eq.lease_rate,
            "lease_type": eq.lease_type,
            "lease_term": eq.lease_term,
            "lease_payment": eq.lease_payment
        })
    
    # Add products and cost drivers
    for prod in scenario.products:
        data["products"].append({
            "id": prod.id,
            "name": prod.name,
            "initial_units": prod.initial_units,
            "unit_price": prod.unit_price,
            "growth_rate": prod.growth_rate,
            "introduction_year": prod.introduction_year,
            "market_size": prod.market_size,
            "price_elasticity": prod.price_elasticity
        })
        
        # Add cost drivers for this product
        data["cost_drivers"][prod.name] = {
            "equipment_costs": {},
            "labor_costs": {}
        }
        
        for cd in prod.cost_drivers:
            eq = session.query(Equipment).filter(Equipment.id == cd.equipment_id).first()
            data["cost_drivers"][prod.name]["equipment_costs"][eq.name] = {
                "cost_per_hour": cd.cost_per_hour,
                "hours_per_unit": cd.hours_per_unit
            }
            
            data["cost_drivers"][prod.name]["labor_costs"] = {
                "materials_cost_per_unit": cd.materials_cost_per_unit,
                "machinist": {
                    "cost_per_hour": cd.machinist_labor_cost_per_hour,
                    "hours_per_unit": cd.machinist_hours_per_unit
                },
                "design": {
                    "cost_per_hour": cd.design_labor_cost_per_hour,
                    "hours_per_unit": cd.design_hours_per_unit
                },
                "supervision": {
                    "cost_per_hour": cd.supervision_cost_per_hour,
                    "hours_per_unit": cd.supervision_hours_per_unit
                }
            }
    
    # Add financial projections
    for fp in scenario.financials:
        data["financial_projections"].append({
            "year": fp.year,
            "income_statement": {
                "revenue": fp.revenue,
                "cogs": fp.cogs,
                "gross_profit": fp.gross_profit,
                "operating_expenses": fp.operating_expenses,
                "ebitda": fp.ebitda,
                "depreciation": fp.depreciation,
                "ebit": fp.ebit,
                "interest": fp.interest,
                "tax": fp.tax,
                "net_income": fp.net_income
            },
            "balance_sheet": {
                "cash": fp.cash,
                "accounts_receivable": fp.accounts_receivable,
                "inventory": fp.inventory,
                "fixed_assets": fp.fixed_assets,
                "accumulated_depreciation": fp.accumulated_depreciation,
                "total_assets": fp.total_assets,
                "accounts_payable": fp.accounts_payable,
                "short_term_debt": fp.short_term_debt,
                "long_term_debt": fp.long_term_debt,
                "equity": fp.equity,
                "total_liabilities_and_equity": fp.total_liabilities_and_equity
            },
            "cash_flow": {
                "operating_cash_flow": fp.operating_cash_flow,
                "investing_cash_flow": fp.investing_cash_flow,
                "financing_cash_flow": fp.financing_cash_flow,
                "net_cash_flow": fp.net_cash_flow
            },
            "production": {
                "total_production": fp.total_production,
                "capacity_utilization": fp.capacity_utilization
            },
            "product_details": fp.product_details
        })
    
    # Write to file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    return data

def get_scenario_by_id(scenario_id: int) -> Optional[Scenario]:
    """
    Retrieve a scenario by its ID.
    
    Args:
        scenario_id (int): ID of the scenario to retrieve
        
    Returns:
        Optional[Scenario]: The scenario if found, None otherwise
    """
    session = get_session()
    return session.query(Scenario).filter(Scenario.id == scenario_id).first()

def get_all_scenarios() -> List[Scenario]:
    """
    Retrieve all scenarios from the database.
    
    Returns:
        List[Scenario]: List of all scenarios
    """
    session = get_session()
    return session.query(Scenario).all()

def get_equipment_by_scenario(scenario_id: int) -> List[Equipment]:
    """
    Retrieve all equipment associated with a scenario.
    
    Args:
        scenario_id (int): ID of the scenario
        
    Returns:
        List[Equipment]: List of equipment for the scenario
    """
    session = get_session()
    return session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()

def get_products_by_scenario(scenario_id: int) -> List[Product]:
    """
    Retrieve all products associated with a scenario.
    
    Args:
        scenario_id (int): ID of the scenario
        
    Returns:
        List[Product]: List of products for the scenario
    """
    session = get_session()
    return session.query(Product).filter(Product.scenario_id == scenario_id).all()

def get_cost_drivers_by_product(product_id: int) -> List[CostDriver]:
    """
    Retrieve all cost drivers associated with a product.
    
    Args:
        product_id (int): ID of the product
        
    Returns:
        List[CostDriver]: List of cost drivers for the product
    """
    session = get_session()
    return session.query(CostDriver).filter(CostDriver.product_id == product_id).all()

def delete_scenario(scenario_id: int) -> bool:
    """
    Delete a scenario and all its related records.
    
    Args:
        scenario_id (int): ID of the scenario to delete
        
    Returns:
        bool: True if deletion successful, False if scenario not found
    """
    session = get_session()
    
    # Find scenario
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        return False
    
    # Delete it (cascade should take care of related records)
    session.delete(scenario)
    session.commit()
    return True

def create_scenario(name: str, description: str, **kwargs) -> Scenario:
    """
    Create a new scenario.
    
    Args:
        name (str): Name of the scenario
        description (str): Description of the scenario
        **kwargs: Additional scenario parameters
        
    Returns:
        Scenario: The created scenario
    """
    session = get_session()
    scenario = Scenario(
        name=name,
        description=description,
        **kwargs
    )
    session.add(scenario)
    session.commit()
    return scenario

def create_equipment(scenario_id: int, name: str, cost: float, useful_life: int, max_capacity: float, **kwargs) -> Equipment:
    """
    Create a new equipment record.
    
    Args:
        scenario_id (int): ID of the associated scenario
        name (str): Name of the equipment
        cost (float): Cost of the equipment
        useful_life (int): Useful life in years
        max_capacity (float): Maximum capacity
        **kwargs: Additional equipment parameters
        
    Returns:
        Equipment: The created equipment record
    """
    session = get_session()
    equipment = Equipment(
        scenario_id=scenario_id,
        name=name,
        cost=cost,
        useful_life=useful_life,
        max_capacity=max_capacity,
        **kwargs
    )
    session.add(equipment)
    session.commit()
    return equipment

def create_product(scenario_id: int, name: str, initial_units: int, unit_price: float, growth_rate: float, **kwargs) -> Product:
    """
    Create a new product record.
    
    Args:
        scenario_id (int): ID of the associated scenario
        name (str): Name of the product
        initial_units (int): Initial number of units
        unit_price (float): Price per unit
        growth_rate (float): Annual growth rate
        **kwargs: Additional product parameters
        
    Returns:
        Product: The created product record
    """
    session = get_session()
    product = Product(
        scenario_id=scenario_id,
        name=name,
        initial_units=initial_units,
        unit_price=unit_price,
        growth_rate=growth_rate,
        **kwargs
    )
    session.add(product)
    session.commit()
    return product

def create_cost_driver(product_id: int, equipment_id: int, cost_per_hour: float, hours_per_unit: float, **kwargs) -> CostDriver:
    """
    Create a new cost driver record.
    
    Args:
        product_id (int): ID of the associated product
        equipment_id (int): ID of the associated equipment
        cost_per_hour (float): Cost per hour of operation
        hours_per_unit (float): Hours required per unit
        **kwargs: Additional cost driver parameters
        
    Returns:
        CostDriver: The created cost driver record
    """
    session = get_session()
    cost_driver = CostDriver(
        product_id=product_id,
        equipment_id=equipment_id,
        cost_per_hour=cost_per_hour,
        hours_per_unit=hours_per_unit,
        **kwargs
    )
    session.add(cost_driver)
    session.commit()
    return cost_driver

def clone_scenario(scenario_id: int, new_name: str, new_description: str) -> Optional[Scenario]:
    """
    Clone an existing scenario with all its related data.
    
    Args:
        scenario_id (int): ID of the scenario to clone
        new_name (str): Name for the new scenario
        new_description (str): Description for the new scenario
        
    Returns:
        Optional[Scenario]: The cloned scenario if successful, None if original not found
    """
    session = get_session()
    
    # Get the original scenario
    original = session.query(Scenario).filter(Scenario.id == scenario_id).first()
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
    session.add(new_scenario)
    session.commit()
    
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
        session.add(new_equipment)
        session.commit()
        equipment_map[old_equipment.id] = new_equipment.id
    
    # Clone products
    product_map = {}
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
        session.add(new_product)
        session.commit()
        product_map[old_product.id] = new_product.id
    
    # Clone cost drivers
    for old_driver in original.cost_drivers:
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
        session.add(new_driver)
    
    session.commit()
    return new_scenario
