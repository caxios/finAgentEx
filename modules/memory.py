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


def store_event(
    ticker: str, 
    summary: str, 
    action: str, 
    reasoning: str, 
    grounding_data: str = "",
    confidence: float = 0.0,
    timeframe: str = "",
    price_at_decision: float = 0.0
):
    """
    Stores a trading decision and its context, including full news content.
    Enhanced with richer metadata for better retrieval.
    """
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now().timestamp()
    
    # We combine info into a text document to embed
    # We append the grounding data (full search results) to the document so it is searchable
    document = f"""Date: {date_str}
Ticker: {ticker}
Action: {action}
Confidence: {confidence}
Timeframe: {timeframe}
Price: {price_at_decision}
Reasoning: {reasoning}
EventSummary: {summary}
FullContext: {grounding_data}"""
    
    # Rich metadata for filtering and retrieval
    metadata = {
        "ticker": ticker, 
        "date": date_str, 
        "action": action, 
        "type": "daily_decision",
        "confidence": confidence,
        "timeframe": timeframe,
        "price": price_at_decision,
        "timestamp": timestamp
    }
    
    collection.add(
        documents=[document],
        metadatas=[metadata],
        ids=[f"{ticker}_{date_str}_{timestamp}"]
    )
    print(f"Stored event for {ticker} in memory (action: {action}, confidence: {confidence}).")


def retrieve_similar_events(query: str, n_results: int = 3) -> list:
    """
    Basic retrieval: Fetches similar past events based on the query.
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


def retrieve_by_ticker(ticker: str, n_results: int = 5) -> list:
    """
    Retrieves past decisions for a specific ticker.
    """
    print(f"Retrieving ticker-specific memories for: {ticker}...")
    
    try:
        results = collection.get(
            where={"ticker": ticker},
            limit=n_results
        )
        
        if results['documents']:
            return results['documents']
    except Exception as e:
        print(f"Error retrieving by ticker: {e}")
    
    return []


def retrieve_by_action(action: str, n_results: int = 3) -> list:
    """
    Retrieves past decisions with a specific action (BUY/SELL/HOLD).
    """
    print(f"Retrieving action-specific memories for: {action}...")
    
    try:
        results = collection.get(
            where={"action": action},
            limit=n_results
        )
        
        if results['documents']:
            return results['documents']
    except Exception as e:
        print(f"Error retrieving by action: {e}")
    
    return []


def retrieve_diversified(query: str, ticker: str = None, n_results: int = 5) -> list:
    """
    Diversified Retrieval: Uses multiple strategies to get comprehensive context.
    
    Strategy 1: Semantic similarity to current query
    Strategy 2: Ticker-specific history  
    Strategy 3: Similar action patterns
    
    This approach prevents over-reliance on any single retrieval method.
    """
    print(f"Performing diversified retrieval...")
    all_memories = []
    seen_ids = set()
    
    # Strategy 1: Semantic similarity to current context
    try:
        semantic_results = collection.query(
            query_texts=[query],
            n_results=min(2, n_results)
        )
        if semantic_results['documents'] and semantic_results['documents'][0]:
            for i, doc in enumerate(semantic_results['documents'][0]):
                doc_id = semantic_results['ids'][0][i] if semantic_results['ids'] else str(i)
                if doc_id not in seen_ids:
                    all_memories.append({
                        "source": "semantic_similarity",
                        "content": doc,
                        "metadata": semantic_results['metadatas'][0][i] if semantic_results['metadatas'] else {}
                    })
                    seen_ids.add(doc_id)
    except Exception as e:
        print(f"Semantic retrieval error: {e}")
    
    # Strategy 2: Ticker-specific history
    if ticker:
        try:
            ticker_results = collection.get(
                where={"ticker": ticker},
                limit=min(2, n_results)
            )
            if ticker_results['documents']:
                for i, doc in enumerate(ticker_results['documents']):
                    doc_id = ticker_results['ids'][i] if ticker_results['ids'] else f"ticker_{i}"
                    if doc_id not in seen_ids:
                        all_memories.append({
                            "source": "ticker_history",
                            "content": doc,
                            "metadata": ticker_results['metadatas'][i] if ticker_results['metadatas'] else {}
                        })
                        seen_ids.add(doc_id)
        except Exception as e:
            print(f"Ticker retrieval error: {e}")
    
    # Strategy 3: Recent high-confidence decisions (learning from success)
    try:
        # Query recent entries and filter by high confidence
        recent_results = collection.query(
            query_texts=["trading decision analysis market"],
            n_results=min(3, n_results),
            where={"confidence": {"$gte": 0.7}}  # High confidence decisions
        )
        if recent_results['documents'] and recent_results['documents'][0]:
            for i, doc in enumerate(recent_results['documents'][0]):
                doc_id = recent_results['ids'][0][i] if recent_results['ids'] else f"recent_{i}"
                if doc_id not in seen_ids:
                    all_memories.append({
                        "source": "high_confidence_history",
                        "content": doc,
                        "metadata": recent_results['metadatas'][0][i] if recent_results['metadatas'] else {}
                    })
                    seen_ids.add(doc_id)
    except Exception as e:
        print(f"High-confidence retrieval error: {e}")
    
    # Limit total results
    all_memories = all_memories[:n_results]
    
    print(f"Retrieved {len(all_memories)} diversified memories")
    return all_memories


def format_memories_for_prompt(memories: list) -> str:
    """
    Formats retrieved memories into a string suitable for LLM prompts.
    """
    if not memories:
        return "No relevant past decisions found in memory."
    
    formatted = []
    for i, mem in enumerate(memories, 1):
        if isinstance(mem, dict):
            source = mem.get("source", "unknown")
            content = mem.get("content", str(mem))
            metadata = mem.get("metadata", {})
            
            formatted.append(f"--- Memory {i} (source: {source}) ---")
            if metadata:
                formatted.append(f"Ticker: {metadata.get('ticker', 'N/A')}, Action: {metadata.get('action', 'N/A')}, Date: {metadata.get('date', 'N/A')}")
            formatted.append(content)
        else:
            formatted.append(f"--- Memory {i} ---")
            formatted.append(str(mem))
        formatted.append("")
    
    return "\n".join(formatted)
