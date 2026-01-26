from edgar import Company, set_identity

# Set identity
set_identity("FinAgentEx finagentex@example.com")

def debug_single_filing():
    ticker = "BE"
    print(f"Fetching data for {ticker}...")
    company = Company(ticker)
    
    # Get ONE recent 10-Q
    filing = company.get_filings(form="10-Q").latest()
    print(f"Filing: {filing.form} {filing.filing_date}")
    
    # Get financials
    tenq = filing.obj()
    financials = tenq.financials
    
    if financials:
        print("\n--- Trying period_view='Quarterly Comparison' on single filing ---")
        try:
            # Does income_statement support period_view?
            # Check arguments helps if strict but python is dynamic
            inc = financials.income_statement(period_view="Quarterly Comparison")
             
            df = inc.to_dataframe()
            print("Columns:", df.columns.tolist())
            rev_row = df[df['label'].str.contains('Revenue', case=False, na=False)]
            if not rev_row.empty:
                print(rev_row.iloc[0])
            else:
                print("No Revenue row found")
        except Exception as e:
            print(f"Error: {e}")
            
        print("\n--- Trying default on single filing ---")
        try:
            inc = financials.income_statement()
            df = inc.to_dataframe()
            print("Columns:", df.columns.tolist())
            rev_row = df[df['label'].str.contains('Revenue', case=False, na=False)]
            if not rev_row.empty:
                print(rev_row.iloc[0])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_single_filing()
