"""
Data Tools Module for Multi-Agent System
Implements data fetching and caching following reference code patterns.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend to avoid Tkinter threading issues
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import os

# --- Global Data Cache ---
DATA_CACHE: Dict[str, pd.DataFrame] = {}

# Chart output directory
CHART_DIR = os.path.join(os.path.dirname(__file__), "modules", "charts")
os.makedirs(CHART_DIR, exist_ok=True)


def fetch_period_data(tickers: List[str], period: str = "3mo") -> Dict[str, pd.DataFrame]:
    """
    Fetch and cache period data for multiple tickers.
    Follows Reference Code A pattern strictly.
    
    Args:
        tickers: List of stock ticker symbols
        period: Data period (e.g., "3mo", "6mo", "1y")
    
    Returns:
        Dictionary mapping ticker to DataFrame
    """
    results = {}
    
    for ticker in tickers:
        ticker = ticker.upper()
        cache_key = f"{ticker}_{period}"
        
        # Check cache first
        if cache_key in DATA_CACHE:
            print(f"[OK] {ticker} (from cache)")
            results[ticker] = DATA_CACHE[cache_key]
            continue
        
        try:
            df = yf.download(ticker, period=period, progress=False)
            
            if not df.empty:
                # Flatten multi-index columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                DATA_CACHE[cache_key] = df
                results[ticker] = df
                print(f"[OK] {ticker} ({len(df)} rows fetched)")
            else:
                print(f"[X] {ticker} (no data)")
                
        except Exception as e:
            print(f"[X] {ticker} (error: {e})")
    
    return results


def fetch_single_ticker_data(ticker: str, period: str = "3mo") -> Optional[pd.DataFrame]:
    """
    Convenience function to fetch data for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: Data period
    
    Returns:
        DataFrame or None if fetch fails
    """
    result = fetch_period_data([ticker], period)
    return result.get(ticker.upper())


def fetch_intraday_data(ticker: str, target_date: str) -> Optional[pd.DataFrame]:
    """
    Fetch 5-minute intraday data for a specific date.
    
    Args:
        ticker: Stock ticker symbol
        target_date: Date string in 'YYYY-MM-DD' format
    
    Returns:
        DataFrame with intraday data including returns and change_percent
    """
    try:
        stock = yf.Ticker(ticker.upper())
        
        # Parse target date and calculate next day
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        next_day = target_dt + timedelta(days=1)
        
        # Fetch 5-minute interval data
        df = stock.history(
            start=target_dt.strftime("%Y-%m-%d"),
            end=next_day.strftime("%Y-%m-%d"),
            interval="5m"
        )
        
        if df.empty:
            print(f"[X] {ticker} intraday (no data for {target_date})")
            return None
        
        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Calculate returns and change_percent
        df['returns'] = df['Close'].pct_change()
        df['change_percent'] = (df['Close'] / df['Close'].iloc[0] - 1) * 100
        
        print(f"[OK] {ticker} intraday ({len(df)} 5-min bars for {target_date})")
        return df
        
    except Exception as e:
        print(f"[X] {ticker} intraday (error: {e})")
        return None


def fetch_news_for_ticker(ticker: str, count: int = 10) -> List[dict]:
    """
    Fetch news using yfinance.
    Follows Reference Code B pattern strictly.
    
    Args:
        ticker: Stock ticker symbol
        count: Number of news items to fetch
    
    Returns:
        List of news dictionaries with keys: id, title, summary, pubDate, url, tickers
    """
    try:
        data = yf.Ticker(ticker.upper()).get_news(count=count)
        news_list = []
        
        if not data:
            print(f"[!] {ticker} : No news articles found")
            return []
        
        for item in data[:count]:
            if 'content' not in item:
                continue
            
            content = item['content']
            
            # Extract URL following reference code logic
            click_url_obj = content.get('clickThroughUrl')
            url = click_url_obj.get('url') if click_url_obj else None
            
            # Extract and format publication date
            pub_date_raw = content.get('pubDate', '')
            pub_date = pub_date_raw[:10] if pub_date_raw else ''
            
            news_list.append({
                'id': content.get('id', ''),
                'title': content.get('title', 'No Title'),
                'summary': content.get('summary', ''),
                'pubDate': pub_date,
                'url': url,
                'tickers': [ticker.upper()]
            })
        
        print(f"[OK] {ticker} news ({len(news_list)} articles fetched)")
        return news_list
        
    except Exception as e:
        print(f"[X] {ticker} news (error: {e})")
        return []


def generate_ohlcv_chart(ticker: str, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
    """
    Generate an OHLCV candlestick chart with volume for Gemini Vision analysis.
    
    Args:
        ticker: Stock ticker symbol
        df: DataFrame with OHLCV data
        save_path: Optional custom path to save the chart
    
    Returns:
        Path to the saved chart image
    """
    if save_path is None:
        save_path = os.path.join(CHART_DIR, f"{ticker}_chart.png")
    
    # Create figure with two subplots (price and volume)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                    gridspec_kw={'height_ratios': [3, 1]},
                                    sharex=True)
    
    fig.suptitle(f'{ticker} - OHLCV Chart', fontsize=14, fontweight='bold')
    
    # Prepare data
    dates = df.index
    opens = df['Open']
    highs = df['High']
    lows = df['Low']
    closes = df['Close']
    volumes = df['Volume']
    
    # Color based on price movement
    colors = ['green' if c >= o else 'red' for c, o in zip(closes, opens)]
    
    # Plot candlesticks
    width = 0.6
    for i, (date, o, h, l, c, color) in enumerate(zip(dates, opens, highs, lows, closes, colors)):
        # Wick
        ax1.plot([i, i], [l, h], color=color, linewidth=1)
        # Body
        body_height = abs(c - o)
        body_bottom = min(o, c)
        ax1.bar(i, body_height, bottom=body_bottom, width=width, color=color, edgecolor=color)
    
    # Add moving averages
    if len(df) >= 20:
        ma20 = closes.rolling(window=20).mean()
        ax1.plot(range(len(dates)), ma20, color='blue', linewidth=1.5, label='MA20', alpha=0.7)
    if len(df) >= 50:
        ma50 = closes.rolling(window=50).mean()
        ax1.plot(range(len(dates)), ma50, color='orange', linewidth=1.5, label='MA50', alpha=0.7)
    
    ax1.set_ylabel('Price', fontsize=10)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Plot volume
    ax2.bar(range(len(dates)), volumes, color=colors, alpha=0.7, width=width)
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.set_xlabel('Date', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis with dates
    tick_positions = list(range(0, len(dates), max(1, len(dates) // 10)))
    tick_labels = [dates[i].strftime('%Y-%m-%d') for i in tick_positions]
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"[OK] Chart saved: {save_path}")
    return save_path


def generate_technical_chart(ticker: str, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
    """
    Generate a comprehensive technical analysis chart with candlesticks.
    Includes: Candlestick with MA 5/20/50, Volume with MA 5/20/50, RSI, MACD.
    
    Args:
        ticker: Stock ticker symbol
        df: DataFrame with OHLCV data
        save_path: Optional custom path to save the chart
    
    Returns:
        Path to the saved chart image
    """
    if save_path is None:
        save_path = os.path.join(CHART_DIR, f"{ticker}_technical.png")
    
    # Calculate indicators
    closes = df['Close']
    opens = df['Open']
    highs = df['High']
    lows = df['Low']
    volumes = df['Volume']
    
    # Price Moving Averages (5, 20, 50)
    ma5 = closes.rolling(window=5).mean() if len(df) >= 5 else closes
    ma20 = closes.rolling(window=20).mean() if len(df) >= 20 else closes
    ma50 = closes.rolling(window=50).mean() if len(df) >= 50 else closes
    
    # Volume Moving Averages (5, 20, 50)
    vol_ma5 = volumes.rolling(window=5).mean() if len(df) >= 5 else volumes
    vol_ma20 = volumes.rolling(window=20).mean() if len(df) >= 20 else volumes
    vol_ma50 = volumes.rolling(window=50).mean() if len(df) >= 50 else volumes
    
    # RSI
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    # Create figure with 4 subplots
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(16, 16),
                                              gridspec_kw={'height_ratios': [4, 1.5, 1, 1]},
                                              sharex=True)
    
    fig.suptitle(f'{ticker} - Technical Analysis (Candlestick)', fontsize=14, fontweight='bold')
    
    x = np.arange(len(df))
    
    # ===== CANDLESTICK CHART =====
    # Determine colors
    colors = ['#26A69A' if c >= o else '#EF5350' for c, o in zip(closes, opens)]  # Green / Red
    
    # Draw candlesticks
    width = 0.6
    for i in range(len(df)):
        o, h, l, c = opens.iloc[i], highs.iloc[i], lows.iloc[i], closes.iloc[i]
        color = colors[i]
        
        # Wick (high-low line)
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)
        
        # Body (open-close rectangle)
        body_bottom = min(o, c)
        body_height = abs(c - o)
        if body_height < 0.001:  # Doji - very small body
            body_height = 0.001
        ax1.bar(i, body_height, bottom=body_bottom, width=width, 
                color=color, edgecolor=color, linewidth=0.5)
    
    # Price Moving Averages
    ax1.plot(x, ma5, color='#2196F3', linewidth=1.2, label='MA5', alpha=0.9)
    ax1.plot(x, ma20, color='#FF9800', linewidth=1.2, label='MA20', alpha=0.9)
    ax1.plot(x, ma50, color='#9C27B0', linewidth=1.2, label='MA50', alpha=0.9)
    
    ax1.set_ylabel('Price', fontsize=10)
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(-1, len(df))
    
    # ===== VOLUME CHART WITH MAs =====
    ax2.bar(x, volumes, color=colors, alpha=0.6, width=width)
    ax2.plot(x, vol_ma5, color='#2196F3', linewidth=1, label='Vol MA5', alpha=0.9)
    ax2.plot(x, vol_ma20, color='#FF9800', linewidth=1, label='Vol MA20', alpha=0.9)
    ax2.plot(x, vol_ma50, color='#9C27B0', linewidth=1, label='Vol MA50', alpha=0.9)
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # ===== RSI =====
    ax3.plot(x, rsi, color='#7E57C2', linewidth=1.2)
    ax3.axhline(y=70, color='#EF5350', linestyle='--', alpha=0.7, linewidth=0.8)
    ax3.axhline(y=30, color='#26A69A', linestyle='--', alpha=0.7, linewidth=0.8)
    ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
    ax3.fill_between(x, 30, 70, alpha=0.05, color='gray')
    ax3.set_ylabel('RSI', fontsize=10)
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    # ===== MACD =====
    ax4.plot(x, macd_line, color='#2196F3', linewidth=1, label='MACD')
    ax4.plot(x, signal_line, color='#FF9800', linewidth=1, label='Signal')
    macd_colors = ['#26A69A' if h >= 0 else '#EF5350' for h in macd_hist]
    ax4.bar(x, macd_hist, color=macd_colors, alpha=0.6, width=width)
    ax4.axhline(y=0, color='gray', linestyle='-', alpha=0.5, linewidth=0.5)
    ax4.set_ylabel('MACD', fontsize=10)
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis with dates
    dates = df.index
    tick_count = min(12, len(dates))
    tick_positions = list(range(0, len(dates), max(1, len(dates) // tick_count)))
    tick_labels = [dates[i].strftime('%m-%d') for i in tick_positions]
    ax4.set_xticks(tick_positions)
    ax4.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
    ax4.set_xlabel('Date', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"[OK] Technical chart saved: {save_path}")
    return save_path


def clear_cache(ticker: Optional[str] = None):
    """
    Clear the data cache.
    
    Args:
        ticker: If provided, clear only this ticker's cache. Otherwise clear all.
    """
    global DATA_CACHE
    
    if ticker:
        keys_to_remove = [k for k in DATA_CACHE if k.startswith(ticker.upper())]
        for key in keys_to_remove:
            del DATA_CACHE[key]
        print(f"[OK] Cleared cache for {ticker}")
    else:
        DATA_CACHE = {}
        print("[OK] Cleared all cache")


def get_cache_info() -> dict:
    """Get information about current cache state."""
    return {
        "cached_keys": list(DATA_CACHE.keys()),
        "total_entries": len(DATA_CACHE),
        "total_rows": sum(len(df) for df in DATA_CACHE.values())
    }
