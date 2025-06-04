import asyncio

from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas, db, models
from .consumer import consume_forever

from fastapi import FastAPI

app = FastAPI(title="Audit Middleware", docs_url=None, redoc_url=None)

@app.on_event("startup")
async def startup_event():
    await db.init_models()
    print("Models initialized successfully")

    loop = asyncio.get_event_loop()
    loop.create_task(consume_forever())
    print("Kafka consumer started successfully")

@app.get("/healthz",)
async def health_check():
    return {"status": "ok"}

# Leave this endpoint for testing purposes, would remove in production
@app.get(
  "/reservations-audit",
  response_model=list[schemas.ReservationAudit],
  status_code=200,
)
async def list_reservations(
  session: AsyncSession = Depends(db.get_db),
) -> list[schemas.ReservationAudit]:
  stmt = select(models.ReservationAudit)          
  result = await session.execute(stmt)  
  reservationsAudit = result.scalars().all() 
  return reservationsAudit