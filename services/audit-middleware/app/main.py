import asyncio

from fastapi import FastAPI

from .consumer import consume_reservations

app = FastAPI(title="Audit Middleware", docs_url=None, redoc_url=None)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(consume_reservations())

@app.get("/healthz",)
async def health_check():
    return {"status": "ok"}