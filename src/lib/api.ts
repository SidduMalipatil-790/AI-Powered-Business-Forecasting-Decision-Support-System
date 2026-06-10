// Configurable API base. Override with VITE_API_BASE_URL env var.
export const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type FetchOpts = RequestInit;

async function request<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return (await res.json()) as T;
}

export interface DashboardData {
  totalSales: number;
  predictedSales: number;
  growth: number;
  alerts: number;
  series: { date: string; actual: number | null; predicted: number | null }[];
  categories: { category: string; sales: number; target: number }[];
}

export const getDashboard = () => request<DashboardData>("/api/dashboard");

export interface ForecastPoint {
  date: string;
  forecast: number;
  lower: number;
  upper: number;
  actual?: number | null;
}
export interface ForecastResponse {
  horizon: number;
  product: string;
  points: ForecastPoint[];
  summary: { mean: number; min: number; max: number; mape: number };
}

export const postForecast = (body: { horizon: number; product: string }) => {
  return request<ForecastResponse>("/api/forecast", {
    method: "POST",
    body: JSON.stringify(body),
  });
};

export interface Recommendation {
  id: string;
  type: "inventory" | "pricing" | "risk";
  title: string;
  confidence: number;
  explanation: string;
  impact: string;
}

export const getRecommendations = () => request<Recommendation[]>("/api/recommendations");

export interface Anomaly {
  id: string;
  date: string;
  metric: string;
  severity: "low" | "medium" | "high";
  delta: number;
  description: string;
}

export const getAnomalies = () => request<Anomaly[]>("/api/anomalies");

export interface SimulatePoint {
  date: string;
  baseline: number;
  scenario: number;
}
export interface SimulateResponse {
  product: string;
  price_change_pct: number;
  horizon: number;
  points: SimulatePoint[];
}

export const postSimulate = (body: { product: string; price_change_pct: number; horizon: number }) => {
  return request<SimulateResponse>("/api/simulate", {
    method: "POST",
    body: JSON.stringify(body),
  });
};
