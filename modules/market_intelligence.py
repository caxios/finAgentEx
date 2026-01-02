from google import genai
from google.genai import types
import yfinance as yf
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))


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


def calculate_technical_indicators(hist: pd.DataFrame) -> dict:
    """
    Calculate technical indicators: MACD, RSI, Moving Averages, OBV, ADL.
    Includes both price-based and volume-based indicators for comprehensive analysis.
    """
    close = hist['Close']
    high = hist['High']
    low = hist['Low']
    volume = hist['Volume']
    
    # Moving Averages
    ma_5 = close.rolling(window=5).mean().iloc[-1] if len(close) >= 5 else close.mean()
    ma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else close.mean()
    ma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else close.mean()
    
    # MACD (12-day EMA - 26-day EMA)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    
    current_macd = macd_line.iloc[-1] if len(macd_line) > 0 else 0
    current_signal = signal_line.iloc[-1] if len(signal_line) > 0 else 0
    current_histogram = macd_histogram.iloc[-1] if len(macd_histogram) > 0 else 0
    
    # MACD Signal
    if current_macd > current_signal:
        macd_signal = "BULLISH" if current_histogram > 0 else "BULLISH_WEAKENING"
    else:
        macd_signal = "BEARISH" if current_histogram < 0 else "BEARISH_WEAKENING"
    
    # RSI (14-day)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50
    
    # RSI Signal with divergence detection
    if current_rsi > 70:
        rsi_signal = "OVERBOUGHT"
    elif current_rsi > 60:
        rsi_signal = "BULLISH"
    elif current_rsi < 30:
        rsi_signal = "OVERSOLD"
    elif current_rsi < 40:
        rsi_signal = "BEARISH"
    else:
        rsi_signal = "NEUTRAL"
    
    # OBV (On-Balance Volume)
    # OBV adds volume on up days and subtracts on down days
    obv = np.zeros(len(close))
    obv[0] = volume.iloc[0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv[i] = obv[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv[i] = obv[i-1] - volume.iloc[i]
        else:
            obv[i] = obv[i-1]
    
    current_obv = obv[-1]
    obv_ma = np.mean(obv[-20:]) if len(obv) >= 20 else np.mean(obv)
    
    # OBV Trend - compare current OBV to its moving average
    if current_obv > obv_ma * 1.05:
        obv_trend = "ACCUMULATION"  # Buying pressure
    elif current_obv < obv_ma * 0.95:
        obv_trend = "DISTRIBUTION"  # Selling pressure
    else:
        obv_trend = "NEUTRAL"
    
    # ADL (Accumulation/Distribution Line)
    # Money Flow Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
    # ADL = Previous ADL + (MFM * Volume)
    high_low_diff = high - low
    # Avoid division by zero
    high_low_diff = high_low_diff.replace(0, 0.0001)
    
    mfm = ((close - low) - (high - close)) / high_low_diff
    mfv = mfm * volume  # Money Flow Volume
    adl = mfv.cumsum()
    
    current_adl = adl.iloc[-1] if len(adl) > 0 else 0
    adl_ma = adl.rolling(window=20).mean().iloc[-1] if len(adl) >= 20 else adl.mean()
    
    # ADL Trend
    if current_adl > adl_ma * 1.05:
        adl_trend = "ACCUMULATION"  # Smart money buying
    elif current_adl < adl_ma * 0.95:
        adl_trend = "DISTRIBUTION"  # Smart money selling
    else:
        adl_trend = "NEUTRAL"
    
    # Volume-Price Confirmation
    price_trend_up = close.iloc[-1] > close.iloc[-5] if len(close) >= 5 else True
    volume_confirms = (obv_trend == "ACCUMULATION" and price_trend_up) or \
                      (obv_trend == "DISTRIBUTION" and not price_trend_up)
    
    # Trend based on MAs
    current_price = close.iloc[-1]
    if current_price > ma_20 > ma_50:
        ma_trend = "STRONG_UPTREND"
    elif current_price > ma_20:
        ma_trend = "UPTREND"
    elif current_price < ma_20 < ma_50:
        ma_trend = "STRONG_DOWNTREND"
    elif current_price < ma_20:
        ma_trend = "DOWNTREND"
    else:
        ma_trend = "SIDEWAYS"
    
    return {
        "macd": {
            "value": round(current_macd, 4),
            "signal_line": round(current_signal, 4),
            "histogram": round(current_histogram, 4),
            "interpretation": macd_signal
        },
        "rsi": {
            "value": round(current_rsi, 2),
            "interpretation": rsi_signal
        },
        "obv": {
            "value": round(current_obv, 0),
            "ma_20": round(obv_ma, 0),
            "interpretation": obv_trend
        },
        "adl": {
            "value": round(current_adl, 0),
            "ma_20": round(adl_ma, 0),
            "interpretation": adl_trend
        },
        "volume_analysis": {
            "obv_trend": obv_trend,
            "adl_trend": adl_trend,
            "volume_confirms_price": volume_confirms
        },
        "moving_averages": {
            "ma_5": round(ma_5, 2),
            "ma_20": round(ma_20, 2),
            "ma_50": round(ma_50, 2),
            "trend": ma_trend
        }
    }


def analyze_price_patterns(hist: pd.DataFrame) -> dict:
    """
    Analyzes price data for patterns: volatility, trend, and recent moves.
    Returns a dictionary of analysis results.
    """
    print(f"Analyzing price patterns...")
    
    if len(hist) == 0:
        return {
            "current_price": 0,
            "period_change_pct": 0,
            "trend": "Unknown",
            "volatility_score": 0,
            "recent_pattern": "No data",
            "history_summary": {}
        }
    
    # Calculate simple metrics
    current_price = hist['Close'].iloc[-1]
    start_price = hist['Close'].iloc[0]
    
    # Trend
    price_change = current_price - start_price
    pct_change = (price_change / start_price) * 100
    trend = "Up" if price_change > 0 else "Down"
    
    # Volatility (Standard Deviation of daily returns)
    daily_returns = hist['Close'].pct_change().dropna()
    volatility = daily_returns.std() * 100 if len(daily_returns) > 0 else 0  # as percentage
    
    # Recent Movement (Last 3 days)
    last_3_days = hist['Close'].tail(3)
    recent_trend_desc = "Consolidating"
    if len(last_3_days) >= 3:
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
    
    print(f"--> Patterns Detected: {trend} ({pct_change:.2f}%), Volatility: {volatility:.2f}, Recent: {recent_trend_desc}")
    return analysis


def analyze_multi_timeframe(ticker: str) -> dict:
    """
    Analyze price patterns across short, medium, and long term timeframes.
    Returns comprehensive multi-timeframe analysis with technical indicators.
    """
    print(f"Performing multi-timeframe analysis for {ticker}...")
    
    stock = yf.Ticker(ticker)
    
    # Fetch data for different timeframes
    short_term_hist = stock.history(period="5d")   # 5 days - short term
    medium_term_hist = stock.history(period="1mo") # 1 month - medium term  
    long_term_hist = stock.history(period="3mo")   # 3 months - long term
    
    # Analyze each timeframe
    short_term = analyze_price_patterns(short_term_hist)
    short_term["timeframe"] = "short_term (5 days)"
    
    medium_term = analyze_price_patterns(medium_term_hist)
    medium_term["timeframe"] = "medium_term (1 month)"
    
    long_term = analyze_price_patterns(long_term_hist)
    long_term["timeframe"] = "long_term (3 months)"
    
    # Calculate technical indicators from longer-term data
    indicators_hist = stock.history(period="6mo")  # Need more data for accurate indicators
    technical_indicators = calculate_technical_indicators(indicators_hist)
    
    # Determine overall trend alignment
    trends = [short_term["trend"], medium_term["trend"], long_term["trend"]]
    if all(t == "Up" for t in trends):
        trend_alignment = "STRONGLY_BULLISH"
    elif all(t == "Down" for t in trends):
        trend_alignment = "STRONGLY_BEARISH"
    elif trends.count("Up") >= 2:
        trend_alignment = "MODERATELY_BULLISH"
    elif trends.count("Down") >= 2:
        trend_alignment = "MODERATELY_BEARISH"
    else:
        trend_alignment = "MIXED"
    
    return {
        "short_term": short_term,
        "medium_term": medium_term,
        "long_term": long_term,
        "technical_indicators": technical_indicators,
        "trend_alignment": trend_alignment,
        "current_price": short_term["current_price"]
    }
