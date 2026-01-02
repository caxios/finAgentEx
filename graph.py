from typing import Annotated, TypedDict, Optional, List
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from agents import price_agent, news_agent, news_prompt
from modules.models import PriceSignal, NewsSignal, TradingSignal
# Import Enhanced Modules
from modules.reflection import low_level_reflection_multi_timeframe, high_level_reflection, synthesize_reflections
from modules.memory import retrieve_diversified, store_event, format_memories_for_prompt
from modules.decision_maker import make_decision, validate_decision
from modules.market_intelligence import analyze_multi_timeframe
import os
import re
from dotenv import load_dotenv
import json

load_dotenv()


# --- 1. Define Enhanced State ---
class AgentState(TypedDict):
    ticker: str
    messages: Annotated[list[BaseMessage], add_messages]
    price_signal: Optional[PriceSignal]
    news_signal: Optional[NewsSignal]
    news_context: Optional[str]          # Stores full raw grounding/search results
    multi_timeframe_data: Optional[dict]  # NEW: Multi-timeframe price analysis
    reflections: Optional[dict]           # CHANGED: Now stores structured reflection
    reflection_synthesis: Optional[str]   # NEW: Synthesized reflection guidance
    memories: Optional[list]              # Stores retrieved similar events
    final_signal: Optional[TradingSignal]


model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)


# --- 2. Nodes ---

