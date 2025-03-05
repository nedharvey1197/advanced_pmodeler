#!/usr/bin/env python3
# Manufacturing Expansion Model - Main Application
# This script provides a unified interface to all model components

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Setup path to include our modules
base_dir = Path('./manufacturing_model')
if str(base_dir) not in sys.path:
    sys.path.append(str(base_dir))

# Import modules
from models import (
    Scenario, Equipment, Product, CostDriver, FinancialProjection,
    get_session, create_tables
)
from services.financial_service import (
    calculate_financial_projections,
    calculate_key_financial_metrics,
    generate_swot_analysis
)
from services.equipment_service import (
    calculate_equipment_utilization_by_product,
    identify_capacity_constraints,
    model_shift_operations,
    optimize_equipment_purchases
)
from services.scenario_service import ScenarioManager
from utils.financial_utils import (
    get_financial_projection_dataframe,
    export_financial_projections_excel,
    create_financial_dashboard
)
from utils.visualization_utils import (
    plot_equipment_utilization,
    plot_utilization_heatmap,
    export_equipment_analysis_report
)

def setup_database():
    """Initialize the database and create tables"""
    create_tables()
    print("Database initialized.")

def import_json_data(json_path):
    """Import data from JSON file"""
    from utils.db_utils import load_json_data, migrate_data_to_database
    
    json_data = load_json_data(json_path)
    scenario_id = migrate_data_to_database(json_data)
    
    print(f"Data imported to scenario with ID: {scenario_id}")
    return scenario_id

def run_financial_analysis(scenario_id, start_year=2025, projection_years=5, export_excel=False, create_dashboard=False):
    """Run comprehensive financial analysis for a scenario"""
    # Get scenario
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        print(f"Scenario with ID {scenario_id} not found.")
        return
    
    # Calculate financial projections
    print(f"Calculating financial projections for '{scenario.name}'...")
    calculate_financial_projections(scenario_id, start_year, projection_years)
    
    # Calculate key metrics
    metrics = calculate_key_financial_metrics(scenario_id)
    
    # Get financial projections dataframe
    df = get_financial_projection_dataframe(scenario_id)
    
    # Print summary
    print(f"\nFinancial Analysis Summary for '{scenario.name}':")
    
    if "revenue_cagr" in metrics:
        print(f"Revenue CAGR: {metrics['revenue_cagr']*100:.2f}%")
    
    if "roi" in metrics:
        print(f"ROI: {metrics['roi']:.2f}%")
    
    if "payback_period" in metrics:
        print(f"Payback Period: {metrics['payback_period']:.2f} years")
    
    # Generate SWOT
    swot = generate_swot_analysis(scenario_id)
    
    print("\nSWOT Analysis:")
    print("Strengths:")
    for s in swot["strengths"]:
        print(f"- {s}")
    
    print("\nWeaknesses:")
    for w in swot["weaknesses"]:
        print(f"- {w}")
    
    print("\nOpportunities:")
    for o in swot["opportunities"]:
        print(f"- {o}")
    
    print("\nThreats:")
    for t in swot["threats"]:
        print(f"- {t}")
    
    # Export to Excel if requested
    if export_excel:
        result = export_financial_projections_excel(scenario_id)
        if "file_path" in result:
            print(f"\nExported financial projections to: {result['file_path']}")
    
    # Create dashboard if requested
    if create_dashboard:
        result = create_financial_dashboard(scenario_id)
        if "file_path" in result:
            print(f"\nCreated financial dashboard at: {result['file_path']}")
    
    return df

def run_equipment_analysis(scenario_id, start_year=2025, end_year=2030, create_report=False):
    """Run comprehensive equipment utilization analysis"""
    # Get scenario
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        print(f"Scenario with ID {scenario_id} not found.")
        return
    
    # Identify capacity constraints
    print(f"Analyzing equipment capacity for '{scenario.name}'...")
    constraints = identify_capacity_constraints(scenario_id, start_year, end_year)
    
    # Print summary
    print(f"\nEquipment Analysis Summary for '{scenario.name}':")
    
    if "bottlenecks_by_year" in constraints:
        bottleneck_count = sum(len(bottlenecks) for bottlenecks in constraints["bottlenecks_by_year"].values())
        print(f"Identified {bottleneck_count} potential bottlenecks across {len(constraints['bottlenecks_by_year'])} years.")
    
    if "capacity_expansion_recommendations" in constraints:
        print(f"Capacity expansion recommendations: {len(constraints['capacity_expansion_recommendations'])}")
        
        for i, rec in enumerate(constraints["capacity_expansion_recommendations"]):
            print(f"\nRecommendation {i+1}:")
            print(f"Equipment: {rec['equipment_name']}")
            print(f"Year: {rec['constraint_year']}")
            print(f"Details: {rec['details']}")
            print(f"Estimated Cost: ${rec['estimated_cost']:,.2f}")
    
    # Run shift analysis for the last year
    shift_analysis = model_shift_operations(scenario_id, end_year)
    
    if "equipment_shift_analysis" in shift_analysis:
        overloaded = [eq_data for eq_id, eq_data in shift_analysis["equipment_shift_analysis"].items() 
                     if eq_data["status"] == "overloaded"]
        
        overtime = [eq_data for eq_id, eq_data in shift_analysis["equipment_shift_analysis"].items() 
                   if eq_data["status"] == "overtime"]
        
        print(f"\nShift Analysis for Year {end_year}:")
        print(f"Total Overtime Cost: ${shift_analysis['total_overtime_cost']:,.2f}")
        print(f"Overloaded Equipment: {len(overloaded)}")
        print(f"Equipment Requiring Overtime: {len(overtime)}")
    
    # Run optimization
    budget = 1000000  # $1M budget
    optimization = optimize_equipment_purchases(
        scenario_id, 
        budget_constraint=budget,
        start_year=start_year,
        optimization_years=end_year - start_year + 1
    )
    
    if "equipment_purchase_plan" in optimization:
        purchase_count = sum(len(purchases) for purchases in optimization["equipment_purchase_plan"].values())
        
        print(f"\nEquipment Purchase Optimization (Budget: ${budget:,.2f}):")
        print(f"Recommended Purchases: {purchase_count}")
        print(f"Total Investment: ${optimization['total_cost']:,.2f}")
        print(f"Bottlenecks Addressed: {optimization['bottlenecks_addressed']}")
        print(f"Bottlenecks Remaining: {len(optimization['bottlenecks_remaining'])}")
    
    # Create report if requested
    if create_report:
        result = export_equipment_analysis_report(scenario_id, start_year, end_year)
        if "file_path" in result:
            print(f"\nCreated equipment analysis report at: {result['file_path']}")
    
    return constraints

