{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Manufacturing Expansion Model - Data Models\n",
    "\n",
    "This notebook establishes the core data models and database structure for the manufacturing expansion financial model.\n",
    "\n",
    "## Tasks:\n",
    "1. Set up SQLAlchemy models\n",
    "2. Create SQLite database\n",
    "3. Implement data migration from JSON\n",
    "4. Create basic CRUD operations"
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
    "# Install required packages\n",
    "!pip install sqlalchemy pandas numpy matplotlib seaborn"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import json\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, Text, JSON\n",
    "from sqlalchemy.ext.declarative import declarative_base\n",
    "from sqlalchemy.orm import sessionmaker, relationship\n",
    "from datetime import datetime\n",
    "from pathlib import Path\n",
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
    "## Create Project Directory Structure"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create project directory structure\n",
    "base_dir = Path('./manufacturing_model')\n",
    "os.makedirs(base_dir, exist_ok=True)\n",
    "\n",
    "# Create subdirectories\n",
    "for subdir in ['models', 'services', 'utils', 'data', 'notebooks']:\n",
    "    os.makedirs(base_dir / subdir, exist_ok=True)\n",
    "    # Create __init__.py in each package directory\n",
    "    if subdir != 'data' and subdir != 'notebooks':\n",
    "        with open(base_dir / subdir / '__init__.py', 'w') as f:\n",
    "            f.write('# Package initialization')\n",
    "\n",
    "print(\"Directory structure created.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Database Setup"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Setup SQLAlchemy Database Connection\n",
    "db_path = base_dir / 'data' / 'manufacturing_model.db'\n",
    "engine = create_engine(f'sqlite:///{db_path}')\n",
    "Base = declarative_base()\n",
    "\n",
    "# Create session\n",
    "Session = sessionmaker(bind=engine)\n",
    "session = Session()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Define SQLAlchemy Models"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Define Scenario model for managing different business scenarios\n",
    "class Scenario(Base):\n",
    "    __tablename__ = 'scenarios'\n",
    "    \n",
    "    id = Column(Integer, primary_key=True)\n",
    "    name = Column(String(100), nullable=False)\n",
    "    description = Column(Text)\n",
    "    created_at = Column(String, default=datetime.now().isoformat())\n",
    "    is_base_case = Column(Boolean, default=False)\n",
    "    \n",
    "    # Financial assumptions\n",
    "    initial_revenue = Column(Float, default=0.0)\n",
    "    initial_costs = Column(Float, default=0.0)\n",
    "    annual_revenue_growth = Column(Float, default=0.15)  # 15% default\n",
    "    annual_cost_growth = Column(Float, default=0.10)     # 10% default\n",
    "    debt_ratio = Column(Float, default=0.50)             # 50% default\n",
    "    interest_rate = Column(Float, default=0.10)          # 10% default\n",
    "    tax_rate = Column(Float, default=0.25)               # 25% default\n",
    "    \n",
    "    # Relationships\n",
    "    equipment = relationship(\"Equipment\", back_populates=\"scenario\")\n",
    "    products = relationship(\"Product\", back_populates=\"scenario\")\n",
    "    financials = relationship(\"FinancialProjection\", back_populates=\"scenario\")\n",
    "    \n",
    "    def __repr__(self):\n",
    "        return f\"<Scenario(name='{self.name}', is_base_case={self.is_base_case})>\"\n",
    "\n",
    "\n",
    "# Define Equipment model\n",
    "class Equipment(Base):\n",
    "    __tablename__ = 'equipment'\n",
    "    \n",
    "    id = Column(Integer, primary_key=True)\n",
    "    scenario_id = Column(Integer, ForeignKey('scenarios.id'))\n",
    "    name = Column(String(100), nullable=False)\n",
    "    cost = Column(Float, nullable=False)\n",
    "    useful_life = Column(Integer, nullable=False)  # in years\n",
    "    max_capacity = Column(Float, nullable=False)   # units per year\n",
    "    maintenance_cost_pct = Column(Float, default=0.05)  # 5% of cost per year\n",
    "    availability_pct = Column(Float, default=0.95)      # 95% uptime\n",
    "    purchase_year = Column(Integer, default=2025)\n",
    "    is_leased = Column(Boolean, default=False)\n",
    "    lease_rate = Column(Float, default=0.0)              # annual lease rate\n",
    "    \n",
    "    # Relationships\n",
    "    scenario = relationship(\"Scenario\", back_populates=\"equipment\")\n",
    "    cost_drivers = relationship(\"CostDriver\", back_populates=\"equipment\")\n",
    "    \n",
    "    def __repr__(self):\n",
    "        return f\"<Equipment(name='{self.name}', cost=${self.cost:,.2f})>\"\n",
    "\n",
    "\n",
    "# Define Product model\n",
    "class Product(Base):\n",
    "    __tablename__ = 'products'\n",
    "    \n",
    "    id = Column(Integer, primary_key=True)\n",
    "    scenario_id = Column(Integer, ForeignKey('scenarios.id'))\n",
    "    name = Column(String(100), nullable=False)\n",
    "    initial_units = Column(Float, nullable=False)\n",
    "    unit_price = Column(Float, nullable=False)\n",
    "    growth_rate = Column(Float, nullable=False)  # annual growth rate\n",
    "    introduction_year = Column(Integer, default=2025)\n",
    "    market_size = Column(Float)  # total addressable market\n",
    "    price_elasticity = Column(Float, default=-1.0)  # price elasticity of demand\n",
    "    \n",
    "    # Relationships\n",
    "    scenario = relationship(\"Scenario\", back_populates=\"products\")\n",
    "    cost_drivers = relationship(\"CostDriver\", back_populates=\"product\")\n",
    "    \n",
    "    def __repr__(self):\n",
    "        return f\"<Product(name='{self.name}', unit_price=${self.unit_price:,.2f})>\"\n",
    "\n",
    "\n",
    "# Define CostDriver model for each product-equipment combination\n",
    "class CostDriver(Base):\n",
    "    __tablename__ = 'cost_drivers'\n",
    "    \n",
    "    id = Column(Integer, primary_key=True)\n",
    "    product_id = Column(Integer, ForeignKey('products.id'))\n",
    "    equipment_id = Column(Integer, ForeignKey('equipment.id'))\n",
    "    cost_per_hour = Column(Float, nullable=False)\n",
    "    hours_per_unit = Column(Float, nullable=False)\n",
    "    \n",
    "    # Additional costs\n",
    "    materials_cost_per_unit = Column(Float, default=0.0)\n",
    "    machinist_labor_cost_per_hour = Column(Float, default=30.0)\n",
    "    machinist_hours_per_unit = Column(Float, default=2.0)\n",
    "    design_labor_cost_per_hour = Column(Float, default=40.0)\n",
    "    design_hours_per_unit = Column(Float, default=1.0)\n",
    "    supervision_cost_per_hour = Column(Float, default=20.0)\n",
    "    supervision_hours_per_unit = Column(Float, default=0.5)\n",
    "    \n",
    "    # Relationships\n",
    "    product = relationship(\"Product\", back_populates=\"cost_drivers\")\n",
    "    equipment = relationship(\"Equipment\", back_populates=\"cost_drivers\")\n",
    "    \n",
    "    def __repr__(self):\n",
    "        return f\"<CostDriver(product_id={self.product_id}, equipment_id={self.equipment_id})>\"\n",
    "\n",
    "\n",
    "# Define FinancialProjection model to store calculated financials\n",
    "class FinancialProjection(Base):\n",
    "    __tablename__ = 'financial_projections'\n",
    "    \n",
    "    id = Column(Integer, primary_key=True)\n",
    "    scenario_id = Column(Integer, ForeignKey('scenarios.id'))\n",
    "    year = Column(Integer, nullable=False)\n",
    "    \n",
    "    # Income Statement\n",
    "    revenue = Column(Float, default=0.0)\n",
    "    cogs = Column(Float, default=0.0)\n",
    "    gross_profit = Column(Float, default=0.0)\n",
    "    operating_expenses = Column(Float, default=0.0)\n",
    "    ebitda = Column(Float, default=0.0)\n",
    "    depreciation = Column(Float, default=0.0)\n",
    "    ebit = Column(Float, default=0.0)\n",
    "    interest = Column(Float, default=0.0)\n",
    "    tax = Column(Float, default=0.0)\n",
    "    net_income = Column(Float, default=0.0)\n",
    "    \n",
    "    # Balance Sheet\n",
    "    cash = Column(Float, default=0.0)\n",
    "    accounts_receivable = Column(Float, default=0.0)\n",
    "    inventory = Column(Float, default=0.0)\n",
    "    fixed_assets = Column(Float, default=0.0)\n",
    "    accumulated_depreciation = Column(Float, default=0.0)\n",
    "    total_assets = Column(Float, default=0.0)\n",
    "    accounts_payable = Column(Float, default=0.0)\n",
    "    short_term_debt = Column(Float, default=0.0)\n",
    "    long_term_debt = Column(Float, default=0.0)\n",
    "    equity = Column(Float, default=0.0)\n",
    "    total_liabilities_and_equity = Column(Float, default=0.0)\n",
    "    \n",
    "    # Cash Flow\n",
    "    operating_cash_flow = Column(Float, default=0.0)\n",
    "    investing_cash_flow = Column(Float, default=0.0)\n",
    "    financing_cash_flow = Column(Float, default=0.0)\n",
    "    net_cash_flow = Column(Float, default=0.0)\n",
    "    \n",
    "    # Production metrics\n",
    "    total_production = Column(Float, default=0.0)\n",
    "    capacity_utilization = Column(Float, default=0.0)  # percentage\n",
    "    \n",
    "    # Store product-specific projections\n",
    "    product_details = Column(JSON)  # Store as JSON for flexibility\n",
    "    \n",
    "    # Relationships\n",
    "    scenario = relationship(\"Scenario\", back_populates=\"financials\")\n",
    "    \n",
    "    def __repr__(self):\n",
    "        return f\"<FinancialProjection(scenario_id={self.scenario_id}, year={self.year})>\""
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Create the Database and Tables"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create all tables in the database\n",
    "Base.metadata.create_all(engine)\n",
    "\n",
    "print(f\"Database created at: {db_path}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Data Migration Functions\n",
    "\n",
    "Create functions to migrate data from existing JSON file to the new database structure."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def load_json_data(file_path=\"financial_model_data.json\"):\n",
    "    \"\"\"Load data from JSON file\"\"\"\n",
    "    try:\n",
    "        with open(file_path, \"r\") as f:\n",
    "            return json.load(f)\n",
    "    except FileNotFoundError:\n",
    "        print(f\"File {file_path} not found. Returning empty data structure.\")\n",
    "        return {\"equipment\": [], \"products\": [], \"cost_drivers\": {}}\n",
    "\n",
    "def migrate_data_to_database(json_data, session):\n",
    "    \"\"\"Migrate data from JSON to SQLite database\"\"\"\n",
    "    # Create a base scenario\n",
    "    base_scenario = Scenario(\n",
    "        name=\"Base Case\",\n",
    "        description=\"Initial scenario migrated from JSON data\",\n",
    "        is_base_case=True\n",
    "    )\n",
    "    session.add(base_scenario)\n",
    "    session.commit()\n",
    "    \n",
    "    # Add equipment\n",
    "    equipment_map = {}  # To map old equipment names to new IDs\n",
    "    for eq_data in json_data.get(\"equipment\", []):\n",
    "        equipment = Equipment(\n",
    "            scenario_id=base_scenario.id,\n",
    "            name=eq_data.get(\"Name\", \"Unknown Equipment\"),\n",
    "            cost=eq_data.get(\"Cost\", 0.0),\n",
    "            useful_life=eq_data.get(\"Useful Life\", 10),\n",
    "            max_capacity=eq_data.get(\"Max Capacity\", 1000)\n",
    "        )\n",
    "        session.add(equipment)\n",
    "        session.commit()\n",
    "        equipment_map[equipment.name] = equipment.id\n",
    "    \n",
    "    # Add products\n",
    "    product_map = {}  # To map old product names to new IDs\n",
    "    for prod_data in json_data.get(\"products\", []):\n",
    "        product = Product(\n",
    "            scenario_id=base_scenario.id,\n",
    "            name=prod_data.get(\"Name\", \"Unknown Product\"),\n",
    "            initial_units=prod_data.get(\"Initial Units\", 0),\n",
    "            unit_price=prod_data.get(\"Unit Price\", 0.0),\n",
    "            growth_rate=prod_data.get(\"Growth Rate\", 0.1)\n",
    "        )\n",
    "        session.add(product)\n",
    "        session.commit()\n",
    "        product_map[product.name] = product.id\n",
    "    \n",
    "    # Add cost drivers\n",
    "    for product_name, drivers in json_data.get(\"cost_drivers\", {}).items():\n",
    "        if product_name not in product_map:\n",
    "            continue\n",
    "            \n",
    "        product_id = product_map[product_name]\n",
    "        \n",
    "        # Add equipment costs\n",
    "        for eq_name, eq_costs in drivers.get(\"Equipment Costs\", {}).items():\n",
    "            if eq_name not in equipment_map:\n",
    "                continue\n",
    "                \n",
    "            equipment_id = equipment_map[eq_name]\n",
    "            cost_driver = CostDriver(\n",
    "                product_id=product_id,\n",
    "                equipment_id=equipment_id,\n",
    "                cost_per_hour=eq_costs.get(\"Cost Per Hour\", 0.0),\n",
    "                hours_per_unit=eq_costs.get(\"Hours Per Unit\", 0.0)\n",
    "            )\n",
    "            \n",
    "            # Add labor costs\n",
    "            if \"Machinist Labor\" in drivers:\n",
    "                cost_driver.machinist_labor_cost_per_hour = drivers[\"Machinist Labor\"].get(\"Cost Per Hour\", 30.0)\n",
    "                cost_driver.machinist_hours_per_unit = drivers[\"Machinist Labor\"].get(\"Hours Per Unit\", 2.0)\n",
    "                \n",
    "            if \"Design Labor\" in drivers:\n",
    "                cost_driver.design_labor_cost_per_hour = drivers[\"Design Labor\"].get(\"Cost Per Hour\", 40.0)\n",
    "                cost_driver.design_hours_per_unit = drivers[\"Design Labor\"].get(\"Hours Per Unit\", 1.0)\n",
    "                \n",
    "            if \"Supervision\" in drivers:\n",
    "                cost_driver.supervision_cost_per_hour = drivers[\"Supervision\"].get(\"Cost Per Hour\", 20.0)\n",
    "                cost_driver.supervision_hours_per_unit = drivers[\"Supervision\"].get(\"Hours Per Unit\", 0.5)\n",
    "                \n",
    "            session.add(cost_driver)\n",
    "    \n",
    "    session.commit()\n",
    "    return base_scenario.id"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Migrate Existing Data"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Load existing JSON data and migrate to database\n",
    "json_data = load_json_data()\n",
    "base_scenario_id = migrate_data_to_database(json_data, session)\n",
    "\n",
    "print(f\"Data migrated to base scenario with ID: {base_scenario_id}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Create Basic CRUD Functions"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def create_equipment(session, scenario_id, name, cost, useful_life, max_capacity, **kwargs):\n",
    "    \"\"\"Create a new equipment record\"\"\"\n",
    "    equipment = Equipment(\n",
    "        scenario_id=scenario_id,\n",
    "        name=name,\n",
    "        cost=cost,\n",
    "        useful_life=useful_life,\n",
    "        max_capacity=max_capacity,\n",
    "        **kwargs\n",
    "    )\n",
    "    session.add(equipment)\n",
    "    session.commit()\n",
    "    return equipment\n",
    "\n",
    "def create_product(session, scenario_id, name, initial_units, unit_price, growth_rate, **kwargs):\n",
    "    \"\"\"Create a new product record\"\"\"\n",
    "    product = Product(\n",
    "        scenario_id=scenario_id,\n",
    "        name=name,\n",
    "        initial_units=initial_units,\n",
    "        unit_price=unit_price,\n",
    "        growth_rate=growth_rate,\n",
    "        **kwargs\n",
    "    )\n",
    "    session.add(product)\n",
    "    session.commit()\n",
    "    return product\n",
    "\n",
    "def create_cost_driver(session, product_id, equipment_id, cost_per_hour, hours_per_unit, **kwargs):\n",
    "    \"\"\"Create a new cost driver record\"\"\"\n",
    "    cost_driver = CostDriver(\n",
    "        product_id=product_id,\n",
    "        equipment_id=equipment_id,\n",
    "        cost_per_hour=cost_per_hour,\n",
    "        hours_per_unit=hours_per_unit,\n",
    "        **kwargs\n",
    "    )\n",
    "    session.add(cost_driver)\n",
    "    session.commit()\n",
    "    return cost_driver\n",
    "\n",
    "def create_scenario(session, name, description, **kwargs):\n",
    "    \"\"\"Create a new scenario\"\"\"\n",
    "    scenario = Scenario(\n",
    "        name=name,\n",
    "        description=description,\n",
    "        **kwargs\n",
    "    )\n",
    "    session.add(scenario)\n",
    "    session.commit()\n",
    "    return scenario\n",
    "\n",
   def clone_scenario(session, scenario_id, new_name, new_description):
    """Clone an existing scenario with all its equipment, products, and cost drivers"""
    # Get the original scenario
    original = session.query(Scenario).filter(Scenario.id == scenario_id).first()
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
    session.add(new_scenario)
    session.commit()
    
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
            lease_rate=old_equipment.lease_rate
        )
        session.add(new_equipment)
        session.commit()
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
        session.add(new_product)
        session.commit()
        product_map[old_product.id] = new_product.id
    
    # Clone cost drivers
    for old_cost_driver in session.query(CostDriver).filter(
        CostDriver.product_id.in_(product_map.keys()),
        CostDriver.equipment_id.in_(equipment_map.keys())
    ).all():
        new_cost_driver = CostDriver(
            product_id=product_map[old_cost_driver.product_id],
            equipment_id=equipment_map[old_cost_driver.equipment_id],
            cost_per_hour=old_cost_driver.cost_per_hour,
            hours_per_unit=old_cost_driver.hours_per_unit,
            materials_cost_per_unit=old_cost_driver.materials_cost_per_unit,
            machinist_labor_cost_per_hour=old_cost_driver.machinist_labor_cost_per_hour,
            machinist_hours_per_unit=old_cost_driver.machinist_hours_per_unit,
            design_labor_cost_per_hour=old_cost_driver.design_labor_cost_per_hour,
            design_hours_per_unit=old_cost_driver.design_hours_per_unit,
            supervision_cost_per_hour=old_cost_driver.supervision_cost_per_hour,
            supervision_hours_per_unit=old_cost_driver.supervision_hours_per_unit
        )
        session.add(new_cost_driver)
    
    session.commit()
    return new_scenario
    
     "def get_scenario_by_id(session, scenario_id):\n",
    "    \"\"\"Get a scenario by ID\"\"\"\n",
    "    return session.query(Scenario).filter(Scenario.id == scenario_id).first()\n",
    "\n",
    "def get_equipment_by_scenario(session, scenario_id):\n",
    "    \"\"\"Get all equipment for a scenario\"\"\"\n",
    "    return session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()\n",
    "\n",
    "def get_products_by_scenario(session, scenario_id):\n",
    "    \"\"\"Get all products for a scenario\"\"\"\n",
    "    return session.query(Product).filter(Product.scenario_id == scenario_id).all()\n",
    "\n",
    "def get_cost_drivers_by_product(session, product_id):\n",
    "    \"\"\"Get all cost drivers for a product\"\"\"\n",
    "    return session.query(CostDriver).filter(CostDriver.product_id == product_id).all()\n",
    "\n",
    "def delete_scenario(session, scenario_id):\n",
    "    \"\"\"Delete a scenario and all related records\"\"\"\n",
    "    # Delete financial projections\n",
    "    session.query(FinancialProjection).