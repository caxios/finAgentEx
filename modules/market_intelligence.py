import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import os
import uuid

# Create charts directory if not exists
os.makedirs("modules/charts", exist_ok=True)

def fetch_market_data(ticker: str):
    """
    Fetches OHLC data and recent news for the ticker.
    """
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    
    # Get 1 month of history for the chart
    hist = stock.history(period="1mo")
    
    # Get news
    news = stock.news
    
    return hist, news

def generate_chart(ticker: str, data: pd.DataFrame):
    """
    Generates a candlestick chart and saves it. Returns the path.
    """
    print(f"Generating chart for {ticker}...")
    filename = f"modules/charts/{ticker}_{uuid.uuid4()}.png"
    
    # Customize style
    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc)
    
    mpf.plot(data, type='candle', style=s, title=f"{ticker} Recent Price", savefig=filename)
    return os.path.abspath(filename)

def format_news(news: list):
    """
    Formats the news list into a string summary.
    """
    summary = ""
    for item in news[:5]: # Top 5 news
        # Handle potential missing keys gracefully
        title = item.get('title', item.get('content', {}).get('title', 'No Title'))
        pub_time = item.get('providerPublishTime', 'N/A')
        summary += f"- [{pub_time}] {title}\n"
    return summary
