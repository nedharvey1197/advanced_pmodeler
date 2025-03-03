# Manufacturing Expansion Model - Project Structure

## Notebook Structure
1. `01_Data_Models.ipynb` - Core data models and database setup
2. `02_Financial_Core.ipynb` - Financial calculation engines
3. `03_Equipment_Utilization.ipynb` - Equipment capacity and utilization modeling
4. `04_Scenario_Analysis.ipynb` - Basic scenario comparison functionality

## Supporting Modules
- `models/` - Data models for SQLAlchemy
  - `__init__.py`
  - `equipment.py`
  - `product.py` 
  - `cost_driver.py`
  - `scenario.py`
- `services/` - Business logic services
  - `__init__.py`
  - `financial_service.py`
  - `equipment_service.py`
  - `optimization_service.py`
- `utils/` - Helper functions
  - `__init__.py`
  - `db_utils.py`
  - `financial_utils.py`
  - `visualization_utils.py`

## Database Schema
- `Equipment` - Equipment details and specifications
- `Product` - Product definitions and growth projections
- `CostDriver` - Cost factors for each product-equipment combination
- `Scenario` - Saved scenarios for comparison
- `FinancialProjection` - Calculated financial projections

## Getting Started Steps
1. Create the project directory structure
2. Set up SQLite database with SQLAlchemy models
3. Migrate data from the existing JSON model
4. Implement core financial calculation functions
5. Create equipment utilization modeling
6. Build basic scenario management
