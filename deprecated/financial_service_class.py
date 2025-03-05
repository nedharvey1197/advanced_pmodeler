import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import and_

class FinancialService:
    def __init__(self, session):
        """
        Initialize Financial Service with a database session
        
        :param session: SQLAlchemy database session
        """
        self.session = session
    
    def calculate_unit_economics(self, product_id):
        """
        Calculate the unit economics for a product
        
        :param product_id: ID of the product
        :return: Dictionary of unit economics metrics
        """
        product = self.session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return {"error": f"Product with ID {product_id} not found"}
        
        # Get all cost drivers for this product
        cost_drivers = self.session.query(CostDriver).filter(CostDriver.product_id == product_id).all()
        
        # Initialize costs
        equipment_costs = 0.0
        materials_costs = 0.0
        labor_costs = 0.0
        
        for cd in cost_drivers:
            # Equipment costs
            equipment_costs += cd.cost_per_hour * cd.hours_per_unit
            
            # Materials costs
            materials_costs += cd.materials_cost_per_unit
            
            # Labor costs
            labor_costs += (cd.machinist_labor_cost_per_hour * cd.machinist_hours_per_unit +
                            cd.design_labor_cost_per_hour * cd.design_hours_per_unit +
                            cd.supervision_cost_per_hour * cd.supervision_hours_per_unit)
        
        # Calculate unit cost
        unit_cost = equipment_costs + materials_costs + labor_costs
        
        # Calculate gross profit per unit and margin
        gross_profit_per_unit = product.unit_price - unit_cost
        gross_margin_pct = (gross_profit_per_unit / product.unit_price) * 100 if product.unit_price > 0 else 0
        
        return {
            "product_name": product.name,
            "unit_price": product.unit_price,
            "unit_cost": unit_cost,
            "equipment_costs": equipment_costs,
            "materials_costs": materials_costs,
            "labor_costs": labor_costs,
            "gross_profit_per_unit": gross_profit_per_unit,
            "gross_margin_pct": gross_margin_pct
        }
    
    def calculate_equipment_utilization(self, scenario_id, year):
        """
        Calculate equipment utilization for a given scenario and year
        
        :param scenario_id: ID of the scenario
        :param year: Year to calculate utilization
        :return: Dictionary of equipment utilization metrics
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get all equipment for this scenario
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
        # Get all products for this scenario
        products = self.session.query(Product).filter(Product.scenario_id == scenario_id).all()
        
        result = {
            "equipment_utilization": [],
            "total_capacity": 0,
            "used_capacity": 0
        }
        
        # Calculate production volume for each product in this year
        product_volumes = {}
        for product in products:
            # Calculate years since introduction
            years_since_intro = year - product.introduction_year
            
            # Skip if product hasn't been introduced yet
            if years_since_intro < 0:
                continue
                
            # Calculate production volume using compound growth
            volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
            product_volumes[product.id] = volume
        
        # Calculate utilization for each equipment
        for equipment in equipment_list:
            # Skip if equipment hasn't been purchased yet
            if equipment.purchase_year > year:
                continue
                
            total_hours_used = 0
            max_available_hours = equipment.max_capacity * equipment.availability_pct
            
            # Calculate hours used by each product on this equipment
            for product_id, volume in product_volumes.items():
                # Get cost driver for this product-equipment combination
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.product_id == product_id,
                        CostDriver.equipment_id == equipment.id
                    )
                ).first()
                
                if cost_driver:
                    hours_used = volume * cost_driver.hours_per_unit
                    total_hours_used += hours_used
            
            # Calculate utilization percentage
            utilization_pct = (total_hours_used / max_available_hours) * 100 if max_available_hours > 0 else 0
            
            result["equipment_utilization"].append({
                "equipment_id": equipment.id,
                "equipment_name": equipment.name,
                "max_capacity": max_available_hours,
                "used_capacity": total_hours_used,
                "utilization_pct": utilization_pct
            })
            
            result["total_capacity"] += max_available_hours
            result["used_capacity"] += total_hours_used
        
        # Calculate overall utilization
        result["overall_utilization_pct"] = (result["used_capacity"] / result["total_capacity"]) * 100 if result["total_capacity"] > 0 else 0
        
        return result
    
    def calculate_financial_projections(self, scenario_id, projection_years=5):
        """
        Generate comprehensive financial projections for a scenario
        
        :param scenario_id: ID of the scenario
        :param projection_years: Number of years to project
        :return: List of financial projections
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get products and equipment
        products = self.session.query(Product).filter(Product.scenario_id == scenario_id).all()
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
        # Clear existing projections
        self.session.query(FinancialProjection).filter(FinancialProjection.scenario_id == scenario_id).delete()
        
        # Projections list
        projections = []
        
        # Initial financial state
        initial_revenue = scenario.initial_revenue
        initial_costs = scenario.initial_costs
        
        for year in range(projection_years):
            # Calculate revenue
            current_revenue = initial_revenue * ((1 + scenario.annual_revenue_growth) ** year)
            
            # Calculate product-specific revenues
            product_revenues = {}
            total_product_revenue = 0
            for product in products:
                # Calculate years since introduction
                years_since_intro = year - product.introduction_year
                
                # Skip if product hasn't been introduced yet
                if years_since_intro < 0:
                    continue
                
                # Calculate product revenue
                product_volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
                product_revenue = product_volume * product.unit_price
                
                product_revenues[product.name] = product_revenue
                total_product_revenue += product_revenue
            
            # Calculate costs
            current_costs = initial_costs * ((1 + scenario.annual_cost_growth) ** year)
            
            # Calculate equipment depreciation
            total_depreciation = sum([
                equipment.cost / equipment.useful_life 
                for equipment in equipment_list 
                if equipment.purchase_year <= year
            ])
            
            # Calculate EBITDA
            ebitda = current_revenue - current_costs
            
            # Calculate interest expense
            total_debt = scenario.debt_ratio * current_revenue
            interest_expense = total_debt * scenario.interest_rate
            
            # Calculate taxable income
            ebit = ebitda - total_depreciation - interest_expense
            
            # Calculate taxes
            tax_expense = max(0, ebit * scenario.tax_rate)
            
            # Calculate net income
            net_income = ebit - tax_expense
            
            # Create financial projection
            projection = FinancialProjection(
                scenario_id=scenario_id,
                year=year,
                
                # Income Statement
                revenue=current_revenue,
                cogs=current_costs,
                gross_profit=current_revenue - current_costs,
                operating_expenses=current_costs,
                ebitda=ebitda,
                depreciation=total_depreciation,
                ebit=ebit,
                interest=interest_expense,
                tax=tax_expense,
                net_income=net_income,
                
                # Additional Details
                product_details=product_revenues,
                total_production=sum(product_revenues.values()),
                
                # Utilization
                **self._calculate_utilization_details(scenario_id, year)
            )
            
            projections.append(projection)
            self.session.add(projection)
        
        # Commit projections
        self.session.commit()
        
        return projections
    
    def _calculate_utilization_details(self, scenario_id, year):
        """
        Calculate detailed utilization metrics for a given scenario and year
        
        :param scenario_id: ID of the scenario
        :param year: Year to calculate utilization
        :return: Dictionary of utilization metrics
        """
        utilization = self.calculate_equipment_utilization(scenario_id, year)
        
        return {
            "capacity_utilization": utilization.get("overall_utilization_pct", 0)
        }
    
    def calculate_key_financial_metrics(self, scenario_id):
        """
        Calculate key financial metrics for a scenario
        
        :param scenario_id: ID of the scenario
        :return: Dictionary of key financial metrics
        """
        # Get financial projections
        projections = self.session.query(FinancialProjection).filter(
            FinancialProjection.scenario_id == scenario_id
        ).order_by(FinancialProjection.year).all()
        
        if not projections:
            return {"error": "No financial projections found"}
        
        # Calculate EBITDA Margin
        ebitda_margin = [{
            "year": p.year,
            "value": (p.ebitda / p.revenue * 100) if p.revenue > 0 else 0
        } for p in projections]
        
        # Calculate Revenue CAGR
        first_year_revenue = projections[0].revenue
        last_year_revenue = projections[-1].revenue
        years = len(projections) - 1
        revenue_cagr = (last_year_revenue / first_year_revenue) ** (1/years) - 1 if first_year_revenue > 0 and years > 0 else 0
        
        # Calculate ROI (simplified)
        # Assuming initial investment is the first year's capital expenditure
        initial_investment = sum(
            equipment.cost for equipment in 
            self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        )
        total_net_income = sum(p.net_income for p in projections)
        
        roi = (total_net_income / initial_investment) * 100 if initial_investment > 0 else 0
        
        # Calculate Payback Period (simplified)
        cumulative_net_income = 0
        payback_period = None
        for p in projections:
            cumulative_net_income += p.net_income
            if cumulative_net_income >= initial_investment:
                payback_period = p.year
                break
        
        return {
            "ebitda_margin": ebitda_margin,
            "revenue_cagr": revenue_cagr,
            "roi": roi,
            "payback_period": payback_period or len(projections),
            "net_income": [p.net_income for p in projections]
        }

