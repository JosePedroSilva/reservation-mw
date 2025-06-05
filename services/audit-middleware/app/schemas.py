
from datetime import datetime
from pydantic import BaseModel

class ReservationAudit(BaseModel):
    id: int
    reservation_id: int
    event_type: str
    payload: dict
    created_at: datetime

    class ConfigDict:
        from_attributes = True