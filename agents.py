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
# Legacy placeholder. Actual news intelligence is now handled by workflow.py via modules.market_intelligence (Google Grounding)
# We keep this lightweight agent here in case the graph architecture needs it, but it has no tools.
# It can only answer basica questions from its internal knowledge.
news_agent = create_react_agent(
    model=model,
    tools=[], # No custom tools needed, Grounding is handled upstream or by the model natively if configured
)
