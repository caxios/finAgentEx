from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

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

@tool('get_balance_sheet', description='A function that returns the balance sheet based on a ticker symbol.')
def get_balance_sheet(ticker: str):
    print('    [Price Agent] Fetching balance sheet...')
    stock = yf.Ticker(ticker)
    return stock.balance_sheet

@tool('get_stock_news', description='A function that returns news based on a ticker symbol.')
def get_stock_news(ticker: str):
    print('    [News Agent] Fetching news...')
    stock = yf.Ticker(ticker)
    return stock.news

# Define the shared model
model = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0
)

# --- Price Agent ---
# Responsible for quantitative data
price_agent = create_react_agent(
    model=model,
    tools=[get_stock_price, get_historical_stock_price, get_balance_sheet],
)

# --- News Agent ---
# Responsible for qualitative data
news_agent = create_react_agent(
    model=model,
    tools=[get_stock_news],
)
