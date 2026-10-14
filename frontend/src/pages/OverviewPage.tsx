import React from 'react';
import { 
  Zap, 
  Activity, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  Cpu, 
  Layers, 
  Flame,
  ArrowRight
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { KPICard } from '../components/KPICard';
import { DatasetSummary, ModelMetricsResponse, ForecastResponse } from '../services/api';

interface OverviewPageProps {
  summary: DatasetSummary | null;
  metrics: ModelMetricsResponse | null;
  latestForecast: ForecastResponse | null;
  onNavigate: (page: any) => void;
  loading: boolean;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  summary,
  metrics,
  latestForecast,
  onNavigate,
  loading
}) => {
  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-sm font-semibold text-slate-500">Loading EnergySense intelligence platform...</p>
      </div>
    );
  }

  const unit = summary?.target_column.toLowerCase().includes('wh') ? 'Wh' : 'kW';
  const totalVal = summary ? ((summary.metrics.mean * summary.total_rows) / 1000).toFixed(1) : '0';
  const avgVal = summary ? summary.metrics.mean.toFixed(1) : '0';
  const peakVal = summary ? summary.metrics.peak_value.toFixed(1) : '0';
  const next24hVal = latestForecast ? latestForecast.summary.mean_forecast.toFixed(1) : '---';
  const pctChange = latestForecast ? latestForecast.summary.percentage_change : 0;

  // Chart data: test set actual vs predicted
  const chartData = metrics?.chart_samples && metrics.chart_samples.length > 0
    ? metrics.chart_samples.slice(0, 48)
    : [];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2 border border-emerald-500/30">
            <Activity className="w-3.5 h-3.5" />
            AI Building Energy Analytics & Deep Forecasting
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Building Energy Overview: {summary?.dataset_name || 'Loading...'}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl">
            Temporal deep learning pipeline trained on chronological building load profiles with recurrent memory units (LSTM & GRU) to forecast future demand and shave peak consumption.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => onNavigate('forecasting')}
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold px-4 py-2.5 rounded-xl shadow-md text-xs transition-colors cursor-pointer"
          >
            <span>Run Forecast</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate('training')}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-4 py-2.5 rounded-xl border border-slate-700 text-xs transition-colors cursor-pointer"
          >
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>Retrain Model</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Period Energy"
          value={totalVal}
          unit={unit === 'Wh' ? 'kWh' : 'MWh'}
          subtitle={`Across ${summary?.total_rows.toLocaleString()} timestamps`}
          icon={<Zap className="w-5 h-5" />}
          variant="emerald"
        />

        <KPICard
          title="Average Consumption"
          value={avgVal}
          unit={unit}
          subtitle={`Std Dev: ±${summary?.metrics.std.toFixed(1)} ${unit}`}
          icon={<Activity className="w-5 h-5" />}
          variant="blue"
        />

        <KPICard
          title="Peak Demand Recorded"
          value={peakVal}
          unit={unit}
          subtitle={`Observed at ${summary?.metrics.peak_timestamp ? summary.metrics.peak_timestamp.slice(0, 16) : 'N/A'}`}
          icon={<Flame className="w-5 h-5" />}
          variant="amber"
        />

        <KPICard
          title="Next 24h Forecast Avg"
          value={next24hVal}
          unit={unit}
          change={pctChange}
          changeLabel="vs recent average"
          icon={<TrendingUp className="w-5 h-5" />}
          variant="purple"
        />
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Actual vs Predicted Performance Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
            <div>
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                Actual vs Deep Learning Predictions (Test Evaluation Window)
              </h3>
              <p className="text-xs text-slate-500">
                Out-of-sample chronological holdout evaluation: Real actual energy load vs LSTM forecast
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 font-medium text-slate-600">
                <span className="w-3 h-0.5 bg-slate-900 rounded"></span> Actual
              </span>
              <span className="flex items-center gap-1.5 font-medium text-emerald-600">
                <span className="w-3 h-0.5 bg-emerald-500 rounded"></span> LSTM Predicted
              </span>
              <span className="flex items-center gap-1.5 font-medium text-amber-500">
                <span className="w-3 h-0.5 bg-amber-400 dashed rounded"></span> Baseline
              </span>
            </div>
          </div>

          <div className="h-80 w-full mt-4">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
                    labelFormatter={(v) => `Timestamp: ${v}`}
                  />
                  <Line type="monotone" dataKey="actual" name="Actual Load" stroke="#0f172a" strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="predicted" name="LSTM Predicted" stroke="#10b981" strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="baseline" name="Persistence Baseline" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <Cpu className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-xs">No model evaluation samples available. Retrain the model on the Model Training tab.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Model & System Status Card */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-600" />
                Active Model Pipeline
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-semibold">
                {metrics?.latest_metrics?.model_type || 'LSTM'} Active
              </span>
            </div>

            <div className="mt-4 space-y-3.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Architecture</span>
                <span className="font-semibold text-slate-800">2-Layer Stacked Recurrent</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Historical Lookback</span>
                <span className="font-semibold text-slate-800">{metrics?.latest_metrics?.lookback || 24} hours</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Forecast Horizon</span>
                <span className="font-semibold text-slate-800">{metrics?.latest_metrics?.horizon || 24} hours</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Test MAE</span>
                <span className="font-semibold text-emerald-600">
                  {metrics?.latest_metrics?.test_mae ? `${metrics.latest_metrics.test_mae.toFixed(1)} ${unit}` : 'N/A'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Baseline MAE</span>
                <span className="font-semibold text-slate-600">
                  {metrics?.latest_metrics?.baseline_mae ? `${metrics.latest_metrics.baseline_mae.toFixed(1)} ${unit}` : 'N/A'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Error Reduction vs Baseline</span>
                <span className="font-semibold text-emerald-600">
                  {metrics?.latest_metrics?.test_mae && metrics?.latest_metrics?.baseline_mae
                    ? `-${(((metrics.latest_metrics.baseline_mae - metrics.latest_metrics.test_mae) / metrics.latest_metrics.baseline_mae) * 100).toFixed(1)}%`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <div className="bg-slate-50 rounded-lg p-3 text-xs border border-slate-200">
              <div className="flex items-center gap-2 text-slate-700 font-semibold mb-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                Data Leakage Protection Active
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                MinMax scalers strictly fit on chronological training split (70%) only. Validation and holdout test sets evaluated sequentially.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Overview Bar */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h4 className="font-bold text-slate-900 text-sm">Active Time-Series Profile</h4>
            <p className="text-xs text-slate-500">
              Span: <span className="font-medium text-slate-700">{summary?.start_time}</span> to <span className="font-medium text-slate-700">{summary?.end_time}</span> • Frequency: <span className="font-semibold text-emerald-700">{summary?.estimated_frequency}</span>
            </p>
          </div>
          <button
            onClick={() => onNavigate('dataset')}
            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
          >
            <span>Explore Dataset Details</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
