"""
Agent Definitions for Multi-Agent Stock Analysis System
This module defines individual agent tools and configurations.
"""

from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import Tool
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Dict, Optional

load_dotenv()

# Import data tools
from data_tools import (
    fetch_period_data,
    fetch_single_ticker_data,
    fetch_news_for_ticker,
    fetch_intraday_data,
    generate_technical_chart,
    generate_ohlcv_chart,
    DATA_CACHE,
    get_cache_info
)

# --- Define the shared model ---
model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL', 'gemini-2.5-flash-lite'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)


# =============================================
# AGENT 1: NEWS AGENT TOOLS (yfinance)
# =============================================

@tool('fetch_stock_news', description='Fetches recent news for a stock ticker using yfinance. Returns list of news articles with title, summary, pubDate, and url.')
def fetch_stock_news(ticker: str, count: int = 10) -> List[dict]:
    """Fetch news using yfinance following Reference Code B pattern."""
    print(f'    [News Agent] Fetching news for {ticker}...')
    return fetch_news_for_ticker(ticker, count)


# =============================================
# AGENT 3: DATA AGENT TOOLS
# =============================================

@tool('fetch_ohlcv_data', description='Fetches OHLCV (Open, High, Low, Close, Volume) data for a stock ticker. Data is cached for efficiency.')
def fetch_ohlcv_data(ticker: str, period: str = "3mo") -> dict:
    """Fetch and cache OHLCV data following Reference Code A pattern."""
    print(f'    [Data Agent] Fetching OHLCV for {ticker}...')
    df = fetch_single_ticker_data(ticker, period)
    
    if df is None or df.empty:
        return {"error": f"No data available for {ticker}"}
    
    return {
        "ticker": ticker,
        "period": period,
        "rows": len(df),
        "start_date": str(df.index[0].date()),
        "end_date": str(df.index[-1].date()),
        "current_price": round(float(df['Close'].iloc[-1]), 2),
        "period_high": round(float(df['High'].max()), 2),
        "period_low": round(float(df['Low'].min()), 2),
        "avg_volume": round(float(df['Volume'].mean()), 0)
    }


@tool('fetch_intraday', description='Fetches 5-minute intraday data for a stock on a specific date.')
def fetch_intraday(ticker: str, date: str) -> dict:
    """Fetch intraday data following reference pattern."""
    print(f'    [Data Agent] Fetching intraday for {ticker} on {date}...')
    df = fetch_intraday_data(ticker, date)
    
    if df is None or df.empty:
        return {"error": f"No intraday data for {ticker} on {date}"}
    
    return {
        "ticker": ticker,
        "date": date,
        "bars": len(df),
        "open_price": round(float(df['Open'].iloc[0]), 2),
        "close_price": round(float(df['Close'].iloc[-1]), 2),
        "high": round(float(df['High'].max()), 2),
        "low": round(float(df['Low'].min()), 2),
        "total_volume": int(df['Volume'].sum())
    }


@tool('generate_chart', description='Generates a technical analysis chart for a stock and saves it as an image.')
def generate_chart(ticker: str, period: str = "3mo") -> str:
    """Generate technical chart for vision analysis."""
    print(f'    [Data Agent] Generating chart for {ticker}...')
    df = fetch_single_ticker_data(ticker, period)
    
    if df is None or df.empty:
        return f"Cannot generate chart: no data for {ticker}"
    
    chart_path = generate_technical_chart(ticker, df)
    return chart_path


@tool('get_current_price', description='Gets the current stock price for a ticker.')
def get_current_price(ticker: str) -> float:
    """Get current stock price."""
    print(f'    [Data Agent] Fetching current price for {ticker}...')
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    if not hist.empty:
        return round(float(hist['Close'].iloc[-1]), 2)
    return 0.0


@tool('get_cache_status', description='Gets the current status of the data cache.')
def get_cache_status() -> dict:
    """Get cache information."""
    return get_cache_info()


# =============================================
# AGENT 4: TECHNICAL ANALYSIS PROMPTS
# =============================================

TECH_ANALYSIS_SYSTEM_PROMPT = """You are an expert technical analyst specializing in chart pattern recognition and indicator analysis.

Your analysis should cover:
1. **Trend Direction**: Identify the primary trend (bullish, bearish, sideways)
2. **Support/Resistance**: Key price levels where the stock tends to bounce or struggle
3. **Moving Averages**: Position relative to MA20 and MA50
4. **RSI Analysis**: Overbought (>70) or Oversold (<30) conditions
5. **MACD Analysis**: Bullish/bearish crossovers and momentum
6. **Volume Analysis**: Confirmation of price moves
7. **Chart Patterns**: Head & Shoulders, Double Top/Bottom, Triangles, Flags, etc.

Provide specific price levels and actionable insights. End with a clear BUY/SELL/HOLD recommendation."""


