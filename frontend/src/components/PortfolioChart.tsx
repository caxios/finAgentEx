"use client";

import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

interface PortfolioChartProps {
    data: any; // API response data
}

const PortfolioChart: React.FC<PortfolioChartProps> = ({ data }) => {
    if (!data || !data.timestamps) {
        return <div className="text-center text-gray-500 py-10">No data available to chart</div>;
    }

    // Transform API data to Recharts format
    // Recharts needs array of objects: [{ date: '...', NVDA: 10, AMD: 5 }, ...]
    const chartData = data.timestamps.map((date: string, idx: number) => {
        const point: any = { date };

        // Add stock data
        Object.keys(data.stocks).forEach(ticker => {
            const stockData = data.stocks[ticker].data;
            if (stockData && idx < stockData.length) {
                point[ticker] = stockData[idx];
            }
        });

        // Add index data
        if (data.index && data.index.data && idx < data.index.data.length) {
            point["Category Index"] = data.index.data[idx];
        }

        return point;
    });

    const formatMarketCap = (mCap: number) => {
        if (!mCap) return '';
        if (mCap >= 1e12) return `(${(mCap / 1e12).toFixed(1)}T)`;
        if (mCap >= 1e9) return `(${(mCap / 1e9).toFixed(1)}B)`;
        if (mCap >= 1e6) return `(${(mCap / 1e6).toFixed(1)}M)`;
        return '';
    };

    return (
        <div className="w-full h-[500px] bg-white rounded-lg shadow-md p-4 mt-4">
            <h3 className="text-lg font-bold mb-4 text-center">Peformance Comparison (Normalized %)</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart
                    data={chartData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="date"
                        minTickGap={30}
                        tickFormatter={(val) => val.slice(5)} // Show MM-DD
                    />
                    <YAxis
                        unit="%"
                        label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                        labelStyle={{ color: '#000' }}
                        formatter={(value: any) => [`${Number(value).toFixed(2)}%`, '']}
                    />
                    <Legend
                        formatter={(value, entry: any) => {
                            const ticker = value;
                            // Attempt to find market cap from data.stocks
                            // entry.payload might contain reference, but simplest is to look up in props.data
                            const mCap = data?.stocks?.[ticker]?.marketCap;
                            return <span className="mr-2 font-medium">{ticker} <span className="text-xs text-gray-500">{formatMarketCap(mCap)}</span></span>;
                        }}
                    />

                    {/* Render lines for each stock */}
                    {Object.keys(data.stocks).map(ticker => (
                        <Line
                            key={ticker}
                            type="monotone"
                            dataKey={ticker}
                            stroke={data.stocks[ticker].color}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6 }}
                        />
                    ))}

                    {/* Render Index line (Thicker, Black) */}
                    <Line
                        key="Category Index"
                        type="monotone"
                        dataKey="Category Index"
                        stroke="#000000"
                        strokeWidth={4}
                        strokeDasharray="5 5"
                        dot={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default PortfolioChart;
