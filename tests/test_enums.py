import sys

sys.path.append('services/reservation-middleware')
from app.enums import EventType as ResEventType

sys.path.append('services/audit-middleware')
from app.enums import EventType as AuditEventType


def test_event_type_values_equal():
    assert list(ResEventType) == list(AuditEventType)


def test_event_type_str():
    assert str(ResEventType.CREATED) == 'EventType.CREATED'
