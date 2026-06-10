from services.reimbursement import ReimbursementService
from schemas.reimbursement import ReimbursementCreate
from unittest.mock import Mock
import uuid
from datetime import date

def test_reimbursement_create():
    mock_repo = Mock()
    mock_audit = Mock()
    mock_repo.create.return_value = Mock(id=uuid.uuid4(), model_dump=lambda mode: {})
    
    service = ReimbursementService(repository=mock_repo, audit_service=mock_audit)
    
    data = ReimbursementCreate(
        request_date=date.today(),
        business_category="Travel",
        nature_of_expense="Flight",
        bill_number="123",
        bill_date=date.today(),
        amount=500.0
    )
    
    result = service.create(data, str(uuid.uuid4()), "test@example.com", "Test User", "http://url")
    assert result is not None
    mock_repo.create.assert_called_once()
    mock_audit.log_action.assert_called_once()
