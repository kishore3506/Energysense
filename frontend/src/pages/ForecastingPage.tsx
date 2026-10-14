import React, { useState } from 'react';
import { 
  TrendingUp, 
  Download, 
  Play, 
  Clock, 
  Sliders, 
  Flame, 
  Zap, 
  ArrowUpRight, 
  ArrowDownRight,
  Database,
  Cpu
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { 
  ForecastResponse, 
  DatasetItem, 
  runForecast, 
  getExportCsvUrl 
} from '../services/api';

interface ForecastingPageProps {
  datasets: DatasetItem[];
  activeDataset: string;
  onSelectDataset: (name: string) => void;
  forecastData: ForecastResponse | null;
  onForecastGenerated: (res: ForecastResponse) => void;
}

export const ForecastingPage: React.FC<ForecastingPageProps> = ({
  datasets,
  activeDataset,
  onSelectDataset,
  forecastData,
  onForecastGenerated,
}) => {
  const [modelType, setModelType] = useState<'LSTM' | 'GRU'>('LSTM');
  const [lookback, setLookback] = useState<number>(24);
  const [horizon, setHorizon] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runForecast({
        dataset_name: activeDataset,
        horizon,
        lookback,
        model_type: modelType,
      });
      onForecastGenerated(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  // Combine historical context with future predictions for continuous chart
  const combinedChartData: any[] = [];
  if (forecastData) {
    if (forecastData.historical_context) {
      forecastData.historical_context.forEach((item) => {
        combinedChartData.push({
          timestamp: item.timestamp,
          actual: item.actual,
          type: 'history',
        });
      });
    }

    if (forecastData.predictions) {
      // Connect the last historical point with forecast for continuous line
      if (forecastData.historical_context && forecastData.historical_context.length > 0) {
        const lastActual = forecastData.historical_context[forecastData.historical_context.length - 1];
        // Ensure first point has predicted continuity
        if (combinedChartData.length > 0) {
          combinedChartData[combinedChartData.length - 1].predicted = lastActual.actual;
          combinedChartData[combinedChartData.length - 1].baseline = lastActual.actual;
        }
      }

      forecastData.predictions.forEach((pred) => {
        combinedChartData.push({
          timestamp: pred.timestamp,
          predicted: pred.predicted,
          baseline: pred.baseline,
          type: 'forecast',
        });
      });
    }
  }

  const unit = forecastData?.summary?.unit || 'Wh';
  const lastHistoryTimestamp = forecastData?.historical_context && forecastData.historical_context.length > 0
    ? forecastData.historical_context[forecastData.historical_context.length - 1].timestamp
    : '';

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between pb-4 border-b border-slate-100 gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              Temporal Deep Learning Energy Forecaster
            </h2>
            <p className="text-xs text-slate-500">
              Configure parameters and trigger multi-step sequence forecasting on current building load
            </p>
          </div>

          <div className="flex items-center gap-3 w-full lg:w-auto">
            <button
              onClick={handleRunForecast}
              disabled={loading}
              className="flex-1 lg:flex-initial flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:bg-emerald-400 text-white font-semibold px-5 py-2.5 rounded-lg text-xs shadow-sm transition-all cursor-pointer"
            >
              <Play className={`w-3.5 h-3.5 fill-white ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Forecasting...' : 'Execute Forecast'}</span>
            </button>

            {forecastData && (
              <a
                href={getExportCsvUrl(forecastData.forecast_id)}
                download={`energysense_forecast_${forecastData.forecast_id}.csv`}
                className="flex items-center justify-center gap-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold px-4 py-2.5 rounded-lg text-xs transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </a>
            )}
          </div>
        </div>

        {/* Configuration Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-1">
          {/* Dataset Selector */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Target Building / Dataset
            </label>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs">
              <Database className="w-4 h-4 text-slate-500 shrink-0" />
              <select
                value={activeDataset}
                onChange={(e) => onSelectDataset(e.target.value)}
                className="bg-transparent w-full text-slate-800 font-semibold focus:outline-hidden cursor-pointer"
              >
                {datasets.map((d) => (
                  <option key={d.name} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Model Architecture */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Model Architecture
            </label>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs">
              <Cpu className="w-4 h-4 text-slate-500 shrink-0" />
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value as any)}
                className="bg-transparent w-full text-slate-800 font-semibold focus:outline-hidden cursor-pointer"
              >
                <option value="LSTM">Stacked LSTM (Recommended)</option>
                <option value="GRU">Stacked GRU (Gated Recurrent)</option>
                <option value="BiLSTM">Stacked BiLSTM (Bidirectional)</option>
              </select>
            </div>
          </div>

          {/* Historical Lookback Window */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Lookback Window: <span className="text-emerald-600 font-bold">{lookback} hours</span>
            </label>
            <input
              type="range"
              min="12"
              max="72"
              step="6"
              value={lookback}
              onChange={(e) => setLookback(Number(e.target.value))}
              className="w-full accent-emerald-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
              <span>12h</span>
              <span>24h (default)</span>
              <span>48h</span>
              <span>72h</span>
            </div>
          </div>

          {/* Forecast Horizon */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Forecast Horizon: <span className="text-emerald-600 font-bold">{horizon} hours ahead</span>
            </label>
            <input
              type="range"
              min="6"
              max="48"
              step="6"
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full accent-emerald-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
              <span>6h</span>
              <span>12h</span>
              <span>24h (1-Day)</span>
              <span>48h</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
            {error}
          </div>
        )}
      </div>

      {/* Forecast Summary KPIs */}
      {forecastData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
            <span className="text-xs font-semibold text-slate-500 uppercase">Mean Forecasted Load</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {forecastData.summary.mean_forecast.toLocaleString()}{' '}
              <span className="text-xs text-slate-500">{unit}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Over next {forecastData.horizon} hours</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
            <span className="text-xs font-semibold text-slate-500 uppercase">Predicted Peak Load</span>
            <div className="text-2xl font-bold text-amber-600 mt-1">
              {forecastData.summary.peak_forecast.toLocaleString()}{' '}
              <span className="text-xs text-slate-500">{unit}</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 truncate">
              At: {forecastData.summary.peak_time ? forecastData.summary.peak_time.slice(0, 16) : 'N/A'}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
            <span className="text-xs font-semibold text-slate-500 uppercase">Cumulative Energy</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {(forecastData.summary.total_forecast / (unit === 'Wh' ? 1000 : 1)).toFixed(1)}{' '}
              <span className="text-xs text-slate-500">{unit === 'Wh' ? 'kWh' : 'MWh'}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Total integral over horizon</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
            <span className="text-xs font-semibold text-slate-500 uppercase">Variance vs Recent History</span>
            <div className={`text-2xl font-bold mt-1 flex items-center gap-1 ${
              forecastData.summary.percentage_change > 0 ? 'text-rose-600' : 'text-emerald-600'
            }`}>
              {forecastData.summary.percentage_change > 0 ? (
                <ArrowUpRight className="w-5 h-5" />
              ) : (
                <ArrowDownRight className="w-5 h-5" />
              )}
              {Math.abs(forecastData.summary.percentage_change)}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Recent Mean: {forecastData.summary.recent_historical_mean} {unit}
            </p>
          </div>
        </div>
      )}

      {/* Main Interactive Forecast Chart */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
          <div>
            <h3 className="font-bold text-slate-900 text-base">
              Historical Context & Future Consumption Trajectory
            </h3>
            <p className="text-xs text-slate-500">
              Blue = Past historical observations • Emerald = Deep Learning forecast • Amber = Persistence baseline
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 font-medium text-slate-700">
              <span className="w-3 h-0.5 bg-blue-600 rounded"></span> Past {lookback}h Context
            </span>
            <span className="flex items-center gap-1.5 font-medium text-emerald-600">
              <span className="w-3 h-0.5 bg-emerald-500 rounded"></span> {modelType} Forecast
            </span>
            <span className="flex items-center gap-1.5 font-medium text-amber-500">
              <span className="w-3 h-0.5 bg-amber-400 dashed rounded"></span> Baseline Persistence
            </span>
          </div>
        </div>

        <div className="h-96 w-full mt-4">
          {combinedChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={combinedChartData} margin={{ top: 15, right: 15, left: -5, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(v) => typeof v === 'string' && v.length >= 16 ? v.slice(11, 16) : v}
                  stroke="#94a3b8" 
                  fontSize={11} 
                  tickLine={false}
                />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} unit={` ${unit}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  labelFormatter={(v) => `Time: ${v}`}
                />
                {lastHistoryTimestamp && (
                  <ReferenceLine x={lastHistoryTimestamp} stroke="#64748b" strokeDasharray="3 3" label={{ value: 'Forecast Start', fill: '#64748b', fontSize: 10, position: 'top' }} />
                )}
                <Line 
                  type="monotone" 
                  dataKey="actual" 
                  name="Observed History" 
                  stroke="#2563eb" 
                  strokeWidth={2.5} 
                  dot={false}
                  connectNulls={false} 
                />
                <Line 
                  type="monotone" 
                  dataKey="predicted" 
                  name="AI Forecast" 
                  stroke="#10b981" 
                  strokeWidth={2.5} 
                  dot={false} 
                />
                <Line 
                  type="monotone" 
                  dataKey="baseline" 
                  name="Persistence Baseline" 
                  stroke="#f59e0b" 
                  strokeWidth={1.5} 
                  strokeDasharray="4 4" 
                  dot={false} 
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <TrendingUp className="w-10 h-10 mb-2 opacity-50" />
              <p className="text-sm">Click "Execute Forecast" above to project building energy demand.</p>
            </div>
          )}
        </div>
      </div>

      {/* Forecast Data Table */}
      {forecastData && forecastData.predictions && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Step-by-Step Forecast Schedule</h3>
              <p className="text-xs text-slate-500">Tabular breakdown of predicted energy usage for each forecast hour</p>
            </div>
            <a
              href={getExportCsvUrl(forecastData.forecast_id)}
              download={`energysense_forecast_${forecastData.forecast_id}.csv`}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download CSV
            </a>
          </div>

          <div className="overflow-x-auto mt-3">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="px-3.5 py-2.5">Horizon Step</th>
                  <th className="px-3.5 py-2.5">Timestamp</th>
                  <th className="px-3.5 py-2.5">AI Forecast ({unit})</th>
                  <th className="px-3.5 py-2.5">Baseline ({unit})</th>
                  <th className="px-3.5 py-2.5">Variance vs Baseline</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {forecastData.predictions.map((p) => {
                  const diff = p.predicted - p.baseline;
                  return (
                    <tr key={p.step} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-3.5 py-2 font-mono font-medium text-slate-500">t + {p.step}h</td>
                      <td className="px-3.5 py-2 font-medium">{p.timestamp}</td>
                      <td className="px-3.5 py-2 font-bold text-emerald-700">{p.predicted.toFixed(2)}</td>
                      <td className="px-3.5 py-2 text-slate-600">{p.baseline.toFixed(2)}</td>
                      <td className="px-3.5 py-2">
                        <span className={`inline-flex items-center font-medium ${
                          diff > 0 ? 'text-rose-600' : 'text-emerald-600'
                        }`}>
                          {diff > 0 ? '+' : ''}{diff.toFixed(2)} {unit}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
