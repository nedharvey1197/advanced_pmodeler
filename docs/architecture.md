# Manufacturing Expansion Model

## Overview

This manufacturing expansion modeling tool is a comprehensive solution for manufacturers to analyze equipment utilization, capacity planning, financial projections, and scenario analysis. The tool helps decision-makers optimize equipment purchases, model shift operations, identify capacity constraints, and evaluate financial outcomes.

## Architecture

### Core Modules

1. **Equipment Service Module** (`equipment_service.py`)
   - Production capacity calculation
   - Equipment utilization analysis
   - Capacity constraint identification
   - Shift operations modeling
   - Equipment purchase optimization
   - Implemented as a class with wrapper functions

2. **Financial Service Module** (`financial_service.py`)
   - Unit economics calculation
   - Financial projections generation
   - Key financial metrics computation
   - Scenario cloning functionality
   - Comprehensive financial analysis

3. **Advanced Financial Modeling** (`advanced_financial_modeling.py`)
   - Detailed cash flow analysis
   - Working capital modeling
   - Progressive tax calculation
   - Risk adjustment factors
   - In-depth financial analysis

4. **Scenario Manager** (`scenario_manager.py`)
   - Scenario creation and management
   - Scenario comparison
   - Sensitivity analysis
   - Reporting and visualization
   - Integration with other modules

5. **Monte Carlo Simulation** (`monte_carlo_simulation.py`)
   - Probability distributions
   - Multi-variable simulation
   - Statistical analysis
   - Visualization of results
   - Risk assessment

6. **Optimization Service** (`optimization_service.py`)
   - Production mix optimization (placeholder)
   - Equipment leasing decisions (placeholder)
   - Staffing level optimization (placeholder)
   - Advanced optimization capabilities (placeholder)

7. **Visualization Utilities** (`visualization_utils.py`)
   - Equipment utilization visualization
   - Multi-year utilization heatmaps
   - Shift configuration comparison
   - Comprehensive PDF reports
   - Financial metrics visualization

### Data Models

- **Scenario**: Core entity representing a manufacturing scenario
- **Equipment**: Equipment specifications and capabilities
- **Product**: Product definitions and growth projections
- **CostDriver**: Cost factors for product-equipment combinations
- **FinancialProjection**: Financial calculations and projections

## Workflow

1. **Scenario Creation**
   - Define base scenario with financial assumptions
   - Add equipment and products
   - Configure cost drivers

2. **Production Capacity Analysis**
   - Calculate equipment capacity
   - Analyze utilization by product
   - Identify bottlenecks
   - Recommend capacity expansions

3. **Financial Projections**
   - Generate multi-year financial projections
   - Calculate key financial metrics
   - Analyze cash flow and working capital
   - Apply risk adjustments

4. **Scenario Analysis**
   - Clone scenarios for comparison
   - Run sensitivity analysis
   - Perform Monte Carlo simulations
   - Compare different scenarios

5. **Reporting**
   - Generate comprehensive reports
   - Create dashboards
   - Visualize key metrics
   - Export analysis results

## Usage Examples

```python
# Initialize scenario manager
scenario_manager = ScenarioManager()

# Create a base scenario
base_scenario = scenario_manager.create_scenario(
    name="Base Manufacturing Scenario",
    description="Initial manufacturing setup with current equipment",
    initial_revenue=1000000,
    initial_costs=750000,
    annual_revenue_growth=0.05,
    annual_cost_growth=0.03,
    debt_ratio=0.3,
    interest_rate=0.04,
    tax_rate=0.21,
    is_base_case=True
)

# Add equipment to the scenario
session = get_session()
new_equipment = Equipment(
    scenario_id=base_scenario.id,
    name="CNC Machine",
    cost=250000,
    useful_life=10,
    max_capacity=4000,  # hours per year
    maintenance_cost_pct=0.05,
    availability_pct=0.95,
    purchase_year=0,
    is_leased=False
)
session.add(new_equipment)
session.commit()

# Calculate financial projections
projections = calculate_financial_projections(base_scenario.id, projection_years=5)

# Identify capacity constraints
constraints = identify_capacity_constraints(base_scenario.id, start_year=0, end_year=5)

# Optimize equipment purchases
optimization = optimize_equipment_purchases(
    base_scenario.id,
    budget_constraint=1000000,
    start_year=0,
    optimization_years=5
)

# Generate comprehensive report
export_equipment_analysis_report(
    base_scenario.id,
    start_year=0,
    end_year=5,
    output_file="Base_Scenario_Analysis.pdf"
)

# Create a variation for comparison
growth_scenario = scenario_manager.clone_scenario(
    base_scenario.id,
    "High Growth Scenario",
    "Scenario with accelerated growth rates",
    annual_revenue_growth=0.08,
    annual_cost_growth=0.04
)

# Compare scenarios
comparison = scenario_manager.compare_scenarios(
    [base_scenario.id, growth_scenario.id],
    metric_type="income_statement"
)
```

## Dependencies

- Python 3.7+
- SQLAlchemy (data models and database access)
- Pandas (data manipulation and analysis)
- NumPy (numerical operations)
- Matplotlib (visualization)
- Seaborn (advanced visualization)

## Project Structure

```
manufacturing_model/
├── models/
│   ├── __init__.py
│   ├── equipment.py
│   ├── product.py
│   ├── cost_driver.py
│   ├── scenario.py
│   └── financial_projection.py
├── services/
│   ├── __init__.py
│   ├── equipment_service.py
│   ├── financial_service.py
│   ├── advanced_financial_modeling.py
│   └── optimization_service.py
├── utils/
│   ├── __init__.py
│   ├── db_utils.py
│   └── visualization_utils.py
└── notebooks/
    ├── 01_Data_Models.ipynb
    ├── 02_Financial_Core.ipynb
    ├── 03_Equipment_Utilization.ipynb
    └── 04_Scenario_Analysis.ipynb
```