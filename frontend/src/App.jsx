import React, { useState, useEffect, useRef } from 'react';
import { 
  TrendingUp, 
  MessageSquare, 
  Cpu, 
  Briefcase, 
  Search, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle,
  Activity,
  Layers,
  Award,
  BookOpen,
  PieChart as PieIcon,
  Plus,
  Trash2,
  ExternalLink,
  TrendingDown,
  Info,
  Calendar,
  FileSpreadsheet
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart
} from 'recharts';

// Simple Markdown to HTML parser for PM recommendation text
const renderMarkdown = (mdText) => {
  if (!mdText) return null;
  const lines = mdText.split('\n');
  return lines.map((line, idx) => {
    // Headings
    if (line.startsWith('# ')) {
      return <h1 key={idx} className="text-2xl font-bold mt-8 mb-4 text-white border-b border-slate-800 pb-2">{line.substring(2)}</h1>;
    }
    if (line.startsWith('## ')) {
      return <h2 key={idx} className="text-xl font-semibold mt-6 mb-3 text-indigo-400">{line.substring(3)}</h2>;
    }
    if (line.startsWith('### ')) {
      return <h3 key={idx} className="text-lg font-medium mt-4 mb-2 text-indigo-400">{line.substring(4)}</h3>;
    }
    // Bullet points
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const isPositive = line.includes('Positive') || line.includes('bullish');
      const isNegative = line.includes('Negative') || line.includes('bearish');
      const isNeutral = line.includes('Neutral') || line.includes('neutral');
      let colorClass = "text-slate-300";
      if (isPositive) colorClass = "text-emerald-400 font-medium";
      if (isNegative) colorClass = "text-rose-400 font-medium";
      if (isNeutral) colorClass = "text-amber-400";
      
      const cleanLine = line.replace(/^[-*]\s+(\*\*Positive\*\*|\*\*Negative\*\*|\*\*Neutral\*\*):?/, '');
      return (
        <li key={idx} className={`ml-4 list-disc mb-1.5 ${colorClass}`}>
          {isPositive && <span className="font-bold mr-1">Positive:</span>}
          {isNegative && <span className="font-bold mr-1">Negative:</span>}
          {isNeutral && <span className="font-bold mr-1">Neutral:</span>}
          {cleanLine}
        </li>
      );
    }
    // Divider
    if (line.trim() === '---') {
      return <hr key={idx} className="border-slate-800 my-6" />;
    }
    // Final Advice highlight
    if (line.startsWith('**Final Advice**:')) {
      const advice = line.split('`')[1] || 'HOLD';
      let badgeColor = "bg-warning";
      let textCol = "text-amber-400";
      if (advice.includes('BUY') || advice.includes('ACCUMULATE')) {
        badgeColor = "badge-success";
        textCol = "text-emerald-400";
      } else if (advice.includes('SELL') || advice.includes('REDUCE')) {
        badgeColor = "badge-danger";
        textCol = "text-rose-400";
      }
      return (
        <div key={idx} className="flex items-center gap-3 my-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <span className="text-slate-400 font-medium text-sm">System Recommendation:</span>
          <span className={`badge ${badgeColor} text-xs font-bold tracking-wider uppercase`}>
            {advice}
          </span>
        </div>
      );
    }
    // Normal lines
    if (line.trim() === '') return <div key={idx} className="h-2" />;
    return <p key={idx} className="text-slate-300 mb-2 leading-relaxed text-sm">{line}</p>;
  });
};

