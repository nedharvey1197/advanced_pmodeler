import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union

class GeneralAdministrativeService:
    def __init__(self, session):
        """
        Initialize G&A Service with a database session
        
        :param session: SQLAlchemy database session
        """
        self.session = session
        
    def calculate_ga_expenses(self, scenario_id: int, start_year: int, end_year: int) -> Dict[str, Any]:
        """
        Calculate G&A expenses across multiple years
        
        :param scenario_id: ID of the scenario
        :param start_year: Start year for forecasting
        :param end_year: End year for forecasting
        :return: Dictionary with G&A expense details
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Initialize results
        ga_expenses = {
            "yearly_data": {},
            "expense_categories": {},
            "headcount": {}
        }
        
        # Calculate for each year
        for year in range(start_year, end_year + 1):
            # Get revenue for scaling
            from .financial_service import calculate_financial_projection
            projection = calculate_financial_projection(scenario_id, year)
            
            if "error" in projection:
                revenue = scenario.initial_revenue * ((1 + scenario.annual_revenue_growth) ** year)
            else:
                revenue = projection["revenue"]
            
            # Get manufacturing headcount to help scale G&A
            from .equipment_service import model_shift_operations
            shift_model = model_shift_operations(scenario_id, year)
            
            manufacturing_headcount = 0
            if "error" not in shift_model:
                # Estimate manufacturing headcount from shift model
                for eq_id, eq_data in shift_model.get("equipment_shift_analysis", {}).items():
                    # Assume average of 1.5 operators per machine per shift
                    manufacturing_headcount += eq_data.get("required_shifts", 0) * 1.5
            
            # Get sales headcount
            from .sales_service import SalesService
            sales_service = SalesService(self.session)
            sales_forecast = sales_service.calculate_sales_forecast(scenario_id, year, year)
            
            sales_headcount = 0
            if "error" not in sales_forecast:
                sales_headcount = sales_forecast.get("staff_requirements", {}).get(year, {}).get("total_headcount", 0)
            
            # Calculate G&A expenses and headcount
            ga_expenses["yearly_data"][year] = self._calculate_ga_for_year(
                scenario_id, year, revenue, manufacturing_headcount, sales_headcount
            )
        
        # Calculate category totals across years
        categories = set()
        for year_data in ga_expenses["yearly_data"].values():
            categories.update(year_data["categories"].keys())
        
        for category in categories:
            ga_expenses["expense_categories"][category] = {
                "total": sum(year_data["categories"].get(category, 0) for year_data in ga_expenses["yearly_data"].values()),
                "yearly": {year: data["categories"].get(category, 0) for year, data in ga_expenses["yearly_data"].items()}
            }
        
        # Calculate headcount totals
        for year, data in ga_expenses["yearly_data"].items():
            ga_expenses["headcount"][year] = data["headcount"]
        
        return ga_expenses
    
    def _calculate_ga_for_year(self, scenario_id: int, year: int, revenue: float, 
                              manufacturing_headcount: float, sales_headcount: float) -> Dict[str, Any]:
        """
        Calculate G&A expenses for a specific year
        
        :param scenario_id: ID of the scenario
        :param year: Year to calculate for
        :param revenue: Revenue for the year
        :param manufacturing_headcount: Manufacturing headcount
        :param sales_headcount: Sales headcount
        :return: Dictionary with G&A expenses for the year
        """
        # Industry standard G&A categories and formulas
        # These could be stored in a parameter table for configurability
        
        # Estimate total company headcount
        total_headcount = manufacturing_headcount + sales_headcount
        
        # Add G&A headcount (scales with company size)
        if total_headcount <= 10:
            ga_headcount = 1  # One person doing everything
        elif total_headcount <= 50:
            ga_headcount = total_headcount * 0.15  # 15% of total headcount
        else:
            ga_headcount = 7.5 + (total_headcount - 50) * 0.10  # Economies of scale
        
        # Calculate expense categories
        categories = {}
        
        # Executive team (scales with revenue)
        if revenue < 1000000:  # <$1M
            categories["executive"] = 200000  # Minimal executive costs
        elif revenue < 10000000:  # $1-10M
            categories["executive"] = 200000 + (revenue - 1000000) * 0.05  # 5% of revenue above $1M
        else:  # >$10M
            categories["executive"] = 650000 + (revenue - 10000000) * 0.02  # 2% of revenue above $10M
        
        # HR costs (scales with headcount)
        categories["hr"] = 2000 * total_headcount  # $2K per employee
        
        # Finance/Accounting (scales with revenue and complexity)
        categories["finance"] = max(60000, revenue * 0.03)  # Minimum $60K or 3% of revenue
        
        # Legal (scales with revenue)
        categories["legal"] = max(30000, revenue * 0.02)  # Minimum $30K or 2% of revenue
        
        # IT (scales with headcount and revenue)
        categories["it"] = 3000 * total_headcount + revenue * 0.01  # $3K per employee + 1% of revenue
        
        # Facilities (scales with headcount)
        categories["facilities"] = 5000 * total_headcount  # $5K per employee
        
        # Insurance (scales with revenue and headcount)
        categories["insurance"] = 1000 * total_headcount + revenue * 0.005  # $1K per employee + 0.5% of revenue
        
        # Professional services (scales with revenue)
        categories["professional_services"] = max(20000, revenue * 0.01)  # Minimum $20K or 1% of revenue
        
        # Travel & Entertainment (scales with revenue and headcount)
        categories["travel"] = 2000 * total_headcount + revenue * 0.01  # $2K per employee + 1% of revenue
        
        # Miscellaneous (fixed percentage of other G&A)
        other_ga = sum(categories.values())
        categories["miscellaneous"] = other_ga * 0.05  # 5% of other G&A
        
        # Total G&A
        total_ga = sum(categories.values())
        
        return {
            "total": total_ga,
            "categories": categories,
            "headcount": ga_headcount,
            "percent_of_revenue": (total_ga / revenue) * 100 if revenue > 0 else 0
        }