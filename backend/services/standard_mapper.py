from typing import Dict, List, Any

# Standard Mapping Configuration
# Maps XBRL Concepts (and common variations) to Unified Display Labels
STANDARD_CONCEPT_MAP = {
    # =========================================================================
    # INCOME STATEMENT
    # =========================================================================
    "Revenue": [
        "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap_Revenues",
        "us-gaap_SalesRevenueNet",
        "us-gaap_SalesRevenueGoodsNet",
        "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap_SalesRevenueServicesNet",
        "us-gaap_RegulatedAndUnregulatedOperatingRevenue",
        "us-gaap_ElectricUtilityRevenue",
        "us-gaap_OilAndGasRevenue",
        "us-gaap_HealthCareOrganizationRevenue",
        "us-gaap_FinancialServicesRevenue",
        "us-gaap_RealEstateRevenueNet",
        "us-gaap_ContractsRevenue",
    ],
    "Cost of Revenue": [
        "us-gaap_CostOfRevenue",
        "us-gaap_CostOfGoodsAndServicesSold",
        "us-gaap_CostOfGoodsSold",
        "us-gaap_CostOfServices",
        "us-gaap_CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
    ],
    "Gross Profit": [
        "us-gaap_GrossProfit",
    ],
    "Total Costs & Expenses": [
        "us-gaap_CostsAndExpenses",
    ],
    "Operating Expenses": [
        "us-gaap_OperatingExpenses",
        "us-gaap_OperatingCostsAndExpenses",
        "us-gaap_CostsAndExpenses",
    ],
    "Research & Development": [
        "us-gaap_ResearchAndDevelopmentExpense",
        "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "us-gaap_ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost",
    ],
    "Selling, General & Admin": [
        "us-gaap_SellingGeneralAndAdministrativeExpense",
        "us-gaap_SellingAndMarketingExpense",
        "us-gaap_GeneralAndAdministrativeExpense",
    ],
    "Operating Income": [
        "us-gaap_OperatingIncomeLoss",
    ],
    "Interest Expense": [
        "us-gaap_InterestExpense",
        "us-gaap_InterestExpenseNonoperating",
        "us-gaap_InterestExpenseDebt",
        "us-gaap_InterestIncomeExpenseNonoperatingNet",
        "us-gaap_InterestExpenseDeposits",
        "us-gaap_RepaymentsOfDebtAndCapitalLeaseObligations",
    ],
    "Interest Income": [
        "us-gaap_InvestmentIncomeInterest",
        "us-gaap_InvestmentIncomeNet",
        "us-gaap_InterestIncomeOther",
        "us-gaap_InterestAndDividendIncomeOperating",
        "us-gaap_InterestIncome",
    ],
    "Other Income (Expense)": [
        "us-gaap_NonoperatingIncomeExpense",
        "us-gaap_OtherNonoperatingIncomeExpense",
        "us-gaap_OtherOperatingIncomeExpenseNet",
        "us-gaap_OtherIncome",
        "us-gaap_OtherNonoperatingIncome",
    ],
    "Income Before Tax": [
        "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
        "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign",
    ],
    "Income Tax Expense": [
        "us-gaap_IncomeTaxExpenseBenefit",
        "us-gaap_IncomeTaxExpenseBenefitContinuingOperations",
        "us-gaap_CurrentIncomeTaxExpenseBenefit",
    ],
    "Net Income": [
        "us-gaap_NetIncomeLoss",
        "us-gaap_ProfitLoss",
        "us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic",
        "us-gaap_NetIncomeLossAvailableToCommonStockholdersDiluted",
    ],
    "EPS (Basic)": [
        "us-gaap_EarningsPerShareBasic",
    ],
    "EPS (Diluted)": [
        "us-gaap_EarningsPerShareDiluted",
    ],
    "Shares Outstanding (Basic)": [
        "us-gaap_WeightedAverageNumberOfSharesOutstandingBasic",
        "us-gaap_CommonStockSharesOutstanding",
    ],
    "Shares Outstanding (Diluted)": [
        "us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "EBITDA": [
        "us-gaap_EarningsBeforeInterestTaxesDepreciationAndAmortization",
    ],

    # =========================================================================
    # BALANCE SHEET - Assets
    # =========================================================================
    "Cash & Equivalents": [
        "us-gaap_CashAndCashEquivalentsAtCarryingValue",
        "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "us-gaap_Cash",
    ],
    "Short-term Investments": [
        "us-gaap_ShortTermInvestments",
        "us-gaap_MarketableSecuritiesCurrent",
        "us-gaap_AvailableForSaleSecuritiesDebtSecuritiesCurrent",
        "us-gaap_HeldToMaturitySecuritiesCurrent",
        "us-gaap_TradingSecuritiesCurrent",
    ],
    "Cash & Short-term Investments": [
        "us-gaap_CashCashEquivalentsAndShortTermInvestments",
    ],
    "Accounts Receivable": [
        "us-gaap_AccountsReceivableNetCurrent",
        "us-gaap_AccountsReceivableNet",
        "us-gaap_ReceivablesNetCurrent",
        "us-gaap_TradeAndOtherReceivablesNetCurrent",
    ],
    "Inventory": [
        "us-gaap_InventoryNet",
        "us-gaap_InventoryFinishedGoods",
        "us-gaap_InventoryGross",
    ],
    "Total Current Assets": [
        "us-gaap_AssetsCurrent",
    ],
    "Property, Plant & Equipment": [
        "us-gaap_PropertyPlantAndEquipmentNet",
        "us-gaap_PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization",
        "us-gaap_PropertyPlantAndEquipmentGross",
    ],
    "Goodwill": [
        "us-gaap_Goodwill",
    ],
    "Intangible Assets": [
        "us-gaap_IntangibleAssetsNetExcludingGoodwill",
        "us-gaap_IntangibleAssetsNetIncludingGoodwill",
        "us-gaap_FiniteLivedIntangibleAssetsNet",
    ],
    "Long-term Investments": [
        "us-gaap_LongTermInvestments",
        "us-gaap_OtherLongTermInvestments",
        "us-gaap_AvailableForSaleSecuritiesDebtSecuritiesNoncurrent",
        "us-gaap_MarketableSecuritiesNoncurrent",
    ],
    "Total Assets": [
        "us-gaap_Assets",
    ],

    # =========================================================================
    # BALANCE SHEET - Liabilities
    # =========================================================================
    "Accounts Payable": [
        "us-gaap_AccountsPayableCurrent",
        "us-gaap_AccountsPayableAndAccruedLiabilitiesCurrent",
        "us-gaap_AccountsPayableTradeCurrent",
    ],
    "Short-term Debt": [
        "us-gaap_DebtCurrent",
        "us-gaap_ShortTermBorrowings",
        "us-gaap_CommercialPaper",
        "us-gaap_ShortTermDebt",
        "us-gaap_LongTermDebtCurrent",
        "us-gaap_NotesPayableCurrent",
    ],
    "Deferred Revenue": [
        "us-gaap_ContractWithCustomerLiabilityCurrent",
        "us-gaap_DeferredRevenueCurrent",
        "us-gaap_DeferredRevenueCurrentAndNoncurrent",
    ],
    "Total Current Liabilities": [
        "us-gaap_LiabilitiesCurrent",
    ],
    "Long-term Debt": [
        "us-gaap_LongTermDebtNoncurrent",
        "us-gaap_LongTermDebt",
        "us-gaap_LongTermDebtAndCapitalLeaseObligations",
        "us-gaap_LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
        "us-gaap_ConvertibleDebtNoncurrent",
        "us-gaap_SeniorLongTermNotes",
        "us-gaap_UnsecuredLongTermDebt",
    ],
    "Total Liabilities": [
        "us-gaap_Liabilities",
        "us-gaap_LiabilitiesAndStockholdersEquity",
    ],
    "Total Equity": [
        "us-gaap_StockholdersEquity",
        "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "Retained Earnings": [
        "us-gaap_RetainedEarningsAccumulatedDeficit",
        "us-gaap_RetainedEarningsUnappropriated",
    ],

    # =========================================================================
    # CASH FLOW STATEMENT
    # =========================================================================
    "Operating Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInOperatingActivities",
        "us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "Capital Expenditures": [
        "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
        "us-gaap_PaymentsToAcquireProductiveAssets",
        "us-gaap_PaymentsForCapitalImprovements",
        "us-gaap_CapitalExpendituresIncurredButNotYetPaid",
    ],
    "Investing Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInInvestingActivities",
        "us-gaap_NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
    ],
    "Financing Cash Flow": [
        "us-gaap_NetCashProvidedByUsedInFinancingActivities",
        "us-gaap_NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
    ],
    "Depreciation & Amortization": [
        "us-gaap_DepreciationDepletionAndAmortization",
        "us-gaap_DepreciationAndAmortization",
        "us-gaap_Depreciation",
        "us-gaap_DepreciationAmortizationAndAccretionNet",
    ],
    "Stock-based Compensation": [
        "us-gaap_ShareBasedCompensation",
        "us-gaap_AllocatedShareBasedCompensationExpense",
    ],
    "Dividends Paid": [
        "us-gaap_PaymentsOfDividends",
        "us-gaap_PaymentsOfDividendsCommonStock",
        "us-gaap_PaymentsOfDividendsPreferredStockAndPreferenceStock",
        "us-gaap_PaymentsOfOrdinaryDividends",
    ],
    "Stock Repurchases": [
        "us-gaap_PaymentsForRepurchaseOfCommonStock",
        "us-gaap_PaymentsForRepurchaseOfEquity",
        "us-gaap_PaymentsForRepurchaseOfOtherEquity",
    ],
    "Debt Issuance": [
        "us-gaap_ProceedsFromIssuanceOfDebt",
        "us-gaap_ProceedsFromIssuanceOfLongTermDebt",
        "us-gaap_ProceedsFromDebtNetOfIssuanceCosts",
        "us-gaap_ProceedsFromIssuanceOfSeniorLongTermDebt",
        "us-gaap_ProceedsFromIssuanceOfCommonStock",
    ],
    "Debt Repayment": [
        "us-gaap_RepaymentsOfDebt",
        "us-gaap_RepaymentsOfLongTermDebt",
        "us-gaap_RepaymentsOfLongTermDebtAndCapitalSecurities",
        "us-gaap_RepaymentsOfConvertibleDebt",
        "us-gaap_RepaymentsOfDebtAndCapitalLeaseObligations",
        "us-gaap_RepaymentsOfSeniorDebt",
    ],
    "Net Change in Cash": [
        "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
        "us-gaap_CashAndCashEquivalentsPeriodIncreaseDecrease",
        "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect",
    ],
    "Interest Paid": [
        "us-gaap_InterestPaidNet",
        "us-gaap_InterestPaid",
    ],
    "Income Taxes Paid": [
        "us-gaap_IncomeTaxesPaidNet",
        "us-gaap_IncomeTaxesPaid",
    ],
    "Free Cash Flow": [
        # FCF is usually calculated (Operating CF - CapEx), but sometimes reported
    ],
}

