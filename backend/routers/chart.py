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
        
        # Calculate Moving Averages for Price
        df['ma5'] = df['Close'].rolling(window=5).mean()
        df['ma20'] = df['Close'].rolling(window=20).mean()
        df['ma60'] = df['Close'].rolling(window=60).mean()
        df['ma120'] = df['Close'].rolling(window=120).mean()
        
        # Calculate Moving Averages for Volume
        df['vol_ma5'] = df['Volume'].rolling(window=5).mean()
        df['vol_ma20'] = df['Volume'].rolling(window=20).mean()
        df['vol_ma60'] = df['Volume'].rolling(window=60).mean()
        df['vol_ma120'] = df['Volume'].rolling(window=120).mean()
        
        # Calculate daily % changes
        df['close_change_pct'] = df['Close'].pct_change() * 100
        df['volume_change_pct'] = df['Volume'].pct_change() * 100
        
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
                ma60=round(float(row['ma60']), 2) if not pd.isna(row['ma60']) else None,
                ma120=round(float(row['ma120']), 2) if not pd.isna(row['ma120']) else None,
                vol_ma5=round(float(row['vol_ma5']), 0) if not pd.isna(row['vol_ma5']) else None,
                vol_ma20=round(float(row['vol_ma20']), 0) if not pd.isna(row['vol_ma20']) else None,
                vol_ma60=round(float(row['vol_ma60']), 0) if not pd.isna(row['vol_ma60']) else None,
                vol_ma120=round(float(row['vol_ma120']), 0) if not pd.isna(row['vol_ma120']) else None,
                close_change_pct=round(float(row['close_change_pct']), 2) if not pd.isna(row['close_change_pct']) else None,
                volume_change_pct=round(float(row['volume_change_pct']), 2) if not pd.isna(row['volume_change_pct']) else None,
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

# Import cache for Tavily news storage
try:
    from backend.cache import get_news_cache, save_news_cache
    NEWS_CACHE_ENABLED = True
except ImportError:
    try:
        import sys
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from cache import get_news_cache, save_news_cache
        NEWS_CACHE_ENABLED = True
    except ImportError:
        NEWS_CACHE_ENABLED = False


@router.get("/news-by-date", response_model=NewsByDateResponse)
async def get_news_by_date(
    ticker: str = Query(..., description="Stock ticker symbol"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Get news for a specific date.
    Uses yfinance for recent news (30 days) and Tavily for older dates.
    Caches Tavily results for future requests.
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
        # Check cache first for this specific date
        if NEWS_CACHE_ENABLED:
            cached_news = get_news_cache(ticker, limit=100)
            for news in cached_news:
                if news.get('pubDate') == date:
                    news_items.append(NewsItem(
                        title=news.get('title', 'No title'),
                        summary=news.get('summary', ''),
                        url=news.get('url'),
                        source='Cached',
                        pubDate=date
                    ))
            
            if news_items:
                print(f"[OK] {ticker} news for {date} (from cache, {len(news_items)} articles)")
                return NewsByDateResponse(
                    ticker=ticker,
                    date=date,
                    news=news_items,
                    source="cache",
                    success=True
                )
        
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
                
                tavily_news_for_cache = []
                
                for result in response.get('results', []):
                    news_item = NewsItem(
                        title=result.get('title', 'No title'),
                        summary=result.get('content', '')[:500],
                        url=result.get('url'),
                        source=result.get('url', '').split('/')[2] if result.get('url') else 'Web',
                        pubDate=date
                    )
                    news_items.append(news_item)
                    
                    # Prepare for cache
                    tavily_news_for_cache.append({
                        'id': f"tavily_{ticker}_{date}_{len(tavily_news_for_cache)}",
                        'title': result.get('title', 'No title'),
                        'summary': result.get('content', '')[:500],
                        'pubDate': date,
                        'url': result.get('url', ''),
                        'tickers': [ticker]
                    })
                
                # Save Tavily results to cache
                if NEWS_CACHE_ENABLED and tavily_news_for_cache:
                    save_news_cache(ticker, tavily_news_for_cache)
                    print(f"[Cache] Saved {len(tavily_news_for_cache)} Tavily news for {ticker} on {date}")
                    
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

