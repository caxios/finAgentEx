"""
SQLite Cache Module for FinAgentEx
Provides persistent caching with incremental updates for OHLCV, News, and Fundamentals data.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # OHLCV Cache Table - stores daily price data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv_cache (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            fetched_at TEXT,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    # News Cache Table - stores news articles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            ticker TEXT NOT NULL,
            news_id TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            pub_date TEXT,
            url TEXT,
            fetched_at TEXT,
            PRIMARY KEY (ticker, news_id)
        )
    """)
    
    # Fundamentals Cache Table - stores financial statement data as JSON
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals_cache (
            ticker TEXT NOT NULL,
            period_type TEXT NOT NULL,
            period TEXT NOT NULL,
            statement_type TEXT NOT NULL,
            data_json TEXT,
            fetched_at TEXT,
            PRIMARY KEY (ticker, period_type, period, statement_type)
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_ticker ON ohlcv_cache(ticker)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON ohlcv_cache(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker ON news_cache(ticker)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_pubdate ON news_cache(pub_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker ON fundamentals_cache(ticker)")
    
    conn.commit()
    conn.close()
    print(f"[Cache] Database initialized: {DB_PATH}")


# ============================================================
# OHLCV Cache Functions
# ============================================================

def get_ohlcv_last_date(ticker: str) -> Optional[str]:
    """Get the last cached date for a ticker's OHLCV data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT MAX(date) as last_date FROM ohlcv_cache WHERE ticker = ?
    """, (ticker.upper(),))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['last_date'] if result and result['last_date'] else None


def get_ohlcv_cache(ticker: str, start_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get cached OHLCV data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Optional start date filter (YYYY-MM-DD)
    
    Returns:
        DataFrame with OHLCV data
    """
    conn = get_connection()
    
    query = "SELECT date, open, high, low, close, volume FROM ohlcv_cache WHERE ticker = ?"
    params = [ticker.upper()]
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    query += " ORDER BY date"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # Rename columns to match yfinance format
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    return df


def save_ohlcv_cache(ticker: str, df: pd.DataFrame):
    """
    Save OHLCV data to cache.
    
    Args:
        ticker: Stock ticker symbol
        df: DataFrame with OHLCV data (index should be datetime)
    """
    if df is None or df.empty:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    ticker = ticker.upper()
    now = datetime.now().isoformat()
    
    for idx, row in df.iterrows():
        date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
        
        cursor.execute("""
            INSERT OR REPLACE INTO ohlcv_cache 
            (ticker, date, open, high, low, close, volume, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            date_str,
            float(row['Open']) if pd.notna(row['Open']) else None,
            float(row['High']) if pd.notna(row['High']) else None,
            float(row['Low']) if pd.notna(row['Low']) else None,
            float(row['Close']) if pd.notna(row['Close']) else None,
            float(row['Volume']) if pd.notna(row['Volume']) else None,
            now
        ))
    
    conn.commit()
    conn.close()
    print(f"[Cache] Saved {len(df)} OHLCV rows for {ticker}")


# ============================================================
# News Cache Functions
# ============================================================

def get_news_last_date(ticker: str) -> Optional[str]:
    """Get the last cached publication date for a ticker's news."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT MAX(pub_date) as last_date FROM news_cache WHERE ticker = ?
    """, (ticker.upper(),))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['last_date'] if result and result['last_date'] else None


def get_news_cache(ticker: str, limit: int = 50) -> List[Dict]:
    """
    Get cached news for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of news items to return
    
    Returns:
        List of news dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT news_id, title, summary, pub_date, url 
        FROM news_cache 
        WHERE ticker = ?
        ORDER BY pub_date DESC
        LIMIT ?
    """, (ticker.upper(), limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': row['news_id'],
            'title': row['title'],
            'summary': row['summary'],
            'pubDate': row['pub_date'],
            'url': row['url'],
            'tickers': [ticker.upper()]
        }
        for row in rows
    ]