# =============================================
# AGENT 5: SENTIMENT ANALYSIS PROMPTS
# =============================================

SENTIMENT_ANALYSIS_SYSTEM_PROMPT = """You are a financial sentiment analyst specializing in analyzing news and social media content.

Your analysis should cover:
1. **Overall Sentiment**: POSITIVE, NEGATIVE, NEUTRAL, or MIXED
2. **Sentiment Drivers**: What's causing the current sentiment
3. **Key Topics**: Main themes being discussed
4. **News Impact**: How news might affect short-term price
5. **Social Buzz**: What retail investors are saying
6. **Risk Signals**: Any warning signs in the sentiment data

Be objective and data-driven. Separate facts from speculation."""


# =============================================
# AGENT 6: STRATEGY PROMPTS  
# =============================================

STRATEGY_SYSTEM_PROMPT = """You are a Senior Equity Research Analyst specializing in quantitative and qualitative stock evaluation. Your role is to provide a detailed research report based on the provided intelligence. 

Your analysis must follow this structured framework:

1. **Sentiment Analysis**: 
   - Synthesize news, social signals, and institutional reports.
   - Determine if the prevailing narrative is Bullish, Bearish, or Neutral and why.

2. **Technical Evaluation**: 
   - Analyze the provided chart patterns, indicators, and price action trends.
   - Identify key support/resistance levels and trend strength.

3. **Unified Momentum Assessment**: 
   - Combine Sentiment and Technical findings to evaluate the stock's current momentum.
   - Explain how these two factors are reinforcing or contradicting each other.

4. **Risk Factors & Catalyst Assessment**: 
   - Detail specific internal or external risks (e.g., macro shifts, earnings uncertainty, regulatory issues).
   - Identify potential "thesis-breakers" that could invalidate the current analysis.

5. **Final Verdict & Quantitative Scoring**: 
   - **Score (0-100)**: Provide a numerical confidence score (0 = Strong Sell conviction, 100 = Strong Buy conviction).
   - **Recommendation**: Clearly state [BUY], [HOLD], or [SELL].

Tone & Style:
- Be objective, analytical, and data-driven.
- Provide specific reasoning for each section rather than generic statements.
- Ensure the 'Unified Momentum' section explains the synergy between market mood and price action."""


# =============================================
# LEGACY COMPATIBILITY
# =============================================

# For backward compatibility with existing code
@tool('get_stock_price', description='A function that returns the current stock price based on a ticker symbol.')
def get_stock_price(ticker: str) -> float:
    """Legacy function for current price."""
    return get_current_price(ticker)


@tool('get_historical_stock_price', description='A function that returns the stock price over time based on a ticker symbol and a start and end date.')
def get_historical_stock_price(ticker: str, start_date: str, end_date: str) -> dict:
    """Legacy function for historical data."""
    print('    [Legacy] Fetching history...')
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    return {
        "ticker": ticker,
        "rows": len(hist),
        "data": hist['Close'].to_dict() if not hist.empty else {}
    }


# =============================================
# REACT AGENTS (Optional - for more complex scenarios)
# =============================================

# Data Agent with tools
data_agent = create_react_agent(
    model=model,
    tools=[fetch_ohlcv_data, fetch_intraday, generate_chart, get_current_price, get_cache_status],
)

# News Agent with tools
news_agent = create_react_agent(
    model=model,
    tools=[fetch_stock_news],
)

# Combined analysis agent
analysis_agent = create_react_agent(
    model=model,
    tools=[fetch_ohlcv_data, fetch_stock_news, generate_chart, get_current_price],
)


# =============================================
# EXPORTS
# =============================================

__all__ = [
    # Tools
    'fetch_stock_news',
    'fetch_ohlcv_data', 
    'fetch_intraday',
    'generate_chart',
    'get_current_price',
    'get_cache_status',
    
    # Legacy tools
    'get_stock_price',
    'get_historical_stock_price',
    
    # Agents
    'data_agent',
    'news_agent',
    'analysis_agent',
    
    # Prompts
    'TECH_ANALYSIS_SYSTEM_PROMPT',
    'SENTIMENT_ANALYSIS_SYSTEM_PROMPT',
    'STRATEGY_SYSTEM_PROMPT',
    
    # Model
    'model',
]
