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
    Includes FUZZY MATCHING for flexibility.
    """
    if not rows:
        return []

    # clone rows to avoid mutating original cache if shared references exist
    new_rows = []
    
    for row in rows:
        new_row = row.copy()
        concept = row.get('concept')
        
        mapped = False
        
        # 1. Try Exact Map (O(1))
        if concept and concept in CONCEPT_TO_LABEL:
            new_row['label'] = CONCEPT_TO_LABEL[concept]
            mapped = True
            
        # 2. Try Fuzzy Match if not mapped
        # Logic: If standard key (e.g., "Cost of Revenue") part is in concept string
        if not mapped and concept and isinstance(concept, str):
            c_lower = concept.lower()
            
            # Priority checks for robust fuzzy matching
            # Order matters: check specific long terms before generic short terms
            
            # Cost of Revenue / COGS
            if "costofrevenue" in c_lower or "costofgood" in c_lower or "costofservice" in c_lower:
                new_row['label'] = "Cost of Revenue"
                mapped = True
            
            # Operating Expenses (check before Operating Income)
            elif "operatingexpense" in c_lower:
                new_row['label'] = "Operating Expenses"
                mapped = True
                
            # R&D
            elif "researchanddevelopment" in c_lower:
                new_row['label'] = "Research & Development"
                mapped = True
            
            # SG&A
            elif "sellinggeneral" in c_lower or "sellingandmarketing" in c_lower:
                new_row['label'] = "Selling, General & Admin"
                mapped = True
            
            # Operating Income
            elif "operatingincome" in c_lower or "operatingloss" in c_lower:
                new_row['label'] = "Operating Income"
                mapped = True
                
            # Net Income
            elif "netincome" in c_lower or "profitloss" in c_lower:
                new_row['label'] = "Net Income"
                mapped = True
            
            # Revenue (Check late as it's often a substring of others like Cost of Revenue)
            elif "revenue" in c_lower or "sales" in c_lower:
                # Guard against false positives like "CostOfRevenue"
                if "cost" not in c_lower:
                    new_row['label'] = "Revenue"
                    mapped = True
                    
            # Cash Flow
            elif "cash" in c_lower and "operating" in c_lower:
                new_row['label'] = "Operating Cash Flow"
                mapped = True
            elif "cash" in c_lower and "investing" in c_lower:
                new_row['label'] = "Investing Cash Flow"
                mapped = True
            elif "cash" in c_lower and "financing" in c_lower:
                new_row['label'] = "Financing Cash Flow"
                mapped = True
        
        new_rows.append(new_row)
        
    return new_rows
