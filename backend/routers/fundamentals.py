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
    
    for i, period in enumerate(sorted_periods):
        data = values.get(period, {})
        if isinstance(data, dict):
            value = data.get("value")
        else:
            value = data
        
        yoy = None
        
        # Calculate YoY if we have previous year's same period
        # For quarterly: compare 2025Q3 with 2024Q3
        # For annual: compare 2025 with 2024
        if i + 4 < len(sorted_periods):  # 4 quarters ago for quarterly
            prev_period = sorted_periods[i + 4]
            prev_data = values.get(prev_period, {})
            prev_value = prev_data.get("value") if isinstance(prev_data, dict) else prev_data
            if value is not None and prev_value is not None and prev_value != 0:
                yoy = round((value - prev_value) / abs(prev_value) * 100, 2)
        elif i + 1 < len(sorted_periods):  # Fallback: compare with previous period
            prev_period = sorted_periods[i + 1]
            prev_data = values.get(prev_period, {})
            prev_value = prev_data.get("value") if isinstance(prev_data, dict) else prev_data
            if value is not None and prev_value is not None and prev_value != 0:
                yoy = round((value - prev_value) / abs(prev_value) * 100, 2)
        
        result[period] = {
            "value": value,
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


def _cache_to_response_format(cached_statement: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Convert cached format (period -> {label: value}) to response format (list of rows).
    """
    if not cached_statement:
        return []
    
    # Collect all labels across periods
    all_labels = set()
    for period_data in cached_statement.values():
        all_labels.update(period_data.keys())
    
    # Build response format
    result = []
    for label in all_labels:
        values = {}
        for period, period_data in cached_statement.items():
            if label in period_data:
                values[period] = period_data[label]
        
        if values:
            result.append({
                "label": label,
                "values": values
            })
    
    return result


@router.get("/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(
    ticker: str = Query(..., description="Stock ticker symbol"),
    type: str = Query("annual", description="annual or quarterly")
):
    """
    Fetch historical financial statements from SEC EDGAR.
    Returns Income Statement, Balance Sheet, and Cash Flow with YoY changes.
    Uses SQLite caching with incremental updates.
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = type.lower() == "annual"
        period_type = "annual" if is_annual else "quarterly"
        
        # Check SQLite cache first
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
                    
                    return FundamentalsResponse(
                        success=True,
                        ticker=ticker,
                        period_type=type,
                        periods=sorted(cached_periods, reverse=True),
                        income=income_data,
                        balance=balance_data,
                        cashflow=cashflow_data
                    )
        
        # Cache miss or insufficient data: fetch from SEC EDGAR
        print(f"[*] {ticker} fundamentals (fetching from SEC EDGAR...)")
        
        # Get company
        company = Company(ticker)
        
        # Fetch filings
        form_type = "10-K" if is_annual else "10-Q"
        num_filings = 10 if is_annual else 40  # 10 years annual or ~10 years quarterly
        
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
                error=f"No {form_type} filings found for {ticker}"
            )
        
        # Use XBRLS stitching for both annual and quarterly
        xbrls = XBRLS.from_filings(filings)
        statements = xbrls.statements
        
        # Extract statements to DataFrames
        income_df = None
        balance_df = None
        cashflow_df = None
        
        try:
            income_stmt = statements.income_statement()
            if income_stmt:
                income_df = income_stmt.to_dataframe()
        except Exception as e:
            print(f"Income statement error: {e}")
        
        try:
            balance_stmt = statements.balance_sheet()
            if balance_stmt:
                balance_df = balance_stmt.to_dataframe()
        except Exception as e:
            print(f"Balance sheet error: {e}")
        
        try:
            cashflow_stmt = statements.cashflow_statement()
            if cashflow_stmt:
                cashflow_df = cashflow_stmt.to_dataframe()
        except Exception as e:
            print(f"Cash flow error: {e}")
        
        # Process statements
        income_data, income_periods = process_statement_df(income_df, is_annual)
        balance_data, balance_periods = process_statement_df(balance_df, is_annual)
        cashflow_data, cashflow_periods = process_statement_df(cashflow_df, is_annual)
        
        # Combine all periods
        all_periods = set(income_periods + balance_periods + cashflow_periods)
        periods = sorted(list(all_periods), reverse=True)
        
        # Save to SQLite cache
        if CACHE_ENABLED and periods:
            save_fundamentals_batch(
                ticker, period_type,
                income_data, balance_data, cashflow_data,
                periods
            )
            print(f"[OK] {ticker} fundamentals ({len(periods)} periods fetched and cached)")
        
        return FundamentalsResponse(
            success=True,
            ticker=ticker,
            period_type=type,
            periods=periods,
            income=income_data,
            balance=balance_data,
            cashflow=cashflow_data
        )
        
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

