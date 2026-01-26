from typing import Dict, List, Any

# Standard Mapping Configuration
# Maps XBRL Concepts (and common variations) to Unified Display Labels
STANDARD_CONCEPT_MAP = {
    # Income Statement
    "Revenue": [
        "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap_Revenues",
        "us-gaap_SalesRevenueNet",
        "us-gaap_SalesRevenueGoodsNet",
        "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax"
    ],
    "Cost of Revenue": [
        "us-gaap_CostOfRevenue",
        "us-gaap_CostOfGoodsAndServicesSold",
        "us-gaap_CostOfGoodsSold",
        "us-gaap_CostOfServices"
    ],
    "Gross Profit": [
        "us-gaap_GrossProfit"
    ],
    "Operating Expenses": [
        "us-gaap_OperatingExpenses",
        "us-gaap_OperatingCostsAndExpenses"
    ],
    "Research & Development": [
        "us-gaap_ResearchAndDevelopmentExpense",
        "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"
    ],
    "Selling, General & Admin": [
        "us-gaap_SellingGeneralAndAdministrativeExpense"
    ],
    "Operating Income": [
        "us-gaap_OperatingIncomeLoss"
    ],
    "Net Income": [
        "us-gaap_NetIncomeLoss",
        "us-gaap_ProfitLoss"
    ],
    "EPS (Basic)": [
        "us-gaap_EarningsPerShareBasic"
    ],
    "EPS (Diluted)": [
        "us-gaap_EarningsPerShareDiluted"
    ],
    
    # Balance Sheet
    "Total Assets": [
        "us-gaap_Assets"
    ],
    "Total Liabilities": [
        "us-gaap_Liabilities"
    ],
    "Total Equity": [
        "us-gaap_StockholdersEquity",
        "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
    ],
    "Cash & Equivalents": [
        "us-gaap_CashAndCashEquivalentsAtCarryingValue",
        "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    ],
    
    # Cash Flow
    "Operating Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInOperatingActivities"
    ],
    "Investing Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInInvestingActivities"
    ],
    "Financing Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInFinancingActivities"
    ],
    "Free Cash Flow": [
        # FCF is usually calculated, but sometimes reported
    ]
}

# Reverse map for O(1) lookup: concept -> Standard Label
CONCEPT_TO_LABEL = {}
for std_label, concepts in STANDARD_CONCEPT_MAP.items():
    for concept in concepts:
        CONCEPT_TO_LABEL[concept] = std_label

def standardize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Standardize a list of rows (Income/Balance/Cashflow).
    If a row's concept matches a standard key, update its 'label'.
    """
    if not rows:
        return []

    # clone rows to avoid mutating original cache if shared references exist
    new_rows = []
    
    # We might have multiple rows mapping to the SAME standard label (e.g. Revenue vs Other Revenue)
    # In a Portfolio Summary View, we usually want the MAIN one.
    # But a simple re-labeling is safer than merging rows here to avoid data loss.
    # The frontend usually picks by label.
    
    for row in rows:
        new_row = row.copy()
        concept = row.get('concept')
        
        # Try to map by XBRL Concept first
        if concept and concept in CONCEPT_TO_LABEL:
            new_row['label'] = CONCEPT_TO_LABEL[concept]
        
        # (Optional) Map by Label text similarity if concept is missing? 
        # Risky, let's stick to explicit XBRL concepts for 100% accuracy requested by user.
        
        new_rows.append(new_row)
        
    return new_rows
