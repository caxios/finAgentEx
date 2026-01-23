"""
Multi-Agent System Graph for Stock Analysis
6-Agent Architecture:
  - Agent 1 (News): Fetches news using yfinance
  - Agent 2 (Blogs): Fetches blog/social opinion using Tavily API
  - Agent 3 (Data): Fetches OHLCV data and generates charts
  - Agent 4 (Tech Analysis): Analyzes charts using Gemini Vision
  - Agent 5 (Sentiment): Analyzes text from Agents 1 & 2
  - Agent 6 (Strategy): Final decision maker
"""

from typing import Annotated, TypedDict, Optional, List, Dict
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from modules.models import TradingSignal, SignalType, SentimentType
from data_tools import (
    fetch_period_data, 
    fetch_news_for_ticker, 
    generate_technical_chart,
    fetch_single_ticker_data
)
import os
import re
import base64
from dotenv import load_dotenv
import json

load_dotenv()

# --- Initialize Models ---
model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL', 'gemini-1.5-flash'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# Gemini Vision model for chart analysis (uses same model as main)
vision_model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL', 'gemini-2.0-flash'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# Tavily API for blog search (optional - check if available)
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
tavily_client = None
if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print("[] Tavily client initialized")
    except ImportError:
        print("[!] Tavily not installed. Blog agent will use fallback.")
    except Exception as e:
        print(f"[!] Tavily initialization failed: {e}")




# --- 1. Define Agent State ---
class AgentState(TypedDict):
    """State shared across all agents in the graph."""
    ticker: str
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Agent 1 (News) Output
    news_data: Optional[List[dict]]           # Raw news from yfinance
    
    # Agent 2 (Blogs) Output  
    blog_data: Optional[List[dict]]           # Blog/social from Tavily
    
    # Agent 3 (Data) Output
    ohlcv_data: Optional[Dict]                # OHLCV data summary
    chart_path: Optional[str]                 # Path to generated chart
    
    # Agent 4 (Tech Analysis) Output
    technical_analysis: Optional[str]         # Vision analysis result
    
    # Agent 5 (Sentiment) Output
    sentiment_analysis: Optional[Dict]        # Combined sentiment analysis
    
    # Agent 6 (Strategy) Output
    final_signal: Optional[TradingSignal]     # Final trading decision


# --- 2. Helper Functions ---

