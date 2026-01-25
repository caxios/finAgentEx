"""Test script to analyze XBRL period structure for 3-month vs YTD data"""
import os
os.environ['EDGAR_LOCAL_DATA_DIR'] = 'c:\\Users\\mrsim\\finAgentEx\\.edgar_cache'
os.environ['EDGAR_CACHE_DIR'] = 'c:\\Users\\mrsim\\finAgentEx\\.edgar_cache'

from edgar import Company, set_identity
set_identity("Test test@test.com")

c = Company("TSLA")
filing = c.get_filings(form="10-Q", amendments=False).latest()
print(f"Filing: {filing.filing_date} - {filing.form}")

xbrl = filing.xbrl()

# Check reporting periods
print("\nReporting periods:")
for p in xbrl.reporting_periods[:15]:
    print(f"  {p}")

# Check facts for Revenue
print("\nRevenue facts:")
facts = xbrl.facts
revenue_facts = facts.query().by_concept("Revenue").to_dataframe()
if not revenue_facts.empty:
    print(revenue_facts[['concept', 'label', 'value', 'period_type', 'start_date', 'end_date']].head(10))
