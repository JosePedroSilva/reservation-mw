from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship
from app.shared.enums import EventType 

Base = declarative_base()


class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True, autoincrement=True) # TODO: Add UUID support
    source = Column(String(50), nullable=False, default="web")

    guest = Column(JSON, nullable=False)  # JSON field to store guest information  first name, last name, email, phone

    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    audits = relationship("ReservationAudit", back_populates="reservation", cascade="all, delete-orphan")


class ReservationAudit(Base):
    __tablename__ = 'reservation_audit'

    id = Column(Integer, primary_key=True, autoincrement=True) # TODO: Add UUID support
    reservation_id = Column(Integer, ForeignKey('reservations.id', ondelete="CASCADE"), nullable=False)
    event_type = Column(SAEnum(EventType, name="event_type", native_enum=False, create_contstraint=True), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reservation = relationship("Reservation", back_populates="audits")
