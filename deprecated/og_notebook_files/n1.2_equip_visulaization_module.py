##Visualization Utilities - This module contains functions for:

# Creating equipment utilization bar charts
# Generating multi-year utilization heatmaps
# Comparing different shift configurations
# Exporting comprehensive PDF reports with all analyses

# Visualization utility functions
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

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

def plot_lease_vs_buy_comparison(scenario_id, equipment_id):
    """
    Create visualization comparing lease vs. buy options for equipment
    
    :param scenario_id: ID of the scenario
    :param equipment_id: ID of the equipment to analyze
    :return: Matplotlib figure
    """
    session = get_session()
    equipment = session.query(Equipment).filter(Equipment.id == equipment_id).first()
    
    if not equipment:
        return {"error": f"Equipment with ID {equipment_id} not found"}
    
    # Calculate purchase option costs
    purchase_cost = equipment.cost
    annual_maintenance = purchase_cost * 0.05  # Assume 5% maintenance
    
    # Calculate lease option costs
    monthly_payment = purchase_cost / 60  # Rough estimate for 5-year lease
    annual_lease = monthly_payment * 12
    
    # Create 5-year cash flow comparison
    years = range(5)
    purchase_cash_flow = [-purchase_cost]
    lease_cash_flow = []
    
    for year in years:
        if year == 0:
            purchase_cash_flow[0] -= annual_maintenance  # First year maintenance
            lease_cash_flow.append(-annual_lease)  # First year lease
        else:
            purchase_cash_flow.append(-annual_maintenance)  # Subsequent maintenance
            lease_cash_flow.append(-annual_lease)  # Subsequent lease
    
    # Calculate cumulative cash flows
    purchase_cumulative = [purchase_cash_flow[0]]
    lease_cumulative = [lease_cash_flow[0]]
    
    for year in range(1, 5):
        purchase_cumulative.append(purchase_cumulative[-1] + purchase_cash_flow[year])
        lease_cumulative.append(lease_cumulative[-1] + lease_cash_flow[year])
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Cash flow by year
    ax1.bar(years, purchase_cash_flow, width=0.4, alpha=0.7, label="Purchase", color="blue")
    ax1.bar([y + 0.4 for y in years], lease_cash_flow, width=0.4, alpha=0.7, label="Lease", color="green")
    
    ax1.set_title(f"Annual Cash Flow: {equipment.name}")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Cash Flow ($)")
    ax1.legend()
    
    # Cumulative cash flow
    ax2.plot(years, purchase_cumulative, marker='o', label="Purchase", color="blue")
    ax2.plot(years, lease_cumulative, marker='s', label="Lease", color="green")
    
    ax2.set_title(f"Cumulative Cost: {equipment.name}")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Cumulative Cost ($)")
    ax2.legend()
    
    plt.tight_layout()
    return fig

def export_equipment_analysis_report(scenario_id, start_year, end_year, output_file=None):
    """Generate a comprehensive equipment analysis report as PDF"""
    import matplotlib.backends.backend_pdf as pdf
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