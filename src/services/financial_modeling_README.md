# Financial Modeling Services

This module provides comprehensive financial modeling capabilities for manufacturing expansion analysis through two integrated services:

## 1. FinancialService (Basic Financial Operations)

The `FinancialService` class provides core financial modeling capabilities including:
- Unit economics calculation
- Basic equipment utilization tracking
- Standard financial projections
- Key financial metrics computation
- Basic lease and tax calculations

### Key Methods:
- `calculate_unit_economics(product_id)`: Calculate unit-level costs and margins
- `calculate_equipment_utilization(scenario_id, year)`: Basic equipment utilization analysis
- `calculate_financial_projections(scenario_id)`: Generate standard financial projections
- `calculate_key_financial_metrics(scenario_id)`: Compute basic financial metrics (ROI, payback, etc.)

## 2. AdvancedFinancialModeling (Advanced Analysis)

The `AdvancedFinancialModeling` class provides sophisticated financial analysis including:
- Advanced cash flow analysis with risk adjustments
- Working capital management
- Tax strategy optimization
- Risk factor modeling
- Comprehensive financial analysis

### Key Methods:
- `calculate_advanced_cash_flow(financial_projections)`: Sophisticated cash flow analysis
- `calculate_advanced_tax_strategy(financial_projections)`: Tax optimization analysis
- `generate_comprehensive_financial_analysis(financial_projections)`: Full financial analysis

## Integration and Usage

### Basic Usage
```python
# Basic financial operations
financial_service = FinancialService(session)
basic_metrics = financial_service.calculate_key_financial_metrics(scenario_id)
```

### Advanced Usage
```python
# Advanced financial analysis
advanced_analysis = financial_service.get_advanced_modeling()
comprehensive_analysis = advanced_analysis.generate_comprehensive_financial_analysis(projections)
```

### Comprehensive Analysis
```python
# Get both basic and advanced analysis
comprehensive_results = financial_service.get_comprehensive_analysis(scenario_id)
```

## Key Differences

### FinancialService
- Focuses on basic financial operations
- Handles core manufacturing metrics
- Provides standard projections
- Simpler tax and lease calculations
- No risk modeling

### AdvancedFinancialModeling
- Provides sophisticated financial analysis
- Includes risk factor modeling
- Handles working capital management
- Offers tax optimization
- Includes comprehensive cash flow analysis

## When to Use Each Service

### Use FinancialService When:
- Calculating basic unit economics
- Generating standard financial projections
- Computing simple financial metrics
- Managing basic lease calculations
- Performing routine financial analysis

### Use AdvancedFinancialModeling When:
- Need comprehensive financial analysis
- Require risk-adjusted projections
- Want to optimize tax strategy
- Need working capital analysis
- Performing strategic financial planning

## Integration Benefits

1. **Flexibility**: Choose the level of analysis needed
2. **Efficiency**: Basic operations remain simple and fast
3. **Comprehensiveness**: Access advanced features when needed
4. **Maintainability**: Clear separation of concerns
5. **Scalability**: Easy to extend either service

## Best Practices

1. Start with `FinancialService` for basic operations
2. Use `AdvancedFinancialModeling` for strategic decisions
3. Use `get_comprehensive_analysis()` when you need both
4. Consider performance implications of advanced analysis
5. Cache advanced analysis results when appropriate

## Future Extensions

The modular design allows for future extensions:
- Additional risk models
- New tax optimization strategies
- Enhanced working capital analysis
- Custom financial metrics
- Integration with external financial systems 