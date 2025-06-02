from datetime import date, datetime

from pydantic import BaseModel, EmailStr

class ReservationCreate(BaseModel):
    guest_first_name: str
    guest_last_name:  str
    guest_email:      EmailStr
    guest_phone:      str # Not sure if str for phone is the best choice
    check_in_date:    date
    check_out_date:   date

class Reservation(BaseModel):
    id:               int
    guest_first_name: str
    guest_last_name:  str
    guest_email:      EmailStr
    guest_phone:      str
    check_in_date:    date
    check_out_date:   date
    created_at:       datetime
    updated_at:       datetime

    class Config:
        orm_mode = True