def extract_ticker_from_message(content: str) -> str:
    """Extract stock ticker from user message."""
    patterns = [
        r'Analyze\s+(\w+)',           # "Analyze AAPL"
        r'ticker[:\s]+(\w+)',          # "ticker: AAPL"
        r'\b([A-Z]{1,5})\b',           # Any 1-5 uppercase letters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return "UNKNOWN"


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for Gemini Vision."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --- 3. Agent Nodes ---

def extract_ticker_node(state: AgentState) -> dict:
    """
    Extract ticker from the initial message at the start of the workflow.
    """
    print("\n" + "="*60)
    print(" MULTI-AGENT STOCK ANALYSIS SYSTEM")
    print("="*60)
    print("\n---> Extracting Ticker from Input")
    
    ticker = state.get('ticker', '')
    
    if not ticker and state['messages']:
        content = state['messages'][0].content
        ticker = extract_ticker_from_message(content)
    
    if not ticker:
        ticker = "UNKNOWN"
    
    print(f"      Ticker identified: {ticker}")
    return {"ticker": ticker}


def news_agent_node(state: AgentState) -> dict:
    """
    Agent 1: News Agent
    Fetches news using yfinance following Reference Code B.
    """
    print("\n---> Agent 1: News Agent (yfinance)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Fetch news using the reference code pattern
    news_list = fetch_news_for_ticker(ticker, count=10)
    
    if news_list:
        print(f"      Retrieved {len(news_list)} news articles")
        for i, article in enumerate(news_list[:3], 1):
            print(f"        {i}. {article['title'][:60]}...")
    else:
        print("      No news articles found")
    
    return {"news_data": news_list}


def blog_agent_node(state: AgentState) -> dict:
    """
    Agent 2: Blog/Social Agent
    Fetches blog and social opinion using Tavily API.
    """
    print("\n---> Agent 2: Blog/Social Agent (Tavily)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    blog_list = []
    
    if tavily_client:
        try:
            # Search for blog posts and social opinions
            query = f"{ticker} stock analysis opinion blog"
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_domains=["seekingalpha.com", "fool.com", "reddit.com", 
                                "stocktwits.com", "medium.com", "substack.com"]
            )
            
            for result in response.get('results', []):
                blog_list.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', ''),
                    'score': result.get('score', 0),
                    'source': result.get('url', '').split('/')[2] if result.get('url') else ''
                })
            
            print(f"      Retrieved {len(blog_list)} blog/social posts")
            for i, blog in enumerate(blog_list, 1):
                print(f"        {i}. [{blog['source']}] {blog['url']}")
            
        except Exception as e:
            print(f"      Tavily search failed: {e}")
    else:
        print("      Tavily not configured - using LLM to generate opinion summary")
        
        # Fallback: Use LLM to generate a summary based on general knowledge
        try:
            response = model.invoke([
                HumanMessage(content=f"""Based on your knowledge, provide a brief summary of 
                common investor opinions and sentiment about {ticker} stock. 
                Include perspectives from retail investors, analysts, and social media.
                Format as a brief paragraph.""")
            ])
            blog_list.append({
                'title': f"AI-Generated Sentiment Summary for {ticker}",
                'content': response.content,
                'url': None,
                'score': 0.5,
                'source': 'AI Summary'
            })
        except Exception as e:
            print(f"      Fallback also failed: {e}")
    
    return {"blog_data": blog_list}


