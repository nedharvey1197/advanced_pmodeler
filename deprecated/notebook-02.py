{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Manufacturing Expansion Model - Financial Core\n",
    "\n",
    "This notebook implements the core financial calculation engine for the manufacturing expansion model.\n",
    "\n",
    "## Tasks:\n",
    "1. Implement unit economics calculations\n",
    "2. Create detailed COGS modeling\n",
    "3. Build proper income statement, balance sheet, and cash flow projections\n",
    "4. Implement working capital modeling\n",
    "5. Create accurate capital expenditure and depreciation schedules"
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
    "## Create Financial Service Module\n",
    "\n",
    "Let's first create our financial service module that will handle all financial calculations."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create the financial_service.py module\n",
    "with open(base_dir / 'services' / 'financial_service.py', 'w') as f:\n",
    "    f.write(\"\"\"\n",
    "# Financial calculation service\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "from datetime import datetime\n",
    "from ..models import (\n",
    "    Scenario, Equipment, Product, CostDriver, FinancialProjection,\n",
    "    get_session\n",
    ")\n",
    "\n",
    "def calculate_unit_economics(product_id):\n",
    "    \"\"\"Calculate the unit economics for a product\"\"\"\n",
    "    session = get_session()\n",
    "    product = session.query(Product).filter(Product.id == product_id).first()\n",
    "    \n",
    "    if not product:\n",
    "        return {\"error\": f\"Product with ID {product_id} not found\"}\n",
    "    \n",
    "    # Get all cost drivers for this product\n",
    "    cost_drivers = session.query(CostDriver).filter(CostDriver.product_id == product_id).all()\n",
    "    \n",
    "    # Initialize costs\n",
    "    equipment_costs = 0.0\n",
    "    materials_costs = 0.0\n",
    "    labor_costs = 0.0\n",
    "    \n",
    "    for cd in cost_drivers:\n",
    "        # Equipment costs\n",
    "        equipment_costs += cd.cost_per_hour * cd.hours_per_unit\n",
    "        \n",
    "        # Materials costs\n",
    "        materials_costs += cd.materials_cost_per_unit\n",
    "        \n",
    "        # Labor costs\n",
    "        labor_costs += (cd.machinist_labor_cost_per_hour * cd.machinist_hours_per_unit +\n",
    "                        cd.design_labor_cost_per_hour * cd.design_hours_per_unit +\n",
    "                        cd.supervision_cost_per_hour * cd.supervision_hours_per_unit)\n",
    "    \n",
    "    # Calculate unit cost\n",
    "    unit_cost = equipment_costs + materials_costs + labor_costs\n",
    "    \n",
    "    # Calculate gross profit per unit and margin\n",
    "    gross_profit_per_unit = product.unit_price - unit_cost\n",
    "    gross_margin_pct = (gross_profit_per_unit / product.unit_price) * 100 if product.unit_price > 0 else 0\n",
    "    \n",
    "    return {\n",
    "        \"product_name\": product.name,\n",
    "        \"unit_price\": product.unit_price,\n",
    "        \"unit_cost\": unit_cost,\n",
    "        \"equipment_costs\": equipment_costs,\n",
    "        \"materials_costs\": materials_costs,\n",
    "        \"labor_costs\": labor_costs,\n",
    "        \"gross_profit_per_unit\": gross_profit_per_unit,\n",
    "        \"gross_margin_pct\": gross_margin_pct\n",
    "    }\n",
    "\n",
    
    def calculate_equipment_utilization(scenario_id, year):
    """Calculate equipment utilization for a given scenario and year"""
    session = get_session()
    scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        return {"error": f"Scenario with ID {scenario_id} not found"}
    
    # Get all equipment for this scenario
    equipment_list = session.query(Equipment).filter(Equipment.scenario_id == scenario_id).all()
    
    # Get all products for this scenario
    products = session.query(Product).filter(Product.scenario_id == scenario_id).all()
    
    result = {
        "equipment_utilization": [],
        "total_capacity": 0,
        "used_capacity": 0
    }
    
    # Calculate production volume for each product in this year
    product_volumes = {}
    for product in products:
        # Calculate years since introduction
        years_since_intro = year - product.introduction_year
        
        # Skip if product hasn't been introduced yet
        if years_since_intro < 0:
            continue
            
        # Calculate production volume using compound growth
        volume = product.initial_units * ((1 + product.growth_rate) ** years_since_intro)
        product_volumes[product.id] = volume
    
    # Calculate utilization for each equipment
    for equipment in equipment_list:
        # Skip if equipment hasn't been purchased yet
        if equipment.purchase_year > year:
            continue
            
        total_hours_used = 0
        max_available_hours = equipment.max_capacity * equipment.availability_pct
        
        # Calculate hours used by each product on this equipment
        for product_id, volume in product_volumes.items():
            # Get cost driver for this product-equipment combination
            cost_driver = session.query(CostDriver).filter(
                CostDriver.product_id == product_id,
                CostDriver.equipment_id == equipment.id
            ).first()
            
            if cost_driver:
                hours_used = volume * cost_driver.hours_per_unit
                total_hours_used += hours_used
        
        # Calculate utilization percentage
        utilization_pct = (total_hours_used / max_available_hours) * 100 if max_available_hours > 0 else 0
        
        result["equipment_utilization"].append({
            "equipment_id": equipment.id,
            "equipment_name": equipment.name,
            "max_capacity": max_available_hours,
            "used_capacity": total_hours_used,
            "utilization_pct": utilization_pct
        })
        
        result["total_capacity"] += max_available_hours
        result["used_capacity"] += total_hours_used
    
    # Calculate overall utilization
    result["overall_utilization_pct"] = (result["used_capacity"] / result["total_capacity"]) * 100 if result["total_capacity"] > 0 else 0
    
    return result