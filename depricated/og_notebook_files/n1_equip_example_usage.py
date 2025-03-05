##I've also included an example usage script showing how to combine these components to perform a complete analysis pipeline:

# Capacity analysis for specific equipment
# Calculating utilization percentages for equipment across products
# Identifying bottlenecks and underutilized equipment
# Multi-year capacity constraint analysis
# Visualizing utilization trends with heatmaps
# Modeling different shift operations
# Optimizing equipment purchases within budget constraints
# Generating comprehensive PDF reports

# Example usage of the Manufacturing Expansion Model
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add the project directory to the Python path
base_dir = Path('./manufacturing_model')
if str(base_dir) not in sys.path:
    sys.path.append(str(base_dir))

# Import our models and services
from models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session, create_tables
)

from services.equipment_service import (
    calculate_production_capacity,
    calculate_equipment_utilization_by_product,
    identify_capacity_constraints,
    model_shift_operations,
    optimize_equipment_purchases
)

from utils.visualization_utils import (
    plot_equipment_utilization,
    plot_utilization_heatmap,
    plot_shift_comparison,
    export_equipment_analysis_report
)

# Ensure tables exist
create_tables()

# Get a database session
session = get_session()

# Set up plotting
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 8)

# Get the base scenario
base_scenario = session.query(Scenario).filter(Scenario.is_base_case == True).first()

if not base_scenario:
    print("No base scenario found. Please run the data migration in Notebook 01 first.")
else:
    # Get equipment for this scenario
    equipment_list = session.query(Equipment).filter(Equipment.scenario_id == base_scenario.id).all()
    
    if not equipment_list:
        print("No equipment found in base scenario. Please add equipment first.")
    else:
        # Analyze first equipment's capacity
        equipment = equipment_list[0]
        capacity = calculate_production_capacity(equipment.id)
        
        print(f"\nCapacity Analysis for {capacity['equipment_name']}:")
        print(f"Max Capacity: {capacity['max_capacity']} hours/year")
        print(f"Available Capacity (adjusted for availability): {capacity['available_capacity']:.2f} hours/year")
        
        # Calculate utilization for 2025
        year = 2025
        utilization = calculate_equipment_utilization_by_product(base_scenario.id, year)
        
        print(f"\nEquipment Utilization in {year}:")
        for eq_id, eq_data in utilization["equipment"].items():
            print(f"\n{eq_data['equipment_name']}:")
            print(f"  Utilization: {eq_data['utilization_pct']:.2f}%")
            print(f"  Used Capacity: {eq_data['used_capacity']:.2f} of {eq_data['available_capacity']:.2f} hours")
            
            print("  Products:")
            for prod_id, prod_data in eq_data["products"].items():
                print(f"    {prod_data['product_name']}: {prod_data['hours_used']:.2f} hours ({prod_data['capacity_pct']:.2f}% of capacity)")
        
        # Check bottlenecks
        if utilization["bottlenecks"]:
            print("\nBottlenecks Detected:")
            for bottleneck in utilization["bottlenecks"]:
                print(f"  {bottleneck['equipment_name']}: {bottleneck['utilization_pct']:.2f}% utilization ({bottleneck['severity']} severity)")
        else:
            print("\nNo bottlenecks detected.")
            
        # Check unutilized capacity
        if utilization["unutilized_capacity"]:
            print("\nUnutilized Capacity:")
            for unused in utilization["unutilized_capacity"]:
                print(f"  {unused['equipment_name']}: {unused['utilization_pct']:.2f}% utilization (unused: {unused['unused_hours']:.2f} hours)")
        
        # Multi-Year Capacity Analysis
        # Analyze capacity constraints from 2025 to 2030
        start_year = 2025
        end_year = 2030
        
        constraints = identify_capacity_constraints(base_scenario.id, start_year, end_year)
        
        print(f"\nCapacity Constraints Analysis ({start_year}-{end_year}):")
        
        # Show bottlenecks by year
        if constraints["bottlenecks_by_year"]:
            print("\nBottlenecks by Year:")
            for year, bottlenecks in sorted(constraints["bottlenecks_by_year"].items()):
                print(f"\n  Year {year}:")
                for bottleneck in bottlenecks:
                    print(f"    {bottleneck['equipment_name']}: {bottleneck['utilization_pct']:.2f}% utilization ({bottleneck['severity']} severity)")
        else:
            print("\nNo bottlenecks detected across the analysis period.")
        
        # Show capacity expansion recommendations
        if constraints["capacity_expansion_recommendations"]:
            print("\nCapacity Expansion Recommendations:")
            for rec in constraints["capacity_expansion_recommendations"]:
                print(f"\n  {rec['equipment_name']} (Year {rec['constraint_year']}):")
                print(f"    {rec['recommendation']}")
                print(f"    Details: {rec['details']}")
                print(f"    Estimated Cost: ${rec['estimated_cost']:,.2f}")
        else:
            print("\nNo capacity expansion recommendations.")

        # Visualize Equipment Utilization
        # Create a heat map of equipment utilization by year
        heatmap_fig = plot_utilization_heatmap(base_scenario.id, start_year, end_year)
        if not isinstance(heatmap_fig, dict):  # Check if it's not an error result
            plt.show()

        # Shift Operation Modeling
        # Model shift operations for 2025
        year = 2025
        
        # Define different shift configurations to compare
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
        
        # Compare shift operations
        shift_comparison_fig = plot_shift_comparison(base_scenario.id, year, shift_configs)
        if not isinstance(shift_comparison_fig, dict):  # Check if it's not an error result
            plt.show()

        # Equipment Purchase Optimization
        # Set budget constraint
        budget_constraint = 1000000  # $1M budget
        
        # Run optimization from 2025 to 2030
        start_year = 2025
        optimization_years = 6
        
        optimization = optimize_equipment_purchases(
            base_scenario.id, 
            budget_constraint=budget_constraint,
            start_year=start_year,
            optimization_years=optimization_years
        )
        
        if "error" in optimization:
            print(f"Error: {optimization['error']}")
        else:
            print(f"\nEquipment Purchase Optimization (Budget: ${budget_constraint:,.2f}):\n")
            
            if optimization["equipment_purchase_plan"]:
                print("Recommended Equipment Purchases:")
                total_cost = 0
                
                for year, purchases in sorted(optimization["equipment_purchase_plan"].items()):
                    year_cost = sum(p["cost"] for p in purchases)
                    total_cost += year_cost
                    
                    print(f"\n  Year {year} (Total: ${year_cost:,.2f}):")
                    for purchase in purchases:
                        print(f"    {purchase['equipment_name']}: ${purchase['cost']:,.2f} - Adds {purchase['capacity_added']} capacity")
                
                print(f"\nTotal Investment: ${total_cost:,.2f}")
                print(f"Bottlenecks Addressed: {optimization['bottlenecks_addressed']}")
            else:
                print("No equipment purchases recommended.")
                
            if optimization["bottlenecks_remaining"]:
                print("\nRemaining Bottlenecks (Budget Constrained):")
                for bottleneck in optimization["bottlenecks_remaining"]:
                    print(f"  {bottleneck['equipment_name']} in year {bottleneck['year']}: {bottleneck['utilization_pct']:.2f}% utilization")

        # Create a comprehensive report
        report_result = export_equipment_analysis_report(
            base_scenario.id,
            start_year=2025,
            end_year=2030,
            output_file="Equipment_Analysis_Report.pdf"
        )
        
        if "error" in report_result:
            print(f"Error generating report: {report_result['error']}")
        else:
            print(f"\nEquipment analysis report generated: {report_result['file_path']}")