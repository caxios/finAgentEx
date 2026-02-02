import yfinance as yf

ticker = "AAPL"
print(f"Testing market cap fetch for {ticker}...")

try:
    print("\n--- Method 1: fast_info ---")
    t = yf.Ticker(ticker)
    # fast_info is an object that can be accessed like a dict or attributes in some versions
    # Let's try both
    try:
        val = t.fast_info['market_cap']
        print(f"t.fast_info['market_cap']: {val}")
    except Exception as e:
        print(f"t.fast_info['market_cap'] failed: {e}")

    try:
        val = t.fast_info.market_cap
        print(f"t.fast_info.market_cap: {val}")
    except Exception as e:
        print(f"t.fast_info.market_cap failed: {e}")

except Exception as e:
    print(f"Method 1 setup failed: {e}")

try:
    print("\n--- Method 2: info ---")
    t = yf.Ticker(ticker)
    info = t.info
    # print keys to verify
    # print(info.keys()) 
    val = info.get('marketCap')
    print(f"t.info.get('marketCap'): {val}")
    val2 = info.get('market_cap')
    print(f"t.info.get('market_cap'): {val2}")

except Exception as e:
    print(f"Method 2 failed: {e}")
