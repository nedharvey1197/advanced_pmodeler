"""
Financial service module for the manufacturing expansion financial model.

This module provides comprehensive financial modeling capabilities including:
- Unit economics calculation
- Equipment utilization tracking
- Financial projections generation
- Key financial metrics computation
- Scenario cloning and management
- Integration with advanced financial modeling
- Support for optimization-based projections

For detailed information about the integration between basic and advanced financial modeling,
see financial_modeling_README.md
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import and_

from advanced_pmodeler.models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session, ServiceMixin
)
# Advanced financial modeling service - will be used for future features
# from .advanced_fin_Services import AdvancedFinancialModeling

class FinancialService(ServiceMixin):
    """
    Service class for financial modeling and analysis.
    
    This class provides methods for calculating various financial metrics,
    generating projections, and managing financial scenarios.
    
    For advanced financial modeling capabilities, use get_advanced_modeling()
    to access the AdvancedFinancialModeling instance.
    """
    
    def __init__(self, session):
        """
        Initialize FinancialService with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._advanced_modeling = None
    
    def get_advanced_modeling(self) -> AdvancedFinancialModeling:
        """
        Get or create the AdvancedFinancialModeling instance.
        
        Returns:
            AdvancedFinancialModeling instance for advanced financial analysis
        """
        if not self._advanced_modeling:
            scenario = self.session.query(Scenario).first()
            if not scenario:
                raise ValueError("No scenario found in the database")
            self._advanced_modeling = AdvancedFinancialModeling(scenario, self.session)
        return self._advanced_modeling
    
    def get_comprehensive_analysis(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get both basic and advanced financial analysis for a scenario.
        
        Args:
            scenario_id: ID of the scenario to analyze
            
        Returns:
            Dictionary containing both basic and advanced analysis results
        """
        # Get basic metrics
        basic_metrics = self.calculate_key_financial_metrics(scenario_id)
        
        # Get financial projections
        projections = self.calculate_financial_projections(scenario_id)
        
        # Get advanced analysis
        advanced_analysis = self.get_advanced_modeling()
        advanced_metrics = advanced_analysis.generate_comprehensive_financial_analysis(projections)
        
        return {
            "basic_metrics": basic_metrics,
            "advanced_analysis": advanced_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_risk_adjusted_metrics(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get risk-adjusted financial metrics using advanced modeling.
        
        Args:
            scenario_id: ID of the scenario to analyze
            
        Returns:
            Dictionary containing risk-adjusted metrics
        """
        projections = self.calculate_financial_projections(scenario_id)
        advanced_analysis = self.get_advanced_modeling()
        
        # Get risk-adjusted cash flow
        cash_flow_analysis = advanced_analysis.calculate_advanced_cash_flow(projections)
        
        # Get tax optimization
        tax_analysis = advanced_analysis.calculate_advanced_tax_strategy(projections)
        
        return {
            "risk_adjusted_cash_flow": cash_flow_analysis,
            "tax_optimization": tax_analysis,
            "risk_factors": advanced_analysis.risk_factors,
            "working_capital": advanced_analysis.working_capital_params
        }
    
    def calculate_unit_economics(self, product_id: int) -> Dict[str, Any]:
        """
        Calculate unit economics for a specific product.
        
        Args:
            product_id: ID of the product to analyze
            
        Returns:
            Dictionary containing unit economics metrics including:
            - Product name and unit price
            - Unit cost breakdown (equipment, materials, labor)
            - Gross profit and margin
        """
        product = self.session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": f"Product with ID {product_id} not found"}
        
        # Get cost drivers for this product
        cost_drivers = self.session.query(CostDriver).filter(
            CostDriver.product_id == product_id
        ).all()
        
        # Calculate total unit cost
        unit_cost = 0
        equipment_costs = {}
        materials_costs = {}
        labor_costs = {}
        
        for driver in cost_drivers:
            # Equipment costs
            equipment_cost = driver.cost_per_hour * driver.hours_per_unit
            equipment_costs[driver.equipment.name] = equipment_cost
            unit_cost += equipment_cost
            
            # Materials costs
            materials_costs[driver.equipment.name] = driver.materials_cost_per_unit
            unit_cost += driver.materials_cost_per_unit
            
            # Labor costs
            labor_costs[driver.equipment.name] = {
                "machinist": driver.machinist_labor_cost_per_hour * driver.machinist_hours_per_unit,
                "design": driver.design_labor_cost_per_hour * driver.design_hours_per_unit,
                "supervision": driver.supervision_cost_per_hour * driver.supervision_hours_per_unit
            }
            unit_cost += sum(labor_costs[driver.equipment.name].values())
        
        # Calculate gross profit and margin
        gross_profit_per_unit = product.unit_price - unit_cost
        gross_margin_pct = (gross_profit_per_unit / product.unit_price * 100) if product.unit_price > 0 else 0
        
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
    
    def calculate_equipment_utilization(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Calculate equipment utilization for a given scenario and year.
        
        Args:
            scenario_id: ID of the scenario to analyze
            year: Year to calculate utilization for
            
        Returns:
            Dictionary containing utilization metrics including:
            - Equipment-specific utilization rates
            - Total and used capacity
            - Overall utilization percentage
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
            "equipment_utilization": [],
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
            
            # Calculate used capacity
            used_capacity = 0
            for product_id, volume in product_volumes.items():
                cost_driver = self.session.query(CostDriver).filter(
                    and_(
                        CostDriver.equipment_id == equipment.id,
                        CostDriver.product_id == product_id
                    )
                ).first()
                
                if cost_driver:
                    used_capacity += volume * cost_driver.hours_per_unit
            
            result["used_capacity"] += used_capacity
            
            # Calculate utilization percentage
            utilization_pct = (used_capacity / available_capacity * 100) if available_capacity > 0 else 0
            
            result["equipment_utilization"].append({
                "equipment_id": equipment.id,
                "equipment_name": equipment.name,
                "available_capacity": available_capacity,
                "used_capacity": used_capacity,
                "utilization_pct": utilization_pct
            })
        
        # Calculate overall utilization
        result["overall_utilization_pct"] = (
            (result["used_capacity"] / result["total_capacity"] * 100)
            if result["total_capacity"] > 0 else 0
        )
        
        return result
    
    def calculate_financial_projections(self, scenario_id: int,
                                     projection_years: int = 5,
                                     use_optimization: bool = False,
                                     optimization_results: Optional[Dict[str, Any]] = None) -> List[FinancialProjection]:
        """
        Generate comprehensive financial projections for a scenario.
        
        Args:
            scenario_id: ID of the scenario to project
            projection_years: Number of years to project (default: 5)
            use_optimization: Whether to use optimization results
            optimization_results: Optional optimization results to apply
            
        Returns:
            List of FinancialProjection objects containing:
            - Income statement metrics
            - Balance sheet metrics
            - Cash flow metrics
            - Production metrics
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get products and equipment
        products = self.session.query(Product).filter(Product.scenario_id == scenario_id).all()
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
        # Clear existing projections
        self.session.query(FinancialProjection).filter(
            FinancialProjection.scenario_id == scenario_id
        ).delete()
        
        projections = []
        initial_revenue = scenario.initial_revenue
        initial_costs = scenario.initial_costs
        
        # Apply optimization impacts if requested
        if use_optimization and optimization_results:
            initial_revenue *= optimization_results.get("revenue_impact", 1.0)
            initial_costs *= optimization_results.get("cost_impact", 1.0)
        
        for year in range(projection_years):
            # Calculate revenue with optimization impact
            current_revenue = initial_revenue * ((1 + scenario.annual_revenue_growth) ** year)
            if use_optimization and optimization_results:
                current_revenue *= optimization_results.get("revenue_impact", 1.0)
            
            # Calculate product-specific revenues
            product_revenues = {}
            total_product_revenue = 0
            for product in products:
                years_since_intro = year - product.introduction_year
                if years_since_intro < 0:
                    continue
                product_volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
                product_revenue = product_volume * product.unit_price
                product_revenues[product.name] = product_revenue
                total_product_revenue += product_revenue
            
            # Calculate costs with optimization impact
            current_costs = initial_costs * ((1 + scenario.annual_cost_growth) ** year)
            if use_optimization and optimization_results:
                current_costs *= optimization_results.get("cost_impact", 1.0)
            
            # Calculate equipment costs
            total_depreciation = 0
            total_lease_costs = 0
            total_tax_deductible_lease = 0
            
            for equipment in equipment_list:
                if equipment.purchase_year > year:
                    continue
                    
                if not equipment.is_leased:
                    if year < equipment.purchase_year + equipment.useful_life:
                        annual_depreciation = equipment.cost / equipment.useful_life
                        total_depreciation += annual_depreciation
                else:
                    lease_costs = self._calculate_lease_costs(equipment.id, year)
                    if equipment.lease_type == "standard":
                        total_lease_costs += lease_costs["annual_lease_cost"]
                        total_tax_deductible_lease += lease_costs["tax_deductible_amount"]
                    elif equipment.lease_type == "fmv_buyout":
                        if lease_costs["book_asset_value"] > 0:
                            years_to_depreciate = max(5, equipment.lease_term // 12)
                            annual_depreciation = (
                                lease_costs["book_asset_value"] + lease_costs["annual_lease_cost"]
                            ) / years_to_depreciate
                            total_depreciation += annual_depreciation
                        total_lease_costs += lease_costs["annual_lease_cost"]
                        total_tax_deductible_lease += lease_costs["tax_deductible_amount"]
            
            # Apply optimization impacts to equipment costs
            if use_optimization and optimization_results:
                equipment_impact = optimization_results.get("equipment_impact", 1.0)
                total_depreciation *= equipment_impact
                total_lease_costs *= equipment_impact
                total_tax_deductible_lease *= equipment_impact
            
            # Calculate financial metrics
            ebitda = current_revenue - current_costs
            total_debt = scenario.debt_ratio * current_revenue
            interest_expense = total_debt * scenario.interest_rate
            ebit = ebitda - total_depreciation - total_tax_deductible_lease - interest_expense
            tax_expense = max(0, ebit * scenario.tax_rate)
            net_income = ebit - tax_expense
            
            # Create projection
            projection = FinancialProjection(
                scenario_id=scenario_id,
                year=year,
                revenue=current_revenue,
                cogs=current_costs,
                gross_profit=current_revenue - current_costs,
                operating_expenses=current_costs + total_lease_costs,
                ebitda=ebitda,
                depreciation=total_depreciation,
                ebit=ebit,
                interest=interest_expense,
                tax=tax_expense,
                net_income=net_income,
                product_details=product_revenues,
                total_production=sum(product_revenues.values()),
                **self._calculate_utilization_details(scenario_id, year)
            )
            
            projections.append(projection)
            self.session.add(projection)
        
        self.session.commit()
        return projections
    
    def calculate_key_financial_metrics(self, scenario_id: int) -> Dict[str, Any]:
        """
        Calculate key financial metrics for a scenario.
        
        Args:
            scenario_id: ID of the scenario to analyze
            
        Returns:
            Dictionary containing key financial metrics including:
            - EBITDA margin trends
            - Revenue CAGR
            - ROI
            - Payback period
        """
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
        revenue_cagr = (
            (last_year_revenue / first_year_revenue) ** (1/years) - 1
            if first_year_revenue > 0 and years > 0 else 0
        )
        
        # Calculate ROI
        initial_investment = sum(
            equipment.cost for equipment in 
            self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        )
        total_net_income = sum(p.net_income for p in projections)
        roi = (total_net_income / initial_investment * 100) if initial_investment > 0 else 0
        
        # Calculate Payback Period
        cumulative_net_income = 0
        payback_period = None
        for p in projections:
            cumulative_net_income += p.net_income
            if cumulative_net_income >= initial_investment:
                payback_period = p.year
                break
        
        return {
            "ebitda_margin": ebitda_margin,
            "revenue_cagr": revenue_cagr * 100,  # Convert to percentage
            "roi": roi,
            "payback_period": payback_period,
            "initial_investment": initial_investment,
            "total_net_income": total_net_income
        }
    
    def _calculate_lease_costs(self, equipment_id: int, year: int) -> Dict[str, float]:
        """
        Calculate lease costs for a piece of equipment in a given year.
        
        Args:
            equipment_id: ID of the equipment
            year: Year to calculate costs for
            
        Returns:
            Dictionary containing lease cost details
        """
        equipment = self.session.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment or not equipment.is_leased:
            return {
                "annual_lease_cost": 0,
                "tax_deductible_amount": 0,
                "book_asset_value": 0
            }
        
        # Calculate annual lease cost
        annual_lease_cost = equipment.lease_rate * equipment.cost
        
        # Calculate tax deductible amount
        tax_deductible_amount = annual_lease_cost
        
        # Calculate book asset value for capital leases
        book_asset_value = 0
        if equipment.lease_type == "fmv_buyout":
            # For FMV buyout leases, treat as capital lease
            book_asset_value = equipment.cost * 0.1  # Assume 10% FMV
        
        return {
            "annual_lease_cost": annual_lease_cost,
            "tax_deductible_amount": tax_deductible_amount,
            "book_asset_value": book_asset_value
        }
    
    def _calculate_utilization_details(self, scenario_id: int, year: int) -> Dict[str, float]:
        """
        Calculate detailed utilization metrics for a scenario and year.
        
        Args:
            scenario_id: ID of the scenario
            year: Year to calculate metrics for
            
        Returns:
            Dictionary containing utilization metrics
        """
        utilization = self.calculate_equipment_utilization(scenario_id, year)
        return {
            "capacity_utilization": utilization.get("overall_utilization_pct", 0)
        }

    def calculate_financial_projection(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """Calculate financial projection for a specific year."""
        from .equipment_service import EquipmentService
        from .sales_service import SalesService
        
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
            
        # Get services through session
        equipment_service = self._get_service(EquipmentService)
        sales_service = self._get_service(SalesService)
        
        # Calculate projections
        utilization = equipment_service.calculate_equipment_utilization(scenario_id, year)
        sales_forecast = sales_service.calculate_sales_forecast(scenario_id, year, year)
        
        return self._calculate_projection(scenario, year, utilization, sales_forecast)

# Wrapper functions for easy access
def calculate_unit_economics(product_id: int) -> Dict[str, Any]:
    """Wrapper function for unit economics calculation."""
    session = get_session()
    service = FinancialService(session)
    return service.calculate_unit_economics(product_id)

def calculate_equipment_utilization(scenario_id: int, year: int) -> Dict[str, Any]:
    """Wrapper function for equipment utilization calculation."""
    session = get_session()
    service = FinancialService(session)
    return service.calculate_equipment_utilization(scenario_id, year)

def calculate_financial_projections(scenario_id: int, projection_years: int = 5) -> List[FinancialProjection]:
    """Wrapper function for financial projections calculation."""
    session = get_session()
    service = FinancialService(session)
    return service.calculate_financial_projections(scenario_id, projection_years)

def calculate_key_financial_metrics(scenario_id: int) -> Dict[str, Any]:
    """Wrapper function for key financial metrics calculation."""
    session = get_session()
    service = FinancialService(session)
    return service.calculate_key_financial_metrics(scenario_id)

def get_comprehensive_analysis(scenario_id: int) -> Dict[str, Any]:
    """Wrapper function for comprehensive financial analysis."""
    session = get_session()
    service = FinancialService(session)
    return service.get_comprehensive_analysis(scenario_id)

def get_risk_adjusted_metrics(scenario_id: int) -> Dict[str, Any]:
    """Wrapper function for risk-adjusted financial metrics."""
    session = get_session()
    service = FinancialService(session)
    return service.get_risk_adjusted_metrics(scenario_id) 