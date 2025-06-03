import asyncio

from fastapi import FastAPI

from .db import init_models
from .consumer import consume_forever

from fastapi import FastAPI

app = FastAPI(title="Audit Middleware", docs_url=None, redoc_url=None)

@app.on_event("startup")
async def startup_event():
    await init_models()
    print("Models initialized successfully")

    loop = asyncio.get_event_loop()
    loop.create_task(consume_forever())
    print("Kafka consumer started successfully")

@app.get("/healthz",)
async def health_check():
    return {"status": "ok"}