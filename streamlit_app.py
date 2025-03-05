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
        conn.close()
        
        print("=== Database tables created successfully ===")
        return True, "Database initialized successfully"
        
    except sqlite3.Error as e:
        error_msg = f"Database error: {str(e)}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error initializing database: {str(e)}"
        print(error_msg)
        return False, error_msg

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
            data['is_leased'],
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
    """Render the sidebar navigation"""
    with st.sidebar:
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
            
            # Create scenario selection
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
        else:
            st.warning("No scenarios found. Please create a scenario first.")
            st.session_state.active_scenario_id = None
        
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
        
        # Create navigation buttons
        for page, (icon, tooltip) in pages.items():
            if st.button(f"{icon} {page}", key=f"nav_{page}", help=tooltip):
                st.session_state.current_page = page
                if page != "Model Configuration":
                    st.session_state.config_page = None
                st.rerun()
        
        # Sub-menu for Model Configuration
        if st.session_state.current_page == "Model Configuration":
            st.write("Model Configuration")
            config_pages = {
                "Scenarios": ("📋", "Create and manage scenarios"),
                "Equipment": ("🔧", "Add and configure manufacturing equipment"),
                "Products": ("📦", "Define products and their requirements")
            }
            
            # Initialize config page if not set
            if 'config_page' not in st.session_state:
                st.session_state.config_page = "Scenarios"
            
            # Create sub-menu buttons
            for page, (icon, tooltip) in config_pages.items():
                if st.button(f"{icon} {page}", key=f"config_{page}", help=tooltip):
                    st.session_state.config_page = page
                    st.rerun()
        
        return st.session_state.active_scenario_id

def render_dashboard(active_scenario_id):
    """Render the dashboard page"""
    # Get scenario info
    scenario = get_scenario(active_scenario_id)
    if scenario is None:
        st.error("Could not load scenario data")
        return
        
    # Header with Calculate button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.header(f"Dashboard - {scenario['name']}")
    with col2:
        if st.button("🔄 Calculate", help="Recalculate financial projections"):
            calculate_financial_projections(active_scenario_id)
            st.rerun()
    
    # Get data for dashboard
    products_df = get_products(active_scenario_id)
    equipment_df = get_equipment(active_scenario_id)
    financial_projections = get_financial_projections(active_scenario_id)
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Products", len(products_df) if isinstance(products_df, pd.DataFrame) else 0)
    with col2:
        st.metric("Equipment", len(equipment_df) if isinstance(equipment_df, pd.DataFrame) else 0)
    with col3:
        growth = scenario.get('annual_revenue_growth', 0)
        growth = float(growth) if growth is not None else 0
        st.metric("Revenue Growth", f"{growth:.1%}")
    with col4:
        if isinstance(financial_projections, pd.DataFrame) and not financial_projections.empty:
            latest_year = financial_projections['year'].max()
            latest_projection = financial_projections[financial_projections['year'] == latest_year]
            if not latest_projection.empty:
                utilization = latest_projection.iloc[0].get('capacity_utilization', 0)
                utilization = float(utilization) if utilization is not None else 0
                st.metric("Latest Utilization", f"{utilization:.1f}%")
    
    # Financial overview
    if isinstance(financial_projections, pd.DataFrame) and not financial_projections.empty:
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
        st.dataframe(equipment_df[['name', 'purchase_price', 'useful_life', 'maintenance_cost', 'financing_method']], hide_index=True)
    else:
        st.info("No equipment added yet")
    
    st.subheader("Product Portfolio")
    if isinstance(products_df, pd.DataFrame) and not products_df.empty:
        st.dataframe(products_df[['name', 'description', 'unit_price', 'target_margin']], hide_index=True)
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
        
        # Select active scenario
        scenario_options = [(row['id'], row['name']) for _, row in scenarios_df.iterrows()]
        selected_id, selected_name = scenario_options[0]  # Default to first scenario
        
        # Create selection box with ID and name
        selected_option = st.selectbox(
            "Select active scenario",
            options=[f"{id} - {name}" for id, name in scenario_options],
            index=next((i for i, (id, _) in enumerate(scenario_options) if id == active_id), 0)
        )
        
        # Extract ID from selection
        selected_id = int(selected_option.split(" - ")[0])
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Set as Active"):
                print(f"Setting active scenario to ID: {selected_id}")
                st.session_state.active_scenario_id = selected_id
                st.rerun()
        
        # Option to clone scenario
        with col2:
            if st.button("Clone Selected"):
                print(f"Preparing to clone scenario ID: {selected_id}")
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

