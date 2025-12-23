import yfinance as yf
import pandas as pd
import os

# Create charts directory if not exists
os.makedirs("modules/charts", exist_ok=True)

def fetch_market_data(ticker: str):
    """
    Fetches OHLC data and recent news for the ticker.
    """
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    
    # Get 1 month of history for the chart
    hist = stock.history(period="1mo")
    
    # News is now handled by the NewsAgent via Google Search Grounding
    news = []
    
    return hist, news

def analyze_price_patterns(hist: pd.DataFrame):
    """
    Analyzes price data for patterns: volatility, trend, and recent moves.
    Returns a dictionary of analysis results.
    """
    print(f"Analyzing price patterns...")
    
    # Calculate simple metrics
    current_price = hist['Close'].iloc[-1] and hist['Close'].iloc[-1]
    start_price = hist['Close'].iloc[0]
    
    # Trend
    price_change = current_price - start_price
    pct_change = (price_change / start_price) * 100
    trend = "Up" if price_change > 0 else "Down"
    
    # Volatility (Standard Deviation of daily returns)
    daily_returns = hist['Close'].pct_change().dropna()
    volatility = daily_returns.std() * 100 # as percentage
    
    # Recent Movement (Last 3 days)
    last_3_days = hist['Close'].tail(3)
    recent_trend_desc = "Consolidating"
    if last_3_days.is_monotonic_increasing:
        recent_trend_desc = "Strongly Rising"
    elif last_3_days.is_monotonic_decreasing:
        recent_trend_desc = "Strongly Falling"
        
    analysis = {
        "current_price": round(current_price, 2),
        "period_change_pct": round(pct_change, 2),
        "trend": trend,
        "volatility_score": round(volatility, 2), # Higher is more volatile
        "recent_pattern": recent_trend_desc,
        "history_summary": hist['Close'].tail(5).to_dict() # Give last 5 points for context
    }
    
    print(f"--> Patterns Detected: {trend} ({pct_change}%), Volatility: {volatility:.2f}, Recent: {recent_trend_desc}")
    return analysis

def format_news(news: list):
    """
    Formats the news list into a string summary.
    """
    summary = ""
    for item in news[:5]: # Top 5 news
        # Handle potential missing keys gracefully
        title = item.get('title', item.get('content', {}).get('title', 'No Title'))
        pub_time = item.get('providerPublishTime', 'N/A')
        summary += f"- [{pub_time}] {title}\n"
    return summary
