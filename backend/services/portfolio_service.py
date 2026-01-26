from typing import List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from backend.schemas.fundamentals import FundamentalsResponse
from backend.services.single_ticker_service import fetch_ticker_fundamentals
from backend.services.standard_mapper import standardize_rows

async def fetch_portfolio_fundamentals(tickers: List[str], period_type: str = "annual") -> Dict[str, FundamentalsResponse]:
    """
    Fetch fundamentals for multiple tickers in parallel.
    Delegates to single_ticker_service.
    Applies LABEL STANDARDIZATION for portfolio consistency.
    """
    loop = asyncio.get_event_loop()
    results = {}
    
    # Limit max_workers to avoid hitting rate limits or memory issues
    max_workers = min(10, len(tickers))
    
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = []
        for ticker in tickers:
            tasks.append(
                loop.run_in_executor(
                    pool, 
                    fetch_ticker_fundamentals, 
                    ticker, 
                    period_type
                )
            )
        
        completed_responses = await asyncio.gather(*tasks)
        
        for response in completed_responses:
            # Apply Standardization Logic Here
            # We modify the response object (it's a Pydantic model, so we can use .copy() or direct modification if mutable)
            # Efficient way: Create new dicts with standardized labels
            
            if response.success:
                response.income = standardize_rows(response.income)
                response.balance = standardize_rows(response.balance)
                response.cashflow = standardize_rows(response.cashflow)
                
            results[response.ticker] = response
            
    return results
