from typing import List, Dict, Any, Union, Optional, Tuple
import pandas as pd
from datetime import datetime
import re
from edgar import Company

from backend.services.fundamentals_utils import (
    date_to_label, calculate_yoy, merge_fundamentals_data
)

def is_annual_period(start_date: Union[str, datetime], end_date: Union[str, datetime]) -> bool:
    """
    Check if the period represents an annual period (~365 days).
    Accepts 350-375 days as valid range.
    """
    try:
        def parse(d):
            if isinstance(d, str):
                return datetime.strptime(d, "%Y-%m-%d")
            return d
            
        s = parse(start_date)
        e = parse(end_date)
        
        days = (e - s).days
        return 350 <= days <= 375
    except:
        return False

def _process_annual_df(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Process DataFrame for Annual data.
    Enforce annual duration checks.
    """
    if df is None or df.empty:
        return [], []
    
    rows = []
    
    date_col_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    period_cols = []
    for col in df.columns:
        if date_col_pattern.match(str(col)):
            period_cols.append(col)
    
    if not period_cols:
         metadata_cols = ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence', 'start_date', 'end_date']
         period_cols = [col for col in df.columns if col not in metadata_cols]

    # Convert date columns to readable labels (is_annual=True)
    period_mapping = {
        col: date_to_label(str(col), is_annual=True)
        for col in period_cols
    }
    
    has_duration = 'start_date' in df.columns and 'end_date' in df.columns
    
    for idx, row in df.iterrows():
        label = str(row.get('label', row.get('concept', 'Unknown')))
        concept = str(row.get('concept', ''))
        
        # Annual Check
        if has_duration:
            s_date = row.get('start_date')
            e_date = row.get('end_date')
            if not is_annual_period(s_date, e_date):
                # Skip non-annual periods
                continue

        values: Dict[str, Dict[str, float]] = {}
        for col in period_cols:
            val = row.get(col)
            if pd.isna(val):
                continue
            
            key = period_mapping[col]
            if key in values:
                continue

            try:
                values[key] = {"value": float(val)}
            except (ValueError, TypeError):
                pass
        
        if values:
            yoy_data = calculate_yoy(values, list(values.keys()))
            rows.append({
                "label": label,
                "concept": concept,
                "values": yoy_data
            })
    
    return rows, list(period_mapping.values())


def fetch_annual_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch, process, and return Annual fundamentals.
    Returns: {'income': [], 'balance': [], 'cashflow': [], 'periods': []}
    """
    try:
        company = Company(ticker)
        # Fetch 10-K filings (10 is usually enough for 5 years history)
        filings = company.get_filings(form="10-K", amendments=False).head(10)
        
        if not filings or len(filings) == 0:
            return {'income': [], 'balance': [], 'cashflow': [], 'periods': []}

        chunk_income = []
        chunk_balance = []
        chunk_cashflow = []
        all_periods = set()
        
        for filing in filings:
            try:
                f_obj = filing.obj()
                financials = getattr(f_obj, 'financials', None)
                if not financials: continue
                
                def extract(method):
                    stmt = getattr(financials, method)()
                    if stmt:
                        return _process_annual_df(stmt.to_dataframe())
                    return [], []

                i_rows, i_p = extract('income_statement')
                chunk_income.append(i_rows)
                all_periods.update(i_p)
                
                b_rows, b_p = extract('balance_sheet')
                chunk_balance.append(b_rows)
                all_periods.update(b_p)
                
                c_rows, c_p = extract('cashflow_statement')
                chunk_cashflow.append(c_rows)
                all_periods.update(c_p)
                
            except Exception as e:
                continue
        
        data = {
            'income': merge_fundamentals_data(chunk_income),
            'balance': merge_fundamentals_data(chunk_balance),
            'cashflow': merge_fundamentals_data(chunk_cashflow),
            'periods': sorted(list(all_periods), reverse=True)
        }
        return data

    except Exception as e:
        print(f"Error fetching annual data for {ticker}: {e}")
        return {'income': [], 'balance': [], 'cashflow': [], 'periods': []}
