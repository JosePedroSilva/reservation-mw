import importlib.util
import sys
import types
from datetime import date, datetime

import pytest

# Provide a stub for the optional email_validator dependency used by Pydantic
module = types.ModuleType("email_validator")


class EmailNotValidError(ValueError):
    pass


def validate_email(email, allow_smtputf8=True, check_deliverability=True):
    return {"email": email}


module.validate_email = validate_email
module.EmailNotValidError = EmailNotValidError
sys.modules.setdefault("email_validator", module)

sys.path.append("services/reservation-middleware")
from app import schemas as res_schemas

AUDIT_SCHEMAS_PATH = "services/audit-middleware/app/schemas.py"
spec = importlib.util.spec_from_file_location("audit_schemas", AUDIT_SCHEMAS_PATH)
audit_schemas = importlib.util.module_from_spec(spec)
assert spec.loader  # for mypy type checking
spec.loader.exec_module(audit_schemas)


def test_guest_email_validation():
    guest_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'phone': '1234567890',
    }
    guest = res_schemas.Guest(**guest_data)
    assert guest.email == 'john@example.com'

    with pytest.raises(ValueError):
        res_schemas.Guest(**{**guest_data, 'email': 'invalid'})


def test_reservation_create_model():
    payload = {
        'guest': {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'phone': '555-0000',
        },
        'source': 'web',
        'check_in_date': date.today(),
        'check_out_date': date.today(),
    }
    reservation = res_schemas.ReservationCreate(**payload)
    assert reservation.source == 'web'
    assert reservation.guest.first_name == 'Jane'


def test_reservation_audit_schema():
    audit_payload = {
        'id': 1,
        'reservation_id': 2,
        'event_type': 'CREATED',
        'payload': {'foo': 'bar'},
        'created_at': datetime.utcnow(),
    }
    audit = audit_schemas.ReservationAudit(**audit_payload)
    assert audit.reservation_id == 2
    assert audit.payload == {'foo': 'bar'}