// Helper function to diagnose and format pipeline execution errors
const parsePipelineError = (err, responseStatus, apiUrl) => {
  const errMsg = (err && err.message) ? err.message : String(err || '');
  const isFailedToFetch = errMsg.toLowerCase().includes('failed to fetch') || 
                          errMsg.toLowerCase().includes('networkerror') ||
                          err?.name === 'TypeError';
  
  if (isFailedToFetch) {
    const isLocalhost = apiUrl.includes('127.0.0.1') || apiUrl.includes('localhost');
    return {
      type: 'NETWORK_ERROR',
      badge: 'Server Unreachable / CORS',
      title: 'Unable to Connect to Backend API',
      summary: `The frontend could not reach the backend server at "${apiUrl}".`,
      causes: [
        isLocalhost 
          ? 'Connecting to local server (127.0.0.1). If deployed online (Vercel/Netlify), set the VITE_API_URL environment variable to your production backend URL.'
          : 'The backend service is currently offline or unreachable.',
        'If hosted on a free cloud provider (e.g. Render), the server spins down after 15 minutes of inactivity and takes ~60 seconds to boot up on request.',
        'Browser security or CORS restrictions blocked the cross-origin API request.'
      ],
      detail: errMsg || 'TypeError: Failed to fetch',
      apiUrl: apiUrl,
      status: responseStatus || 'Network Failure'
    };
  }

  if (responseStatus === 502 || responseStatus === 504 || errMsg.includes('502') || errMsg.includes('504')) {
    return {
      type: 'COLD_START',
      badge: 'Free Tier Cold Start (502/504)',
      title: 'Backend Container Waking Up',
      summary: 'The backend server timed out while starting up or processing the request.',
      causes: [
        'Free cloud hosting (e.g., Render Free Plan) puts backend containers to sleep after 15 minutes of inactivity.',
        'Initial container spin-up and dependency loading can take between 50 to 90 seconds.',
        'Heavy ML calculations (KNN Imputation & Random Forest) timed out on the host gateway.'
      ],
      detail: errMsg || `HTTP ${responseStatus} Gateway Timeout`,
      apiUrl: apiUrl,
      status: responseStatus || 502
    };
  }

  if (responseStatus === 500 || errMsg.includes('500')) {
    return {
      type: 'SERVER_ERROR',
      badge: 'Backend Exception (500)',
      title: 'Model Pipeline Execution Error',
      summary: 'The backend server encountered an unhandled error during multi-agent analysis.',
      causes: [
        'Historical data source (Yahoo Finance) or news scrapers were rate-limited or failed for ticker.',
        'Memory limit exceeded (512MB RAM cap on free tier hosting).',
        'Model training error during feature matrix alignment.'
      ],
      detail: errMsg,
      apiUrl: apiUrl,
      status: 500
    };
  }

  return {
    type: 'GENERIC_ERROR',
    badge: 'Pipeline Error',
    title: 'Pipeline Execution Failed',
    summary: errMsg || 'An unexpected error occurred while executing the stock analysis pipeline.',
    causes: [
      'The requested stock ticker might be invalid or unlisted.',
      'One or more social scraper agents failed to complete within the request timeout.',
      'Check browser console (F12) for detailed network trace.'
    ],
    detail: errMsg,
    apiUrl: apiUrl,
    status: responseStatus || 'Error'
  };
};

const DEFAULT_WATCHLIST = [
  { ticker: 'RELIANCE', rec: 'BUY' },
  { ticker: 'TCS', rec: 'HOLD' },
  { ticker: 'INFY', rec: 'HOLD' }
];

const SUGGESTIONS = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'TATAMOTORS'];

