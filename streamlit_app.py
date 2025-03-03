import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import sqlite3
import datetime
from pathlib import Path
import math

# Set page configuration
st.set_page_config(
    page_title="Manufacturing Expansion Planner",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DB_PATH = "manufacturing_model.db"

def init_database():
    """Initialize SQLite database with required tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Scenario table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scenario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        initial_revenue REAL,
        initial_costs REAL,
        annual_revenue_growth REAL,
        annual_cost_growth REAL,
        debt_ratio REAL,
        interest_rate REAL,
        tax_rate REAL,
        is_base_case INTEGER,
        created_at TEXT
    )
    ''')
    
    # Create Equipment table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        name TEXT NOT NULL,
        cost REAL,
        useful_life INTEGER,
        max_capacity REAL,
        maintenance_cost_pct REAL,
        availability_pct REAL,
        purchase_year INTEGER,
        is_leased INTEGER,
        lease_rate REAL,
        FOREIGN KEY (scenario_id) REFERENCES scenario (id)
    )
    ''')
    
    # Create Product table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        name TEXT NOT NULL,
        initial_units REAL,
        unit_price REAL,
        growth_rate REAL,
        introduction_year INTEGER,
        market_size REAL,
        price_elasticity REAL,
        FOREIGN KEY (scenario_id) REFERENCES scenario (id)
    )
    ''')
    
    # Create CostDriver table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cost_driver (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        equipment_id INTEGER,
        cost_per_hour REAL,
        hours_per_unit REAL,
        materials_cost_per_unit REAL,
        machinist_labor_cost_per_hour REAL,
        machinist_hours_per_unit REAL,
        design_labor_cost_per_hour REAL,
        design_hours_per_unit REAL,
        supervision_cost_per_hour REAL,
        supervision_hours_per_unit REAL,
        FOREIGN KEY (product_id) REFERENCES product (id),
        FOREIGN KEY (equipment_id) REFERENCES equipment (id)
    )
    ''')
    
    # Create FinancialProjection table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_projection (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        year INTEGER,
        revenue REAL,
        cogs REAL,
        gross_profit REAL,
        operating_expenses REAL,
        ebitda REAL,
        depreciation REAL,
        ebit REAL,
        interest REAL,
        tax REAL,
        net_income REAL,
        capacity_utilization REAL,
        FOREIGN KEY (scenario_id) REFERENCES scenario (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_scenarios():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM scenario ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_scenario(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM scenario WHERE id = {scenario_id}", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_equipment(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM equipment WHERE scenario_id = {scenario_id}", conn)
    conn.close()
    return df

def get_products(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM product WHERE scenario_id = {scenario_id}", conn)
    conn.close()
    return df

def get_cost_drivers(product_id, equipment_id=None):
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM cost_driver WHERE product_id = {product_id}"
    if equipment_id:
        query += f" AND equipment_id = {equipment_id}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_financial_projections(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM financial_projection WHERE scenario_id = {scenario_id} ORDER BY year", conn)
    conn.close()
    return df

def create_scenario(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO scenario (
        name, description, initial_revenue, initial_costs, 
        annual_revenue_growth, annual_cost_growth, debt_ratio, 
        interest_rate, tax_rate, is_base_case, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], 
        data['description'], 
        data['initial_revenue'], 
        data['initial_costs'],
        data['annual_revenue_growth'], 
        data['annual_cost_growth'], 
        data['debt_ratio'],
        data['interest_rate'], 
        data['tax_rate'], 
        data['is_base_case'],
        datetime.datetime.now().isoformat()
    ))
    
    scenario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scenario_id

def add_equipment(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO equipment (
        scenario_id, name, cost, useful_life, max_capacity,
        maintenance_cost_pct, availability_pct, purchase_year, is_leased, lease_rate
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['scenario_id'],
        data['name'],
        data['cost'],
        data['useful_life'],
        data['max_capacity'],
        data['maintenance_cost_pct'],
        data['availability_pct'],
        data['purchase_year'],
        data['is_leased'],
        data['lease_rate']
    ))
    
    equipment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return equipment_id

def add_product(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO product (
        scenario_id, name, initial_units, unit_price, growth_rate,
        introduction_year, market_size, price_elasticity
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['scenario_id'],
        data['name'],
        data['initial_units'],
        data['unit_price'],
        data['growth_rate'],
        data['introduction_year'],
        data.get('market_size', 0),
        data.get('price_elasticity', 0)
    ))
    
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def add_cost_driver(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO cost_driver (
        product_id, equipment_id, cost_per_hour, hours_per_unit,
        materials_cost_per_unit, machinist_labor_cost_per_hour, machinist_hours_per_unit,
        design_labor_cost_per_hour, design_hours_per_unit,
        supervision_cost_per_hour, supervision_hours_per_unit
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['product_id'],
        data['equipment_id'],
        data['cost_per_hour'],
        data['hours_per_unit'],
        data['materials_cost_per_unit'],
        data['machinist_labor_cost_per_hour'],
        data['machinist_hours_per_unit'],
        data['design_labor_cost_per_hour'],
        data['design_hours_per_unit'],
        data['supervision_cost_per_hour'],
        data['supervision_hours_per_unit']
    ))
    
    cost_driver_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cost_driver_id

def delete_equipment(equipment_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete associated cost drivers first
    cursor.execute(f"DELETE FROM cost_driver WHERE equipment_id = {equipment_id}")
    
    # Delete the equipment
    cursor.execute(f"DELETE FROM equipment WHERE id = {equipment_id}")
    
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete associated cost drivers first
    cursor.execute(f"DELETE FROM cost_driver WHERE product_id = {product_id}")
    
    # Delete the product
    cursor.execute(f"DELETE FROM product WHERE id = {product_id}")
    
    conn.commit()
    conn.close()

def save_financial_projection(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if projection exists for this scenario and year
    cursor.execute(
        "SELECT id FROM financial_projection WHERE scenario_id = ? AND year = ?",
        (data['scenario_id'], data['year'])
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update existing
        fields = ', '.join([f"{k} = ?" for k in data.keys() if k not in ['id', 'scenario_id', 'year']])
        values = [data[k] for k in data.keys() if k not in ['id', 'scenario_id', 'year']]
        values.extend([data['scenario_id'], data['year']])
        
        cursor.execute(
            f"UPDATE financial_projection SET {fields} WHERE scenario_id = ? AND year = ?",
            values
        )
    else:
        # Insert new
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = list(data.values())
        
        cursor.execute(
            f"INSERT INTO financial_projection ({fields}) VALUES ({placeholders})",
            values
        )
    
    conn.commit()
    conn.close()

# Simple implementation of the calculation functions
def calculate_unit_economics(product_id):
    """
    Calculate the unit economics for a product
    """
    conn = sqlite3.connect(DB_PATH)
    product = pd.read_sql(f"SELECT * FROM product WHERE id = {product_id}", conn)
    cost_drivers = pd.read_sql(f"SELECT * FROM cost_driver WHERE product_id = {product_id}", conn)
    conn.close()
    
    if product.empty:
        return {"error": f"Product with ID {product_id} not found"}
    
    # Calculate costs
    equipment_costs = 0
    materials_costs = 0
    labor_costs = 0
    
    for _, cd in cost_drivers.iterrows():
        equipment_costs += cd['cost_per_hour'] * cd['hours_per_unit']
        materials_costs += cd['materials_cost_per_unit']
        labor_costs += (
            cd['machinist_labor_cost_per_hour'] * cd['machinist_hours_per_unit'] +
            cd['design_labor_cost_per_hour'] * cd['design_hours_per_unit'] +
            cd['supervision_cost_per_hour'] * cd['supervision_hours_per_unit']
        )
    
    # Calculate unit cost and margins
    unit_cost = equipment_costs + materials_costs + labor_costs
    gross_profit_per_unit = product.iloc[0]['unit_price'] - unit_cost
    gross_margin_pct = (gross_profit_per_unit / product.iloc[0]['unit_price']) * 100 if product.iloc[0]['unit_price'] > 0 else 0
    
    return {
        "product_name": product.iloc[0]['name'],
        "unit_price": product.iloc[0]['unit_price'],
        "unit_cost": unit_cost,
        "equipment_costs": equipment_costs,
        "materials_costs": materials_costs,
        "labor_costs": labor_costs,
        "gross_profit_per_unit": gross_profit_per_unit,
        "gross_margin_pct": gross_margin_pct
    }

def calculate_equipment_utilization(scenario_id, year):
    """
    Calculate equipment utilization for a scenario and year
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Get products and equipment
    products = pd.read_sql(f"SELECT * FROM product WHERE scenario_id = {scenario_id}", conn)
    equipment = pd.read_sql(f"SELECT * FROM equipment WHERE scenario_id = {scenario_id}", conn)
    
    result = {
        "equipment_utilization": [],
        "total_capacity": 0,
        "used_capacity": 0
    }
    
    # Calculate production volumes for each product
    product_volumes = {}
    for _, prod in products.iterrows():
        if prod['introduction_year'] <= year:
            years_since_intro = year - prod['introduction_year']
            volume = prod['initial_units'] * ((1 + prod['growth_rate']) ** years_since_intro)
            product_volumes[prod['id']] = volume
    
    # Calculate utilization for each equipment
    for _, eq in equipment.iterrows():
        if eq['purchase_year'] <= year:
            max_available_hours = eq['max_capacity'] * eq['availability_pct']
            total_hours_used = 0
            
            # Get hours used per product on this equipment
            cost_drivers = pd.read_sql(f"SELECT * FROM cost_driver WHERE equipment_id = {eq['id']}", conn)
            
            for _, cd in cost_drivers.iterrows():
                if cd['product_id'] in product_volumes:
                    volume = product_volumes[cd['product_id']]
                    hours_used = volume * cd['hours_per_unit']
                    total_hours_used += hours_used
            
            # Calculate utilization percentage
            utilization_pct = (total_hours_used / max_available_hours) * 100 if max_available_hours > 0 else 0
            
            result["equipment_utilization"].append({
                "equipment_id": eq['id'],
                "equipment_name": eq['name'],
                "max_capacity": max_available_hours,
                "used_capacity": total_hours_used,
                "utilization_pct": utilization_pct
            })
            
            result["total_capacity"] += max_available_hours
            result["used_capacity"] += total_hours_used
    
    # Calculate overall utilization
    result["overall_utilization_pct"] = (result["used_capacity"] / result["total_capacity"]) * 100 if result["total_capacity"] > 0 else 0
    
    conn.close()
    return result

def calculate_financial_projection(scenario_id, year):
    """
    Calculate financial projection for a specific year
    """
    # Get scenario details
    scenario = get_scenario(scenario_id)
    if scenario is None:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get products
    products_df = get_products(scenario_id)
    
    # Get equipment
    equipment_df = get_equipment(scenario_id)
    
    # Calculate total revenue and costs
    total_revenue = 0
    total_cogs = 0
    
    for _, product in products_df.iterrows():
        if product['introduction_year'] <= year:
            # Calculate years since introduction
            years_since_intro = year - product['introduction_year']
            
            # Calculate units based on growth
            units = product['initial_units'] * ((1 + product['growth_rate']) ** years_since_intro)
            
            # Calculate revenue for this product
            product_revenue = units * product['unit_price']
            total_revenue += product_revenue
            
            # Calculate COGS for this product
            unit_economics = calculate_unit_economics(product['id'])
            if "error" not in unit_economics:
                total_cogs += units * unit_economics["unit_cost"]
    
    # If no product-specific calculations, use scenario defaults
    if total_revenue == 0:
        total_revenue = scenario['initial_revenue'] * ((1 + scenario['annual_revenue_growth']) ** year)
    
    if total_cogs == 0:
        total_cogs = scenario['initial_costs'] * ((1 + scenario['annual_cost_growth']) ** year)
    
    # Calculate other financials
    gross_profit = total_revenue - total_cogs
    operating_expenses = total_cogs * 0.20  # Simplified assumption
    ebitda = gross_profit - operating_expenses
    
    # Calculate equipment depreciation
    total_depreciation = 0
    for _, eq in equipment_df.iterrows():
        if eq['purchase_year'] <= year and year < eq['purchase_year'] + eq['useful_life']:
            annual_depreciation = eq['cost'] / eq['useful_life']
            total_depreciation += annual_depreciation
    
    # Calculate other financials
    ebit = ebitda - total_depreciation
    interest = scenario['debt_ratio'] * total_revenue * scenario['interest_rate']
    taxable_income = ebit - interest
    tax = max(0, taxable_income * scenario['tax_rate'])
    net_income = taxable_income - tax
    
    # Get utilization
    utilization = calculate_equipment_utilization(scenario_id, year)
    
    # Create projection data
    projection = {
        "scenario_id": scenario_id,
        "year": year,
        "revenue": total_revenue,
        "cogs": total_cogs,
        "gross_profit": gross_profit,
        "operating_expenses": operating_expenses,
        "ebitda": ebitda,
        "depreciation": total_depreciation,
        "ebit": ebit,
        "interest": interest,
        "tax": tax,
        "net_income": net_income,
        "capacity_utilization": utilization["overall_utilization_pct"]
    }
    
    return projection

def calculate_financial_projections(scenario_id, projection_years=5):
    """
    Generate financial projections for multiple years
    """
    projections = []
    
    for year in range(projection_years):
        projection = calculate_financial_projection(scenario_id, year)
        if "error" not in projection:
            projections.append(projection)
            save_financial_projection(projection)
    
    return projections

def identify_capacity_constraints(scenario_id, start_year, end_year):
    """
    Identify capacity constraints and bottlenecks over time
    """
    # Initialize result
    result = {
        "bottlenecks_by_year": {},
        "equipment_utilization_trend": {},
        "capacity_expansion_recommendations": []
    }
    
    # Get equipment list
    equipment_df = get_equipment(scenario_id)
    
    # Track utilization trends
    utilization_trends = {}
    for _, eq in equipment_df.iterrows():
        utilization_trends[eq['id']] = {
            "equipment_name": eq['name'],
            "years": [],
            "utilization": []
        }
    
    # Calculate utilization for each year
    for year in range(start_year, end_year + 1):
        utilization = calculate_equipment_utilization(scenario_id, year)
        
        # Track bottlenecks
        bottlenecks = []
        for eq_util in utilization["equipment_utilization"]:
            if eq_util["utilization_pct"] > 85:
                bottlenecks.append({
                    "equipment_id": eq_util["equipment_id"],
                    "equipment_name": eq_util["equipment_name"],
                    "utilization_pct": eq_util["utilization_pct"],
                    "severity": "high" if eq_util["utilization_pct"] > 95 else "medium"
                })
                
                # Update trend data
                if eq_util["equipment_id"] in utilization_trends:
                    utilization_trends[eq_util["equipment_id"]]["years"].append(year)
                    utilization_trends[eq_util["equipment_id"]]["utilization"].append(eq_util["utilization_pct"])
        
        if bottlenecks:
            result["bottlenecks_by_year"][year] = bottlenecks
    
    # Store utilization trends
    result["equipment_utilization_trend"] = utilization_trends
    
    # Generate recommendations
    for eq_id, trend in utilization_trends.items():
        if trend["utilization"] and any(util >= 85 for util in trend["utilization"]):
            years_over_threshold = [
                trend["years"][i] for i, util in enumerate(trend["utilization"]) 
                if util >= 85
            ]
            
            if years_over_threshold:
                first_year_over = min(years_over_threshold)
                
                # Get equipment details
                eq_info = equipment_df[equipment_df['id'] == eq_id]
                if not eq_info.empty:
                    eq = eq_info.iloc[0]
                    
                    # Add recommendation
                    result["capacity_expansion_recommendations"].append({
                        "equipment_id": eq_id,
                        "equipment_name": trend["equipment_name"],
                        "constraint_year": first_year_over,
                        "recommendation": "Add additional capacity",
                        "details": f"Utilization exceeds 85% in year {first_year_over}. Consider purchasing additional {trend['equipment_name']} equipment.",
                        "estimated_cost": eq['cost']
                    })
    
    return result

def generate_swot_analysis(scenario_id):
    """Generate SWOT analysis based on financial projections and utilization"""
    projections = get_financial_projections(scenario_id)
    
    if projections.empty:
        return None
    
    revenue_forecast = projections['revenue'].tolist()
    cost_forecast = projections['cogs'].tolist()
    utilization_rate = projections['capacity_utilization'].tolist()
    
    strengths, weaknesses, opportunities, threats = [], [], [], []

    # Strengths
    if max(utilization_rate) < 80:
        strengths.append("Capacity available for expansion")
    if max(revenue_forecast) / max(cost_forecast) > 1.5:
        strengths.append("Strong revenue-to-cost ratio")
    if all(proj['net_income'] > 0 for _, proj in projections.iterrows()):
        strengths.append("Consistently profitable across all years")

    # Weaknesses
    if min(utilization_rate) > 90:
        weaknesses.append("High equipment utilization may lead to bottlenecks")
    if min(revenue_forecast) / min(cost_forecast) < 1.2:
        weaknesses.append("Tight profit margins in some periods")
    if max(utilization_rate) - min(utilization_rate) > 40:
        weaknesses.append("Significant variability in capacity utilization")

    # Opportunities
    if max(revenue_forecast) > 2 * min(revenue_forecast):
        opportunities.append("Strong revenue growth potential")
    if min(utilization_rate) < 50:
        opportunities.append("Potential to add more production volume")
    if projections['capacity_utilization'].iloc[-1] > 80:
        opportunities.append("Potential market for capacity expansion")

    # Threats
    if any(proj['net_income'] < 0 for _, proj in projections.iterrows()):
        threats.append("Negative profitability in some periods")
    if max(utilization_rate) > 95:
        threats.append("Risk of capacity constraints and production bottlenecks")
    if max(cost_forecast) / min(cost_forecast) > max(revenue_forecast) / min(revenue_forecast):
        threats.append("Costs growing faster than revenue")
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats
    }

