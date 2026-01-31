from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import displays, groups, schedules

app = FastAPI(
    title="LDPM API",
    description="Linux Display Power Management for Sony BRAVIA TVs",
    version="0.0.1",
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
