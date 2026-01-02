import argparse
import sys
import os
import json

# Ensure we can import from modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage
from graph import graph

def run_finagent(ticker: str, query: str = None, verbose: bool = False):
    """
    Run the FinAgent trading analysis system.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA, GOOGL)
        query: Optional specific question or focus for the analysis
        verbose: If True, print detailed intermediate results
    """
    print("=" * 60)
    print(f"   Starting FinAgent Analysis for {ticker}")
    print("=" * 60)
    print()
    
    # Build user input
    if query:
        print(f"--> User Query: {query}")
        user_input = f"Analyze {ticker}. Focus on this specific request: {query}"
    else:
        user_input = f"Analyze {ticker}"
        
    print("--> Invoking Agent Graph...")
    print("    Pipeline: ExtractTicker -> PriceAgent -> NewsAgent -> Reflection -> Memory -> Strategy -> Decision -> Storage")
    print()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "ticker": ticker
    }
    
    # Run the graph
    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        print(f"\n[ERROR] Graph execution failed: {e}")
        print("Please check your API keys and network connection.")
        return None
    
    # Extract results
    final_signal = result.get("final_signal")
    multi_tf_data = result.get("multi_timeframe_data", {})
    reflections = result.get("reflections", {})
    
    # Print results
    print()
    print("=" * 60)
    print("   ANALYSIS COMPLETE")
    print("=" * 60)
    
    # Multi-timeframe summary
    if multi_tf_data and verbose:
        print("\n" + "-" * 40)
        print("MULTI-TIMEFRAME ANALYSIS")
        print("-" * 40)
        
        for tf in ["short_term", "medium_term", "long_term"]:
            data = multi_tf_data.get(tf, {})
            print(f"\n{tf.upper().replace('_', ' ')}:")
            print(f"  Trend: {data.get('trend', 'N/A')}")
            print(f"  Change: {data.get('period_change_pct', 'N/A')}%")
            print(f"  Volatility: {data.get('volatility_score', 'N/A')}")
        
        print(f"\nTrend Alignment: {multi_tf_data.get('trend_alignment', 'N/A')}")
        
        # Technical indicators
        indicators = multi_tf_data.get("technical_indicators", {})
        if indicators:
            print("\nTECHNICAL INDICATORS:")
            macd = indicators.get("macd", {})
            rsi = indicators.get("rsi", {})
            ma = indicators.get("moving_averages", {})
            print(f"  MACD: {macd.get('interpretation', 'N/A')}")
            print(f"  RSI: {rsi.get('value', 'N/A')} ({rsi.get('interpretation', 'N/A')})")
            print(f"  MA Trend: {ma.get('trend', 'N/A')}")
    
    # Final trading signal
    if final_signal:
        print("\n" + "=" * 40)
        print("FINAL TRADING SIGNAL")
        print("=" * 40)
        
        print(f"\n  Decision:   {final_signal.decision.value}")
        print(f"  Confidence: {final_signal.confidence:.1%}")
        print(f"  Timeframe:  {final_signal.timeframe}")
        
        print(f"\n  Reasoning:")
        for line in final_signal.reasoning.split('. '):
            if line.strip():
                print(f"    - {line.strip()}.")
        
        print(f"\n  Risk Factors:")
        for line in final_signal.risk_factors.split('. '):
            if line.strip():
                print(f"    ! {line.strip()}.")
        
        # JSON output
        print("\n" + "-" * 40)
        print("STRUCTURED OUTPUT (JSON)")
        print("-" * 40)
        print(final_signal.model_dump_json(indent=2))
        
    elif result["messages"]:
        # Fallback to text if structured failed
        final_message = result["messages"][-1]
        print("\n" + "-" * 40)
        print("FINAL OUTPUT (Unstructured Fallback)")
        print("-" * 40)
        print(final_message.content)
    else:
        print("\n[WARNING] No output from graph.")
    
    print("\n" + "=" * 60)
    print("   Analysis Complete")
    print("=" * 60)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="FinAgent - Multi-Agent Trading Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python workflow.py --ticker AAPL
  python workflow.py --ticker TSLA --query "Should I buy before earnings?"
  python workflow.py --ticker NVDA --verbose
        """
    )
    parser.add_argument(
        "--ticker", 
        type=str, 
        required=True, 
        help="Stock ticker symbol (e.g., AAPL, TSLA, GOOGL)"
    )
    parser.add_argument(
        "--query", 
        type=str, 
        required=False, 
        help="Specific question or focus for the analysis"
    )
    parser.add_argument(
        "--verbose", 
        "-v",
        action="store_true",
        help="Print detailed intermediate results"
    )
    
    args = parser.parse_args()
    run_finagent(args.ticker, args.query, args.verbose)


if __name__ == "__main__":
    main()
