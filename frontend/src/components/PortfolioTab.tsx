"use client";

import React, { useState, useEffect } from 'react';
import PortfolioChart from './PortfolioChart';

const API_BASE = "http://localhost:8000/api/portfolio";

export default function PortfolioTab() {
    const [categories, setCategories] = useState<any[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<any>(null);
    const [stocks, setStocks] = useState<string[]>([]);
    const [analysisData, setAnalysisData] = useState<any>(null);
    const [timeframe, setTimeframe] = useState<string>("6mo");
    const [loading, setLoading] = useState(false);

    // Inputs
    const [newCatName, setNewCatName] = useState("");
    const [newTicker, setNewTicker] = useState("");

    // Fetch Categories on Load
    useEffect(() => {
        fetchCategories();
    }, []);

    // Fetch Stocks when Category selected
    useEffect(() => {
        if (selectedCategory) {
            fetchStocks(selectedCategory.id);
            setAnalysisData(null); // Reset chart
        }
    }, [selectedCategory]);

    // Fetch Analysis when stocks or timeframe changes
    useEffect(() => {
        if (selectedCategory && stocks.length > 0) {
            runAnalysis();
        }
    }, [stocks, timeframe]);

    const fetchCategories = async () => {
        try {
            const res = await fetch(`${API_BASE}/categories`);
            const data = await res.json();
            setCategories(data);
        } catch (err) {
            console.error("Failed to fetch categories", err);
        }
    };

    const createCategory = async () => {
        if (!newCatName) return;
        try {
            const res = await fetch(`${API_BASE}/categories`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newCatName })
            });
            const data = await res.json();
            if (res.ok) {
                setNewCatName("");
                fetchCategories();
            } else {
                alert(data.detail || "Error creating category");
            }
        } catch (err) {
            console.error(err);
        }
    };

    const deleteCategory = async (id: number) => {
        if (!confirm("Delete this category?")) return;
        await fetch(`${API_BASE}/categories/${id}`, { method: "DELETE" });
        fetchCategories();
        if (selectedCategory?.id === id) {
            setSelectedCategory(null);
            setStocks([]);
            setAnalysisData(null);
        }
    };

    const fetchStocks = async (catId: number) => {
        const res = await fetch(`${API_BASE}/categories/${catId}/stocks`);
        const data = await res.json();
        setStocks(data.stocks || []);
    };

    const addStock = async () => {
        if (!newTicker || !selectedCategory) return;
        try {
            const res = await fetch(`${API_BASE}/categories/${selectedCategory.id}/stocks`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ticker: newTicker })
            });

            if (res.ok) {
                setNewTicker("");
                fetchStocks(selectedCategory.id);
            } else {
                const data = await res.json();
                alert(data.message || "Error adding stock");
            }
        } catch (err) {
            console.error(err);
        }
    };

    const removeStock = async (ticker: string) => {
        if (!selectedCategory) return;
        await fetch(`${API_BASE}/categories/${selectedCategory.id}/stocks/${ticker}`, {
            method: "DELETE"
        });
        fetchStocks(selectedCategory.id);
    };

    const runAnalysis = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/analysis`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    category_id: selectedCategory.id,
                    period: timeframe
                })
            });
            const result = await res.json();
            if (result.success) {
                setAnalysisData(result.data);
            } else {
                console.error(result.error);
            }
        } catch (err) {
            console.error("Analysis failed", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-gray-100 text-black">
            {/* Sidebar: Categories */}
            <div className="w-1/4 bg-white shadow-lg p-4 flex flex-col">
                <h2 className="text-xl font-bold mb-4">My Portfolios</h2>

                <div className="flex gap-2 mb-4">
                    <input
                        className="border p-2 rounded flex-1 text-sm bg-gray-50 text-black"
                        placeholder="New Category..."
                        value={newCatName}
                        onChange={e => setNewCatName(e.target.value)}
                    />
                    <button
                        onClick={createCategory}
                        className="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
                    >
                        Add
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {categories.map(cat => (
                        <div
                            key={cat.id}
                            onClick={() => setSelectedCategory(cat)}
                            className={`p-3 border-b cursor-pointer flex justify-between items-center hover:bg-gray-50 ${selectedCategory?.id === cat.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''}`}
                        >
                            <span className="font-medium">{cat.name}</span>
                            <button
                                onClick={(e) => { e.stopPropagation(); deleteCategory(cat.id); }}
                                className="text-red-400 hover:text-red-600 px-2"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 overflow-y-auto">
                {selectedCategory ? (
                    <>
                        <div className="flex justify-between items-center mb-6">
                            <h1 className="text-2xl font-bold">{selectedCategory.name} Analysis</h1>

                            <div className="flex gap-2">
                                {["5D", "1mo", "3mo", "6mo", "1y", "3y", "5y"].map(tf => (
                                    <button
                                        key={tf}
                                        onClick={() => setTimeframe(tf)}
                                        className={`px-3 py-1 rounded border ${timeframe === tf ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
                                    >
                                        {tf.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Stock Management */}
                        <div className="bg-white p-4 rounded shadow mb-6">
                            <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase">Portfolio Constituents</h3>
                            <div className="flex flex-wrap gap-2 mb-3">
                                {stocks.map(ticker => (
                                    <span key={ticker} className="bg-gray-100 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                                        {ticker}
                                        <button onClick={() => removeStock(ticker)} className="text-gray-500 hover:text-red-500">×</button>
                                    </span>
                                ))}
                                {stocks.length === 0 && <span className="text-gray-400 text-sm">No stocks added yet.</span>}
                            </div>

                            <div className="flex gap-2 max-w-sm">
                                <input
                                    className="border p-2 rounded flex-1 text-sm bg-gray-50 text-black"
                                    placeholder="Add Ticker (e.g. NVDA)"
                                    value={newTicker}
                                    onChange={e => setNewTicker(e.target.value.toUpperCase())}
                                    onKeyDown={e => e.key === 'Enter' && addStock()}
                                />
                                <button
                                    onClick={addStock}
                                    className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
                                >
                                    Add Stock
                                </button>
                            </div>
                        </div>

                        {/* Analysis Chart */}
                        {loading ? (
                            <div className="h-64 flex items-center justify-center text-gray-500">
                                Loading Analysis Data...
                            </div>
                        ) : analysisData ? (
                            <PortfolioChart data={analysisData} />
                        ) : (
                            <div className="h-64 flex items-center justify-center text-gray-400 bg-gray-50 rounded border border-dashed">
                                Add stocks to visualize performance
                            </div>
                        )}

                        {/* Stats Summary */}
                        {analysisData && (
                            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-white p-4 rounded shadow border-t-4 border-black">
                                    <div className="text-gray-500 text-sm">Category Index Return</div>
                                    <div className={`text-2xl font-bold ${analysisData.index.final >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {analysisData.index.final > 0 ? '+' : ''}{analysisData.index.final}%
                                    </div>
                                </div>
                                {/* Top Performer */}
                                <div className="bg-white p-4 rounded shadow border-t-4 border-green-500">
                                    <div className="text-gray-500 text-sm">Top Performer</div>
                                    <div className="text-xl font-bold">
                                        {Object.entries(analysisData.stocks).sort(([, a]: any, [, b]: any) => b.final - a.final)[0]?.[0]}
                                    </div>
                                </div>
                                {/* Worst Performer */}
                                <div className="bg-white p-4 rounded shadow border-t-4 border-red-500">
                                    <div className="text-gray-500 text-sm">Worst Performer</div>
                                    <div className="text-xl font-bold">
                                        {Object.entries(analysisData.stocks).sort(([, a]: any, [, b]: any) => a.final - b.final)[0]?.[0]}
                                    </div>
                                </div>
                            </div>
                        )}

                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <p className="text-lg">Select or create a portfolio category to begin</p>
                    </div>
                )}
            </div>
        </div>
    );
}
