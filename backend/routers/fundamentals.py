"""
Fundamentals Router - Historical financial statements using edgartools
Returns 10 years of annual/quarterly data with YoY calculations
Now with SQLite persistent caching and incremental updates.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import re
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from backend.redis_client import redis_client

# EDGAR environment variables are set in main.py before this import
from edgar import Company, set_identity
from edgar.xbrl import XBRLS

# Import SQLite cache functions
import sys
import os

CACHE_ENABLED = False

# Strategy 1: Direct import
try:
    from backend.cache import (
        get_fundamentals_cache, save_fundamentals_batch,
        get_fundamentals_cached_periods
    )
    CACHE_ENABLED = True
except ImportError:
    pass

# Strategy 2: Relative from routers directory
if not CACHE_ENABLED:
    try:
        # Go up from routers -> backend, then import cache
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from cache import (
            get_fundamentals_cache, save_fundamentals_batch,
            get_fundamentals_cached_periods
        )
        CACHE_ENABLED = True
    except ImportError:
        pass

# Strategy 3: From project root
if not CACHE_ENABLED:
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from backend.cache import (
            get_fundamentals_cache, save_fundamentals_batch,
            get_fundamentals_cached_periods
        )
        CACHE_ENABLED = True
    except ImportError as e:
        print(f"[Warning] SQLite cache not available for fundamentals: {e}")

router = APIRouter(prefix="/api", tags=["fundamentals"])

# Set SEC EDGAR identity (required)
set_identity("FinAgentEx finagentex@example.com")



class FundamentalsResponse(BaseModel):
    success: bool
    ticker: str
    period_type: str  # "annual" or "quarterly"
    periods: List[str]  # Column headers (years/quarters)
    income: List[Dict[str, Any]]
    balance: List[Dict[str, Any]]
    cashflow: List[Dict[str, Any]]
    error: Optional[str] = None

class BatchFundamentalsRequest(BaseModel):
    tickers: List[str]
    period_type: str = "annual"  # "annual" or "quarterly"



def date_to_label(date_str: str, is_annual: bool = False) -> str:
    """Convert date string (2025-09-30) to display label."""
    try:
        if isinstance(date_str, str):
            # Handle different date formats
            if re.match(r'^\d{4}$', date_str):
                return date_str  # Already just a year
            date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = date_str
        
        if is_annual:
            return str(date.year)
        
        # For quarterly, return 2025Q3 format
        month = date.month
        if month <= 3:
            quarter = "Q1"
        elif month <= 6:
            quarter = "Q2"
        elif month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"
        
        return f"{date.year}{quarter}"
    except:
        return str(date_str)


def calculate_yoy(values: Dict[str, Any], periods: List[str]) -> Dict[str, Dict[str, Any]]:
    """Calculate YoY % change for each period."""
    result = {}
    sorted_periods = sorted(periods, reverse=True)  # Most recent first
    
    # helper to parse period string
    def parse_period(p_str):
        # returns (year, quarter) or (year, None)
        # format: "2024" or "2024Q3"
        m_q = re.match(r'^(\d{4})Q(\d)$', p_str)
        if m_q:
            return int(m_q.group(1)), int(m_q.group(2))
        
        m_y = re.match(r'^(\d{4})$', p_str)
        if m_y:
            return int(m_y.group(1)), None
        return None, None

    for period in sorted_periods:
        current_data = values.get(period, {})
        val = current_data.get("value") if isinstance(current_data, dict) else current_data
        
        yoy = None
        
        if val is not None:
            year, quarter = parse_period(period)
            if year:
                prev_period_str = ""
                if quarter:
                    prev_period_str = f"{year-1}Q{quarter}"
                else:
                    prev_period_str = str(year-1)
                
                prev_data = values.get(prev_period_str, {})
                prev_val = prev_data.get("value") if isinstance(prev_data, dict) else prev_data
                
                if prev_val is not None and prev_val != 0:
                     yoy = round((val - prev_val) / abs(prev_val) * 100, 2)

        result[period] = {
            "value": val,
            "yoy": yoy
        }
    
    return result


def process_statement_df(df: pd.DataFrame, is_annual: bool = True) -> tuple:
    """
    Process DataFrame to structured list with YoY calculations.
    Returns (rows, periods)
    """
    if df is None or df.empty:
        return [], []
    
    rows = []
    # Get period columns (exclude metadata columns)
    metadata_cols = ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence']
    period_cols = [col for col in df.columns if col not in metadata_cols]
    
    # Convert date columns to readable labels
    period_mapping = {}
    for col in period_cols:
        new_label = date_to_label(str(col), is_annual)
        period_mapping[col] = new_label
    
    # Get unique period labels in order
    period_labels = []
    seen = set()
    for col in period_cols:
        label = period_mapping[col]
        if label not in seen:
            seen.add(label)
            period_labels.append(label)
    
    for _, row in df.iterrows():
        label = row.get('label', row.get('concept', 'Unknown'))
        
        # Extract values for each period with new labels
        values = {}
        for col in period_cols:
            val = row.get(col)
            if pd.notna(val):
                try:
                    new_key = period_mapping[col]
                    values[new_key] = {"value": float(val)}
                except (ValueError, TypeError):
                    pass
        
        if values:  # Only include rows with data
            yoy_data = calculate_yoy(values, list(values.keys()))
            rows.append({
                "label": str(label),
                "values": yoy_data
            })
    
    return rows, period_labels


def merge_fundamentals_data(all_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge multiple lists of rows (from different filings) into one.
    format: [{label: 'Revenue', values: { '2025Q3': {value: 100},... }}]
    """
    merged_map = {}  # label -> { 'label': ..., 'values': { period: {value: ...} } }
    
    for chunk in all_data:
        for row in chunk:
            label = row['label']
            if label not in merged_map:
                merged_map[label] = {'label': label, 'values': {}}
            
            # Merge values
            # If overlap, new data might overwrite old, or we can simply update
            # Since we iterate filings (recommend newest first), we can just update
            merged_map[label]['values'].update(row['values'])
            
    # Convert back to list
    return list(merged_map.values())

