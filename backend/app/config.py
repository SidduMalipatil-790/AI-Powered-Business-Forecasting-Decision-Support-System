"""Application configuration via environment variables / .env file."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend root (one level up from app/)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'business_forecast.db'}")
DATA_CSV_PATH: str = os.getenv("DATA_CSV_PATH", str(BASE_DIR / "data" / "sales_data.csv"))

# CORS origins accepted (comma-separated)
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://localhost:3000",
).split(",")

# PSO settings
PSO_PARTICLES: int = int(os.getenv("PSO_PARTICLES", "15"))
PSO_ITERATIONS: int = int(os.getenv("PSO_ITERATIONS", "10"))
PSO_CACHE_PATH: str = str(BASE_DIR / "pso_cache.json")

# Model artefact cache
MODEL_CACHE_PATH: str = str(BASE_DIR / "model_cache")