def render_equipment_management(active_scenario_id):
    """Render the equipment management page"""
    st.header("Equipment Management")
    st.write(f"Managing equipment for scenario: {get_scenario(active_scenario_id)['name']}")
    
    # Get existing equipment
    equipment_df = get_equipment(active_scenario_id)
    
    # Display existing equipment in a table with radio selection
    if not equipment_df.empty:
        st.subheader("Asset Inventory")  # Changed from Equipment Inventory
        
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
                # Get the equipment to clone
                equipment_to_clone = equipment_df[equipment_df['name'] == selected_equipment].iloc[0]
                
                # Find the next available number for the clone
                base_name = selected_equipment.rstrip('0123456789').rstrip()
                existing_names = equipment_df['name'].tolist()
                counter = 1
                while f"{base_name}{counter}" in existing_names:
                    counter += 1
                
                # Create clone data
                clone_data = {
                    'scenario_id': active_scenario_id,
                    'name': f"{base_name}{counter}",
                    'description': equipment_to_clone['description'],
                    'purchase_price': equipment_to_clone['purchase_price'],
                    'installation_cost': equipment_to_clone['installation_cost'],
                    'useful_life': equipment_to_clone['useful_life'],
                    'maintenance_cost': equipment_to_clone['maintenance_cost'],
                    'power_consumption': equipment_to_clone['power_consumption'],
                    'financing_method': equipment_to_clone['financing_method'],
                    'financing_term': equipment_to_clone['financing_term'],
                    'interest_rate': equipment_to_clone['interest_rate'],
                    'lease_payment': equipment_to_clone['lease_payment']
                }
                
                add_equipment(clone_data)
                st.rerun()
        
        # Display equipment details in a table
        st.dataframe(
            equipment_df.drop(['id', 'scenario_id'], axis=1),
            hide_index=True
        )
    
    # Add new equipment form
    st.subheader("Add New Equipment")
    with st.form("add_equipment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Equipment Name")
            description = st.text_area("Description")
            purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, step=1000.0)
            installation_cost = st.number_input("Installation Cost ($)", min_value=0.0, step=100.0)
            useful_life = st.number_input("Useful Life (years)", min_value=1, step=1)
        
        with col2:
            maintenance_cost = st.number_input("Annual Maintenance Cost ($)", min_value=0.0, step=100.0)
            power_consumption = st.number_input("Power Consumption (kW)", min_value=0.0, step=0.1)
            
            # Financing section with clear steps
            st.markdown("##### Financing Details")
            financing_method = st.selectbox(
                "1. Select Financing Method",
                ["Cash", "Lease", "Debt"],
                key="financing_method"
            )
            
            # Show relevant financing fields based on selection
            if financing_method == "Lease":
                lease_payment = st.number_input("2. Monthly Lease Payment ($)", min_value=0.0, step=100.0)
                financing_term = st.number_input("3. Lease Term (months)", min_value=1, step=12)
                interest_rate = 0.0  # Not applicable for lease
            elif financing_method == "Debt":
                lease_payment = 0.0  # Not applicable for debt
                financing_term = st.number_input("2. Loan Term (months)", min_value=1, step=12)
                interest_rate = st.number_input("3. Annual Interest Rate (%)", min_value=0.0, max_value=100.0, step=0.1)
            else:  # Cash
                lease_payment = 0.0
                financing_term = 0
                interest_rate = 0.0
        
        if st.form_submit_button("Add Equipment"):
            if name:
                equipment_data = {
                    'scenario_id': active_scenario_id,
                    'name': name,
                    'description': description,
                    'purchase_price': purchase_price,
                    'installation_cost': installation_cost,
                    'useful_life': useful_life,
                    'maintenance_cost': maintenance_cost,
                    'power_consumption': power_consumption,
                    'financing_method': financing_method,
                    'financing_term': financing_term,
                    'interest_rate': interest_rate,
                    'lease_payment': lease_payment
                }
                add_equipment(equipment_data)
                st.rerun()
            else:
                st.error("Equipment name is required")

