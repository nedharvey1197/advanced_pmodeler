"""
Scenario service module for the manufacturing expansion financial model.

This module provides comprehensive scenario management and analysis capabilities including:
- Scenario creation, management, and CRUD operations
- Scenario comparison and analysis
- Scenario cloning and versioning
- Advanced financial analysis including sensitivity analysis
- Report generation with visualizations
- Monte Carlo simulation framework
- Integration with optimization services
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)
from .financial_service import (
    calculate_financial_projections,
    calculate_key_financial_metrics
)
from .visualization_services import plot_scenario_comparison
from .optimization_services import OptimizationService

class ScenarioManager:
    """
    Service class for managing business scenarios.
    
    This class provides methods for:
    - Scenario creation and management
    - Scenario comparison and analysis
    - Scenario cloning and versioning
    - Advanced financial analysis
    - Report generation
    - Monte Carlo simulation
    - Optimization integration
    """
    
    def __init__(self, session):
        """
        Initialize ScenarioManager with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._optimization_service = None
    
    def get_optimization_service(self) -> OptimizationService:
        """
        Get or create an instance of OptimizationService.
        
        Returns:
            OptimizationService instance
        """
        if self._optimization_service is None:
            self._optimization_service = OptimizationService(self)
        return self._optimization_service
    
    def optimize_scenario(self, scenario_id: int,
                         optimization_type: str,
                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize a scenario using the optimization service.
        
        Args:
            scenario_id: ID of the scenario to optimize
            optimization_type: Type of optimization to perform
            constraints: Optimization constraints
            
        Returns:
            Dictionary containing optimization results
        """
        optimization_service = self.get_optimization_service()
        return optimization_service.optimize_scenario(
            scenario_id,
            optimization_type,
            constraints
        )
    
    def compare_scenarios(self, scenario_ids: List[int],
                         metric_type: str = "income_statement",
                         include_optimization: bool = False) -> Union[Dict[str, Any], pd.DataFrame]:
        """
        Compare multiple scenarios across different metric types.
        
        Args:
            scenario_ids: List of scenario IDs to compare
            metric_type: Type of metrics to compare
            include_optimization: Whether to include optimization results
            
        Returns:
            DataFrame with comparative metrics or dictionary with error message
        """
        if not scenario_ids:
            return {"error": "No scenario IDs provided"}
        
        # Get scenarios
        scenarios = self.session.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        scenario_map = {s.id: s for s in scenarios}
        
        if not scenarios:
            return {"error": "No matching scenarios found"}
        
        # Get financial projections for all scenarios
        all_projections = {}
        for scenario_id in scenario_ids:
            if scenario_id not in scenario_map:
                continue
                
            projections = self.session.query(FinancialProjection).filter(
                FinancialProjection.scenario_id == scenario_id
            ).order_by(FinancialProjection.year).all()
            
            all_projections[scenario_id] = projections
        
        # Determine which metrics to include based on type
        metrics_map = {
            "income_statement": ["revenue", "cogs", "gross_profit", "operating_expenses", "ebitda", "depreciation", "ebit", "interest", "tax", "net_income"],
            "balance_sheet": ["cash", "accounts_receivable", "inventory", "fixed_assets", "accumulated_depreciation", "total_assets", "accounts_payable", "long_term_debt", "equity"],
            "cash_flow": ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_flow"],
            "operations": ["total_production", "capacity_utilization"]
        }
        
        if metric_type not in metrics_map:
            return {"error": f"Unknown metric type: {metric_type}"}
        
        # Create comparison DataFrame
        comparison_data = []
        for scenario_id in scenario_ids:
            if scenario_id not in scenario_map or scenario_id not in all_projections:
                continue
            
            scenario = scenario_map[scenario_id]
            projections = all_projections[scenario_id]
            
            # Get optimization metadata if requested
            optimization_metadata = None
            if include_optimization and hasattr(scenario, 'optimization_metadata'):
                optimization_metadata = scenario.optimization_metadata
            
            for projection in projections:
                row_data = {
                    "scenario_id": scenario_id,
                    "scenario_name": scenario.name,
                    "year": projection.year
                }
                
                # Add requested metrics
                for metric in metrics_map[metric_type]:
                    if hasattr(projection, metric):
                        row_data[metric] = getattr(projection, metric)
                
                # Add optimization metadata if available
                if optimization_metadata:
                    row_data["optimization_status"] = "optimized"
                    row_data["last_optimized"] = optimization_metadata.get("last_optimized")
                else:
                    row_data["optimization_status"] = "not_optimized"
                    row_data["last_optimized"] = None
                
                comparison_data.append(row_data)
        
        if not comparison_data:
            return {"error": "No comparison data available"}
        
        return pd.DataFrame(comparison_data)
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List all available scenarios.
        
        Returns:
            List of dictionaries containing basic scenario information
        """
        scenarios = self.session.query(Scenario).all()
        
        result = []
        for s in scenarios:
            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "is_base_case": s.is_base_case,
                "annual_revenue_growth": s.annual_revenue_growth,
                "annual_cost_growth": s.annual_cost_growth
            })
        
        return result
    
    def create_scenario(self, name: str, description: str, **kwargs) -> Scenario:
        """
        Create a new scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            **kwargs: Additional scenario parameters
            
        Returns:
            Created scenario object
        """
        scenario = Scenario(
            name=name,
            description=description,
            **kwargs
        )
        self.session.add(scenario)
        self.session.commit()
        return scenario
    
    def get_scenario(self, scenario_id: int) -> Optional[Scenario]:
        """
        Get a specific scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to retrieve
            
        Returns:
            Scenario object if found, None otherwise
        """
        return self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    def update_scenario(self, scenario_id: int, **kwargs) -> Optional[Scenario]:
        """
        Update a scenario's parameters.
        
        Args:
            scenario_id: ID of the scenario to update
            **kwargs: Parameters to update
            
        Returns:
            Updated scenario object if found, None otherwise
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)
        
        self.session.commit()
        return scenario
    
    def delete_scenario(self, scenario_id: int) -> bool:
        """
        Delete a scenario and all associated data.
        
        Args:
            scenario_id: ID of the scenario to delete
            
        Returns:
            True if successful, False otherwise
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        # Get product IDs and equipment IDs for this scenario
        product_ids = [p.id for p in self.session.query(Product).filter(Product.scenario_id == scenario_id).all()]
        equipment_ids = [e.id for e in self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()]
        
        # Delete financial projections
        self.session.query(FinancialProjection).filter(FinancialProjection.scenario_id == scenario_id).delete()
        
        # Delete cost drivers
        self.session.query(CostDriver).filter(CostDriver.product_id.in_(product_ids)).delete(synchronize_session='fetch')
        
        # Delete products and equipment
        self.session.query(Product).filter(Product.scenario_id == scenario_id).delete()
        self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).delete()
        
        # Delete scenario
        self.session.delete(scenario)
        self.session.commit()
        return True
    
    def clone_scenario(self, source_scenario_id: int, new_name: str, new_description: str) -> Optional[Scenario]:
        """
        Clone an existing scenario with all its data.
        
        Args:
            source_scenario_id: ID of the original scenario
            new_name: Name for the new scenario
            new_description: Description for the new scenario
            
        Returns:
            Newly created scenario if successful, None otherwise
        """
        # Get the original scenario
        original = self.get_scenario(source_scenario_id)
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
        self.session.add(new_scenario)
        self.session.commit()
        
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
            self.session.add(new_equipment)
            self.session.commit()
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
            self.session.add(new_product)
            self.session.commit()
            product_map[old_product.id] = new_product.id
        
        # Clone cost drivers
        for old_driver in self.session.query(CostDriver).filter(
            CostDriver.product_id.in_(product_map.keys())
        ).all():
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
            self.session.add(new_driver)
        
        self.session.commit()
        return new_scenario
    
    def get_summary(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a scenario.
        
        Args:
            scenario_id: ID of the scenario to summarize
            
        Returns:
            Dictionary containing scenario details and key metrics
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Count products and equipment
        product_count = self.session.query(Product).filter(
            Product.scenario_id == scenario_id
        ).count()
        equipment_count = self.session.query(Equipment).filter(
            Equipment.scenario_id == scenario_id
        ).count()
        
        # Get financial projections
        projections = self.session.query(FinancialProjection).filter(
            FinancialProjection.scenario_id == scenario_id
        ).order_by(FinancialProjection.year).all()
        
        # Calculate metrics
        metrics = calculate_key_financial_metrics(scenario_id)
        
        # Prepare summary
        summary = {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "is_base_case": scenario.is_base_case,
            "annual_revenue_growth": scenario.annual_revenue_growth,
            "annual_cost_growth": scenario.annual_cost_growth,
            "debt_ratio": scenario.debt_ratio,
            "interest_rate": scenario.interest_rate,
            "tax_rate": scenario.tax_rate,
            "product_count": product_count,
            "equipment_count": equipment_count,
            "has_projections": len(projections) > 0,
            "projection_years": [p.year for p in projections] if projections else [],
            "key_metrics": metrics if "error" not in metrics else None
        }
        
        return summary
    
    def run_sensitivity_analysis(self, base_scenario_id: int, variable: str, values: List[float], recalculate: bool = True) -> Dict[str, Any]:
        """
        Run sensitivity analysis by varying a specific variable.
        
        Args:
            base_scenario_id: ID of the base scenario
            variable: Variable to modify (e.g., 'annual_revenue_growth')
            values: List of values to test
            recalculate: Whether to recalculate financial projections
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        base_scenario = self.get_scenario(base_scenario_id)
        if not base_scenario:
            return {"error": f"Base scenario with ID {base_scenario_id} not found"}
        
        # Create scenario variants
        variants = []
        for value in values:
            # Clone the base scenario
            variant_name = f"{base_scenario.name} - {variable} {value}"
            variant_description = f"Sensitivity analysis variant with {variable} = {value}"
            
            # Create variant
            variant = self.clone_scenario(base_scenario_id, variant_name, variant_description)
            if not variant:
                continue
            
            # Set the variable value
            if hasattr(variant, variable):
                setattr(variant, variable, value)
                self.session.commit()
            
            variants.append(variant)
            
            # Calculate financial projections
            if recalculate:
                calculate_financial_projections(variant.id)
        
        # Collect scenario IDs for comparison
        scenario_ids = [v.id for v in variants]
        
        return {
            "base_scenario_id": base_scenario_id,
            "variable": variable,
            "values": values,
            "scenario_variants": variants,
            "scenario_ids": scenario_ids
        }
    
    def export_comparison_report(self, scenario_ids: List[int], output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export a comprehensive comparison report for multiple scenarios.
        
        Args:
            scenario_ids: List of scenario IDs to compare
            output_file: Optional output file path
            
        Returns:
            Dictionary with export status and file path
        """
        # Get scenarios
        scenarios = self.session.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        scenario_map = {s.id: s for s in scenarios}
        
        if not scenarios:
            return {"error": "No matching scenarios found"}
        
        # Create PDF
        if output_file is None:
            scenario_names = "_vs_".join([s.name.replace(" ", "_") for s in scenarios][:2])
            if len(scenarios) > 2:
                scenario_names += "_and_more"
            output_file = f"scenario_comparison_{scenario_names}.pdf"
        
        pdf_pages = pdf.PdfPages(output_file)
        
        # Get comparison data
        df_income = self.compare_scenarios(scenario_ids, "income_statement")
        df_ops = self.compare_scenarios(scenario_ids, "operations")
        
        # Create plots using visualization service
        figures = plot_scenario_comparison(scenario_ids, df_income, df_ops, scenario_map)
        
        # Save plots to PDF
        for fig in figures:
            pdf_pages.savefig(fig)
            plt.close(fig)
        
        pdf_pages.close()
        
        return {"status": "success", "file_path": output_file}
    
    def recalculate_all_scenarios(self) -> List[Dict[str, Any]]:
        """
        Recalculate financial projections for all scenarios.
        
        Returns:
            List of calculation results for each scenario
        """
        scenarios = self.session.query(Scenario).all()
        
        results = []
        for scenario in scenarios:
            result = calculate_financial_projections(scenario.id)
            results.append({
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
                "result": result
            })
        
        return results
    
    def run_monte_carlo_simulation(self, scenario_id: int, iterations: int = 1000, variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for scenario analysis.
        
        Args:
            scenario_id: ID of the base scenario
            iterations: Number of simulation iterations
            variables: Variables to simulate (optional)
            
        Returns:
            Dictionary with simulation results
        """
        base_scenario = self.get_scenario(scenario_id)
        if not base_scenario:
            return {"error": f"Base scenario with ID {scenario_id} not found"}
        
        if variables is None:
            variables = [
                "annual_revenue_growth",
                "annual_cost_growth",
                "interest_rate",
                "product_growth_rates"
            ]
        
        # Initialize results storage
        results = {
            "scenario_id": scenario_id,
            "iterations": iterations,
            "variables": variables,
            "simulations": []
        }
        
        # Run simulations
        for i in range(iterations):
            # Clone base scenario
            sim_name = f"{base_scenario.name}_sim_{i}"
            sim_description = f"Monte Carlo simulation iteration {i}"
            simulation = self.clone_scenario(scenario_id, sim_name, sim_description)
            
            if not simulation:
                continue
            
            # Apply random variations to variables
            for var in variables:
                if hasattr(simulation, var):
                    # Generate random variation (normal distribution)
                    current_value = getattr(simulation, var)
                    variation = np.random.normal(0, 0.1)  # 10% standard deviation
                    new_value = current_value * (1 + variation)
                    setattr(simulation, var, new_value)
            
            self.session.commit()
            
            # Calculate financial projections
            projections = calculate_financial_projections(simulation.id)
            
            # Store results
            results["simulations"].append({
                "iteration": i,
                "scenario_id": simulation.id,
                "variables": {var: getattr(simulation, var) for var in variables},
                "projections": projections
            })
            
            # Clean up simulation scenario
            self.delete_scenario(simulation.id)
        
        # Calculate statistics
        if results["simulations"]:
            # Calculate mean and standard deviation for key metrics
            metrics = ["revenue", "net_income", "ebitda"]
            for metric in metrics:
                values = [sim["projections"][-1].get(metric, 0) for sim in results["simulations"]]
                results[f"{metric}_mean"] = np.mean(values)
                results[f"{metric}_std"] = np.std(values)
        
        return results

# Wrapper functions for easy access
def list_scenarios() -> List[Dict[str, Any]]:
    """Wrapper function for listing scenarios."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.list_scenarios()

def create_scenario(name: str, description: str, **kwargs) -> Scenario:
    """Wrapper function for creating a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.create_scenario(name, description, **kwargs)

def get_scenario(scenario_id: int) -> Optional[Scenario]:
    """Wrapper function for getting a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.get_scenario(scenario_id)

def update_scenario(scenario_id: int, **kwargs) -> Optional[Scenario]:
    """Wrapper function for updating a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.update_scenario(scenario_id, **kwargs)

def delete_scenario(scenario_id: int) -> bool:
    """Wrapper function for deleting a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.delete_scenario(scenario_id)

def clone_scenario(source_scenario_id: int, new_name: str, new_description: str) -> Optional[Scenario]:
    """Wrapper function for cloning a scenario."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.clone_scenario(source_scenario_id, new_name, new_description)

def get_scenario_summary(scenario_id: int) -> Dict[str, Any]:
    """Wrapper function for getting a scenario summary."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.get_summary(scenario_id)

def compare_scenarios(scenario_ids: List[int], metric_type: str = "income_statement", include_optimization: bool = False) -> Union[Dict[str, Any], pd.DataFrame]:
    """Wrapper function for comparing scenarios."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.compare_scenarios(scenario_ids, metric_type, include_optimization)

def run_sensitivity_analysis(base_scenario_id: int, variable: str, values: List[float], recalculate: bool = True) -> Dict[str, Any]:
    """Wrapper function for running sensitivity analysis."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.run_sensitivity_analysis(base_scenario_id, variable, values, recalculate)

def export_comparison_report(scenario_ids: List[int], output_file: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper function for exporting comparison reports."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.export_comparison_report(scenario_ids, output_file)

def recalculate_all_scenarios() -> List[Dict[str, Any]]:
    """Wrapper function for recalculating all scenarios."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.recalculate_all_scenarios()

def run_monte_carlo_simulation(scenario_id: int, iterations: int = 1000, variables: Optional[List[str]] = None) -> Dict[str, Any]:
    """Wrapper function for running Monte Carlo simulations."""
    session = get_session()
    manager = ScenarioManager(session)
    return manager.run_monte_carlo_simulation(scenario_id, iterations, variables) 