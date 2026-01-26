from fastapi import APIRouter
from typing import Dict, List

from backend.schemas.fundamentals import BatchFundamentalsRequest, FundamentalsResponse
from backend.services.portfolio_service import fetch_portfolio_fundamentals

router = APIRouter(prefix="/api", tags=["fundamentals-batch"])

@router.post("/fundamentals/batch", response_model=Dict[str, FundamentalsResponse])
async def fetch_fundamentals_batch(request: BatchFundamentalsRequest):
    """
    Fetch fundamentals for multiple tickers in parallel.
    Delegates to portfolio service.
    """
    return await fetch_portfolio_fundamentals(request.tickers, request.period_type)