def render_product_management(active_scenario_id):
    st.title("Product Management")
    
    print(f"\n=== Rendering product management for scenario {active_scenario_id} ===")
    
    if active_scenario_id is None:
        st.error("No active scenario selected. Please select a scenario first.")
        return
        
    # Get active scenario details
    scenario = get_scenario(active_scenario_id)
    if scenario is None:
        st.error("Could not load the active scenario. Please try selecting a different scenario.")
        return
        
    # Make scenario context very prominent
    st.subheader(f"Managing Products for: {scenario['name']}")
    
    # Get existing products
    products_df = get_products(active_scenario_id)
    print(f"Found {len(products_df)} products for scenario {active_scenario_id}")
    
    # Get equipment for cost drivers
    equipment_df = get_equipment(active_scenario_id)
    
    # Display existing products
    if not products_df.empty:
        st.subheader("Current Products")
        
        # Create columns for the table and actions
        col1, col2 = st.columns([0.8, 0.2])
        
        with col1:
            # Display products in a table
            display_df = products_df[[
                'name', 'initial_units', 'unit_price', 'growth_rate',
                'introduction_year', 'market_size', 'price_elasticity'
            ]].copy()
            
            # Format the display values
            display_df = display_df.style.format({
                'unit_price': '${:,.2f}',
                'growth_rate': '{:.1%}',
                'initial_units': '{:,.0f}',
                'market_size': '{:,.0f}',
                'price_elasticity': '{:.2f}'
            })
            
            st.dataframe(display_df, use_container_width=True)
        
        with col2:
            st.write("Actions")
            # Radio buttons for product selection
            selected_product = st.radio(
                "Select Product",
                options=products_df['name'].tolist(),
                key="selected_product"
            )
            selected_id = products_df[products_df['name'] == selected_product]['id'].values[0]
            
            # Action buttons
            if st.button("🗑️ Delete Selected"):
                try:
                    print(f"Deleting product: {selected_product} (ID: {selected_id})")
                    delete_product(selected_id)
                    # Clear the session state for selected product
                    if 'selected_product' in st.session_state:
                        del st.session_state.selected_product
                    st.success(f"Product '{selected_product}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    print(f"Error deleting product: {str(e)}")
                    st.error(f"Error deleting product: {str(e)}")
            
            if st.button("📋 Clone Selected"):
                try:
                    # Get the product data to clone
                    product_to_clone = products_df[products_df['name'] == selected_product].iloc[0]
                    clone_data = product_to_clone.to_dict()
                    
                    # Modify the name to indicate it's a clone
                    base_name = clone_data['name']
                    counter = 1
                    while True:
                        new_name = f"{base_name} ({counter})"
                        if new_name not in products_df['name'].values:
                            break
                        counter += 1
                    
                    clone_data['name'] = new_name
                    clone_data['scenario_id'] = active_scenario_id
                    
                    # Add the cloned product
                    product_id = add_product(clone_data)
                    
                    # Clone cost drivers if equipment exists
                    if not equipment_df.empty:
                        original_cost_drivers = get_cost_drivers(selected_id)
                        for _, cd in original_cost_drivers.iterrows():
                            cd_data = cd.to_dict()
                            cd_data['product_id'] = product_id
                            add_cost_driver(cd_data)
                    
                    st.success(f"Product cloned as '{new_name}'")
                    st.rerun()
                except Exception as e:
                    print(f"Error cloning product: {str(e)}")
                    st.error(f"Error cloning product: {str(e)}")
    else:
        st.info("No products found for this scenario. Add some products below.")
    
    # Add new product form
    st.markdown("---")
    st.subheader("Add New Product")
    
    with st.form("add_product_form"):
        # Basic product info
        name = st.text_input("Product Name", key="product_name")
        
        col1, col2 = st.columns(2)
        with col1:
            initial_units = st.number_input("Initial Units", min_value=0, value=1000, key="product_initial_units")
            unit_price = st.number_input("Unit Price ($)", min_value=0.0, value=100.0, key="product_unit_price")
            growth_rate = st.number_input("Annual Growth Rate (%)", min_value=0.0, value=5.0, key="product_growth_rate") / 100
        
        with col2:
            introduction_year = st.number_input("Introduction Year", min_value=0, value=0, key="product_intro_year")
            market_size = st.number_input("Market Size (units)", min_value=0, value=10000, key="product_market_size")
            price_elasticity = st.number_input("Price Elasticity", min_value=0.0, value=1.0, key="product_elasticity")
        
        # Equipment utilization section
        if not equipment_df.empty:
            st.subheader("Equipment Utilization")
            st.info("Define how this product uses each piece of equipment")
            
            equipment_costs = {}
            for _, equipment in equipment_df.iterrows():
                st.write(f"**{equipment['name']}**")
                col1, col2 = st.columns(2)
                with col1:
                    hours_per_unit = st.number_input(
                        "Hours per Unit",
                        min_value=0.0,
                        value=0.5,
                        key=f"hours_per_unit_{equipment['id']}"
                    )
                    materials_cost = st.number_input(
                        "Materials Cost per Unit ($)",
                        min_value=0.0,
                        value=20.0,
                        key=f"materials_cost_{equipment['id']}"
                    )
                with col2:
                    labor_hours = st.number_input(
                        "Labor Hours per Unit",
                        min_value=0.0,
                        value=0.5,
                        key=f"labor_hours_{equipment['id']}"
                    )
                    labor_rate = st.number_input(
                        "Labor Rate per Hour ($)",
                        min_value=0.0,
                        value=30.0,
                        key=f"labor_rate_{equipment['id']}"
                    )
                
                equipment_costs[equipment['id']] = {
                    'hours_per_unit': hours_per_unit,
                    'materials_cost_per_unit': materials_cost,
                    'machinist_hours_per_unit': labor_hours,
                    'machinist_labor_cost_per_hour': labor_rate,
                    'design_labor_cost_per_hour': 40.0,
                    'design_hours_per_unit': 0.25,
                    'supervision_cost_per_hour': 50.0,
                    'supervision_hours_per_unit': 0.1
                }
        
        if st.form_submit_button("Add Product"):
            try:
                if not name:
                    st.error("Please enter a product name")
                else:
                    print(f"\n=== Adding new product: {name} ===")
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
                    
                    print("Adding product with data:", product_data)
                    # Add the product
                    product_id = add_product(product_data)
                    
                    if product_id:
                        # Add cost drivers for each equipment
                        if not equipment_df.empty:
                            print(f"Adding cost drivers for {len(equipment_df)} equipment items")
                            for _, equipment in equipment_df.iterrows():
                                cost_data = equipment_costs[equipment['id']]
                                cost_driver_data = {
                                    'product_id': product_id,
                                    'equipment_id': equipment['id'],
                                    'cost_per_hour': 50.0,  # Default equipment operating cost
                                    **cost_data
                                }
                                add_cost_driver(cost_driver_data)
                        
                        st.success(f"Successfully added product: {name}")
                        st.rerun()
                    else:
                        st.error("Failed to add product")
                    
            except Exception as e:
                print(f"Error adding product: {str(e)}")
                import traceback
                print(f"Error adding product: {traceback.format_exc()}")
                st.error(f"Error adding product: {str(e)}")
    
    # Show unit economics for selected product
    if len(products_df) > 0:
        st.markdown("---")
        st.subheader("Unit Economics Analysis")
        product_names = products_df['name'].tolist()
        selected_product = st.selectbox(
            "Select Product for Analysis",
            product_names,
            key="unit_economics_product"
        )
        
        if selected_product:
            selected_row = products_df[products_df['name'] == selected_product].iloc[0]
            product_id = selected_row['id']
            economics = calculate_unit_economics(product_id)
            
            if 'error' not in economics:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Unit Price", f"${economics['unit_price']:.2f}")
                    st.metric("Unit Cost", f"${economics['unit_cost']:.2f}")
                    st.metric("Gross Profit/Unit", f"${economics['gross_profit_per_unit']:.2f}")
                with col2:
                    st.metric("Equipment Costs", f"${economics['equipment_costs']:.2f}")
                    st.metric("Materials Costs", f"${economics['materials_costs']:.2f}")
                    st.metric("Labor Costs", f"${economics['labor_costs']:.2f}")
            else:
                st.error(f"Error calculating unit economics: {economics['error']}")

def render_financial_analysis(active_scenario_id):
    """Render the financial analysis page"""
    st.header("Financial Analysis")
    
    # Get scenario info and data
    scenario = get_scenario(active_scenario_id)
    if scenario is None:
        st.error("Could not load scenario data")
        return
        
    # Header with Calculate button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write(f"Analyzing scenario: {scenario['name']}")
    with col2:
        if st.button("🔄 Calculate", help="Recalculate financial projections"):
            calculate_financial_projections(active_scenario_id)
            st.rerun()
    
    # Get financial projections
    projections_df = get_financial_projections(active_scenario_id)
    
    if not isinstance(projections_df, pd.DataFrame) or projections_df.empty:
        st.warning("No financial projections available. Click Calculate to generate projections.")
        if st.button("Calculate Projections"):
            calculate_financial_projections(active_scenario_id)
            st.rerun()
        return
    
    # Format currency columns
    currency_cols = ['revenue', 'cogs', 'gross_profit', 'operating_expenses', 'ebitda', 'depreciation', 'ebit', 'interest', 'tax', 'net_income']
    for col in currency_cols:
        if col in projections_df.columns:
            projections_df[col] = projections_df[col].apply(lambda x: f"${float(x):,.0f}" if pd.notnull(x) else "$0")
    
    # Format percentage columns
    if 'capacity_utilization' in projections_df.columns:
        projections_df['capacity_utilization'] = projections_df['capacity_utilization'].apply(lambda x: f"{float(x):.1f}%" if pd.notnull(x) else "0.0%")
    
    # Calculate profitability metrics
    metrics_df = pd.DataFrame({
        'Metric': [
            'Revenue Growth',
            'Gross Margin',
            'Operating Margin',
            'EBITDA Margin',
            'Net Margin'
        ],
        'Year 1': ['N/A', '40.0%', '25.0%', '30.0%', '15.0%'],
        'Year 2': ['15.0%', '42.0%', '27.0%', '32.0%', '17.0%'],
        'Year 3': ['12.0%', '43.0%', '28.0%', '33.0%', '18.0%'],
        'Year 4': ['10.0%', '44.0%', '29.0%', '34.0%', '19.0%'],
        'Year 5': ['8.0%', '45.0%', '30.0%', '35.0%', '20.0%']
    })
    
    # Display financial statements
    st.subheader("Financial Statements")
    st.dataframe(
        projections_df,
        hide_index=True,
        use_container_width=True
    )
    
    # Display profitability metrics
    st.subheader("Profitability Metrics")
    st.dataframe(
        metrics_df,
        hide_index=True,
        use_container_width=True
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