def data_agent_node(state: AgentState) -> dict:
    """
    Agent 3: Data Agent
    Fetches OHLCV data using fetch_period_data and generates charts.
    """
    print("\n---> Agent 3: Data Agent (OHLCV + Charts)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Fetch OHLCV data using reference code pattern
    df = fetch_single_ticker_data(ticker, period="3mo")
    
    if df is None or df.empty:
        print(f"      No OHLCV data available for {ticker}")
        return {
            "ohlcv_data": None,
            "chart_path": None
        }
    
    # Generate summary statistics
    ohlcv_summary = {
        "ticker": ticker,
        "period": "3mo",
        "data_points": len(df),
        "start_date": str(df.index[0].date()),
        "end_date": str(df.index[-1].date()),
        "current_price": round(float(df['Close'].iloc[-1]), 2),
        "period_high": round(float(df['High'].max()), 2),
        "period_low": round(float(df['Low'].min()), 2),
        "period_change_pct": round(
            (float(df['Close'].iloc[-1]) / float(df['Close'].iloc[0]) - 1) * 100, 2
        ),
        "avg_volume": round(float(df['Volume'].mean()), 0),
        "volatility": round(float(df['Close'].pct_change().std() * 100), 2)
    }
    
    print(f"      Data Summary:")
    print(f"        Price: ${ohlcv_summary['current_price']} ({ohlcv_summary['period_change_pct']:+.2f}%)")
    print(f"        Range: ${ohlcv_summary['period_low']} - ${ohlcv_summary['period_high']}")
    print(f"        Volatility: {ohlcv_summary['volatility']:.2f}%")
    
    # Generate chart for technical analysis
    chart_path = generate_technical_chart(ticker, df)
    print(f"      Chart generated: {chart_path}")
    
    return {
        "ohlcv_data": ohlcv_summary,
        "chart_path": chart_path
    }


def tech_analysis_node(state: AgentState) -> dict:
    """
    Agent 4: Technical Analysis Agent
    Analyzes charts using Gemini Vision.
    """
    print("\n---> Agent 4: Technical Analysis (Gemini Vision)")
    
    chart_path = state.get('chart_path')
    ticker = state.get('ticker', 'UNKNOWN')
    ohlcv_data = state.get('ohlcv_data', {})
    
    if not chart_path or not os.path.exists(chart_path):
        print("      No chart available for analysis")
        return {"technical_analysis": "Chart not available for technical analysis."}
    
    try:
        # Convert chart to base64
        image_base64 = image_to_base64(chart_path)
        
        # Create vision prompt
        vision_prompt = f"""You are an expert technical analyst. Analyze this chart for {ticker} stock.

Current Data Summary:
- Current Price: ${ohlcv_data.get('current_price', 'N/A')}
- Period Change: {ohlcv_data.get('period_change_pct', 'N/A')}%
- Period High/Low: ${ohlcv_data.get('period_high', 'N/A')} / ${ohlcv_data.get('period_low', 'N/A')}

Analyze the chart and provide:
1. **Trend Analysis**: Overall trend direction (bullish/bearish/sideways)
2. **Support/Resistance**: Key price levels identified
3. **Technical Indicators**: Analysis of RSI, MACD, and volume patterns
4. **Pattern Recognition**: Any chart patterns (head & shoulders, double top/bottom, etc.)
5. **Technical Signal**: BUY, SELL, or HOLD recommendation with reasoning

Be specific about price levels and percentages. Focus on actionable insights."""

        # Invoke Gemini Vision
        response = vision_model.invoke([
            HumanMessage(content=[
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
            ])
        ])
        
        analysis = response.content
        print(f"      Technical analysis completed ({len(analysis)} chars)")
        
    except Exception as e:
        print(f"      Vision analysis failed: {e}")
        analysis = f"Technical analysis failed: {e}. Using OHLCV data only."
        
        # Fallback to text-based analysis
        if ohlcv_data:
            change = ohlcv_data.get('period_change_pct', 0)
            if change > 5:
                analysis += f"\nBased on data: {ticker} shows bullish momentum with +{change}% gain."
            elif change < -5:
                analysis += f"\nBased on data: {ticker} shows bearish pressure with {change}% loss."
            else:
                analysis += f"\nBased on data: {ticker} is consolidating with {change}% change."
    
    return {"technical_analysis": analysis}


def sentiment_agent_node(state: AgentState) -> dict:
    """
    Agent 5: Sentiment Analysis Agent
    Analyzes text from News (Agent 1) and Blogs (Agent 2).
    """
    print("\n---> Agent 5: Sentiment Analysis")
    
    ticker = state.get('ticker', 'UNKNOWN')
    news_data = state.get('news_data', [])
    blog_data = state.get('blog_data', [])
    
    # Combine all text sources
    text_sources = []
    
    # Add news content
    for news in news_data[:5]:
        text_sources.append({
            "source": "News",
            "title": news.get('title', ''),
            "content": news.get('summary', '')
        })
    
    # Add blog content
    for blog in blog_data[:3]:
        text_sources.append({
            "source": blog.get('source', 'Blog'),
            "title": blog.get('title', ''),
            "content": blog.get('content', '')[:500]  # Limit content length
        })
    
    if not text_sources:
        print("      No text sources available for sentiment analysis")
        return {
            "sentiment_analysis": {
                "overall_sentiment": "NEUTRAL",
                "confidence": 0.3,
                "news_sentiment": "Unknown",
                "social_sentiment": "Unknown",
                "key_themes": [],
                "summary": "Insufficient data for sentiment analysis."
            }
        }
    
    # Build prompt for sentiment analysis
    sources_text = "\n\n".join([
        f"[{s['source']}] {s['title']}\n{s['content']}"
        for s in text_sources
    ])
    
    sentiment_prompt = f"""Analyze the sentiment of the following news and social content about {ticker}:

{sources_text}

Provide a structured analysis:
1. Overall Sentiment: POSITIVE, NEGATIVE, NEUTRAL, or MIXED
2. Confidence: Your confidence level (0.0 to 1.0)
3. News Sentiment: Sentiment from news sources specifically
4. Social Sentiment: Sentiment from blogs/social media
5. Key Themes: Main topics being discussed (list 3-5)
6. Summary: Brief 2-3 sentence summary of the sentiment landscape

Respond in JSON format."""

    try:
        response = model.invoke([HumanMessage(content=sentiment_prompt)])
        
        # Parse response
        content = response.content
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            sentiment_result = json.loads(json_match.group())
        else:
            # Fallback parsing
            sentiment_result = {
                "overall_sentiment": "NEUTRAL",
                "confidence": 0.5,
                "news_sentiment": "See analysis",
                "social_sentiment": "See analysis",
                "key_themes": [],
                "summary": content[:500]
            }
        
        print(f"      Sentiment: {sentiment_result.get('overall_sentiment', 'N/A')}")
        print(f"        Confidence: {sentiment_result.get('confidence', 'N/A')}")
        
    except Exception as e:
        print(f"      Sentiment analysis failed: {e}")
        sentiment_result = {
            "overall_sentiment": "NEUTRAL",
            "confidence": 0.3,
            "news_sentiment": "Analysis failed",
            "social_sentiment": "Analysis failed",
            "key_themes": [],
            "summary": f"Sentiment analysis failed: {e}"
        }
    
    return {"sentiment_analysis": sentiment_result}


def strategy_agent_node(state: AgentState) -> dict:
    """
    Agent 6: Strategy Agent (Final Decision Maker)
    Synthesizes all inputs to make final trading decision.
    """
    print("\n---> Agent 6: Strategy (Final Decision)")
    print("="*60)
    
    ticker = state.get('ticker', 'UNKNOWN')
    ohlcv_data = state.get('ohlcv_data', {})
    technical_analysis = state.get('technical_analysis', '')
    sentiment_analysis = state.get('sentiment_analysis', {})
    news_data = state.get('news_data', [])
    blog_data = state.get('blog_data', [])
    
    # Build comprehensive context
    strategy_prompt = f"""You are a senior portfolio strategist. Make a final trading decision for {ticker}.

## QUANTITATIVE DATA (Agent 3)
- Current Price: ${ohlcv_data.get('current_price', 'N/A')}
- Period Change: {ohlcv_data.get('period_change_pct', 'N/A')}%
- Price Range: ${ohlcv_data.get('period_low', 'N/A')} - ${ohlcv_data.get('period_high', 'N/A')}
- Volatility: {ohlcv_data.get('volatility', 'N/A')}%

## TECHNICAL ANALYSIS (Agent 4)
{technical_analysis[:1500] if technical_analysis else 'Not available'}

## SENTIMENT ANALYSIS (Agent 5)
- Overall Sentiment: {sentiment_analysis.get('overall_sentiment', 'N/A')}
- Sentiment Confidence: {sentiment_analysis.get('confidence', 'N/A')}
- Key Themes: {', '.join(sentiment_analysis.get('key_themes', [])) or 'N/A'}
- Summary: {sentiment_analysis.get('summary', 'N/A')}

## NEWS HEADLINES (Agent 1)
{chr(10).join([f"- {n.get('title', '')}" for n in news_data[:5]]) or 'No news available'}

---

Based on ALL the above inputs, provide your final trading decision:

1. DECISION: BUY, SELL, or HOLD
2. CONFIDENCE: 0.0 to 1.0
3. TIMEFRAME: Short-term (1-2 weeks), Medium-term (1-3 months), or Long-term (3+ months)
4. REASONING: Detailed explanation combining technical, fundamental, and sentiment factors
5. RISK_FACTORS: Key risks that could invalidate this decision

Be specific and actionable. Consider risk-adjusted returns.

Respond in JSON format with keys: decision, confidence, timeframe, reasoning, risk_factors"""

    try:
        response = model.invoke([HumanMessage(content=strategy_prompt)])
        content = response.content
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        
        if json_match:
            decision_data = json.loads(json_match.group())
        else:
            decision_data = {
                "decision": "HOLD",
                "confidence": 0.5,
                "timeframe": "Medium-term",
                "reasoning": content[:500],
                "risk_factors": "Unable to parse detailed risk factors"
            }
        
        # Convert to TradingSignal
        decision_str = decision_data.get('decision', 'HOLD').upper()
        signal_type = SignalType.HOLD
        if decision_str == 'BUY':
            signal_type = SignalType.BUY
        elif decision_str == 'SELL':
            signal_type = SignalType.SELL
        
        # Ensure risk_factors is a string (not a list)
        risk_factors = decision_data.get('risk_factors', 'No risk factors identified')
        if isinstance(risk_factors, list):
            risk_factors = '; '.join(str(r) for r in risk_factors)
        
        # Ensure reasoning is a string
        reasoning = decision_data.get('reasoning', 'No reasoning provided')
        if isinstance(reasoning, list):
            reasoning = ' '.join(str(r) for r in reasoning)
        
        final_signal = TradingSignal(
            decision=signal_type,
            confidence=float(decision_data.get('confidence', 0.5)),
            timeframe=str(decision_data.get('timeframe', 'Medium-term')),
            reasoning=reasoning,
            risk_factors=risk_factors
        )
        
        # Print final decision
        print(f"\n{'='*60}")
        print(f" FINAL DECISION FOR {ticker}")
        print(f"{'='*60}")
        print(f"   Decision: {final_signal.decision.value}")
        print(f"   Confidence: {final_signal.confidence:.0%}")
        print(f"   Timeframe: {final_signal.timeframe}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"      Strategy decision failed: {e}")
        final_signal = TradingSignal(
            decision=SignalType.HOLD,
            confidence=0.3,
            timeframe="Short-term",
            reasoning=f"Decision generation failed: {e}. Defaulting to HOLD.",
            risk_factors="System error - manual review required"
        )
    
    return {"final_signal": final_signal}


# --- 4. Build the Graph ---
builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("ExtractTicker", extract_ticker_node)
builder.add_node("NewsAgent", news_agent_node)
builder.add_node("BlogAgent", blog_agent_node)
builder.add_node("DataAgent", data_agent_node)
builder.add_node("TechAnalysis", tech_analysis_node)
builder.add_node("Sentiment", sentiment_agent_node)
builder.add_node("Strategy", strategy_agent_node)

# Define edges
# Start -> Extract Ticker
builder.add_edge(START, "ExtractTicker")

# Ticker -> Three parallel-ish agents (sequenced for simplicity)
builder.add_edge("ExtractTicker", "NewsAgent")
builder.add_edge("ExtractTicker", "BlogAgent")
builder.add_edge("ExtractTicker", "DataAgent")

# Data Agent -> Tech Analysis (needs chart)
builder.add_edge("DataAgent", "TechAnalysis")

# News + Blog -> Sentiment (needs text data)
builder.add_edge("NewsAgent", "Sentiment")
builder.add_edge("BlogAgent", "Sentiment")

# Tech Analysis + Sentiment -> Strategy
builder.add_edge("TechAnalysis", "Strategy")
builder.add_edge("Sentiment", "Strategy")

# Strategy -> End
builder.add_edge("Strategy", END)

# Compile the graph
graph = builder.compile()


# --- 5. Convenience Run Function ---
def analyze_stock(ticker: str) -> TradingSignal:
    """
    Convenience function to run the multi-agent analysis.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
    
    Returns:
        TradingSignal with the final decision
    """
    result = graph.invoke({
        "ticker": ticker.upper(),
        "messages": [HumanMessage(content=f"Analyze {ticker}")]
    })
    
    return result.get("final_signal")


if __name__ == "__main__":
    # Test run
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    signal = analyze_stock(ticker)
    
    if signal:
        print(f"\n Full Analysis Complete")
        print(f"   Decision: {signal.decision.value}")
        print(f"   Confidence: {signal.confidence:.0%}")
        print(f"   Timeframe: {signal.timeframe}")
        print(f"\n   Reasoning: {signal.reasoning[:300]}...")
        print(f"\n   Risk Factors: {signal.risk_factors[:200]}...")
