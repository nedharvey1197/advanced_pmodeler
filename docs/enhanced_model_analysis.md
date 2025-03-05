# Enhanced Model Analysis Report
==================================================

## Model Analysis
--------------------

### industry_models

Classes:
- IndustryStandard
- ScenarioAssumption

Dependencies:
- Base

### base_models

Classes:
- ServiceMixin

Dependencies:

### scenario_models

Classes:
- Scenario

Dependencies:
- Base

### equipment_models

Classes:
- Equipment

Dependencies:
- Base

### ga_models

Classes:
- GAExpense

Dependencies:
- Base

### product_models

Classes:
- Product
- CostDriver

Dependencies:
- Base

### sales_models

Classes:
- SalesParameter
- SalesForecast
- ProductForecast

Dependencies:
- Base

### financial_projections_model

Classes:
- FinancialProjection

Dependencies:
- Base

## Service Analysis
--------------------

### advanced_fin_Services

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

### sales_service

Model Dependencies:
- Scenario
- ServiceMixin
- Product
- FinancialProjection
- get_session

Service Dependencies:

### spreadsheet_services

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

### visualization_services

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:
- calculate_key_financial_metrics
- optimize_equipment_purchases
- identify_capacity_constraints
- model_shift_operations

### monty_carlo_services

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

### scenario_service

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

### template_service

Model Dependencies:
- Scenario
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:
- spreadsheetservice

### assumptions_service

Model Dependencies:
- Scenario

Service Dependencies:

### ga_services

Model Dependencies:
- Scenario

Service Dependencies:

### equipment_service

Model Dependencies:
- Scenario
- ServiceMixin
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

### optimization_services

Model Dependencies:
- Scenario

Service Dependencies:

### financial_service

Model Dependencies:
- Scenario
- ServiceMixin
- Equipment
- Product
- FinancialProjection
- get_session
- CostDriver

Service Dependencies:

## Database Analysis
--------------------

## Circular Dependencies
--------------------
- sales_service
- sales_service -> financial_service
- equipment_service
- financial_service