def save_news_cache(ticker: str, news_list: List[Dict]):
    """
    Save news data to cache.
    
    Args:
        ticker: Stock ticker symbol
        news_list: List of news dictionaries
    """
    if not news_list:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    ticker = ticker.upper()
    now = datetime.now().isoformat()
    saved_count = 0
    
    for news in news_list:
        news_id = news.get('id', '')
        if not news_id:
            continue
        
        cursor.execute("""
            INSERT OR IGNORE INTO news_cache 
            (ticker, news_id, title, summary, pub_date, url, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            news_id,
            news.get('title', ''),
            news.get('summary', ''),
            news.get('pubDate', ''),
            news.get('url', ''),
            now
        ))
        saved_count += cursor.rowcount
    
    conn.commit()
    conn.close()
    print(f"[Cache] Saved {saved_count} new news items for {ticker}")


# ============================================================
# Fundamentals Cache Functions
# ============================================================

def get_fundamentals_cached_periods(ticker: str, period_type: str) -> List[str]:
    """Get list of cached periods for a ticker's fundamentals."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT period FROM fundamentals_cache 
        WHERE ticker = ? AND period_type = ?
        ORDER BY period DESC
    """, (ticker.upper(), period_type))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row['period'] for row in rows]


def get_fundamentals_cache(ticker: str, period_type: str) -> Dict[str, Any]:
    """
    Get cached fundamentals data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        period_type: 'annual' or 'quarterly'
    
    Returns:
        Dictionary with income, balance, cashflow data organized by period
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT period, statement_type, data_json 
        FROM fundamentals_cache 
        WHERE ticker = ? AND period_type = ?
    """, (ticker.upper(), period_type))
    
    rows = cursor.fetchall()
    conn.close()
    
    result = {
        'income': {},
        'balance': {},
        'cashflow': {}
    }
    
    for row in rows:
        statement_type = row['statement_type']
        period = row['period']
        data = json.loads(row['data_json']) if row['data_json'] else {}
        
        if statement_type in result:
            result[statement_type][period] = data
    
    return result


def save_fundamentals_cache(ticker: str, period_type: str, period: str, 
                            statement_type: str, data: Dict):
    """
    Save fundamentals data to cache.
    
    Args:
        ticker: Stock ticker symbol
        period_type: 'annual' or 'quarterly'
        period: Period label (e.g., '2024' or '2024Q3')
        statement_type: 'income', 'balance', or 'cashflow'
        data: Dictionary of statement data
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO fundamentals_cache 
        (ticker, period_type, period, statement_type, data_json, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ticker.upper(),
        period_type,
        period,
        statement_type,
        json.dumps(data),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()


def save_fundamentals_batch(ticker: str, period_type: str, 
                            income_data: List[Dict], 
                            balance_data: List[Dict], 
                            cashflow_data: List[Dict],
                            periods: List[str]):
    """
    Save all fundamentals data for a ticker in batch.
    
    Args:
        ticker: Stock ticker symbol
        period_type: 'annual' or 'quarterly'
        income_data: List of income statement rows
        balance_data: List of balance sheet rows
        cashflow_data: List of cash flow rows
        periods: List of period labels
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    ticker = ticker.upper()
    now = datetime.now().isoformat()
    
    # Convert list format to period-based format and save
    for period in periods:
        # Build data dict for each statement type
        for statement_type, data_list in [
            ('income', income_data),
            ('balance', balance_data),
            ('cashflow', cashflow_data)
        ]:
            period_data = {}
            for row in data_list:
                label = row.get('label', '')
                values = row.get('values', {})
                if period in values:
                    period_data[label] = values[period]
            
            if period_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO fundamentals_cache 
                    (ticker, period_type, period, statement_type, data_json, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ticker, period_type, period, statement_type, json.dumps(period_data), now))
    
    conn.commit()
    conn.close()
    print(f"[Cache] Saved fundamentals for {ticker} ({period_type}): {len(periods)} periods")


# ============================================================
# Utility Functions
# ============================================================

def clear_cache(ticker: Optional[str] = None, cache_type: Optional[str] = None):
    """
    Clear cache data.
    
    Args:
        ticker: If provided, clear only this ticker's cache
        cache_type: 'ohlcv', 'news', 'fundamentals', or None for all
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = []
    if cache_type == 'ohlcv':
        tables = ['ohlcv_cache']
    elif cache_type == 'news':
        tables = ['news_cache']
    elif cache_type == 'fundamentals':
        tables = ['fundamentals_cache']
    else:
        tables = ['ohlcv_cache', 'news_cache', 'fundamentals_cache']
    
    for table in tables:
        if ticker:
            cursor.execute(f"DELETE FROM {table} WHERE ticker = ?", (ticker.upper(),))
        else:
            cursor.execute(f"DELETE FROM {table}")
    
    conn.commit()
    conn.close()
    
    scope = f"for {ticker}" if ticker else "all"
    print(f"[Cache] Cleared {cache_type or 'all'} cache {scope}")


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the cache."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # OHLCV stats
    cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT ticker) as tickers FROM ohlcv_cache")
    row = cursor.fetchone()
    stats['ohlcv'] = {'rows': row['count'], 'tickers': row['tickers']}
    
    # News stats
    cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT ticker) as tickers FROM news_cache")
    row = cursor.fetchone()
    stats['news'] = {'rows': row['count'], 'tickers': row['tickers']}
    
    # Fundamentals stats
    cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT ticker) as tickers FROM fundamentals_cache")
    row = cursor.fetchone()
    stats['fundamentals'] = {'rows': row['count'], 'tickers': row['tickers']}
    
    conn.close()
    
    return stats


# Initialize database on module import
init_db()
