"""
Multi-Agent System Graph for Stock Analysis
7-Agent Architecture:
  - Agent 1 (News): Fetches news using yfinance
  - Agent 2 (Blogs): Fetches blog/social opinion using Tavily API
  - Agent 3 (Data): Fetches OHLCV data and generates charts
  - Agent 4 (Tech Analysis): Analyzes charts using Gemini Vision
  - Agent 5 (Sentiment): Analyzes text from Agents 1 & 2
  - Agent 6 (Fundamentals): Fetches SEC EDGAR financial data
  - Agent 7 (Strategy): Final decision maker
"""

from typing import Annotated, TypedDict, Optional, List, Dict
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from modules.models import TradingSignal, SignalType, SentimentType
from data_tools import (
    fetch_period_data, 
    fetch_news_for_ticker, 
    generate_technical_chart,
    fetch_single_ticker_data
)
import os
import re
import base64
from dotenv import load_dotenv
import json

load_dotenv()

# --- Initialize Models ---
model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL', 'gemini-2.5-flash-lite'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# Gemini Vision model for chart analysis (uses same model as main)
vision_model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL', 'gemini-2.0-flash'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# Strategy model for final decision (more powerful model)
strategy_model = ChatGoogleGenerativeAI(
    model=os.getenv('STRATEGY_MODEL', 'gemini-2.5-pro'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# Tavily API for blog search (optional - check if available)
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
tavily_client = None
if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print("[] Tavily client initialized")
    except ImportError:
        print("[!] Tavily not installed. Blog agent will use fallback.")
    except Exception as e:
        print(f"[!] Tavily initialization failed: {e}")




# --- 1. Define Agent State ---
class AgentState(TypedDict):
    """State shared across all agents in the graph."""
    ticker: str
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Agent 1 (News) Output
    news_data: Optional[List[dict]]           # Raw news from yfinance
    
    # Agent 2 (Blogs) Output  
    blog_data: Optional[List[dict]]           # Blog/social from Tavily
    
    # Agent 3 (Data) Output
    ohlcv_data: Optional[Dict]                # OHLCV data summary
    chart_path: Optional[str]                 # Path to generated chart
    
    # Agent 4 (Tech Analysis) Output
    technical_analysis: Optional[str]         # Vision analysis result
    
    # Agent 5 (Sentiment) Output
    sentiment_analysis: Optional[Dict]        # Combined sentiment analysis
    
    # Agent 6 (Fundamentals) Output
    fundamentals_data: Optional[Dict]         # SEC EDGAR financial data
    
    # Agent 7 (Strategy) Output
    final_signal: Optional[TradingSignal]     # Final trading decision


# --- 2. Helper Functions ---

def extract_ticker_from_message(content: str) -> str:
    """Extract stock ticker from user message."""
    patterns = [
        r'Analyze\s+(\w+)',           # "Analyze AAPL"
        r'ticker[:\s]+(\w+)',          # "ticker: AAPL"
        r'\b([A-Z]{1,5})\b',           # Any 1-5 uppercase letters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return "UNKNOWN"


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for Gemini Vision."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --- 3. Agent Nodes ---

def extract_ticker_node(state: AgentState) -> dict:
    """
    Extract ticker from the initial message at the start of the workflow.
    """
    print("\n" + "="*60)
    print(" MULTI-AGENT STOCK ANALYSIS SYSTEM")
    print("="*60)
    print("\n---> Extracting Ticker from Input")
    
    ticker = state.get('ticker', '')
    
    if not ticker and state['messages']:
        content = state['messages'][0].content
        ticker = extract_ticker_from_message(content)
    
    if not ticker:
        ticker = "UNKNOWN"
    
    print(f"      Ticker identified: {ticker}")
    return {"ticker": ticker}


def news_agent_node(state: AgentState) -> dict:
    """
    Agent 1: News Agent
    Fetches news using yfinance following Reference Code B.
    """
    print("\n---> Agent 1: News Agent (yfinance)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Fetch news using the reference code pattern (uses default count from data_tools)
    news_list = fetch_news_for_ticker(ticker)
    
    if news_list:
        print(f"      Retrieved {len(news_list)} news articles")
        for i, article in enumerate(news_list[:3], 1):
            print(f"        {i}. {article['title'][:60]}...")
    else:
        print("      No news articles found")
    
    return {"news_data": news_list}


def blog_agent_node(state: AgentState) -> dict:
    """
    Agent 2: Blog/Social Agent
    Fetches blog and social opinion using Tavily API.
    """
    print("\n---> Agent 2: Blog/Social Agent (Tavily)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    blog_list = []
    
    if tavily_client:
        try:
            # Search for blog posts and social opinions
            query = f"{ticker} stock analysis opinion blog"
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=10,
                include_domains=["seekingalpha.com", "fool.com", "reddit.com", 
                                "stocktwits.com", "medium.com", "substack.com"]
            )
            
            for result in response.get('results', []):
                blog_list.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', ''),
                    'score': result.get('score', 0),
                    'source': result.get('url', '').split('/')[2] if result.get('url') else ''
                })
            
            print(f"      Retrieved {len(blog_list)} blog/social posts")
            for i, blog in enumerate(blog_list, 1):
                print(f"        {i}. [{blog['source']}] {blog['url']}")
            
        except Exception as e:
            print(f"      Tavily search failed: {e}")
    else:
        print("      Tavily not configured - using LLM to generate opinion summary")
        
        # Fallback: Use LLM to generate a summary based on general knowledge
        try:
            response = model.invoke([
                HumanMessage(content=f"""Based on your knowledge, provide a brief summary of 
                common investor opinions and sentiment about {ticker} stock. 
                Include perspectives from retail investors, analysts, and social media.
                Format as a brief paragraph.""")
            ])
            blog_list.append({
                'title': f"AI-Generated Sentiment Summary for {ticker}",
                'content': response.content,
                'url': None,
                'score': 0.5,
                'source': 'AI Summary'
            })
        except Exception as e:
            print(f"      Fallback also failed: {e}")
    
    return {"blog_data": blog_list}


def data_agent_node(state: AgentState) -> dict:
    """
    Agent 3: Data Agent
    Fetches OHLCV data using fetch_period_data and generates charts.
    """
    print("\n---> Agent 3: Data Agent (OHLCV + Charts)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Fetch OHLCV data using reference code pattern
    df = fetch_single_ticker_data(ticker, period="3mo")
    
    if df is None or df.empty:
        print(f"      No OHLCV data available for {ticker}")
        return {
            "ohlcv_data": None,
            "chart_path": None
        }
    
    # Generate summary statistics
    ohlcv_summary = {
        "ticker": ticker,
        "period": "3mo",
        "data_points": len(df),
        "start_date": str(df.index[0].date()),
        "end_date": str(df.index[-1].date()),
        "current_price": round(float(df['Close'].iloc[-1]), 2),
        "period_high": round(float(df['High'].max()), 2),
        "period_low": round(float(df['Low'].min()), 2),
        "period_change_pct": round(
            (float(df['Close'].iloc[-1]) / float(df['Close'].iloc[0]) - 1) * 100, 2
        ),
        "avg_volume": round(float(df['Volume'].mean()), 0),
        "volatility": round(float(df['Close'].pct_change().std() * 100), 2)
    }
    
    print(f"      Data Summary:")
    print(f"        Price: ${ohlcv_summary['current_price']} ({ohlcv_summary['period_change_pct']:+.2f}%)")
    print(f"        Range: ${ohlcv_summary['period_low']} - ${ohlcv_summary['period_high']}")
    print(f"        Volatility: {ohlcv_summary['volatility']:.2f}%")
    
    # Generate chart for technical analysis
    chart_path = generate_technical_chart(ticker, df)
    print(f"      Chart generated: {chart_path}")
    
    return {
        "ohlcv_data": ohlcv_summary,
        "chart_path": chart_path
    }


def fundamentals_agent_node(state: AgentState) -> dict:
    """
    Agent 6: Fundamentals Agent
    Fetches SEC EDGAR financial data (8 quarters / 2 years).
    Uses SQLite cache for persistence.
    """
    print("\n---> Agent 6: Fundamentals Agent (SEC EDGAR)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    
    # Try to import from SEC EDGAR
    try:
        from edgar import Company, set_identity
        from edgar.xbrl import XBRLS
        set_identity("FinAgentEx finagentex@example.com")
        
        company = Company(ticker)
        
        # Fetch last 8 quarterly reports (2 years)
        filings = company.get_filings(form="10-Q", amendments=False).head(8)
        
        if not filings or len(filings) == 0:
            print(f"      No quarterly filings found for {ticker}")
            return {"fundamentals_data": None}
        
        # Parse XBRL data
        xbrls = XBRLS.from_filings(filings)
        statements = xbrls.statements
        
        # Extract key metrics
        fundamentals = {
            "ticker": ticker,
            "periods_analyzed": len(filings),
            "metrics": {}
        }
        
        # Get income statement data
        try:
            income_stmt = statements.income_statement()
            if income_stmt:
                income_df = income_stmt.to_dataframe()
                
                # Extract Revenue
                revenue_row = income_df[income_df['label'].str.contains('Revenue|Sales', case=False, na=False)]
                if not revenue_row.empty:
                    revenue_cols = [c for c in income_df.columns if c not in ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence']]
                    revenues = {}
                    for col in revenue_cols[:8]:  # Last 8 quarters
                        val = revenue_row.iloc[0].get(col)
                        if val is not None and str(val) != 'nan':
                            try:
                                revenues[str(col)[:10]] = float(val)
                            except:
                                pass
                    if revenues:
                        fundamentals["metrics"]["revenue"] = revenues
                        # Calculate YoY growth
                        values = list(revenues.values())
                        if len(values) >= 5:
                            yoy_growth = ((values[0] - values[4]) / abs(values[4])) * 100 if values[4] != 0 else 0
                            fundamentals["metrics"]["revenue_yoy"] = round(yoy_growth, 2)
                
                # Extract Net Income
                net_income_row = income_df[income_df['label'].str.contains('Net Income|Net Earnings', case=False, na=False)]
                if not net_income_row.empty:
                    net_incomes = {}
                    for col in revenue_cols[:8]:
                        val = net_income_row.iloc[0].get(col)
                        if val is not None and str(val) != 'nan':
                            try:
                                net_incomes[str(col)[:10]] = float(val)
                            except:
                                pass
                    if net_incomes:
                        fundamentals["metrics"]["net_income"] = net_incomes
                        values = list(net_incomes.values())
                        if len(values) >= 5:
                            yoy_growth = ((values[0] - values[4]) / abs(values[4])) * 100 if values[4] != 0 else 0
                            fundamentals["metrics"]["net_income_yoy"] = round(yoy_growth, 2)
                            
        except Exception as e:
            print(f"      Error parsing income statement: {e}")
        
        # Get balance sheet data
        try:
            balance_stmt = statements.balance_sheet()
            if balance_stmt:
                balance_df = balance_stmt.to_dataframe()
                
                # Extract Total Assets
                assets_row = balance_df[balance_df['label'].str.contains('Total Assets', case=False, na=False)]
                if not assets_row.empty:
                    balance_cols = [c for c in balance_df.columns if c not in ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence']]
                    val = assets_row.iloc[0].get(balance_cols[0]) if balance_cols else None
                    if val is not None:
                        try:
                            fundamentals["metrics"]["total_assets"] = float(val)
                        except:
                            pass
                
                # Extract Total Debt/Liabilities
                debt_row = balance_df[balance_df['label'].str.contains('Total Liabilities|Long-term Debt', case=False, na=False)]
                if not debt_row.empty:
                    val = debt_row.iloc[0].get(balance_cols[0]) if balance_cols else None
                    if val is not None:
                        try:
                            fundamentals["metrics"]["total_liabilities"] = float(val)
                        except:
                            pass
                            
        except Exception as e:
            print(f"      Error parsing balance sheet: {e}")
        
        # Calculate key ratios
        metrics = fundamentals["metrics"]
        if "total_assets" in metrics and "total_liabilities" in metrics:
            equity = metrics["total_assets"] - metrics["total_liabilities"]
            if equity > 0:
                metrics["debt_to_equity"] = round(metrics["total_liabilities"] / equity, 2)
        
        # Print summary
        print(f"      Fundamentals Summary:")
        if "revenue_yoy" in metrics:
            print(f"        Revenue YoY: {metrics['revenue_yoy']:+.1f}%")
        if "net_income_yoy" in metrics:
            print(f"        Net Income YoY: {metrics['net_income_yoy']:+.1f}%")
        if "debt_to_equity" in metrics:
            print(f"        Debt/Equity: {metrics['debt_to_equity']:.2f}")
        
        return {"fundamentals_data": fundamentals}
        
    except ImportError:
        print("      SEC EDGAR library not available")
        return {"fundamentals_data": None}
    except Exception as e:
        print(f"      Error fetching fundamentals: {e}")
        return {"fundamentals_data": None}

def tech_analysis_node(state: AgentState) -> dict:
    """
    Agent 4: Technical Analysis Agent (Enhanced)
    Analyzes charts using Gemini + Multi-Timeframe Analysis (1wk, 1mo, 3mo, 6mo).
    Uses strategy_model (gemini-2.5-pro) for better analysis.
    """
    print("\n---> Agent 4: Technical Analysis (Multi-Timeframe)")
    
    chart_path = state.get('chart_path')
    ticker = state.get('ticker', 'UNKNOWN')
    ohlcv_data = state.get('ohlcv_data', {})
    
    # Define timeframes for analysis
    timeframes = {
        '1wk': '5d',    # 5 trading days
        '1mo': '1mo',
        '3mo': '3mo', 
        '6mo': '6mo'
    }
    
    # Collect multi-timeframe data
    tf_analysis = {}
    print("      Fetching multi-timeframe data...")
    
    for tf_name, period in timeframes.items():
        try:
            df = fetch_single_ticker_data(ticker, period=period)
            if df is not None and len(df) >= 2:
                # Calculate metrics
                price_change = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
                volume_avg = df['Volume'].mean()
                volume_change = (df['Volume'].iloc[-1] / volume_avg - 1) * 100 if volume_avg > 0 else 0
                volatility = df['Close'].pct_change().std() * 100
                
                # Price momentum (rate of change trend)
                mid_idx = len(df) // 2
                first_half_change = (df['Close'].iloc[mid_idx] / df['Close'].iloc[0] - 1) * 100 if mid_idx > 0 else 0
                second_half_change = (df['Close'].iloc[-1] / df['Close'].iloc[mid_idx] - 1) * 100 if mid_idx > 0 else 0
                momentum = "accelerating" if second_half_change > first_half_change else "decelerating"
                
                tf_analysis[tf_name] = {
                    "price_change": round(price_change, 2),
                    "volume_change_vs_avg": round(volume_change, 2),
                    "volatility": round(volatility, 2),
                    "momentum": momentum,
                    "start_price": round(float(df['Close'].iloc[0]), 2),
                    "end_price": round(float(df['Close'].iloc[-1]), 2),
                    "high": round(float(df['High'].max()), 2),
                    "low": round(float(df['Low'].min()), 2)
                }
                print(f"        {tf_name}: {price_change:+.2f}% (momentum: {momentum})")
        except Exception as e:
            print(f"        {tf_name}: Error - {e}")
            tf_analysis[tf_name] = {"error": str(e)}
    
    # Build comprehensive prompt
    tf_summary = "\n".join([
        f"- {tf}: Price {data.get('price_change', 'N/A'):+.1f}%, "
        f"Volume vs Avg: {data.get('volume_change_vs_avg', 'N/A'):+.1f}%, "
        f"Volatility: {data.get('volatility', 'N/A'):.1f}%, "
        f"Momentum: {data.get('momentum', 'N/A')}"
        for tf, data in tf_analysis.items() if 'error' not in data
    ])
    
    vision_prompt = f"""You are a senior technical analyst. Perform comprehensive multi-timeframe analysis for {ticker}.

## CURRENT DATA
- Current Price: ${ohlcv_data.get('current_price', 'N/A')}
- Period Change: {ohlcv_data.get('period_change_pct', 'N/A')}%

## MULTI-TIMEFRAME ANALYSIS
{tf_summary}

## ANALYSIS REQUIRED
Based on the chart and timeframe data:

1. **Timeframe Momentum Comparison**:
   - Compare momentum across 1wk vs 1mo vs 3mo vs 6mo
   - Is short-term momentum aligned with long-term trend?
   - Any divergence signals?

2. **Trend Strength by Timeframe**:
   - 1 Week: Short-term direction and strength
   - 1 Month: Medium-term trend
   - 3 Months: Intermediate trend
   - 6 Months: Long-term trend

3. **Volume Analysis**:
   - Is volume confirming price movement in each timeframe?
   - Volume momentum trend

4. **Key Price Levels**:
   - Major support and resistance across timeframes
   - Price position relative to these levels

5. **Technical Signal**: 
   - BUY / SELL / HOLD recommendation
   - Timeframe for the recommendation
   - Risk level and stop-loss suggestion

Be specific about momentum changes and trend alignment across timeframes."""

    try:
        # Use chart if available
        if chart_path and os.path.exists(chart_path):
            image_base64 = image_to_base64(chart_path)
            response = strategy_model.invoke([
                HumanMessage(content=[
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ])
            ])
        else:
            # Text-only analysis
            response = strategy_model.invoke([HumanMessage(content=vision_prompt)])
        
        analysis = response.content
        print(f"      Technical analysis completed ({len(analysis)} chars)")
        
    except Exception as e:
        print(f"      Technical analysis failed: {e}")
        analysis = f"Technical analysis error: {e}\n\nTimeframe Data:\n{tf_summary}"
    
    return {"technical_analysis": analysis}


def sentiment_agent_node(state: AgentState) -> dict:
    """
    Agent 5: Sentiment Analysis Agent (Enhanced)
    Multi-Timeframe sentiment analysis: 1wk, 1mo, 3mo, 6mo.
    Uses yfinance for recent news + Tavily for historical search.
    Uses strategy_model (gemini-2.5-pro) for analysis.
    """
    print("\n---> Agent 5: Sentiment Analysis (Multi-Timeframe)")
    
    ticker = state.get('ticker', 'UNKNOWN')
    news_data = state.get('news_data', [])
    blog_data = state.get('blog_data', [])
    
    # Organize sentiment data by timeframe
    timeframe_data = {
        '1wk': {'news': [], 'tavily': []},
        '1mo': {'news': [], 'tavily': []},
        '3mo': {'news': [], 'tavily': []},
        '6mo': {'news': [], 'tavily': []}
    }
    
    print("      Organizing news by timeframe...")
    
    # Categorize existing news and blogs (recent - within ~30 days)
    for news in news_data[:15]:
        timeframe_data['1wk']['news'].append(news)  # Recent news covers 1wk and 1mo
        timeframe_data['1mo']['news'].append(news)
    
    for blog in blog_data[:5]:
        timeframe_data['1wk']['tavily'].append(blog)
        timeframe_data['1mo']['tavily'].append(blog)
    
    print(f"        Recent: {len(news_data)} news, {len(blog_data)} blogs")
    
    # Use Tavily for historical sentiment (3mo, 6mo)
    if tavily_client:
        historical_queries = [
            ('3mo', f"{ticker} stock news analysis Q3 Q4 2024"),
            ('3mo', f"{ticker} earnings performance last quarter"),
            ('6mo', f"{ticker} stock news sentiment 2024 review"),
            ('6mo', f"{ticker} company performance analysis 6 months")
        ]
        
        print("      Fetching historical sentiment via Tavily...")
        for tf, query in historical_queries:
            try:
                response = tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=3
                )
                for result in response.get('results', []):
                    timeframe_data[tf]['tavily'].append({
                        'title': result.get('title', ''),
                        'content': result.get('content', '')[:2000],
                        'source': result.get('url', '').split('/')[2] if result.get('url') else 'Web'
                    })
            except Exception as e:
                print(f"        Tavily search failed for {tf}: {e}")
        
        print(f"        3mo: {len(timeframe_data['3mo']['tavily'])} articles")
        print(f"        6mo: {len(timeframe_data['6mo']['tavily'])} articles")
    else:
        print("      Tavily not available for historical search")
    
    # Build comprehensive prompt for multi-timeframe analysis
    def format_timeframe_content(tf_name: str, data: dict) -> str:
        items = []
        for news in data.get('news', [])[:5]:
            items.append(f"  - [News] {news.get('title', 'No title')}")
        for tavily in data.get('tavily', [])[:3]:
            items.append(f"  - [{tavily.get('source', 'Web')}] {tavily.get('title', '')[:100]}")
        return "\n".join(items) if items else "  - No data available"
    
    content_summary = ""
    for tf in ['1wk', '1mo', '3mo', '6mo']:
        content_summary += f"\n### {tf} Content:\n{format_timeframe_content(tf, timeframe_data[tf])}\n"
    
    sentiment_prompt = f"""You are a senior market sentiment analyst. Analyze the market sentiment for {ticker} across multiple timeframes.

## NEWS AND SOCIAL CONTENT BY TIMEFRAME
{content_summary}

## DETAILED CONTENT FOR ANALYSIS
### Recent News (1 Week - 1 Month):
{chr(10).join([f"- {n.get('title', '')}: {n.get('summary', '')[:300]}" for n in news_data[:8]])}

### Blog/Social Content:
{chr(10).join([f"- {b.get('title', '')}: {b.get('content', '')[:300]}" for b in blog_data[:4]])}

## ANALYSIS REQUIRED
Provide a comprehensive multi-timeframe sentiment analysis:

1. **Sentiment by Timeframe** (POSITIVE/NEGATIVE/NEUTRAL/MIXED for each):
   - 1 Week sentiment and key drivers
   - 1 Month sentiment and key drivers
   - 3 Month sentiment and key drivers  
   - 6 Month sentiment and key drivers

2. **Sentiment Momentum**:
   - Is sentiment improving or deteriorating over time?
   - Any recent sentiment shifts?
   - Sentiment trend direction (accelerating positive/negative, stabilizing, reversing)

3. **Key Themes by Timeframe**:
   - What topics dominate each period?
   - Any emerging concerns or catalysts?

4. **Overall Sentiment Score**: 
   - Combined sentiment (POSITIVE/NEGATIVE/NEUTRAL/MIXED)
   - Confidence level (0.0 to 1.0)

5. **Summary**: 2-3 sentences on the overall sentiment landscape and its trajectory.

Respond in JSON format with the following structure:
{{
    "timeframe_sentiment": {{
        "1wk": {{"sentiment": "...", "key_driver": "..."}},
        "1mo": {{"sentiment": "...", "key_driver": "..."}},
        "3mo": {{"sentiment": "...", "key_driver": "..."}},
        "6mo": {{"sentiment": "...", "key_driver": "..."}}
    }},
    "sentiment_momentum": "...",
    "momentum_direction": "...",
    "overall_sentiment": "...",
    "confidence": 0.0,
    "key_themes": [],
    "summary": "..."
}}"""

    try:
        response = strategy_model.invoke([HumanMessage(content=sentiment_prompt)])
        content = response.content
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            sentiment_result = json.loads(json_match.group())
        else:
            sentiment_result = {
                "timeframe_sentiment": {},
                "sentiment_momentum": "Unknown",
                "overall_sentiment": "NEUTRAL",
                "confidence": 0.5,
                "key_themes": [],
                "summary": content[:500]
            }
        
        print(f"      Overall Sentiment: {sentiment_result.get('overall_sentiment', 'N/A')}")
        print(f"        Momentum: {sentiment_result.get('sentiment_momentum', 'N/A')}")
        print(f"        Confidence: {sentiment_result.get('confidence', 'N/A')}")
        
    except Exception as e:
        print(f"      Sentiment analysis failed: {e}")
        sentiment_result = {
            "timeframe_sentiment": {},
            "sentiment_momentum": "Unknown",
            "overall_sentiment": "NEUTRAL",
            "confidence": 0.3,
            "key_themes": [],
            "summary": f"Sentiment analysis failed: {e}"
        }
    
    return {"sentiment_analysis": sentiment_result}


def strategy_agent_node(state: AgentState) -> dict:
    """
    Agent 7: Strategy Agent (Final Decision Maker)
    Synthesizes all inputs including fundamentals to make final trading decision.
    """
    print("\n---> Agent 7: Strategy (Final Decision)")
    print("="*60)
    
    ticker = state.get('ticker', 'UNKNOWN')
    ohlcv_data = state.get('ohlcv_data', {})
    technical_analysis = state.get('technical_analysis', '')
    sentiment_analysis = state.get('sentiment_analysis', {})
    news_data = state.get('news_data', [])
    blog_data = state.get('blog_data', [])
    fundamentals_data = state.get('fundamentals_data', {})
    
    # Format fundamentals data
    fundamentals_summary = "Not available"
    if fundamentals_data and fundamentals_data.get('metrics'):
        metrics = fundamentals_data['metrics']
        total_assets = metrics.get('total_assets')
        total_liabilities = metrics.get('total_liabilities')
        
        assets_str = f"${total_assets:,.0f}" if isinstance(total_assets, (int, float)) else str(total_assets)
        liabilities_str = f"${total_liabilities:,.0f}" if isinstance(total_liabilities, (int, float)) else str(total_liabilities)
        
        fundamentals_summary = f"""- Periods Analyzed: {fundamentals_data.get('periods_analyzed', 'N/A')} quarters
- Revenue YoY Growth: {metrics.get('revenue_yoy', 'N/A')}%
- Net Income YoY Growth: {metrics.get('net_income_yoy', 'N/A')}%
- Debt/Equity Ratio: {metrics.get('debt_to_equity', 'N/A')}
- Total Assets: {assets_str}
- Total Liabilities: {liabilities_str}"""
    
    # [수정 1] Key Themes 안전하게 변환
    # 리스트 컴프리헨션 내에서 확실하게 str()로 감싸서 딕셔너리가 join으로 넘어가는 것을 방지
    key_themes = sentiment_analysis.get('key_themes', [])
    key_themes_list = []
    if isinstance(key_themes, list):
        for t in key_themes:
            if isinstance(t, str):
                key_themes_list.append(t)
            elif isinstance(t, dict):
                # 'theme' 키가 없으면 딕셔너리 전체를 문자열로 변환
                key_themes_list.append(str(t.get('theme', str(t))))
            else:
                key_themes_list.append(str(t))
        key_themes_str = ', '.join(key_themes_list)
    else:
        key_themes_str = str(key_themes) if key_themes else 'N/A'
    
    # [수정 2] News Headlines 안전하게 변환
    # 뉴스 데이터가 딕셔너리 리스트일 때 안전하게 타이틀만 추출
    news_lines = []
    if news_data and isinstance(news_data, list):
        for n in news_data[:5]:
            if isinstance(n, dict):
                news_lines.append(f"- {n.get('title', 'No Title')}")
            else:
                news_lines.append(f"- {str(n)}")
    
    news_str = "\n".join(news_lines) if news_lines else "No news available"
    
    # Build comprehensive context
    strategy_prompt = f"""You are a senior portfolio strategist. Make a final trading decision for {ticker}.

## QUANTITATIVE DATA (Agent 3)
- Current Price: ${ohlcv_data.get('current_price', 'N/A')}
- Period Change: {ohlcv_data.get('period_change_pct', 'N/A')}%
- Price Range: ${ohlcv_data.get('period_low', 'N/A')} - ${ohlcv_data.get('period_high', 'N/A')}
- Volatility: {ohlcv_data.get('volatility', 'N/A')}%

## TECHNICAL ANALYSIS (Agent 4)
{technical_analysis[:1500] if technical_analysis else 'Not available'}

## SENTIMENT ANALYSIS (Agent 5)
- Overall Sentiment: {sentiment_analysis.get('overall_sentiment', 'N/A')}
- Sentiment Confidence: {sentiment_analysis.get('confidence', 'N/A')}
- Key Themes: {key_themes_str}
- Summary: {sentiment_analysis.get('summary', 'N/A')}

## FUNDAMENTAL ANALYSIS (Agent 6) - 8 Quarters / 2 Years
{fundamentals_summary}

## NEWS HEADLINES (Agent 1)
{news_str}

---

Based on ALL the above inputs, provide your final trading decision:

1. DECISION: BUY, SELL, or HOLD
2. CONFIDENCE: 0.0 to 1.0
3. TIMEFRAME: Short-term (1-2 weeks), Medium-term (1-3 months), or Long-term (3+ months)
4. REASONING: Detailed explanation combining technical, fundamental, and sentiment factors
5. RISK_FACTORS: Key risks that could invalidate this decision

Be specific and actionable. Consider risk-adjusted returns.

Respond in JSON format with keys: decision, confidence, timeframe, reasoning, risk_factors"""

    try:
        response = strategy_model.invoke([HumanMessage(content=strategy_prompt)])
        content = response.content if response and response.content else ""
        
        if not content:
            raise ValueError("Empty response from strategy model")
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        
        if json_match:
            decision_data = json.loads(json_match.group())
        else:
            decision_data = {
                "decision": "HOLD",
                "confidence": 0.5,
                "timeframe": "Medium-term",
                "reasoning": content[:500],
                "risk_factors": "Unable to parse detailed risk factors"
            }
        
        # Convert to TradingSignal
        decision_str = decision_data.get('decision', 'HOLD').upper()
        signal_type = SignalType.HOLD
        if decision_str == 'BUY':
            signal_type = SignalType.BUY
        elif decision_str == 'SELL':
            signal_type = SignalType.SELL
        
        # Ensure risk_factors is a string (not a list)
        risk_factors = decision_data.get('risk_factors', 'No risk factors identified')
        if isinstance(risk_factors, list):
            risk_factors = '; '.join(str(r) if not isinstance(r, dict) else str(r.get('factor', r.get('risk', str(r)))) for r in risk_factors)
        elif isinstance(risk_factors, dict):
            risk_factors = str(risk_factors)
        
        # Ensure reasoning is a string
        reasoning = decision_data.get('reasoning', 'No reasoning provided')
        if isinstance(reasoning, list):
            reasoning = ' '.join(str(r) if not isinstance(r, dict) else str(r.get('point', r.get('reason', str(r)))) for r in reasoning)
        elif isinstance(reasoning, dict):
            reasoning = str(reasoning)
        
        final_signal = TradingSignal(
            decision=signal_type,
            confidence=float(decision_data.get('confidence', 0.5)),
            timeframe=str(decision_data.get('timeframe', 'Medium-term')),
            reasoning=reasoning,
            risk_factors=risk_factors
        )
        
        # Print final decision
        print(f"\n{'='*60}")
        print(f" FINAL DECISION FOR {ticker}")
        print(f"{'='*60}")
        print(f"   Decision: {final_signal.decision.value}")
        print(f"   Confidence: {final_signal.confidence:.0%}")
        print(f"   Timeframe: {final_signal.timeframe}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"      Strategy decision failed: {e}")
        final_signal = TradingSignal(
            decision=SignalType.HOLD,
            confidence=0.3,
            timeframe="Short-term",
            reasoning=f"Decision generation failed: {e}. Defaulting to HOLD.",
            risk_factors="System error - manual review required"
        )
    
    return {"final_signal": final_signal}


# --- 4. Build the Graph ---
builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("ExtractTicker", extract_ticker_node)
builder.add_node("NewsAgent", news_agent_node)
builder.add_node("BlogAgent", blog_agent_node)
builder.add_node("DataAgent", data_agent_node)
builder.add_node("FundamentalsAgent", fundamentals_agent_node)
builder.add_node("TechAnalysis", tech_analysis_node)
builder.add_node("Sentiment", sentiment_agent_node)
builder.add_node("Strategy", strategy_agent_node)

# Define edges
# Start -> Extract Ticker
builder.add_edge(START, "ExtractTicker")

# Ticker -> Four parallel-ish agents (sequenced for simplicity)
builder.add_edge("ExtractTicker", "NewsAgent")
builder.add_edge("ExtractTicker", "BlogAgent")
builder.add_edge("ExtractTicker", "DataAgent")
builder.add_edge("ExtractTicker", "FundamentalsAgent")

# Data Agent -> Tech Analysis (needs chart)
builder.add_edge("DataAgent", "TechAnalysis")

# News + Blog -> Sentiment (needs text data)
builder.add_edge("NewsAgent", "Sentiment")
builder.add_edge("BlogAgent", "Sentiment")

# Tech Analysis + Sentiment + Fundamentals -> Strategy
builder.add_edge("TechAnalysis", "Strategy")
builder.add_edge("Sentiment", "Strategy")
builder.add_edge("FundamentalsAgent", "Strategy")

# Strategy -> End
builder.add_edge("Strategy", END)

# Compile the graph
graph = builder.compile()


# --- 5. Convenience Run Function ---
def analyze_stock(ticker: str) -> TradingSignal:
    """
    Convenience function to run the multi-agent analysis.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
    
    Returns:
        TradingSignal with the final decision
    """
    result = graph.invoke({
        "ticker": ticker.upper(),
        "messages": [HumanMessage(content=f"Analyze {ticker}")]
    })
    
    return result.get("final_signal")


if __name__ == "__main__":
    # Test run
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    signal = analyze_stock(ticker)
    
    if signal:
        print(f"\n Full Analysis Complete")
        print(f"   Decision: {signal.decision.value}")
        print(f"   Confidence: {signal.confidence:.0%}")
        print(f"   Timeframe: {signal.timeframe}")
        print(f"\n   Reasoning: {signal.reasoning[:300]}...")
        print(f"\n   Risk Factors: {signal.risk_factors[:200]}...")
