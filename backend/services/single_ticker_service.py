from typing import Optional, Dict, Any, List
from backend.schemas.fundamentals import FundamentalsResponse
from backend.redis_client import redis_client
from backend.services.fundamentals_utils import (
    calculate_yoy, cache_to_response_format, parse_period_sort_key
)
from backend.services.annual_processor import fetch_annual_data
from backend.services.quarterly_processor import fetch_quarterly_data

# Cache imports
try:
    from backend.cache import (
        get_fundamentals_cache, save_fundamentals_batch,
        get_fundamentals_cached_periods
    )
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False

def fetch_ticker_fundamentals(ticker: str, period_type_req: str) -> FundamentalsResponse:
    """
    Orchestrate fetching fundamentals for a single ticker.
    1. Check Redis
    2. Check SQLite
    3. Fetch via Processors
    4. Save to Cache
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = period_type_req.lower() == "annual"
        period_type = "annual" if is_annual else "quarterly"
        redis_key = f"fundamentals:{ticker}:{period_type}"
        
        # 1. Redis Cache
        cached_redis = redis_client.get(redis_key)
        if cached_redis:
            print(f"[OK] {ticker} fundamentals (from Redis cache)")
            return FundamentalsResponse(**cached_redis)

        # 2. SQLite Cache
        if CACHE_ENABLED:
            cached_periods = get_fundamentals_cached_periods(ticker, period_type)
            if cached_periods and len(cached_periods) >= 5:
                cached_data = get_fundamentals_cache(ticker, period_type)
                if cached_data['income'] or cached_data['balance']:
                    print(f"[OK] {ticker} fundamentals (from SQLite cache)")
                    
                    # Convert to response format
                    income_data = cache_to_response_format(cached_data.get('income', {}))
                    balance_data = cache_to_response_format(cached_data.get('balance', {}))
                    cashflow_data = cache_to_response_format(cached_data.get('cashflow', {}))
                    
                    response = FundamentalsResponse(
                        success=True,
                        ticker=ticker,
                        period_type=period_type_req,
                        periods=sorted(cached_periods, key=parse_period_sort_key, reverse=True),
                        income=income_data,
                        balance=balance_data,
                        cashflow=cashflow_data
                    )
                    redis_client.set(redis_key, response.model_dump(), ex=86400 * 7)
                    return response

        # 3. Fetch from Processors
        print(f"[*] {ticker} {period_type} fundamentals (fetching from Processors...)")
        
        if is_annual:
            raw_data = fetch_annual_data(ticker)
        else:
            raw_data = fetch_quarterly_data(ticker)
            
        periods = raw_data.get('periods', [])
        income_data = raw_data.get('income', [])
        balance_data = raw_data.get('balance', [])
        cashflow_data = raw_data.get('cashflow', [])
        
        if not periods:
            return FundamentalsResponse(
                success=False, ticker=ticker, period_type=period_type_req,
                periods=[], income=[], balance=[], cashflow=[],
                error=f"No data found for {ticker}"
            )
            
        # Post-process: Recalculate YoY on the full merged dataset ensures accuracy across filings
        def recalc_yoy(data_list):
            for row in data_list:
                val_map = row['values']
                # calculate_yoy returns full dict with yoy
                new_vals = calculate_yoy(val_map, periods)
                row['values'] = new_vals
            return data_list

        income_data = recalc_yoy(income_data)
        balance_data = recalc_yoy(balance_data)
        cashflow_data = recalc_yoy(cashflow_data)

        # 4. Save to SQLite Cache
        if CACHE_ENABLED and periods:
            save_fundamentals_batch(
                ticker, period_type,
                income_data, balance_data, cashflow_data,
                periods
            )
            print(f"[OK] {ticker} fundamentals (cached {len(periods)} periods)")

        response = FundamentalsResponse(
            success=True,
            ticker=ticker,
            period_type=period_type_req,
            periods=periods,
            income=income_data,
            balance=balance_data,
            cashflow=cashflow_data
        )
        
        # Save to Redis
        redis_client.set(redis_key, response.model_dump(), ex=86400 * 7)
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return FundamentalsResponse(
            success=False, ticker=ticker, period_type=period_type_req,
            periods=[], income=[], balance=[], cashflow=[], error=str(e)
        )
