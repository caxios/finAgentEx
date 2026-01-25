"use client";

import React, { useState, useEffect } from 'react';

interface NewsItem {
    id: string;
    title: string;
    summary: string;
    pubDate: string;
    url: string | null;
    tickers: string[];
}

interface PortfolioNewsProps {
    categoryId: number;
}

export default function PortfolioNews({ categoryId }: PortfolioNewsProps) {
    const [news, setNews] = useState<NewsItem[]>([]); // Accumulates all fetched news
    const [loading, setLoading] = useState(false);
    const [selectedDate, setSelectedDate] = useState<string>('');

    const mergeNews = (newItems: NewsItem[]) => {
        setNews(prev => {
            const existingIds = new Set(prev.map(n => n.id));
            const unique = newItems.filter(n => !existingIds.has(n.id));
            if (unique.length === 0) return prev;
            // Sort by date desc
            return [...prev, ...unique].sort((a, b) => b.pubDate.localeCompare(a.pubDate));
        });
    };

    const fetchLatestNews = async () => {
        setLoading(true);
        try {
            // Default latest fetch (replaces current state)
            const res = await fetch(`http://localhost:8000/api/portfolio/categories/${categoryId}/news?limit=100`);
            const data = await res.json();
            if (data.news) {
                setNews(data.news);
            }
        } catch (err) {
            console.error("Failed to fetch news", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchDateNews = async (date: string) => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/portfolio/categories/${categoryId}/news?limit=100&date=${date}`);
            const data = await res.json();
            if (data.news) {
                mergeNews(data.news);
            }
        } catch (err) {
            console.error("Failed to fetch date news", err);
        } finally {
            setLoading(false);
        }
    };

    // Initial Load (Latest News)
    useEffect(() => {
        fetchLatestNews();
    }, [categoryId]);

    // Fetch when Date Selected
    useEffect(() => {
        if (selectedDate) {
            fetchDateNews(selectedDate);
        }
    }, [selectedDate, categoryId]);

    // View Filter: If date selected, show only that date. Else show all history.
    const displayedNews = selectedDate
        ? news.filter(n => n.pubDate === selectedDate)
        : news;

    return (
        <div className="mt-8 bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
            {/* Control Bar */}
            <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    📰 Portfolio News
                    <span className="text-xs font-normal text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                        {displayedNews.length} / {news.length}
                    </span>
                </h3>

                <div className="flex gap-2 items-center">
                    <span className="text-sm text-gray-500">Filter by Date:</span>
                    {/* Date Picker */}
                    <input
                        type="date"
                        className="border rounded px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />

                    {selectedDate && (
                        <button
                            onClick={() => setSelectedDate('')}
                            className="text-xs text-red-500 hover:text-red-700 underline"
                        >
                            Clear
                        </button>
                    )}

                    <div className="bg-gray-300 w-px h-6 mx-2"></div>

                    {/* Refresh Button - Resets to Latest */}
                    <button
                        onClick={() => { setSelectedDate(''); fetchLatestNews(); }}
                        disabled={loading}
                        className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1 transition-colors"
                    >
                        {loading ? (
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                        ) : (
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                        )}
                        Reset
                    </button>
                </div>
            </div>

            {/* News Card Component */}
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto bg-white">
                {loading && displayedNews.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">Loading portfolio news...</div>
                ) : displayedNews.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        {selectedDate
                            ? `No news found for ${selectedDate}.`
                            : "No news articles found."}
                    </div>
                ) : (
                    displayedNews.map(item => (
                        <article key={item.id} className="p-4 hover:bg-blue-50/30 transition-colors">
                            {/* Header */}
                            <div className="mb-2">
                                <a
                                    href={item.url || '#'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-base font-bold text-gray-900 hover:text-blue-600 leading-tight block mb-1"
                                >
                                    {item.title}
                                </a>
                            </div>

                            {/* Meta Info Row */}
                            <div className="flex items-center flex-wrap gap-2 mb-2">
                                <span className="text-xs text-gray-400 font-mono">{item.pubDate}</span>

                                {/* Ticker Badges */}
                                <div className="flex gap-1">
                                    {item.tickers.map(ticker => (
                                        <span
                                            key={ticker}
                                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-500 text-white shadow-sm"
                                        >
                                            {ticker}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Body */}
                            <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                                {item.summary}
                            </p>
                        </article>
                    ))
                )}
            </div>
        </div>
    );
}
