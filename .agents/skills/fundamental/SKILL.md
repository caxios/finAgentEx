# SKILL: Fetch Historical Financial Statements using EdgarTools

## Description
This skill enables the retrieval and formatting of historical financial statements (Income Statement, Balance Sheet, Cash Flow) for a specific US public company using the `edgartools` Python library. It focuses on generating multi-period dataframes suitable for dashboard visualization (e.g., historical trend tabs).

## Dependencies
- `edgartools` (latest version)
- `pandas`

## Core Concepts
To provide a historical view, we cannot use the simple `company.get_financials()` method (which only fetches the latest 10-K). Instead, we must:

1. Fetch a series of past filings (e.g., last 5 years of 10-Ks).
2. Use **XBRL Stitching (`XBRLS`)** to align columns and concepts across different reporting periods.
3. Convert these stitched statements into Pandas DataFrames.

---

## Implementation Guide

### 1. Setup & Identity
**Crucial:** Before making any requests, the SEC EDGAR identity must be set.

```python
from edgar import set_identity
set_identity("YourAppName contact@example.com")
```

---

### 2. The Strategy: Multi-Period Stitching
Use `XBRLS.from_filings()` to create a unified view of financial data over time.  
This approach is superior to fetching individual filings manually because it automatically aligns concepts across periods.

#### Step-by-Step Code Pattern

```python
from edgar import Company
from edgar.xbrl import XBRLS
import pandas as pd

def get_historical_financials(ticker: str, num_years: int = 5):
    """
    Retrieves historical financial statements for a given ticker.
    
    Args:
        ticker (str): Stock symbol (e.g., "AAPL")
        num_years (int): Number of past annual filings to retrieve.
        
    Returns:
        dict: A dictionary containing 'income', 'balance', and 'cashflow' DataFrames.
    """
    company = Company(ticker)
    
    # 1. Get the last N annual filings (10-K)
    # amendments=False avoids incomplete 10-K/A filings
    filings = company.get_filings(form="10-K", amendments=False).head(num_years)
    
    if not filings:
        return None

    # 2. Stitch filings together using XBRLS
    xbrls = XBRLS.from_filings(filings)
    
    # 3. Extract Statements
    income_stmt = xbrls.statements.income_statement()
    balance_stmt = xbrls.statements.balance_sheet()
    cashflow_stmt = xbrls.statements.cashflow_statement()
    
    # 4. Convert to DataFrames
    dfs = {
        "income": income_stmt.to_dataframe(view="standard"),
        "balance": balance_stmt.to_dataframe(view="standard"),
        "cashflow": cashflow_stmt.to_dataframe(view="standard")
    }
    
    return dfs
```

---

### 3. Data Presentation & Formatting

When displaying the data in a dashboard or table UI:

- **Columns**  
  The resulting DataFrame typically includes:
  - `label`
  - `concept`
  - Date-based columns (e.g., `2025-12-31`, `2024-12-31`)

- **Sorting**  
  Ensure period columns are sorted chronologically for correct trend visualization.

- **Units**  
  EDGAR values are usually in raw units.
  - Divide by `1e9` for billions
  - Divide by `1e6` for millions

---

### 4. Advanced: Standardized Metrics (Optional)
If stitched statements are inconsistent due to taxonomy changes, fall back to standardized metrics.

```python
financials = company.get_financials()
metrics = financials.get_financial_metrics()

# Example access
metrics["revenue"]
metrics["net_income"]
metrics["free_cash_flow"]
```

⚠️ Note: This method works per filing. For historical trends, manual iteration is required if not using `XBRLS`.

---

## Troubleshooting & Edge Cases

- **"No financial data found"**
  - Smaller or newer companies may not have XBRL data.
  - Always check `filing.xbrl()` before processing.

- **Quarterly Data**
  - Use `form="10-Q"` instead of `10-K`.
  - Increase `head()` size (e.g., 12 filings for ~3 years).

- **Missing Columns**
  - Indicates inconsistent XBRL structures or missing filings.
  - Common for older filings or restated periods.

---

## Example Output Structure (DataFrame)

| Label         | Concept                    | 2023-12-31 | 2022-12-31 | 2021-12-31 |
|---------------|----------------------------|------------|------------|------------|
| Revenue       | RevenueFromContract...     | 383,285M   | 394,328M   | 365,817M   |
| Cost of Sales | CostOfGoodsAndServ...      | 214,136M   | 223,546M   | 212,981M   |

---

## Use Cases
- Financial dashboards (historical tabs)
- Cross-period trend analysis
- Fundamental screening pipelines
- LLM-based financial agents

---

## Notes
- Always respect SEC rate limits.
- Set a clear EDGAR identity string.
- Prefer stitched views for trends; standardized metrics for robustness.
