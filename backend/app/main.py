"""
FastAPI Application Entry Point.

Lifespan order:
  1. Init / migrate DB tables
  2. Seed DB from CSV (if empty)
  3. Warm up ARIMA models (PSO-tuned)
  4. Warm up XGBoost surrogate models for SHAP
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import init_db
from app.utils.seed_db import seed_database
from app.core.forecaster import warm_up_models
from app.core.explainer import warm_up_explainers
from app.routers import dashboard, forecast, recommendations, anomalies, simulate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle."""
    t0 = time.time()
    logger.info("═══════════════════════════════════════")
    logger.info("  Oracle Spark Insight — Backend Boot  ")
    logger.info("═══════════════════════════════════════")

    logger.info("[1/4] Initialising database…")
    init_db()

    logger.info("[2/4] Seeding database from CSV…")
    seed_database()

    logger.info("[3/4] Training ARIMA models (PSO-tuned)…")
    warm_up_models()

    logger.info("[4/4] Training XGBoost surrogate models (SHAP)…")
    warm_up_explainers()

    elapsed = time.time() - t0
    logger.info("✓ Backend ready in %.1fs — listening on http://localhost:8000", elapsed)
    logger.info("  Docs: http://localhost:8000/docs")
    logger.info("═══════════════════════════════════════")

    yield  # Application runs here

    logger.info("Backend shutting down.")


app = FastAPI(
    title="Oracle Spark Insight — AI Forecasting API",
    description=(
        "Production backend for the AI-Powered Business Forecasting & Decision Support System. "
        "Provides ARIMA forecasting (PSO-tuned), Isolation Forest anomaly detection, "
        "SHAP explainability, and rule-based decision recommendations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS — allow Vite dev server and any configured origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(forecast.router, prefix="/api", tags=["Forecasting"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(anomalies.router, prefix="/api", tags=["Anomalies"])
app.include_router(simulate.router, prefix="/api", tags=["Simulation"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "service": "Oracle Spark Insight API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
