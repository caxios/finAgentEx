from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import base64
from dotenv import load_dotenv

load_dotenv()

class TradingDecision(BaseModel):
    Action: str = Field(description="BUY, SELL, or HOLD")
    Reasoning: str = Field(description="Detailed explanation of the decision")
    Confidence: float = Field(description="Confidence score between 0.0 and 1.0")

model = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0
)

def make_decision(ticker: str, news_summary: str, memories: list, reflections: str, chart_path: str):
    """
    Synthesizes all multimodal inputs to make a trading decision.
    """
    print("Synthesizing data for final decision...")
    
    # 1. Prepare Image
    with open(chart_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
    # 2. Prepare Memory Text
    memory_text = "\n".join([f"- {m}" for m in memories]) if memories else "No relevant memories found."
    
    # 3. Construct Prompt
    # We send a multimodal message: Text + Image
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"""
You are FinAgent, an autonomous trading AI. 
Analyze the following data for {ticker} and make a trading decision.

1. MARKET INTELLIGENCE (News):
{news_summary}

2. REFLECTION (Self-Correction & Analysis):
{reflections}

3. MEMORY (Similar Past Events):
{memory_text}

4. TECHNICAL VISUALS (Attached Chart):
Reference the attached candlestick chart (OHLC). Analyze the trend, support/resistance, and volume.

Based on ALL inputs (Text + Visual), decide on an action (BUY, SELL, or HOLD).
Provide a structured JSON response.
"""
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"}
            }
        ]
    )
    
    # 4. Invoke with Structured Output
    response = model.with_structured_output(TradingDecision).invoke([message])
    return response.model_dump()
