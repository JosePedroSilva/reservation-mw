#TODO: Refactor the models to use a shared library
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from app.shared.enums import EventType 

Base = declarative_base()


class ReservationAudit(Base):
    __tablename__ = 'reservation_audit'

    id = Column(Integer, primary_key=True, autoincrement=True) # TODO: Add UUID support
    reservation_id = Column(Integer, nullable=False) # TODO Add ForeignKey('reservations.id') after refactoring the reservations model
    event_type = Column(SAEnum(EventType, name="event_type", native_enum=False, create_contstraint=True), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
