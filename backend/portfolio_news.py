"""
Portfolio News Manager
Fetches and aggregates news for all tickers in a portfolio category.
Implements source tagging (related_tickers) and deduplication.
"""

from typing import List, Dict, Set
from datetime import datetime
from backend import portfolio_db
from typing import List, Dict, Set
from datetime import datetime
from backend import portfolio_db
from data_tools import fetch_news_for_ticker, fetch_news_for_date

def fetch_portfolio_news(category_id: int, count_per_ticker: int = 10, date: str = None) -> List[Dict]:
    """
    Fetch news for all tickers in the category, merge, and deduplicate.
    
    Args:
        category_id: ID of the portfolio category
        count_per_ticker: Number of news items to fetch per ticker
        date: Optional date filter (YYYY-MM-DD)
        
    Returns:
        List of news items sorted by date (newest first)
    """
    # 1. Get tickers from DB
    tickers = portfolio_db.get_stocks(category_id)
    if not tickers:
        return []

    # 2. Fetch news for each ticker
    all_news_map: Dict[str, Dict] = {}  # Map ID -> News Item
    
    # We need to know which tickers are in the portfolio to tag them efficiently
    portfolio_tickers_set = set(tickers)
    
    for ticker in tickers:
        if date:
            # Date specific fetch - Fetch 5 items as requested
            ticker_news = fetch_news_for_date(ticker, date, count=5)
        else:
            # fetch_news_for_ticker returns list of dicts with 'tickers': [ticker]
            ticker_news = fetch_news_for_ticker(ticker, count=count_per_ticker)
        
        for item in ticker_news:
            news_id = item['id']
            
            if news_id in all_news_map:
                # Deduplication: Merge 'tickers' list
                existing_item = all_news_map[news_id]
                if ticker not in existing_item['tickers']:
                    existing_item['tickers'].append(ticker)
            else:
                # New item
                all_news_map[news_id] = item

    # 3. Advanced Tagging (Optional step mentioned in SKILL.md)
    # Check if other portfolio tickers appear in title/summary but weren't caught by basic search
    # (This is computationally expensive if list is huge, but fine for personal portfolio)
    # Optimization: Do this only for items that have only 1 ticker so far? Or all?
    # Let's do a simple pass.
    
    processed_news = list(all_news_map.values())
    
    for item in processed_news:
        title_summary = (item['title'] + " " + item['summary']).upper()
        current_tags = set(item['tickers'])
        
        for p_ticker in portfolio_tickers_set:
            if p_ticker not in current_tags:
                # Simple keyword matching: check if TICKER appears as a whole word
                # (Crude check, but effective enough for now)
                # To be safer, we'd use regex bounds \bTICKER\b, but let's keep it simple
                 if f" {p_ticker} " in f" {title_summary} ": # Surround with spaces to avoid substring match
                     item['tickers'].append(p_ticker)
                     
    # 4. Sort by Date
    # pubDate format from yfinance is usually ISO or similar, data_tools formats it as YYYY-MM-DD
    processed_news.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    
    return processed_news

def get_portfolio_news_dates(news_list: List[Dict]) -> List[str]:
    """Extract unique dates from news list"""
    dates = set()
    for item in news_list:
        if item.get('pubDate'):
            dates.add(item['pubDate'])
    return sorted(list(dates), reverse=True)
