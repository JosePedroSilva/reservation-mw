from uuid import uuid4
from datetime import datetime

from app.shared.enums import EventType

from fastapi import FastAPI, Depends, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import db, schemas, models, kafka

app = FastAPI(title="Reservation Middleware")

@app.on_event("startup")
async def _startup() -> None:
  await db.init_models()
  await kafka.start_producer() 

@app.on_event("shutdown")
async def _shutdown() -> None:
    await kafka.stop_producer() 

@app.post("/reservations", status_code=status.HTTP_201_CREATED)
async def create_reservation(
  payload: schemas.ReservationCreate,
  request: Request,
  session: AsyncSession = Depends(db.get_db),
) -> schemas.ReservationResponse:
  
  reservation = models.Reservation(**payload.model_dump())
  session.add(reservation)
  await session.commit()
  await session.refresh(reservation)

  reservation_out = schemas.Reservation.model_validate(reservation, from_attributes=True)
  reservation_data = reservation_out.model_dump()

  envelope = {
    "status": "success",
    "statusCode": status.HTTP_201_CREATED,
    "data": reservation_data,
    "timestamp": datetime.utcnow(),
    "path": request.url.path,
    "requestId": str(uuid4()),
  }

  kafka_envelope = {
    "id": reservation.id,
    "data": reservation_data,
    "event_type": EventType.CREATED,
  }

  await kafka.publish(kafka_envelope)

  return envelope

#TODO: Remove this endpoint this is for testing purposes only
@app.get(
  "/reservations",
  response_model=list[schemas.Reservation],
  status_code=200,
)
async def list_reservations(
  session: AsyncSession = Depends(db.get_db),
) -> list[schemas.Reservation]:
  """
  Execute a simple SELECT * FROM reservations
  and return a list of ORM objects, which Pydantic will convert to JSON.
  """
  stmt = select(models.Reservation)          
  result = await session.execute(stmt)  
  reservations = result.scalars().all() 
  return reservations

@app.get(
  "/audits",
  response_model=list[schemas.ReservationAudit],
  status_code=200,
)
async def list_audits(
  session: AsyncSession = Depends(db.get_db),
) -> list[schemas.ReservationAudit]:
  """
  Execute a simple SELECT * FROM reservation_audit
  and return a list of ORM objects, which Pydantic will convert to JSON.
  """
  stmt = select(models.ReservationAudit)          
  result = await session.execute(stmt)  
  audits = result.scalars().all() 
  return audits