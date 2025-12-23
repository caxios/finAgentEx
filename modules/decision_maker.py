from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class TradingDecision(BaseModel):
    Action: str = Field(description="BUY, SELL, or HOLD")
    Reasoning: str = Field(description="Detailed explanation of the decision")
    Confidence: float = Field(description="Confidence score between 0.0 and 1.0")

model = ChatGoogleGenerativeAI(
    model='gemini-pro-latest',
    temperature=0
)

def make_decision(ticker: str, news_summary: str, memories: list, reflections: str, price_patterns: dict):
    """
    Synthesizes all multimodal inputs to make a trading decision.
    """
    print("Synthesizing data for final decision...")
        
    # 2. Prepare Memory Text
    memory_text = "\n".join([f"- {m}" for m in memories]) if memories else "No relevant memories found."
    
    # 3. Construct Prompt
    # We send a text-only message now with structured price data
    message = HumanMessage(
        content=f"""
You are FinAgent, an autonomous trading AI. 
Analyze the following data for {ticker} and make a trading decision.

1. MARKET INTELLIGENCE (News):
{news_summary}

2. REFLECTION (Self-Correction & Analysis):
{reflections}

3. MEMORY (Similar Past Events):
{memory_text}

4. QUANTITATIVE ANALYSIS (Price Patterns):
- Current Price: {price_patterns.get('current_price')}
- Trend: {price_patterns.get('trend')} ({price_patterns.get('period_change_pct')}%)
- Volatility: {price_patterns.get('volatility_score')}
- Recent Pattern: {price_patterns.get('recent_pattern')}
- History: {price_patterns.get('history_summary')}

Based on ALL inputs, decide on an action (BUY, SELL, or HOLD).
Provide a structured JSON response.
"""
    )
    
    # 4. Invoke with Structured Output
    response = model.with_structured_output(TradingDecision).invoke([message])
    return response.model_dump()
