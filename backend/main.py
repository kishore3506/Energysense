from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import DATASETS_DIR, MODELS_DIR
from services.db_service import init_db
from api.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize SQLite database tables
    init_db()
    print("EnergySense SQLite Database Initialized.")
    yield

app = FastAPI(
    title="EnergySense API",
    description="Temporal Deep Learning API for Building Energy Consumption Forecasting",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes FIRST so they take precedence over static files
app.include_router(router)

# Mount frontend static build if present (for single-port Docker / Hugging Face Spaces / production deployment)
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if not frontend_dist.exists():
    frontend_dist = BASE_DIR / "frontend_dist"

if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "project": "EnergySense",
            "description": "Temporal Deep Learning for Building Energy Consumption Forecasting",
            "docs_url": "/docs",
            "health_url": "/api/health",
            "frontend_note": "Run 'npm run build' in frontend/ to enable unified single-port web interface."
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
