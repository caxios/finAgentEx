import argparse
import sys
import os
import json

# Ensure we can import from modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# CORRECT IMPORTS from modules/
from modules.market_intelligence import fetch_market_data, analyze_price_patterns
from modules.memory import retrieve_similar_events, store_event
from modules.reflection import low_level_reflection, high_level_reflection
from modules.decision_maker import make_decision

def run_finagent(ticker: str):
    print(f"=== Starting FinAgent for {ticker} ===\n")
    
    # Step 1: Fetch Data
    # news_summary is now directly returned from Google Grounding
    hist, news_summary = fetch_market_data(ticker)
    print(f"--> Market Data Fetched. Latest Close: {hist['Close'].iloc[-1]:.2f}")
    
    # Step 1.5: Programmatic Price Analysis
    patterns = analyze_price_patterns(hist)
    
    # Step 2: [Skipped Visuals]
    
    # Step 3: Retrieve Memory
    # we use the news summary as the query to find similar news events
    memories = retrieve_similar_events(query=news_summary)
    print(f"--> Retrieved {len(memories)} past similar events.")
    
    # Step 4: Reflect
    # Low-level: Correlation
    recent_trend = patterns['trend']
    ll_reflection = low_level_reflection(news_summary, f"Price is {recent_trend}, Recent Pattern: {patterns['recent_pattern']}")
    
    # High-level: Strategy check (using retrieved memories as proxy for past decisions)
    # Extract past actions from memories to reflect on
    past_actions_text = [m for m in memories if "Action:" in m]
    hl_reflection = high_level_reflection(past_actions_text)
    
    full_reflection = f"Low-Level: {ll_reflection}\nHigh-Level: {hl_reflection}"
    print("--> Reflection Completed.")
    
    # Step 5: Decide
    decision = make_decision(ticker, news_summary, memories, full_reflection, patterns)
    
    print("\n=== FINAL TRADING DECISION ===")
    print(f"ACTION: {decision['Action']}")
    print(f"CONFIDENCE: {decision['Confidence']}")
    print(f"REASONING: {decision['Reasoning']}")
    print("==============================\n")
    
    # Step 6: Store
    store_event(
        ticker=ticker,
        summary=news_summary,
        action=decision['Action'],
        reasoning=decision['Reasoning']
    )
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAgent Trading System")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker (e.g., AAPL)")
    args = parser.parse_args()
    
    run_finagent(args.ticker)
