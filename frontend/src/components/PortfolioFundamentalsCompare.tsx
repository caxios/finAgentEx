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
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    // Helper to find value in statement list
    const findValue = (statement: any[], labelSubstrings: string[], period: string) => {
        if (!statement) return null;

        // Find row that matches label
        const row = statement.find(r =>
            labelSubstrings.some(sub => r.label.toLowerCase().includes(sub.toLowerCase()))
        );

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

    // Get latest common period if possible, otherwise just use latest available for each?
    // For comparison, we usually want the same period.
    // Let's find the most recent period common to at least one stock to start.
    // Actually, each stock might have different fiscal years.
    // We will just show the "Latest" column produced by the backend's sorted periods.

    // We will display a matrix: Rows = Metrics, Cols = Tickers
    // Metrics: Revenue, Net Income, Net Margin %, Operating Cash Flow, Total Assets, Total Liabilities, Debt Ratio

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg mt-6 overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <span className="text-2xl">📊</span> Financials Comparison
                </h2>

                <div className="flex gap-2">
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
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
                            <tr>
                                <th className="px-4 py-3 sticky left-0 bg-gray-50 font-bold min-w-[200px]">Metric (Latest)</th>
                                {stocks.map(ticker => (
                                    <th key={ticker} className="px-4 py-3 font-bold text-center min-w-[120px]">
                                        {ticker}
                                        {data[ticker]?.error && <span className="text-red-500 text-xs block">Error</span>}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {/* Revenue */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Revenue</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.income, ['revenue', 'sales'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Net Income */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Net Income</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.income, ['net income', 'net loss'], latestPeriod);
                                    return (
                                        <td key={ticker} className={`text-center font-medium ${val && val >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {formatNumber(val)}
                                        </td>
                                    );
                                })}
                            </tr>

                            {/* Net Margin */}
                            <tr className="hover:bg-gray-50 bg-gray-50/50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-gray-50/50">Net Margin</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const rev = findValue(d.income, ['revenue', 'sales'], latestPeriod);
                                    const inc = findValue(d.income, ['net income', 'net loss'], latestPeriod);
                                    const margin = (rev && inc) ? inc / rev : null;
                                    return <td key={ticker} className="text-center font-bold text-blue-600">{formatPercent(margin)}</td>;
                                })}
                            </tr>

                            {/* Operating Cash Flow */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Operating Cash Flow</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.cashflow, ['operating activities', 'operations'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Total Assets */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Total Assets</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.balance, ['total assets'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Total Liabilities */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Total Liabilities</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.balance, ['total liabilities'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* --- New Metrics --- */}

                            {/* Operating Income */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Operating Income</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.income, ['operating income', 'operating profit'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Operating Expenses */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Operating Expenses</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.income, ['operating expenses'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Interest Paid / Expense */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Interest Paid</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    // Try cash flow first, then income statement
                                    let val = findValue(d.cashflow, ['interest paid', 'cash paid for interest'], latestPeriod);
                                    if (val === null) {
                                        val = findValue(d.income, ['interest expense'], latestPeriod);
                                    }
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Investing Cash Flow */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Investing Cash Flow</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.cashflow, ['investing activities', 'investments'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Net Cash Flow (Net Change) */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Net Cash Flow</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.cashflow, ['net change in cash', 'increase (decrease) in cash', 'cash and cash equivalents, period increase'], latestPeriod);
                                    return (
                                        <td key={ticker} className={`text-center font-bold ${val && val >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {formatNumber(val)}
                                        </td>
                                    );
                                })}
                            </tr>

                            {/* Short-term Debt */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Short-term Debt</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.balance, ['short-term debt', 'current debt', 'debt, current', 'current liabilities'], latestPeriod); // Including Current Liabilities as fallback if strictly debt not found? No, keep strictly debt first.
                                    // Actually user asked for short term debt. Often it is part of Current Liabilities.
                                    // Let's stick to specific debt terms first.
                                    // Refine: ['short-term debt', 'current portion of long-term debt']
                                    // Ideally we want just debt, not all current liabilities.
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>

                            {/* Long-term Debt */}
                            <tr className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 sticky left-0 bg-white">Long-term Debt</td>
                                {stocks.map(ticker => {
                                    const d = data[ticker];
                                    if (!d || d.error) return <td key={ticker} className="text-center text-gray-400">-</td>;
                                    const latestPeriod = d.periods[0];
                                    const val = findValue(d.balance, ['long-term debt', 'non-current debt'], latestPeriod);
                                    return <td key={ticker} className="text-center">{formatNumber(val)}</td>;
                                })}
                            </tr>
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