def run_scenario_analysis(scenario_ids, export_report=False):
    """Run scenario comparison analysis"""
    # Initialize scenario manager
    scenario_manager = ScenarioManager()
    
    # Get scenarios
    session = get_session()
    scenarios = session.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
    
    if not scenarios:
        print("No matching scenarios found.")
        return
    
    scenario_names = [s.name for s in scenarios]
    print(f"Comparing scenarios: {', '.join(scenario_names)}")
    
    # Compare income statement
    df_income = scenario_manager.compare_scenarios(scenario_ids, "income_statement")
    
    # Print summary
    if not isinstance(df_income, dict):
        print("\nIncome Statement Comparison:")
        
        # Get the last year for each scenario
        last_year = df_income.index[-1]
        
        print(f"\nKey metrics for year {last_year}:")
        for scenario in scenarios:
            if (scenario.name, "revenue") in df_income.columns and (scenario.name, "net_income") in df_income.columns:
                revenue = df_income.loc[last_year, (scenario.name, "revenue")]
                net_income = df_income.loc[last_year, (scenario.name, "net_income")]
                margin = (net_income / revenue) * 100 if revenue else 0
                
                print(f"\n{scenario.name}:")
                print(f"Revenue: ${revenue:,.2f}")
                print(f"Net Income: ${net_income:,.2f}")
                print(f"Net Margin: {margin:.2f}%")
    
    # Export report if requested
    if export_report:
        result = scenario_manager.export_comparison_report(scenario_ids)
        if "file_path" in result:
            print(f"\nExported scenario comparison report to: {result['file_path']}")
    
    return df_income

def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description='Manufacturing Expansion Financial Model')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Initialize the database')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import data from JSON file')
    import_parser.add_argument('json_path', help='Path to JSON file')
    
    # Financial analysis command
    financial_parser = subparsers.add_parser('finance', help='Run financial analysis')
    financial_parser.add_argument('scenario_id', type=int, help='Scenario ID')
    financial_parser.add_argument('--start', type=int, default=2025, help='Start year')
    financial_parser.add_argument('--years', type=int, default=5, help='Projection years')
    financial_parser.add_argument('--excel', action='store_true', help='Export to Excel')
    financial_parser.add_argument('--dashboard', action='store_true', help='Create dashboard')
    
    # Equipment analysis command
    equipment_parser = subparsers.add_parser('equipment', help='Run equipment analysis')
    equipment_parser.add_argument('scenario_id', type=int, help='Scenario ID')
    equipment_parser.add_argument('--start', type=int, default=2025, help='Start year')
    equipment_parser.add_argument('--end', type=int, default=2030, help='End year')
    equipment_parser.add_argument('--report', action='store_true', help='Create report')
    
    # Scenario comparison command
    scenario_parser = subparsers.add_parser('compare', help='Compare scenarios')
    scenario_parser.add_argument('scenario_ids', type=int, nargs='+', help='Scenario IDs to compare')
    scenario_parser.add_argument('--report', action='store_true', help='Export comparison report')
    
    # List scenarios command
    list_parser = subparsers.add_parser('list', help='List all scenarios')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'setup':
        setup_database()
    
    elif args.command == 'import':
        import_json_data(args.json_path)
    
    elif args.command == 'finance':
        run_financial_analysis(
            args.scenario_id, 
            args.start, 
            args.years, 
            args.excel, 
            args.dashboard
        )
    
    elif args.command == 'equipment':
        run_equipment_analysis(
            args.scenario_id, 
            args.start, 
            args.end, 
            args.report
        )
    
    elif args.command == 'compare':
        run_scenario_analysis(
            args.scenario_ids, 
            args.report
        )
    
    elif args.command == 'list':
        scenario_manager = ScenarioManager()
        scenarios = scenario_manager.list_scenarios()
        
        print("Available Scenarios:")
        for s in scenarios:
            print(f"ID: {s['id']}, Name: {s['name']}{' (Base Case)' if s['is_base_case'] else ''}")
            print(f"  Description: {s['description']}")
            print(f"  Financial Assumptions: Revenue Growth: {s['annual_revenue_growth']*100:.1f}%, Cost Growth: {s['annual_cost_growth']*100:.1f}%")
            print()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
