"""Tests for service dependency management."""

import pytest
from sqlalchemy.orm import Session

from advanced_pmodeler.models import get_session
from advanced_pmodeler.services.financial_service import FinancialService
from advanced_pmodeler.services.equipment_service import EquipmentService
from advanced_pmodeler.services.sales_service import SalesService

def test_service_sharing():
    """Test that services share the same session."""
    session = get_session()
    
    # Create services
    financial = FinancialService(session)
    equipment = financial._get_service(EquipmentService)
    sales = financial._get_service(SalesService)
    
    # Test session sharing
    assert financial.session is equipment.session
    assert financial.session is sales.session
    
    # Test service reuse
    assert equipment is financial._get_service(EquipmentService)
    assert sales is financial._get_service(SalesService)

def test_service_isolation():
    """Test that different sessions have different service instances."""
    session1 = get_session()
    session2 = get_session()
    
    financial1 = FinancialService(session1)
    financial2 = FinancialService(session2)
    
    equipment1 = financial1._get_service(EquipmentService)
    equipment2 = financial2._get_service(EquipmentService)
    
    assert equipment1 is not equipment2
    assert equipment1.session is session1
    assert equipment2.session is session2

def test_session_cleanup():
    """Test that services are cleaned up when session ends."""
    session = get_session()
    financial = FinancialService(session)
    equipment = financial._get_service(EquipmentService)
    
    assert hasattr(session, '_services')
    assert 'equipmentservice' in session._services
    
    session.close()
    assert not hasattr(session, '_services') 