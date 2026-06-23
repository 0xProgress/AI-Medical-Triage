from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.config import config
from backend.routes.endpoints import router
from backend.services.report_generator import REPORTS_DIR

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Privacy-first, open-source medical triage system"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "http://localhost:5173", 
        "http://localhost:3000",
        "http://127.0.0.1:4321",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/downloads", StaticFiles(directory=str(REPORTS_DIR)), name="downloads")

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )