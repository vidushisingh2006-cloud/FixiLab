from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import audits, health
from app.database import init_db

app = FastAPI(title="FixiLab API")

# Add CORS middleware - must be before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
REPORTS_DIR = BACKEND_DIR / "reports"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# Mount static directories for serving uploaded documents and generated PDF reports
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/backend/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="backend_uploads")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/backend/reports", StaticFiles(directory=str(REPORTS_DIR)), name="backend_reports")

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(audits.router, prefix="/api/audits", tags=["audits"])


@app.get("/")
def read_root():
    return {"message": "FixiLab API is running", "status": "healthy"}
