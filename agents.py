from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

from modules.market_intelligence import fetch_market_data, analyze_price_patterns

# Define tools
@tool('get_stock_price', description='A function that returns the current stock price based on a ticker symbol.')
def get_stock_price(ticker: str):
    print('    [Price Agent] Fetching stock price...')
    stock = yf.Ticker(ticker)
    return stock.history()['Close'].iloc[-1]

@tool('get_historical_stock_price', description='A function that returns the current stock price over time based on a ticker symbol and a start and end date.')
def get_historical_stock_price(ticker: str, start_date: str, end_date: str):
    print('    [Price Agent] Fetching history...')
    stock = yf.Ticker(ticker)
    return stock.history(start=start_date, end=end_date).to_dict()

@tool('get_price_analysis', description='A function that performs advanced quantitative analysis on a stock ticker to detect patterns like trends, volatility, and specific price movements.')
def get_price_analysis(ticker: str):
    print('    [Price Agent] Analyzing price patterns...')
    # Fetch 1 year of data for deep analysis
    hist, _ = fetch_market_data(ticker, period="1y") 
    analysis = analyze_price_patterns(hist)
    return analysis

@tool('get_balance_sheet', description='A function that returns the balance sheet based on a ticker symbol.')
def get_balance_sheet(ticker: str):
    print('    [Price Agent] Fetching balance sheet...')
    stock = yf.Ticker(ticker)
    return stock.balance_sheet

# Define the shared model
model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0
)

# --- Price Agent ---
# Responsible for quantitative data and pattern recognition
price_agent = create_react_agent(
    model=model,
    tools=[get_stock_price, get_historical_stock_price, get_balance_sheet, get_price_analysis],
)

# --- News Agent ---
# Responsible for qualitative data using Google Search Grounding
news_prompt = """You are a News Agent. Your goal is to extract qualitative signals from news and official corporate announcements that might correlate with market movements.

You have access to **Google Search**. Use it to find:
1.  **Recent News**: "stock news financial analysis" for the ticker.
2.  **Press Releases**: Official announcements from the company.

**Workflow**:
1.  **Search**: Use your search tool to find high-impact headlines (Earnings, Mergers, Regulatory shifts, New Products).
2.  **Synthesize**: Combine insights from the search results.

Look for:
- Earnings surprises
- Regulatory shifts
- Mergers and Acquisitions
- New product launches
- Sentiment shifts

Return a single synthesized summary.
"""

# Native Google Search Grounding Tool definition
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

# Example usage for your news_agent:
search = GoogleSearchAPIWrapper(
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    google_cse_id=os.getenv('GOOGLE_CSE_ID')
)
google_search_tool = Tool(
    name="google_search",
    description="Search Google for recent news.",
    func=search.run,
)
# Configure a specific model instance for the News Agent that has Grounding enabled
# Note: This requires the 'google_search_retrieval' capability
# grounded_model = ChatGoogleGenerativeAI(
#     model=os.getenv('MODEL'),
#     temperature=0,
#     google_search_retrieval=True # Enable native grounding
# )

news_agent = create_react_agent(
    model=model,
    tools=[google_search_tool], # Tools are handled natively by the model's grounding capability
)
