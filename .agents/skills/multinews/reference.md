```python
"""
News data fetching and caching for Stock Dashboard
"""
import json
import os
from typing import List, Dict, Set
from datetime import datetime
import yfinance as yf

NEWS_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'newsdata.json')

# =============================================================================
# Cache Operations
# =============================================================================

def load_news_cache() -> List[dict]:
    """Load cached news from newsdata.json"""
    if os.path.exists(NEWS_CACHE_FILE):
        try:
            with open(NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_news_cache(news_list: List[dict]) -> None:
    """Save news to newsdata.json"""
    try:
        with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[News] Failed to save cache: {e}")


# =============================================================================
# News Fetching
# =============================================================================

def get_unique_tickers(ticker_groups: List[dict]) -> Set[str]:
    """Extract unique tickers from all categories"""
    tickers = set()
    for group in ticker_groups:
        for ticker in group.get('tickers', []):
            tickers.add(ticker)
    return tickers


def fetch_news_for_ticker(ticker: str, count: int = 10) -> List[dict]:
    """Fetch news for a single ticker"""
    try:
        data = yf.Ticker(ticker).get_news(count=count)
        news_list = []
        
        for item in data[:count]:
            if 'content' not in item:
                continue
            
            content = item['content']
            url = None
            if content.get('clickThroughUrl'):
                url = content['clickThroughUrl'].get('url')
            
            pub_date = content.get('pubDate', '')[:10] if content.get('pubDate') else ''
            
            news_list.append({
                'id': content.get('id', ''),
                'title': content.get('title', 'No Title'),
                'summary': content.get('summary', ''),
                'pubDate': pub_date,
                'url': url,
                'tickers': [ticker]  # Track which ticker this news came from
            })
        
        return news_list
    except Exception as e:
        print(f"[News] Failed to fetch news for {ticker}: {e}")
        return []


def fetch_all_news(ticker_groups: List[dict], count_per_ticker: int = 10) -> List[dict]:
    """
    Fetch news for all tickers, merge with cache, deduplicate by ID.
    Returns updated news list sorted by date (newest first).
    """
    # Load existing cache
    cached_news = load_news_cache()
    existing_ids = {news['id'] for news in cached_news}
    
    # Build a map of id -> news item for merging tickers
    news_map: Dict[str, dict] = {news['id']: news for news in cached_news}
    
    # Get unique tickers
    tickers = get_unique_tickers(ticker_groups)
    total = len(tickers)
    
    print(f"[News] Fetching news for {total} tickers...")
    
    new_count = 0
    for i, ticker in enumerate(tickers, 1):
        print(f"[News] ({i}/{total}) Fetching {ticker}...")
        
        ticker_news = fetch_news_for_ticker(ticker, count_per_ticker)
        
        for news in ticker_news:
            news_id = news['id']
            
            if news_id in news_map:
                # News already exists, add ticker to list if not present
                if ticker not in news_map[news_id]['tickers']:
                    news_map[news_id]['tickers'].append(ticker)
            else:
                # New news item
                news_map[news_id] = news
                new_count += 1
    
    print(f"[News] Added {new_count} new articles")
    
    # Convert map back to list and sort by date (newest first)
    all_news = list(news_map.values())
    all_news.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    
    # Save to cache
    save_news_cache(all_news)
    
    return all_news


def get_available_dates(news_list: List[dict]) -> List[str]:
    """Get list of unique dates from news, sorted newest first"""
    dates = set()
    for news in news_list:
        if news.get('pubDate'):
            dates.add(news['pubDate'])
    return sorted(list(dates), reverse=True)


def filter_news_by_date(news_list: List[dict], date: str) -> List[dict]:
    """Filter news by specific date"""
    if not date or date == 'all':
        return news_list
    return [news for news in news_list if news.get('pubDate') == date]

```