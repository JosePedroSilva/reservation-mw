from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import db, schemas, models

app = FastAPI(title="Reservation Middleware")

@app.on_event("startup")
async def _startup() -> None:
    await db.init_models()

@app.post("/reservations", response_model=schemas.Reservation, status_code=201)
async def create_reservation(
    payload: schemas.ReservationCreate,
    session: AsyncSession = Depends(db.get_db),
):
    reservation = models.Reservation(**payload.model_dump())
    session.add(reservation)
    await session.commit()
    await session.refresh(reservation)
    return reservation

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
    stmt = select(models.Reservation)          # this is SELECT * FROM reservations
    result = await session.execute(stmt)       # runs the query asynchronously
    reservations = result.scalars().all()      # .scalars() returns ORM models; .all() pulls them into a list
    return reservations