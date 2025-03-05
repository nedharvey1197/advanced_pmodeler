# Import statements first
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import math
import time
import altair as alt

# Set up page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Manufacturing Model",
    page_icon="🏭",
    layout="wide"
)

# Constants
DB_PATH = "manufacturing_model.db"

def init_sample_data():
    """Initialize database with sample data"""
    try:
        print("\n=== Initializing sample data ===")
        
        # Check if we already have scenarios
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scenario")
        count = cursor.fetchone()[0]
        
        # Create a base case scenario
        base_scenario_data = {
            'name': 'Base Case',
            'description': 'Initial baseline scenario for manufacturing expansion',
            'initial_revenue': 1000000.0,
            'initial_costs': 750000.0,
            'annual_revenue_growth': 0.05,
            'annual_cost_growth': 0.03,
            'debt_ratio': 0.3,
            'interest_rate': 0.04,
            'tax_rate': 0.21,
            'is_base_case': 1
        }
        
        # Create the scenario
        scenario_id = create_scenario(base_scenario_data)
        
        # Create an optimistic scenario
        optimistic_scenario = {
            'name': 'Optimistic Case',
            'description': 'High growth scenario with favorable market conditions',
            'initial_revenue': 1200000.0,
            'initial_costs': 800000.0,
            'annual_revenue_growth': 0.08,
            'annual_cost_growth': 0.04,
            'debt_ratio': 0.4,
            'interest_rate': 0.035,
            'tax_rate': 0.21,
            'is_base_case': 0
        }
        optimistic_id = create_scenario(optimistic_scenario)
        
        # Equipment data template
        base_equipment = [
            {
                'name': 'CNC Machine',
                'cost': 250000.0,
                'useful_life': 10,
                'max_capacity': 4000.0,
                'maintenance_cost_pct': 0.05,
                'availability_pct': 0.95,
                'purchase_year': 0,
                'financing_type': 'Debt',
                'is_leased': 0,
                'lease_type': None,
                'lease_rate': 0.0,
                'debt_ratio': 0.8,
                'interest_rate': 0.05
            },
            {
                'name': '3D Printer',
                'cost': 75000.0,
                'useful_life': 5,
                'max_capacity': 3000.0,
                'maintenance_cost_pct': 0.03,
                'availability_pct': 0.98,
                'purchase_year': 0,
                'financing_type': 'Cash Purchase',
                'is_leased': 0,
                'lease_type': None,
                'lease_rate': 0.0,
                'debt_ratio': 0.0,
                'interest_rate': 0.0
            },
            {
                'name': 'Assembly Line',
                'cost': 500000.0,
                'useful_life': 15,
                'max_capacity': 6000.0,
                'maintenance_cost_pct': 0.06,
                'availability_pct': 0.92,
                'purchase_year': 1,
                'financing_type': 'Lease',
                'is_leased': 1,
                'lease_type': 'Capital Lease',
                'lease_rate': 75000.0,
                'debt_ratio': 0.0,
                'interest_rate': 0.0
            }
        ]
        
        # Add equipment to both scenarios
        equipment_ids = {}
        for scenario_id in [scenario_id, optimistic_id]:
            scenario_equipment = []
            for eq in base_equipment:
                eq_data = eq.copy()
                eq_data['scenario_id'] = scenario_id
                eq_id = add_equipment(eq_data)
                scenario_equipment.append(eq_id)
            equipment_ids[scenario_id] = scenario_equipment
        
        # Product data template
        base_products = [
            {
                'name': 'Widget A',
                'initial_units': 5000,
                'unit_price': 100.0,
                'growth_rate': 0.08,
                'introduction_year': 0,
                'market_size': 50000,
                'price_elasticity': 1.2
            },
            {
                'name': 'Widget B',
                'initial_units': 3000,
                'unit_price': 150.0,
                'growth_rate': 0.12,
                'introduction_year': 1,
                'market_size': 30000,
                'price_elasticity': 1.5
            },
            {
                'name': 'Premium Widget',
                'initial_units': 1000,
                'unit_price': 300.0,
                'growth_rate': 0.15,
                'introduction_year': 2,
                'market_size': 15000,
                'price_elasticity': 2.0
            }
        ]
        
        # Add products to both scenarios
        for scenario_id in [scenario_id, optimistic_id]:
            for prod in base_products:
                prod_data = prod.copy()
                prod_data['scenario_id'] = scenario_id
                
                # Adjust volumes for optimistic scenario
                if scenario_id == optimistic_id:
                    prod_data['initial_units'] *= 1.2
                    prod_data['growth_rate'] *= 1.2
                    prod_data['market_size'] *= 1.1
                
                product_id = add_product(prod_data)
                
                # Add cost drivers for each equipment piece
                for eq_id in equipment_ids[scenario_id]:
                    cost_driver_data = {
                        'product_id': product_id,
                        'equipment_id': eq_id,
                        'cost_per_hour': 50.0,
                        'hours_per_unit': 0.5,
                        'materials_cost_per_unit': 20.0,
                        'machinist_labor_cost_per_hour': 30.0,
                        'machinist_hours_per_unit': 0.5,
                        'design_labor_cost_per_hour': 40.0,
                        'design_hours_per_unit': 0.25,
                        'supervision_cost_per_hour': 50.0,
                        'supervision_hours_per_unit': 0.1
                    }
                    
                    # Adjust costs for optimistic scenario
                    if scenario_id == optimistic_id:
                        cost_driver_data['hours_per_unit'] *= 0.9  # 10% efficiency improvement
                        cost_driver_data['materials_cost_per_unit'] *= 0.95  # 5% cost reduction
                    
                    add_cost_driver(cost_driver_data)
        
        # Generate initial financial projections
        calculate_financial_projections(scenario_id, 5)
        calculate_financial_projections(optimistic_id, 5)
        
        print("Sample data initialized successfully!")
        return True, "Sample data initialized successfully!"
        
    except Exception as e:
        error_msg = f"Error initializing sample data: {str(e)}"
        import traceback
        traceback_msg = f"Traceback: {traceback.format_exc()}"
        print(error_msg)
        print(traceback_msg)
        return False, error_msg

