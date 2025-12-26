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

@tool('get_stock_news', description='A function that returns news based on a ticker symbol.')
def get_stock_news(ticker: str):
    print('    [News Agent] Fetching news...')
    stock = yf.Ticker(ticker)
    return stock.news

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

from ddgs import DDGS

import requests # Fallback/Type hinting
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

@tool('scrape_website', description='Scrapes the content of a specific URL. Use this to get the full text of a news article or press release found by the search tool.')
def scrape_website(url: str):
    print(f"    [News Agent] Scraping URL: {url}")
    try:
        # Use curl_cffi to impersonate a real browser (Chrome) to bypass 403 blocks
        session = cffi_requests.Session(impersonate="chrome")
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements (scripts, styles, navs, footers, etc.)
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()
            
        # Strategy 1: Look for semantic <article> tag
        article = soup.find('article')
        if article:
            text = article.get_text(separator=' ', strip=True)
        else:
            # Strategy 2: Aggregate text from paragraphs, avoiding menu links/short garbage needed
            paragraphs = soup.find_all('p')
            # Filter out short snippets (often nav links or metadata)
            clean_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
            text = '\n\n'.join(clean_paragraphs)

        # Fallback
        if not text or len(text) < 100:
            text = soup.get_text(separator=' ', strip=True)
        
        # Truncate raw text to avoid overflowing context window before summarization
        # 15,000 chars is plenty for a PR but safe for Gemini 1.5 Flash/Pro context
        raw_text = text[:15000]

        print(f"    [News Agent] Summarizing {len(raw_text)} chars of text...")
        
        # --- LLM Summarization Step ---
        summary_prompt = f"""You are a financial analyst helper. Read the following article content and generate a HIGH-DENSITY, bulleted summary of key facts.
        Focus on:
        - Earnings figures (Revenue, EPS, Guidance)
        - Strategic announcements (Mergers, partnerships, products)
        - Identifying specific risks or opportunities.
        
        Ignore generic legal disclaimers or navigation text.
        
        Article Content:
        {raw_text}
        """
        
        try:
            summary = model.invoke(summary_prompt).content
            return f"Scraped and Summarized Content for {url}:\n{summary}"
        except Exception as llm_e:
            print(f"    [News Agent] Warning: LLM Summarization failed ({llm_e}). Using fallback.")
            # Fallback: Top 300 words / 2000 chars
            fallback_text = raw_text[:2000]
            return f"Scraped Content for {url} (Summary Failed - Raw Excerpt):\n{fallback_text}..."
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

# --- News Agent ---
# Responsible for qualitative data
news_prompt = """You are a News Agent. Your goal is to extract qualitative signals from news and official corporate announcements that might correlate with market movements.

You have access to:
1.  **DuckDuckGo Search**: To find headlines and URLs.
2.  **Web Scraper**: To read the full content of an important article (`scrape_website`).

**Workflow**:
1.  **Search**: Perform TWO searches:
    *   General News: `"{ticker} stock news financial analysis"`
    *   Press Releases: `"{ticker} press releases site:businesswire.com OR site:prnewswire.com OR site:globenewswire.com"`
2.  **Scrape**: If you find a high-impact headline (e.g., earnings release, bad news, major product launch), use `scrape_website` on its URL to get the full details. Don't scrape everything, only the most critical 5-10 items.
3.  **Synthesize**: Combine insights from search snippets and scraped content.

Look for:
- Earnings surprises (get exact numbers via scraping)
- Regulatory shifts
- Mergers and Acquisitions
- New product launches
- Sentiment shifts

Return a single synthesized summary.
"""

@tool('duckduckgo_search_tool', description='A search engine. Useful for when you need to answer questions about current events. Input should be a search query.')
def duckduckgo_search_tool(query: str):
    print(f"    [News Agent] Searching DDG for: {query}")
    # Fetch 25 results to enable time-based filtering
    raw_results = DDGS().news(query, region='us-en', max_results=25)
    
    # Filter matches older than 6 months to ensure freshness
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=180) 
    
    filtered_results = []
    if raw_results:
        for res in raw_results:
            date_str = res.get('date', '')
            if date_str:
                try:
                    res_date = datetime.fromisoformat(date_str)
                    if res_date >= cutoff_date:
                        filtered_results.append(res)
                except ValueError:
                    continue
    
    # Sort by date descending (newest first)
    sorted_results = sorted(filtered_results, key=lambda x: x.get('date', ''), reverse=True)
    
    # Return top 10 most recent
    return sorted_results[:10]

news_agent = create_react_agent(
    model=model,
    tools=[duckduckgo_search_tool, scrape_website],
)
