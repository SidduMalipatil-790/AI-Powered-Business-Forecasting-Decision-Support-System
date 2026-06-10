from fastapi import APIRouter, HTTPException
import logging

from app.schemas.simulate import SimulateRequest, SimulateResponse
from app.core.simulator import run_simulation
from app.core.data_loader import PRODUCT_MAP

router = APIRouter(prefix="/simulate", tags=["Simulation"])
logger = logging.getLogger(__name__)

@router.post("", response_model=SimulateResponse)
def simulate_scenario(req: SimulateRequest):
    if req.product != "ALL" and req.product not in PRODUCT_MAP.values():
        raise HTTPException(status_code=400, detail="Invalid product ID")
        
    try:
        points = run_simulation(req.product, req.horizon, req.price_change_pct)
        return SimulateResponse(
            product=req.product,
            price_change_pct=req.price_change_pct,
            horizon=req.horizon,
            points=points
        )
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
