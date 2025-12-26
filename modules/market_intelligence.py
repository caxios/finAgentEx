from google import genai
from google.genai import types
import yfinance as yf
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def fetch_market_data(ticker: str, period: str = "1mo"):
    """
    Fetches OHLC data via yfinance and News via Google Search Grounding.
    """
    print(f"Fetching data for {ticker} ({period})...")
    
    # 1. Get Price History (yfinance is still best for this)
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    
    # 2. Get News via Google Search Grounding
    print(f"Searching news for {ticker} with Google Grounding...")
    
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    grounding_config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0.0 # Strict factual search
    )
    
    prompt = f"""
    Find the latest important financial news, quarterly earnings reports, and major events for {ticker} 
    from the last 3 months. Summarize the key points that would affect the stock price.
    Also mention if there are any upcoming earnings or fed decisions relevant to it.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=grounding_config,
    )
    
    # The response.text contains the grounded summary with citations
    news_summary = response.text
    
    return hist, news_summary

def analyze_price_patterns(hist: pd.DataFrame):
    """
    Analyzes price data for patterns: volatility, trend, and recent moves.
    Returns a dictionary of analysis results.
    """
    print(f"Analyzing price patterns...")
    
    # Calculate simple metrics
    current_price = hist['Close'].iloc[-1]
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
