'use client';

import { useState, useEffect, useCallback } from 'react';

interface ValueWithYoY {
    value: number | null;
    yoy: number | null;
}

interface FinancialRow {
    label: string;
    values: Record<string, ValueWithYoY>;
}

interface FundamentalsData {
    success: boolean;
    ticker: string;
    period_type: string;
    periods: string[];
    income: FinancialRow[];
    balance: FinancialRow[];
    cashflow: FinancialRow[];
    error?: string;
}

interface FundamentalsPanelProps {
    ticker: string;
}

const TABS = ['Income Statement', 'Balance Sheet', 'Cash Flow'] as const;
type TabType = typeof TABS[number];

export default function FundamentalsPanel({ ticker }: FundamentalsPanelProps) {
    const [periodType, setPeriodType] = useState<'annual' | 'quarterly'>('annual');
    const [activeTab, setActiveTab] = useState<TabType>('Income Statement');
    const [data, setData] = useState<FundamentalsData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchData = useCallback(async () => {
        if (!ticker) return;
        setLoading(true);
        setError('');

        try {
            const res = await fetch(
                `http://localhost:8000/api/fundamentals?ticker=${ticker}&type=${periodType}`
            );
            const result = await res.json();

            if (result.success) {
                setData(result);
            } else {
                setError(result.error || 'Failed to fetch fundamentals');
            }
        } catch (e) {
            setError('Failed to connect to server');
        } finally {
            setLoading(false);
        }
    }, [ticker, periodType]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Format value
    const formatValue = (val: number | null): string => {
        if (val === null || val === undefined) return '-';
        const absVal = Math.abs(val);
        if (absVal >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
        if (absVal >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
        if (absVal >= 1e3) return `$${(val / 1e3).toFixed(1)}K`;
        return `$${val.toFixed(0)}`;
    };

    // Format YoY
    const formatYoY = (yoy: number | null): string => {
        if (yoy === null || yoy === undefined) return '';
        const sign = yoy >= 0 ? '+' : '';
        return `${sign}${yoy.toFixed(1)}%`;
    };

    // Get YoY color
    const getYoYColor = (yoy: number | null): string => {
        if (yoy === null) return 'text-slate-500';
        return yoy >= 0 ? 'text-emerald-400' : 'text-rose-400';
    };

    // Get current data based on active tab
    const getActiveData = (): FinancialRow[] => {
        if (!data) return [];
        switch (activeTab) {
            case 'Income Statement': return data.income;
            case 'Balance Sheet': return data.balance;
            case 'Cash Flow': return data.cashflow;
            default: return [];
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 bg-slate-800/30 rounded-2xl">
                <div className="flex items-center gap-3 text-slate-400">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Loading fundamentals (SEC EDGAR)...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-64 bg-slate-800/30 rounded-2xl">
                <div className="text-center">
                    <div className="text-rose-400 mb-2">{error}</div>
                    <div className="text-slate-500 text-sm">Note: Only US stocks are supported (SEC EDGAR)</div>
                </div>
            </div>
        );
    }

    const rows = getActiveData();
    const periods = data?.periods || [];

    return (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-4 backdrop-blur-sm">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                    📊 {ticker} Fundamentals
                </h3>

                {/* Period Type Toggle */}
                <div className="flex items-center gap-2 bg-slate-900/50 rounded-lg p-1">
                    <button
                        onClick={() => setPeriodType('annual')}
                        className={`px-3 py-1.5 text-sm rounded-md transition-all ${periodType === 'annual'
                                ? 'bg-blue-500 text-white'
                                : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        Annual (10Y)
                    </button>
                    <button
                        onClick={() => setPeriodType('quarterly')}
                        className={`px-3 py-1.5 text-sm rounded-md transition-all ${periodType === 'quarterly'
                                ? 'bg-blue-500 text-white'
                                : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        Quarterly
                    </button>
                </div>
            </div>

            {/* Statement Tabs */}
            <div className="flex gap-1 mb-4 border-b border-slate-700/50">
                {TABS.map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${activeTab === tab
                                ? 'border-blue-500 text-blue-400'
                                : 'border-transparent text-slate-400 hover:text-white'
                            }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-slate-400 border-b border-slate-700/50">
                            <th className="text-left py-2 px-2 font-medium sticky left-0 bg-slate-800/80 min-w-[200px]">
                                Item
                            </th>
                            {periods.slice(0, 10).map(period => (
                                <th key={period} className="text-right py-2 px-3 font-medium whitespace-nowrap">
                                    {period.split('-')[0]}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr>
                                <td colSpan={periods.length + 1} className="py-8 text-center text-slate-500">
                                    No data available
                                </td>
                            </tr>
                        ) : (
                            rows.map((row, idx) => (
                                <tr
                                    key={idx}
                                    className="border-b border-slate-800/50 hover:bg-slate-700/20 transition-colors"
                                >
                                    <td className="py-2 px-2 text-slate-300 sticky left-0 bg-slate-800/80">
                                        {row.label}
                                    </td>
                                    {periods.slice(0, 10).map(period => {
                                        const cell = row.values[period];
                                        return (
                                            <td key={period} className="py-2 px-3 text-right whitespace-nowrap">
                                                <div className="text-slate-200 font-mono">
                                                    {formatValue(cell?.value)}
                                                </div>
                                                {cell?.yoy !== null && cell?.yoy !== undefined && (
                                                    <div className={`text-xs ${getYoYColor(cell?.yoy)}`}>
                                                        {formatYoY(cell?.yoy)}
                                                    </div>
                                                )}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer */}
            <div className="mt-4 text-xs text-slate-500 text-center">
                Data source: SEC EDGAR • US stocks only
            </div>
        </div>
    );
}
