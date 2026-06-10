from pydantic import BaseModel, Field

class SimulateRequest(BaseModel):
    product: str
    price_change_pct: float = Field(..., description="Percentage change in price (e.g., -15.0 for a 15% discount)")
    horizon: int = Field(30, description="Days to simulate")

class SimulatedPoint(BaseModel):
    date: str
    baseline: float
    scenario: float

class SimulateResponse(BaseModel):
    product: str
    price_change_pct: float
    horizon: int
    points: list[SimulatedPoint]
