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

def run_finagent(ticker: str):
    print(f"=== Starting FinAgent for {ticker} ===\n")
    print("--> Invoking Agent Graph (Price -> News -> Synthesis)...")
    
    # Run the graph
    # Note: This will trigger API calls. 
    # Use 'invoke' to run to completion.
    initial_state = {"messages": [HumanMessage(content=f"Analyze {ticker}")]}
    result = graph.invoke(initial_state)
    
    # Extract the final response
    if result["messages"]:
        final_message = result["messages"][-1]
        print("\n=== FINAL OUTPUT ===")
        print(final_message.content)
        print("====================\n")
    else:
        print("No output from graph.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAgent Trading System")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker (e.g., AAPL)")
    args = parser.parse_args()
    
    run_finagent(args.ticker)
