from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from database.db import engine, Base
from routes.api import router as api_router
from services.background import start_periodic_update

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="YouTube Aggregator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Background task for periodic updates
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_periodic_update())

@app.get("/")
def read_root():
    return {"status": "API is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    