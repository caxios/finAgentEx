from edgar import Company, set_identity
import pandas as pd

set_identity("FinAgentEx finagentex@example.com")

def debug_mu():
    try:
        print("Fetching MU filings...")
        company = Company("MU")
        # Get a recent 10-Q (not 10-K)
        filings = company.get_filings(form="10-Q").head(5)
        
        for filing in filings:
            print(f"\nFiling: {filing.accession_number} Date: {filing.filing_date}")
            f_obj = filing.obj()
            financials = getattr(f_obj, 'financials', None)
            
            if not financials:
                print("No financials object.")
                continue
                
            income = financials.income_statement()
            if income:
                df = income.to_dataframe()
                print("Columns:", list(df.columns))
                print("Row count:", len(df))
                
                # Check for net income and revenue
                found_rev = False
                for idx, row in df.iterrows():
                    concept = str(row.get('concept', ''))
                    label = str(row.get('label', ''))
                    if 'Revenue' in concept or 'Sales' in label:
                        print(f"  [Row] {label} ({concept})")
                        # Print non-null values
                        vals = {k:v for k,v in row.items() if k not in ['concept','label','level','abstract','dimension','balance','weight','preferred_sign'] and pd.notna(v)}
                        print(f"    Values: {vals}")
                        found_rev = True
                        break
                if not found_rev:
                    print("  No Revenue row found.")
            else:
                print("No income statement found.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_mu()
