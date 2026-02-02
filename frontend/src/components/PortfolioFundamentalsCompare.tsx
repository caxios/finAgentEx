import React, { useState, useEffect } from 'react';

interface FundamentalsResponse {
    ticker: string;
    period_type: string;
    periods: string[];
    income: any[];
    balance: any[];
    cashflow: any[];
    error?: string;
}

interface Props {
    stocks: string[];
}

export default function PortfolioFundamentalsCompare({ stocks }: Props) {
    const [data, setData] = useState<Record<string, FundamentalsResponse>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [periodType, setPeriodType] = useState<'annual' | 'quarterly'>('annual');
    const [availablePeriods, setAvailablePeriods] = useState<string[]>([]);

    useEffect(() => {
        if (stocks.length > 0) {
            fetchBatchData();
        }
    }, [stocks, periodType]);

    const fetchBatchData = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await fetch('http://localhost:8000/api/fundamentals/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: stocks,
                    period_type: periodType
                })
            });

            if (!res.ok) throw new Error('Failed to fetch batch data');

            const result = await res.json();
            setData(result);

            // Extract all unique periods
            const allPeriods = new Set<string>();
            Object.values(result).forEach((d: any) => {
                if (d.periods) {
                    d.periods.forEach((p: string) => allPeriods.add(p));
                }
            });
            // Sort periods (descending)
            const sortedPeriods = Array.from(allPeriods).sort().reverse();
            setAvailablePeriods(sortedPeriods);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    // Helper to find value in statement list
    // Supports both concept-based matching (preferred) and label-based fallback
    const findValue = (statement: any[], identifiers: string[], period: string) => {
        if (!statement) return null;

        // 1. Try exact concept match first (most reliable)
        let row = statement.find(r =>
            identifiers.some(id => r.concept === id)
        );

        // 2. Fallback to exact label match
        if (!row) {
            row = statement.find(r =>
                identifiers.some(id => r.label.toLowerCase() === id.toLowerCase())
            );
        }

        // 3. Fallback to partial label match
        if (!row) {
            row = statement.find(r =>
                identifiers.some(id => r.label.toLowerCase().includes(id.toLowerCase()))
            );
        }

        if (!row || !row.values[period]) return null;
        return row.values[period].value;
    };

    const formatNumber = (num: number | null) => {
        if (num === null || num === undefined) return '-';
        if (Math.abs(num) >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (Math.abs(num) >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toLocaleString()}`;
    };

    const formatPercent = (num: number | null) => {
        if (num === null) return '-';
        return `${(num * 100).toFixed(2)}%`;
    };

    // Helper to get previous period string (YoY)
    const getPrevPeriod = (currentPeriod: string, type: 'annual' | 'quarterly') => {
        if (type === 'annual') {
            const year = parseInt(currentPeriod);
            return isNaN(year) ? null : (year - 1).toString();
        } else {
            // Format "2025Q4" or "2025-Q4" or however it comes. 
            // The image shows "2025Q4". 
            // Regex to parse Year and Quarter
            const match = currentPeriod.match(/^(\d{4})Q(\d)$/);
            if (match) {
                const year = parseInt(match[1]);
                const q = match[2];
                return `${year - 1}Q${q}`;
            }
            return null;
        }
    };

    // Render helper for a cell containing multiple tickers
    const renderCell = (
        getValue: (d: FundamentalsResponse, p: string) => number | null,
        formatter: (v: number | null) => string = formatNumber,
        colorCondition?: (v: number) => string
    ) => {
        return availablePeriods.map(period => (
            <td key={period} className="px-2 py-3 text-center min-w-[160px] align-top border-l border-gray-100">
                <div className="flex flex-col gap-1">
                    {stocks.map(ticker => {
                        const d = data[ticker];
                        if (!d || d.error) return null;

                        const val = getValue(d, period);
                        const displayVal = formatter(val);
                        const colorClass = (val !== null && colorCondition) ? colorCondition(val) : '';

                        // Calculate YoY
                        let yoyChange: number | null = null;
                        const prevPeriod = getPrevPeriod(period, periodType);
                        if (prevPeriod && val !== null) {
                            const prevVal = getValue(d, prevPeriod);
                            if (prevVal !== null && prevVal !== 0) {
                                yoyChange = ((val - prevVal) / Math.abs(prevVal)) * 100;
                            }
                        }

                        return (
                            <div key={ticker} className="flex justify-between items-center text-xs px-2 py-0.5 hover:bg-gray-50 rounded">
                                <span className="font-bold text-gray-500 w-10 text-left shrink-0">{ticker}:</span>
                                <div className="flex items-center justify-end gap-2 text-right w-full">
                                    <span className={`font-medium ${colorClass}`}>{displayVal}</span>
                                    {yoyChange !== null && (
                                        <span className={`text-[10px] w-12 text-right ${yoyChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                            {yoyChange > 0 ? '+' : ''}{yoyChange.toFixed(1)}%
                                        </span>
                                    )}
                                    {yoyChange === null && (
                                        <span className="text-[10px] w-12 text-right text-gray-300">-</span>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </td>
        ));
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg mt-6 overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <span className="text-2xl">📊</span> Financials Comparison
                </h2>

                <div className="flex gap-2 items-center">
                    <button
                        onClick={() => setPeriodType('annual')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${periodType === 'annual'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        Annual
                    </button>
                    <button
                        onClick={() => setPeriodType('quarterly')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${periodType === 'quarterly'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        Quarterly
                    </button>
                </div>
            </div>

            {loading && (
                <div className="text-center py-10">
                    <div className="animate-spin text-blue-500 text-4xl mb-2">⟳</div>
                    <p className="text-gray-500">Fetching financial data for {stocks.length} companies...</p>
                </div>
            )}

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-4">
                    {error}
                </div>
            )}

            {!loading && !error && Object.keys(data).length > 0 && (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left border-collapse">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
                            <tr>
                                <th className="px-4 py-3 sticky left-0 bg-gray-50 font-bold min-w-[180px] z-10 shadow-sm">Metric</th>
                                {availablePeriods.map(period => (
                                    <th key={period} className="px-4 py-3 font-bold text-center min-w-[140px] border-l border-gray-200">
                                        {period}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {/* Revenue */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Revenue</td>
                                {renderCell((d, p) => findValue(d.income, ['us-gaap_Revenues', 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 'revenue', 'net sales'], p))}
                            </tr>

                            {/* Operating Expenses */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Operating Expenses</td>
                                {renderCell((d, p) => findValue(d.income, ['us-gaap_OperatingExpenses', 'us-gaap_CostsAndExpenses', 'operating expenses', 'total operating expenses'], p))}
                            </tr>

                            {/* Operating Income */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Operating Income</td>
                                {renderCell((d, p) => findValue(d.income, ['us-gaap_OperatingIncomeLoss', 'operating income', 'income from operations'], p))}
                            </tr>

                            {/* Net Income */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Net Income</td>
                                {renderCell(
                                    (d, p) => findValue(d.income, ['us-gaap_NetIncomeLoss', 'net income'], p),
                                    formatNumber,
                                    (val) => val >= 0 ? 'text-green-600' : 'text-red-600'
                                )}
                            </tr>

                            {/* Net Margin */}
                            <tr className="hover:bg-gray-50 bg-gray-50/50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-gray-50/50 z-10 shadow-sm border-r border-gray-100">Net Margin</td>
                                {renderCell(
                                    (d, p) => {
                                        const rev = findValue(d.income, ['us-gaap_Revenues', 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 'revenue', 'net sales'], p);
                                        const inc = findValue(d.income, ['us-gaap_NetIncomeLoss', 'net income'], p);
                                        return (rev && inc) ? inc / rev : null;
                                    },
                                    formatPercent,
                                    () => 'text-blue-600 font-bold'
                                )}
                            </tr>

                            {/* --- New Metrics --- */}

                            {/* Operating Cash Flow */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Operating Cash Flow</td>
                                {renderCell((d, p) => findValue(d.cashflow, ['us-gaap_NetCashProvidedByUsedInOperatingActivities', 'operating activities', 'operations'], p))}
                            </tr>

                            {/* Investing Cash Flow */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Investing Cash Flow</td>
                                {renderCell((d, p) => findValue(d.cashflow, ['us-gaap_NetCashProvidedByUsedInInvestingActivities', 'investing activities'], p))}
                            </tr>

                            {/* Net Cash Flow */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Net Cash Flow</td>
                                {renderCell(
                                    (d, p) => findValue(d.cashflow, ['us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 'us-gaap_CashAndCashEquivalentsPeriodIncreaseDecrease', 'net change in cash'], p),
                                    formatNumber,
                                    (val) => val >= 0 ? 'text-green-600' : 'text-red-600'
                                )}
                            </tr>

                            {/* Total Assets */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Total Assets</td>
                                {renderCell((d, p) => findValue(d.balance, ['us-gaap_Assets', 'total assets'], p))}
                            </tr>

                            {/* Total Liabilities */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Total Liabilities</td>
                                {renderCell((d, p) => findValue(d.balance, ['us-gaap_Liabilities', 'total liabilities'], p))}
                            </tr>

                            {/* Short-term Debt */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Short-term Debt</td>
                                {renderCell((d, p) => findValue(d.balance, ['us-gaap_DebtCurrent', 'us-gaap_ShortTermBorrowings', 'us-gaap_CommercialPaper', 'us-gaap_LongTermDebtCurrent', 'short-term debt'], p))}
                            </tr>

                            {/* Long-term Debt */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Long-term Debt</td>
                                {renderCell((d, p) => findValue(d.balance, ['us-gaap_LongTermDebtNoncurrent', 'us-gaap_LongTermDebt', 'us-gaap_LongTermDebtAndCapitalLeaseObligations', 'long-term debt'], p))}
                            </tr>

                            {/* Interest Paid */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white z-10 shadow-sm border-r border-gray-100">Interest Expense</td>
                                {renderCell((d, p) => {
                                    let val = findValue(d.income, ['us-gaap_InterestExpense', 'us-gaap_InterestExpenseNonoperating', 'interest expense'], p);
                                    if (val === null) val = findValue(d.cashflow, ['us-gaap_InterestPaidNet', 'interest paid'], p);
                                    return val;
                                })}
                            </tr>

                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
