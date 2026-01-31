from contextlib import asynccontextmanager
import os
import secrets

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api import displays, groups, schedules
from app.services.scheduler import SchedulerService
from app.db.database import SessionLocal

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verify HTTP Basic authentication credentials.
    
    Compares credentials against environment variables ADMIN_USERNAME and ADMIN_PASSWORD.
    Uses secrets.compare_digest to prevent timing attacks.
    
    Raises:
        HTTPException: 401 Unauthorized if credentials don't match
    
    Returns:
        str: Username if authentication successful
    """
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


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

app.include_router(displays.router, prefix="/api/v1", dependencies=[Depends(verify_credentials)])
app.include_router(groups.router, prefix="/api/v1", dependencies=[Depends(verify_credentials)])
app.include_router(schedules.router, prefix="/api/v1", dependencies=[Depends(verify_credentials)])


@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "message": "LDPM API is running"}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ldpm"}
