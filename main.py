from dotenv import load_dotenv
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# --- CHANGED: Using Google GenAI ---
from langchain_google_genai import ChatGoogleGenerativeAI

# Import the new Multi-Agent Graph
from graph import graph as agent
from langgraph.checkpoint.memory import InMemorySaver

import yfinance as yf

load_dotenv()

app = FastAPI()

# We don't need to define model/tools here anymore, they are in agents.py and graph.py

# Checkpointer is handled inside graph.py or main.py? 
# The graph in graph.py is compiled. We can pass a checkpointer when invoking, 
# or compile it with one. Let's assume we pass config with thread_id which LangGraph handles if compiled with checkpointer.
# For now, let's just use the compiled graph directly. If we need persistence, we should attach checkpointer in graph.py
# Let's check graph.py content... it compiled without checkpointer. 
# We should probably update graph.py to include checkpointer if we want memory.
# For now, let's just import 'agent' which is the compiled graph.


class PromptObject(BaseModel):
    content: str
    id: str
    role: str


class RequestObject(BaseModel):
    prompt: PromptObject
    threadId: str
    responseId: str


@app.post('/api/chat')
async def chat(request: RequestObject):
    config = {'configurable': {'thread_id': request.threadId}}

    def generate():
        for token, _ in agent.stream(
            {'messages': [
                SystemMessage('You are a stock analysis assistant. You have the ability to get real-time stock prices, historical stock prices (given a date range), news and balance sheet data for a given ticker symbol.'),
                HumanMessage(request.prompt.content)
            ]},
            stream_mode='messages',
            config=config
        ):
            yield token.content

    return StreamingResponse(generate(), media_type='text/event-stream',
                             headers={
                                 'Cache-Control': 'no-cache, no-transform',
                                 'Connection': 'keep-alive',
                             })

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8888)