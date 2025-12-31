from typing import Annotated, TypedDict, Optional
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from agents import price_agent, news_agent, news_prompt, search
from modules.models import PriceSignal, NewsSignal, TradingSignal
# Import Advanced Modules
from modules.reflection import low_level_reflection, high_level_reflection
from modules.memory import retrieve_similar_events, store_event
from modules.decision_maker import make_decision
import os
from dotenv import load_dotenv
import json

load_dotenv()

# --- 1. Define State ---
class AgentState(TypedDict):
    ticker: str
    messages: Annotated[list[BaseMessage], add_messages]
    price_signal: Optional[PriceSignal]
    news_signal: Optional[NewsSignal]
    news_context: Optional[str]       # Stores full raw grounding/search results
    reflections: Optional[str]        # Stores combined reflection output
    memories: Optional[list]          # Stores retrieved similar events
    final_signal: Optional[TradingSignal]

model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# --- 2. Nodes ---

def call_price_agent(state: AgentState):
    print("--> Calling Price Agent (Structured)")
    # Explicitly ask for 1 Year data
    response = price_agent.invoke({"messages": [HumanMessage(content="Perform a comprehensive price analysis for the requested ticker, covering the last 1 year of data.")]})
    
    ai_msg = response["messages"][-1]
    print("    [Price Agent] Converting to Structured Output...")
    structured_llm = model.with_structured_output(PriceSignal)
    signal = structured_llm.invoke(f"Extract the following analysis into a structured signal:\n\n{ai_msg.content}")
    
    return {
        "messages": [ai_msg], 
        "price_signal": signal
    }

def call_news_agent(state: AgentState):
    print("--> Calling News Agent (Structured)")
    last_message = state['messages'][0] # User query
    query = last_message.content
    
    # 1. MANUAL GROUNDING: Execute Search explicitly
    print(f"    [News Agent] Searching Google for: {query[:50]}...")
    try:
        raw_results = search.run(query)
    except Exception as e:
        print(f"    [News Agent] Search failed: {e}")
        raw_results = "Search failed. No news available."

    # 2. Prepare Context for Synthesis
    # We combine the system prompt, user query, and the raw search results
    synthesis_prompt = f"""
{news_prompt}

USER REQUEST: {query}

SOURCE MATERIAL (Search Results):
{raw_results}

Based on the SOURCE MATERIAL above, provide the NewsSignal.
"""
    messages = [HumanMessage(content=synthesis_prompt)]
    
    # 3. Invoke Model (Synthesis)
    # news_agent is just the model (ChatGoogleGenerativeAI)
    ai_msg = news_agent.invoke(messages)
    
    # 4. Convert to Structured Output
    print("    [News Agent] Converting to Structured Output...")
    structured_llm = model.with_structured_output(NewsSignal)
    signal = structured_llm.invoke(f"Extract the following news analysis into a structured signal:\n\n{ai_msg.content}")
    
    return {
        "messages": [ai_msg],
        "news_signal": signal,
        "news_context": raw_results # Save the RAW TEXT results to memory
    }

def reflection_node(state: AgentState):
    print("--> Calling Reflection Node")
    news = state.get('news_signal')
    price = state.get('price_signal')
    
    # 1. Low-Level Reflection: Correlation between News & Price
    low_level = low_level_reflection(
        news_summary=news.summary if news else "No news",
        price_trend=f"{price.trend} (Volatility: {price.volatility})" if price else "No price data"
    )
    
    return {"reflections": f"### Logic Check:\n{low_level}"}

def memory_node(state: AgentState):
    print("--> Calling Memory Node (Retrieval)")
    # Retrieve similar past events based on current reflection/situation
    current_context = state.get('reflections', '')
    memories = retrieve_similar_events(current_context)
    return {"memories": memories}

def high_level_reflection_node(state: AgentState):
    print("--> Calling High-Level Reflection Node")
    memories = state.get('memories', [])
    existing_reflections = state.get('reflections', '')
    
    # Reflect on the retrieved memories to find patterns
    high_level = high_level_reflection(past_decisions=memories)
    
    combined_reflection = f"{existing_reflections}\n\n### Strategic Analysis:\n{high_level}"
    return {"reflections": combined_reflection}

def synthesis_node(state: AgentState):
    print("--> Calling Decision Maker (Synthesis)")
    
    price = state.get('price_signal')
    news = state.get('news_signal')
    memories = state.get('memories')
    reflections = state.get('reflections')
    
    # Extract ticker from initial message if possible, else default
    ticker = "Target Asset" 
    if state['messages']:
        content = state['messages'][0].content
        if "Analyze " in content:
            ticker = content.split("Analyze ")[1].split(".")[0].split()[0]

    # Convert signals to dicts for the module
    price_dict = price.model_dump() if price else {}
    # Flatten price signal to match expected "price_patterns" dict format somewhat
    # The module expects specific keys: current_price, trend, volatility_score, etc.
    # Our PriceSignal has: trend, volatility, key_levels, signal, confidence.
    # We map them to ensure best compatibility.
    price_patterns = {
        "current_price": "See Key Levels",
        "trend": price.trend,
        "period_change_pct": "N/A", # Agent abstraction
        "volatility_score": price.volatility,
        "recent_pattern": price.signal,
        "history_summary": str(price.key_levels)
    }

    decision_json = make_decision(
        ticker=ticker,
        news_summary=news.summary if news else "",
        memories=memories,
        reflections=reflections,
        price_patterns=price_patterns
    )
    
    # Convert validated JSON back to TradingSignal object for consistency
    final_signal = TradingSignal(**decision_json)
    
    return {"final_signal": final_signal}

def storage_node(state: AgentState):
    print("--> Calling Storage Node (Learning)")
    
    final_signal = state.get('final_signal')
    news = state.get('news_signal')
    full_news = state.get('news_context', "No detailed search data.")
    
    if final_signal:
        store_event(
            ticker=state['ticker'], 
            summary=news.summary, 
            action=final_signal.decision, 
            reasoning=final_signal.reasoning,
            grounding_data=full_news
        )
        print("    [Storage] Decision saved to long-term memory.")
        
    return {}

# --- 3. Build the Graph ---
builder = StateGraph(AgentState)

builder.add_node("PriceAgent", call_price_agent)
builder.add_node("NewsAgent", call_news_agent)
builder.add_node("Reflection", reflection_node)
builder.add_node("MemoryRetrieval", memory_node)
builder.add_node("StrategyAnalysis", high_level_reflection_node)
builder.add_node("Synthesis", synthesis_node)
builder.add_node("Storage", storage_node)

# Flow
builder.add_edge(START, "PriceAgent")
builder.add_edge("PriceAgent", "NewsAgent")
builder.add_edge("NewsAgent", "Reflection")
builder.add_edge("Reflection", "MemoryRetrieval")
builder.add_edge("MemoryRetrieval", "StrategyAnalysis")
builder.add_edge("StrategyAnalysis", "Synthesis")
builder.add_edge("Synthesis", "Storage")
builder.add_edge("Storage", END)

graph = builder.compile()
