from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)


def low_level_reflection(news_summary: str, price_trend: str) -> str:
    """
    Basic low-level reflection: Analyze correlation between news and price.
    """
    prompt = f"""
    Perform a Low-Level Reflection on the following data:
    
    Market News Summary:
    {news_summary}
    
    Price Trend:
    {price_trend}
    
    Question: Why did the price move (or not move) in this way given the news? 
    Is there a direct correlation?
    """
    res = model.invoke(prompt)
    return res.content


def low_level_reflection_multi_timeframe(
    news_summary: str, 
    price_data: dict
) -> dict:
    """
    Enhanced low-level reflection with multi-timeframe analysis.
    Analyzes price-news correlation across short, medium, and long term.
    
    Args:
        news_summary: Summary of recent news
        price_data: Multi-timeframe price analysis from market_intelligence
    
    Returns:
        Dictionary with timeframe-specific insights and combined analysis
    """
    print("Performing multi-timeframe low-level reflection...")
    
    short_term = price_data.get("short_term", {})
    medium_term = price_data.get("medium_term", {})
    long_term = price_data.get("long_term", {})
    indicators = price_data.get("technical_indicators", {})
    
    prompt = f"""
You are a financial analyst performing Low-Level Reflection on market data.
Analyze the correlation between news and price movements across different timeframes.

=== MARKET NEWS ===
{news_summary}

=== PRICE ANALYSIS ===

SHORT-TERM (5 days):
- Trend: {short_term.get('trend', 'N/A')}
- Change: {short_term.get('period_change_pct', 'N/A')}%
- Volatility: {short_term.get('volatility_score', 'N/A')}
- Recent Pattern: {short_term.get('recent_pattern', 'N/A')}

MEDIUM-TERM (1 month):
- Trend: {medium_term.get('trend', 'N/A')}
- Change: {medium_term.get('period_change_pct', 'N/A')}%
- Volatility: {medium_term.get('volatility_score', 'N/A')}

LONG-TERM (3 months):
- Trend: {long_term.get('trend', 'N/A')}
- Change: {long_term.get('period_change_pct', 'N/A')}%
- Volatility: {long_term.get('volatility_score', 'N/A')}

=== TECHNICAL INDICATORS ===
- MACD: {indicators.get('macd', {}).get('interpretation', 'N/A')}
- RSI: {indicators.get('rsi', {}).get('value', 'N/A')} ({indicators.get('rsi', {}).get('interpretation', 'N/A')})
- MA Trend: {indicators.get('moving_averages', {}).get('trend', 'N/A')}

=== ANALYSIS REQUIRED ===

Provide your analysis in the following structure:

1. SHORT-TERM IMPACT: How does the news explain the 5-day price movement? What is the immediate market reaction?

2. MEDIUM-TERM IMPACT: How might this news affect the stock over the next month? Are there delayed effects?

3. LONG-TERM IMPACT: What are the structural implications for the company's 3-month outlook?

4. CORRELATION ASSESSMENT: Rate the news-price correlation (STRONG/MODERATE/WEAK/NONE) and explain why.

5. KEY INSIGHT: What is the single most important takeaway for making a trading decision?
"""
    
    res = model.invoke(prompt)
    
    return {
        "analysis": res.content,
        "short_term_trend": short_term.get('trend', 'Unknown'),
        "medium_term_trend": medium_term.get('trend', 'Unknown'),
        "long_term_trend": long_term.get('trend', 'Unknown'),
        "technical_signals": {
            "macd": indicators.get('macd', {}).get('interpretation', 'N/A'),
            "rsi": indicators.get('rsi', {}).get('interpretation', 'N/A'),
            "ma_trend": indicators.get('moving_averages', {}).get('trend', 'N/A')
        }
    }


def high_level_reflection(past_decisions: list) -> str:
    """
    Review past decisions. 
    (For this MVP, we analyze the retrieved memories of past actions).
    """
    if not past_decisions:
        return "No past decisions available for reflection."

    # Format past decisions - handle both dict and string formats
    past_text_parts = []
    for decision in past_decisions:
        if isinstance(decision, dict):
            content = decision.get("content", str(decision))
            metadata = decision.get("metadata", {})
            source = decision.get("source", "unknown")
            past_text_parts.append(f"[Source: {source}]\n{content}")
        else:
            past_text_parts.append(str(decision))
    
    past_text = "\n---\n".join(past_text_parts)
    
    prompt = f"""
You are a trading AI performing High-Level Reflection on past trading decisions.
Your goal is to identify patterns, learn from mistakes, and extract actionable lessons.

=== PAST TRADING DECISIONS ===
{past_text}

=== REFLECTION REQUIRED ===

Analyze these past decisions and provide:

1. PATTERN RECOGNITION: What patterns do you see in successful vs unsuccessful decisions?

2. MISTAKE ANALYSIS: Were there any decisions that appear to be mistakes in hindsight? What went wrong?

3. SUCCESS FACTORS: What factors contributed to good decisions?

4. BIAS CHECK: Are there any biases evident (e.g., always bullish, ignoring negative news)?

5. ACTIONABLE LESSONS: Based on this analysis, what specific lessons should guide the current decision?

6. RISK AWARENESS: What risks from past decisions should we be especially careful about now?

Be specific and reference actual past decisions where possible.
"""
    res = model.invoke(prompt)
    return res.content


def synthesize_reflections(
    low_level: dict,
    high_level: str,
    price_data: dict
) -> str:
    """
    Synthesize low-level and high-level reflections into actionable guidance.
    """
    trend_alignment = price_data.get("trend_alignment", "UNKNOWN")
    
    prompt = f"""
Synthesize the following reflection components into clear trading guidance:

=== LOW-LEVEL REFLECTION (News-Price Correlation) ===
{low_level.get('analysis', 'N/A')}

=== HIGH-LEVEL REFLECTION (Past Decision Patterns) ===
{high_level}

=== TREND ALIGNMENT ===
Current trend alignment across timeframes: {trend_alignment}

=== SYNTHESIS REQUIRED ===

Combine these insights into:

1. CONVICTION LEVEL: How confident should we be in taking action? (HIGH/MEDIUM/LOW)

2. TIMEFRAME RECOMMENDATION: Is this a short-term, medium-term, or long-term play?

3. KEY RISKS: What are the top 2-3 risks to watch?

4. DECISION GUIDANCE: Based on all reflections, what action bias should we have? (Bullish/Bearish/Neutral)

Be concise and actionable.
"""
    res = model.invoke(prompt)
    return res.content
