scenario_manager = ScenarioManager(session)

# Export scenario management module to reuse across notebooks
with open(base_dir / 'services' / 'scenario_service.py', 'w') as f:
    f.write(\"\"\"
# Scenario management service
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ..models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session
)
from .financial_service import (
    calculate_financial_projections, calculate_key_financial_metrics, 
    generate_swot_analysis, clone_scenario as clone_scenario_func
)

class ScenarioManager:
    def __init__(self, session=None):
        self.session = session if session else get_session()
    
    def list_scenarios(self):
        \"\"\"List all available scenarios\"\"\"
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
        \"\"\"Create a new empty scenario\"\"\"
        scenario = Scenario(
            name=name,
            description=description,
            **kwargs
        )
        self.session.add(scenario)
        self.session.commit()
        return scenario
    
    def clone_scenario(self, source_scenario_id, new_name, new_description, **kwargs):
        \"\"\"Clone an existing scenario with all its data\"\"\"
        new_scenario = clone_scenario_func(self.session, source_scenario_id, new_name, new_description)
        
        if new_scenario:
            # Update any additional parameters
            for key, value in kwargs.items():
                if hasattr(new_scenario, key):
                    setattr(new_scenario, key, value)
            
            self.session.commit()
        
        return new_scenario
    
    def delete_scenario(self, scenario_id):
        \"\"\"Delete a scenario and all its data\"\"\"
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
        \"\"\"Get a summary of a scenario\"\"\"
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
        \"\"\"Compare scenarios and return a DataFrame for the specified metric type\"\"\"
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
        if metric_type == "income_statement":
            metrics = ["revenue", "cogs", "gross_profit", "operating_expenses", "ebitda", "depreciation", "ebit", "interest", "tax", "net_income"]
        elif metric_type == "balance_sheet":
            metrics = ["cash", "accounts_receivable", "inventory", "fixed_assets", "accumulated_depreciation", "total_assets", "accounts_payable", "long_term_debt", "equity"]
        elif metric_type == "cash_flow":
            metrics = ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_flow"]
        elif metric_type == "operations":
            metrics = ["total_production", "capacity_utilization"]
        else:
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
        \"\"\"Run sensitivity analysis by varying a specific variable\"\"\"
        base_scenario = self.session.query(Scenario).filter(Scenario.id == base_scenario_id).first()
        
        if not base_scenario:
            return {"error": f"Base scenario with ID {base_scenario_id} not found."}
        
        # Create scenario variants
        variants = []
        for i, value in enumerate(values):
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
        \"\"\"Export a comparison report for multiple scenarios\"\"\"
        import matplotlib.backends.backend_pdf as pdf
        
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
        
        # Create comparison charts
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
            fig, ax = plt.subplots(figsize=(12, 8))
            for scenario_id in scenario_ids:
                if scenario_id not in scenario_map:
                    continue
                    
                scenario_name = scenario_map[scenario_id].name
                if (scenario_name, "capacity_utilization") in df_ops.columns:
                    ax.plot(df_ops.index, df_ops[(scenario_name, "capacity_utilization")], 
                            marker="o", linewidth=2, label=f"{scenario_name} - Utilization")
            
            ax.set_title("Capacity Utilization Comparison", fontsize=14)
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Utilization (%)", fontsize=12)
            ax.axhline(y=85, color='r', linestyle='--', alpha=0.5, label="Bottleneck Threshold (85%)")
            ax.set_ylim(0, 110)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf_pages.savefig(fig)
            plt.close(fig)
        
        # Key Metrics Comparison
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        plt.suptitle("Key Financial Metrics Comparison", fontsize=16)
        
        # Collect metrics for each scenario
        metrics_by_scenario = {}
        for scenario_id in scenario_ids:
            if scenario_id not in scenario_map:
                continue
                
            metrics = calculate_key_financial_metrics(scenario_id)
            if "error" not in metrics:
                metrics_by_scenario[scenario_id] = metrics
        
        # EBITDA Margin
        ax1 = axs[0, 0]
        for scenario_id, metrics in metrics_by_scenario.items():
            scenario_name = scenario_map[scenario_id].name
            ebitda_margins = [item["value"] for item in metrics["ebitda_margin"]]
            years = [item["year"] for item in metrics["ebitda_margin"]]
            ax1.plot(years, ebitda_margins, marker="o", linewidth=2, label=scenario_name)
        
        ax1.set_title("EBITDA Margin")
        ax1.set_ylabel("Margin (%)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # ROI
        ax2 = axs[0, 1]
        roi_values = [metrics["roi"] for scenario_id, metrics in metrics_by_scenario.items()]
        scenario_names = [scenario_map[scenario_id].name for scenario_id in metrics_by_scenario.keys()]
        
        if roi_values:
            ax2.bar(scenario_names, roi_values, alpha=0.7)
            ax2.set_title("Return on Investment (ROI)")
            ax2.set_ylabel("ROI (%)")
            ax2.grid(True, alpha=0.3)
            
            # Add value labels
            for i, roi in enumerate(roi_values):
                ax2.annotate(f"{roi:.1f}%", (i, roi), ha='center', va='bottom')
        
        # Payback Period
        ax3 = axs[1, 0]
        payback_values = [metrics["payback_period"] for scenario_id, metrics in metrics_by_scenario.items()]
        
        if payback_values:
            ax3.bar(scenario_names, payback_values, alpha=0.7)
            ax3.set_title("Payback Period")
            ax3.set_ylabel("Years")
            ax3.grid(True, alpha=0.3)
            
            # Add value labels
            for i, payback in enumerate(payback_values):
                ax3.annotate(f"{payback:.1f} yrs", (i, payback), ha='center', va='bottom')
        
        # Revenue CAGR
        ax4 = axs[1, 1]
        cagr_values = [metrics["revenue_cagr"] * 100 for scenario_id, metrics in metrics_by_scenario.items()]
        
        if cagr_values:
            ax4.bar(scenario_names, cagr_values, alpha=0.7)
            ax4.set_title("Revenue CAGR")
            ax4.set_ylabel("CAGR (%)")
            ax4.grid(True, alpha=0.3)
            
            # Add value labels
            for i, cagr in enumerate(cagr_values):
                ax4.annotate(f"{cagr:.1f}%", (i, cagr), ha='center', va='bottom')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        pdf_pages.savefig(fig)
        plt.close(fig)
        
        pdf_pages.close()
        
        return {"status": "success", "file_path": output_file}
    
    def recalculate_all_scenarios(self):
        \"\"\"Recalculate financial projections for all scenarios\"\"\"
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
\"\"\")\n",
    "    \n",
    "print(\"Scenario service module created.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Test Scenario Management Functions\n",
    "\n",
    "Let's test our scenario management functions."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# List all available scenarios\n",
    "scenario_manager.list_scenarios()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Get the base scenario\n",
    "base_scenario = session.query(Scenario).filter(Scenario.is_base_case == True).first()\n",
    "\n",
    "if not base_scenario:\n",
    "    print(\"No base scenario found. Please run the data migration in Notebook 01 first.\")\n",
    "else:\n",
    "    # Create a set of scenarios for sensitivity analysis\n",
    "    from services.financial_service import calculate_financial_projections\n",
    "    \n",
    "    # Ensure base scenario has financial projections\n",
    "    calculate_financial_projections(base_scenario.id)\n",
    "    \n",
    "    # Get summary of base scenario\n",
    "    summary = scenario_manager.get_summary(base_scenario.id)\n",
    "    print(f\"\\nSummary of {summary['name']}:\")\n",
    "    print(f\"Description: {summary['description']}\")\n",
    "    print(f\"Products: {summary['product_count']}, Equipment: {summary['equipment_count']}\")\n",
    "    print(f\"Revenue Growth: {summary['annual_revenue_growth']*100:.1f}%, Cost Growth: {summary['annual_cost_growth']*100:.1f}%\")\n",
    "    \n",
    "    if summary['has_projections']:\n",
    "        print(f\"Projection Years: {', '.join(map(str, summary['projection_years']))}\")\n",
    "        \n",
    "        if summary['key_metrics']:\n",
    "            print(f\"\\nKey Metrics:\")\n",
    "            print(f\"Revenue CAGR: {summary['key_metrics']['revenue_cagr']*100:.1f}%\")\n",
    "            print(f\"ROI: {summary['key_metrics']['roi']:.1f}%\")\n",
    "            print(f\"Payback Period: {summary['key_metrics']['payback_period']:.1f} years\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Sensitivity Analysis\n",
    "\n",
    "Let's run sensitivity analysis by varying the revenue growth rate."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "if base_scenario:\n",
    "    # Run sensitivity analysis on revenue growth rate\n",
    "    growth_rates = [0.05, 0.10, 0.15, 0.20, 0.25]\n",
    "    sensitivity = scenario_manager.run_sensitivity_analysis(\n",
    "        base_scenario.id,\n",
    "        \"annual_revenue_growth\",\n",
    "        growth_rates\n",
    "    )\n",
    "    \n",
    "    print(f\"\\nCreated {len(sensitivity['scenario_variants'])} sensitivity analysis scenarios\")\n",
    "    \n",
    "    # Compare the scenarios\n",
    "    scenario_ids = sensitivity['scenario_ids']\n",
    "    \n",
    "    # Get net income comparison\n",
    "    df_income = scenario_manager.compare_scenarios(scenario_ids, \"income_statement\")\n",
    "    \n",
    "    # Extract net income for each scenario\n",
    "    scenario_names = [s.name for s in sensitivity['scenario_variants']]\n",
    "    net_incomes = {}\n",
    "    \n",
    "    for name in scenario_names:\n",
    "        net_incomes[name] = df_income[(name, 'net_income')].tolist()\n",
    "    \n",
    "    # Plot the comparison\n",
    "    plt.figure(figsize=(12, 8))\n",
    "    \n",
    "    for name, values in net_incomes.items():\n",
    "        plt.plot(df_income.index, values, marker='o', linewidth=2, label=name)\n",
    "    \n",
    "    plt.title(\"Net Income Sensitivity to Revenue Growth Rate\", fontsize=14)\n",
    "    plt.xlabel(\"Year\", fontsize=12)\n",
    "    plt.ylabel(\"Net Income ($)\", fontsize=12)\n",
    "    plt.grid(True, alpha=0.3)\n",
    "    plt.legend()\n",
    "    plt.tight_layout()\n",
    "    plt.show()\n",
    "    \n",
    "    # Export comparison report\n",
    "    report = scenario_manager.export_comparison_report(scenario_ids)\n",
    "    \n",
    "    if \"status\" in report and report[\"status\"] == \"success\":\n",
    "        print(f\"\\nExported comparison report to: {report['file_path']}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Create Monte Carlo Simulation Placeholder\n",
    "\n",
    "Let's create a placeholder for Monte Carlo simulation (to be implemented in Phase 2)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def run_monte_carlo_simulation(scenario_id, iterations=1000, variables=None):\n",
    "    \"\"\"Run Monte Carlo simulation for scenario analysis - PLACEHOLDER\"\"\"\n",
    "    print(\"Monte Carlo simulation will be implemented in Phase 2\")\n",
    "    print(f\"This will simulate {iterations} iterations with random variations in:\")\n",
    "    \n",
    "    if variables is None:\n",
    "        variables = [\n",
    "            \"annual_revenue_growth\",\n",
    "            \"annual_cost_growth\",\n",
    "            \"interest_rate\",\n",
    "            \"product_growth_rates\"\n",
    "        ]\n",
    "    \n",
    "    for var in variables:\n",
    "        print(f\"- {var}\")\n",
    "    \n",
    "    return {\n",
    "        \"status\": \"not_implemented\", \n",
    "        \"message\": \"Monte Carlo simulation will be implemented in Phase 2\"\n",
    "    }\n",
    "\n",
    "# Test the placeholder\n",
    "if base_scenario:\n",
    "    run_monte_carlo_simulation(base_scenario.id)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}session.query(FinancialProjection).filter(
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
        \"\"\"Compare scenarios and return a DataFrame for the specified metric type\"\"\"
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
        if metric_type == "income_statement":
            metrics = ["revenue", "cogs", "gross_profit", "operating_expenses", "ebitda", "depreciation", "ebit", "interest", "tax", "net_income"]
        elif metric_type == "balance_sheet":
            metrics = ["cash", "accounts_receivable", "inventory", "fixed_assets", "accumulated_depreciation", "total_assets", "accounts_payable", "long_term_debt", "equity"]
        elif metric_type == "cash_flow":
            metrics = ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "net_cash_flow"]
        elif metric_type == "operations":
            metrics = ["total_production", "capacity_utilization"]
        else:
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
        \"\"\"Run sensitivity analysis by varying a specific variable\"\"\"
        base_scenario = self.session.query(Scenario).filter(Scenario.id == base_scenario_id).first()
        
        if not base_scenario:
            return {"error": f"Base scenario with ID {base_scenario_id} not found."}
        
        # Create scenario variants
        variants = []
        for i, value in enumerate(values):
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
            {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Manufacturing Expansion Model - Scenario Analysis\n",
    "\n",
    "This notebook implements scenario management and comparison capabilities for the manufacturing expansion model.\n",
    "\n",
    "## Tasks:\n",
    "1. Create scenario management system\n",
    "2. Implement scenario comparison functionality\n",
    "3. Build sensitivity analysis for key variables\n",
    "4. Develop export capability for scenario reports"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Setup and Dependencies"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from pathlib import Path\n",
    "import json\n",
    "\n",
    "# Add the project directory to the Python path\n",
    "base_dir = Path('./manufacturing_model')\n",
    "if str(base_dir) not in sys.path:\n",
    "    sys.path.append(str(base_dir))\n",
    "\n",
    "# Import our models\n",
    "from models import (\n",
    "    Scenario, Equipment, Product, CostDriver, FinancialProjection,\n",
    "    get_session, create_tables\n",
    ")\n",
    "\n",
    "# Ensure tables exist\n",
    "create_tables()\n",
    "\n",
    "# Get a database session\n",
    "session = get_session()\n",
    "\n",
    "# Set up plotting\n",
    "sns.set_theme(style=\"whitegrid\")\n",
    "plt.rcParams[\"figure.figsize\"] = (12, 8)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Scenario Management Functions\n",
    "\n",
    "First, let's define some functions for managing scenarios."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def list_scenarios():\n",
    "    \"\"\"List all available scenarios\"\"\"\n",
    "    scenarios = session.query(Scenario).all()\n",
    "    \n",
    "    if not scenarios:\n",
    "        print(\"No scenarios found.\")\n",
    "        return\n",
    "    \n",
    "    print(\"Available Scenarios:\")\n",
    "    for s in scenarios:\n",
    "        print(f\"ID: {s.id}, Name: {s.name}{' (Base Case)' if s.is_base_case else ''}\")\n",
    "        print(f\"  Description: {s.description}\")\n",
    "        print(f\"  Financial Assumptions: Revenue Growth: {s.annual_revenue_growth*100:.1f}%, Cost Growth: {s.annual_cost_growth*100:.1f}%\")\n",
    "        print()\n",
    "\n",
    "def create_new_scenario(name, description, **kwargs):\n",
    "    \"\"\"Create a new empty scenario\"\"\"\n",
    "    scenario = Scenario(\n",
    "        name=name,\n",
    "        description=description,\n",