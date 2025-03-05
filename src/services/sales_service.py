"""
Sales service module for the manufacturing expansion financial model.

This module provides comprehensive sales forecasting capabilities including:
- Market-driven sales forecasting
- Operations-driven sales forecasting
- Sales pipeline analysis
- Channel distribution modeling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from ..models import (
    Scenario, Product, FinancialProjection,
    get_session
)

class SalesService:
    """
    Service class for sales forecasting and analysis.
    
    This class provides methods for generating sales forecasts based on either
    market-driven or operations-driven approaches, and analyzing sales performance
    across different channels.
    """
    
    def __init__(self, session):
        """
        Initialize Sales Service with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def calculate_sales_forecast(
        self,
        scenario_id: int,
        start_year: int,
        end_year: int,
        market_driven: Optional[List[bool]] = None
    ) -> Dict[str, Any]:
        """
        Calculate sales forecast based on either market-driven or operations-driven approach.
        
        Args:
            scenario_id: ID of the scenario to forecast
            start_year: Start year for forecasting
            end_year: End year for forecasting
            market_driven: List of booleans indicating if each year is market-driven (True)
                          or operations-driven (False)
            
        Returns:
            Dictionary containing sales forecast details including:
            - Yearly sales data
            - Product-specific forecasts
            - Staff requirements
            - Sales pipeline metrics
            - Channel distribution
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Get products data
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
        
        # Calculate forecasts for each year
        for year in range(start_year, end_year + 1):
            year_index = year - start_year
            is_market_driven = market_driven[year_index]
            
            # Get revenue for scaling
            from .financial_service import calculate_financial_projection
            projection = calculate_financial_projection(scenario_id, year)
            
            if "error" in projection:
                revenue = scenario.initial_revenue * ((1 + scenario.annual_revenue_growth) ** year)
            else:
                revenue = projection["revenue"]
            
            # Calculate product-specific forecasts
            product_forecasts = {}
            total_units = 0
            total_revenue = 0
            
            for product in products:
                years_since_intro = year - product.introduction_year
                if years_since_intro < 0:
                    continue
                
                # Calculate base volume
                base_volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
                
                # Adjust for market-driven vs operations-driven
                if is_market_driven:
                    # Market-driven: Consider market size and price elasticity
                    if product.market_size:
                        market_share = min(1.0, base_volume / product.market_size)
                        price_factor = (1 + product.price_elasticity * 0.1)  # 10% price change
                        volume = base_volume * market_share * price_factor
                    else:
                        volume = base_volume
                else:
                    # Operations-driven: Use base volume
                    volume = base_volume
                
                product_revenue = volume * product.unit_price
                
                product_forecasts[product.id] = {
                    "product_name": product.name,
                    "volume": volume,
                    "revenue": product_revenue,
                    "unit_price": product.unit_price,
                    "market_share": min(1.0, volume / product.market_size) if product.market_size else None
                }
                
                total_units += volume
                total_revenue += product_revenue
            
            # Calculate staff requirements
            # Assume $1M revenue per sales person
            sales_staff = max(1, int(total_revenue / 1_000_000))
            
            # Calculate sales pipeline metrics
            # Assume 3x pipeline coverage
            pipeline_coverage = 3.0
            required_pipeline = total_revenue * pipeline_coverage
            
            # Calculate channel distribution
            # Default distribution: 60% direct, 30% distributors, 10% OEM
            channel_distribution = {
                "direct": total_revenue * 0.6,
                "distributors": total_revenue * 0.3,
                "oem": total_revenue * 0.1
            }
            
            # Store yearly data
            forecast["yearly_data"][year] = {
                "total_revenue": total_revenue,
                "total_units": total_units,
                "is_market_driven": is_market_driven,
                "average_unit_price": total_revenue / total_units if total_units > 0 else 0
            }
            
            # Store product forecasts
            forecast["products"][year] = product_forecasts
            
            # Store staff requirements
            forecast["staff_requirements"][year] = {
                "total_headcount": sales_staff,
                "revenue_per_head": total_revenue / sales_staff if sales_staff > 0 else 0
            }
            
            # Store pipeline metrics
            forecast["sales_pipeline"][year] = {
                "required_pipeline": required_pipeline,
                "pipeline_coverage": pipeline_coverage,
                "leads_needed": required_pipeline / 10000,  # Assume $10k average deal size
                "opportunities_needed": required_pipeline / 50000,  # Assume $50k average opportunity
                "deals_needed": required_pipeline / 200000  # Assume $200k average deal
            }
            
            # Store channel distribution
            forecast["channel_distribution"][year] = channel_distribution
        
        return forecast
    
    def analyze_sales_performance(self, scenario_id: int, year: int) -> Dict[str, Any]:
        """
        Analyze sales performance for a specific scenario and year.
        
        Args:
            scenario_id: ID of the scenario to analyze
            year: Year to analyze
            
        Returns:
            Dictionary containing sales performance metrics
        """
        # Get sales forecast
        forecast = self.calculate_sales_forecast(scenario_id, year, year)
        
        if "error" in forecast:
            return forecast
        
        # Get yearly data
        yearly_data = forecast["yearly_data"][year]
        product_forecasts = forecast["products"][year]
        
        # Calculate performance metrics
        metrics = {
            "revenue_metrics": {
                "total_revenue": yearly_data["total_revenue"],
                "average_unit_price": yearly_data["average_unit_price"],
                "revenue_growth": (
                    (yearly_data["total_revenue"] / yearly_data["total_revenue"] - 1) * 100
                    if yearly_data["total_revenue"] > 0 else 0
                )
            },
            "product_metrics": {},
            "channel_metrics": forecast["channel_distribution"][year],
            "pipeline_metrics": forecast["sales_pipeline"][year],
            "staff_metrics": forecast["staff_requirements"][year]
        }
        
        # Calculate product-specific metrics
        for product_id, product_data in product_forecasts.items():
            metrics["product_metrics"][product_id] = {
                "product_name": product_data["product_name"],
                "volume": product_data["volume"],
                "revenue": product_data["revenue"],
                "unit_price": product_data["unit_price"],
                "market_share": product_data["market_share"],
                "revenue_contribution": (
                    product_data["revenue"] / yearly_data["total_revenue"] * 100
                    if yearly_data["total_revenue"] > 0 else 0
                )
            }
        
        return metrics

# Wrapper functions for easy access
def calculate_sales_forecast(
    scenario_id: int,
    start_year: int,
    end_year: int,
    market_driven: Optional[List[bool]] = None
) -> Dict[str, Any]:
    """Wrapper function for sales forecast calculation."""
    session = get_session()
    service = SalesService(session)
    return service.calculate_sales_forecast(scenario_id, start_year, end_year, market_driven)

def analyze_sales_performance(scenario_id: int, year: int) -> Dict[str, Any]:
    """Wrapper function for sales performance analysis."""
    session = get_session()
    service = SalesService(session)
    return service.analyze_sales_performance(scenario_id, year) 