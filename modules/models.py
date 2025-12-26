from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

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

class PriceSignal(BaseModel):
    """Structured output for quantitative price analysis."""
    trend: str = Field(..., description="Description of the current price trend (e.g., 'Uptrend', 'Consolidation').")
    volatility: str = Field(..., description="Assessment of volatility (e.g., 'High', 'Low', 'Expanding').")
    key_levels: str = Field(..., description="Important support/resistance levels identified.")
    signal: SignalType = Field(..., description="The quantitative signal derived from price action.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")

class NewsSignal(BaseModel):
    """Structured output for qualitative news analysis."""
    summary: str = Field(..., description="Concise summary of the most important news drivers.")
    sentiment: SentimentType = Field(..., description="Overall sentiment derived from news.")
    impact_assessment: str = Field(..., description="How this news is expected to impact the stock price.")
    signal: SignalType = Field(..., description="The qualitative signal derived from news sentiment.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")

class TradingSignal(BaseModel):
    """Final synthesized trading decision."""
    decision: SignalType = Field(..., description="The final trading decision.")
    confidence: float = Field(..., description="Aggregate confidence score between 0.0 and 1.0.")
    timeframe: str = Field(..., description="Applicable timeframe for this prediction (e.g., 'Short-term', 'Medium-term').")
    reasoning: str = Field(..., description="Detailed explanation combining price and news factors to justify the decision.")
    risk_factors: str = Field(..., description="Key risks that could invalidate this prediction.")
