# Manufacturing Model System Overview

## 1. Core Models

### Scenario Model
- **Purpose**: Central model for business scenarios
- **Key Relationships**:
  - Has many: Equipment, Products, Financial Projections
  - Has parameters for: Sales, GA Expenses
- **Used By**: Assumptions, GA, and Optimization services

### Equipment Model
- **Purpose**: Manufacturing equipment and capacity
- **Key Relationships**:
  - Belongs to: Scenario
  - Has many: Cost Drivers
- **Used By**: Financial and Optimization services

### Product Model
- **Purpose**: Products and their specifications
- **Key Relationships**:
  - Belongs to: Scenario
  - Has many: Cost Drivers
- **Key Attributes**: Unit price, production rate, quality rate

### Cost Driver Model
- **Purpose**: Manufacturing costs and labor requirements
- **Key Relationships**:
  - Belongs to: Product and Equipment
- **Key Metrics**: Cost per hour, materials cost, labor costs

## 2. Financial Models

### Financial Projection
- **Purpose**: Financial forecasting and analysis
- **Key Metrics**: Revenue, COGS, EBITDA, cash flows
- **Relationships**: Belongs to Scenario

### GA Expense
- **Purpose**: General & Administrative expenses
- **Key Metrics**: Amount, headcount, % of revenue
- **Relationships**: Belongs to Scenario

## 3. Sales Models

### Sales Parameter & Forecast
- **Purpose**: Sales planning and forecasting
- **Components**:
  - Sales Parameters: Configuration
  - Sales Forecast: Yearly projections
  - Product Forecast: Product-specific predictions

## 4. Service Architecture

### Core Services
1. **Financial Service**
   - Uses: Equipment model
   - Dependencies: Advanced Finance, Equipment, Sales

2. **Optimization Service**
   - Uses: Equipment, Scenario models
   - Dependencies: Equipment, Financial

3. **GA Service**
   - Uses: Scenario model
   - Dependencies: Equipment, Sales, Financial

### Support Services
1. **Visualization Service**
   - Purpose: Data visualization
   - Used by: Monte Carlo, Scenario services

2. **Template Service**
   - Purpose: Report templates
   - Uses: Spreadsheet service

3. **Monte Carlo Service**
   - Purpose: Simulation
   - Dependencies: Visualization, Financial

## ⚠️ Known Issues

### Database Mismatches
- Several tables missing from database:
  - scenarios
  - products
  - cost_drivers
  - financial_projections
  - sales_parameters
  - sales_forecasts
  - product_forecasts
  - ga_expenses
  - industry_standards
  - scenario_assumptions

### Circular Dependencies
1. Equipment Service ↔ Financial Service
2. Sales Service ↔ Financial Service

## System Paths
- Database: `/data/manufacturing_model.db`
- Models: `/src/models`
- Services: `/src/services`