# App UI functions
def render_sidebar():
    st.sidebar.title("Manufacturing Expansion Planner")
    
    # Navigation
    st.sidebar.header("Navigation")
    return st.sidebar.radio(
        "Select Section", 
        ["Dashboard", "Manage Scenarios", "Equipment Management", "Product Management", "Financial Analysis", "Capacity Planning"]
    )

def render_dashboard(active_scenario_id):
    st.title("Manufacturing Expansion Dashboard")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario to view the dashboard.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    
    # Get counts
    products_df = get_products(active_scenario_id)
    equipment_df = get_equipment(active_scenario_id)
    financial_projections = get_financial_projections(active_scenario_id)
    
    # Header with key metrics
    st.header(f"Scenario: {scenario['name']}")
    st.write(f"*{scenario['description']}*")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Products", len(products_df))
    with col2:
        st.metric("Equipment", len(equipment_df))
    with col3:
        st.metric("Revenue Growth", f"{scenario['annual_revenue_growth']:.1%}")
    with col4:
        if not financial_projections.empty:
            latest_year = financial_projections['year'].max()
            latest_projection = financial_projections[financial_projections['year'] == latest_year]
            if not latest_projection.empty:
                st.metric("Latest Utilization", f"{latest_projection.iloc[0]['capacity_utilization']:.1f}%")
    
    # Check if we have financial projections
    if financial_projections.empty:
        st.warning("No financial projections available. Go to Financial Analysis to generate projections.")
        if st.button("Generate Financial Projections"):
            with st.spinner("Calculating financial projections..."):
                calculate_financial_projections(active_scenario_id, 5)
                st.success("Financial projections generated!")
                st.experimental_rerun()
        return
    
    # Financial overview
    st.subheader("Financial Overview")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue and Income chart
        plt.figure(figsize=(10, 5))
        plt.plot(financial_projections['year'], financial_projections['revenue'], 'b-', marker='o', label='Revenue')
        plt.plot(financial_projections['year'], financial_projections['net_income'], 'g-', marker='s', label='Net Income')
        plt.title("Revenue and Net Income Projection")
        plt.xlabel("Year")
        plt.ylabel("Amount ($)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        st.pyplot(plt)
        plt.close()
    
    with col2:
        # Capacity Utilization chart
        plt.figure(figsize=(10, 5))
        plt.plot(financial_projections['year'], financial_projections['capacity_utilization'], 'r-', marker='o')
        plt.axhline(y=85, color='r', linestyle='--', alpha=0.5, label="Bottleneck Threshold (85%)")
        plt.axhline(y=50, color='g', linestyle='--', alpha=0.5, label="Underutilization Threshold (50%)")
        plt.title("Capacity Utilization Trend")
        plt.xlabel("Year")
        plt.ylabel("Utilization (%)")
        plt.ylim(0, 105)
        plt.legend()
        plt.grid(True, alpha=0.3)
        st.pyplot(plt)
        plt.close()
    
    # SWOT Analysis
    st.subheader("SWOT Analysis")
    swot = generate_swot_analysis(active_scenario_id)
    
    if swot:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Strengths**")
            for strength in swot["strengths"]:
                st.write(f"✅ {strength}")
            
            st.write("**Weaknesses**")
            for weakness in swot["weaknesses"]:
                st.write(f"⚠️ {weakness}")
        
        with col2:
            st.write("**Opportunities**")
            for opportunity in swot["opportunities"]:
                st.write(f"🚀 {opportunity}")
            
            st.write("**Threats**")
            for threat in swot["threats"]:
                st.write(f"🔴 {threat}")
    
    # Equipment and Product tables
    st.subheader("Equipment Inventory")
    st.dataframe(equipment_df[['name', 'cost', 'useful_life', 'max_capacity', 'availability_pct']])
    
    st.subheader("Product Portfolio")
    st.dataframe(products_df[['name', 'initial_units', 'unit_price', 'growth_rate', 'introduction_year']])
    
    # Capacity constraints
    constraints = identify_capacity_constraints(active_scenario_id, 0, 5)
    
    if constraints["capacity_expansion_recommendations"]:
        st.subheader("⚠️ Capacity Alerts")
        for rec in constraints["capacity_expansion_recommendations"]:
            st.warning(f"**{rec['equipment_name']}**: {rec['details']}")

def render_scenario_management():
    st.title("Scenario Management")
    
    # Get all scenarios
    scenarios_df = get_scenarios()
    
    # Show existing scenarios
    if not scenarios_df.empty:
        st.subheader("Existing Scenarios")
        
        # Format the dataframe for display
        display_df = display_df = scenarios_df[['id', 'name', 'description', 'annual_revenue_growth', 'annual_cost_growth', 'is_base_case', 'created_at']]
        
        ## PART 2
        
        display_df['annual_revenue_growth'] = display_df['annual_revenue_growth'].apply(lambda x: f"{x:.1%}")
        display_df['annual_cost_growth'] = display_df['annual_cost_growth'].apply(lambda x: f"{x:.1%}")
        display_df['is_base_case'] = display_df['is_base_case'].apply(lambda x: "✓" if x else "")
        
        # Show the dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Select active scenario
        scenario_options = scenarios_df['name'].tolist()
        selected_scenario = st.selectbox("Select active scenario", scenario_options)
        
        selected_id = scenarios_df[scenarios_df['name'] == selected_scenario]['id'].values[0]
        if st.button("Set as Active Scenario"):
            st.session_state.active_scenario_id = selected_id
            st.success(f"Scenario '{selected_scenario}' set as active")
        
        # Option to clone scenario
        if st.button("Clone Selected Scenario"):
            st.session_state.clone_scenario = selected_id
            st.info("Fill in the form below to clone the scenario")
    
    # Create new scenario form
    st.subheader("Create New Scenario")
    
    # If cloning, pre-fill with selected scenario data
    prefill_data = {}
    if 'clone_scenario' in st.session_state and st.session_state.clone_scenario:
        clone_id = st.session_state.clone_scenario
        clone_data = get_scenario(clone_id)
        if clone_data is not None:
            prefill_data = clone_data.to_dict()
            st.info(f"Cloning scenario: {prefill_data['name']}")
    
    with st.form("create_scenario_form"):
        # Basic scenario info
        name = st.text_input("Scenario Name", value=f"{prefill_data.get('name', '')} Copy" if prefill_data else "")
        description = st.text_area("Description", value=prefill_data.get('description', ''))
        
        # Financial assumptions
        col1, col2 = st.columns(2)
        with col1:
            initial_revenue = st.number_input(
                "Initial Annual Revenue ($)", 
                min_value=0.0, 
                value=float(prefill_data.get('initial_revenue', 1000000))
            )
            annual_revenue_growth = st.slider(
                "Annual Revenue Growth (%)", 
                min_value=0.0, 
                max_value=50.0, 
                value=float(prefill_data.get('annual_revenue_growth', 0.05)) * 100
            ) / 100
        
        with col2:
            initial_costs = st.number_input(
                "Initial Annual Costs ($)", 
                min_value=0.0, 
                value=float(prefill_data.get('initial_costs', 750000))
            )
            annual_cost_growth = st.slider(
                "Annual Cost Growth (%)", 
                min_value=0.0, 
                max_value=50.0, 
                value=float(prefill_data.get('annual_cost_growth', 0.03)) * 100
            ) / 100
        
        # Financing inputs
        col1, col2 = st.columns(2)
        with col1:
            debt_ratio = st.slider(
                "Debt Financing Ratio (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=float(prefill_data.get('debt_ratio', 0.3)) * 100
            ) / 100
            
        with col2:
            interest_rate = st.slider(
                "Annual Interest Rate (%)", 
                min_value=0.0, 
                max_value=20.0, 
                value=float(prefill_data.get('interest_rate', 0.04)) * 100
            ) / 100
        
        # Tax rate
        tax_rate = st.slider(
            "Corporate Tax Rate (%)", 
            min_value=0.0, 
            max_value=40.0, 
            value=float(prefill_data.get('tax_rate', 0.21)) * 100
        ) / 100
        
        # Base case flag
        is_base_case = st.checkbox("Set as Base Case", value=False)
        
        ## PART#
        
        # Submit button
        submitted = st.form_submit_button("Create Scenario")
        
        if submitted and name:
            # Create scenario data
            scenario_data = {
                'name': name,
                'description': description,
                'initial_revenue': initial_revenue,
                'initial_costs': initial_costs,
                'annual_revenue_growth': annual_revenue_growth,
                'annual_cost_growth': annual_cost_growth,
                'debt_ratio': debt_ratio,
                'interest_rate': interest_rate,
                'tax_rate': tax_rate,
                'is_base_case': 1 if is_base_case else 0
            }
            
            # Create the scenario
            scenario_id = create_scenario(scenario_data)
            
            # Clone equipment and products if needed
            if 'clone_scenario' in st.session_state and st.session_state.clone_scenario:
                clone_id = st.session_state.clone_scenario
                
                # Clone equipment
                equipment_df = get_equipment(clone_id)
                for _, eq in equipment_df.iterrows():
                    equipment_data = {
                        'scenario_id': scenario_id,
                        'name': eq['name'],
                        'cost': eq['cost'],
                        'useful_life': eq['useful_life'],
                        'max_capacity': eq['max_capacity'],
                        'maintenance_cost_pct': eq['maintenance_cost_pct'],
                        'availability_pct': eq['availability_pct'],
                        'purchase_year': eq['purchase_year'],
                        'is_leased': eq['is_leased'],
                        'lease_rate': eq['lease_rate']
                    }
                    add_equipment(equipment_data)
                
                # Clone products
                products_df = get_products(clone_id)
                for _, prod in products_df.iterrows():
                    product_data = {
                        'scenario_id': scenario_id,
                        'name': prod['name'],
                        'initial_units': prod['initial_units'],
                        'unit_price': prod['unit_price'],
                        'growth_rate': prod['growth_rate'],
                        'introduction_year': prod['introduction_year'],
                        'market_size': prod['market_size'],
                        'price_elasticity': prod['price_elasticity']
                    }
                    add_product(product_data)
                
                # Clear clone flag
                st.session_state.clone_scenario = None
            
            # Set as active scenario
            st.session_state.active_scenario_id = scenario_id
            
            st.success(f"Scenario '{name}' created successfully!")
            st.experimental_rerun()

def render_equipment_management(active_scenario_id):
    st.title("Equipment Management")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Managing Equipment for: {scenario['name']}")
    
    # Get equipment for this scenario
    equipment_df = get_equipment(active_scenario_id)
    
    # Display existing equipment
    if not equipment_df.empty:
        st.subheader("Current Equipment")
        
        # Create a dataframe for display
        display_df = equipment_df[['id', 'name', 'cost', 'useful_life', 'max_capacity', 'availability_pct', 'purchase_year']]
        display_df['availability_pct'] = display_df['availability_pct'].apply(lambda x: f"{x:.1%}")
        
        # Show the dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Allow deleting equipment
        if st.button("Delete Selected Equipment"):
            selected_equipment = st.selectbox("Select equipment to delete", equipment_df['name'])
            selected_id = equipment_df[equipment_df['name'] == selected_equipment]['id'].values[0]
            
            if st.checkbox("Confirm deletion"):
                delete_equipment(selected_id)
                st.success(f"Equipment '{selected_equipment}' deleted successfully!")
                st.experimental_rerun()
    else:
        st.info("No equipment added yet. Use the form below to add equipment.")
    
    # Add new equipment form
    st.subheader("Add New Equipment")
    
    with st.form("add_equipment_form"):
        # Basic equipment info
        name = st.text_input("Equipment Name")
        
        # Cost and capacity
        col1, col2 = st.columns(2)
        with col1:
            cost = st.number_input("Cost ($)", min_value=0.0, value=500000.0)
            useful_life = st.number_input("Useful Life (years)", min_value=1, value=10)
        
        with col2:
            max_capacity = st.number_input("Maximum Capacity (hours/year)", min_value=0.0, value=4000.0)
            availability_pct = st.slider("Availability Percentage (%)", min_value=0.0, max_value=100.0, value=95.0) / 100
        
        # Maintenance and purchase details
        col1, col2 = st.columns(2)
        with col1:
            maintenance_cost_pct = st.slider("Annual Maintenance Cost (% of purchase price)", min_value=0.0, max_value=20.0, value=5.0) / 100
            purchase_year = st.number_input("Purchase Year (0 = initial year)", min_value=0, value=0)
        
        with col2:
            is_leased = st.checkbox("Equipment is Leased")
            lease_rate = st.number_input("Annual Lease Rate ($, if leased)", min_value=0.0, value=0.0)
        
        # Submit button
        submitted = st.form_submit_button("Add Equipment")
        
        if submitted and name:
            # Create equipment data
            equipment_data = {
                'scenario_id': active_scenario_id,
                'name': name,
                'cost': cost,
                'useful_life': useful_life,
                'max_capacity': max_capacity,
                'maintenance_cost_pct': maintenance_cost_pct,
                'availability_pct': availability_pct,
                'purchase_year': purchase_year,
                'is_leased': 1 if is_leased else 0,
                'lease_rate': lease_rate
            }
            
            # Add the equipment
            add_equipment(equipment_data)
            
            st.success(f"Equipment '{name}' added successfully!")
            st.experimental_rerun()

def render_product_management(active_scenario_id):
    st.title("Product Management")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Managing Products for: {scenario['name']}")
    
    # Get products for this scenario
    products_df = get_products(active_scenario_id)
    
    # Display existing products
    if not products_df.empty:
        st.subheader("Current Products")
        
        # Create a dataframe for display
        display_df = products_df[['id', 'name', 'initial_units', 'unit_price', 'growth_rate', 'introduction_year']]
        display_df['growth_rate'] = display_df['growth_rate'].apply(lambda x: f"{x:.1%}")
        display_df['unit_price'] = display_df['unit_price'].apply(lambda x: f"${x:.2f}")
        
        # Show the dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Show unit economics for each product
        for _, product in products_df.iterrows():
            with st.expander(f"Unit Economics: {product['name']}"):
                economics = calculate_unit_economics(product['id'])
                
                if "error" not in economics:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Unit Price", f"${economics['unit_price']:.2f}")
                        st.metric("Unit Cost", f"${economics['unit_cost']:.2f}")
                    with col2:
                        st.metric("Gross Profit", f"${economics['gross_profit_per_unit']:.2f}")
                        st.metric("Gross Margin", f"{economics['gross_margin_pct']:.1f}%")
                    with col3:
                        st.metric("Equipment Costs", f"${economics['equipment_costs']:.2f}")
                        st.metric("Labor Costs", f"${economics['labor_costs']:.2f}")
                        st.metric("Material Costs", f"${economics['materials_costs']:.2f}")
                else:
                    st.warning(economics["error"])
        
        # Allow deleting products
        if st.button("Delete Selected Product"):
            selected_product = st.selectbox("Select product to delete", products_df['name'])
            selected_id = products_df[products_df['name'] == selected_product]['id'].values[0]
            
            if st.checkbox("Confirm deletion"):
                delete_product(selected_id)
                st.success(f"Product '{selected_product}' deleted successfully!")
                st.experimental_rerun()
    else:
        st.info("No products added yet. Use the form below to add products.")
    
    # Add new product form
    st.subheader("Add New Product")
    
    # First get equipment for this scenario for cost drivers
    equipment_df = get_equipment(active_scenario_id)
    
    if equipment_df.empty:
        st.warning("Please add equipment first before adding products.")
        return
    
    with st.form("add_product_form"):
        # Basic product info
        name = st.text_input("Product Name")
        
        # Volume and price
        col1, col2 = st.columns(2)
        with col1:
            initial_units = st.number_input("Initial Annual Volume (units)", min_value=1, value=1000)
            unit_price = st.number_input("Unit Selling Price ($)", min_value=0.01, value=100.0)
        
        with col2:
            growth_rate = st.slider("Annual Growth Rate (%)", min_value=0.0, max_value=50.0, value=10.0) / 100
            introduction_year = st.number_input("Introduction Year (0 = initial year)", min_value=0, value=0)
        
        # Advanced product info
        with st.expander("Advanced Product Details"):
            market_size = st.number_input("Total Market Size (units)", min_value=0, value=0)
            price_elasticity = st.number_input("Price Elasticity of Demand", min_value=0.0, value=0.0)
        
        # Cost Drivers
        st.subheader("Cost Drivers by Equipment")
        
        # Create dict to store cost driver inputs
        cost_driver_inputs = {}
        
        for _, eq in equipment_df.iterrows():
            with st.expander(f"Cost Drivers for {eq['name']}"):
                # Equipment usage
                col1, col2 = st.columns(2)
                with col1:
                    cost_per_hour = st.number_input(f"{eq['name']} - Cost Per Hour ($)", min_value=0.0, value=50.0, key=f"cost_per_hour_{eq['id']}")
                with col2:
                    hours_per_unit = st.number_input(f"{eq['name']} - Hours Per Unit", min_value=0.0, value=0.5, key=f"hours_per_unit_{eq['id']}")
                
                # Materials cost
                materials_cost_per_unit = st.number_input(f"{eq['name']} - Materials Cost Per Unit ($)", min_value=0.0, value=20.0, key=f"materials_{eq['id']}")
                
                # Labor costs
                col1, col2 = st.columns(2)
                with col1:
                    machinist_cost_per_hour = st.number_input(f"Machinist Labor - Cost Per Hour ($)", min_value=0.0, value=30.0, key=f"mach_cost_{eq['id']}")
                    design_cost_per_hour = st.number_input(f"Design Labor - Cost Per Hour ($)", min_value=0.0, value=40.0, key=f"design_cost_{eq['id']}")
                    supervision_cost_per_hour = st.number_input(f"Supervision - Cost Per Hour ($)", min_value=0.0, value=50.0, key=f"super_cost_{eq['id']}")
                
                with col2:
                    machinist_hours_per_unit = st.number_input(f"Machinist Labor - Hours Per Unit", min_value=0.0, value=0.5, key=f"mach_hours_{eq['id']}")
                    design_hours_per_unit = st.number_input(f"Design Labor - Hours Per Unit", min_value=0.0, value=0.25, key=f"design_hours_{eq['id']}")
                    supervision_hours_per_unit = st.number_input(f"Supervision - Hours Per Unit", min_value=0.0, value=0.1, key=f"super_hours_{eq['id']}")
                
                # Store in dictionary
                cost_driver_inputs[eq['id']] = {
                    "cost_per_hour": cost_per_hour,
                    "hours_per_unit": hours_per_unit,
                    "materials_cost_per_unit": materials_cost_per_unit,
                    "machinist_labor_cost_per_hour": machinist_cost_per_hour,
                    "machinist_hours_per_unit": machinist_hours_per_unit,
                    "design_labor_cost_per_hour": design_cost_per_hour,
                    "design_hours_per_unit": design_hours_per_unit,
                    "supervision_cost_per_hour": supervision_cost_per_hour,
                    "supervision_hours_per_unit": supervision_hours_per_unit
                }
                
                # Submit button
        submitted = st.form_submit_button("Add Product")
        
        if submitted and name:
            # Create product data
            product_data = {
                'scenario_id': active_scenario_id,
                'name': name,
                'initial_units': initial_units,
                'unit_price': unit_price,
                'growth_rate': growth_rate,
                'introduction_year': introduction_year,
                'market_size': market_size,
                'price_elasticity': price_elasticity
            }
            
            # Add the product
            product_id = add_product(product_data)
            
            # Add cost drivers
            for equipment_id, driver_data in cost_driver_inputs.items():
                cost_driver_data = {
                    'product_id': product_id,
                    'equipment_id': equipment_id,
                    **driver_data
                }
                add_cost_driver(cost_driver_data)
            
            st.success(f"Product '{name}' added successfully!")
            st.experimental_rerun()

def render_financial_analysis(active_scenario_id):
    st.title("Financial Analysis")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Financial Analysis for: {scenario['name']}")
    
    # Get financial projections
    financial_projections = get_financial_projections(active_scenario_id)
    
    # Option to generate/recalculate projections
    col1, col2 = st.columns([3, 1])
    with col1:
        projection_years = st.slider("Projection Years", min_value=1, max_value=10, value=5)
    with col2:
        if st.button("Calculate Projections"):
            with st.spinner("Calculating financial projections..."):
                calculate_financial_projections(active_scenario_id, projection_years)
                st.success("Financial projections calculated!")
                st.experimental_rerun()
    
    # If we have projections, display them
    if not financial_projections.empty:
        # Income Statement
        st.subheader("Income Statement")
        
        # Format the income statement
        income_statement = financial_projections[['year', 'revenue', 'cogs', 'gross_profit', 
                                                 'operating_expenses', 'ebitda', 'depreciation', 
                                                 'ebit', 'interest', 'tax', 'net_income']]
        
        # Show the income statement
        st.dataframe(income_statement.style.format("${:,.0f}", subset=income_statement.columns[1:]), use_container_width=True)
        
        # Profitability Metrics
        st.subheader("Profitability Metrics")
        
        # Calculate profitability metrics
        profitability = pd.DataFrame({
            "Year": financial_projections['year'],
            "Gross Margin": (financial_projections['gross_profit'] / financial_projections['revenue']) * 100,
            "EBITDA Margin": (financial_projections['ebitda'] / financial_projections['revenue']) * 100,
            "Net Profit Margin": (financial_projections['net_income'] / financial_projections['revenue']) * 100
        })
        
        # Display metrics
        st.dataframe(profitability.style.format("{:.1f}%", subset=profitability.columns[1:]), use_container_width=True)
        
        # Revenue and Income visualization
        st.subheader("Revenue and Income Visualization")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.bar(financial_projections['year'], financial_projections['revenue'], alpha=0.7, label='Revenue')
        ax.bar(financial_projections['year'], financial_projections['net_income'], alpha=0.7, label='Net Income')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Revenue and Net Income Projection')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        st.pyplot(fig)
        plt.close()
        
        # Margin visualization
        st.subheader("Margin Visualization")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(profitability['Year'], profitability['Gross Margin'], marker='o', label='Gross Margin')
        ax.plot(profitability['Year'], profitability['EBITDA Margin'], marker='s', label='EBITDA Margin')
        ax.plot(profitability['Year'], profitability['Net Profit Margin'], marker='^', label='Net Profit Margin')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Margin (%)')
        ax.set_title('Margin Trends')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        st.pyplot(fig)
        plt.close()
        
        # Return on Investment analysis
        st.subheader("Return on Investment Analysis")
        
        # Calculate cumulative metrics
        total_revenue = financial_projections['revenue'].sum()
        total_net_income = financial_projections['net_income'].sum()
        
        # Get equipment investment
        equipment_df = get_equipment(active_scenario_id)
        total_investment = equipment_df['cost'].sum()
        
        # Calculate ROI
        if total_investment > 0:
            roi = (total_net_income / total_investment) * 100
            
            # Display ROI
            st.metric("Return on Investment (ROI)", f"{roi:.1f}%")
            
            # Calculate payback period (simplified)
            cumulative_income = 0
            payback_year = None
            
            for year, income in zip(financial_projections['year'], financial_projections['net_income']):
                cumulative_income += income
                if cumulative_income >= total_investment and payback_year is None:
                    payback_year = year
            
            if payback_year is not None:
                st.metric("Payback Period", f"{payback_year} years")
            else:
                st.warning("Investment not fully recovered within the projection period")
        else:
            st.info("No equipment investment to calculate ROI")
    else:
        st.warning("No financial projections available. Click 'Calculate Projections' to generate them.")

def render_capacity_planning(active_scenario_id):
    st.title("Capacity Planning")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Capacity Planning for: {scenario['name']}")
    
    # Get equipment
    equipment_df = get_equipment(active_scenario_id)
    
    if equipment_df.empty:
        st.warning("No equipment added yet. Please add equipment first.")
        return
    
    # Select year range for analysis
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", min_value=0, value=0)
    with col2:
        end_year = st.number_input("End Year", min_value=start_year, value=5)
    
    # Run capacity analysis
    if st.button("Analyze Capacity Constraints"):
        with st.spinner("Analyzing capacity constraints..."):
            constraints = identify_capacity_constraints(active_scenario_id, start_year, end_year)
            
            # Display utilization heatmap
            st.subheader("Equipment Utilization Heatmap")
            
            # Prepare data for heatmap
            utilization_trends = constraints["equipment_utilization_trend"]
            equipment_names = []
            years = sorted(set(year for trend in utilization_trends.values() for year in trend["years"]))
            
            if years:
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
                if heatmap_data:
                    fig, ax = plt.subplots(figsize=(12, len(equipment_names) * 0.5 + 2))
                    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn_r", 
                                vmin=0, vmax=100, cbar_kws={'label': 'Utilization %'},
                                yticklabels=equipment_names, xticklabels=years, ax=ax)
                    
                    plt.title("Equipment Utilization Heatmap")
                    plt.xlabel("Year")
                    plt.ylabel("Equipment")
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                    plt.close()
            
            # Display bottlenecks by year
            if constraints["bottlenecks_by_year"]:
                st.subheader("Bottlenecks by Year")
                
                for year, bottlenecks in sorted(constraints["bottlenecks_by_year"].items()):
                    st.write(f"**Year {year}:**")
                    for bottleneck in bottlenecks:
                        severity_color = "🔴" if bottleneck["severity"] == "high" else "🟠"
                        st.write(f"{severity_color} {bottleneck['equipment_name']}: {bottleneck['utilization_pct']:.1f}% utilization ({bottleneck['severity']} severity)")
            else:
                st.success("No bottlenecks detected within the selected time range.")
            
            # Display capacity expansion recommendations
            if constraints["capacity_expansion_recommendations"]:
                st.subheader("Capacity Expansion Recommendations")
                
                for rec in constraints["capacity_expansion_recommendations"]:
                    with st.expander(f"{rec['equipment_name']} - Year {rec['constraint_year']}"):
                        st.write(f"**Recommendation:** {rec['recommendation']}")
                        st.write(f"**Details:** {rec['details']}")
                        st.write(f"**Estimated Cost:** ${rec['estimated_cost']:,.2f}")
            else:
                st.info("No capacity expansion recommendations for the selected time range.")
    
    # Shift operations modeling
    st.subheader("Shift Operations Modeling")
    
    # Select year for shift modeling
    shift_year = st.number_input("Select Year for Shift Analysis", min_value=0, value=1)
    
    # Shift configuration inputs
    shift_configs = {}
    
    for config_name, default_values in [
        ("Single Shift", {"shifts": 1, "hours": 8, "days": 5, "ot_mult": 1.5, "ot_hours": 10}),
        ("Double Shift", {"shifts": 2, "hours": 8, "days": 5, "ot_mult": 1.5, "ot_hours": 5}),
        ("24/7 Operation", {"shifts": 3, "hours": 8, "days": 7, "ot_mult": 2.0, "ot_hours": 0})
    ]:
        with st.expander(f"Configure {config_name}"):
            col1, col2 = st.columns(2)
            with col1:

                
                ## PART 4
                
                shifts = st.number_input(f"Shifts per Day", min_value=1, max_value=3, value=default_values["shifts"], key=f"shifts_{config_name}")
                hours = st.number_input(f"Hours per Shift", min_value=1, max_value=12, value=default_values["hours"], key=f"hours_{config_name}")
            
            with col2:
                days = st.number_input(f"Days per Week", min_value=1, max_value=7, value=default_values["days"], key=f"days_{config_name}")
                weeks = st.number_input(f"Weeks per Year", min_value=1, max_value=52, value=50, key=f"weeks_{config_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                ot_mult = st.number_input(f"Overtime Multiplier", min_value=1.0, max_value=3.0, value=default_values["ot_mult"], key=f"ot_mult_{config_name}")
            
            with col2:
                ot_hours = st.number_input(f"Max Overtime Hours per Week", min_value=0, max_value=40, value=default_values["ot_hours"], key=f"ot_hours_{config_name}")
            
            shift_configs[config_name] = {
                "shifts_per_day": shifts,
                "hours_per_shift": hours,
                "days_per_week": days,
                "weeks_per_year": weeks,
                "overtime_multiplier": ot_mult,
                "max_overtime_hours_per_week": ot_hours
            }
    
    if st.button("Compare Shift Configurations"):
        st.subheader("Shift Configuration Comparison")
        
        # Calculate standard hours and capacity for each configuration
        standard_hours = {}
        overtime_capacity = {}
        total_capacity = {}
        
        for name, config in shift_configs.items():
            standard_hours[name] = (
                config["shifts_per_day"] * 
                config["hours_per_shift"] * 
                config["days_per_week"] * 
                config["weeks_per_year"]
            )
            
            overtime_capacity[name] = (
                config["max_overtime_hours_per_week"] * 
                config["weeks_per_year"]
            )
            
            total_capacity[name] = standard_hours[name] + overtime_capacity[name]
        
        # Create comparison visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot standard hours comparison
        ax1.bar(standard_hours.keys(), standard_hours.values(), color="blue", alpha=0.7, label="Standard Hours")
        ax1.bar(overtime_capacity.keys(), overtime_capacity.values(), bottom=list(standard_hours.values()), 
                color="orange", alpha=0.7, label="Overtime Capacity")
        
        ax1.set_title("Annual Hours by Shift Configuration")
        ax1.set_xlabel("Shift Configuration")
        ax1.set_ylabel("Hours per Year")
        ax1.legend()
        
        # Add value labels
        for i, config in enumerate(standard_hours.keys()):
            # Standard hours
            standard = standard_hours[config]
            ax1.annotate(f'{standard:,}',
                       xy=(i, standard/2),
                       ha='center', va='center',
                       color='white', fontweight='bold')
            
            # Total including overtime
            if overtime_capacity[config] > 0:
                total = standard + overtime_capacity[config]
                ax1.annotate(f'Total: {total:,}',
                           xy=(i, standard + 100),
                           ha='center', va='bottom')
        
        # Plot cost comparison (simplified)
        annual_costs = {
            name: (standard_hours[name] * 50) +  # Base rate of $50/hour
                 (overtime_capacity[name] * 50 * config["overtime_multiplier"])  # Overtime rate
            for name, config in shift_configs.items()
        }
        
        ax2.bar(annual_costs.keys(), annual_costs.values(), color="red", alpha=0.7)
        ax2.set_title("Estimated Annual Labor Cost by Shift Configuration")
        ax2.set_xlabel("Shift Configuration")
        ax2.set_ylabel("Cost ($)")
        
        # Add value labels
        for i, (config, cost) in enumerate(annual_costs.items()):
            ax2.annotate(f'${cost:,.0f}',
                       xy=(i, cost),
                       ha='center', va='bottom')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # Calculate required equipment based on utilization
        st.subheader(f"Equipment Requirements (Year {shift_year})")
        
        # Get equipment utilization for the selected year
        utilization = calculate_equipment_utilization(active_scenario_id, shift_year)
        
        # Create a table to show requirements for each shift configuration
        equipment_requirements = []
        
        for eq_util in utilization["equipment_utilization"]:
            eq_name = eq_util["equipment_name"]
            used_capacity = eq_util["used_capacity"]
            
            row = {"Equipment": eq_name, "Required Hours": f"{used_capacity:.1f}"}
            
            for config_name, hours in standard_hours.items():
                # Calculate number of machines needed
                machines_needed = used_capacity / hours
                overtime_machines = 0
                
                # If we need overtime or additional machines
                if machines_needed > 1:
                    # Integer part is full machines
                    full_machines = int(machines_needed)
                    
                    # Fractional part could be overtime on one machine
                    remaining_hours = used_capacity - (full_machines * hours)
                    
                    # Check if remaining can be covered by overtime
                    if remaining_hours <= overtime_capacity[config_name]:
                        overtime_machines = 1
                        machines_needed = full_machines
                    else:
                        # Need another full machine
                        machines_needed = full_machines + 1
                        overtime_machines = 0
                
                if overtime_machines > 0:
                    row[config_name] = f"{machines_needed} + OT"
                else:
                    row[config_name] = f"{math.ceil(machines_needed)}"
            
            equipment_requirements.append(row)
        
        # Display the requirements table
        if equipment_requirements:
            st.dataframe(pd.DataFrame(equipment_requirements))
        else:
            st.info("No equipment utilization data for the selected year.")

# Main application
def main():
    # Initialize database if needed
    init_database()
    
    # Initialize session state
    if 'active_scenario_id' not in st.session_state:
        # Check if we have any scenarios
        scenarios_df = get_scenarios()
        if not scenarios_df.empty:
            # Use the first scenario as active by default
            st.session_state.active_scenario_id = scenarios_df.iloc[0]['id']
        else:
            st.session_state.active_scenario_id = None
    
    # Render sidebar for navigation
    section = render_sidebar()
    
    # Render selected section
    if section == "Dashboard":
        render_dashboard(st.session_state.active_scenario_id)
    elif section == "Manage Scenarios":
        render_scenario_management()
    elif section == "Equipment Management":
        render_equipment_management(st.session_state.active_scenario_id)
    elif section == "Product Management":
        render_product_management(st.session_state.active_scenario_id)
    elif section == "Financial Analysis":
        render_financial_analysis(st.session_state.active_scenario_id)
    elif section == "Capacity Planning":
        render_capacity_planning(st.session_state.active_scenario_id)

if __name__ == "__main__":
    main()