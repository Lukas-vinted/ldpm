from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import displays, groups, schedules
from app.services.scheduler import SchedulerService
from app.db.database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize and start scheduler
    - Shutdown: Stop scheduler
    """
    # Startup: Initialize scheduler
    db = SessionLocal()
    try:
        scheduler = SchedulerService(db_session=db)
        scheduler.load_schedules_from_db()
        scheduler.start()
        
        # Store scheduler in app state for access by endpoints
        app.state.scheduler = scheduler
        
        yield
    finally:
        # Shutdown: Stop scheduler
        if hasattr(app.state, "scheduler"):
            app.state.scheduler.stop()
        db.close()


app = FastAPI(
    title="LDPM API",
    description="Linux Display Power Management for Sony BRAVIA TVs",
    version="0.0.1",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:80", "localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(displays.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(schedules.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "message": "LDPM API is running"}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ldpm"}