# Reverse map for O(1) lookup: concept -> Standard Label
CONCEPT_TO_LABEL = {}
for std_label, concepts in STANDARD_CONCEPT_MAP.items():
    for concept in concepts:
        CONCEPT_TO_LABEL[concept] = std_label

# Fuzzy matching rules: list of (substring_check_fn, target_label)
# Order matters: more specific rules come first to avoid false positives
_FUZZY_RULES = [
    # --- Income Statement (specific -> generic) ---
    (lambda c: "costofrevenue" in c or "costofgood" in c or "costofservice" in c,
     "Cost of Revenue"),
    (lambda c: "costsandexpenses" in c and "cost" in c,
     "Total Costs & Expenses"),
    (lambda c: "grosspro" in c,
     "Gross Profit"),
    (lambda c: "researchanddevelopment" in c,
     "Research & Development"),
    (lambda c: "sellinggeneralandadministrative" in c,
     "Selling, General & Admin"),
    (lambda c: "sellingandmarketing" in c or "generalandadministrative" in c,
     "Selling, General & Admin"),
    (lambda c: "operatingexpense" in c or "operatingcostsandexpenses" in c,
     "Operating Expenses"),
    (lambda c: "operatingincome" in c or "operatingincomeloss" in c,
     "Operating Income"),
    (lambda c: "interestexpense" in c and "income" not in c,
     "Interest Expense"),
    (lambda c: ("investmentincome" in c or "interestincome" in c) and "expense" not in c,
     "Interest Income"),
    (lambda c: "incometaxexpense" in c or "incometaxbenefit" in c,
     "Income Tax Expense"),
    (lambda c: "incomelossfromcontinuingoperationsbeforeincometax" in c,
     "Income Before Tax"),
    (lambda c: "earningspersharebasic" in c,
     "EPS (Basic)"),
    (lambda c: "earningspersharediluted" in c,
     "EPS (Diluted)"),
    (lambda c: "weightedaveragenumberofsharesoutstandingbasic" in c,
     "Shares Outstanding (Basic)"),
    (lambda c: "weightedaveragenumberofdilutedshares" in c,
     "Shares Outstanding (Diluted)"),
    (lambda c: "netincome" in c or "profitloss" in c,
     "Net Income"),
    # Revenue last (substring of CostOfRevenue)
    (lambda c: ("revenue" in c or "sales" in c) and "cost" not in c
     and "deferred" not in c and "increasedecrease" not in c,
     "Revenue"),

    # --- Balance Sheet ---
    (lambda c: "cashandcashequivalents" in c and "period" not in c and "shortterm" not in c,
     "Cash & Equivalents"),
    (lambda c: "cashcashequivalentsandshortterm" in c,
     "Cash & Short-term Investments"),
    (lambda c: "accountsreceivable" in c or "receivablesnet" in c or "tradeandotherreceivables" in c,
     "Accounts Receivable"),
    (lambda c: "inventorynet" in c or "inventoryfinished" in c or "inventorygross" in c,
     "Inventory"),
    (lambda c: "assetscurrent" in c and "total" not in c and "other" not in c and "deferred" not in c,
     "Total Current Assets"),
    (lambda c: "propertyplantandequipment" in c,
     "Property, Plant & Equipment"),
    (lambda c: "goodwill" in c and "impairment" not in c and "intangible" not in c,
     "Goodwill"),
    (lambda c: "intangibleassetsnet" in c or "finitelivedintangibleassets" in c,
     "Intangible Assets"),
    (lambda c: c == "us-gaap_assets",
     "Total Assets"),
    (lambda c: "accountspayable" in c and "increase" not in c,
     "Accounts Payable"),
    (lambda c: "debtcurrent" in c or "shorttermborrowings" in c or "commercialpaper" in c
     or "shorttermdebt" in c
     or ("longtermdebt" in c and "current" in c and "noncurrent" not in c),
     "Short-term Debt"),
    (lambda c: "contractwithcustomerliability" in c and "increase" not in c,
     "Deferred Revenue"),
    (lambda c: "liabilitiescurrent" in c,
     "Total Current Liabilities"),
    (lambda c: "longtermdebt" in c and "increase" not in c
     and ("noncurrent" in c or "current" not in c),
     "Long-term Debt"),
    (lambda c: c == "us-gaap_liabilities",
     "Total Liabilities"),
    (lambda c: "stockholdersequity" in c,
     "Total Equity"),
    (lambda c: "retainedearnings" in c,
     "Retained Earnings"),

    # --- Cash Flow ---
    (lambda c: "netcashprovidedbyusedinoperatingactivities" in c,
     "Operating Cash Flow"),
    (lambda c: "paymentstoacquirepropertyplantandequipment" in c
     or "paymentstoacquireproductiveassets" in c,
     "Capital Expenditures"),
    (lambda c: "netcashprovidedbyusedininvestingactivities" in c,
     "Investing Cash Flow"),
    (lambda c: "netcashprovidedbyusedinfinancingactivities" in c,
     "Financing Cash Flow"),
    (lambda c: ("depreciation" in c or "amortization" in c) and "increasedecrease" not in c
     and "rightofuse" not in c and "accumulated" not in c,
     "Depreciation & Amortization"),
    (lambda c: "sharebasedcompensation" in c or "stockbasedcompensation" in c,
     "Stock-based Compensation"),
    (lambda c: "paymentsofdividends" in c,
     "Dividends Paid"),
    (lambda c: "paymentsforrepurchase" in c,
     "Stock Repurchases"),
    (lambda c: ("proceedsfromissuanceofdebt" in c or "proceedsfromdebt" in c)
     and "repay" not in c,
     "Debt Issuance"),
    (lambda c: "repaymentsof" in c and "debt" in c,
     "Debt Repayment"),
    (lambda c: "cashcashequivalentsrestrictedcash" in c and "periodincreasedecrease" in c,
     "Net Change in Cash"),
    (lambda c: "interestpaid" in c,
     "Interest Paid"),
    (lambda c: "incometaxespaid" in c,
     "Income Taxes Paid"),
]


def standardize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Standardize a list of rows (Income/Balance/Cashflow).
    If a row's concept matches a standard key, update its 'label'.
    Uses exact mapping first, then rule-based fuzzy matching.
    """
    if not rows:
        return []

    new_rows = []

    for row in rows:
        new_row = row.copy()
        concept = row.get('concept')

        mapped = False

        # 1. Try Exact Map (O(1))
        if concept and concept in CONCEPT_TO_LABEL:
            new_row['label'] = CONCEPT_TO_LABEL[concept]
            mapped = True

        # 2. Try Rule-based Fuzzy Match
        if not mapped and concept and isinstance(concept, str):
            c_lower = concept.lower().replace("-", "").replace("_", "")
            for check_fn, target_label in _FUZZY_RULES:
                if check_fn(c_lower):
                    new_row['label'] = target_label
                    mapped = True
                    break

        new_rows.append(new_row)

    return new_rows
