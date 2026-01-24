'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi } from 'lightweight-charts';

interface OHLCVItem {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma5: number | null;
    ma20: number | null;
    ma50: number | null;
    vol_ma5: number | null;
    vol_ma20: number | null;
    vol_ma50: number | null;
}

interface NewsItem {
    title: string;
    summary: string;
    url: string | null;
    pubDate: string;
}

interface ChartProps {
    ticker: string;
    period?: string;
}

export default function CandlestickChart({ ticker, period = '6mo' }: ChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [data, setData] = useState<OHLCVItem[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [hoveredData, setHoveredData] = useState<OHLCVItem | null>(null);
    const [selectedNews, setSelectedNews] = useState<NewsItem[]>([]);
    const [selectedDate, setSelectedDate] = useState<string | null>(null);
    const [loadingNews, setLoadingNews] = useState(false);

    // Fetch OHLCV data
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError('');
            try {
                const response = await fetch(
                    `http://localhost:8000/api/ohlcv?ticker=${ticker}&period=${period}`
                );
                const result = await response.json();
                if (result.success) {
                    setData(result.data);
                    setNews(result.news);
                } else {
                    setError(result.error || 'Failed to fetch data');
                }
            } catch (err) {
                setError('Failed to connect to server');
            } finally {
                setLoading(false);
            }
        };

        if (ticker) {
            fetchData();
        }
    }, [ticker, period]);

    // Create chart
    useEffect(() => {
        if (!chartContainerRef.current || data.length === 0) return;

        // Clear existing chart safely
        if (chartRef.current) {
            try {
                chartRef.current.remove();
            } catch (e) {
                // Chart already disposed, ignore
            }
            chartRef.current = null;
        }

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { color: 'transparent' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 500,
            crosshair: {
                mode: 1,
                vertLine: {
                    color: '#6366f1',
                    width: 1,
                    style: 2,
                },
                horzLine: {
                    color: '#6366f1',
                    width: 1,
                    style: 2,
                },
            },
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
            },
            rightPriceScale: {
                borderColor: '#334155',
            },
        });

        chartRef.current = chart;

        // Candlestick series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderUpColor: '#22c55e',
            borderDownColor: '#ef4444',
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });

        const candleData = data.map((d) => ({
            time: d.time,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        candleSeries.setData(candleData as any);

        // MA5 line
        const ma5Series = chart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 1,
        });
        ma5Series.setData(
            data.filter((d) => d.ma5 !== null).map((d) => ({ time: d.time, value: d.ma5! })) as any
        );

        // MA20 line
        const ma20Series = chart.addLineSeries({
            color: '#f97316',
            lineWidth: 1,
        });
        ma20Series.setData(
            data.filter((d) => d.ma20 !== null).map((d) => ({ time: d.time, value: d.ma20! })) as any
        );

        // MA50 line
        const ma50Series = chart.addLineSeries({
            color: '#a855f7',
            lineWidth: 1,
        });
        ma50Series.setData(
            data.filter((d) => d.ma50 !== null).map((d) => ({ time: d.time, value: d.ma50! })) as any
        );

        // Volume series (using histogram)
        const volumeSeries = chart.addHistogramSeries({
            color: '#6366f1',
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
        });

        chart.priceScale('volume').applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
        });

        const volumeData = data.map((d) => ({
            time: d.time,
            value: d.volume,
            color: d.close >= d.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
        }));
        volumeSeries.setData(volumeData as any);

        // Crosshair move handler
        chart.subscribeCrosshairMove((param) => {
            if (param.time) {
                const timeStr = param.time as string;
                const item = data.find((d) => d.time === timeStr);
                if (item) {
                    setHoveredData(item);
                }
            } else {
                setHoveredData(null);
            }
        });

        // Click handler
        chart.subscribeClick((param) => {
            if (param.time) {
                const timeStr = param.time as string;
                handleDateClick(timeStr);
            }
        });

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            try {
                chart.remove();
            } catch (e) {
                // Chart already disposed
            }
        };
    }, [data]);

    // Handle date click - fetch news
    const handleDateClick = async (date: string) => {
        setSelectedDate(date);
        setLoadingNews(true);
        setSelectedNews([]);

        // First check pre-fetched news
        const matchedNews = news.filter((n) => n.pubDate === date);
        if (matchedNews.length > 0) {
            setSelectedNews(matchedNews as NewsItem[]);
            setLoadingNews(false);
            return;
        }

        // Fallback to API
        try {
            const response = await fetch(
                `http://localhost:8000/api/news-by-date?ticker=${ticker}&date=${date}`
            );
            const result = await response.json();
            if (result.success) {
                setSelectedNews(result.news);
            }
        } catch (err) {
            console.error('Failed to fetch news:', err);
        } finally {
            setLoadingNews(false);
        }
    };

    const formatVolume = (vol: number) => {
        if (vol >= 1e9) return (vol / 1e9).toFixed(2) + 'B';
        if (vol >= 1e6) return (vol / 1e6).toFixed(2) + 'M';
        if (vol >= 1e3) return (vol / 1e3).toFixed(2) + 'K';
        return vol.toString();
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96 bg-slate-800/30 rounded-2xl">
                <div className="text-slate-400">Loading chart data...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-96 bg-slate-800/30 rounded-2xl">
                <div className="text-rose-400">{error}</div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Chart Container */}
            <div className="relative bg-slate-800/30 border border-slate-700/50 rounded-2xl p-4 backdrop-blur-sm">
                <h3 className="text-lg font-semibold text-white mb-4">
                    {ticker} - Interactive Candlestick Chart
                </h3>

                <div ref={chartContainerRef} className="w-full" />

                {/* Info Panels (positioned at bottom) */}
                <div className="flex gap-4 mt-4">
                    {/* OHLCV Info Panel */}
                    <div className="flex-1 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
                        <h4 className="text-sm text-slate-400 mb-2">
                            {hoveredData ? `📊 ${hoveredData.time}` : '📊 Hover over a candle'}
                        </h4>
                        {hoveredData ? (
                            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-slate-500">Open:</span>
                                    <span className="text-white font-mono">${hoveredData.open.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">High:</span>
                                    <span className="text-emerald-400 font-mono">${hoveredData.high.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">Low:</span>
                                    <span className="text-rose-400 font-mono">${hoveredData.low.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">Close:</span>
                                    <span className="text-white font-mono">${hoveredData.close.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">Volume:</span>
                                    <span className="text-slate-300 font-mono">{formatVolume(hoveredData.volume)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">MA5:</span>
                                    <span className="text-blue-400 font-mono">
                                        {hoveredData.ma5 ? `$${hoveredData.ma5.toFixed(2)}` : '-'}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">MA20:</span>
                                    <span className="text-orange-400 font-mono">
                                        {hoveredData.ma20 ? `$${hoveredData.ma20.toFixed(2)}` : '-'}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-500">MA50:</span>
                                    <span className="text-purple-400 font-mono">
                                        {hoveredData.ma50 ? `$${hoveredData.ma50.toFixed(2)}` : '-'}
                                    </span>
                                </div>
                                <div className="flex justify-between col-span-2 border-t border-slate-700 pt-1 mt-1">
                                    <span className="text-slate-500">Vol MA5/20/50:</span>
                                    <span className="text-slate-300 font-mono text-xs">
                                        {hoveredData.vol_ma5 ? formatVolume(hoveredData.vol_ma5) : '-'} /
                                        {hoveredData.vol_ma20 ? formatVolume(hoveredData.vol_ma20) : '-'} /
                                        {hoveredData.vol_ma50 ? formatVolume(hoveredData.vol_ma50) : '-'}
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">Move your mouse over the chart to see details</p>
                        )}
                    </div>

                    {/* News Panel */}
                    <div className="flex-1 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 max-h-64 overflow-y-auto">
                        <h4 className="text-sm text-slate-400 mb-2">
                            {selectedDate ? `📰 News for ${selectedDate}` : '📰 Click a candle to see news'}
                        </h4>
                        {loadingNews ? (
                            <p className="text-slate-500 text-sm">Loading news...</p>
                        ) : selectedNews.length > 0 ? (
                            <div className="space-y-2">
                                {selectedNews.map((n, i) => (
                                    <div key={i} className="p-2 bg-slate-800/50 rounded-lg">
                                        <a
                                            href={n.url || '#'}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-sm text-blue-400 hover:text-blue-300 line-clamp-2"
                                        >
                                            {n.title}
                                        </a>
                                        {n.summary && (
                                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{n.summary}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : selectedDate ? (
                            <p className="text-slate-500 text-sm">No news found for this date</p>
                        ) : (
                            <p className="text-slate-500 text-sm">Click on a candle to view related news</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
