from typing import Dict, Any, List
from edgar import Company
from edgar.xbrl import XBRLS


def fetch_fundamentals_data(ticker: str, period_type: str = "annual") -> Dict[str, Any]:
    """
    Fetch fundamentals using XBRLS render_statement().
    Uses edgartools' built-in YoY comparison and standardization.
    """
    try:
        ticker = ticker.upper().strip()
        is_annual = period_type.lower() == "annual"

        # 1. Fetch Filings
        company = Company(ticker)
        if is_annual:
            filings = company.get_filings(form="10-K").filter(amendments=False).head(10)
        else:
            filings = company.get_filings(form="10-Q").filter(amendments=False).head(12)

        if not filings or len(filings) == 0:
            return _empty_response()

        # 2. Initialize XBRLS
        try:
            xbrls = XBRLS.from_filings(filings)
        except Exception as e:
            print(f"Error initializing XBRLS for {ticker}: {e}")
            return _empty_response()

        # 3. Render Statements (edgartools handles standardization & YoY)
        max_periods = 10 if is_annual else 12

        income_stmt = xbrls.render_statement('IncomeStatement', max_periods=max_periods, standardize=True)
        balance_stmt = xbrls.render_statement('BalanceSheet', max_periods=max_periods, standardize=True)
        cashflow_stmt = xbrls.render_statement('CashFlowStatement', max_periods=max_periods, standardize=True)

        # 4. Convert to frontend format
        comparison_data = income_stmt.metadata.get('comparison_data', {})

        income_data = _convert_statement(income_stmt, comparison_data, is_annual)
        balance_data = _convert_statement(balance_stmt, balance_stmt.metadata.get('comparison_data', {}), is_annual)
        cashflow_data = _convert_statement(cashflow_stmt, cashflow_stmt.metadata.get('comparison_data', {}), is_annual)

        # 5. Collect periods
        periods = _get_period_labels(income_stmt, is_annual)

        return {
            'income': income_data,
            'balance': balance_data,
            'cashflow': cashflow_data,
            'periods': periods
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return _empty_response()


def _convert_statement(stmt, comparison_data: Dict, is_annual: bool) -> List[Dict[str, Any]]:
    """Convert RenderedStatement to frontend format."""
    rows = []
    df = stmt.to_dataframe()

    # Get period columns (date columns like '2024-01-28')
    period_cols = [c for c in df.columns if c not in ['concept', 'label', 'level', 'abstract', 'dimension', 'is_breakdown']]

    for _, row in df.iterrows():
        if row.get('abstract', False):
            continue

        label = str(row.get('label', ''))
        concept = str(row.get('concept', ''))

        # Skip empty labels
        if not label or label == 'nan':
            continue

        values_map = {}

        for col in period_cols:
            raw_val = row.get(col)
            if raw_val is None or (isinstance(raw_val, float) and str(raw_val) == 'nan'):
                continue

            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                continue

            # Get YoY from comparison_data
            yoy = None
            if concept in comparison_data:
                for pk, (change, _) in comparison_data[concept].items():
                    if col in pk:
                        yoy = round(change * 100, 2) if change is not None else None
                        break

            # Convert date to display label
            display_period = _date_to_display(col, is_annual)

            values_map[display_period] = {
                "value": val,
                "yoy": yoy
            }

        if values_map:
            rows.append({
                "label": label,
                "concept": concept,
                "values": values_map
            })

    return rows


def _get_period_labels(stmt, is_annual: bool) -> List[str]:
    """Extract period labels from statement."""
    labels = []
    for p in stmt.periods:
        labels.append(_date_to_display(p.end_date, is_annual))
    return labels


def _date_to_display(date_str: str, is_annual: bool) -> str:
    """Convert date string to display format."""
    from datetime import datetime
    import re
    try:
        # Extract date part (handle cases like "2025-04-27 (Q2)")
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1)
        else:
            date_part = date_str

        d = datetime.strptime(date_part, "%Y-%m-%d")
        if is_annual:
            return str(d.year)
        else:
            q = (d.month - 1) // 3 + 1
            return f"{d.year}Q{q}"
    except:
        return date_str


def _empty_response():
    return {'income': [], 'balance': [], 'cashflow': [], 'periods': []}
