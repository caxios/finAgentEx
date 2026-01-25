"""
Fundamentals Router - Historical financial statements using edgartools
Returns 10 years of annual/quarterly data with YoY calculations
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd

# EDGAR environment variables are set in main.py before this import
from edgar import Company, set_identity
from edgar.xbrl import XBRLS

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


def calculate_yoy(values: Dict[str, float], periods: List[str]) -> Dict[str, Dict[str, Any]]:
    """Calculate YoY % change for each period."""
    result = {}
    sorted_periods = sorted(periods, reverse=True)  # Most recent first
    
    for i, period in enumerate(sorted_periods):
        value = values.get(period)
        yoy = None
        
        # Calculate YoY if we have previous period
        if i + 1 < len(sorted_periods):
            prev_period = sorted_periods[i + 1]
            prev_value = values.get(prev_period)
            if value is not None and prev_value is not None and prev_value != 0:
                yoy = round((value - prev_value) / abs(prev_value) * 100, 2)
        
        result[period] = {
            "value": value,
            "yoy": yoy
        }
    
    return result


def format_value(value: float) -> str:
    """Format value in billions/millions."""
    if value is None:
        return None
    abs_val = abs(value)
    if abs_val >= 1e9:
        return round(value / 1e9, 2)
    elif abs_val >= 1e6:
        return round(value / 1e6, 2)
    else:
        return round(value, 2)


def process_statement_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process DataFrame to structured list with YoY calculations."""
    if df is None or df.empty:
        return []
    
    rows = []
    # Get period columns (exclude metadata columns)
    period_cols = [col for col in df.columns if col not in ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence']]
    
    for _, row in df.iterrows():
        label = row.get('label', row.get('concept', 'Unknown'))
        
        # Extract values for each period
        values = {}
        for col in period_cols:
            val = row.get(col)
            if pd.notna(val):
                try:
                    values[str(col)] = float(val)
                except (ValueError, TypeError):
                    pass
        
        if values:  # Only include rows with data
            yoy_data = calculate_yoy(values, list(values.keys()))
            rows.append({
                "label": str(label),
                "values": yoy_data
            })
    
    return rows


@router.get("/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(
    ticker: str = Query(..., description="Stock ticker symbol"),
    type: str = Query("annual", description="annual or quarterly")
):
    """
    Fetch historical financial statements from SEC EDGAR.
    Returns Income Statement, Balance Sheet, and Cash Flow with YoY changes.
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = type.lower() == "annual"
        
        # Get company
        company = Company(ticker)
        
        # Fetch filings
        form_type = "10-K" if is_annual else "10-Q"
        num_filings = 10 if is_annual else 40  # 10 years annual or 10 years quarterly
        
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
        
        # Stitch filings together
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
        income_data = process_statement_df(income_df)
        balance_data = process_statement_df(balance_df)
        cashflow_data = process_statement_df(cashflow_df)
        
        # Extract periods from data
        periods = set()
        for item in income_data + balance_data + cashflow_data:
            periods.update(item.get("values", {}).keys())
        periods = sorted(list(periods), reverse=True)  # Most recent first
        
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
