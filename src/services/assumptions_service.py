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