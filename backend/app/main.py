from fastapi import FastAPI
from backend.app.modules.checkin.router import router as checkin_router

app = FastAPI(title="QueueLess 2.3 Member 2 API")

# Include routers
app.include_router(checkin_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
