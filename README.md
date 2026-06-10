# Oracle Spark Insight — AI-Powered Business Forecasting & Decision Support System

An end-to-end, full-stack application that leverages advanced Machine Learning models to provide real-time business intelligence, predictive forecasting, anomaly detection, and automated decision support.

## 🌟 Overview

This project consists of a modern, highly interactive **React frontend** and a powerful **Python/FastAPI backend**. It is designed to replace static dashboards with an intelligent agent that not only shows you what happened but predicts what *will* happen, explains *why*, and tells you *what to do* about it.

## 🏗️ Architecture

### Frontend (React + Vite)
- **Framework:** React 18 with TypeScript, bundled by Vite for lightning-fast development.
- **Styling:** Tailwind CSS with a custom glassmorphism design system for a premium, modern aesthetic.
- **Components:** shadcn/ui components (Radix UI) for accessible, unstyled primitives.
- **Data Fetching:** TanStack React Query for intelligent caching, background updates, and state management.
- **Visualizations:** Recharts for responsive, interactive, and beautiful data visualization.

### Backend (Python + FastAPI)
- **Framework:** FastAPI for high-performance, async API endpoints.
- **Database:** SQLite (via SQLAlchemy ORM) for lightweight, portable data storage.
- **Data Processing:** Pandas and NumPy for heavy data lifting and feature engineering.
- **API Validation:** Pydantic for strict request/response contract enforcement.

## 🧠 Machine Learning Stack

The system utilizes a suite of distinct ML algorithms, each selected for a specific business purpose:

1. **Forecasting Engine (ARIMA + PSO)**
   - **Model:** AutoRegressive Integrated Moving Average (ARIMA) via `statsmodels`.
   - **Optimization:** A custom, pure-NumPy **Particle Swarm Optimization (PSO)** algorithm runs on startup to find the mathematically optimal `(p, d, q)` hyperparameters for each product's specific dataset.
   - **Output:** Multi-day forecasts with 95% statistical confidence intervals.

2. **Anomaly Detection (Isolation Forest)**
   - **Model:** Scikit-learn's `IsolationForest`.
   - **Function:** Scans 6 engineered features (including rolling averages and calendar effects) over a 30-day lookback window to isolate statistical outliers in demand.
   - **Output:** Risk alerts categorized by severity (High/Medium/Low) with dynamically generated natural language descriptions.

3. **Explainable AI (XGBoost + SHAP)**
   - **Model:** A lightweight `XGBRegressor` trained as a surrogate model.
   - **Function:** Uses **SHAP (SHapley Additive exPlanations)** to break down the forecast and compute exactly which features (e.g., "7-day average" or "Day of the week") drove the prediction.
   - **Output:** Human-readable explanations attached to the API responses.

4. **Decision Support (Rule-Based AI Engine)**
   - **Function:** Combines the ARIMA forecast trajectory, Isolation Forest risk alerts, and current inventory levels to generate actionable business recommendations (e.g., pricing optimization, proactive restocking).

---

## 🚀 Getting Started

Follow these steps to run both the backend and frontend simultaneously on your local machine.

### 1. Start the Backend

Open a terminal and navigate to the `backend` directory:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **Note on First Startup:** The very first time you boot the server, it will generate a synthetic 3,650-row CSV dataset, seed the SQLite database, and run the PSO hyperparameter tuning across all product categories. This tuning process takes **1–3 minutes**. Subsequent startups will be instant, as the optimized parameters are cached locally.

### 2. Start the Frontend

Open a **new, separate terminal** and remain in the root directory (`oracle-spark-insight-main`):

Install the Node dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

### 3. View the Application

Open your browser and navigate to:
👉 **http://localhost:8080** *(or the port specified by Vite in your terminal)*

The frontend will automatically connect to the Python backend running on `localhost:8000`. You can also view the interactive backend API documentation at **http://localhost:8000/docs**.

---

## 📁 Key Directory Structure

```text
oracle-spark-insight-main/
├── src/                    # React Frontend Source
│   ├── components/         # Reusable UI components
│   ├── lib/                # API client (api.ts) & utils
│   └── pages/              # Main dashboard views
│
├── backend/                # Python Backend Source
│   ├── app/
│   │   ├── core/           # ML Models (ARIMA, PSO, Isolation Forest)
│   │   ├── models/         # SQLAlchemy ORM definitions
│   │   ├── routers/        # FastAPI endpoint handlers
│   │   └── schemas/        # Pydantic data validation schemas
│   ├── data/               # CSV datasets
│   └── business_forecast.db# Auto-generated SQLite database
│
└── .env.local              # Tells frontend where to find the backend
```