function App() {
  const [ticker, setTicker] = useState('RELIANCE');
  const [modelType, setModelType] = useState('Random Forest');
  const [startDate, setStartDate] = useState('2015-01-01');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('forecast'); // forecast, oscillators, sentiment, backtest
  const [corpusPlatformFilter, setCorpusPlatformFilter] = useState('all'); // all, Reddit, Twitter, Telegram, News
  
  // Watchlist state & cache
  const [watchlist, setWatchlist] = useState([]);
  const [cache, setCache] = useState({});

  // Health check & diagnostic state
  const [healthCheckState, setHealthCheckState] = useState({ status: 'idle', message: '' });
  const [showTechDetails, setShowTechDetails] = useState(false);

  const terminalEndRef = useRef(null);

  // Test connection to backend health endpoint
  const testBackendHealth = async () => {
    setHealthCheckState({ status: 'checking', message: 'Pinging backend API endpoint...' });
    const rawUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const API_BASE_URL = rawUrl.replace(/\/+$/, '');
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
      if (res.ok) {
        const json = await res.json();
        setHealthCheckState({ 
          status: 'online', 
          message: `Backend Online (${json.status || 'healthy'}). Server is ready!` 
        });
      } else {
        setHealthCheckState({ 
          status: 'offline', 
          message: `Backend returned status ${res.status}. Container may be booting.` 
        });
      }
    } catch (err) {
      setHealthCheckState({ 
        status: 'offline', 
        message: `Unreachable: ${err.message}. Check API URL (${API_BASE_URL}).` 
      });
    }
  };

  // Initialize watchlist from Local Storage
  useEffect(() => {
    const saved = localStorage.getItem('sentiscrapper_watchlist');
    if (saved) {
      try {
        setWatchlist(JSON.parse(saved));
      } catch (e) {
        setWatchlist(DEFAULT_WATCHLIST);
      }
    } else {
      setWatchlist(DEFAULT_WATCHLIST);
      localStorage.setItem('sentiscrapper_watchlist', JSON.stringify(DEFAULT_WATCHLIST));
    }
  }, []);

  // Save Watchlist to Local Storage
  const saveWatchlist = (newList) => {
    setWatchlist(newList);
    localStorage.setItem('sentiscrapper_watchlist', JSON.stringify(newList));
  };

  // Scroll terminal logs to bottom on update
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [data?.agent_logs, isLoading]);

  const handleAnalyze = async (e, customTicker = null) => {
    if (e) e.preventDefault();
    
    const targetTicker = (customTicker || ticker).trim().toUpperCase();
    if (!targetTicker) return;

    // Check Cache first if not forcing reload
    if (!e && cache[targetTicker]) {
      setData(cache[targetTicker]);
      setTicker(targetTicker);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setData(null);
    setTicker(targetTicker);

    const rawUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const API_BASE_URL = rawUrl.replace(/\/+$/, '');
    let responseStatus = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: targetTicker,
          model_type: modelType,
          start_date: startDate
        }),
      });

      responseStatus = response.status;

      if (!response.ok) {
        let errorDetail = '';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || response.statusText;
        } catch {
          const rawText = await response.text();
          errorDetail = rawText.slice(0, 300) || `Server responded with HTTP status ${response.status}`;
        }
        throw new Error(errorDetail || `Analysis request failed with status ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      
      // Update Cache
      setCache(prev => ({ ...prev, [targetTicker]: result }));

      // Add/Update Watchlist item recommendations dynamically
      const recMatch = result.recommendation.match(/\*\*Final Advice\*\*: `([^`]+)`/);
      const advice = recMatch ? recMatch[1] : 'HOLD';
      
      const exists = watchlist.some(w => w.ticker === targetTicker);
      if (exists) {
        saveWatchlist(watchlist.map(w => w.ticker === targetTicker ? { ...w, rec: advice } : w));
      } else {
        saveWatchlist([...watchlist, { ticker: targetTicker, rec: advice }]);
      }

    } catch (err) {
      console.error('Analysis Pipeline Error:', err);
      const structuredError = parsePipelineError(err, responseStatus, API_BASE_URL);
      setError(structuredError);
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle Watchlist state
  const handleAddToWatchlist = () => {
    if (!data) return;
    const currentTicker = data.ticker.toUpperCase();
    const exists = watchlist.some(w => w.ticker === currentTicker);
    
    if (exists) {
      saveWatchlist(watchlist.filter(w => w.ticker !== currentTicker));
    } else {
      const recMatch = data.recommendation.match(/\*\*Final Advice\*\*: `([^`]+)`/);
      const advice = recMatch ? recMatch[1] : 'HOLD';
      saveWatchlist([...watchlist, { ticker: currentTicker, rec: advice }]);
    }
  };

  const [isExporting, setIsExporting] = useState(false);

  const handleExportExcel = async () => {
    if (!data) return;
    setIsExporting(true);
    try {
      const rawUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const API_BASE_URL = rawUrl.replace(/\/+$/, '');
      const response = await fetch(`${API_BASE_URL}/api/export/excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to compile Excel workbook.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SentiScrapper_Financial_Model_${data.ticker}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
      alert('Error downloading Excel report: ' + err.message);
    } finally {
      setIsExporting(false);
    }
  };

  const handleRemoveFromWatchlist = (e, tickerToRemove) => {
    e.stopPropagation();
    saveWatchlist(watchlist.filter(w => w.ticker !== tickerToRemove));
  };

  // Compile historical + predicted data for plotting
  const getChartData = () => {
    if (!data) return [];
    
    // Convert date fields
    const hist = data.historical_data.map(d => ({
      ...d,
      displayDate: d.Date.split('T')[0],
      price: d.Close,
      sentiment: d.Weighted_Sentiment,
      rsiVal: d.RSI,
      macdVal: d.MACD,
      type: 'historical'
    }));

    // Predictions
    const forecast = data.forecast_data.map((d, index) => ({
      Date: d.Date,
      displayDate: d.Date,
      forecastPrice: d.Predicted_Close,
      type: 'forecast'
    }));

    return [...hist, ...forecast];
  };

  // Compile backtesting chart data
  const getBacktestData = () => {
    if (!data || !data.metrics.test_actual) return [];
    return data.metrics.test_actual.map((val, idx) => ({
      index: idx,
      actual: val,
      predicted: data.metrics.test_predicted[idx]
    }));
  };

  // Platform breakdown calculation
  const getPlatformBreakdown = () => {
    if (!data || !data.sentiment_details) return [];
    const platforms = ['Reddit', 'Twitter', 'Telegram', 'News'];
    
    return platforms.map(p => {
      const items = data.sentiment_details.filter(item => {
        const source = (item.Source || 'Unknown').toLowerCase();
        if (p === 'News') {
          return source.includes('moneycontrol') || source.includes('yfinance') || source.includes('news') || source.includes('yahoo');
        }
        return source.includes(p.toLowerCase());
      });
      
      const count = items.length;
      const avgCompound = count > 0 
        ? items.reduce((acc, curr) => acc + curr.compound, 0) / count 
        : 0.0;
        
      return {
        name: p,
        count,
        avgCompound,
        sentiment: avgCompound > 0.15 ? 'BULLISH' : avgCompound < -0.15 ? 'BEARISH' : 'NEUTRAL'
      };
    });
  };

  // Filter Corpus items by selected platform
  const getFilteredCorpus = () => {
    if (!data) return [];
    const items = data.sentiment_details || [];
    if (corpusPlatformFilter === 'all') return items;
    
    return items.filter(item => {
      const source = (item.Source || 'Unknown').toLowerCase();
      if (corpusPlatformFilter === 'News') {
        return source.includes('moneycontrol') || source.includes('yfinance') || source.includes('news') || source.includes('yahoo');
      }
      return source.includes(corpusPlatformFilter.toLowerCase());
    });
  };

  const sentimentDetails = getFilteredCorpus();
  const chartData = getChartData();
  const backtestData = getBacktestData();
  const platformBreakdown = getPlatformBreakdown();
  
  // Technical Signals Analysis
  const lastHistItem = data?.historical_data?.[data.historical_data.length - 1];
  const lastRSI = lastHistItem?.RSI ?? 50;
  const lastMACD = lastHistItem?.MACD ?? 0;
  const lastSentiment = lastHistItem?.Weighted_Sentiment ?? 0;

  const getRSISignal = (val) => {
    if (val > 70) return { label: 'Overbought', class: 'badge-danger' };
    if (val < 30) return { label: 'Oversold', class: 'badge-success' };
    return { label: 'Neutral', class: 'badge-warning' };
  };

  const getMACDSignal = (val) => {
    return val >= 0 
      ? { label: 'Bullish momentum', class: 'badge-success' } 
      : { label: 'Bearish momentum', class: 'badge-danger' };
  };

  const getSentimentSignal = (val) => {
    if (val > 0.15) return { label: 'Bullish', class: 'badge-success' };
    if (val < -0.15) return { label: 'Bearish', class: 'badge-danger' };
    return { label: 'Neutral', class: 'badge-warning' };
  };

  return (
    <div className="pb-12">
      {/* HEADER */}
      <header className="border-b border-slate-800 bg-slate-950/40 backdrop-blur-md sticky top-0 z-50 py-4 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl shadow-glow">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">SentiScrapper <span className="text-indigo-400 font-normal">Analytics</span></h1>
              <p className="text-xs text-slate-400">Multi-Agent Stock Forecasting Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400 bg-slate-900/60 px-4 py-2 rounded-xl border border-slate-800/80">
            <span className="flex items-center gap-1.5"><CheckCircle className="h-3.5 w-3.5 text-emerald-400" /> API Active</span>
            <span className="h-4 w-px bg-slate-800"></span>
            <span>OS: Windows / PyTorch-CUDA Ready</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 mt-8">
        
        {/* WATCHLIST BAR */}
        <section className="mb-8">
          <div className="watchlist-bar">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Briefcase className="h-3.5 w-3.5" /> Watchlist:
            </span>
            <div className="flex gap-2 flex-wrap">
              {watchlist.map((item, idx) => (
                <div 
                  key={idx} 
                  onClick={() => handleAnalyze(null, item.ticker)}
                  className={`watchlist-pill ${ticker.toUpperCase() === item.ticker.toUpperCase() ? 'active' : ''}`}
                >
                  <span className="ticker-name">{item.ticker}</span>
                  <span className={`rec-val ${item.rec.toLowerCase().includes('buy') ? 'buy' : item.rec.toLowerCase().includes('sell') ? 'sell' : 'hold'}`}>
                    {item.rec}
                  </span>
                  <button 
                    onClick={(e) => handleRemoveFromWatchlist(e, item.ticker)} 
                    className="remove-btn" 
                    title="Remove from Watchlist"
                  >
                    ×
                  </button>
                </div>
              ))}
              {watchlist.length === 0 && (
                <span className="text-xs text-slate-500 italic">No tickers in watchlist. Analyze a stock to add it.</span>
              )}
            </div>
          </div>
        </section>

        {/* INPUT CONFIGURATIONS */}
        <section className="glass-panel mb-8">
          <form onSubmit={handleAnalyze} className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Search className="h-3.5 w-3.5" /> Stock Ticker
              </label>
              <input 
                type="text" 
                value={ticker} 
                onChange={(e) => setTicker(e.target.value)}
                placeholder="e.g. RELIANCE, TCS, INFY" 
                className="form-input"
                required
                disabled={isLoading}
              />
              <div className="ticker-suggestions">
                {SUGGESTIONS.map((tag) => (
                  <span 
                    key={tag} 
                    onClick={() => !isLoading && handleAnalyze(null, tag)}
                    className="suggestion-tag"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Cpu className="h-3.5 w-3.5" /> Model Engine
              </label>
              <select 
                value={modelType} 
                onChange={(e) => setModelType(e.target.value)} 
                className="form-select"
                disabled={isLoading}
              >
                <option value="Random Forest">Random Forest (Ensemble Trees)</option>
                <option value="LSTM">Deep LSTM Network (NVIDIA GPU)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" /> Training Start Date
              </label>
              <input 
                type="text" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)} 
                placeholder="YYYY-MM-DD"
                className="form-input"
                disabled={isLoading}
              />
            </div>
            <div className="flex gap-2">
              <button 
                type="submit" 
                disabled={isLoading} 
                className="btn-primary w-full"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    Running Agents...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-5 w-5" />
                    Analyze Stock
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {/* IDLE READY STATE */}
        {!data && !isLoading && !error && (
          <section className="glass-panel text-center py-12 px-6 mb-8 border border-indigo-500/20 bg-slate-900/60 rounded-2xl shadow-xl">
            <div className="mx-auto h-14 w-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-4 shadow-glow">
              <Cpu className="h-7 w-7" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Ready to Run Multi-Agent Analysis</h2>
            <p className="text-sm text-slate-400 max-w-lg mx-auto mb-6 leading-relaxed">
              Select a stock ticker symbol above and click <strong className="text-indigo-300">"Analyze Stock"</strong> to start fetching market data, social sentiment, and running predictive machine learning models.
            </p>
            <div className="flex items-center justify-center gap-6 text-xs text-slate-400 flex-wrap">
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-emerald-400" /> Market Data Miner</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-purple-400" /> Multi-Platform Social Miner</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-amber-400" /> Random Forest / LSTM Engine</span>
            </div>
          </section>
        )}

        {/* LOADING TERMINAL LOGS SCREEN */}
        {isLoading && (
          <section className="glass-panel mb-8">
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <Cpu className="h-5 w-5 text-indigo-400 animate-spin" /> Live Multi-Agent Logs Console
            </h2>
            <div className="terminal-container">
              <div className="terminal-line text-emerald-400">[00:00:01] [System Orchestrator] Triggering stock pipeline run. Spawning sub-agents...</div>
              <div className="terminal-line text-slate-400">[00:00:02] [Data Collection Agent] Searching stock database for ticker symbol: {ticker.toUpperCase()}...</div>
              <div className="terminal-line text-slate-400">[00:00:03] [Data Collection Agent] Requesting historical price points from Yahoo Finance API...</div>
              <div className="terminal-line text-purple-300">[00:00:05] [Sentiment Agent] Querying Social Channels (Reddit, Twitter, Telegram, News)...</div>
              <div className="terminal-line text-amber-400">[00:00:10] [Quant Agent] Initializing model matrices and calculating math formulas...</div>
              <div className="terminal-line text-slate-400">Loading data aggregators, text miners, and time-series model layers...</div>
              <div ref={terminalEndRef}></div>
            </div>
          </section>
        )}

        {/* ENHANCED DIAGNOSTIC ERROR PANEL */}
        {error && (
          <div className="p-6 mb-8 bg-slate-900/90 border border-rose-500/30 rounded-2xl shadow-xl space-y-5 text-slate-200">
            {/* Header section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
              <div className="flex items-start gap-3">
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl">
                  <AlertTriangle className="h-6 w-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg font-bold text-white">{error.title}</h3>
                    <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300">
                      {error.badge}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 mt-1">{error.summary}</p>
                </div>
              </div>
              
              {/* Primary Retry Action */}
              <button
                onClick={(e) => handleAnalyze(e)}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium rounded-xl flex items-center justify-center gap-2 text-sm shadow-md transition-all flex-shrink-0 cursor-pointer"
              >
                <RefreshCw className="h-4 w-4" />
                Retry Analysis
              </button>
            </div>

            {/* Diagnostic Checklist */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
                <Info className="h-4 w-4 text-amber-400" />
                Possible Causes & Recommended Solutions:
              </h4>
              <ul className="space-y-2 text-sm text-slate-300 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                {error.causes.map((cause, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="text-amber-400 font-bold mt-0.5">•</span>
                    <span>{cause}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Real-time Health Check & Tech Details Toggle */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  type="button"
                  onClick={testBackendHealth}
                  disabled={healthCheckState.status === 'checking'}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
                >
                  <Activity className={`h-3.5 w-3.5 text-indigo-400 ${healthCheckState.status === 'checking' ? 'animate-spin' : ''}`} />
                  Test Backend Connection
                </button>

                {healthCheckState.status !== 'idle' && (
                  <span className={`text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${
                    healthCheckState.status === 'online'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : healthCheckState.status === 'checking'
                      ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {healthCheckState.status === 'online' && <CheckCircle className="h-3.5 w-3.5" />}
                    {healthCheckState.status === 'offline' && <AlertTriangle className="h-3.5 w-3.5" />}
                    {healthCheckState.message}
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="text-xs text-slate-400 hover:text-slate-200 underline flex items-center gap-1 cursor-pointer"
              >
                {showTechDetails ? 'Hide technical logs' : 'Show technical details'}
              </button>
            </div>

            {/* Collapsible Technical Details */}
            {showTechDetails && (
              <div className="mt-3 p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono space-y-2 text-slate-400 overflow-x-auto">
                <div><span className="text-slate-500">Target Endpoint:</span> <span className="text-indigo-300">{error.apiUrl}/api/analyze</span></div>
                <div><span className="text-slate-500">HTTP Status Code:</span> <span className="text-amber-300">{String(error.status)}</span></div>
                <div><span className="text-slate-500">Raw Traceback / Message:</span></div>
                <pre className="p-3 bg-slate-900 rounded-lg text-rose-300 whitespace-pre-wrap break-all border border-slate-800/60 font-mono">
                  {error.detail || 'No additional traceback available.'}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* ANALYSIS RESULTS DASHBOARD */}
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* COLUMN 1 & 2: CHARTS & PM RECOMMENDATION */}
            <div className="lg:col-span-2 space-y-8">
              
              {/* RECOMMENDATION BANNER */}
              <div className={`recommendation-banner ${data.recommendation.includes('BUY') ? 'BUY' : data.recommendation.includes('SELL') ? 'SELL' : 'HOLD'}`}>
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    <Briefcase className="h-6 w-6 text-indigo-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">Target Ticker: {data.ticker}</h2>
                    <p className="text-xs text-slate-400">Analysis run using {data.model_type} algorithm</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-wrap">
                  <button 
                    onClick={handleAddToWatchlist}
                    className="btn-primary !py-2 !px-4 !text-xs !bg-slate-900/80 !border !border-slate-800 hover:!border-indigo-500 text-white"
                  >
                    {watchlist.some(w => w.ticker === data.ticker) ? 'Remove Watchlist' : 'Add Watchlist'}
                  </button>
                  <button 
                    onClick={handleExportExcel}
                    disabled={isExporting}
                    className="btn-primary !py-2 !px-4 !text-xs !bg-emerald-600 hover:!bg-emerald-500 !border-none text-white flex items-center gap-1.5 shadow-lg shadow-emerald-900/20"
                  >
                    {isExporting ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        Generating Model...
                      </>
                    ) : (
                      <>
                        <FileSpreadsheet className="h-3.5 w-3.5" />
                        Export Excel Model (.xlsx)
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* INTERACTIVE CHART PANEL */}
              <div className="glass-panel">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                  <div>
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-indigo-400" /> Forecasting Engine Output
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">Interactive multi-tab visual analytical engine</p>
                  </div>
                  <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 overflow-x-auto w-full sm:w-auto">
                    <button 
                      onClick={() => setActiveTab('forecast')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${activeTab === 'forecast' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      5d Forecast
                    </button>
                    <button 
                      onClick={() => setActiveTab('oscillators')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${activeTab === 'oscillators' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      RSI / MACD
                    </button>
                    <button 
                      onClick={() => setActiveTab('sentiment')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${activeTab === 'sentiment' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      Sentiment vs Price
                    </button>
                    <button 
                      onClick={() => setActiveTab('backtest')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${activeTab === 'backtest' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      Backtesting
                    </button>
                  </div>
                </div>

                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    {activeTab === 'forecast' ? (
                      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="displayDate" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '10px' }}
                          labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                        />
                        <Area type="monotone" dataKey="price" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorPrice)" name="Historical Price" />
                        <Area type="monotone" dataKey="forecastPrice" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorForecast)" name="Predicted price (5d)" />
                      </ComposedChart>
                    ) : activeTab === 'oscillators' ? (
                      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="displayDate" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis yAxisId="left" stroke="#818cf8" fontSize={11} tickLine={false} domain={[0, 100]} />
                        <YAxis yAxisId="right" orientation="right" stroke="#fbbf24" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '10px' }}
                          labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                        />
                        <ReferenceLine yAxisId="left" y={70} stroke="#f87171" strokeDasharray="3 3" label={{ value: 'Overbought', fill: '#f87171', fontSize: 10, position: 'top' }} />
                        <ReferenceLine yAxisId="left" y={30} stroke="#34d399" strokeDasharray="3 3" label={{ value: 'Oversold', fill: '#34d399', fontSize: 10, position: 'bottom' }} />
                        <Line yAxisId="left" type="monotone" dataKey="rsiVal" stroke="#818cf8" strokeWidth={2} name="RSI" dot={false} />
                        <Line yAxisId="right" type="monotone" dataKey="macdVal" stroke="#fbbf24" strokeWidth={2} name="MACD" dot={false} />
                      </ComposedChart>
                    ) : activeTab === 'sentiment' ? (
                      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="displayDate" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis yAxisId="left" stroke="#6366f1" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
                        <YAxis yAxisId="right" orientation="right" stroke="#fbbf24" fontSize={11} tickLine={false} domain={[-1, 1]} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '10px' }}
                        />
                        <Line yAxisId="left" type="monotone" dataKey="price" stroke="#6366f1" strokeWidth={2.5} name="Close Price" dot={false} />
                        <Area yAxisId="right" type="monotone" dataKey="sentiment" stroke="#fbbf24" fill="rgba(251, 191, 36, 0.1)" strokeWidth={1.5} name="Social Sentiment" />
                      </ComposedChart>
                    ) : (
                      <LineChart data={backtestData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="index" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '10px' }}
                        />
                        <Line type="monotone" dataKey="actual" stroke="#38bdf8" strokeWidth={2} name="Actual Test Price" dot={false} />
                        <Line type="monotone" dataKey="predicted" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Model Prediction" dot={false} />
                      </LineChart>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>

              {/* PORTFOLIO ADVISORY CARD */}
              <div className="glass-panel border-l-4 border-l-indigo-500">
                <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-indigo-400" /> Portfolio Manager Advisor Report
                </h2>
                <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed">
                  {renderMarkdown(data.recommendation)}
                </div>
              </div>
            </div>

            {/* COLUMN 3: SIDEBAR (METRICS, TECHNICAL SIGNALS, SENTIMENT CORPUS) */}
            <div className="space-y-8">
              
              {/* EVALUATION METRICS CARD */}
              <div className="glass-panel">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-1.5">
                  <Award className="h-4 w-4 text-indigo-400" /> Quant Validation Metrics
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400">Directional Accuracy</p>
                    <p className="text-lg font-bold text-white mt-1">{(data.metrics.directional_accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400">Model R² Coefficient</p>
                    <p className="text-lg font-bold text-white mt-1">{data.metrics.r2.toFixed(3)}</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400">Mean Squared Error</p>
                    <p className="text-lg font-bold text-white mt-1">{data.metrics.mse.toFixed(2)}</p>
                  </div>
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400">Mean Absolute Error</p>
                    <p className="text-lg font-bold text-white mt-1">{data.metrics.mae.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* TECHNICAL SIGNALS PANEL */}
              <div className="glass-panel">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-1.5">
                  <Activity className="h-4 w-4 text-indigo-400" /> Real-time Tech Signals
                </h2>
                <div className="signals-summary-grid">
                  <div className="signal-metric-card">
                    <div className="title">RSI (14)</div>
                    <div className="value text-white">{lastRSI.toFixed(1)}</div>
                    <span className={`status ${getRSISignal(lastRSI).class}`}>
                      {getRSISignal(lastRSI).label}
                    </span>
                  </div>
                  <div className="signal-metric-card">
                    <div className="title">MACD</div>
                    <div className="value text-white">{lastMACD.toFixed(2)}</div>
                    <span className={`status ${getMACDSignal(lastMACD).class}`}>
                      {lastMACD >= 0 ? 'Bullish' : 'Bearish'}
                    </span>
                  </div>
                  <div className="signal-metric-card">
                    <div className="title">Sentiment</div>
                    <div className="value text-white">{lastSentiment.toFixed(2)}</div>
                    <span className={`status ${getSentimentSignal(lastSentiment).class}`}>
                      {getSentimentSignal(lastSentiment).label}
                    </span>
                  </div>
                </div>
              </div>

              {/* SENTIMENT SCORES & CHANNEL BREAKDOWN */}
              <div className="glass-panel">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-1.5">
                  <MessageSquare className="h-4 w-4 text-indigo-400" /> Platform Sentiment Breakdown
                </h2>
                
                <div className="flex items-center gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800 mb-6">
                  <div className="h-12 w-12 rounded-full border-2 border-indigo-500/30 flex items-center justify-center bg-indigo-500/10">
                    <PieIcon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Total Net Sentiment</p>
                    <p className="text-xl font-extrabold text-white mt-0.5">{data.average_sentiment.toFixed(3)}</p>
                  </div>
                  <div className="ml-auto">
                    <span className={`badge ${data.average_sentiment > 0.15 ? 'badge-success' : data.average_sentiment < -0.15 ? 'badge-danger' : 'badge-warning'}`}>
                      {data.average_sentiment > 0.15 ? 'BULLISH' : data.average_sentiment < -0.15 ? 'BEARISH' : 'NEUTRAL'}
                    </span>
                  </div>
                </div>

                <div className="platform-sentiment-container mb-6">
                  {platformBreakdown.map((platform, idx) => {
                    const fillPercent = ((platform.avgCompound + 1) / 2) * 100;
                    const fillColor = platform.avgCompound > 0.15 
                      ? 'var(--success)' 
                      : platform.avgCompound < -0.15 
                        ? 'var(--danger)' 
                        : 'var(--warning)';

                    return (
                      <div key={idx} className="platform-sentiment-card">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300">{platform.name}</span>
                          <span className="text-[10px] text-slate-500">({platform.count} items)</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-sm font-bold text-white">{platform.avgCompound.toFixed(2)}</span>
                          <span className="text-[10px] uppercase font-bold" style={{ color: fillColor }}>{platform.sentiment}</span>
                        </div>
                        <div className="sentiment-bar-bg">
                          <div 
                            className="sentiment-bar-fill"
                            style={{ 
                              width: `${platform.count > 0 ? fillPercent : 50}%`,
                              backgroundColor: platform.count > 0 ? fillColor : 'rgba(255,255,255,0.1)'
                            }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5" /> Social Media Corpus Items
                </h3>

                {/* platform filter tabs */}
                <div className="platform-tabs">
                  {['all', 'Reddit', 'Twitter', 'Telegram', 'News'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setCorpusPlatformFilter(tab)}
                      className={`platform-tab-btn ${corpusPlatformFilter === tab ? 'active' : ''}`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                  {sentimentDetails.map((item, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-900 text-xs">
                      <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                        <span className="font-semibold text-indigo-400">{item.Source}</span>
                        <span className={item.compound > 0.15 ? 'text-emerald-400' : item.compound < -0.15 ? 'text-rose-400' : 'text-amber-400'}>
                          Compound: {item.compound.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                  {sentimentDetails.length === 0 && (
                    <div className="text-xs text-slate-500 italic text-center py-4">No scraped posts found matching this platform filter.</div>
                  )}
                </div>
              </div>

              {/* MULTI-AGENT LOGS STEPPER */}
              <div className="glass-panel">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-1.5">
                  <Cpu className="h-4 w-4 text-indigo-400" /> Orchestrated Agent Steppers
                </h2>
                <div className="terminal-container !h-64">
                  {data.agent_logs.map((log, idx) => {
                    let color = "text-sky-400";
                    if (log.includes("[Data Collection Agent]")) color = "text-emerald-400";
                    if (log.includes("[Sentiment Agent]")) color = "text-purple-300";
                    if (log.includes("[Quant Agent]")) color = "text-amber-400";
                    if (log.includes("[Portfolio Manager]")) color = "text-rose-400 font-semibold";
                    return (
                      <div key={idx} className="log-stepper-item">
                        <span className="text-[10px] text-slate-600 select-none">#{idx+1}</span>
                        <div className={`terminal-line ${color}`} style={{ margin: 0 }}>
                          {log}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={terminalEndRef}></div>
                </div>
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
