import argparse
import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Ensure we can import from modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import graph
from langchain_core.messages import HumanMessage

def run_finagent(ticker: str, query: str = None):
    print(f"=== Starting FinAgent for {ticker} ===\n")
    if query:
        print(f"--> User Query: {query}")
        user_input = f"Analyze {ticker}. Focus on this specific request: {query}"
    else:
        user_input = f"Analyze {ticker}"
        
    print("--> Invoking Agent Graph (Price -> News -> Synthesis)...")
    
    # Run the graph
    # Note: This will trigger API calls. 
    # Use 'invoke' to run to completion.
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    result = graph.invoke(initial_state)
    
    # Extract the final structured response
    final_signal = result.get("final_signal")
    
    if final_signal:
        print("\n=== FINAL TRADING SIGNAL (Structured) ===")
        print(final_signal.model_dump_json(indent=2))
        print("=========================================\n")
    elif result["messages"]:
        # Fallback to text if structured failed
        final_message = result["messages"][-1]
        print("\n=== FINAL OUTPUT (Unstructured Fallback) ===")
        print(final_message.content)
        print("====================\n")
    else:
        print("No output from graph.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAgent Trading System")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker (e.g., AAPL)")
    parser.add_argument("--query", type=str, required=False, help="Specific question or focus")
    args = parser.parse_args()
    
    run_finagent(args.ticker, args.query)