# Wrapper functions for ease of use
def calculate_financial_projections(scenario_id, projection_years=5):
    """
    Wrapper function for financial projections calculation
    
    :param scenario_id: ID of the scenario
    :param projection_years: Number of years to project
    :return: Calculation results
    """
    session = get_session()
    financial_service = FinancialService(session)
    return financial_service.calculate_financial_projections(scenario_id, projection_years)

def calculate_key_financial_metrics(scenario_id):
    """
    Wrapper function for key financial metrics calculation
    
    :param scenario_id: ID of the scenario
    :return: Key financial metrics
    """
    session = get_session()
    financial_service = FinancialService(session)
    return financial_service.calculate_key_financial_metrics(scenario_id)

def clone_scenario(session, source_scenario_id, new_name, new_description):
    """
    Clone an existing scenario with all its data
    
    :param session: Database session
    :param source_scenario_id: ID of the original scenario
    :param new_name: Name for the new scenario
    :param new_description: Description for the new scenario
    :return: Newly created scenario
    """
    # Get the original scenario
    original = session.query(Scenario).filter(Scenario.id == source_scenario_id).first()
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
            lease_rate=old_equipment.lease_rate
        )
        session.add(new_equipment)
        session.commit()
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
        session.add(new_product)
        session.commit()
        product_map[old_product.id] = new_product.id
    
    # Clone cost drivers
    for old_cost_driver in session.query(CostDriver).filter(
        CostDriver.product_id.in_(list(product_map.keys())),
        CostDriver.equipment_id.in_(list(equipment_map.keys()))
    ).all():
        new_cost_driver = CostDriver(
            product_id=product_map[old_cost_driver.product_id],
            equipment_id=equipment_map[old_cost_driver.equipment_id],
            cost_per_hour=old_cost_driver.cost_per_hour,
            hours_per_unit=old_cost_driver.hours_per_unit,
            materials_cost_per_unit=old_cost_driver.materials_cost_per_unit,
            machinist_labor_cost_per_hour=old_cost_driver.machinist_labor_cost_per_hour,
            machinist_hours_per_unit=old_cost_driver.machinist_hours_per_unit,
            design_labor_cost_per_hour=old_cost_driver.design_labor_cost_per_hour,
            design_hours_per_unit=old_cost_driver.design_hours_per_unit,
            supervision_cost_per_hour=old_cost_driver.supervision_cost_per_hour,
            supervision_hours_per_unit=old_cost_driver.supervision_hours_per_unit
        )
        session.add(new_cost_driver)
    
    session.commit()
    return new_scenario