from datetime import date, datetime
from pydantic import BaseModel, EmailStr

class Guest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str  # Not sure if str for phone is the best choice, could use a more structured type and constraint

class ReservationCreate(BaseModel):
    guest: Guest
    source: str 
    check_in_date:    date
    check_out_date:   date

class Reservation(BaseModel):
    id: int
    source: str
    guest: Guest
    check_in_date: date
    check_out_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReservationResponse(BaseModel):
    status: str
    statusCode: int
    data: Reservation
    timestamp: datetime
    path: str
    requestId: str