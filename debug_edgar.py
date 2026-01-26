from edgar import Company, set_identity
from edgar.xbrl import XBRLS
import pandas as pd

# Set identity
set_identity("FinAgentEx finagentex@example.com")

def debug_quarterly():
    ticker = "BE"
    print(f"Fetching data for {ticker}...")
    company = Company(ticker)
    
    # Get recent 10-Qs
    filings = company.get_filings(form="10-Q").head(4)
    if not filings:
        print("No filings found")
        return

    print(f"Found {len(filings)} filings")
    
    # Create XBRLS
    xbrls = XBRLS.from_filings(filings)
    statements = xbrls.statements
    
    # Try the fix method
    try:
        print("\n--- Trying period_view='Quarterly Comparison' ---")
        inc = statements.income_statement(period_view="Quarterly Comparison")
        if inc:
            df = inc.to_dataframe()
            # Print columns (which should be dates/periods)
            print("Columns:", df.columns.tolist())
            # Print a row like Revenue
            rev_row = df[df['label'].str.contains('Revenue', case=False, na=False)]
            if not rev_row.empty:
                print(rev_row.iloc[0])
            else:
                print("No Revenue row found")
            
            # Check period durations if possible (metadata might be hidden in df, but xbrl object has it)
            # Actually, let's verify if the values look like YTD or Quarterly.
            # Printing raw dataframe head
            print(df.head())
    except Exception as e:
        print(f"Error with period_view: {e}")

    # Try default
    try:
        print("\n--- Default View (no params) ---")
        inc = statements.income_statement()
        if inc:
            df = inc.to_dataframe()
            print("Columns:", df.columns.tolist())
            rev_row = df[df['label'].str.contains('Revenue', case=False, na=False)]
            if not rev_row.empty:
                print(rev_row.iloc[0])
    except Exception as e:
        print(f"Error default: {e}")

if __name__ == "__main__":
    debug_quarterly()
