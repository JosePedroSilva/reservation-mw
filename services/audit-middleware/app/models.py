from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import declarative_base

from .enums import EventType 

Base = declarative_base()


class ReservationAudit(Base):
    __tablename__ = 'reservation_audit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, nullable=False) # Since the models are separated by service, we assume reservation_id is an Integer, ideally it should be a ForeignKey to a Reservation table.
    event_type = Column(SAEnum(EventType, name="event_type", native_enum=False, create_constraint=True), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
