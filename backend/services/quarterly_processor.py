from typing import List, Dict, Any, Union, Optional, Tuple
import pandas as pd
from datetime import datetime
import re
from edgar import Company

from backend.services.fundamentals_utils import (
    date_to_label, calculate_yoy, merge_fundamentals_data
)

def is_discrete_quarter(start_date: Union[str, datetime], end_date: Union[str, datetime]) -> bool:
    """
    Check if the period represents a discrete quarter (~90 days).
    Accepts 80-100 days as valid range.
    """
    try:
        def parse(d):
            if isinstance(d, str):
                return datetime.strptime(d, "%Y-%m-%d")
            return d
            
        s = parse(start_date)
        e = parse(end_date)
        
        days = (e - s).days
        return 80 <= days <= 100
    except:
        return False

def _process_quarterly_df(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Process DataFrame for Quarterly data.
    STRICTLY enforce discrete quarter checks (80-100 days).
    """
    if df is None or df.empty:
        return [], []
    
    rows = []
    
    # Robust column detection: Detect columns that look like dates (YYYY-MM-DD)
    date_col_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    period_cols = []
    for col in df.columns:
        col_str = str(col)
        if date_col_pattern.match(col_str):
            period_cols.append(col)
    
    if not period_cols:
         metadata_cols = ['label', 'concept', 'standard_concept', 'depth', 'is_total', 'section', 'confidence', 'start_date', 'end_date']
         period_cols = [col for col in df.columns if col not in metadata_cols]

    # Convert date columns to readable labels (is_annual=False)
    period_mapping = {
        col: date_to_label(str(col), is_annual=False)
        for col in period_cols
    }
    
    # Check if we have duration columns for filtering
    has_duration = 'start_date' in df.columns and 'end_date' in df.columns
    
    for idx, row in df.iterrows():
        label = str(row.get('label', row.get('concept', 'Unknown')))
        concept = str(row.get('concept', ''))  # Capture concept for merging
        
        # Quarter Discrete Check (CRITICAL)
        if has_duration:
            s_date = row.get('start_date')
            e_date = row.get('end_date')
            if not is_discrete_quarter(s_date, e_date):
                # Skip non-discrete quarters (YTD filters)
                continue
        # If no duration columns, we might be risking YTD data inclusion, 
        # but EDGAR usually provides these. 

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


def fetch_quarterly_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch, process, and return Quarterly fundamentals.
    Returns: {'income': [], 'balance': [], 'cashflow': [], 'periods': []}
    """
    try:
        company = Company(ticker)
        # Fetch generous number of filings to ensure we catch enough discrete quarters filtering out YTDs
        filings = company.get_filings(form=["10-K", "10-Q"], amendments=False).head(40)
        
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
                        return _process_quarterly_df(stmt.to_dataframe())
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
                # print(f"Error processing filing {filing.accession_number}: {e}")
                continue
        
        data = {
            'income': merge_fundamentals_data(chunk_income),
            'balance': merge_fundamentals_data(chunk_balance),
            'cashflow': merge_fundamentals_data(chunk_cashflow),
            'periods': sorted(list(all_periods), reverse=True)
        }
        return data

    except Exception as e:
        print(f"Error fetching quarterly data for {ticker}: {e}")
        return {'income': [], 'balance': [], 'cashflow': [], 'periods': []}
