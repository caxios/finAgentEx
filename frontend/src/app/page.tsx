'use client';

import { useState } from 'react';
import CustomCandlestickChart from '@/components/CustomCandlestickChart';
import FundamentalsPanel from '@/components/FundamentalsPanel';

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
  const [tickerInput, setTickerInput] = useState('');
  const [activeTicker, setActiveTicker] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [mainTab, setMainTab] = useState<'chart' | 'fundamentals'>('chart');

  // Handle ticker search - just show chart
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tickerInput.trim()) return;
    setActiveTicker(tickerInput.toUpperCase());
    setResult(null); // Clear previous analysis
    setError('');
  };

  // Handle AI Analysis button click
  const handleAnalyze = async () => {
    if (!activeTicker) return;

    setAnalyzing(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: activeTicker }),
      });

      if (!response.ok) throw new Error('Failed to analyze stock');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setAnalyzing(false);
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'BUY': return 'text-emerald-400';
      case 'SELL': return 'text-rose-400';
      default: return 'text-amber-400';
    }
  };

  const getDecisionBg = (decision: string) => {
    switch (decision) {
      case 'BUY': return 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30';
      case 'SELL': return 'from-rose-500/20 to-rose-600/10 border-rose-500/30';
      default: return 'from-amber-500/20 to-amber-600/10 border-amber-500/30';
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
            Stock Analysis Agent
          </h1>
          <p className="text-slate-400">Multi-Agent AI System for Stock Analysis</p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="max-w-xl mx-auto mb-8">
          <div className="relative">
            <input
              type="text"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
              placeholder="Enter stock ticker (e.g., AAPL, NVDA)"
              className="w-full px-6 py-4 bg-slate-800/50 border border-slate-700/50 rounded-2xl text-white text-lg placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all backdrop-blur-sm"
            />
            <button
              type="submit"
              disabled={!tickerInput.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
            >
              View Chart
            </button>
          </div>
        </form>

        {/* Content Section */}
        {activeTicker && (
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Main Tab Selector */}
            <div className="flex justify-center gap-2 mb-4">
              <button
                onClick={() => setMainTab('chart')}
                className={`px-6 py-2.5 rounded-xl font-medium transition-all ${mainTab === 'chart'
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                    : 'bg-slate-800/50 text-slate-400 hover:text-white border border-slate-700/50'
                  }`}
              >
                📈 Chart & Analysis
              </button>
              <button
                onClick={() => setMainTab('fundamentals')}
                className={`px-6 py-2.5 rounded-xl font-medium transition-all ${mainTab === 'fundamentals'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
                    : 'bg-slate-800/50 text-slate-400 hover:text-white border border-slate-700/50'
                  }`}
              >
                📊 Fundamentals
              </button>
            </div>

            {/* Chart Tab Content */}
            {mainTab === 'chart' && (
              <>
                <CustomCandlestickChart ticker={activeTicker} period="1y" />

                {/* AI Analysis Button */}
                {!result && (
                  <div className="flex justify-center">
                    <button
                      onClick={handleAnalyze}
                      disabled={analyzing}
                      className="px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold text-lg rounded-2xl hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/25 flex items-center gap-3"
                    >
                      {analyzing ? (
                        <>
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          AI Analyzing...
                        </>
                      ) : (
                        <>🤖 Run AI Analysis</>
                      )}
                    </button>
                  </div>
                )}

                {/* Error */}
                {error && (
                  <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-center">
                    {error}
                  </div>
                )}

                {/* Analysis Results */}
                {result && (
                  <div className="space-y-4 animate-fade-in">
                    {/* Decision Card */}
                    <div className={`p-6 rounded-2xl bg-gradient-to-br ${getDecisionBg(result.decision)} border backdrop-blur-sm`}>
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <span className="text-slate-400 text-sm uppercase tracking-wider">AI Analysis Result</span>
                          <h2 className="text-2xl font-bold text-white">{result.ticker}</h2>
                        </div>
                        <div className="text-right">
                          <div className={`text-4xl font-bold ${getDecisionColor(result.decision)}`}>{result.decision}</div>
                          <div className="text-slate-400">Confidence: {(result.confidence * 100).toFixed(0)}%</div>
                        </div>
                      </div>
                      <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden mb-4">
                        <div
                          className={`h-full rounded-full transition-all duration-1000 ${result.decision === 'BUY' ? 'bg-emerald-400' :
                            result.decision === 'SELL' ? 'bg-rose-400' : 'bg-amber-400'
                            }`}
                          style={{ width: `${result.confidence * 100}%` }}
                        />
                      </div>
                      <div className="text-sm text-slate-400">Timeframe: {result.timeframe}</div>
                    </div>

                    {/* Reasoning */}
                    <div className="p-5 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
                      <h3 className="text-md font-semibold text-white mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-400 rounded-full" />Reasoning
                      </h3>
                      <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{result.reasoning}</p>
                    </div>

                    {/* Risk */}
                    <div className="p-5 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
                      <h3 className="text-md font-semibold text-white mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-rose-400 rounded-full" />Risk Factors
                      </h3>
                      <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{result.risk_factors}</p>
                    </div>

                    {/* Analyze again button */}
                    <div className="flex justify-center">
                      <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        className="px-6 py-3 bg-slate-700/50 border border-slate-600/50 text-slate-300 rounded-xl hover:bg-slate-700 transition-all"
                      >
                        🔄 Re-analyze
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Fundamentals Tab Content */}
            {mainTab === 'fundamentals' && (
              <FundamentalsPanel ticker={activeTicker} />
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-slate-600 text-sm">
          Powered by Multi-Agent AI System • 6 Specialized Analysis Agents
        </div>
      </div>
    </main>
  );
}
