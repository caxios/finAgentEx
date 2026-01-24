"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel
from typing import Optional, List


# =============================================
# ANALYSIS SCHEMAS
# =============================================

class AnalyzeRequest(BaseModel):
    ticker: str


class AnalyzeResponse(BaseModel):
    ticker: str
    decision: str
    confidence: float
    timeframe: str
    reasoning: str
    risk_factors: str
    success: bool
    error: Optional[str] = None


# =============================================
# CHART SCHEMAS
# =============================================

class OHLCVItem(BaseModel):
    """Single OHLCV data point with indicators."""
    time: str  # YYYY-MM-DD format
    open: float
    high: float
    low: float
    close: float
    volume: float
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    vol_ma5: Optional[float] = None
    vol_ma20: Optional[float] = None
    vol_ma50: Optional[float] = None


class OHLCVRequest(BaseModel):
    ticker: str
    period: str = "6mo"  # 1mo, 3mo, 6mo, 1y, 2y


class OHLCVResponse(BaseModel):
    ticker: str
    period: str
    data: List[OHLCVItem]
    news: List[dict]  # Pre-fetched news for date matching
    success: bool
    error: Optional[str] = None


class NewsByDateRequest(BaseModel):
    ticker: str
    date: str  # YYYY-MM-DD format


class NewsItem(BaseModel):
    title: str
    summary: str
    url: Optional[str] = None
    source: str
    pubDate: str


class NewsByDateResponse(BaseModel):
    ticker: str
    date: str
    news: List[NewsItem]
    source: str  # "yfinance" or "tavily"
    success: bool
    error: Optional[str] = None