def init_database():
    """Initialize SQLite database with required tables if they don't exist"""
    print("\n=== Initializing database... ===")
    conn = None
    try:
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tables
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
        
        # Create Equipment table with financing options
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
            financing_type TEXT,
            is_leased INTEGER,
            lease_type TEXT,
            lease_rate REAL,
            debt_ratio REAL,
            interest_rate REAL,
            FOREIGN KEY (scenario_id) REFERENCES scenario (id) ON DELETE CASCADE
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
            FOREIGN KEY (scenario_id) REFERENCES scenario (id) ON DELETE CASCADE
        )
        ''')
        
        # Create Cost Driver table
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
            FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE,
            FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE
        )
        ''')
        
        # Create Financial Projections table
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
            FOREIGN KEY (scenario_id) REFERENCES scenario (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        print("Database initialized successfully")
        return True, "Database initialized successfully"
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        st.error(f"Error initializing database: {e}")
        return False, f"Error initializing database: {e}"
        
    finally:
        if conn:
            conn.close()

def ensure_database():
    """Ensure database exists with tables and sample data"""
    try:
        print("\n=== Checking database state ===")
        
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            print(f"Database not found at {DB_PATH}")
            success, message = init_database()
            if not success:
                st.error(message)
                return False
                
            print("Initializing sample data after database creation")
            success, message = init_sample_data()
            if success:
                st.success(message)
            else:
                st.error(message)
            return success
            
        return True
            
    except Exception as e:
        st.error(f"Error ensuring database: {str(e)}")
        return False

def get_scenarios():
    """Get all scenarios from the database"""
    try:
        print("\n=== Starting get_scenarios() ===")
        conn = sqlite3.connect(DB_PATH)
        
        # Define the query with explicit type casting
        query = """
        SELECT 
            CAST(id AS INTEGER) as id,
            CAST(name AS TEXT) as name,
            CAST(description AS TEXT) as description,
            CAST(initial_revenue AS REAL) as initial_revenue,
            CAST(initial_costs AS REAL) as initial_costs,
            CAST(annual_revenue_growth AS REAL) as annual_revenue_growth,
            CAST(annual_cost_growth AS REAL) as annual_cost_growth,
            CAST(debt_ratio AS REAL) as debt_ratio,
            CAST(interest_rate AS REAL) as interest_rate,
            CAST(tax_rate AS REAL) as tax_rate,
            CAST(is_base_case AS INTEGER) as is_base_case,
            CAST(created_at AS TEXT) as created_at
        FROM scenario 
        ORDER BY created_at DESC
        """
        
        # Use pandas.read_sql with dtype specifications
        df = pd.read_sql(
            query, 
            conn,
            dtype={
                'id': 'Int64',
                'name': 'object',
                'description': 'object',
                'initial_revenue': 'float64',
                'initial_costs': 'float64',
                'annual_revenue_growth': 'float64',
                'annual_cost_growth': 'float64',
                'debt_ratio': 'float64',
                'interest_rate': 'float64',
                'tax_rate': 'float64',
                'is_base_case': 'Int64',
                'created_at': 'object'
            }
        )
        
        conn.close()
        
        print("\nDEBUG: DataFrame shape:", df.shape)
        print("DEBUG: DataFrame dtypes:", df.dtypes)
        
        return df

    except Exception as e:
        print(f"\nERROR in get_scenarios: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Create an empty DataFrame with correct dtypes
        df = pd.DataFrame({
            'id': pd.Series(dtype='Int64'),
            'name': pd.Series(dtype='object'),
            'description': pd.Series(dtype='object'),
            'initial_revenue': pd.Series(dtype='float64'),
            'initial_costs': pd.Series(dtype='float64'),
            'annual_revenue_growth': pd.Series(dtype='float64'),
            'annual_cost_growth': pd.Series(dtype='float64'),
            'debt_ratio': pd.Series(dtype='float64'),
            'interest_rate': pd.Series(dtype='float64'),
            'tax_rate': pd.Series(dtype='float64'),
            'is_base_case': pd.Series(dtype='Int64'),
            'created_at': pd.Series(dtype='object')
        })
        return df

# Database helper functions
def get_scenario(scenario_id):
    """Get a scenario by ID"""
    if scenario_id is None:
        return None
        
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM scenario WHERE id = {scenario_id}", conn)
    conn.close()
    
    if df.empty:
        return None
        
    # Convert the first row to a dictionary
    scenario_dict = df.iloc[0].to_dict()
    
    # Ensure all fields are present
    required_fields = ['id', 'name', 'description', 'is_base_case', 'annual_revenue_growth']
    for field in required_fields:
        if field not in scenario_dict:
            scenario_dict[field] = None
            
    return scenario_dict

def get_equipment(scenario_id):
    try:
        print(f"\n=== Getting equipment for scenario {scenario_id} ===")
        conn = sqlite3.connect(DB_PATH)
        
        # Get the data with explicit type casting
        query = """
        SELECT 
            CAST(id AS INTEGER) as id,
            CAST(scenario_id AS INTEGER) as scenario_id,
            CAST(name AS TEXT) as name,
            CAST(cost AS REAL) as cost,
            CAST(useful_life AS INTEGER) as useful_life,
            CAST(max_capacity AS REAL) as max_capacity,
            CAST(maintenance_cost_pct AS REAL) as maintenance_cost_pct,
            CAST(availability_pct AS REAL) as availability_pct,
            CAST(purchase_year AS INTEGER) as purchase_year,
            CAST(financing_type AS TEXT) as financing_type,
            CAST(is_leased AS INTEGER) as is_leased,
            CAST(lease_type AS TEXT) as lease_type,
            CAST(lease_rate AS REAL) as lease_rate,
            CAST(debt_ratio AS REAL) as debt_ratio,
            CAST(interest_rate AS REAL) as interest_rate
        FROM equipment 
        WHERE scenario_id = ?
        """
        
        # Use pandas.read_sql with dtype specifications
        df = pd.read_sql(
            query,
            conn,
            params=(int(scenario_id),),  # Ensure scenario_id is an integer
            dtype={
                'id': 'Int64',
                'scenario_id': 'Int64',
                'name': 'object',
                'cost': 'float64',
                'useful_life': 'Int64',
                'max_capacity': 'float64',
                'maintenance_cost_pct': 'float64',
                'availability_pct': 'float64',
                'purchase_year': 'Int64',
                'financing_type': 'object',
                'is_leased': 'Int64',
                'lease_type': 'object',
                'lease_rate': 'float64',
                'debt_ratio': 'float64',
                'interest_rate': 'float64'
            }
        )
        
        print(f"Found {len(df)} equipment items")
        print(f"Equipment data: {df.to_dict('records')}")
        
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting equipment: {e}")
        st.error(f"Error getting equipment: {e}")
        return pd.DataFrame(columns=[
            'id', 'scenario_id', 'name', 'cost', 'useful_life', 'max_capacity',
            'maintenance_cost_pct', 'availability_pct', 'purchase_year', 'financing_type',
            'is_leased', 'lease_type', 'lease_rate', 'debt_ratio', 'interest_rate'
        ])

def get_products(scenario_id):
    try:
        print(f"\n=== Getting products for scenario {scenario_id} ===")
        conn = sqlite3.connect(DB_PATH)
        
        # Get the data with explicit type casting
        query = """
        SELECT 
            CAST(id AS INTEGER) as id,
            CAST(scenario_id AS INTEGER) as scenario_id,
            CAST(name AS TEXT) as name,
            CAST(initial_units AS REAL) as initial_units,
            CAST(unit_price AS REAL) as unit_price,
            CAST(growth_rate AS REAL) as growth_rate,
            CAST(introduction_year AS INTEGER) as introduction_year,
            CAST(market_size AS REAL) as market_size,
            CAST(price_elasticity AS REAL) as price_elasticity
        FROM product 
        WHERE scenario_id = ?
        """
        
        # Use pandas.read_sql with dtype specifications
        df = pd.read_sql(
            query,
            conn,
            params=(int(scenario_id),),  # Ensure scenario_id is an integer
            dtype={
                'id': 'Int64',
                'scenario_id': 'Int64',
                'name': 'object',
                'initial_units': 'float64',
                'unit_price': 'float64',
                'growth_rate': 'float64',
                'introduction_year': 'Int64',
                'market_size': 'float64',
                'price_elasticity': 'float64'
            }
        )
        
        print(f"Found {len(df)} products")
        print(f"Product data: {df.to_dict('records')}")
        
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting products: {e}")
        st.error(f"Error getting products: {e}")
        return pd.DataFrame(columns=[
            'id', 'scenario_id', 'name', 'initial_units', 'unit_price',
            'growth_rate', 'introduction_year', 'market_size', 'price_elasticity'
        ])

def get_cost_drivers(product_id, equipment_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute("PRAGMA table_info(cost_driver)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build query
        query = "SELECT * FROM cost_driver WHERE product_id = ?"
        params = [product_id]
        
        if equipment_id:
            query += " AND equipment_id = ?"
            params.append(equipment_id)
            
            # Get the data
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=columns) if data else pd.DataFrame(columns=columns)
            
            conn.close()
            return df
    except Exception as e:
        st.error(f"Error getting cost drivers: {e}")
        return pd.DataFrame(columns=[
            'id', 'product_id', 'equipment_id', 'cost_per_hour', 'hours_per_unit',
            'materials_cost_per_unit', 'machinist_labor_cost_per_hour',
            'machinist_hours_per_unit', 'design_labor_cost_per_hour',
            'design_hours_per_unit', 'supervision_cost_per_hour',
            'supervision_hours_per_unit'
        ])

def get_financial_projections(scenario_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get the data with explicit type casting
        query = """
        SELECT 
            CAST(id AS INTEGER) as id,
            CAST(scenario_id AS INTEGER) as scenario_id,
            CAST(year AS INTEGER) as year,
            CAST(revenue AS REAL) as revenue,
            CAST(cogs AS REAL) as cogs,
            CAST(gross_profit AS REAL) as gross_profit,
            CAST(operating_expenses AS REAL) as operating_expenses,
            CAST(ebitda AS REAL) as ebitda,
            CAST(depreciation AS REAL) as depreciation,
            CAST(ebit AS REAL) as ebit,
            CAST(interest AS REAL) as interest,
            CAST(tax AS REAL) as tax,
            CAST(net_income AS REAL) as net_income,
            CAST(capacity_utilization AS REAL) as capacity_utilization
        FROM financial_projection 
        WHERE scenario_id = ? 
        ORDER BY year
        """
        
        # Use pandas.read_sql with dtype specifications
        df = pd.read_sql(
            query,
            conn,
            params=(scenario_id,),
            dtype={
                'id': 'Int64',
                'scenario_id': 'Int64',
                'year': 'Int64',
                'revenue': 'float64',
                'cogs': 'float64',
                'gross_profit': 'float64',
                'operating_expenses': 'float64',
                'ebitda': 'float64',
                'depreciation': 'float64',
                'ebit': 'float64',
                'interest': 'float64',
                'tax': 'float64',
                'net_income': 'float64',
                'capacity_utilization': 'float64'
            }
        )
        
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error getting financial projections: {e}")
        return pd.DataFrame(columns=[
            'id', 'scenario_id', 'year', 'revenue', 'cogs', 'gross_profit',
            'operating_expenses', 'ebitda', 'depreciation', 'ebit', 'interest',
            'tax', 'net_income', 'capacity_utilization'
        ])

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
        datetime.now().isoformat()
    ))
    
    scenario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scenario_id

def add_equipment(data):
    print(f"\n=== Adding equipment: {data['name']} ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO equipment (
            scenario_id, name, cost, useful_life, max_capacity,
            maintenance_cost_pct, availability_pct, purchase_year, 
            financing_type, is_leased, lease_type, lease_rate, debt_ratio, interest_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['scenario_id'],
            data['name'],
            data['cost'],
            data['useful_life'],
            data['max_capacity'],
            data['maintenance_cost_pct'],
            data['availability_pct'],
            data['purchase_year'],
            data['financing_type'],
            1 if data['is_leased'] else 0,
            data['lease_type'],
            data['lease_rate'],
            data['debt_ratio'],
            data['interest_rate']
        ))
        
        equipment_id = cursor.lastrowid
        print(f"Successfully added equipment with ID: {equipment_id}")
        conn.commit()
        conn.close()
        return equipment_id
        
    except Exception as e:
        print(f"Error adding equipment: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        conn.close()
        raise

def add_product(data):
    print(f"\n=== Adding product: {data['name']} ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO product (
                scenario_id, name, initial_units, unit_price,
                growth_rate, introduction_year, market_size, price_elasticity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            data['scenario_id'],
            data['name'],
            data['initial_units'],
            data['unit_price'],
            data['growth_rate'],
            data['introduction_year'],
            data['market_size'],
            data['price_elasticity']
        ))
        
        product_id = cursor.lastrowid
        print(f"Successfully added product with ID: {product_id}")
        conn.commit()
        conn.close()
        return product_id
            
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        conn.close()
        raise

def add_cost_driver(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
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
        
    except Exception as e:
        print(f"Error adding cost driver: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        conn.close()
        raise

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
    """Render the sidebar navigation"""
    with st.sidebar:
        # Add some padding at the top
        st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
        
        st.subheader("Navigation")
        
        # Get available scenarios
        scenarios_df = get_scenarios()
        
        if not scenarios_df.empty:
            # Initialize active scenario if not set
            if 'active_scenario_id' not in st.session_state:
                base_case = scenarios_df[scenarios_df['is_base_case'] == 1]
                if not base_case.empty:
                    st.session_state.active_scenario_id = base_case.iloc[0]['id']
                else:
                    st.session_state.active_scenario_id = scenarios_df.iloc[0]['id']
            
            # Create scenario selection with custom styling
            st.markdown("""
                <style>
                .stSelectbox {
                    margin-bottom: 1rem;
                    z-index: 1000;
                }
                </style>
            """, unsafe_allow_html=True)
            
            scenario_names = scenarios_df['name'].tolist()
            current_scenario = scenarios_df[scenarios_df['id'] == st.session_state.active_scenario_id].iloc[0]['name']
            selected_scenario = st.selectbox(
                "Select Scenario",
                scenario_names,
                index=scenario_names.index(current_scenario),
                key="scenario_selector",
                help="Choose which scenario to view or modify"
            )
            
            # Update active scenario if changed
            if selected_scenario != current_scenario:
                new_scenario_id = scenarios_df[scenarios_df['name'] == selected_scenario].iloc[0]['id']
                st.session_state.active_scenario_id = new_scenario_id
                st.rerun()
        else:
            st.warning("No scenarios found. Please create a scenario first.")
            st.session_state.active_scenario_id = None
        
        # Add spacing between sections
        st.markdown("<div style='padding: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Navigation options
        st.write("Pages")
        pages = {
            "Dashboard": ("📊", "Overview of key metrics and projections"),
            "Financial Analysis": ("💰", "Detailed financial statements and metrics"),
            "Capacity Planning": ("📈", "Analyze and plan production capacity"),
            "Model Configuration": ("⚙️", "Set up scenarios, equipment, and products")
        }
        
        # Initialize current page if not set
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Dashboard"
        
        # Create navigation buttons with spacing
        for page, (icon, tooltip) in pages.items():
            if st.button(f"{icon} {page}", key=f"nav_{page}", help=tooltip):
                st.session_state.current_page = page
                if page != "Model Configuration":
                    st.session_state.config_page = None
                st.rerun()
            st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Sub-menu for Model Configuration
        if st.session_state.current_page == "Model Configuration":
            st.markdown("<div style='padding: 1rem 0;'></div>", unsafe_allow_html=True)
            st.write("Model Configuration")
            config_pages = {
                "Scenarios": ("📋", "Create and manage scenarios"),
                "Equipment": ("🔧", "Add and configure manufacturing equipment"),
                "Products": ("📦", "Define products and their requirements")
            }
            
            # Initialize config page if not set
            if 'config_page' not in st.session_state:
                st.session_state.config_page = "Scenarios"
            
            # Create sub-menu buttons with spacing
            for page, (icon, tooltip) in config_pages.items():
                if st.button(f"{icon} {page}", key=f"config_{page}", help=tooltip):
                    st.session_state.config_page = page
                    st.rerun()
                st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        return st.session_state.active_scenario_id

def render_dashboard(scenario_id):
    st.title("Dashboard")
    
    # Get scenario data
    scenario = get_scenario(scenario_id)
    if not scenario:
        st.error("Scenario not found")
        return
    
    # Asset Inventory Section
    st.header("Asset Inventory")
    equipment_df = get_equipment(scenario_id)
    
    if not equipment_df.empty:
        # Create display DataFrame with formatted columns
        display_df = equipment_df[['name', 'cost', 'useful_life', 'maintenance_cost_pct', 'financing_type']].copy()
        
        # Format currency columns
        display_df['cost'] = display_df['cost'].apply(lambda x: f"${x:,.2f}")
        
        # Calculate and format maintenance cost
        display_df['annual_maintenance'] = equipment_df.apply(
            lambda row: f"${row['cost'] * row['maintenance_cost_pct']/100:,.2f}", axis=1
        )
        
        # Drop the maintenance_cost_pct column as we now have the calculated value
        display_df = display_df.drop('maintenance_cost_pct', axis=1)
        
        # Rename columns for display
        display_df.columns = ['Equipment', 'Purchase Price', 'Useful Life (Years)', 'Financing', 'Annual Maintenance']
        
        st.dataframe(display_df, hide_index=True)
    else:
        st.info("No equipment data available")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Products", len(get_products(scenario_id)) if isinstance(get_products(scenario_id), pd.DataFrame) else 0)
    with col2:
        st.metric("Equipment", len(equipment_df) if isinstance(equipment_df, pd.DataFrame) else 0)
    with col3:
        growth = scenario.get('annual_revenue_growth', 0)
        growth = float(growth) if growth is not None else 0
        st.metric("Revenue Growth", f"{growth:.1%}")
    with col4:
        if isinstance(get_financial_projections(scenario_id), pd.DataFrame) and not get_financial_projections(scenario_id).empty:
            latest_year = get_financial_projections(scenario_id)['year'].max()
            latest_projection = get_financial_projections(scenario_id)[get_financial_projections(scenario_id)['year'] == latest_year]
            if not latest_projection.empty:
                utilization = latest_projection.iloc[0].get('capacity_utilization', 0)
                utilization = float(utilization) if utilization is not None else 0
                st.metric("Latest Utilization", f"{utilization:.1f}%")
    
    # Financial overview
    if isinstance(get_financial_projections(scenario_id), pd.DataFrame) and not get_financial_projections(scenario_id).empty:
        st.subheader("Financial Overview")
    
        # Create two columns for charts
        col1, col2 = st.columns(2)
    
    with col1:
            # Revenue and Profit Chart
            chart_data = pd.DataFrame({
                'Year': get_financial_projections(scenario_id)['year'],
                'Revenue': get_financial_projections(scenario_id)['revenue'],
                'EBITDA': get_financial_projections(scenario_id)['ebitda'],
                'Net Income': get_financial_projections(scenario_id)['net_income']
            })
            
            chart = alt.Chart(chart_data.melt('Year', var_name='Metric', value_name='Amount')).mark_line(point=True).encode(
                x='Year:O',
                y=alt.Y('Amount:Q', axis=alt.Axis(format='$~s')),
                color='Metric:N',
                tooltip=['Year:O', alt.Tooltip('Amount:Q', format='$,.0f'), 'Metric:N']
            ).properties(
                title='Revenue and Profit Trends'
            )
            
            st.altair_chart(chart, use_container_width=True)
    
    with col2:
            # Margin Chart
            margin_data = pd.DataFrame({
                'Year': get_financial_projections(scenario_id)['year'],
                'Gross Margin': (get_financial_projections(scenario_id)['gross_profit'] / get_financial_projections(scenario_id)['revenue'] * 100),
                'EBITDA Margin': (get_financial_projections(scenario_id)['ebitda'] / get_financial_projections(scenario_id)['revenue'] * 100),
                'Net Margin': (get_financial_projections(scenario_id)['net_income'] / get_financial_projections(scenario_id)['revenue'] * 100)
            })
            
            margin_chart = alt.Chart(margin_data.melt('Year', var_name='Metric', value_name='Percentage')).mark_line(point=True).encode(
                x='Year:O',
                y=alt.Y('Percentage:Q', axis=alt.Axis(format='%')),
                color='Metric:N',
                tooltip=['Year:O', alt.Tooltip('Percentage:Q', format='.1%'), 'Metric:N']
            ).properties(
                title='Margin Analysis'
            )
            
            st.altair_chart(margin_chart, use_container_width=True)
    
    # SWOT Analysis
    st.subheader("SWOT Analysis")
    swot = generate_swot_analysis(scenario_id)
    
    if swot and isinstance(swot, dict):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Strengths**")
            for strength in swot.get("strengths", []):
                st.write(f"✅ {strength}")
            
            st.write("**Weaknesses**")
            for weakness in swot.get("weaknesses", []):
                st.write(f"⚠️ {weakness}")
        
        with col2:
            st.write("**Opportunities**")
            for opportunity in swot.get("opportunities", []):
                st.write(f"🚀 {opportunity}")
            
            st.write("**Threats**")
            for threat in swot.get("threats", []):
                st.write(f"🔴 {threat}")
    
    # Equipment and Product tables
    st.subheader("Asset Inventory")
    if isinstance(equipment_df, pd.DataFrame) and not equipment_df.empty:
        st.dataframe(equipment_df[['name', 'cost', 'useful_life', 'maintenance_cost_pct', 'financing_type']], hide_index=True)
    else:
        st.info("No equipment added yet")
    
    st.subheader("Product Portfolio")
    if isinstance(get_products(scenario_id), pd.DataFrame) and not get_products(scenario_id).empty:
        display_df = get_products(scenario_id)[['name', 'unit_price', 'initial_units', 'growth_rate']].copy()
        
        # Format the columns
        display_df['unit_price'] = display_df['unit_price'].apply(lambda x: f"${x:,.2f}")
        display_df['initial_units'] = display_df['initial_units'].apply(lambda x: f"{x:,.0f}")
        display_df['growth_rate'] = display_df['growth_rate'].apply(lambda x: f"{x:.1%}")
        
        # Rename columns for display
        display_df.columns = ['Product', 'Unit Price', 'Initial Units', 'Annual Growth']
        
        st.dataframe(display_df, hide_index=True)
    else:
        st.info("No products added yet")

def render_scenario_management():
    st.title("Scenario Management")
    
    print("\n=== Starting render_scenario_management() ===")
    
    # Get all scenarios
    scenarios_df = get_scenarios()
    print(f"Found {len(scenarios_df)} existing scenarios")
    
    # Show existing scenarios
    if not scenarios_df.empty:
        st.subheader("Existing Scenarios")
        
        # Sort scenarios by created_at in descending order (newest first)
        scenarios_df = scenarios_df.sort_values('created_at', ascending=False)
        
        # Create a copy of the dataframe for display
        display_columns = ['id', 'name', 'description', 'annual_revenue_growth', 'annual_cost_growth', 'is_base_case', 'created_at']
        display_df = scenarios_df[display_columns].copy()
        
        # Format the data
        display_df['annual_revenue_growth'] = display_df['annual_revenue_growth'].astype(float).apply(lambda x: f"{x:.1%}")
        display_df['annual_cost_growth'] = display_df['annual_cost_growth'].astype(float).apply(lambda x: f"{x:.1%}")
        display_df['is_base_case'] = display_df['is_base_case'].astype(bool).apply(lambda x: "✓" if x else "")
        
        # Add an "Active" column
        active_id = st.session_state.get('active_scenario_id')
        display_df['Active'] = display_df['id'].apply(lambda x: "★" if x == active_id else "")
        
        # Reorder columns to show Active first
        display_df = display_df[['Active', 'id', 'name', 'description', 'annual_revenue_growth', 'annual_cost_growth', 'is_base_case', 'created_at']]
        
        # Rename columns for better display
        display_df.columns = ['Active', 'ID', 'Name', 'Description', 'Revenue Growth', 'Cost Growth', 'Base Case', 'Created']
        
        # Show the dataframe without index
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Create scenario selection with proper state management
        st.subheader("Scenario Selection")
        scenario_options = [(row['id'], row['name']) for _, row in scenarios_df.iterrows()]
        
        # Get current selection
        current_id = st.session_state.get('active_scenario_id')
        current_index = next((i for i, (id, _) in enumerate(scenario_options) if id == current_id), 0)
        
        # Create selection box with ID and name
        selected_option = st.selectbox(
            "Select active scenario",
            options=[f"{id} - {name}" for id, name in scenario_options],
            index=current_index,
            key="scenario_management_selector"
        )
        
        # Extract ID from selection
        selected_id = int(selected_option.split(" - ")[0])
        
        # Only update if selection has changed
        if selected_id != current_id:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Set as Active"):
                    st.session_state.active_scenario_id = selected_id
                    st.rerun()
            
            # Option to clone scenario
            with col2:
                if st.button("Clone Selected"):
                    st.session_state.clone_scenario = selected_id
                    st.info("Fill in the form below to clone the scenario")
    
    # Create new scenario form
    st.subheader("Create New Scenario")
    
    # If cloning, pre-fill with selected scenario data
    prefill_data = {}
    if 'clone_scenario' in st.session_state and st.session_state.clone_scenario:
        clone_id = st.session_state.clone_scenario
        print(f"Cloning scenario ID: {clone_id}")
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
        
        # Submit button
        submitted = st.form_submit_button("Create Scenario")
        
        if submitted and name:
            print(f"\n=== Creating new scenario: {name} ===")
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
            
            try:
            # Create the scenario
                print("Creating scenario with data:", scenario_data)
                scenario_id = create_scenario(scenario_data)
                print(f"Created scenario with ID: {scenario_id}")
            
            # Clone equipment and products if needed
                if 'clone_scenario' in st.session_state and st.session_state.clone_scenario:
                    clone_id = st.session_state.clone_scenario
                    print(f"Cloning data from scenario {clone_id} to new scenario {scenario_id}")
                    
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
                                'financing_type': eq['financing_type'],
                                'is_leased': eq['is_leased'],
                                'lease_type': eq['lease_type'],
                                'lease_rate': eq['lease_rate'],
                                'debt_ratio': eq['debt_ratio'],
                                'interest_rate': eq['interest_rate']
                        }
                        print(f"Adding equipment: {equipment_data['name']}")
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
                    print(f"Adding product: {product_data['name']}")
                    add_product(product_data)
                
                # Clear clone flag
                print("Clearing clone flag")
                st.session_state.clone_scenario = None
            
                # Set as active scenario and navigate to dashboard
                print(f"Setting new scenario {scenario_id} as active")
                st.session_state.active_scenario_id = scenario_id
                st.session_state.section = "Dashboard"  # Set navigation to dashboard
                st.rerun()
                
            except Exception as e:
                print(f"Error creating scenario: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                st.error(f"Error creating scenario: {str(e)}")
                return

def get_standard_equipment():
    """Return a list of standard equipment with their default parameters"""
    return [
        {
            'name': 'Lapping Machine - 24" Diameter',
            'description': 'Precision flat lapping and polishing system with digital control',
            'purchase_price': 85000,
            'installation_cost': 8500,
            'useful_life': 15,
            'maintenance_cost': 4250,
            'power_consumption': 5.5,
            'availability_pct': 95
        },
        {
            'name': 'Large Ultrasonic Cleaning Tank',
            'description': 'Industrial ultrasonic cleaner with filtration and heating',
            'purchase_price': 45000,
            'installation_cost': 4500,
            'useful_life': 12,
            'maintenance_cost': 2250,
            'power_consumption': 3.8,
            'availability_pct': 98
        },
        {
            'name': 'Vacuum Furnace - 48" Chamber',
            'description': 'High-temperature vacuum furnace with programmable controls',
            'purchase_price': 275000,
            'installation_cost': 27500,
            'useful_life': 20,
            'maintenance_cost': 13750,
            'power_consumption': 45,
            'availability_pct': 92
        },
        {
            'name': 'Laser Welder with Safety Enclosure',
            'description': 'Fiber laser welding system with class 1 safety enclosure',
            'purchase_price': 195000,
            'installation_cost': 19500,
            'useful_life': 10,
            'maintenance_cost': 9750,
            'power_consumption': 12,
            'availability_pct': 95
        },
        {
            'name': 'Sinker EDM',
            'description': 'CNC sinker EDM with automatic tool changer',
            'purchase_price': 165000,
            'installation_cost': 16500,
            'useful_life': 15,
            'maintenance_cost': 8250,
            'power_consumption': 15,
            'availability_pct': 94
        },
        {
            'name': 'Wire EDM',
            'description': 'CNC wire EDM with auto-threading',
            'purchase_price': 185000,
            'installation_cost': 18500,
            'useful_life': 15,
            'maintenance_cost': 9250,
            'power_consumption': 12,
            'availability_pct': 93
        },
        {
            'name': 'Surface Grinder - 24x48',
            'description': 'Precision surface grinder with digital readout',
            'purchase_price': 95000,
            'installation_cost': 9500,
            'useful_life': 20,
            'maintenance_cost': 4750,
            'power_consumption': 7.5,
            'availability_pct': 96
        },
        {
            'name': 'CNC Mill - 4 Axis',
            'description': 'Vertical machining center with 4th axis rotary',
            'purchase_price': 225000,
            'installation_cost': 22500,
            'useful_life': 12,
            'maintenance_cost': 11250,
            'power_consumption': 20,
            'availability_pct': 94
        },
        {
            'name': 'CNC Lathe with Live Tooling',
            'description': 'CNC turning center with live tooling capability',
            'purchase_price': 245000,
            'installation_cost': 24500,
            'useful_life': 12,
            'maintenance_cost': 12250,
            'power_consumption': 18,
            'availability_pct': 94
        },
        {
            'name': 'CMM Machine',
            'description': 'Coordinate measuring machine with scanning probe',
            'purchase_price': 175000,
            'installation_cost': 17500,
            'useful_life': 15,
            'maintenance_cost': 8750,
            'power_consumption': 3.5,
            'availability_pct': 97
        },
        {
            'name': 'Heat Treatment Oven',
            'description': 'Programmable heat treatment oven with data logging',
            'purchase_price': 85000,
            'installation_cost': 8500,
            'useful_life': 18,
            'maintenance_cost': 4250,
            'power_consumption': 25,
            'availability_pct': 96
        },
        {
            'name': 'Optical Comparator',
            'description': 'Digital optical comparator with DRO and software',
            'purchase_price': 45000,
            'installation_cost': 4500,
            'useful_life': 15,
            'maintenance_cost': 2250,
            'power_consumption': 1.5,
            'availability_pct': 98
        },
        {
            'name': 'Surface Finish Tester',
            'description': 'Portable surface roughness tester with printer',
            'purchase_price': 15000,
            'installation_cost': 1500,
            'useful_life': 8,
            'maintenance_cost': 750,
            'power_consumption': 0.2,
            'availability_pct': 99
        },
        {
            'name': 'Blast Cabinet',
            'description': 'Industrial blast cabinet with dust collection',
            'purchase_price': 12000,
            'installation_cost': 1200,
            'useful_life': 15,
            'maintenance_cost': 600,
            'power_consumption': 2.5,
            'availability_pct': 98
        },
        {
            'name': 'Tool Presetter',
            'description': 'CNC tool presetting and measuring system',
            'purchase_price': 65000,
            'installation_cost': 6500,
            'useful_life': 12,
            'maintenance_cost': 3250,
            'power_consumption': 1.2,
            'availability_pct': 99
        }
    ]

def get_standard_products():
    """Return a list of standard products with their default parameters"""
    return [
        {
            'name': 'Precision Ground Shafts',
            'description': 'Custom ground shafts with tight tolerances',
            'unit_price': 750,
            'target_margin': 0.35,
            'growth_rate': 0.05,
            'introduction_year': 0
        },
        {
            'name': 'EDM Cut Components',
            'description': 'Complex geometry parts made with EDM',
            'unit_price': 1200,
            'target_margin': 0.40,
            'growth_rate': 0.06,
            'introduction_year': 0
        },
        {
            'name': 'Lapped Seal Faces',
            'description': 'Ultra-flat seal faces for industrial applications',
            'unit_price': 850,
            'target_margin': 0.38,
            'growth_rate': 0.04,
            'introduction_year': 0
        },
        {
            'name': 'Precision Machined Housings',
            'description': 'Multi-axis machined housings with tight tolerances',
            'unit_price': 2500,
            'target_margin': 0.32,
            'growth_rate': 0.05,
            'introduction_year': 0
        },
        {
            'name': 'Custom Vacuum Components',
            'description': 'Specialty vacuum chamber components',
            'unit_price': 3500,
            'target_margin': 0.35,
            'growth_rate': 0.07,
            'introduction_year': 0
        },
        {
            'name': 'Laser Welded Assemblies',
            'description': 'Precision assemblies with laser welded joints',
            'unit_price': 1800,
            'target_margin': 0.33,
            'growth_rate': 0.06,
            'introduction_year': 0
        },
        {
            'name': 'Heat Treated Tool Components',
            'description': 'Precision tools with specific heat treatment',
            'unit_price': 950,
            'target_margin': 0.36,
            'growth_rate': 0.04,
            'introduction_year': 0
        },
        {
            'name': 'Ground Gauge Blocks',
            'description': 'High-precision gauge blocks with certification',
            'unit_price': 450,
            'target_margin': 0.42,
            'growth_rate': 0.03,
            'introduction_year': 0
        },
        {
            'name': 'Custom Mold Components',
            'description': 'Precision components for injection molds',
            'unit_price': 4500,
            'target_margin': 0.38,
            'growth_rate': 0.06,
            'introduction_year': 0
        },
        {
            'name': 'Aerospace Brackets',
            'description': 'Precision brackets for aerospace applications',
            'unit_price': 1650,
            'target_margin': 0.35,
            'growth_rate': 0.08,
            'introduction_year': 0
        },
        {
            'name': 'Medical Device Components',
            'description': 'High-precision parts for medical devices',
            'unit_price': 2800,
            'target_margin': 0.40,
            'growth_rate': 0.09,
            'introduction_year': 0
        },
        {
            'name': 'Optical Mount Components',
            'description': 'Precision components for optical systems',
            'unit_price': 1950,
            'target_margin': 0.37,
            'growth_rate': 0.06,
            'introduction_year': 0
        }
    ]

def render_equipment_management(active_scenario_id):
    st.title("Equipment Management")
    st.write(f"Managing equipment for scenario: {get_scenario(active_scenario_id)['name']}")
    
    # Get existing equipment
    equipment_df = get_equipment(active_scenario_id)
    print(f"Found {len(equipment_df)} equipment items")
    
    if isinstance(equipment_df, pd.DataFrame) and not equipment_df.empty:
        st.subheader("Current Equipment")
        
        # Create display DataFrame with formatted columns
        display_df = equipment_df[['name', 'cost', 'useful_life', 'max_capacity', 'availability_pct', 'purchase_year', 'financing_type', 'lease_type', 'lease_rate']].copy()
        
        # Format currency columns
        display_df['cost'] = display_df['cost'].apply(lambda x: f"${x:,.2f}")
        display_df['lease_rate'] = display_df['lease_rate'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        display_df['availability_pct'] = display_df['availability_pct'].apply(lambda x: f"{x:.1%}")
        
        # Rename columns for display
        display_df.columns = ['Equipment', 'Purchase Price', 'Useful Life (Years)', 'Max Capacity', 'Availability', 'Purchase Year', 'Financing', 'Lease Type', 'Lease Rate']
        
        st.dataframe(display_df, hide_index=True)
        
        # Add radio button for selection
        selected_equipment = st.radio(
            "Select equipment to modify:",
            equipment_df['name'].tolist(),
            key="equipment_selector"
        )
        
        # Show delete and clone buttons for selected equipment
        col1, col2 = st.columns([1, 11])
        with col1:
            if st.button("🗑️ Delete", key="delete_equipment"):
                equipment_id = equipment_df[equipment_df['name'] == selected_equipment].iloc[0]['id']
                delete_equipment(equipment_id)
                st.rerun()
        with col2:
            if st.button("📋 Clone", key="clone_equipment"):
                equipment_to_clone = equipment_df[equipment_df['name'] == selected_equipment].iloc[0]
                
                # Find the next available number for the clone
                base_name = selected_equipment.rstrip('0123456789').rstrip()
                existing_names = equipment_df['name'].tolist()
                counter = 1
                while f"{base_name}{counter}" in existing_names:
                    counter += 1
                
                # Create clone data with correct column names
                clone_data = {
                    'scenario_id': active_scenario_id,
                    'name': f"{base_name}{counter}",
                    'cost': equipment_to_clone['cost'],
                    'useful_life': equipment_to_clone['useful_life'],
                    'max_capacity': equipment_to_clone['max_capacity'],
                    'maintenance_cost_pct': equipment_to_clone['maintenance_cost_pct'],
                    'availability_pct': equipment_to_clone['availability_pct'],
                    'purchase_year': equipment_to_clone['purchase_year'],
                    'financing_type': equipment_to_clone['financing_type'],
                    'is_leased': equipment_to_clone['is_leased'],
                    'lease_type': equipment_to_clone['lease_type'],
                    'lease_rate': equipment_to_clone['lease_rate'],
                    'debt_ratio': equipment_to_clone['debt_ratio'],
                    'interest_rate': equipment_to_clone['interest_rate']
                }
                
                add_equipment(clone_data)
                st.success(f"Created clone: {clone_data['name']}")
                st.rerun()
    else:
        st.info("No equipment added yet")
    
    # Add new equipment form
    st.subheader("Add New Equipment")
    
    # Get standard equipment list and add "Create New" option
    standard_equipment = get_standard_equipment()
    equipment_options = ["Create New"] + [eq['name'] for eq in standard_equipment]
    
    selected_option = st.selectbox(
        "Choose equipment type or create new",
        options=equipment_options,
        help="Select from standard equipment types or create a custom one"
    )
    
    # Financing section
    st.markdown("##### Financing Details")
    financing_type = st.selectbox(
        "1. Select Financing Type",
        ["Cash Purchase", "Lease", "Debt Financing"],
        key="financing_type"
    )
  
    with st.form("add_equipment_form"):
        col1, col2 = st.columns(2)
        
        # Pre-fill values if standard equipment selected
        default_values = {}
        if selected_option != "Create New":
            default_values = next(eq for eq in standard_equipment if eq['name'] == selected_option)
        
        with col1:
            name = st.text_input("Equipment Name", value=default_values.get('name', '') if selected_option != "Create New" else "")
            cost = st.number_input("Purchase Price ($)", min_value=0.0, step=1000.0, value=float(default_values.get('cost', 0)))
            useful_life = st.number_input("Useful Life (years)", min_value=1, step=1, value=int(default_values.get('useful_life', 1)))
            max_capacity = st.number_input("Maximum Capacity (hours/year)", min_value=0.0, step=100.0, value=float(default_values.get('max_capacity', 2080)))
            maintenance_cost_pct = st.number_input("Annual Maintenance (% of purchase price)", min_value=0.0, max_value=100.0, step=0.1, value=float(default_values.get('maintenance_cost_pct', 5)))
        
        with col2:
            availability_pct = st.number_input("Availability (%)", min_value=0.0, max_value=100.0, step=0.1, value=float(default_values.get('availability_pct', 90)))
            purchase_year = st.number_input("Purchase Year", min_value=2024, step=1, value=int(default_values.get('purchase_year', 2024)))
            
            # Show relevant financing fields based on selection
            is_leased = financing_type == "Lease"
            if is_leased:
                lease_type = st.selectbox(
                    "2. Lease Type", 
                    ["Operating Lease", "Capital Lease", "$1 Buyout Lease"],
                    key="lease_type"
                )
                lease_rate = st.number_input("3. Monthly Lease Rate ($)", min_value=0.0, step=100.0)
                debt_ratio = 0.0
                interest_rate = 0.0
            elif financing_type == "Debt Financing":
                lease_type = None
                lease_rate = 0.0
                debt_ratio = st.number_input("2. Debt Ratio (%)", min_value=0.0, max_value=100.0, step=1.0, value=80.0) / 100
                interest_rate = st.number_input("3. Annual Interest Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=5.0) / 100
            else:  # Cash Purchase
                lease_type = None
                lease_rate = 0.0
                debt_ratio = 0.0
                interest_rate = 0.0
        
        if st.form_submit_button("Add Equipment"):
            print(f"\n=== Adding equipment with name: '{name}' ===")
            if name and len(name.strip()) > 0:
                equipment_data = {
                    'scenario_id': active_scenario_id,
                        'name': name.strip(),
                    'cost': cost,
                    'useful_life': useful_life,
                    'max_capacity': max_capacity,
                    'maintenance_cost_pct': maintenance_cost_pct,
                    'availability_pct': availability_pct,
                    'purchase_year': purchase_year,
                        'financing_type': financing_type,
                    'is_leased': 1 if is_leased else 0,
                        'lease_type': lease_type,
                        'lease_rate': lease_rate,
                        'debt_ratio': debt_ratio,
                        'interest_rate': interest_rate
                }
                print(f"Equipment data: {equipment_data}")
                add_equipment(equipment_data)
                st.success(f"Added equipment: {name}")
                st.rerun()
            else:
                st.error("Equipment name is required")

def render_product_management(active_scenario_id):
    st.title("Product Management")
    st.write(f"Managing products for scenario: {get_scenario(active_scenario_id)['name']}")
    
    # Get existing products
    products_df = get_products(active_scenario_id)
    print(f"Found {len(products_df)} products")
    
    if isinstance(products_df, pd.DataFrame) and not products_df.empty:
        st.subheader("Current Products")
        
        # Create display DataFrame with formatted columns
        display_df = products_df[['name', 'initial_units', 'unit_price', 'growth_rate', 'introduction_year']].copy()
        
        # Format columns
        display_df['unit_price'] = display_df['unit_price'].apply(lambda x: f"${x:,.2f}")
        display_df['initial_units'] = display_df['initial_units'].apply(lambda x: f"{x:,.0f}")
        display_df['growth_rate'] = display_df['growth_rate'].apply(lambda x: f"{x:.1%}")
        
        # Rename columns for display
        display_df.columns = ['Product', 'Initial Units', 'Unit Price', 'Growth Rate', 'Introduction Year']
        
        st.dataframe(display_df, hide_index=True)
        
        # Add radio button for selection
        selected_product = st.radio(
            "Select product to modify:",
            products_df['name'].tolist(),
            key="product_selector"
        )
        
        # Show delete and clone buttons for selected product
        col1, col2 = st.columns([1, 11])
        with col1:
            if st.button("🗑️ Delete", key="delete_product"):
                product_id = products_df[products_df['name'] == selected_product].iloc[0]['id']
                delete_product(product_id)
                st.rerun()
    
    # Add new product form
    st.subheader("Add New Product")
    
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name").strip()
            initial_units = st.number_input("Initial Annual Units", min_value=0, step=100, value=1000)
            unit_price = st.number_input("Unit Price ($)", min_value=0.0, step=1.0, value=100.0)
            
        with col2:
            growth_rate = st.number_input("Annual Growth Rate (%)", min_value=-100.0, max_value=1000.0, value=10.0) / 100
            introduction_year = st.number_input("Introduction Year", min_value=2024, step=1, value=2024)
            market_size = st.number_input("Total Market Size (units)", min_value=0, step=1000, value=10000)
            price_elasticity = st.number_input("Price Elasticity", min_value=-10.0, max_value=0.0, value=-1.0)
        
        if st.form_submit_button("Add Product"):
            if name:
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
                print(f"Adding product with data: {product_data}")
                add_product(product_data)
                st.success(f"Added product: {name}")
                st.rerun()
            else:
                st.error("Product name is required")

def render_financial_analysis(active_scenario_id):
    """Render the financial analysis page"""
    st.header("Financial Analysis")
    
    # Get scenario data
    scenario = get_scenario(active_scenario_id)
    if scenario is None:
        st.error("Could not load scenario data")
        return
    
    st.write(f"Analyzing scenario: {scenario['name']}")
    
    # Get financial projections
    financial_projections = get_financial_projections(active_scenario_id)
    
    # Add Calculate button
    if st.button("🔄 Calculate", help="Recalculate financial projections"):
        calculate_financial_projections(active_scenario_id)
        st.rerun()
    
    if not isinstance(financial_projections, pd.DataFrame) or financial_projections.empty:
        st.warning("No financial projections available. Click Calculate to generate projections.")
        return
    
    # Get products and equipment data
    products_df = get_products(active_scenario_id)
    equipment_df = get_equipment(active_scenario_id)
    
    # Create detailed product economics table
    st.subheader("Product Economics")
    product_details = []
    for _, product in products_df.iterrows():
        economics = calculate_unit_economics(product['id'])
        if 'error' not in economics:
            product_details.append({
                'Product': economics['product_name'],
                'Unit Price': f"${economics['unit_price']:,.2f}",
                'Unit Cost': f"${economics['unit_cost']:,.2f}",
                'Equipment Cost': f"${economics['equipment_costs']:,.2f}",
                'Materials Cost': f"${economics['materials_costs']:,.2f}",
                'Labor Cost': f"${economics['labor_costs']:,.2f}",
                'Gross Profit/Unit': f"${economics['gross_profit_per_unit']:,.2f}",
                'Gross Margin': f"{economics['gross_margin_pct']:.1f}%"
            })
    
    if product_details:
        product_economics_df = pd.DataFrame(product_details)
        st.dataframe(product_economics_df, hide_index=True)
        
        # Download button for product economics
        csv = product_economics_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Product Economics",
            data=csv,
            file_name="product_economics.csv",
            mime="text/csv",
            help="Download detailed product economics data"
        )
    
    # Create equipment utilization table
    st.subheader("Equipment Utilization")
    latest_year = financial_projections['year'].max()
    utilization = calculate_equipment_utilization(active_scenario_id, latest_year)
    
    if 'equipment_utilization' in utilization:
        equipment_details = []
        for eq in utilization['equipment_utilization']:
            equipment_details.append({
                'Equipment': eq['equipment_name'],
                'Available Hours': f"{eq['max_capacity']:,.0f}",
                'Used Hours': f"{eq['used_capacity']:,.0f}",
                'Utilization': f"{eq['utilization_pct']:.1f}%"
            })
        
        if equipment_details:
            equipment_util_df = pd.DataFrame(equipment_details)
            st.dataframe(equipment_util_df, hide_index=True)
            
            # Download button for equipment utilization
            csv = equipment_util_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Equipment Utilization",
                data=csv,
                file_name="equipment_utilization.csv",
                mime="text/csv",
                help="Download detailed equipment utilization data"
            )
    
    # Financial Statements
    st.subheader("Financial Statements")
    
    # Format currency columns
    currency_cols = ['revenue', 'cogs', 'gross_profit', 'operating_expenses', 
                    'ebitda', 'depreciation', 'ebit', 'interest', 'tax', 'net_income']
    
    display_df = financial_projections.copy()
    
    # Format currency columns
    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "$0")
    
    # Format percentage columns
    if 'capacity_utilization' in display_df.columns:
        display_df['capacity_utilization'] = display_df['capacity_utilization'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%")
    
    # Display the table
    st.dataframe(display_df.drop(['id', 'scenario_id'], axis=1, errors='ignore'), hide_index=True)
    
    # Download button for financial statements
    csv = financial_projections.to_csv(index=False)
    st.download_button(
        label="📥 Download Financial Statements",
        data=csv,
        file_name="financial_statements.csv",
        mime="text/csv",
        help="Download detailed financial statements"
    )
    
    # Profitability Metrics
    st.subheader("Profitability Metrics")
    metrics_df = pd.DataFrame({
        'Year': financial_projections['year'],
        'Revenue': financial_projections['revenue'].apply(lambda x: f"${x:,.0f}"),
        'Gross Margin': (financial_projections['gross_profit'] / financial_projections['revenue'] * 100).apply(lambda x: f"{x:.1f}%"),
        'EBITDA Margin': (financial_projections['ebitda'] / financial_projections['revenue'] * 100).apply(lambda x: f"{x:.1f}%"),
        'Net Margin': (financial_projections['net_income'] / financial_projections['revenue'] * 100).apply(lambda x: f"{x:.1f}%"),
        'Capacity Utilization': financial_projections['capacity_utilization'].apply(lambda x: f"{x:.1f}%")
    })
    
    st.dataframe(metrics_df, hide_index=True)
    
    # Download button for profitability metrics
    csv = metrics_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Profitability Metrics",
        data=csv,
        file_name="profitability_metrics.csv",
        mime="text/csv",
        help="Download detailed profitability metrics"
    )

def render_capacity_planning(active_scenario_id):
    st.title("Capacity Planning")
    
    # First check if we have a scenario ID
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get available scenarios to validate the ID
    scenarios_df = get_scenarios()
    if active_scenario_id not in scenarios_df['id'].values:
        st.error("The selected scenario no longer exists. Please select a different scenario.")
        # Reset the active scenario
        if not scenarios_df.empty:
            st.session_state.active_scenario_id = scenarios_df.iloc[0]['id']
        else:
            st.session_state.active_scenario_id = None
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    if scenario is None:
        st.error("Could not load the scenario data. Please try again or select a different scenario.")
        return
    
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

def main():
    """Main application entry point"""
    # Initialize database if needed
    success, message = init_database()
    if not success:
        st.error(f"Failed to initialize database: {message}")
        return
    
    # Render sidebar and get active scenario
    active_scenario_id = render_sidebar()
    
    # Render main content based on current page
    if st.session_state.current_page == "Dashboard":
        render_dashboard(active_scenario_id)
    elif st.session_state.current_page == "Financial Analysis":
        render_financial_analysis(active_scenario_id)
    elif st.session_state.current_page == "Capacity Planning":
        render_capacity_planning(active_scenario_id)
    elif st.session_state.current_page == "Model Configuration":
        config_page = st.session_state.get('config_page', 'Scenarios')
        if config_page == "Scenarios":
            render_scenario_management()
        elif config_page == "Equipment":
            render_equipment_management(active_scenario_id)
        elif config_page == "Products":
            render_product_management(active_scenario_id)
        else:
            st.error(f"Invalid configuration page: {config_page}")
            st.session_state.config_page = "Scenarios"
            st.rerun()
    else:
        st.error("Invalid page selection")

if __name__ == "__main__":
    main()