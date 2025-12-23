import requests # Fallback/Type hinting
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from ddgs import DDGS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize the model for testing
model = ChatGoogleGenerativeAI(
    model='gemini-pro-latest',
    temperature=0
)

def scrape_website(url: str):
    print(f"    [Test] Scraping URL: {url}")
    try:
        # Use curl_cffi to impersonate a real browser (Chrome)
        session = cffi_requests.Session(impersonate="chrome")
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()
            
        # Strategy 1: Look for semantic <article> tag
        article = soup.find('article')
        if article:
            text = article.get_text(separator=' ', strip=True)
        else:
            # Strategy 2: Aggregate text from paragraphs
            paragraphs = soup.find_all('p')
            clean_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
            text = '\n\n'.join(clean_paragraphs)
            
        # Fallback
        if not text or len(text) < 100:
            text = soup.get_text(separator=' ', strip=True)
            
        # Truncate raw text to avoid overflowing context window
        raw_text = text[:15000]
        
        print(f"    [Test] Summarizing {len(raw_text)} chars of text with LLM...", flush=True)
        
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
        
        print(f"    [Test] Invoking Gemini model...", flush=True)
        try:
            summary = model.invoke(summary_prompt).content
            print(f"    [Test] Model returned summary ({len(summary)} chars).", flush=True)
            return f"Scraped and Summarized Content for {url}:\n{summary}"
        except Exception as llm_error:
             print(f"    [Test] LLM Error: {llm_error}", flush=True)
             print(f"    [Test] FALLBACK: Returning first 2000 chars.", flush=True)
             fallback_text = raw_text[:2000]
             return f"Scraped Content for {url} (Summary Failed - Raw Excerpt):\n{fallback_text}..."
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

def test_duckduckgo_search(query: str, max_results: int = 5, timelimit: str = None):
    print(f"\n{'='*60}")
    print(f"Testing DuckDuckGo Search for: '{query}'")
    # Fetch more results to allow for sorting/filtering
    fetch_count = 20
    print(f"Fetching {fetch_count} items to sort by date...")
    print(f"{'='*60}")
    
    final_results = []
    try:
        # Fetch raw results without strict time limit (unless specified)
        raw_results = DDGS().news(query, region='us-en', max_results=fetch_count, timelimit=timelimit)
        
        if raw_results:
            # Filter matches older than 6 months
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=180) 
            
            filtered_results = []
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
            
            # Take top N requested
            final_results = sorted_results[:max_results]
            
            # Limit scraping to 1 item for testing speed
            final_results = final_results[:1]
            
            print(f"\n[INFO] Scraping full content for top {len(final_results)} results...")
            for res in final_results:
                url = res.get('url')
                if url:
                    full_text = scrape_website(url)
                    # Update body with full text
                    res['body'] = full_text
                    
            # Save Enriched results to file
            with open('ddg_raw_results.json', 'w', encoding='utf-8') as f:
                import json
                json.dump(final_results, f, indent=2, default=str)
            print(f"[INFO] Saved ENRICHED results (with full body) to 'ddg_raw_results.json'")
            
            print(f"\nSUCCESS: Found {len(raw_results)} raw items. Filtered to {len(filtered_results)} recent items. Showing top {len(final_results)}.")
            
            for i, res in enumerate(final_results, 1):
                print(f"\nResult {i}:")
                date = res.get('date', 'No Date')
                print(f"  Date:  {date}")
                title = res.get('title', '')
                print(f"  Title: {title.encode('ascii', 'ignore').decode('ascii')}")
                link = res.get('url', '')
                print(f"  Link:  {link.encode('ascii', 'ignore').decode('ascii')}")
                # Body is now huge, so maybe don't print it all to console
                body_snippet = res.get('body', '')[:200].replace('\n', ' ')
                print(f"  Body (Snippet): {body_snippet.encode('ascii', 'ignore').decode('ascii')}...")
        else:
            print("\nWARNING: No results returned (list is empty).")
            
    except Exception as e:
        print(f"\nERROR: Search failed with exception: {e}")
        
    return final_results

if __name__ == "__main__":
    ticker = "AAPL"
    
    # 2. Test Press Releases
    pr_query = f"{ticker} press releases site:businesswire.com OR site:prnewswire.com OR site:globenewswire.com"
    results = test_duckduckgo_search(pr_query, max_results=5)
    
    if results:
        target_url = results[0].get('url')
        if target_url:
            print(f"\n{'='*60}")
            print(f"TESTING SCRAPER on: {target_url}")
            print(f"{'='*60}")
            content = scrape_website(target_url)
            print("\n[Scraped Content Snippet]:")
            print(content.encode('ascii', 'ignore').decode('ascii'))

