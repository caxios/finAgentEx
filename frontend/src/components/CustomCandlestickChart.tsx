'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';

interface OHLCVItem {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma5: number | null;
    ma20: number | null;
    ma60: number | null;
    ma120: number | null;
    vol_ma5: number | null;
    vol_ma20: number | null;
    vol_ma60: number | null;
    vol_ma120: number | null;
    close_change_pct: number | null;
    volume_change_pct: number | null;
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

const COLORS = {
    up: '#22c55e',
    down: '#ef4444',
    ma5: '#3b82f6',
    ma20: '#f97316',
    ma60: '#a855f7',
    ma120: '#06b6d4',
    grid: '#1e293b',
    text: '#94a3b8',
};

export default function CustomCandlestickChart({ ticker, period = '6mo' }: ChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const svgRef = useRef<SVGSVGElement>(null);
    const dataRef = useRef<OHLCVItem[]>([]);
    const [data, setData] = useState<OHLCVItem[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [hoveredData, setHoveredData] = useState<OHLCVItem | null>(null);
    const [selectedDate, setSelectedDate] = useState<string | null>(null);
    const [selectedNews, setSelectedNews] = useState<NewsItem[]>([]);
    const [loadingNews, setLoadingNews] = useState(false);

    // Keep data in ref to avoid re-renders
    useEffect(() => {
        dataRef.current = data;
    }, [data]);

    // Fetch data
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
            } catch {
                setError('Failed to connect to server');
            } finally {
                setLoading(false);
            }
        };
        if (ticker) fetchData();
    }, [ticker, period]);

    // Handle date click for news
    const handleDateClick = useCallback(async (date: string) => {
        setSelectedDate(date);
        setLoadingNews(true);
        setSelectedNews([]);

        const matched = news.filter((n) => n.pubDate === date);
        if (matched.length > 0) {
            setSelectedNews(matched as NewsItem[]);
            setLoadingNews(false);
            return;
        }

        try {
            const res = await fetch(`http://localhost:8000/api/news-by-date?ticker=${ticker}&date=${date}`);
            const result = await res.json();
            if (result.success) setSelectedNews(result.news);
        } catch { /* ignore */ } finally {
            setLoadingNews(false);
        }
    }, [news, ticker]);

    // Draw chart
    useEffect(() => {
        if (!svgRef.current || !containerRef.current || data.length === 0) return;

        const container = containerRef.current;
        const width = container.clientWidth;
        const priceHeight = 350;
        const volumeHeight = 120;
        const totalHeight = priceHeight + volumeHeight + 40;
        const margin = { top: 20, right: 60, bottom: 30, left: 60 };

        // Clear previous
        d3.select(svgRef.current).selectAll('*').remove();

        const svg = d3.select(svgRef.current)
            .attr('width', width)
            .attr('height', totalHeight);

        const parseDate = d3.timeParse('%Y-%m-%d');
        const chartData = data.map(d => ({ ...d, date: parseDate(d.time)! }));

        // Scales
        const xScale = d3.scaleBand()
            .domain(chartData.map(d => d.time))
            .range([margin.left, width - margin.right])
            .padding(0.3);

        const yPriceScale = d3.scaleLinear()
            .domain([d3.min(chartData, d => d.low)! * 0.98, d3.max(chartData, d => d.high)! * 1.02])
            .range([priceHeight - margin.top, margin.top]);

        const yVolumeScale = d3.scaleLinear()
            .domain([0, d3.max(chartData, d => d.volume)! * 1.2])
            .range([totalHeight - margin.bottom, priceHeight + 20]);

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .selectAll('line')
            .data(yPriceScale.ticks(6))
            .join('line')
            .attr('x1', margin.left)
            .attr('x2', width - margin.right)
            .attr('y1', d => yPriceScale(d))
            .attr('y2', d => yPriceScale(d))
            .attr('stroke', COLORS.grid)
            .attr('stroke-dasharray', '2,2');

        // Price axis
        svg.append('g')
            .attr('transform', `translate(${width - margin.right}, 0)`)
            .call(d3.axisRight(yPriceScale).ticks(6).tickFormat(d => `$${d}`))
            .call(g => g.select('.domain').remove())
            .call(g => g.selectAll('.tick text').attr('fill', COLORS.text));

        // Volume axis
        svg.append('g')
            .attr('transform', `translate(${width - margin.right}, 0)`)
            .call(d3.axisRight(yVolumeScale).ticks(3).tickFormat(d => {
                const n = d as number;
                if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
                if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
                return `${(n / 1e3).toFixed(0)}K`;
            }))
            .call(g => g.select('.domain').remove())
            .call(g => g.selectAll('.tick text').attr('fill', COLORS.text));

        // X axis
        svg.append('g')
            .attr('transform', `translate(0, ${totalHeight - margin.bottom})`)
            .call(d3.axisBottom(xScale).tickValues(
                xScale.domain().filter((_, i) => i % Math.ceil(chartData.length / 8) === 0)
            ))
            .call(g => g.select('.domain').attr('stroke', COLORS.grid))
            .call(g => g.selectAll('.tick text').attr('fill', COLORS.text).attr('font-size', '10px'));

        // Candlesticks
        const candleWidth = xScale.bandwidth();

        // Wicks
        svg.selectAll('.wick')
            .data(chartData)
            .join('line')
            .attr('class', 'wick')
            .attr('x1', d => xScale(d.time)! + candleWidth / 2)
            .attr('x2', d => xScale(d.time)! + candleWidth / 2)
            .attr('y1', d => yPriceScale(d.high))
            .attr('y2', d => yPriceScale(d.low))
            .attr('stroke', d => d.close >= d.open ? COLORS.up : COLORS.down)
            .attr('pointer-events', 'none');

        // Bodies
        svg.selectAll('.candle')
            .data(chartData)
            .join('rect')
            .attr('class', 'candle')
            .attr('x', d => xScale(d.time)!)
            .attr('y', d => yPriceScale(Math.max(d.open, d.close)))
            .attr('width', candleWidth)
            .attr('height', d => Math.max(1, Math.abs(yPriceScale(d.open) - yPriceScale(d.close))))
            .attr('fill', d => d.close >= d.open ? COLORS.up : COLORS.down)
            .attr('pointer-events', 'none');

        // Volume bars
        svg.selectAll('.volume')
            .data(chartData)
            .join('rect')
            .attr('class', 'volume')
            .attr('x', d => xScale(d.time)!)
            .attr('y', d => yVolumeScale(d.volume))
            .attr('width', candleWidth)
            .attr('height', d => totalHeight - margin.bottom - yVolumeScale(d.volume))
            .attr('fill', d => d.close >= d.open ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)')
            .attr('pointer-events', 'none');

        // MA Lines helper
        const drawMALine = (key: keyof OHLCVItem, color: string, isVolume = false) => {
            const lineData = chartData.filter(d => d[key] !== null);
            const yScale = isVolume ? yVolumeScale : yPriceScale;
            const line = d3.line<typeof chartData[0]>()
                .x(d => xScale(d.time)! + candleWidth / 2)
                .y(d => yScale(d[key] as number))
                .curve(d3.curveMonotoneX);
            svg.append('path')
                .datum(lineData)
                .attr('fill', 'none')
                .attr('stroke', color)
                .attr('stroke-width', 1.5)
                .attr('d', line)
                .attr('pointer-events', 'none');
        };

        // Price MAs
        drawMALine('ma5', COLORS.ma5);
        drawMALine('ma20', COLORS.ma20);
        drawMALine('ma60', COLORS.ma60);
        drawMALine('ma120', COLORS.ma120);

        // Volume MAs
        drawMALine('vol_ma5', COLORS.ma5, true);
        drawMALine('vol_ma20', COLORS.ma20, true);
        drawMALine('vol_ma60', COLORS.ma60, true);
        drawMALine('vol_ma120', COLORS.ma120, true);

        // Crosshair
        const crosshairV = svg.append('line')
            .attr('stroke', '#6366f1')
            .attr('stroke-dasharray', '3,3')
            .attr('y1', margin.top)
            .attr('y2', totalHeight - margin.bottom)
            .style('opacity', 0)
            .attr('pointer-events', 'none');

        // Invisible hit areas for each candle (better than overlay)
        svg.selectAll('.hit-area')
            .data(chartData)
            .join('rect')
            .attr('class', 'hit-area')
            .attr('x', d => xScale(d.time)! - candleWidth * 0.2)
            .attr('y', margin.top)
            .attr('width', candleWidth * 1.4)
            .attr('height', totalHeight - margin.top - margin.bottom)
            .attr('fill', 'transparent')
            .attr('cursor', 'pointer')
            .on('mouseenter', (_, d) => {
                setHoveredData(d);
                crosshairV
                    .attr('x1', xScale(d.time)! + candleWidth / 2)
                    .attr('x2', xScale(d.time)! + candleWidth / 2)
                    .style('opacity', 1);
            })
            .on('click', (_, d) => {
                handleDateClick(d.time);
            });

        // Mouse leave from SVG
        svg.on('mouseleave', () => {
            setHoveredData(null);
            crosshairV.style('opacity', 0);
        });

    }, [data, handleDateClick]);

    // Helpers
    const formatVolume = (v: number) => {
        if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
        if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
        if (v >= 1e3) return (v / 1e3).toFixed(2) + 'K';
        return v.toFixed(0);
    };

    const formatPct = (pct: number | null) => {
        if (pct === null) return '-';
        const sign = pct >= 0 ? '+' : '';
        return `${sign}${pct.toFixed(2)}%`;
    };

    const getPctColor = (pct: number | null) => {
        if (pct === null) return 'text-slate-400';
        return pct >= 0 ? 'text-emerald-400' : 'text-rose-400';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96 bg-slate-800/30 rounded-2xl">
                <div className="text-slate-400">Loading chart...</div>
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
            <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-4 backdrop-blur-sm">
                {/* Header with legend */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">{ticker} - Candlestick Chart</h3>
                    <div className="flex gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5" style={{ background: COLORS.ma5 }}></span>MA5</span>
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5" style={{ background: COLORS.ma20 }}></span>MA20</span>
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5" style={{ background: COLORS.ma60 }}></span>MA60</span>
                        <span className="flex items-center gap-1"><span className="w-3 h-0.5" style={{ background: COLORS.ma120 }}></span>MA120</span>
                    </div>
                </div>

                {/* Chart */}
                <div ref={containerRef} className="w-full">
                    <svg ref={svgRef}></svg>
                </div>

                {/* Info panels - FIXED HEIGHT to prevent layout shift */}
                <div className="flex gap-4 mt-4">
                    {/* Data panel */}
                    <div className="flex-1 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 min-h-[200px]">
                        <h4 className="text-sm text-slate-400 mb-2">
                            {hoveredData ? `📊 ${hoveredData.time}` : '📊 Hover over a candle'}
                        </h4>
                        {hoveredData ? (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
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
                                    <span className="text-white font-mono">
                                        ${hoveredData.close.toFixed(2)}
                                        <span className={`ml-1 ${getPctColor(hoveredData.close_change_pct)}`}>
                                            ({formatPct(hoveredData.close_change_pct)})
                                        </span>
                                    </span>
                                </div>
                                <div className="flex justify-between col-span-2">
                                    <span className="text-slate-500">Volume:</span>
                                    <span className="text-slate-300 font-mono">
                                        {formatVolume(hoveredData.volume)}
                                        <span className={`ml-1 ${getPctColor(hoveredData.volume_change_pct)}`}>
                                            ({formatPct(hoveredData.volume_change_pct)})
                                        </span>
                                    </span>
                                </div>
                                <div className="col-span-2 border-t border-slate-700 pt-2 mt-1">
                                    <div className="text-slate-500 text-xs mb-1">Price MAs:</div>
                                    <div className="flex gap-3 text-xs">
                                        <span><span style={{ color: COLORS.ma5 }}>5:</span> {hoveredData.ma5 ?? '-'}</span>
                                        <span><span style={{ color: COLORS.ma20 }}>20:</span> {hoveredData.ma20 ?? '-'}</span>
                                        <span><span style={{ color: COLORS.ma60 }}>60:</span> {hoveredData.ma60 ?? '-'}</span>
                                        <span><span style={{ color: COLORS.ma120 }}>120:</span> {hoveredData.ma120 ?? '-'}</span>
                                    </div>
                                </div>
                                <div className="col-span-2">
                                    <div className="text-slate-500 text-xs mb-1">Volume MAs:</div>
                                    <div className="flex gap-3 text-xs">
                                        <span><span style={{ color: COLORS.ma5 }}>5:</span> {hoveredData.vol_ma5 ? formatVolume(hoveredData.vol_ma5) : '-'}</span>
                                        <span><span style={{ color: COLORS.ma20 }}>20:</span> {hoveredData.vol_ma20 ? formatVolume(hoveredData.vol_ma20) : '-'}</span>
                                        <span><span style={{ color: COLORS.ma60 }}>60:</span> {hoveredData.vol_ma60 ? formatVolume(hoveredData.vol_ma60) : '-'}</span>
                                        <span><span style={{ color: COLORS.ma120 }}>120:</span> {hoveredData.vol_ma120 ? formatVolume(hoveredData.vol_ma120) : '-'}</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">Move your mouse over the chart to see details</p>
                        )}
                    </div>

                    {/* News panel */}
                    <div className="flex-1 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 min-h-[200px] max-h-[200px] overflow-y-auto">
                        <h4 className="text-sm text-slate-400 mb-2">
                            {selectedDate ? `📰 News for ${selectedDate}` : '📰 Click a candle to see news'}
                        </h4>
                        {loadingNews ? (
                            <p className="text-slate-500 text-sm">Loading news...</p>
                        ) : selectedNews.length > 0 ? (
                            <div className="space-y-2">
                                {selectedNews.map((n, i) => (
                                    <div key={i} className="p-2 bg-slate-800/50 rounded-lg">
                                        <a href={n.url || '#'} target="_blank" rel="noopener noreferrer"
                                            className="text-sm text-blue-400 hover:text-blue-300 line-clamp-2">
                                            {n.title}
                                        </a>
                                        {n.summary && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{n.summary}</p>}
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
