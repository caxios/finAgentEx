from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from modules.models import TradingSignal
from dotenv import load_dotenv

import os
load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)


def make_decision(
    ticker: str, 
    news_summary: str, 
    memories: list, 
    reflections: str, 
    price_patterns: dict,
    multi_timeframe_data: dict = None,
    reflection_synthesis: str = None
) -> dict:
    """
    Enhanced decision making with multi-timeframe analysis and technical indicators.
    Uses Chain-of-Thought reasoning for sophisticated decisions.
    
    Args:
        ticker: Stock symbol
        news_summary: Summary of recent news
        memories: Retrieved past decisions
        reflections: Low and high level reflection analysis
        price_patterns: Basic price pattern analysis
        multi_timeframe_data: Optional multi-timeframe price analysis
        reflection_synthesis: Optional synthesized reflection guidance
    """
    print(f"Synthesizing data for final decision on {ticker}...")
    
    # Format memories
    if memories:
        if isinstance(memories, list) and len(memories) > 0:
            if isinstance(memories[0], dict):
                memory_text = "\n".join([
                    f"- [{m.get('source', 'unknown')}] {m.get('content', str(m))[:200]}..." 
                    for m in memories
                ])
            else:
                memory_text = "\n".join([f"- {str(m)[:200]}..." for m in memories])
        else:
            memory_text = "No relevant memories found."
    else:
        memory_text = "No relevant memories found."
    
    # Build technical indicators section
    tech_section = ""
    if multi_timeframe_data:
        indicators = multi_timeframe_data.get("technical_indicators", {})
        macd = indicators.get("macd", {})
        rsi = indicators.get("rsi", {})
        ma = indicators.get("moving_averages", {})
        obv = indicators.get("obv", {})
        adl = indicators.get("adl", {})
        volume_analysis = indicators.get("volume_analysis", {})
        
        tech_section = f"""
                        === TECHNICAL INDICATORS (Tools) ===
                        MACD Analysis:
                        - Signal: {macd.get('interpretation', 'N/A')}
                        - MACD Value: {macd.get('value', 'N/A')}
                        - Signal Line: {macd.get('signal_line', 'N/A')}
                        - Histogram: {macd.get('histogram', 'N/A')}

                        RSI Analysis:
                        - Value: {rsi.get('value', 'N/A')}
                        - Status: {rsi.get('interpretation', 'N/A')}

                        === VOLUME INDICATORS ===
                        OBV (On-Balance Volume):
                        - Current OBV: {obv.get('value', 'N/A')}
                        - OBV MA(20): {obv.get('ma_20', 'N/A')}
                        - Trend: {obv.get('interpretation', 'N/A')}

                        ADL (Accumulation/Distribution Line):
                        - Current ADL: {adl.get('value', 'N/A')}
                        - ADL MA(20): {adl.get('ma_20', 'N/A')}
                        - Trend: {adl.get('interpretation', 'N/A')}

                        Volume-Price Confirmation: {volume_analysis.get('volume_confirms_price', 'N/A')}

                        Moving Averages:
                        - MA(5): {ma.get('ma_5', 'N/A')}
                        - MA(20): {ma.get('ma_20', 'N/A')}
                        - MA(50): {ma.get('ma_50', 'N/A')}
                        - Trend: {ma.get('trend', 'N/A')}

                        Trend Alignment: {multi_timeframe_data.get('trend_alignment', 'N/A')}
                        """
    
    # Build multi-timeframe section
    mtf_section = ""
    if multi_timeframe_data:
        short = multi_timeframe_data.get("short_term", {})
        medium = multi_timeframe_data.get("medium_term", {})
        long = multi_timeframe_data.get("long_term", {})
        
        mtf_section = f"""
                        === MULTI-TIMEFRAME ANALYSIS ===
                        SHORT-TERM (5 days):
                        - Trend: {short.get('trend', 'N/A')} ({short.get('period_change_pct', 'N/A')}%)
                        - Volatility: {short.get('volatility_score', 'N/A')}
                        - Pattern: {short.get('recent_pattern', 'N/A')}

                        MEDIUM-TERM (1 month):
                        - Trend: {medium.get('trend', 'N/A')} ({medium.get('period_change_pct', 'N/A')}%)
                        - Volatility: {medium.get('volatility_score', 'N/A')}

                        LONG-TERM (3 months):
                        - Trend: {long.get('trend', 'N/A')} ({long.get('period_change_pct', 'N/A')}%)
                        - Volatility: {long.get('volatility_score', 'N/A')}
                        """
    else:
        # Fallback to basic price_patterns
        mtf_section = f"""
                        === PRICE ANALYSIS ===
                        - Current Price: {price_patterns.get('current_price', 'N/A')}
                        - Trend: {price_patterns.get('trend', 'N/A')} ({price_patterns.get('period_change_pct', 'N/A')}%)
                        - Volatility: {price_patterns.get('volatility_score', 'N/A')}
                        - Recent Pattern: {price_patterns.get('recent_pattern', 'N/A')}
                        """
    
    # Build synthesis section
    synthesis_section = ""
    if reflection_synthesis:
        synthesis_section = f"""
                             === REFLECTION SYNTHESIS ===
                             {reflection_synthesis}
                             """
    
    # Construct the comprehensive prompt
    system_message = SystemMessage(content="""You are FinAgent, an autonomous trading AI designed for sophisticated market analysis.

                                            Your decision-making framework:
                                            1. ANALYZE all inputs systematically using Chain-of-Thought reasoning
                                            2. IDENTIFY confluences where multiple signals agree
                                            3. WEIGH contradictory signals carefully
                                            4. PRIORITIZE risk-adjusted returns
                                            5. PROVIDE clear, actionable decisions with confidence levels

                                            You must consider:
                                            - Technical indicators (MACD, RSI, Moving Averages)
                                            - Multi-timeframe trend alignment
                                            - News sentiment and market events
                                            - Historical patterns from memory
                                            - Lessons from past reflections

                                            Decision Rules:
                                            - BUY: When signals show high conviction bullish setup with trend alignment
                                            - SELL: When signals show high conviction bearish setup or deteriorating fundamentals
                                            - HOLD: When signals are mixed, uncertain, or when already well-positioned
                                            """
                                    )
    
    human_message = HumanMessage(content=f"""
                                        Analyze the following data for {ticker} and make a trading decision.

                                        === MARKET INTELLIGENCE (News) ===
                                        {news_summary}
                                        {mtf_section}
                                        {tech_section}

                                        === REFLECTION & ANALYSIS ===
                                        {reflections}
                                        {synthesis_section}

                                        === MEMORY (Past Decisions) ===
                                        {memory_text}

                                        === DECISION REQUIRED ===

                                        Using Chain-of-Thought reasoning, work through:

                                        1. SIGNAL ANALYSIS: What are the key signals telling us?
                                        - Technical: Are MACD/RSI/MA aligned?
                                        - Trend: Is there multi-timeframe trend alignment?
                                        - Sentiment: What is the news telling us?

                                        2. CONFLUENCE CHECK: Where do signals agree/disagree?

                                        3. RISK ASSESSMENT: What could go wrong?

                                        4. DECISION: Based on ALL inputs, decide BUY, SELL, or HOLD

                                        Provide:
                                        - Decision (BUY/SELL/HOLD)
                                        - Confidence (0.0 to 1.0)
                                        - Timeframe (Short-term/Medium-term/Long-term)
                                        - Detailed reasoning
                                        - Key risk factors
                                        """
                                )
    
    # Invoke with Structured Output
    response = model.with_structured_output(TradingSignal).invoke([system_message, human_message])
    return response.model_dump()


def validate_decision(decision: dict, price_data: dict) -> dict:
    """
    Validate the decision against common pitfalls and biases.
    """
    warnings = []
    
    # Check for contradictions
    if price_data:
        trend_alignment = price_data.get("trend_alignment", "")
        decision_action = decision.get("decision", "")
        
        if "BEARISH" in trend_alignment and decision_action == "BUY":
            warnings.append("WARNING: Buying against bearish trend alignment")
        if "BULLISH" in trend_alignment and decision_action == "SELL":
            warnings.append("WARNING: Selling against bullish trend alignment")
    
    # Check confidence
    confidence = decision.get("confidence", 0)
    if confidence > 0.9:
        warnings.append("CAUTION: Very high confidence may indicate overconfidence")
    if confidence < 0.4 and decision.get("decision") != "HOLD":
        warnings.append("CAUTION: Low confidence trade - consider HOLD instead")
    
    decision["validation_warnings"] = warnings
    return decision
