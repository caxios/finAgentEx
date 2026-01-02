from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

from modules.market_intelligence import fetch_market_data, analyze_price_patterns

# --- Define the shared model ---
model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

# =============================================
# PRICE AGENT TOOLS
# =============================================

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

# --- Price Agent ---
# Responsible for quantitative data and pattern recognition
price_agent = create_react_agent(
    model=model,
    tools=[get_stock_price, get_historical_stock_price, get_balance_sheet, get_price_analysis],
)

# =============================================
# NEWS AGENT WITH GOOGLE SEARCH CAPABILITY
# =============================================

# Initialize Google Search API Wrapper
search = GoogleSearchAPIWrapper(
    google_api_key=os.getenv('GOOGLE_SEARCH_API_KEY'),
    google_cse_id=os.getenv('GOOGLE_CSE_ID')
)

# Create the Google Search Tool that the news agent will use
google_search_tool = Tool(
    name="google_search",
    description="Search Google for recent financial news, stock analysis, earnings reports, and market updates. Use this tool to find the latest news about a stock or company.",
    func=search.run,
)

# System prompt for the News Agent
news_agent_prompt = """You are a News Agent specialized in financial market intelligence. 
Your goal is to gather and analyze the latest news and information about stocks and companies.

**Your Capabilities:**
You have access to Google Search to find:
1. Recent financial news and headlines
2. Earnings reports and quarterly results
3. Press releases and official announcements
4. Analyst ratings and price targets
5. Market sentiment and investor opinions

**Your Workflow:**
1. Use the google_search tool to search for relevant news about the requested stock/company
2. Focus on high-impact news: Earnings, Mergers, Regulatory shifts, New Products
3. Look for sentiment signals (positive, negative, neutral)
4. Synthesize the findings into actionable market intelligence

**What to Look For:**
- Earnings surprises (beats or misses)
- Regulatory changes affecting the company
- Mergers and acquisitions announcements
- New product launches or service updates
- Management changes
- Competitor actions
- Macroeconomic factors affecting the sector

**Output:**
Provide a comprehensive but concise summary of the news landscape and its potential impact on the stock price.
"""

# --- News Agent ---
# Responsible for qualitative data using Google Search
# This is a ReAct agent that can autonomously search for news
news_agent = create_react_agent(
    model=model,
    tools=[google_search_tool],
)

# Export the prompt for use in graph.py
news_prompt = news_agent_prompt
