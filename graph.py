from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from agents import price_agent, news_agent, news_prompt
from dotenv import load_dotenv

load_dotenv()

# --- 1. Define State ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

model = ChatGoogleGenerativeAI(
    model='gemini-pro-latest',
    temperature=0
)

# --- 2. Nodes ---

def call_price_agent(state: AgentState):
    print("--> Calling Price Agent")
    # We instruct the Price Agent to perform the analysis
    response = price_agent.invoke({"messages": [HumanMessage(content="Perform a comprehensive price analysis for the requested ticker. Use the get_price_analysis tool.")]})
    # We add a tag or prefix to identify this as price analysis if needed, but the content should be self-explanatory.
    return {"messages": [response["messages"][-1]]}

def call_news_agent(state: AgentState):
    print("--> Calling News Agent")
    # We instruct the News Agent to find signals
    last_message = state['messages'][0]
    # Inject system prompt
    messages = [SystemMessage(content=news_prompt), last_message]
    response = news_agent.invoke({"messages": messages})
    return {"messages": [response["messages"][-1]]}

def synthesis_node(state: AgentState):
    print("--> Calling Synthesis Node")
    messages = state['messages']
    
    # We construct a prompt for the synthesis
    synthesis_prompt = """You are a Financial Analyst.
    Review the following Price Analysis and News Analysis.
    
    Goal: Predict the next price movement interactively based on how news contextualizes recent price action.
    Do NOT output an image. Output a structured text prediction.
    
    Structure your response as:
    1. MARKET CONTEXT: Synthesis of price and news.
    2. PREDICTION: Up/Down/Sideways with confidence level.
    3. RATIONALE: Why?
    """
    
    # We invoke the model directly for synthesis
    synthesis_messages = [
        {"role": "system", "content": synthesis_prompt}
    ] + messages 
    
    response = model.invoke(synthesis_messages)
    return {"messages": [response]}

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
