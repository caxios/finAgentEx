from typing import Annotated, TypedDict, Optional
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from agents import price_agent, news_agent, news_prompt
from modules.models import PriceSignal, NewsSignal, TradingSignal
import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. Define State ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    price_signal: Optional[PriceSignal]
    news_signal: Optional[NewsSignal]
    final_signal: Optional[TradingSignal]

model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0
)

# --- 2. Nodes ---

def call_price_agent(state: AgentState):
    print("--> Calling Price Agent (Structured)")
    response = price_agent.invoke({"messages": [HumanMessage(content="Perform a comprehensive price analysis for the requested ticker, covering the last 1 year of data.")]})
    
    # Extract the text response
    ai_msg = response["messages"][-1]
    
    # Structure it
    print("    [Price Agent] Converting to Structured Output...")
    structured_llm = model.with_structured_output(PriceSignal)
    signal = structured_llm.invoke(f"Extract the following analysis into a structured signal:\n\n{ai_msg.content}")
    
    return {
        "messages": [ai_msg], 
        "price_signal": signal
    }

def call_news_agent(state: AgentState):
    print("--> Calling News Agent (Structured)")
    # Pass context (Price Signal) to News Agent if useful, or just ensure continuity
    last_message = state['messages'][0] # User query
    
    # Inject system prompt
    messages = [SystemMessage(content=news_prompt), last_message]
    response = news_agent.invoke({"messages": messages})
    
    ai_msg = response["messages"][-1]
    
    # Structure it
    print("    [News Agent] Converting to Structured Output...")
    structured_llm = model.with_structured_output(NewsSignal)
    signal = structured_llm.invoke(f"Extract the following news analysis into a structured signal:\n\n{ai_msg.content}")
    
    return {
        "messages": [ai_msg],
        "news_signal": signal
    }

def synthesis_node(state: AgentState):
    print("--> Calling Synthesis Node (Structured)")
    
    price = state.get('price_signal')
    news = state.get('news_signal')
    
    if not price or not news:
        return {"messages": [HumanMessage(content="Error: Missing signals for synthesis.")]}

    synthesis_prompt = f"""You are a Financial Analyst.
    Synthesize the following structured signals into a final trading decision.
    
    PRICE ANALYSIS:
    Signal: {price.signal}
    Trend: {price.trend}
    Volatility: {price.volatility}
    
    NEWS ANALYSIS:
    Signal: {news.signal}
    Sentiment: {news.sentiment}
    Summary: {news.summary}
    
    Goal: Predict the next price movement and provide a structured rationale.
    """
    
    structured_llm = model.with_structured_output(TradingSignal)
    final_signal = structured_llm.invoke(synthesis_prompt)
    
    # Return the object in state
    return {"final_signal": final_signal}

# --- 3. Build the Graph ---
builder = StateGraph(AgentState)

builder.add_node("PriceAgent", call_price_agent)
builder.add_node("NewsAgent", call_news_agent)
builder.add_node("Synthesis", synthesis_node)

# Linear Flow
builder.add_edge(START, "PriceAgent")
builder.add_edge("PriceAgent", "NewsAgent")
builder.add_edge("NewsAgent", "Synthesis")
builder.add_edge("Synthesis", END)

graph = builder.compile()
