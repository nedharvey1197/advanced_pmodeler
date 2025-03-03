import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union

class AssumptionsService:
    def __init__(self, session):
        """
        Initialize Assumptions Service with a database session
        
        :param session: SQLAlchemy database session
        """
        self.session = session
        
    def get_industry_standards(self, industry_type: str = "manufacturing") -> Dict[str, Any]:
        """
        Get industry standard parameters with boundaries
        
        :param industry_type: Type of industry (manufacturing, high-tech, etc.)
        :return: Dictionary with industry standard parameters and bounds
        """
        # These values would ideally be stored in a database table
        # For now, we'll use hardcoded values based on industry type
        
        if industry_type == "manufacturing":
            return self._get_manufacturing_standards()
        elif industry_type == "high-tech":
            return self._get_high_tech_standards()
        else:
            return self._get_default_standards()
    
    def _get_manufacturing_standards(self) -> Dict[str, Any]:
        """
        Get manufacturing industry standard parameters
        
        :return: Dictionary with parameters and bounds
        """
        return {
            "financial": {
                "gross_margin": {
                    "value": 35.0,
                    "min": 20.0,
                    "max": 60.0,
                    "description": "Gross margin as percentage of revenue"
                },
                "revenue_growth": {
                    "value": 10.0,
                    "min": 5.0,
                    "max": 20.0,
                    "description": "Annual revenue growth percentage"
                },
                "debt_ratio": {
                    "value": 30.0,
                    "min": 0.0,
                    "max": 50.0,
                    "description": "Debt as percentage of total capital"
                },
                "interest_rate": {
                    "value": 5.0,
                    "min": 3.0,
                    "max": 10.0,
                    "description": "Annual interest rate percentage"
                },
                "tax_rate": {
                    "value": 21.0,
                    "min": 15.0,
                    "max": 35.0,
                    "description": "Corporate tax rate percentage"
                }
            },
            "operations": {
                "equipment_availability": {
                    "value": 85.0,
                    "min": 75.0,
                    "max": 95.0,
                    "description": "Equipment availability percentage"
                },
                "maintenance_cost": {
                    "value": 5.0,
                    "min": 3.0,
                    "max": 10.0,
                    "description": "Annual maintenance cost as percentage of equipment cost"
                },
                "equipment_useful_life": {
                    "value": 10.0,
                    "min": 5.0,
                    "max": 20.0,
                    "description": "Average useful life of equipment in years"
                },
                "capacity_utilization": {
                    "value": 75.0,
                    "min": 60.0,
                    "max": 90.0,
                    "description": "Capacity utilization percentage"
                }
            },
            "sales": {
                "revenue_per_sales_rep": {
                    "value": 1000000,
                    "min": 500000,
                    "max": 2000000,
                    "description": "Annual revenue per sales representative"
                },
                "leads_per_marketing_staff": {
                    "value": 500,
                    "min": 300,
                    "max": 800,
                    "description": "Annual leads per marketing staff member"
                },
                "lead_to_opportunity_conversion": {
                    "value": 25.0,
                    "min": 15.0,
                    "max": 35.0,
                    "description": "Lead to opportunity conversion percentage"
                },
                "opportunity_to_sale_conversion": {
                    "value": 20.0,
                    "min": 10.0,
                    "max": 30.0,
                    "description": "Opportunity to sale conversion percentage"
                },
                "sales_cycle_days": {
                    "value": 90,
                    "min": 60,
                    "max": 180,
                    "description": "Average sales cycle length in days"
                }
            },
            "g_and_a": {
                "ga_as_percent_of_revenue": {
                    "value": 15.0,
                    "min": 10.0,
                    "max": 25.0,
                    "description": "G&A as percentage of revenue"
                },
                "ga_headcount_ratio": {
                    "value": 10.0,
                    "min": 5.0,
                    "max": 20.0,
                    "description": "G&A staff as percentage of total headcount"
                }
            },
            "outsourcing": {
                "cost_premium": {
                    "value": 30.0,
                    "min": 15.0,
                    "max": 50.0,
                    "description": "Outsourcing cost premium percentage over internal production"
                },
                "capacity_threshold": {
                    "value": 90.0,
                    "min": 80.0,
                    "max": 95.0,
                    "description": "Capacity utilization threshold for considering outsourcing"
                }
            }
        }
    
    def _get_high_tech_standards(self) -> Dict[str, Any]:
        """
        Get high-tech industry standard parameters
        
        :return: Dictionary with parameters and bounds
        """
        # Similar structure to manufacturing but with different values
        # Would implement with high-tech specific values
        pass
    
    def _get_default_standards(self) -> Dict[str, Any]:
        """
        Get default industry standard parameters
        
        :return: Dictionary with parameters and bounds
        """
        # Would implement with general values
        pass
    
    def validate_scenario_parameters(self, scenario_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate scenario parameters against industry standards
        
        :param scenario_id: ID of the scenario
        :param parameters: Dictionary of parameters to validate
        :return: Dictionary with validation results
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get industry standards
        standards = self.get_industry_standards()
        
        # Validate each parameter
        validation_results = {
            "valid": True,
            "warnings": [],
            "out_of_bounds": []
        }
        
        for category, params in standards.items():
            for param_name, param_data in params.items():
                if param_name in parameters:
                    value = parameters[param_name]
                    
                    if value < param_data["min"] or value > param
                    if value < param_data["min"] or value > param_data["max"]:
                        validation_results["valid"] = False
                        validation_results["out_of_bounds"].append({
                            "parameter": param_name,
                            "category": category,
                            "value": value,
                            "min": param_data["min"],
                            "max": param_data["max"],
                            "description": param_data["description"]
                        })
                    elif (value < param_data["min"] * 1.1) or (value > param_data["max"] * 0.9):
                        # Within bounds but close to limits
                        validation_results["warnings"].append({
                            "parameter": param_name,
                            "category": category,
                            "value": value,
                            "standard_value": param_data["value"],
                            "description": param_data["description"],
                            "message": f"{param_name} is close to {category} industry limits"
                        })
        
        return validation_results
    
    def get_scenario_assumptions(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get all assumptions for a specific scenario
        
        :param scenario_id: ID of the scenario
        :return: Dictionary with all assumptions
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Collect assumptions from various modules
        assumptions = {
            "financial": {},
            "operations": {},
            "sales": {},
            "g_and_a": {},
            "outsourcing": {}
        }
        
        # Get basic scenario assumptions
        assumptions["financial"] = {
            "initial_revenue": scenario.initial_revenue,
            "initial_costs": scenario.initial_costs,
            "annual_revenue_growth": scenario.annual_revenue_growth * 100,  # Convert to percentage
            "annual_cost_growth": scenario.annual_cost_growth * 100,  # Convert to percentage
            "debt_ratio": scenario.debt_ratio * 100,  # Convert to percentage
            "interest_rate": scenario.interest_rate * 100,  # Convert to percentage
            "tax_rate": scenario.tax_rate * 100  # Convert to percentage
        }
        
        # Get operational assumptions
        equipment_list = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
        
        if equipment_list:
            avg_availability = sum(eq.availability_pct for eq in equipment_list) / len(equipment_list) * 100
            avg_maintenance = sum(eq.maintenance_cost_pct for eq in equipment_list) / len(equipment_list) * 100
            avg_useful_life = sum(eq.useful_life for eq in equipment_list) / len(equipment_list)
            
            assumptions["operations"] = {
                "equipment_availability": avg_availability,
                "maintenance_cost": avg_maintenance,
                "equipment_useful_life": avg_useful_life,
                "equipment_count": len(equipment_list)
            }
        
        # Get sales assumptions - would need to build structure to store these
        # Similarly for G&A and outsourcing
        
        # Compare to industry standards
        standards = self.get_industry_standards()
        
        # Add comparison to standards
        for category, params in assumptions.items():
            if category in standards:
                for param_name, value in params.items():
                    if param_name in standards[category]:
                        std_data = standards[category][param_name]
                        params[f"{param_name}_standard"] = std_data["value"]
                        params[f"{param_name}_min"] = std_data["min"]
                        params[f"{param_name}_max"] = std_data["max"]
                        
                        # Calculate deviation from standard
                        if std_data["value"] != 0:
                            deviation = ((value - std_data["value"]) / std_data["value"]) * 100
                            params[f"{param_name}_deviation"] = deviation
        
        return assumptions
```

Now, let's integrate these new services by updating our existing modules:

## 4. Integration with Existing Modules

### Add references to the Financial Service module:

```python
# In calculate_financial_projections function
# After calculating basic financials, add:

# Calculate G&A expenses
from .ga_service import GeneralAdministrativeService
ga_service = GeneralAdministrativeService(session)
ga_expenses = ga_service.calculate_ga_expenses(scenario_id, year, year)

if "error" not in ga_expenses:
    ga_cost = ga_expenses["yearly_data"][year]["total"]
    operating_expenses += ga_cost  # Add G&A to operating expenses

# Calculate sales team expenses
from .sales_service import SalesService
sales_service = SalesService(session)
sales_forecast = sales_service.calculate_sales_forecast(scenario_id, year, year)

if "error" not in sales_forecast:
    sales_cost = sales_forecast["staff_requirements"][year]["total_cost"]
    operating_expenses += sales_cost  # Add sales team cost to operating expenses

# Check if outsourcing is needed
outsourcing_requirements = sales_service.calculate_outsourcing_requirements(scenario_id, year)

if "error" not in outsourcing_requirements and outsourcing_requirements["required"]:
    outsourcing_cost = outsourcing_requirements["total_outsourcing_cost"]
    current_costs += outsourcing_cost  # Add outsourcing to COGS
```

### Create New Database Models:

We'll need to add these new models to store our sales, G&A, and assumptions data:

```python
# In models/__init__.py or models/sales.py

class SalesParameter(Base):
    """Sales parameters for scenarios"""
    __tablename__ = 'sales_parameter'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    parameter_name = Column(String, nullable=False)
    parameter_value = Column(Float, nullable=False)
    parameter_description = Column(String)
    
    def __repr__(self):
        return f"<SalesParameter(scenario_id={self.scenario_id}, name='{self.parameter_name}')>"

class SalesForecast(Base):
    """Sales forecast data by year"""
    __tablename__ = 'sales_forecast'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    year = Column(Integer, nullable=False)
    is_market_driven = Column(Boolean, default=False)
    total_revenue = Column(Float, default=0.0)
    total_units = Column(Float, default=0.0)
    leads_needed = Column(Float, default=0.0)
    opportunities_needed = Column(Float, default=0.0)
    deals_needed = Column(Float, default=0.0)
    total_headcount = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<SalesForecast(scenario_id={self.scenario_id}, year={self.year})>"

class GAExpense(Base):
    """G&A expense data by year"""
    __tablename__ = 'ga_expense'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
    year = Column(Integer, nullable=False)
    expense_category = Column(String, nullable=False)
    amount = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<GAExpense(scenario_id={self.scenario_id}, year={self.year}, category='{self.expense_category}')>"

class IndustryStandard(Base):
    """Industry standard parameters"""
    __tablename__ = 'industry_standard'
    
    id = Column(Integer, primary_key=True)
    industry_type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    parameter_name = Column(String, nullable=False)
    standard_value = Column(Float, nullable=False)
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    description = Column(String)
    
    def __repr__(self):
        return f"<IndustryStandard(industry='{self.industry_type}', parameter='{self.parameter_name}')>"
```

## 5. Integration into Streamlit App

To expose these new features in the Streamlit app, we'd need to add:

1. A new "Sales Planning" section:
   - Toggles for market-driven vs. operations-driven approaches
   - Input fields for sales conversion rates
   - Visualization of sales pipeline and staffing needs

2. A new "G&A Planning" section:
   - Breakdown of G&A expenses by category
   - Headcount planning
   - Benchmarking against industry standards

3. An "Assumptions" section:
   - Comprehensive view of all assumptions
   - Ability to modify with validation against industry standards
   - Warnings for out-of-bounds values

4. Update the "Capacity Planning" section:
   - Add outsourcing analysis when capacity limits are reached
   - Comparison of build vs. buy decisions

## Implementation Steps

To implement these enhancements, I'd recommend this approach:

1. First, create the new database models to store the additional data
2. Then implement the service modules one at a time:
   - Start with the Assumptions service as it underpins the others
   - Then implement the Sales service
   - Finally implement the G&A service

3. Update the existing financial calculations to integrate the new services
4. Add the new UI sections to the Streamlit app

This phased approach lets you build and test incrementally while maintaining a working application throughout the process.