"""
Advanced financial modeling service for sophisticated financial analysis.

This module provides advanced financial modeling capabilities including:
- Risk-adjusted cash flow analysis
- Working capital management
- Tax strategy optimization
- Comprehensive financial analysis

For detailed information about the integration with basic financial modeling,
see financial_modeling_README.md
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)

class AdvancedFinancialModeling:
    """
    Advanced financial modeling class for sophisticated analysis.
    
    This class provides methods for advanced financial analysis including:
    - Risk-adjusted cash flow analysis
    - Working capital management
    - Tax strategy optimization
    - Comprehensive financial analysis
    
    This class is typically accessed through FinancialService.get_advanced_modeling()
    """
    
    def __init__(self, scenario: Scenario, session):
        """
        Initialize advanced financial modeling
        
        Args:
            scenario: Scenario object
            session: Database session
        """
        self.scenario = scenario
        self.session = session
        
        # Risk and uncertainty parameters
        self.risk_factors = {
            'revenue_volatility': 0.1,  # 10% revenue volatility
            'cost_volatility': 0.08,   # 8% cost volatility
            'market_risk_premium': 0.05,  # 5% market risk premium
            'liquidity_risk': 0.03,    # 3% liquidity risk adjustment
        }
        
        # Working capital parameters
        self.working_capital_params = {
            'accounts_receivable_days': 45,  # Days to collect receivables
            'inventory_turnover_days': 60,   # Days to turn over inventory
            'accounts_payable_days': 30,     # Days to pay suppliers
            'cash_conversion_cycle': 75,     # Total cash conversion cycle
        }
    
    def update_risk_factors(self, new_factors: Dict[str, float]) -> None:
        """
        Update risk factors for analysis
        
        Args:
            new_factors: Dictionary of new risk factor values
        """
        self.risk_factors.update(new_factors)
    
    def update_working_capital_params(self, new_params: Dict[str, int]) -> None:
        """
        Update working capital parameters
        
        Args:
            new_params: Dictionary of new working capital parameters
        """
        self.working_capital_params.update(new_params)
    
    def calculate_advanced_cash_flow(self, financial_projections: List[FinancialProjection]) -> List[Dict[str, Any]]:
        """
        Generate sophisticated cash flow analysis
        
        Args:
            financial_projections: List of financial projection objects
            
        Returns:
            List of dictionaries containing enhanced cash flow analysis
        """
        cash_flow_analysis = []
        
        for proj in financial_projections:
            # Working capital calculations
            working_capital = self._calculate_working_capital(proj)
            
            # Advanced cash flow components
            operating_cash_flow = self._calculate_operating_cash_flow(proj, working_capital)
            investing_cash_flow = self._calculate_investing_cash_flow(proj)
            financing_cash_flow = self._calculate_financing_cash_flow(proj)
            
            # Risk-adjusted net cash flow
            net_cash_flow = (
                operating_cash_flow + 
                investing_cash_flow + 
                financing_cash_flow
            ) * (1 - self._calculate_risk_adjustment())
            
            cash_flow_analysis.append({
                'year': proj.year,
                'operating_cash_flow': operating_cash_flow,
                'investing_cash_flow': investing_cash_flow,
                'financing_cash_flow': financing_cash_flow,
                'net_cash_flow': net_cash_flow,
                'working_capital': working_capital,
                'risk_adjustment': self._calculate_risk_adjustment()
            })
        
        return cash_flow_analysis
    
    def _calculate_working_capital(self, projection):
        """
        Calculate detailed working capital metrics
        
        :param projection: Financial projection object
        :return: Working capital metrics dictionary
        """
        # Accounts Receivable
        ar_days = self.working_capital_params['accounts_receivable_days']
        accounts_receivable = (projection.revenue / 365) * ar_days
        
        # Inventory
        inventory_days = self.working_capital_params['inventory_turnover_days']
        inventory = (projection.cogs / 365) * inventory_days
        
        # Accounts Payable
        ap_days = self.working_capital_params['accounts_payable_days']
        accounts_payable = (projection.cogs / 365) * ap_days
        
        # Net Working Capital
        net_working_capital = (
            accounts_receivable + 
            inventory - 
            accounts_payable
        )
        
        return {
            'accounts_receivable': accounts_receivable,
            'inventory': inventory,
            'accounts_payable': accounts_payable,
            'net_working_capital': net_working_capital,
            'cash_conversion_cycle': self.working_capital_params['cash_conversion_cycle']
        }
    
    def _calculate_operating_cash_flow(self, projection, working_capital):
        """
        Calculate operating cash flow with advanced considerations
        
        :param projection: Financial projection object
        :param working_capital: Working capital metrics
        :return: Operating cash flow
        """
        # Base operating cash flow from net income
        base_ocf = projection.net_income
        
        # Add back non-cash expenses (depreciation)
        base_ocf += projection.depreciation
        
        # Adjust for changes in working capital
        wc_change = (
            working_capital['accounts_receivable'] +
            working_capital['inventory'] -
            working_capital['accounts_payable']
        )
        
        return base_ocf - wc_change
    
    def _calculate_investing_cash_flow(self, projection):
        """
        Calculate investing cash flow
        
        :param projection: Financial projection object
        :return: Investing cash flow
        """
        # Capital expenditures based on equipment purchases
        capex = sum([
            equipment.cost for equipment in self.scenario.equipment 
            if equipment.purchase_year == projection.year
        ])
        
        # Consider potential asset sales or investments
        asset_sales = 0  # Can be customized based on business strategy
        
        return -capex + asset_sales
    
    def _calculate_financing_cash_flow(self, projection):
        """
        Calculate financing cash flow
        
        :param projection: Financial projection object
        :return: Financing cash flow
        """
        # Debt financing
        new_debt = projection.revenue * self.scenario.debt_ratio
        
        # Debt repayment
        debt_repayment = projection.long_term_debt * 0.1 if hasattr(projection, 'long_term_debt') and projection.long_term_debt else 0  # 10% annual repayment
        
        # Dividend payments (optional, can be customized)
        dividend_rate = 0.2  # 20% of net income
        dividends = projection.net_income * dividend_rate
        
        return new_debt - debt_repayment - dividends
    
    def _calculate_risk_adjustment(self):
        """
        Calculate comprehensive risk adjustment factor
        
        :return: Risk adjustment percentage
        """
        # Combine multiple risk factors
        risk_factors = [
            self.risk_factors['revenue_volatility'],
            self.risk_factors['cost_volatility'],
            self.risk_factors['market_risk_premium'],
            self.risk_factors['liquidity_risk']
        ]
        
        # Weighted risk calculation
        total_risk = np.mean(risk_factors)
        
        return total_risk
    
    def calculate_advanced_tax_strategy(self, financial_projections: List[FinancialProjection]) -> List[Dict[str, Any]]:
        """
        Implement more sophisticated tax calculation methods
        
        Args:
            financial_projections: List of financial projection objects
            
        Returns:
            List of dictionaries containing tax optimization analysis
        """
        tax_analysis = []
        
        for proj in financial_projections:
            # Base taxable income
            taxable_income = proj.ebit
            
            # Apply tax credits and deductions
            tax_credits = self._calculate_tax_credits(proj)
            tax_deductions = self._calculate_tax_deductions(proj)
            
            # Adjusted taxable income
            adjusted_taxable_income = max(
                taxable_income - tax_credits - tax_deductions, 
                0
            )
            
            # Progressive tax rate calculation
            effective_tax_rate = self._calculate_progressive_tax_rate(adjusted_taxable_income)
            
            # Calculate tax liability
            tax_liability = adjusted_taxable_income * effective_tax_rate
            
            tax_analysis.append({
                'year': proj.year,
                'taxable_income': taxable_income,
                'tax_credits': tax_credits,
                'tax_deductions': tax_deductions,
                'adjusted_taxable_income': adjusted_taxable_income,
                'effective_tax_rate': effective_tax_rate,
                'tax_liability': tax_liability
            })
        
        return tax_analysis
    
    def _calculate_tax_credits(self, projection):
        """
        Calculate potential tax credits
        
        :param projection: Financial projection object
        :return: Total tax credits
        """
        # Equipment investment tax credit
        capex = sum([
            equipment.cost * 0.1  # 10% investment tax credit
            for equipment in self.scenario.equipment 
            if equipment.purchase_year == projection.year
        ])
        
        # R&D tax credit (example)
        rd_expenses = projection.operating_expenses * 0.05  # Assume 5% R&D
        rd_credit = rd_expenses * 0.2  # 20% R&D tax credit
        
        return capex + rd_credit
    
    def _calculate_tax_deductions(self, projection):
        """
        Calculate potential tax deductions
        
        :param projection: Financial projection object
        :return: Total tax deductions
        """
        # Depreciation deduction
        depreciation_deduction = projection.depreciation
        
        # Interest expense deduction
        interest_deduction = projection.interest
        
        # Loss carryforward (if applicable)
        loss_carryforward = max(
            0, 
            -projection.net_income * 0.8  # Can carry forward 80% of net loss
        )
        
        return depreciation_deduction + interest_deduction + loss_carryforward
    
    def _calculate_progressive_tax_rate(self, taxable_income):
        """
        Calculate progressive tax rate
        
        :param taxable_income: Taxable income amount
        :return: Effective tax rate
        """
        # Example progressive tax brackets
        tax_brackets = [
            (0, 50000, 0.10),
            (50000, 100000, 0.15),
            (100000, 250000, 0.25),
            (250000, float('inf'), 0.35)
        ]
        
        total_tax = 0
        remaining_income = taxable_income
        
        for lower, upper, rate in tax_brackets:
            if remaining_income <= 0:
                break
            
            taxable_amount = min(remaining_income, upper - lower)
            total_tax += taxable_amount * rate
            remaining_income -= taxable_amount
        
        # Calculate effective tax rate
        return total_tax / (taxable_income if taxable_income > 0 else 1)
    
    def generate_comprehensive_financial_analysis(self, financial_projections: List[FinancialProjection]) -> Dict[str, Any]:
        """
        Generate a comprehensive financial analysis
        
        Args:
            financial_projections: List of financial projection objects
            
        Returns:
            Dictionary containing comprehensive financial analysis
        """
        return {
            'cash_flow_analysis': self.calculate_advanced_cash_flow(financial_projections),
            'tax_analysis': self.calculate_advanced_tax_strategy(financial_projections),
            'risk_factors': self.risk_factors,
            'working_capital_params': self.working_capital_params,
            'analysis_timestamp': datetime.now().isoformat()
        }

# Extension method for FinancialService
def generate_advanced_financial_analysis(scenario_id):
    """
    Wrapper function for advanced financial analysis
    
    :param scenario_id: ID of the scenario
    :return: Comprehensive financial analysis
    """
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get financial projections
    projections = session.query(FinancialProjection).filter(
        FinancialProjection.scenario_id == scenario_id
    ).order_by(FinancialProjection.year).all()
    
    # Create advanced financial modeling instance
    advanced_modeling = AdvancedFinancialModeling(scenario, session)
    
    # Generate comprehensive analysis
    return advanced_modeling.generate_comprehensive_financial_analysis(projections)