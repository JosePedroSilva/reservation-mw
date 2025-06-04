from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, default="web")

    guest = Column(JSON, nullable=False)  # JSON field to store guest information  first name, last name, email, phone

    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
