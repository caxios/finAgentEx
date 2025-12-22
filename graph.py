from typing import Annotated, Literal, TypedDict
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from agents import price_agent, news_agent
from dotenv import load_dotenv

load_dotenv()

# --- 1. Define State ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # We can track who acted last to help routing
    next_step: str

# --- 2. Supervisor / Router ---
# The Supervisor decides which agent to call next or if we are done.
# It outputs a structured decision: "News", "Price", or "FINISH".

model = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0
)

# A simple system-prompt-based router
supervisor_prompt = """You are a supervisor tasked with managing a conversation between the following workers: {members}. 
Given the following user request, respond with the worker to act next. 
Each worker will perform a task and respond with their results and status. 
When finished, respond with FINISH.

The workers are:
- PriceAgent: Gets stock prices, history, and balance sheets.
- NewsAgent: Gets recent news about companies.

Select the next worker based on what information is missing to answer the user's question completely.
"""

members = ["PriceAgent", "NewsAgent"]
options = ["FINISH"] + members

# Using structured output (function calling) for reliable routing
class RouteResponse(TypedDict):
    next: Literal["PriceAgent", "NewsAgent", "FINISH"]

def supervisor_node(state: AgentState):
    messages = [
        {"role": "system", "content": supervisor_prompt.format(members=members)},
    ] + state["messages"]
    
    # We ask the model to predict the next step
    response = model.with_structured_output(RouteResponse).invoke(messages)
    next_agent = response["next"]
    
    return {"next_step": next_agent}

# --- 3. Nodes Wrappers ---
# We need to wrap our react agents to fit into the graph format if needed,
# but since they are already compiled graphs (LangGraph agents), we can invoke them directly.

def call_price_agent(state: AgentState):
    # We delegate to the price agent. 
    # It returns a new state dictionary like {'messages': [...]}.
    # The 'add_messages' reducer in AgentState will handle merging.
    response = price_agent.invoke(state)
    return {"messages": [response["messages"][-1]]} # Return the last message (the agent's conclusion)

def call_news_agent(state: AgentState):
    response = news_agent.invoke(state)
    return {"messages": [response["messages"][-1]]}

# --- 4. Build the Graph ---
builder = StateGraph(AgentState)

builder.add_node("Supervisor", supervisor_node)
builder.add_node("PriceAgent", call_price_agent)
builder.add_node("NewsAgent", call_news_agent)

builder.add_edge(START, "Supervisor")

# Conditional edges from Supervisor
def router(state: AgentState):
    # The supervisor node updates 'next_step' in the state
    return state["next_step"]

builder.add_conditional_edges(
    "Supervisor",
    router,
    {
        "PriceAgent": "PriceAgent",
        "NewsAgent": "NewsAgent",
        "FINISH": END
    }
)

# Edges from workers back to Supervisor
builder.add_edge("PriceAgent", "Supervisor")
builder.add_edge("NewsAgent", "Supervisor")

graph = builder.compile()
