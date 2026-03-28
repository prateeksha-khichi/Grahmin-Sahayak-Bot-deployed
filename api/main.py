"""
FastAPI Main Application
Complete REST API for Gramin Sahayak
Enhanced Edition
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger
import os

# ---------------- ROUTERS ---------------- #

from api.routes.loan import router as loan_router
from api.routes.fraud import router as fraud_router
from api.routes.rag import router as rag_router

from api.routes.pdf_routes import router as pdf_router
from api.routes.language_routes import router as language_router
from api.routes.advisory_routes import router as advisory_router


# ---------------- CORE ---------------- #

from api.schemas.request_response import HealthResponse
from utils.file_utils import init_project_directories
from database.db import init_db as init_new_db


from scheduler.daily_advisory import start_scheduler

# ------------------------------------------------
init_new_db()

init_project_directories()

app = FastAPI(
    title="Gramin Sahayak API",
    description="Rural Financial Literacy & Loan Assistant API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ---------------- CORS ---------------- #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- REGISTER ROUTERS ---------------- #

app.include_router(loan_router)
app.include_router(fraud_router)
app.include_router(rag_router)

app.include_router(pdf_router)
app.include_router(language_router)
app.include_router(advisory_router)

# ---------------- EVENTS ---------------- #

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Gramin Sahayak API")

    try:
        init_new_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.warning(f"DB init skipped: {e}")

    try:
        start_scheduler()
        logger.info("✓ Advisory scheduler started")
    except Exception as e:
        logger.warning(f"Scheduler skipped: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Server shutting down")

# ---------------- HEALTH ---------------- #

@app.get("/", response_model=HealthResponse)
async def root():
    from services.rag_service import RAGService

    rag_service = RAGService()
    service_status = rag_service.get_service_status()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services={
            "rag": service_status.get("rag_status"),
            "llm": service_status.get("llm_available"),
            "database": "connected",
            "pdf_explainer": "ready",
            "language": "ready",
            "advisory": "ready",
            "tts": "ready"
        }
    )

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

@app.get("/features")
async def features():
    return {
        "loan": "/loan/predict",
        "fraud": "/fraud/detect",
        "rag": "/rag/query",
        "pdf": "/pdf/explain",
        "language": "/language/set-language",
        "advisory": "/advisory/send/{user_id}"
    }

# ---------------- GLOBAL ERROR ---------------- #

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )

# ---------------- LOCAL RUN ---------------- #

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
