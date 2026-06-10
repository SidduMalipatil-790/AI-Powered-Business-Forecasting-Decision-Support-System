# Oracle Spark Insight — Backend

AI-Powered Business Forecasting & Decision Support System backend.

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point (lifespan startup)
│   ├── config.py            # Settings from environment
│   ├── database.py          # SQLAlchemy + SQLite
│   ├── models/              # ORM: SalesRecord, PredictionRecord, AnomalyEvent
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # One router per endpoint group
│   │   ├── dashboard.py     # GET /api/dashboard
│   │   ├── forecast.py      # POST /api/forecast
│   │   ├── recommendations.py # GET /api/recommendations
│   │   └── anomalies.py     # GET /api/anomalies
│   ├── core/
│   │   ├── data_loader.py   # CSV loader + feature engineering
│   │   ├── pso_optimizer.py # Particle Swarm Optimization (pure NumPy)
│   │   ├── forecaster.py    # ARIMA with PSO-tuned hyperparameters
│   │   ├── anomaly_detector.py # Isolation Forest
│   │   ├── explainer.py     # XGBoost surrogate + SHAP
│   │   └── decision_engine.py  # Rule-based recommendations
│   └── utils/
│       └── seed_db.py       # One-time DB seeder
└── data/
    └── sales_data.csv       # 3,650-row synthetic dataset (5 products × 730 days)
```

## ML Stack

| Component | Technology |
|---|---|
| Forecasting | **ARIMA** (statsmodels) with PSO-tuned (p,d,q) order |
| Hyperparameter Tuning | **PSO** — pure NumPy, no external library |
| Anomaly Detection | **Isolation Forest** (scikit-learn) |
| Explainability | **SHAP** TreeExplainer on XGBoost surrogate |
| Decision Support | Rule-based engine combining forecasts + anomalies |
| Database | **SQLite** via SQLAlchemy ORM |

## Quick Start

### 1. Create a virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note**: First install may take 2-3 minutes (XGBoost, statsmodels).

### 3. Configure environment (optional)

```bash
copy .env.example .env
# Edit .env if you want to change ports, DB path, etc.
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first boot the server will:
1. Create the SQLite database (`business_forecast.db`)
2. Seed 3,650 rows of sales data
3. Run PSO to tune ARIMA hyperparameters for each product (**~1-3 min**)
4. Train XGBoost surrogate models for SHAP

Subsequent boots use cached PSO results (`pso_cache.json`) and are instant.

### 5. Connect the frontend

The `.env.local` file in the project root is already configured:
```
VITE_API_BASE_URL=http://localhost:8000
```

In a **separate terminal**:
```bash
cd ..          # back to oracle-spark-insight-main/
npm run dev
```

Open **http://localhost:5173** — the frontend now calls the real backend.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard` | KPIs, time series, category performance |
| POST | `/api/forecast` | ARIMA forecast + confidence intervals |
| GET | `/api/recommendations` | AI-generated business recommendations |
| GET | `/api/anomalies` | Isolation Forest anomaly detection |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/health` | Health check |

### POST /api/forecast — Example

```bash
curl -X POST http://localhost:8000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"horizon": 30, "product": "Wireless Earbuds Pro"}'
```

Response:
```json
{
  "horizon": 30,
  "product": "Wireless Earbuds Pro",
  "points": [
    {"date": "2026-05-03", "forecast": 1245.50, "lower": 980.20, "upper": 1510.80, "actual": null}
  ],
  "summary": {"mean": 1280.0, "min": 1100.0, "max": 1450.0, "mape": 6.2},
  "explanation": "Top forecast drivers: 7-day avg (38%), Last-week sales (29%), Month (18%)."
}
```

## PSO Tuning Details

The Particle Swarm Optimization runs on first startup to find the best ARIMA(p,d,q) order:
- **15 particles**, **10 iterations** per product
- Search space: p ∈ [0,3], d ∈ [0,2], q ∈ [0,3]
- Objective: minimise MAPE on 20% holdout set
- Results cached to `pso_cache.json` — delete this file to force re-tuning

## Anomaly Detection

Isolation Forest is trained on 6 features:
- `sales`, `lag_7`, `rolling_7_mean`, `rolling_7_std`, `day_of_week`, `is_weekend`

Severity thresholds:
- **High**: Isolation Forest score < -0.15
- **Medium**: score < 0.0
- **Low**: score >= 0.0

## Production Deployment

For production, switch to PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host:5432/forecast_db
```

And run with multiple workers:
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```
