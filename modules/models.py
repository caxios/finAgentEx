from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List


class SignalType(str, Enum):
    """Buy, Sell, or Hold signal."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SentimentType(str, Enum):
    """Market sentiment classification."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    UNCERTAIN = "UNCERTAIN"


class TrendType(str, Enum):
    """Trend direction classification."""
    STRONGLY_BULLISH = "STRONGLY_BULLISH"
    MODERATELY_BULLISH = "MODERATELY_BULLISH"
    NEUTRAL = "NEUTRAL"
    MODERATELY_BEARISH = "MODERATELY_BEARISH"
    STRONGLY_BEARISH = "STRONGLY_BEARISH"
    MIXED = "MIXED"


class TimeframeType(str, Enum):
    """Trading timeframe."""
    SHORT_TERM = "Short-term"
    MEDIUM_TERM = "Medium-term"
    LONG_TERM = "Long-term"


class TechnicalIndicator(BaseModel):
    """Individual technical indicator reading."""
    value: float = Field(..., description="The numeric value of the indicator")
    interpretation: str = Field(..., description="Human-readable interpretation (e.g., 'BULLISH', 'OVERBOUGHT')")


class TechnicalIndicators(BaseModel):
    """Collection of technical indicators for a stock."""
    macd: Optional[TechnicalIndicator] = Field(None, description="MACD indicator reading")
    rsi: Optional[TechnicalIndicator] = Field(None, description="RSI indicator reading")
    ma_trend: Optional[str] = Field(None, description="Moving average trend analysis")


class TimeframePriceAnalysis(BaseModel):
    """Price analysis for a specific timeframe."""
    timeframe: str = Field(..., description="The timeframe analyzed (e.g., 'short_term', 'medium_term', 'long_term')")
    trend: str = Field(..., description="Direction of the trend (Up/Down)")
    change_pct: float = Field(..., description="Percentage change in the period")
    volatility: float = Field(..., description="Volatility score")
    pattern: Optional[str] = Field(None, description="Recent price pattern identified")


class MultiTimeframePriceSignal(BaseModel):
    """Structured output for multi-timeframe price analysis."""
    short_term: TimeframePriceAnalysis = Field(..., description="5-day price analysis")
    medium_term: TimeframePriceAnalysis = Field(..., description="1-month price analysis")
    long_term: TimeframePriceAnalysis = Field(..., description="3-month price analysis")
    current_price: float = Field(..., description="Current stock price")
    trend_alignment: str = Field(..., description="Overall trend alignment across timeframes")
    technical_indicators: Optional[TechnicalIndicators] = Field(None, description="Technical indicator readings")


class PriceSignal(BaseModel):
    """Structured output for quantitative price analysis."""
    trend: str = Field(..., description="Description of the current price trend (e.g., 'Uptrend', 'Consolidation').")
    volatility: str = Field(..., description="Assessment of volatility (e.g., 'High', 'Low', 'Expanding').")
    key_levels: str = Field(..., description="Important support/resistance levels identified.")
    signal: SignalType = Field(..., description="The quantitative signal derived from price action.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")


class NewsSignal(BaseModel):
    """Structured output for qualitative news analysis."""
    summary: str = Field(..., description="Concise summary of the most important news drivers.")
    sentiment: SentimentType = Field(..., description="Overall sentiment derived from news.")
    impact_assessment: str = Field(..., description="How this news is expected to impact the stock price.")
    signal: SignalType = Field(..., description="The qualitative signal derived from news sentiment.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")


class ReflectionResult(BaseModel):
    """Structured output from reflection analysis."""
    low_level_analysis: str = Field(..., description="Analysis of news-price correlation")
    high_level_analysis: str = Field(..., description="Analysis of past decision patterns")
    synthesis: str = Field(..., description="Combined actionable guidance")
    conviction_level: str = Field(..., description="HIGH/MEDIUM/LOW conviction")
    recommended_timeframe: Optional[TimeframeType] = Field(None, description="Recommended trading timeframe")


class TradingSignal(BaseModel):
    """Final synthesized trading decision."""
    decision: SignalType = Field(..., description="The final trading decision.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregate confidence score between 0.0 and 1.0.")
    timeframe: str = Field(..., description="Applicable timeframe for this prediction (e.g., 'Short-term', 'Medium-term').")
    reasoning: str = Field(..., description="Detailed explanation combining price and news factors to justify the decision.")
    risk_factors: str = Field(..., description="Key risks that could invalidate this prediction.")


class EnhancedTradingSignal(BaseModel):
    """Enhanced trading signal with additional context."""
    decision: SignalType = Field(..., description="The final trading decision (BUY/SELL/HOLD)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    timeframe: TimeframeType = Field(..., description="Recommended trading timeframe")
    reasoning: str = Field(..., description="Detailed Chain-of-Thought reasoning for the decision")
    risk_factors: str = Field(..., description="Key risks that could invalidate this prediction")
    
    # Enhanced fields
    signal_confluences: Optional[List[str]] = Field(None, description="List of signals that agree with the decision")
    signal_contradictions: Optional[List[str]] = Field(None, description="List of signals that contradict the decision")
    position_sizing_hint: Optional[str] = Field(None, description="Suggested position sizing (e.g., 'Full', 'Half', 'Quarter')")
    stop_loss_trigger: Optional[str] = Field(None, description="Condition that would trigger a stop loss")
