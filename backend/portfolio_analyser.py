"""
Portfolio Analyser
Isolated logic for fetching data, normalizing returns, and calculating indices.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

def fetch_and_normalize_data(tickers: List[str], period: str = "6mo") -> Dict[str, Any]:
    """
    Fetch OHLCV data for multiple tickers, align timestamps, and normalize to % returns.
    """
    if not tickers:
        return {"error": "No tickers provided"}
    
    # Clean tickers
    tickers = [t.upper().strip() for t in tickers]
    
    # Download data in batch
    try:
        # yfinance batch download
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, progress=False)
    except Exception as e:
        return {"error": f"Failed to download data: {e}"}
    
    # Handle single ticker case (structure is different)
    if len(tickers) == 1:
        ticker = tickers[0]
        close_data = pd.DataFrame({ticker: data['Close']})
    else:
        # Extract Close prices for all tickers
        # data structure is (Date, (Ticker, OHLCV...)) or MultiIndex columns
        try:
            # If MultiIndex columns level 0 is Ticker, level 1 is Price Type
            close_data = data.xs('Close', level=1, axis=1)
        except KeyError:
            # Maybe flat structure if columns are just tickers?
            # Or data might be (Date, Ticker) if checking 'Close' column?
            # Let's try safer extraction
            close_dict = {}
            for t in tickers:
                if t in data.columns:
                     close_dict[t] = data[t]
                elif (t, 'Close') in data.columns:
                     close_dict[t] = data[(t, 'Close')]
            close_data = pd.DataFrame(close_dict)
            
    # Drop rows where ALL columns are NaN (weekends/holidays common to all)
    close_data.dropna(how='all', inplace=True)
    
    # Fill remaining NaNs (e.g. if one stock has missing data) using ffill then bfill
    close_data.fillna(method='ffill', inplace=True)
    close_data.fillna(method='bfill', inplace=True)
    
    if close_data.empty:
        return {"error": "No data found for the selected period"}
    
    # --- Normalization Logic ---
    # Formula: (Price_t - Price_0) / Price_0 * 100
    normalized_df = pd.DataFrame()
    
    for ticker in close_data.columns:
        start_price = close_data[ticker].iloc[0]
        if start_price and start_price > 0:
            normalized_df[ticker] = ((close_data[ticker] - start_price) / start_price) * 100
        else:
            normalized_df[ticker] = 0.0
            
    # --- Equal-Weighted Index Calculation ---
    # Average of all normalized returns at each timestamp
    normalized_df['Category Index'] = normalized_df.mean(axis=1)
    
    # Prepare Result for JSON
    timestamps = normalized_df.index.strftime('%Y-%m-%d').tolist()
    
    result_data = {
        "timestamps": timestamps,
        "stocks": {},
        "index": {
            "name": "Category Index",
            "data": normalized_df['Category Index'].round(2).tolist(),
            "final": round(normalized_df['Category Index'].iloc[-1], 2)
        }
    }
    
    # Assign colors (simple rotation)
    colors = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", 
        "#EC4899", "#6366F1", "#14B8A6", "#F97316", "#06B6D4"
    ]
    
    for idx, ticker in enumerate(tickers):
        if ticker in normalized_df.columns:
            series = normalized_df[ticker].round(2).tolist()
            result_data["stocks"][ticker] = {
                "data": series,
                "final": series[-1] if series else 0,
                "color": colors[idx % len(colors)]
            }
            
    return result_data
