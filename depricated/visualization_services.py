# Visualization utility functions
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.backends.backend_pdf as pdf

def plot_equipment_utilization(scenario_id, year):
    """Plot equipment utilization for a specific scenario and year"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get equipment utilization data
    utilization = calculate_equipment_utilization_by_product(scenario_id, year)
    
    if "error" in utilization:
        return utilization
    
    # Prepare data for visualization
    equipment_names = []
    utilization_values = []
    used_capacity = []
    available_capacity = []
    colors = []
    
    for eq_id, eq_data in utilization["equipment"].items():
        equipment_names.append(eq_data["equipment_name"])
        utilization_values.append(eq_data["utilization_pct"])
        used_capacity.append(eq_data["used_capacity"])
        available_capacity.append(eq_data["available_capacity"])
        
        # Determine color based on utilization
        if eq_data["utilization_pct"] > 85:
            colors.append("red")
        elif eq_data["utilization_pct"] < 50:
            colors.append("green")
        else:
            colors.append("blue")
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot utilization percentages
    bars = ax1.bar(equipment_names, utilization_values, color=colors, alpha=0.7)
    ax1.set_title(f"Equipment Utilization in {year} - {scenario.name}")
    ax1.set_xlabel("Equipment")
    ax1.set_ylabel("Utilization (%)")
    ax1.set_ylim(0, max(100, max(utilization_values) * 1.1 if utilization_values else 100))
    
    # Add threshold lines
    ax1.axhline(y=85, color='r', linestyle='--', alpha=0.5, label="Bottleneck Threshold (85%)")
    ax1.axhline(y=50, color='g', linestyle='--', alpha=0.5, label="Underutilization Threshold (50%)")
    ax1.legend()
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # Plot capacity utilization
    x = np.arange(len(equipment_names))
    width = 0.35
    
    ax2.bar(x - width/2, used_capacity, width, label='Used Capacity', color='blue', alpha=0.7)
    ax2.bar(x + width/2, available_capacity, width, label='Available Capacity', color='lightgray', alpha=0.7)
    
    ax2.set_title(f"Capacity Utilization in {year} - {scenario.name}")
    ax2.set_xlabel("Equipment")
    ax2.set_ylabel("Capacity (hours)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(equipment_names)
    ax2.legend()
    
    # Rotate x-axis labels if there are many equipment types
    if len(equipment_names) > 3:
        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")
        plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    
    plt.tight_layout()
    return fig

def plot_utilization_heatmap(scenario_id, start_year, end_year):
    """Create a heatmap of equipment utilization over multiple years"""
    # Get capacity constraints analysis
    constraints = identify_capacity_constraints(scenario_id, start_year, end_year)
    
    if "error" in constraints:
        return constraints
    
    # Prepare data for heatmap
    utilization_trends = constraints["equipment_utilization_trend"]
    equipment_names = []
    years = sorted(set(year for trend in utilization_trends.values() for year in trend["years"]))
    
    if not years:
        return {"error": "No utilization data available for the specified years"}
    
    # Prepare data for heatmap
    heatmap_data = []
    for eq_id, trend in utilization_trends.items():
        equipment_names.append(trend["equipment_name"])
        
        # Create a row of utilization percentages for each year
        row = []
        for year in years:
            if year in trend["years"]:
                idx = trend["years"].index(year)
                row.append(trend["utilization"][idx])
            else:
                row.append(0)  # No data for this year
        
        heatmap_data.append(row)
    
    # Create heatmap
    fig = plt.figure(figsize=(12, len(equipment_names) * 0.5 + 2))
    ax = sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn_r", 
                      vmin=0, vmax=100, cbar_kws={'label': 'Utilization %'},
                      yticklabels=equipment_names, xticklabels=years)
    
    plt.title("Equipment Utilization Heatmap", fontsize=14)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Equipment", fontsize=12)
    plt.tight_layout()
    
    return fig

def plot_shift_comparison(scenario_id, year, shift_configs=None):
    """Plot comparison of different shift configurations"""
    # Import here to avoid circular imports
    from ..services.equipment_service import model_shift_operations
    
    # Define default shift configurations if not provided
    if shift_configs is None:
        shift_configs = {
            "Single Shift": {
                "shifts_per_day": 1,
                "hours_per_shift": 8,
                "days_per_week": 5,
                "weeks_per_year": 50,
                "overtime_multiplier": 1.5,
                "max_overtime_hours_per_week": 10
            },
            "Double Shift": {
                "shifts_per_day": 2,
                "hours_per_shift": 8,
                "days_per_week": 5,
                "weeks_per_year": 50,
                "overtime_multiplier": 1.5,
                "max_overtime_hours_per_week": 5
            },
            "24/7 Operation": {
                "shifts_per_day": 3,
                "hours_per_shift": 8,
                "days_per_week": 7,
                "weeks_per_year": 50,
                "overtime_multiplier": 2.0,
                "max_overtime_hours_per_week": 0
            }
        }
    
    # Run shift analysis for each configuration
    shift_results = {}
    for config_name, config in shift_configs.items():
        shift_results[config_name] = model_shift_operations(scenario_id, year, config)
    
    # Check for errors
    for config_name, result in shift_results.items():
        if "error" in result:
            return {"error": f"{config_name}: {result['error']}"}
    
    # Prepare data for visualization
    config_names = list(shift_configs.keys())
    standard_hours = [result["standard_hours_per_year"] for result in shift_results.values()]
    overtime_costs = [result["total_overtime_cost"] for result in shift_results.values()]
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot standard hours comparison
    ax1.bar(config_names, standard_hours, color="blue", alpha=0.7)
    ax1.set_title("Standard Hours by Shift Configuration")
    ax1.set_xlabel("Shift Configuration")
    ax1.set_ylabel("Standard Hours per Year")
    
    # Add value labels on bars
    for i, hours in enumerate(standard_hours):
        ax1.annotate(f'{hours:,}',
                   xy=(i, hours),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom')
    
    # Plot overtime cost comparison
    ax2.bar(config_names, overtime_costs, color="red", alpha=0.7)
    ax2.set_title("Overtime Costs by Shift Configuration")
    ax2.set_xlabel("Shift Configuration")
    ax2.set_ylabel("Overtime Cost ($)")
    
    # Add value labels on bars
    for i, cost in enumerate(overtime_costs):
        ax2.annotate(f'${cost:,.2f}',
                   xy=(i, cost),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def export_equipment_analysis_report(scenario_id, start_year, end_year, output_file=None):
    """Generate a comprehensive equipment analysis report as PDF"""
    # Import here to avoid circular imports
    from ..services.equipment_service import identify_capacity_constraints, optimize_equipment_purchases
    
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    scenario_name = scenario.name
    
    # Create PDF
    if output_file is None:
        output_file = f"{scenario_name}_equipment_analysis.pdf"
    
    pdf_pages = pdf.PdfPages(output_file)
    
    # Generate equipment utilization heatmap
    fig1 = plot_utilization_heatmap(scenario_id, start_year, end_year)
    pdf_pages.savefig(fig1)
    plt.close(fig1)
    
    # Generate equipment utilization for each year
    for year in range(start_year, end_year + 1):
        fig2 = plot_equipment_utilization(scenario_id, year)
        pdf_pages.savefig(fig2)
        plt.close(fig2)
    
    # Generate shift comparison
    fig3 = plot_shift_comparison(scenario_id, end_year)
    pdf_pages.savefig(fig3)
    plt.close(fig3)
    
    # Generate optimization analysis
    constraints = identify_capacity_constraints(scenario_id, start_year, end_year)
    
    if "error" not in constraints and constraints["capacity_expansion_recommendations"]:
        # Set budget constraint at 3x the cost of the most expensive recommendation
        max_rec_cost = max(rec["estimated_cost"] for rec in constraints["capacity_expansion_recommendations"] 
                           if isinstance(rec["estimated_cost"], (int, float)))
        budget_constraint = max_rec_cost * 3
        
        # Run optimization
        optimization = optimize_equipment_purchases(
            scenario_id,
            budget_constraint=budget_constraint,
            start_year=start_year,
            optimization_years=end_year - start_year + 1
        )
        
        if "error" not in optimization and optimization["equipment_purchase_plan"]:
            # Prepare data for visualization
            years = sorted(optimization["equipment_purchase_plan"].keys())
            costs_by_year = [sum(p["cost"] for p in optimization["equipment_purchase_plan"].get(year, [])) for year in years]
            
            # Plot optimization results
            fig4 = plt.figure(figsize=(12, 6))
            
            # Plot costs by year
            ax1 = plt.subplot(1, 2, 1)
            ax1.bar(years, costs_by_year, color="blue", alpha=0.7)
            
            # Add budget line
            ax1.axhline(y=budget_constraint, color='r', linestyle='--', alpha=0.7, label="Budget Constraint")
            
            ax1.set_title("Equipment Investment by Year")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Investment ($)")
            ax1.set_ylim(0, max(costs_by_year) * 1.2 if costs_by_year else budget_constraint * 1.2)
            ax1.legend()
            
            # Plot equipment types purchased
            ax2 = plt.subplot(1, 2, 2)
            
            # Count equipment types
            equipment_counts = {}
            for purchases in optimization["equipment_purchase_plan"].values():
                for purchase in purchases:
                    eq_name = purchase["equipment_name"]
                    if eq_name in equipment_counts:
                        equipment_counts[eq_name] += 1
                    else:
                        equipment_counts[eq_name] = 1
            
            # Plot equipment counts
            if equipment_counts:
                names = list(equipment_counts.keys())
                counts = list(equipment_counts.values())
                
                ax2.bar(names, counts, color="green", alpha=0.7)
                ax2.set_title("Equipment Types Purchased")
                ax2.set_xlabel("Equipment Type")
                ax2.set_ylabel("Count")
                
                # Rotate x-axis labels if there are many equipment types
                if len(names) > 3:
                    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
            
            plt.tight_layout()
            pdf_pages.savefig(fig4)
            plt.close(fig4)
    
    pdf_pages.close()
    
    return {"status": "success", "file_path": output_file}

def plot_financial_metrics(scenario_id):
    """
    Plot key financial metrics for a scenario
    
    :param scenario_id: ID of the scenario to visualize
    :return: Dictionary with plot figures
    """
    # Import to avoid circular imports
    from ..services.financial_service import calculate_key_financial_metrics
    
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get financial metrics
    metrics = calculate_key_financial_metrics(scenario_id)
    
    if "error" in metrics:
        return metrics
    
    # Initialize result dictionary
    result = {}
    
    # Plot net income
    if "net_income" in metrics and metrics["net_income"]:
        fig1 = plt.figure(figsize=(10, 6))
        plt.plot(range(len(metrics["net_income"])), metrics["net_income"], marker='o', linestyle='-', linewidth=2)
        plt.title(f"Net Income Over Time - {scenario.name}")
        plt.xlabel("Year")
        plt.ylabel("Net Income ($)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        result["net_income_fig"] = fig1
    
    # Plot EBITDA margin
    if "ebitda_margin" in metrics and metrics["ebitda_margin"]:
        years = [item["year"] for item in metrics["ebitda_margin"]]
        values = [item["value"] for item in metrics["ebitda_margin"]]
        
        fig2 = plt.figure(figsize=(10, 6))
        plt.plot(years, values, marker='o', linestyle='-', linewidth=2)
        plt.title(f"EBITDA Margin Over Time - {scenario.name}")
        plt.xlabel("Year")
        plt.ylabel("EBITDA Margin (%)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        result["ebitda_margin_fig"] = fig2
    
    # Return figures
    return result

def plot_product_revenue_breakdown(scenario_id, year):
    """
    Plot revenue breakdown by product for a specific year
    
    :param scenario_id: ID of the scenario
    :param year: Year to visualize
    :return: Plot figure
    """
    session = get_session()
    
    # Get financial projection for the specified year
    projection = session.query(FinancialProjection).filter(
        FinancialProjection.scenario_id == scenario_id,
        FinancialProjection.year == year
    ).first()
    
    if not projection:
        return {"error": f"No financial projection found for scenario {scenario_id}, year {year}"}
    
    # Get product details
    if not hasattr(projection, 'product_details') or not projection.product_details:
        return {"error": "No product details found in financial projection"}
    
    # Extract product revenues
    products = []
    revenues = []
    
    for product_name, revenue in projection.product_details.items():
        products.append(product_name)
        revenues.append(revenue)
    
    # Create pie chart
    fig = plt.figure(figsize=(10, 8))
    plt.pie(revenues, labels=products, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(f"Revenue Breakdown by Product - Year {year}")
    plt.tight_layout()
    
    return fig

def create_dashboard(scenario_id, output_file=None):
    """
    Create a comprehensive dashboard for a scenario
    
    :param scenario_id: ID of the scenario
    :param output_file: Optional output file path
    :return: Dictionary with dashboard status and file path
    """
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Create PDF
    if output_file is None:
        output_file = f"{scenario.name}_dashboard.pdf"
    
    pdf_pages = pdf.PdfPages(output_file)
    
    # Get projections
    projections = session.query(FinancialProjection).filter(
        FinancialProjection.scenario_id == scenario_id
    ).order_by(FinancialProjection.year).all()
    
    if not projections:
        return {"error": "No financial projections found for scenario"}
    
    year_range = range(min(p.year for p in projections), max(p.year for p in projections) + 1)
    
    # Add financial metrics
    financial_plots = plot_financial_metrics(scenario_id)
    if not isinstance(financial_plots, dict) or "error" not in financial_plots:
        for plot_name, fig in financial_plots.items():
            pdf_pages.savefig(fig)
            plt.close(fig)
    
    # Add product revenue breakdown for the latest year
    latest_year = max(p.year for p in projections)
    revenue_breakdown = plot_product_revenue_breakdown(scenario_id, latest_year)
    if not isinstance(revenue_breakdown, dict) or "error" not in revenue_breakdown:
        pdf_pages.savefig(revenue_breakdown)
        plt.close(revenue_breakdown)
    
    # Add equipment utilization
    for year in year_range:
        utilization_plot = plot_equipment_utilization(scenario_id, year)
        if not isinstance(utilization_plot, dict) or "error" not in utilization_plot:
            pdf_pages.savefig(utilization_plot)
            plt.close(utilization_plot)
    
    # Add utilization heatmap
    heatmap = plot_utilization_heatmap(scenario_id, min(year_range), max(year_range))
    if not isinstance(heatmap, dict) or "error" not in heatmap:
        pdf_pages.savefig(heatmap)
        plt.close(heatmap)
    
    pdf_pages.close()
    
    return {"status": "success", "file_path": output_file}