def extract_ticker_node(state: AgentState):
    """
    Extract ticker from the initial message at the start of the workflow.
    This ensures ticker is available for all subsequent nodes.
    """
    print("--> Extracting Ticker from Input")
    
    ticker = state.get('ticker', '')
    
    # If ticker not provided in state, try to extract from message
    if not ticker and state['messages']:
        content = state['messages'][0].content
        
        # Try common patterns
        patterns = [
            r'Analyze\s+(\w+)',           # "Analyze AAPL"
            r'ticker[:\s]+(\w+)',          # "ticker: AAPL" or "ticker AAPL"
            r'\b([A-Z]{1,5})\b',           # Any 1-5 uppercase letters (stock symbol)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                ticker = match.group(1).upper()
                break
        
        if not ticker:
            ticker = "UNKNOWN"
    
    print(f"    Ticker identified: {ticker}")
    return {"ticker": ticker}


def call_price_agent(state: AgentState):
    """
    Enhanced Price Agent with multi-timeframe analysis.
    Uses the new analyze_multi_timeframe function for comprehensive analysis.
    """
    print("--> Calling Price Agent (Multi-Timeframe)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Perform multi-timeframe analysis
    multi_tf_data = analyze_multi_timeframe(ticker)
    
    # Also get structured signal from LLM
    response = price_agent.invoke({
        "messages": [HumanMessage(content=f"Perform a comprehensive price analysis for {ticker}, covering the last 1 year of data. Focus on trend detection, volatility, and key support/resistance levels.")]
    })
    
    ai_msg = response["messages"][-1]
    print("    [Price Agent] Converting to Structured Output...")
    structured_llm = model.with_structured_output(PriceSignal)
    signal = structured_llm.invoke(f"Extract the following analysis into a structured signal:\n\n{ai_msg.content}")
    
    return {
        "messages": [ai_msg], 
        "price_signal": signal,
        "multi_timeframe_data": multi_tf_data
    }


def call_news_agent(state: AgentState):
    """
    News Agent that uses Google Search tool to find recent financial news.
    This is a ReAct agent that can autonomously search and synthesize news.
    """
    print("--> Calling News Agent (ReAct with Google Search)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    user_query = state['messages'][0].content if state['messages'] else f"Analyze {ticker}"
    
    # Construct the prompt for the news agent
    agent_prompt = f"""
{news_prompt}

TASK: Analyze recent news and market intelligence for {ticker}.

User's specific request: {user_query}

Please:
1. Use the google_search tool to find recent financial news about {ticker}
2. Search for earnings reports, analyst ratings, and major announcements
3. Look for any regulatory or market events affecting {ticker}
4. Synthesize your findings into actionable market intelligence

Provide a comprehensive analysis of the news landscape and its potential impact on the stock.
"""
    
    # Invoke the ReAct agent - it will autonomously use the google_search tool
    print(f"    [News Agent] Invoking ReAct agent to search for {ticker} news...")
    try:
        response = news_agent.invoke({
            "messages": [HumanMessage(content=agent_prompt)]
        })
        ai_msg = response["messages"][-1]
        raw_results = ai_msg.content
    except Exception as e:
        print(f"    [News Agent] Agent invocation failed: {e}")
        ai_msg = HumanMessage(content=f"News search failed: {e}")
        raw_results = "News search failed. No data available."
    
    # Convert to Structured Output
    print("    [News Agent] Converting to Structured Output...")
    try:
        structured_llm = model.with_structured_output(NewsSignal)
        signal = structured_llm.invoke(f"Extract the following news analysis into a structured signal:\n\n{raw_results}")
    except Exception as e:
        print(f"    [News Agent] Structured output failed: {e}")
        from modules.models import SentimentType, SignalType
        signal = NewsSignal(
            summary=raw_results[:500] if len(raw_results) > 500 else raw_results,
            sentiment=SentimentType.UNCERTAIN,
            impact_assessment="Unable to assess impact due to processing error",
            signal=SignalType.HOLD,
            confidence=0.3
        )
    
    return {
        "messages": [ai_msg],
        "news_signal": signal,
        "news_context": raw_results
    }


def reflection_node(state: AgentState):
    """
    Enhanced Reflection Node with multi-timeframe correlation analysis.
    """
    print("--> Calling Reflection Node (Multi-Timeframe)")
    
    news = state.get('news_signal')
    multi_tf_data = state.get('multi_timeframe_data')
    
    # Use multi-timeframe reflection
    if multi_tf_data:
        low_level_result = low_level_reflection_multi_timeframe(
            news_summary=news.summary if news else "No news available",
            price_data=multi_tf_data
        )
    else:
        # Fallback to basic reflection
        price = state.get('price_signal')
        from modules.reflection import low_level_reflection
        low_level_analysis = low_level_reflection(
            news_summary=news.summary if news else "No news",
            price_trend=f"{price.trend} (Volatility: {price.volatility})" if price else "No price data"
        )
        low_level_result = {"analysis": low_level_analysis}
    
    return {"reflections": low_level_result}


def memory_node(state: AgentState):
    """
    Enhanced Memory Node with diversified retrieval.
    """
    print("--> Calling Memory Node (Diversified Retrieval)")
    
    ticker = state.get('ticker', '')
    reflections = state.get('reflections', {})
    
    # Build query from current context
    context = reflections.get('analysis', '') if isinstance(reflections, dict) else str(reflections)
    
    # Use diversified retrieval
    memories = retrieve_diversified(
        query=context[:500],  # Limit query length
        ticker=ticker,
        n_results=5
    )
    
    return {"memories": memories}


def high_level_reflection_node(state: AgentState):
    """
    Enhanced High-Level Reflection with synthesis.
    """
    print("--> Calling High-Level Reflection Node")
    
    memories = state.get('memories', [])
    existing_reflections = state.get('reflections', {})
    multi_tf_data = state.get('multi_timeframe_data', {})
    
    # Reflect on the retrieved memories
    high_level = high_level_reflection(past_decisions=memories)
    
    # Synthesize low-level and high-level reflections
    synthesis = synthesize_reflections(
        low_level=existing_reflections,
        high_level=high_level,
        price_data=multi_tf_data
    )
    
    # Combine into structured reflection
    combined_reflection = {
        "low_level": existing_reflections,
        "high_level": high_level,
    }
    
    return {
        "reflections": combined_reflection,
        "reflection_synthesis": synthesis
    }


def synthesis_node(state: AgentState):
    """
    Enhanced Decision Maker with full context integration.
    """
    print("--> Calling Decision Maker (Enhanced Synthesis)")
    
    ticker = state.get('ticker', 'Unknown')
    price = state.get('price_signal')
    news = state.get('news_signal')
    memories = state.get('memories', [])
    reflections = state.get('reflections', {})
    reflection_synthesis = state.get('reflection_synthesis', '')
    multi_tf_data = state.get('multi_timeframe_data', {})
    
    # Format reflections for prompt
    if isinstance(reflections, dict):
        low_level = reflections.get('low_level', {})
        high_level = reflections.get('high_level', '')
        reflections_text = f"""
### Low-Level Reflection (News-Price Correlation):
{low_level.get('analysis', 'N/A') if isinstance(low_level, dict) else str(low_level)}

### High-Level Reflection (Past Decision Analysis):
{high_level}
"""
    else:
        reflections_text = str(reflections)
    
    # Build price patterns for backward compatibility
    price_patterns = {}
    if price:
        price_patterns = {
            "current_price": multi_tf_data.get('current_price', 'See analysis'),
            "trend": price.trend,
            "period_change_pct": "See multi-timeframe",
            "volatility_score": price.volatility,
            "recent_pattern": price.signal.value,
            "history_summary": str(price.key_levels)
        }
    
    # Make enhanced decision
    decision_json = make_decision(
        ticker=ticker,
        news_summary=news.summary if news else "",
        memories=memories,
        reflections=reflections_text,
        price_patterns=price_patterns,
        multi_timeframe_data=multi_tf_data,
        reflection_synthesis=reflection_synthesis
    )
    
    # Validate decision
    decision_json = validate_decision(decision_json, multi_tf_data)
    
    # Log validation warnings
    if decision_json.get('validation_warnings'):
        for warning in decision_json['validation_warnings']:
            print(f"    [Validation] {warning}")
    
    # Convert to TradingSignal
    final_signal = TradingSignal(**{
        k: v for k, v in decision_json.items() 
        if k in ['decision', 'confidence', 'timeframe', 'reasoning', 'risk_factors']
    })
    
    return {"final_signal": final_signal}


def storage_node(state: AgentState):
    """
    Enhanced Storage Node with richer metadata.
    """
    print("--> Calling Storage Node (Learning)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    final_signal = state.get('final_signal')
    news = state.get('news_signal')
    full_news = state.get('news_context', "No detailed search data.")
    multi_tf_data = state.get('multi_timeframe_data', {})
    
    if final_signal:
        store_event(
            ticker=ticker, 
            summary=news.summary if news else "", 
            action=final_signal.decision.value,
            reasoning=final_signal.reasoning,
            grounding_data=full_news,
            confidence=final_signal.confidence,
            timeframe=final_signal.timeframe,
            price_at_decision=multi_tf_data.get('current_price', 0.0)
        )
        print(f"    [Storage] Decision saved: {final_signal.decision.value} with {final_signal.confidence:.2f} confidence")
        
    return {}


# --- 3. Build the Enhanced Graph ---
builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("ExtractTicker", extract_ticker_node)
builder.add_node("PriceAgent", call_price_agent)
builder.add_node("NewsAgent", call_news_agent)
builder.add_node("Reflection", reflection_node)
builder.add_node("MemoryRetrieval", memory_node)
builder.add_node("StrategyAnalysis", high_level_reflection_node)
builder.add_node("Synthesis", synthesis_node)
builder.add_node("Storage", storage_node)

# Enhanced Flow with Ticker Extraction
# Start -> Extract Ticker -> Parallel analysis -> Reflection -> Memory -> Strategy -> Decision -> Storage
builder.add_edge(START, "ExtractTicker")

# After ticker extraction, both Price and News agents can run
# (Note: LangGraph doesn't support true parallel edges in basic StateGraph,
#  but we sequence them efficiently)
builder.add_edge("ExtractTicker", "PriceAgent")
builder.add_edge("PriceAgent", "NewsAgent")

# Then continue through the reflection pipeline
builder.add_edge("NewsAgent", "Reflection")
builder.add_edge("Reflection", "MemoryRetrieval")
builder.add_edge("MemoryRetrieval", "StrategyAnalysis")
builder.add_edge("StrategyAnalysis", "Synthesis")
builder.add_edge("Synthesis", "Storage")
builder.add_edge("Storage", END)

graph = builder.compile()
