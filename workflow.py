import argparse
import sys
import os

# Ensure we can import from modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.market_intelligence import fetch_market_data, generate_chart, format_news
from modules.memory import retrieve_similar_events, store_event
from modules.reflection import low_level_reflection, high_level_reflection
from modules.decision_maker import make_decision

def run_finagent(ticker: str):
    print(f"=== Starting FinAgent for {ticker} ===\n")
    
    # Step 1: Fetch Data
    hist, news = fetch_market_data(ticker)
    news_summary = format_news(news)
    print(f"--> Market Data Fetched. Latest Close: {hist['Close'].iloc[-1]:.2f}")
    
    # Step 2: Visualize
    chart_path = generate_chart(ticker, hist)
    print(f"--> Chart Generated: {chart_path}")
    
    # Step 3: Retrieve Memory
    # we use the news summary as the query to find similar news events
    memories = retrieve_similar_events(query=news_summary)
    
    # Step 4: Reflect
    # Low-level: Correlation
    recent_trend = "Up" if hist['Close'].iloc[-1] > hist['Close'].iloc[-2] else "Down"
    ll_reflection = low_level_reflection(news_summary, f"Price went {recent_trend}")
    
    # High-level: Strategy check (using retrieved memories as proxy for past decisions)
    # Extract past actions from memories to reflect on
    past_actions_text = [m for m in memories if "Action:" in m]
    hl_reflection = high_level_reflection(past_actions_text)
    
    full_reflection = f"Low-Level: {ll_reflection}\nHigh-Level: {hl_reflection}"
    print("--> Reflection Completed.")
    
    # Step 5: Decide
    decision = make_decision(ticker, news_summary, memories, full_reflection, chart_path)
    
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
