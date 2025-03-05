import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union

class SalesService:
    def __init__(self, session):
        """
        Initialize Sales Service with a database session
        
        :param session: SQLAlchemy database session
        """
        self.session = session
        
    def calculate_sales_forecast(self, scenario_id: int, start_year: int, end_year: int, 
                                 market_driven: Optional[List[bool]] = None) -> Dict[str, Any]:
        """
        Calculate sales forecast based on either market-driven or operations-driven approach
        
        :param scenario_id: ID of the scenario
        :param start_year: Start year for forecasting
        :param end_year: End year for forecasting
        :param market_driven: List of booleans indicating if each year is market-driven (True) 
                              or operations-driven (False)
        :return: Dictionary with sales forecast details
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get products and equipment data
        products = self.session.query(Product).filter(Product.scenario_id == scenario_id).all()
        
        # Initialize results
        forecast = {
            "yearly_data": {},
            "products": {},
            "staff_requirements": {},
            "sales_pipeline": {},
            "channel_distribution": {}
        }
        
        # Default to operations-driven in year 0-1, transitioning to market-driven by year 3
        if market_driven is None:
            years = list(range(start_year, end_year + 1))
            market_driven = [year >= start_year + 2 for year in years]
        
        # Import needed functions from equipment service
        from .equipment_service import calculate_equipment_utilization_by_product
        
        # Calculate for each year
        for idx, year in enumerate(range(start_year, end_year + 1)):
            is_market_driven = market_driven[idx] if idx < len(market_driven) else True
            
            if is_market_driven:
                # Market-driven approach
                forecast["yearly_data"][year] = self._calculate_market_driven_forecast(
                    scenario_id, products, year
                )
            else:
                # Operations-driven approach
                forecast["yearly_data"][year] = self._calculate_operations_driven_forecast(
                    scenario_id, products, year
                )
            
            # Calculate staff requirements
            forecast["staff_requirements"][year] = self._calculate_staff_requirements(
                scenario_id, forecast["yearly_data"][year], year
            )
            
            # Calculate sales pipeline metrics
            forecast["sales_pipeline"][year] = self._calculate_sales_pipeline(
                scenario_id, forecast["yearly_data"][year], year
            )
            
            # Calculate channel distribution
            forecast["channel_distribution"][year] = self._calculate_channel_distribution(
                scenario_id, forecast["yearly_data"][year], year
            )
        
        return forecast
    
    def _calculate_market_driven_forecast(self, scenario_id: int, products: List, year: int) -> Dict[str, Any]:
        """
        Calculate market-driven sales forecast
        
        :param scenario_id: ID of the scenario
        :param products: List of products
        :param year: Year to forecast
        :return: Dictionary with forecast details
        """
        # Get market size data from products
        forecast_data = {
            "total_revenue": 0,
            "total_units": 0,
            "by_product": {}
        }
        
        for product in products:
            # Skip products not yet introduced
            if product.introduction_year > year:
                continue
                
            # Calculate years since introduction
            years_since_intro = year - product.introduction_year
            
            # Market-driven calculation using market size and growth
            if product.market_size > 0:
                # Calculate market growth
                market_growth = 1.05  # Default 5% market growth
                current_market_size = product.market_size * (market_growth ** years_since_intro)
                
                # Calculate market share
                base_market_share = 0.05  # Starting with 5% market share
                market_share_growth = 1.2  # 20% growth in market share annually
                current_market_share = min(0.35, base_market_share * (market_share_growth ** years_since_intro))
                
                # Calculate unit volume
                unit_volume = current_market_size * current_market_share
            else:
                # Fallback to standard growth projection if market size not defined
                unit_volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
            
            # Calculate revenue
            product_revenue = unit_volume * product.unit_price
            
            # Store product-specific data
            forecast_data["by_product"][product.id] = {
                "product_name": product.name,
                "units": unit_volume,
                "revenue": product_revenue,
                "market_driven": True
            }
            
            # Add to totals
            forecast_data["total_units"] += unit_volume
            forecast_data["total_revenue"] += product_revenue
        
        return forecast_data
    
    def _calculate_operations_driven_forecast(self, scenario_id: int, products: List, year: int) -> Dict[str, Any]:
        """
        Calculate operations-driven sales forecast based on production capacity
        
        :param scenario_id: ID of the scenario
        :param products: List of products
        :param year: Year to forecast
        :return: Dictionary with forecast details
        """
        # Import equipment utilization calculation
        from .equipment_service import calculate_equipment_utilization_by_product
        
        # Get equipment utilization
        utilization = calculate_equipment_utilization_by_product(scenario_id, year)
        
        forecast_data = {
            "total_revenue": 0,
            "total_units": 0,
            "by_product": {},
            "capacity_utilization": utilization.get("overall_utilization_pct", 0),
            "capacity_limited": False
        }
        
        # Check if we're capacity limited
        capacity_limited = any(bottleneck["utilization_pct"] > 95 for bottleneck in utilization.get("bottlenecks", []))
        forecast_data["capacity_limited"] = capacity_limited
        
        # Get product production data from utilization
        for eq_id, eq_data in utilization.get("equipment", {}).items():
            for prod_id, prod_data in eq_data.get("products", {}).items():
                if prod_id not in forecast_data["by_product"]:
                    product = next((p for p in products if p.id == prod_id), None)
                    if product:
                        product_revenue = prod_data["volume"] * product.unit_price
                        
                        forecast_data["by_product"][prod_id] = {
                            "product_name": product.name,
                            "units": prod_data["volume"],
                            "revenue": product_revenue,
                            "market_driven": False
                        }
                        
                        # Add to totals
                        forecast_data["total_units"] += prod_data["volume"]
                        forecast_data["total_revenue"] += product_revenue
        
        return forecast_data
    
    def _calculate_staff_requirements(self, scenario_id: int, forecast_data: Dict[str, Any], year: int) -> Dict[str, Any]:
        """
        Calculate sales staffing requirements based on forecast
        
        :param scenario_id: ID of the scenario
        :param forecast_data: Forecast data for the specified year
        :param year: Year to calculate for
        :return: Dictionary with staffing requirements
        """
        # Get industry standard parameters (could be stored in a scenario parameter table)
        annual_revenue_per_sales_rep = 1000000  # $1M per year per sales rep
        leads_per_marketing_staff = 500  # Marketing staff generates 500 leads per year
        lead_to_opportunity_conversion = 0.25  # 25% of leads convert to opportunities
        opportunity_to_sale_conversion = 0.20  # 20% of opportunities convert to sales
        avg_deal_size = 50000  # $50K average deal size
        
        # Calculate requirements
        total_revenue = forecast_data["total_revenue"]
        
        # Calculate sales team size
        sales_reps = total_revenue / annual_revenue_per_sales_rep
        sales_managers = sales_reps / 5  # 1 manager per 5 reps
        
        # Calculate marketing team size
        deals_needed = total_revenue / avg_deal_size
        opportunities_needed = deals_needed / opportunity_to_sale_conversion
        leads_needed = opportunities_needed / lead_to_opportunity_conversion
        marketing_staff = leads_needed / leads_per_marketing_staff
        
        # Calculate sales operations team
        sales_ops = sales_reps / 10  # 1 sales ops per 10 reps
        
        # Total sales and marketing headcount
        total_headcount = sales_reps + sales_managers + marketing_staff + sales_ops
        
        # Calculate cost
        avg_sales_rep_cost = 120000  # $120K fully loaded cost per rep
        avg_manager_cost = 180000  # $180K fully loaded cost per manager
        avg_marketing_cost = 90000  # $90K fully loaded cost per marketing staff
        avg_sales_ops_cost = 80000  # $80K fully loaded cost per sales ops
        
        total_sales_cost = (sales_reps * avg_sales_rep_cost + 
                           sales_managers * avg_manager_cost + 
                           marketing_staff * avg_marketing_cost +
                           sales_ops * avg_sales_ops_cost)
        
        return {
            "sales_representatives": sales_reps,
            "sales_managers": sales_managers,
            "marketing_staff": marketing_staff,
            "sales_operations": sales_ops,
            "total_headcount": total_headcount,
            "total_cost": total_sales_cost,
            "leads_needed": leads_needed,
            "opportunities_needed": opportunities_needed,
            "deals_needed": deals_needed
        }
    
    def _calculate_sales_pipeline(self, scenario_id: int, forecast_data: Dict[str, Any], year: int) -> Dict[str, Any]:
        """
        Calculate sales pipeline metrics
        
        :param scenario_id: ID of the scenario
        :param forecast_data: Forecast data for the specified year
        :param year: Year to calculate for
        :return: Dictionary with pipeline metrics
        """
        # Get industry standard parameters
        prospect_to_lead_conversion = 0.10  # 10% of prospects convert to leads
        lead_to_opportunity_conversion = 0.25  # 25% of leads convert to opportunities
        opportunity_to_sale_conversion = 0.20  # 20% of opportunities convert to sales
        avg_deal_size = 50000  # $50K average deal size
        
        # Calculate pipeline metrics
        total_revenue = forecast_data["total_revenue"]
        
        deals_needed = total_revenue / avg_deal_size
        opportunities_needed = deals_needed / opportunity_to_sale_conversion
        leads_needed = opportunities_needed / lead_to_opportunity_conversion
        prospects_needed = leads_needed / prospect_to_lead_conversion
        
        # Time-to-conversion metrics (in days)
        prospect_to_lead_time = 15
        lead_to_opportunity_time = 30
        opportunity_to_deal_time = 60
        
        # Calculate average sales cycle
        sales_cycle_days = prospect_to_lead_time + lead_to_opportunity_time + opportunity_to_deal_time
        
        return {
            "prospects_needed": prospects_needed,
            "leads_needed": leads_needed,
            "opportunities_needed": opportunities_needed,
            "deals_needed": deals_needed,
            "avg_deal_size": avg_deal_size,
            "sales_cycle_days": sales_cycle_days,
            "conversion_rates": {
                "prospect_to_lead": prospect_to_lead_conversion,
                "lead_to_opportunity": lead_to_opportunity_conversion,
                "opportunity_to_sale": opportunity_to_sale_conversion
            }
        }
    
    def _calculate_channel_distribution(self, scenario_id: int, forecast_data: Dict[str, Any], year: int) -> Dict[str, Any]:
        """
        Calculate sales channel distribution
        
        :param scenario_id: ID of the scenario
        :param forecast_data: Forecast data for the specified year
        :param year: Year to calculate for
        :return: Dictionary with channel distribution metrics
        """
        # Default channel mix - could be stored in scenario parameters
        direct_sales_pct = 0.70  # 70% through direct sales
        channel_partner_pct = 0.20  # 20% through channel partners
        online_pct = 0.10  # 10% through online channels
        
        # Calculate revenue by channel
        total_revenue = forecast_data["total_revenue"]
        
        return {
            "direct_sales": {
                "percentage": direct_sales_pct,
                "revenue": total_revenue * direct_sales_pct
            },
            "channel_partners": {
                "percentage": channel_partner_pct,
                "revenue": total_revenue * channel_partner_pct
            },
            "online": {
                "percentage": online_pct,
                "revenue": total_revenue * online_pct
            }
        }
    
    def calculate_outsourcing_requirements(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Calculate outsourcing requirements when at capacity limits
        
        :param scenario_id: ID of the scenario
        :param year: Year to calculate for
        :return: Dictionary with outsourcing requirements
        """
        # Import equipment utilization calculation
        from .equipment_service import calculate_equipment_utilization_by_product
        
        # Get equipment utilization
        utilization = calculate_equipment_utilization_by_product(scenario_id, year)
        
        # Get market-driven demand
        market_forecast = self._calculate_market_driven_forecast(
            scenario_id, 
            self.session.query(Product).filter(Product.scenario_id == scenario_id).all(), 
            year
        )
        
        # Get operations-driven capacity
        operations_forecast = self._calculate_operations_driven_forecast(
            scenario_id,
            self.session.query(Product).filter(Product.scenario_id == scenario_id).all(),
            year
        )
        
        # Initialize results
        outsourcing = {
            "required": False,
            "by_product": {},
            "total_units_to_outsource": 0,
            "total_outsourcing_cost": 0,
            "bottlenecks": utilization.get("bottlenecks", [])
        }
        
        # Check if outsourcing is needed
        if any(bottleneck["utilization_pct"] > 95 for bottleneck in utilization.get("bottlenecks", [])):
            outsourcing["required"] = True
            
            # Calculate gap between market demand and production capacity
            for prod_id, market_data in market_forecast["by_product"].items():
                operations_data = operations_forecast["by_product"].get(prod_id, {"units": 0})
                
                # Calculate gap
                market_units = market_data["units"]
                capacity_units = operations_data.get("units", 0)
                
                if market_units > capacity_units:
                    # Outsourcing needed
                    units_to_outsource = market_units - capacity_units
                    
                    # Calculate outsourcing cost (assume 30% premium over internal production)
                    product = self.session.query(Product).filter(Product.id == prod_id).first()
                    if product:
                        # Get unit economics
                        from .financial_service import calculate_unit_economics
                        unit_economics = calculate_unit_economics(prod_id)
                        
                        if "error" not in unit_economics:
                            unit_cost = unit_economics["unit_cost"]
                            outsourcing_cost = units_to_outsource * unit_cost * 1.3  # 30% premium
                            
                            outsourcing["by_product"][prod_id] = {
                                "product_name": product.name,
                                "internal_capacity_units": capacity_units,
                                "market_demand_units": market_units,
                                "units_to_outsource": units_to_outsource,
                                "outsourcing_cost": outsourcing_cost
                            }
                            
                            # Add to totals
                            outsourcing["total_units_to_outsource"] += units_to_outsource
                            outsourcing["total_outsourcing_cost"] += outsourcing_cost
        
        return outsourcing