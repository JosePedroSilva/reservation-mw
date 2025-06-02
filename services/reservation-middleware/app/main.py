from fastapi import FastAPI

app = FastAPI(title="Reservation Middleware")

@app.post("/reservations", status_code=201)
async def create_reservation():
    return {"message": "Reservation created successfully"}