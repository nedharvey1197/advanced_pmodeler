import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf

from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)
from .financial_service import (
    calculate_financial_projections, 
    calculate_key_financial_metrics, 
    clone_scenario as clone_scenario_func
)

class ScenarioManager:
    def __init__(self, session=None):
        """
        Initialize ScenarioManager with a database session
        
        :param session: SQLAlchemy database session (optional)
        """
        self.session = session if session else get_session()
    
    def list_scenarios(self):
        """
        List all available scenarios
        
        :return: List of scenario dictionaries with basic information
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
    
    def create_scenario(self, name, description, **kwargs):
        """
        Create a new scenario
        
        :param name: Scenario name
        :param description: Scenario description
        :param kwargs: Additional scenario parameters
        :return: Created scenario object
        """
        scenario = Scenario(
            name=name,
            description=description,
            **kwargs
        )
        self.session.add(scenario)
        self.session.commit()
        return scenario
    
    def clone_scenario(self, source_scenario_id, new_name, new_description, **kwargs):
        """
        Clone an existing scenario with all its data
        
        :param source_scenario_id: ID of the scenario to clone
        :param new_name: Name for the new scenario
        :param new_description: Description for the new scenario
        :param kwargs: Additional parameters to override in the cloned scenario
        :return: Newly created scenario
        """
        new_scenario = clone_scenario_func(
            self.session, 
            source_scenario_id, 
            new_name, 
            new_description
        )
        
        if new_scenario:
            # Update any additional parameters
            for key, value in kwargs.items():
                if hasattr(new_scenario, key):
                    setattr(new_scenario, key, value)
            
            self.session.commit()
        
        return new_scenario
    
    def delete_scenario(self, scenario_id):
        """
        Delete a scenario and all its associated data
        
        :param scenario_id: ID of the scenario to delete
        :return: Deletion status dictionary
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found."}
        
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
        self.session.query(Scenario).filter(Scenario.id == scenario_id).delete()
        
        self.session.commit()
        return {"status": "success", "message": f"Deleted scenario with ID: {scenario_id}"}
    
    def get_summary(self, scenario_id):
        """
        Get a comprehensive summary of a scenario
        
        :param scenario_id: ID of the scenario to summarize
        :return: Dictionary with scenario details and key metrics
        """
        scenario = self.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not scenario:
            return {"error": f"Scenario with ID {scenario_id} not found."}
        
        # Count products and equipment
        product_count = self.session.query(Product).filter(Product.scenario_id == scenario_id).count()
        equipment_count = self.session.query(Equipment).filter(Equipment.scenario_id == scenario_id).count()
        
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
    
    def compare_scenarios(self, scenario_ids, metric_type="income_statement"):
        """
        Compare multiple scenarios across different metric types
        
        :param scenario_ids: List of scenario IDs to compare
        :param metric_type: Type of metrics to compare (income_statement, balance_sheet, cash_flow, operations)
        :return: DataFrame with comparative metrics
        """
        if not scenario_ids:
            return {"error": "No scenario IDs provided."}
        
        # Get scenarios
        scenarios = self.session.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        scenario_map = {s.id: s for s in scenarios}
        
        if not scenarios:
            return {"error": "No matching scenarios found."}
        
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
        
        metrics = metrics_map.get(metric_type)
        if not metrics:
            return {"error": f"Unknown metric type: {metric_type}"}
        
        # Find all years across all scenarios
        all_years = sorted(set(p.year for projections in all_projections.values() for p in projections))
        
        if not all_years:
            return {"error": "No projection years found."}
        
        # Create multi-level columns
        column_tuples = []
        for scenario_id in scenario_ids:
            if scenario_id not in scenario_map:
                continue
                
            scenario_name = scenario_map[scenario_id].name
            for metric in metrics:
                column_tuples.append((scenario_name, metric))
        
        # Create empty DataFrame with multi-level columns
        columns = pd.MultiIndex.from_tuples(column_tuples, names=["Scenario", "Metric"])
        df = pd.DataFrame(index=all_years, columns=columns)
        df.index.name = "Year"
        
        # Fill DataFrame with projection data
        for scenario_id in scenario_ids:
            if scenario_id not in scenario_map or scenario_id not in all_projections:
                continue
                
            scenario_name = scenario_map[scenario_id].name
            projections = all_projections[scenario_id]
            
            for projection in projections:
                for metric in metrics:
                    if hasattr(projection, metric):
                        df.loc[projection.year, (scenario_name, metric)] = getattr(projection, metric)
        
        return df
    
    def run_sensitivity_analysis(self, base_scenario_id, variable, values, recalculate=True):
        """
        Run sensitivity analysis by varying a specific variable
        
        :param base_scenario_id: ID of the base scenario
        :param variable: Variable to modify (e.g., 'annual_revenue_growth')
        :param values: List of values to test
        :param recalculate: Whether to recalculate financial projections
        :return: Dictionary with sensitivity analysis results
        """
        base_scenario = self.session.query(Scenario).filter(Scenario.id == base_scenario_id).first()
        
        if not base_scenario:
            return {"error": f"Base scenario with ID {base_scenario_id} not found."}
        
        # Create scenario variants
        variants = []
        for value in values:
            # Clone the base scenario
            variant_name = f"{base_scenario.name} - {variable} {value}"
            variant_description = f"Sensitivity analysis variant with {variable} = {value}"
            
            # Create variant
            variant = self.clone_scenario(base_scenario_id, variant_name, variant_description)
            
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
    
    def export_comparison_report(self, scenario_ids, output_file=None):
        """
        Export a comprehensive comparison report for multiple scenarios
        
        :param scenario_ids: List of scenario IDs to compare
        :param output_file: Optional output file path
        :return: Dictionary with export status and file path
        """
        # Get scenarios
        scenarios = self.session.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        scenario_map = {s.id: s for s in scenarios}
        
        if not scenarios:
            return {"error": "No matching scenarios found."}
        
        # Create PDF
        if output_file is None:
            scenario_names = "_vs_".join([s.name.replace(" ", "_") for s in scenarios][:2])
            if len(scenarios) > 2:
                scenario_names += "_and_more"
            output_file = f"scenario_comparison_{scenario_names}.pdf"
        
        pdf_pages = pdf.PdfPages(output_file)
        
        # Income Statement Comparison
        df_income = self.compare_scenarios(scenario_ids, "income_statement")
        if not isinstance(df_income, dict) and not df_income.empty:
            # Revenue Comparison
            fig, ax = plt.subplots(figsize=(12, 8))
            for scenario_id in scenario_ids:
                if scenario_id not in scenario_map:
                    continue
                    
                scenario_name = scenario_map[scenario_id].name
                if (scenario_name, "revenue") in df_income.columns:
                    ax.plot(df_income.index, df_income[(scenario_name, "revenue")], 
                            marker="o", linewidth=2, label=f"{scenario_name} - Revenue")
            
            ax.set_title("Revenue Comparison", fontsize=14)
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Revenue ($)", fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf_pages.savefig(fig)
            plt.close(fig)
            
            # Net Income Comparison
            fig, ax = plt.subplots(figsize=(12, 8))
            for scenario_id in scenario_ids:
                if scenario_id not in scenario_map:
                    continue
                    
                scenario_name = scenario_map[scenario_id].name
                if (scenario_name, "net_income") in df_income.columns:
                    ax.plot(df_income.index, df_income[(scenario_name, "net_income")], 
                            marker="o", linewidth=2, label=f"{scenario_name} - Net Income")
            
            ax.set_title("Net Income Comparison", fontsize=14)
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Net Income ($)", fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf_pages.savefig(fig)
            plt.close(fig)
        
        # Operations Comparison
        df_ops = self.compare_scenarios(scenario_ids, "operations")
        if not isinstance(df_ops, dict) and not df_ops.empty:
            # Capacity Utilization Comparison
            fig, ax = plt.subplots(figsize=(12, 8))
            for scenario_id in scenario_ids:
                if scenario_id not in scenario_map:
                    continue
                    
                scenario_name = scenario_map[scenario_id].name
                if (scenario_name, "capacity_utilization") in df_ops.columns:
                    ax.plot(df_ops.index, df_ops[(scenario_name, "capacity_utilization")], 
                            marker="o", linewidth=2, label=f"{scenario_name} - Capacity Utilization")
            
            ax.set_title("Capacity Utilization Comparison", fontsize=14)
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Utilization (%)", fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf_pages.savefig(fig)
            plt.close(fig)
        
        pdf_pages.close()
        
        return {"status": "success", "file_path": output_file}
    
    def recalculate_all_scenarios(self):
        """
        Recalculate financial projections for all scenarios
        
        :return: List of calculation results for each scenario
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
    
    def run_monte_carlo_simulation(self, scenario_id, iterations=1000, variables=None):
        """
        Run Monte Carlo simulation for scenario analysis - PLACEHOLDER
        
        :param scenario_id: ID of the base scenario
        :param iterations: Number of simulation iterations
        :param variables: Variables to simulate (optional)
        :return: Dictionary with simulation results
        """
        print("Monte Carlo simulation will be implemented in Phase 2")
        print(f"This will simulate {iterations} iterations with random variations in:")
        
        if variables is None:
            variables = [
                "annual_revenue_growth",
                "annual_cost_growth",
                "interest_rate",
                "product_growth_rates"
            ]
        
        for var in variables:
            print(f"- {var}")
        
        return {
            "status": "not_implemented", 
            "message": "Monte Carlo simulation will be implemented in Phase 2"
        }