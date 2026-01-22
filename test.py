"""
Test script for Multi-Agent Stock Analysis System
"""

from graph import graph, analyze_stock
from langchain_core.messages import HumanMessage


def test_single_stock(ticker: str = "AAPL"):
    """Test the multi-agent system with a single stock."""
    print(f"\n{'='*70}")
    print(f"TESTING MULTI-AGENT ANALYSIS FOR: {ticker}")
    print(f"{'='*70}\n")
    
    # Run the analysis
    signal = analyze_stock(ticker)
    
    if signal:
        print(f"\n{'='*70}")
        print("FINAL RESULT")
        print(f"{'='*70}")
        print(f"Ticker: {ticker}")
        print(f"Decision: {signal.decision.value}")
        print(f"Confidence: {signal.confidence:.0%}")
        print(f"Timeframe: {signal.timeframe}")
        print(f"\nReasoning:\n{signal.reasoning}")
        print(f"\nRisk Factors:\n{signal.risk_factors}")
        print(f"{'='*70}\n")
        return signal
    else:
        print("Analysis failed - no signal returned")
        return None


def test_data_tools():
    """Test the data tools module directly."""
    from data_tools import (
        fetch_period_data,
        fetch_news_for_ticker,
        fetch_single_ticker_data,
        generate_technical_chart,
        get_cache_info
    )
    
    print("\n" + "="*50)
    print("TESTING DATA TOOLS")
    print("="*50 + "\n")
    
    ticker = "MSFT"
    
    # Test news fetching
    print("1. Testing fetch_news_for_ticker...")
    news = fetch_news_for_ticker(ticker, count=5)
    print(f"   Retrieved {len(news)} news articles")
    for i, article in enumerate(news[:3], 1):
        print(f"   {i}. {article['title'][:50]}...")
    
    # Test OHLCV data fetching
    print("\n2. Testing fetch_single_ticker_data...")
    df = fetch_single_ticker_data(ticker, period="1mo")
    if df is not None:
        print(f"   Retrieved {len(df)} rows of OHLCV data")
        print(f"   Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"   Current price: ${df['Close'].iloc[-1]:.2f}")
    
    # Test chart generation
    print("\n3. Testing generate_technical_chart...")
    if df is not None:
        chart_path = generate_technical_chart(ticker, df)
        print(f"   Chart saved to: {chart_path}")
    
    # Test cache
    print("\n4. Testing cache...")
    cache_info = get_cache_info()
    print(f"   Cached entries: {cache_info['total_entries']}")
    print(f"   Cached keys: {cache_info['cached_keys']}")
    
    print("\n" + "="*50)
    print("DATA TOOLS TEST COMPLETE")
    print("="*50 + "\n")


def test_graph_state():
    """Test the graph with full state inspection."""
    print("\n" + "="*50)
    print("TESTING GRAPH STATE")
    print("="*50 + "\n")
    
    result = graph.invoke({
        "ticker": "NVDA",
        "messages": [HumanMessage(content="Analyze NVDA")]
    })
    
    print("\nFinal State Keys:")
    for key in result.keys():
        value = result[key]
        if value is not None:
            if isinstance(value, str):
                print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
            elif isinstance(value, dict):
                print(f"  {key}: {{{len(value)} keys}}")
            else:
                print(f"  {key}: {type(value).__name__}")
        else:
            print(f"  {key}: None")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tools":
            test_data_tools()
        elif sys.argv[1] == "--state":
            test_graph_state()
        else:
            test_single_stock(sys.argv[1])
    else:
        # Default: test with AAPL
        test_single_stock("AAPL")