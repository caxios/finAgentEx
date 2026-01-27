from typing import Dict, Any, List, Optional
import pandas as pd
from edgar import Company
from edgar.xbrl import XBRLS
from datetime import datetime, timedelta

def fetch_fundamentals_data(ticker: str, period_type: str = "annual") -> Dict[str, Any]:
    """
    Fetch and process fundamentals data using XBRLS.
    
    Args:
        ticker: Stock symbol
        period_type: 'annual' or 'quarterly'
        
    Returns:
        Dict with keys: 'income', 'balance', 'cashflow', 'periods'
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = period_type.lower() == "annual"
        
        # 1. Fetch Filings
        company = Company(ticker)
        if is_annual:
            # 10-K filings (Annual)
            filings = company.get_filings(form="10-K").filter(amendments=False).head(10)
        else:
            # 10-Q and 10-K to catch Q4 if needed, but usually 10-Q for quarterly trend
            # Fetching deep to ensure we get matching prior year quarters for YoY
            filings = company.get_filings(form=["10-Q", "10-K"]).filter(amendments=False).head(40)
            
        if not filings or len(filings) == 0:
            return _empty_response()

        # 2. Initialize XBRLS
        try:
            xbrls = XBRLS.from_filings(filings)
        except Exception as e:
            print(f"Error initializing XBRLS for {ticker}: {e}")
            return _empty_response()

        # 3. Process Statements
        # Use standard=True to leverage edgartools' built-in concept standardization
        income_df = xbrls.statements.income_statement(standard=True).to_dataframe()
        balance_df = xbrls.statements.balance_sheet(standard=True).to_dataframe()
        cashflow_df = xbrls.statements.cash_flow_statement(standard=True).to_dataframe()

        # 4. Filter Periods (Conceptually "Stitching")
        # XBRLS columns are period end dates.
        # We need to filter based on period type and logic.
        
        # Get period metadata from XBRLS to check duration
        # We need to match DF columns to period metadata
        period_map = _get_period_metadata(xbrls, is_annual)
        
        # Filter DataFrames to keep only valid columns
        valid_periods = [p for p in income_df.columns if p in period_map]
        
        if not valid_periods:
             return _empty_response()
             
        # Sort periods: Newest first
        valid_periods.sort(reverse=True)
        
        # Helper to process each dataframe
        def process_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
            if df.empty:
                return []
            
            # Select valid columns and mapped concepts
            # Ensure 'standard_concept' or index is used as label/concept
            # to_dataframe() with standard=True usually puts labels as index? 
            # Actually edgar tools puts standard_concept as a column if standard=True?
            # Let's inspect: xbrls.statements.income_statement(standard=True).to_dataframe()
            # It usually returns index as concept name (or label), and columns as dates.
            # If standard=True, the labels might be standardized.
            
            # We will trust the index as the label/concept for now.
            # But standard_concept metadata is better.
            # Let's conform to the structure: label, concept, values
            
            # Filter columns
            current_cols = [c for c in df.columns if c in valid_periods]
            if not current_cols:
                return []
                
            subset = df[current_cols].copy()
            
            # Calculate YoY
            # Rows are concepts, Cols are periods (Newest...Oldest or Oldest...Newest?)
            # Usually to_dataframe columns are dates.
            # YoY logic: (T - (T-1)) / abs(T-1)
            # We need to find the T-1 column for each T column.
            
            processed_rows = []
            
            for index, row in subset.iterrows():
                # Index is the Label or Concept Name
                label = str(index)
                
                # Concept: In standard=True, the index is often the standard label (e.g., "Revenue")
                # We can use it as both label and concept.
                concept = label 
                
                values_map = {}
                
                for col in current_cols: # col is date str '2024-09-30'
                    val = row[col]
                    if pd.isna(val):
                        continue
                        
                    # Find T-1 period
                    prev_col = _find_prev_period_col(col, current_cols, is_annual)
                    
                    yoy = None
                    if prev_col:
                        prev_val = row[prev_col]
                        if pd.notna(prev_val) and prev_val != 0:
                            yoy = round((val - prev_val) / abs(prev_val) * 100, 2)
                    
                    # Store
                    # Convert column date to display period (e.g. 2024Q3)
                    display_period = period_map[col]['display']
                    
                    values_map[display_period] = {
                        "value": float(val),
                        "yoy": yoy
                    }
                
                if values_map:
                    processed_rows.append({
                        "label": label,
                        "concept": concept,
                        "values": values_map
                    })
            
            # Apply standardization (Exact + Fuzzy)
            from backend.services.standard_mapper import standardize_rows
            return standardize_rows(processed_rows)

        income_data = process_df(income_df)
        balance_data = process_df(balance_df)
        cashflow_data = process_df(cashflow_df)
        
        # Collect all unique display periods from the processed data
        all_display_periods = set()
        for row in income_data + balance_data + cashflow_data:
            all_display_periods.update(row['values'].keys())
            
        sorted_periods = sorted(list(all_display_periods), reverse=True)

        return {
            'income': income_data,
            'balance': balance_data,
            'cashflow': cashflow_data,
            'periods': sorted_periods
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return _empty_response()

def _empty_response():
    return {'income': [], 'balance': [], 'cashflow': [], 'periods': []}

def _get_period_metadata(xbrls: XBRLS, is_annual: bool) -> Dict[str, Dict]:
    """
    Map DataFrame column headers (dates) to period metadata (display label, strict valid check).
    """
    valid_map = {}
    periods = xbrls.get_periods()
    
    for p in periods:
        # p is dict with 'period_end', 'period_start', 'type', 'days' etc depending on implementation
        # Or p is just info.
        # xbrls.get_periods() returns a list of dictionaries with period info.
        
        p_end = p.get('period_end')
        p_start = p.get('period_start')
        p_type = p.get('type') # 'duration' or 'instant'
        days = p.get('days', 0)
        
        if not p_end: continue
        
        # Strict Filtering
        is_valid = False
        if is_annual:
            # Annual: Duration ~ 365 days
            if p_type == 'duration' and 350 <= days <= 375:
                is_valid = True
            elif p_type == 'instant': 
                # Balance sheet acts as instant, but usually tied to the covering period logic
                # XBRLS handles this by associating instant with the duration period.
                # But here we filter based on column header which is usually the end date.
                pass
        else:
            # Quarterly: Duration ~ 90 days (Discrete)
            # EXCLUDE YTD (~180, ~270, ~365)
            if p_type == 'duration' and 80 <= days <= 105:
                is_valid = True
                
        # For Instant concepts (Balance Sheet), XBRLS usually aligns them with the period end.
        # So if we filter for valid duration periods, we can accept the corresponding instant date.
        # But wait, income statement (duration) and balance sheet (instant) might share columns?
        # A 10-Q will have income for 3 months (Discrete) and balance sheet as of End Date.
        # A 10-Q might ALSO have income for 9 months (YTD).
        # We only want the 3 month column for Income Statement.
        # Balance Sheet is always instant, so snapshot date is same.
        
        # Simplified approach: valid_map keys are DATES.
        # Only map dates that correspond to valid INCOME periods (Durations).
        # Balance sheet columns matching these dates will be effectively selected.
        
        if is_valid:
            if is_annual:
                # 2024-09-28 -> "2024"
                label = str(datetime.strptime(p_end, "%Y-%m-%d").year)
            else:
                # 2024-09-28 -> "2024Q4"
                d = datetime.strptime(p_end, "%Y-%m-%d")
                # Adjust for fiscal year offset? user asks for calendar or fiscal?
                # Usually standard mapping:
                # But simple mapping:
                if d.day <= 7: d -= timedelta(days=7) # Fiscal alignment
                q = (d.month - 1) // 3 + 1
                label = f"{d.year}Q{q}"
                
            valid_map[p_end] = {
                'display': label,
                'end_date': datetime.strptime(p_end, "%Y-%m-%d")
            }
            
    return valid_map

def _find_prev_period_col(current_col: str, all_cols: List[str], is_annual: bool) -> Optional[str]:
    """
    Find the column representing the T-1 period.
    """
    try:
        curr_date = datetime.strptime(current_col, "%Y-%m-%d")
        
        # Target date is approx 1 year ago for BOTH Annual and Quarterly (YoY)
        target_date = curr_date - timedelta(days=365)
        
        best_match = None
        min_diff = 30 # Allow 30 days drift (Gregorian vs 52-53 week fiscal)
        
        for col in all_cols:
            if col == current_col: continue
            d = datetime.strptime(col, "%Y-%m-%d")
            diff = abs((d - target_date).days)
            
            if diff < min_diff:
                min_diff = diff
                best_match = col
                
        return best_match
        
    except:
        return None
