from edgar import Company, set_identity
import pandas as pd
import re

set_identity("FinAgentEx finagentex@example.com")

def debug_tsla():
    try:
        print("Fetching TSLA filings...")
        company = Company("TSLA")
        filings = company.get_filings(form="10-Q").head(1)
        if not filings:
            print("No filings.")
            return

        filing = filings[0]
        print(f"Filing: {filing.accession_number}")
        
        f_obj = filing.obj()
        financials = getattr(f_obj, 'financials', None)
        
        income = financials.income_statement()
        if income:
            df = income.to_dataframe()
            print("\nColumns:", list(df.columns))
            
            # Check for Total Revenues
            print("\nScanning for Revenue-like rows...")
            for idx, row in df.iterrows():
                label = str(row.get('label', row.get('concept', '')))
                if 'revenu' in label.lower() or 'sales' in label.lower():
                    print(f"Row: {label}")
                    print(row.to_dict())
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_tsla()
