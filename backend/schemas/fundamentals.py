from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FundamentalsResponse(BaseModel):
    success: bool
    ticker: str
    period_type: str  # "annual" or "quarterly"
    periods: List[str]  # Column headers (years/quarters)
    income: List[Dict[str, Any]]
    balance: List[Dict[str, Any]]
    cashflow: List[Dict[str, Any]]
    error: Optional[str] = None

class BatchFundamentalsRequest(BaseModel):
    tickers: List[str]
    period_type: str = "annual"  # "annual" or "quarterly"
