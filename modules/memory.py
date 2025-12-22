import chromadb
from chromadb.utils import embedding_functions
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# Setup ChromaDB
db_path = "modules/chroma_db"
os.makedirs(db_path, exist_ok=True)

client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(name="market_memory")

def store_event(ticker: str, summary: str, action: str, reasoning: str):
    """
    Stores a trading decision and its context.
    """
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # We combine info into a text document to embed
    document = f"Date: {date_str} | Ticker: {ticker} | Action: {action} | Reasoning: {reasoning} | EventSummary: {summary}"
    
    collection.add(
        documents=[document],
        metadatas=[{"ticker": ticker, "date": date_str, "action": action, "type": "daily_decision"}],
        ids=[f"{ticker}_{date_str}_{datetime.datetime.now().timestamp()}"]
    )
    print(f"Stored event for {ticker} in memory.")

def retrieve_similar_events(query: str, n_results: int = 3):
    """
    Diversified Retrieval: Fetches similar past events based on the query.
    """
    print(f"Retrieving memories for: {query[:50]}...")
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Flatten results
    memories = []
    if results['documents']:
        for doc in results['documents'][0]:
            memories.append(doc)
            
    return memories
