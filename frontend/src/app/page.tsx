'use client';

import { useState } from 'react';
import CandlestickChart from '@/components/CandlestickChart';

interface AnalysisResult {
  ticker: string;
  decision: string;
  confidence: number;
  timeframe: string;
  reasoning: string;
  risk_factors: string;
  success: boolean;
  error?: string;
}

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: ticker.toUpperCase() }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze stock');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return 'text-emerald-400';
      case 'SELL':
        return 'text-rose-400';
      default:
        return 'text-amber-400';
    }
  };

  const getDecisionBg = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30';
      case 'SELL':
        return 'from-rose-500/20 to-rose-600/10 border-rose-500/30';
      default:
        return 'from-amber-500/20 to-amber-600/10 border-amber-500/30';
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
            Stock Analysis Agent
          </h1>
          <p className="text-slate-400 text-lg">
            Multi-Agent AI System for Stock Analysis
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleAnalyze} className="max-w-xl mx-auto mb-12">
          <div className="relative">
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Enter stock ticker (e.g., AAPL, NVDA)"
              className="w-full px-6 py-4 bg-slate-800/50 border border-slate-700/50 rounded-2xl text-white text-lg placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all backdrop-blur-sm"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !ticker.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/25"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                'Analyze'
              )}
            </button>
          </div>
        </form>

        {/* Error Message */}
        {error && (
          <div className="max-w-2xl mx-auto mb-8 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-center">
            {error}
          </div>
        )}

        {/* Loading Animation */}
        {loading && (
          <div className="max-w-2xl mx-auto text-center py-12">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-slate-800/50 rounded-full border border-slate-700/50">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-slate-400">AI Agents are analyzing {ticker}...</span>
            </div>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            {/* Decision Card */}
            <div className={`p-8 rounded-3xl bg-gradient-to-br ${getDecisionBg(result.decision)} border backdrop-blur-sm`}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <span className="text-slate-400 text-sm uppercase tracking-wider">Analysis Result</span>
                  <h2 className="text-3xl font-bold text-white">{result.ticker}</h2>
                </div>
                <div className="text-right">
                  <div className={`text-5xl font-bold ${getDecisionColor(result.decision)}`}>
                    {result.decision}
                  </div>
                  <div className="text-slate-400 mt-1">
                    Confidence: {(result.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mb-6">
                <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${result.decision === 'BUY' ? 'bg-emerald-400' :
                        result.decision === 'SELL' ? 'bg-rose-400' : 'bg-amber-400'
                      }`}
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div className="p-4 bg-slate-900/30 rounded-xl">
                  <span className="text-slate-500">Timeframe</span>
                  <p className="text-white font-medium">{result.timeframe}</p>
                </div>
                <div className="p-4 bg-slate-900/30 rounded-xl">
                  <span className="text-slate-500">Status</span>
                  <p className={result.success ? 'text-emerald-400' : 'text-amber-400'}>
                    {result.success ? '✓ Analysis Complete' : '⚠ Partial Analysis'}
                  </p>
                </div>
              </div>
            </div>

            {/* Reasoning Card */}
            <div className="p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-400 rounded-full" />
                Analysis Reasoning
              </h3>
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {result.reasoning}
              </p>
            </div>

            {/* Risk Factors Card */}
            <div className="p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-rose-400 rounded-full" />
                Risk Factors
              </h3>
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {result.risk_factors}
              </p>
            </div>

            {/* Interactive Candlestick Chart */}
            <CandlestickChart ticker={result.ticker} period="6mo" />
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-16 text-slate-600 text-sm">
          Powered by Multi-Agent AI System • 6 Specialized Analysis Agents
        </div>
      </div>
    </main>
  );
}
