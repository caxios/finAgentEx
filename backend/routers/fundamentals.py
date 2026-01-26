from fastapi import APIRouter, Query
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.schemas.fundamentals import FundamentalsResponse
from backend.services.single_ticker_service import fetch_ticker_fundamentals

# EDGAR identity is assumed to be set in main.py or core service
from edgar import set_identity
set_identity("FinAgentEx finagentex@example.com")

router = APIRouter(prefix="/api", tags=["fundamentals"])

@router.get("/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(
    ticker: str = Query(..., description="Stock ticker symbol"),
    type: str = Query("annual", description="annual or quarterly")
):
    """
    Fetch historical financial statements from SEC EDGAR.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, fetch_ticker_fundamentals, ticker, type
        )
    return result
