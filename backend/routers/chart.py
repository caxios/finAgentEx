"""
Chart Router - OHLCV data and news endpoints for interactive chart
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_tools import fetch_single_ticker_data, fetch_news_for_ticker
from backend.schemas.models import (
    OHLCVResponse, OHLCVItem,
    NewsByDateResponse, NewsItem
)

# Try to import Tavily for fallback news search
try:
    from tavily import TavilyClient
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
except ImportError:
    tavily_client = None

router = APIRouter(prefix="/api", tags=["chart"])


@router.get("/ohlcv", response_model=OHLCVResponse)
async def get_ohlcv(
    ticker: str = Query(..., description="Stock ticker symbol"),
    period: str = Query("6mo", description="Time period: 1mo, 3mo, 6mo, 1y, 2y")
):
    """
    Get OHLCV data with moving averages for the interactive chart.
    Also returns pre-fetched news for date matching.
    """
    ticker = ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Must be one of: {valid_periods}")
    
    try:
        # Fetch OHLCV data
        df = fetch_single_ticker_data(ticker, period)
        
        if df is None or df.empty:
            return OHLCVResponse(
                ticker=ticker,
                period=period,
                data=[],
                news=[],
                success=False,
                error="No data available for this ticker"
            )
        
        # Calculate Moving Averages
        df['ma5'] = df['Close'].rolling(window=5).mean()
        df['ma20'] = df['Close'].rolling(window=20).mean()
        df['ma50'] = df['Close'].rolling(window=50).mean()
        df['vol_ma5'] = df['Volume'].rolling(window=5).mean()
        df['vol_ma20'] = df['Volume'].rolling(window=20).mean()
        df['vol_ma50'] = df['Volume'].rolling(window=50).mean()
        
        # Convert to list of OHLCVItem
        ohlcv_data = []
        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
            ohlcv_data.append(OHLCVItem(
                time=date_str,
                open=round(float(row['Open']), 2),
                high=round(float(row['High']), 2),
                low=round(float(row['Low']), 2),
                close=round(float(row['Close']), 2),
                volume=float(row['Volume']),
                ma5=round(float(row['ma5']), 2) if not pd.isna(row['ma5']) else None,
                ma20=round(float(row['ma20']), 2) if not pd.isna(row['ma20']) else None,
                ma50=round(float(row['ma50']), 2) if not pd.isna(row['ma50']) else None,
                vol_ma5=round(float(row['vol_ma5']), 0) if not pd.isna(row['vol_ma5']) else None,
                vol_ma20=round(float(row['vol_ma20']), 0) if not pd.isna(row['vol_ma20']) else None,
                vol_ma50=round(float(row['vol_ma50']), 0) if not pd.isna(row['vol_ma50']) else None,
            ))
        
        # Pre-fetch news for the ticker (for date matching on frontend)
        news_list = fetch_news_for_ticker(ticker, count=50)
        
        return OHLCVResponse(
            ticker=ticker,
            period=period,
            data=ohlcv_data,
            news=news_list,
            success=True
        )
        
    except Exception as e:
        print(f"Error fetching OHLCV for {ticker}: {e}")
        return OHLCVResponse(
            ticker=ticker,
            period=period,
            data=[],
            news=[],
            success=False,
            error=str(e)
        )


# Need to import pandas for isna check
import pandas as pd


@router.get("/news-by-date", response_model=NewsByDateResponse)
async def get_news_by_date(
    ticker: str = Query(..., description="Stock ticker symbol"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Get news for a specific date.
    Uses yfinance for recent news (30 days) and Tavily for older dates.
    """
    ticker = ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    
    # Parse the requested date
    try:
        requested_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    days_ago = (datetime.now() - requested_date).days
    
    news_items = []
    source = "yfinance"
    
    try:
        if days_ago <= 30:
            # Use yfinance for recent news
            news_list = fetch_news_for_ticker(ticker, count=50)
            
            for news in news_list:
                pub_date = news.get('pubDate', '')
                if pub_date and pub_date == date:
                    news_items.append(NewsItem(
                        title=news.get('title', 'No title'),
                        summary=news.get('summary', ''),
                        url=news.get('url'),
                        source='Yahoo Finance',
                        pubDate=pub_date
                    ))
        
        # If no yfinance results or date is older, try Tavily
        if not news_items and tavily_client:
            source = "tavily"
            try:
                query = f"{ticker} stock news {date}"
                response = tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5
                )
                
                for result in response.get('results', []):
                    news_items.append(NewsItem(
                        title=result.get('title', 'No title'),
                        summary=result.get('content', '')[:500],
                        url=result.get('url'),
                        source=result.get('url', '').split('/')[2] if result.get('url') else 'Web',
                        pubDate=date
                    ))
            except Exception as e:
                print(f"Tavily search failed: {e}")
        
        return NewsByDateResponse(
            ticker=ticker,
            date=date,
            news=news_items,
            source=source,
            success=True
        )
        
    except Exception as e:
        print(f"Error fetching news for {ticker} on {date}: {e}")
        return NewsByDateResponse(
            ticker=ticker,
            date=date,
            news=[],
            source=source,
            success=False,
            error=str(e)
        )