def _fetch_fundamental_data_internal(ticker: str, type: str) -> FundamentalsResponse:
    """
    Internal synchronous function to fetch fundamentals.
    Checks Redis -> SQLite -> Edgar.
    Designed to be run in a thread pool.
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = type.lower() == "annual"
        period_type = "annual" if is_annual else "quarterly"
        redis_key = f"fundamentals:{ticker}:{period_type}"
        
        # 1. Check Redis Cache
        cached_redis = redis_client.get(redis_key)
        if cached_redis:
            print(f"[OK] {ticker} fundamentals (from Redis cache)")
            return FundamentalsResponse(**cached_redis)

        # 2. Check SQLite Cache
        if CACHE_ENABLED:
            cached_periods = get_fundamentals_cached_periods(ticker, period_type)
            
            if cached_periods and len(cached_periods) >= 5:  # At least 5 periods cached
                # Get cached data
                cached_data = get_fundamentals_cache(ticker, period_type)
                
                # Reconstruct response from cache
                if cached_data['income'] or cached_data['balance'] or cached_data['cashflow']:
                    print(f"[OK] {ticker} fundamentals (from SQLite cache, {len(cached_periods)} periods)")
                    
                    # Convert cached format back to response format
                    income_data = _cache_to_response_format(cached_data.get('income', {}))
                    balance_data = _cache_to_response_format(cached_data.get('balance', {}))
                    cashflow_data = _cache_to_response_format(cached_data.get('cashflow', {}))
                    
                    response = FundamentalsResponse(
                        success=True,
                        ticker=ticker,
                        period_type=type,
                        periods=sorted(cached_periods, reverse=True),
                        income=income_data,
                        balance=balance_data,
                        cashflow=cashflow_data
                    )
                    
                    # Save to Redis for future fast access
                    redis_client.set(redis_key, response.model_dump(), ex=86400 * 7) # 7 days
                    return response
        
        # 3. Cache miss or insufficient data: fetch from SEC EDGAR
        print(f"[*] {ticker} fundamentals (fetching from SEC EDGAR...)")
        
        # Get company
        company = Company(ticker)
        
        # Fetch filings
        # For Quarterly: We need to stitch manually to ensure "Quarterly Comparison" view is used
        # For Annual: "Annual Comparison" on 10-K is usually fine
        
        form_type = "10-K" if is_annual else ["10-K", "10-Q"] 
        # Note: We include 10-K for quarterly too because Q4 implies 10-K, 
        # though standard 10-K might not give Q4 easily. 
        # But let's try to get as much as possible.
        
        num_filings = 10 if is_annual else 20 
        
        filings = company.get_filings(form=form_type, amendments=False).head(num_filings)
        
        if not filings or len(filings) == 0:
            return FundamentalsResponse(
                success=False,
                ticker=ticker,
                period_type=type,
                periods=[],
                income=[],
                balance=[],
                cashflow=[],
                error=f"No filings found for {ticker}"
            )

        # Manual Stitching Strategy
        chunk_income = []
        chunk_balance = []
        chunk_cashflow = []
        
        all_periods = set()
        p_view = "Annual Comparison" if is_annual else "Quarterly Comparison"
        
        # Iterate filings (most recent first usually)
        for filing in filings:
            try:
                # Get financials (this parses XBRL)
                # obj() automiatically returns TenQ/TenK/EightK object
                f_obj = filing.obj()
                financials = getattr(f_obj, 'financials', None)
                
                if not financials:
                    continue
                
                # Helper to process a statement type
                def extract_and_process(method_name):
                    stmt = getattr(financials, method_name)(period_view=p_view)
                    if stmt:
                        df = stmt.to_dataframe()
                        # Note: we pass is_annual to date_to_label
                        # For quarterly data, process_statement_df expects dataframe columns
                        return process_statement_df(df, is_annual)
                    return [], []

                # Income
                i_rows, i_periods = extract_and_process('income_statement')
                chunk_income.append(i_rows)
                all_periods.update(i_periods)
                
                # Balance
                b_rows, b_periods = extract_and_process('balance_sheet')
                chunk_balance.append(b_rows)
                all_periods.update(b_periods)
                
                # Cashflow
                c_rows, c_periods = extract_and_process('cashflow_statement')
                chunk_cashflow.append(c_rows)
                all_periods.update(c_periods)
                
            except Exception as e:
                print(f"Error processing filing {filing.accession_number}: {e}")
                continue
        
        # Merge chunks
        income_data = merge_fundamentals_data(chunk_income)
        balance_data = merge_fundamentals_data(chunk_balance)
        cashflow_data = merge_fundamentals_data(chunk_cashflow)
        
        # Final set of periods
        periods = sorted(list(all_periods), reverse=True)
        
        # Re-calculate YoY on merged data (since previous year might be in a different filing)
        def recalc_yoy(data_list):
            for row in data_list:
                # row['values'] is currently { period: {value: v, yoy: None} } (from process_statement_df)
                # We need to re-run calculate_yoy logic on the full set of values
                
                # extract raw value map: period -> value/dict
                val_map = row['values']
                # calculate_yoy expects {period: {value: ...}} or {period: value}
                # it returns full dict with yoy
                new_vals = calculate_yoy(val_map, periods)
                row['values'] = new_vals
            return data_list

        income_data = recalc_yoy(income_data)
        balance_data = recalc_yoy(balance_data)
        cashflow_data = recalc_yoy(cashflow_data)
        
        # 4. Save to SQLite cache
        if CACHE_ENABLED and periods:
            save_fundamentals_batch(
                ticker, period_type,
                income_data, balance_data, cashflow_data,
                periods
            )
            print(f"[OK] {ticker} fundamentals ({len(periods)} periods fetched and cached)")
        
        response = FundamentalsResponse(
            success=True,
            ticker=ticker,
            period_type=type,
            periods=periods,
            income=income_data,
            balance=balance_data,
            cashflow=cashflow_data
        )
        
        # 5. Save to Redis
        redis_client.set(redis_key, response.model_dump(), ex=86400 * 7) # 7 days
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return FundamentalsResponse(
            success=False,
            ticker=ticker,
            period_type=type,
            periods=[],
            income=[],
            balance=[],
            cashflow=[],
            error=str(e)
        )


@router.get("/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(
    ticker: str = Query(..., description="Stock ticker symbol"),
    type: str = Query("annual", description="annual or quarterly")
):
    """
    Fetch historical financial statements from SEC EDGAR.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, _fetch_fundamental_data_internal, ticker, type
        )
    return result


@router.post("/fundamentals/batch", response_model=Dict[str, FundamentalsResponse])
async def fetch_fundamentals_batch(request: BatchFundamentalsRequest):
    """
    Fetch fundamentals for multiple tickers in parallel.
    Optimized with Redis caching and thread pooling.
    """
    loop = asyncio.get_event_loop()
    results = {}
    
    # Use a ThreadPoolExecutor to run sync edgar functions in parallel
    # Limit max_workers to avoid hitting rate limits or memory issues
    max_workers = min(10, len(request.tickers))
    
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = []
        for ticker in request.tickers:
            tasks.append(
                loop.run_in_executor(
                    pool, 
                    _fetch_fundamental_data_internal, 
                    ticker, 
                    request.period_type
                )
            )
        
        completed_responses = await asyncio.gather(*tasks)
        
        for response in completed_responses:
            results[response.ticker] = response
            
    return results


