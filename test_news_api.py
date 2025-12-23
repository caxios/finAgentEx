import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RAPID_API_KEY")
host = "seeking-alpha-api.p.rapidapi.com"

def test_endpoint(path, params):
    url = f"https://{host}{path}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": host
    }
    print(f"Testing {url} with params {params}...")
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Success! Keys in response:", data.keys() if isinstance(data, dict) else "List")
            if isinstance(data, dict) and 'search_result' in data:
                 results = data['search_result']
                 print("Results keys:", results.keys())
                 # Print first item of 'articles' or 'news' if present
                 if 'articles' in results:
                     print("First article:", results['articles'][0])
                 elif 'news' in results:
                     print("First news:", results['news'][0])
                 elif 'list' in results:
                     print("First list item:", results['list'][0])
                 elif 'pages' in results:
                     print("First page item:", results['pages'][0])
                     # Check if it has title/date
                     print("Page detail:", str(results['pages'][0])[:500])
            return True
        else:
            print("Error response:", response.text)
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

# Try 2: Alternative endpoints
# print("--- TEST 4: /news/list?id=AAPL ---")
# test_endpoint("/news/list", {"id": "AAPL"})

# Try by symbol
# print("\n--- TEST 5: /news/list?symbol=AAPL ---")
# test_endpoint("/news/list", {"symbol": "AAPL"})

# print("\n--- TEST 6: /search?query=AAPL&type=articles ---")
# test_endpoint("/search", {"query": "AAPL", "type": "articles"})

print("\n--- TEST 8: /getnews/v2/list-by-symbol?symbol=AAPL ---")
test_endpoint("/getnews/v2/list-by-symbol", {"symbol": "AAPL"})

# print("\n--- TEST 7: /market/get-news?id=aapl ---")
# # Sometimes it's /market/get-news
# test_endpoint("/market/get-news", {"id": "aapl"})
