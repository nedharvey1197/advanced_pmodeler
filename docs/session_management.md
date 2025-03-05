# Session Management in Advanced PModeler

## Overview

The Advanced PModeler uses SQLAlchemy's session management enhanced with service dependency management. This document explains how sessions work, how they manage service dependencies, and best practices for using them.

## Core Components

### 1. Session Factory
```python
# src/models/base_models.py
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)

def get_session():
    """Get a new database session with service management."""
    session = Session()
    session._services = {}  # Initialize services dict
    return session
```

### 2. Service Management Mixin
```python
class ServiceMixin:
    """Mixin that adds service dependency management to services."""
    def _get_service(self, service_class):
        if not hasattr(self.session, '_services'):
            self.session._services = {}
        service_name = service_class.__name__.lower()
        if service_name not in self.session._services:
            self.session._services[service_name] = service_class(self.session)
        return self.session._services[service_name]
```

## Usage Patterns

### 1. Direct Service Creation
```python
session = get_session()
financial_service = FinancialService(session)
result = financial_service.calculate_financial_projection(scenario_id, year)
session.close()
```

### 2. Service Dependencies
```python
class FinancialService(ServiceMixin):
    def calculate_projection(self, scenario_id, year):
        # Get dependent services through session
        equipment_service = self._get_service(EquipmentService)
        sales_service = self._get_service(SalesService)
        
        # Use services with same session
        utilization = equipment_service.calculate_utilization(scenario_id, year)
        sales = sales_service.calculate_forecast(scenario_id, year)
```

### 3. Wrapper Functions
```python
def calculate_financial_metrics(scenario_id):
    """Wrapper function that manages its own session."""
    session = get_session()
    service = FinancialService(session)
    try:
        return service.calculate_key_financial_metrics(scenario_id)
    finally:
        session.close()
```

## Key Features

1. **Automatic Service Sharing**
   - Services created through `_get_service()` share the same session
   - Services are cached in session._services
   - Prevents duplicate service instances

2. **Session Isolation**
   - Each session has its own set of services
   - Different sessions don't interfere with each other
   - Perfect for parallel processing

3. **Resource Management**
   - Services are cleaned up when session closes
   - No need to manually manage service lifecycles
   - Prevents memory leaks

4. **Dependency Resolution**
   - Circular dependencies are prevented
   - Services are created on-demand
   - Clear service relationship hierarchy

## Best Practices

1. **Session Lifecycle**
   ```python
   session = get_session()
   try:
       # Use session
       result = service.do_something()
       session.commit()
       return result
   except Exception as e:
       session.rollback()
       raise
   finally:
       session.close()
   ```

2. **Service Creation**
   ```python
   # Good: Let session manage services
   equipment_service = self._get_service(EquipmentService)
   
   # Bad: Don't create services directly
   equipment_service = EquipmentService(self.session)
   ```

3. **Transaction Management**
   ```python
   def complex_operation(self, scenario_id):
       # Start with data queries
       scenario = self.session.query(Scenario).get(scenario_id)
       
       # Make changes
       scenario.status = 'processing'
       self.session.add(scenario)
       
       # Let caller manage transaction
       # (don't commit here)
   ```

## Testing

1. **Service Sharing Tests**
   ```python
   def test_service_sharing():
       session = get_session()
       financial = FinancialService(session)
       equipment = financial._get_service(EquipmentService)
       assert financial.session is equipment.session
   ```

2. **Session Isolation Tests**
   ```python
   def test_service_isolation():
       session1, session2 = get_session(), get_session()
       service1 = FinancialService(session1)
       service2 = FinancialService(session2)
       assert service1.session is not service2.session
   ```

3. **Cleanup Tests**
   ```python
   def test_session_cleanup():
       session = get_session()
       financial = FinancialService(session)
       session.close()
       assert not hasattr(session, '_services')
   ```

## Common Pitfalls

1. **Session Leaks**
   ```python
   # Bad: Session never closed
   def leaky_function():
       session = get_session()
       return FinancialService(session)
   
   # Good: Use context manager or close explicitly
   def proper_function():
       session = get_session()
       try:
           service = FinancialService(session)
           return service.calculate_something()
       finally:
           session.close()
   ```

2. **Premature Commits**
   ```python
   # Bad: Service commits in middle of operation
   def bad_service_method(self):
       self.session.commit()  # Don't do this
   
   # Good: Let caller manage transactions
   def good_service_method(self):
       # Make changes
       # Let caller commit
   ```

3. **Cross-Session Access**
   ```python
   # Bad: Using service after session closed
   session = get_session()
   service = FinancialService(session)
   session.close()
   service.do_something()  # Will fail
   
   # Good: Service used within session lifetime
   session = get_session()
   try:
       service = FinancialService(session)
       service.do_something()
   finally:
       session.close()
   ```

## Advanced Topics

1. **Custom Session Management**
   ```python
   class CustomSession(Session):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self._services = {}
           self._custom_data = {}
   ```

2. **Service Factory Pattern**
   ```python
   def create_service(service_class, session):
       """Create service with proper session management."""
       if not hasattr(session, '_services'):
           session._services = {}
       return service_class(session)
   ```

3. **Session Events**
   ```python
   from sqlalchemy import event
   
   @event.listens_for(Session, 'after_commit')
   def receive_after_commit(session):
       """Handle post-commit cleanup."""
       pass
   ``` 