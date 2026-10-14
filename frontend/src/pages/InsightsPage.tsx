import React, { useState, useEffect } from 'react';
import { 
  Lightbulb, 
  Flame, 
  Calendar, 
  AlertTriangle, 
  Zap, 
  ArrowRight, 
  Clock, 
  ShieldAlert, 
  TrendingUp,
  Sliders,
  CheckCircle2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { EnergyInsightsResponse, getEnergyInsights } from '../services/api';

interface InsightsPageProps {
  activeDataset: string;
}

export const InsightsPage: React.FC<InsightsPageProps> = ({ activeDataset }) => {
  const [insights, setInsights] = useState<EnergyInsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadInsights();
  }, [activeDataset]);

  const loadInsights = async () => {
    setLoading(true);
    try {
      const data = await getEnergyInsights(activeDataset);
      setInsights(data);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-xs font-semibold text-slate-500">Computing energy consumption patterns and anomalies...</p>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
        <Lightbulb className="w-10 h-10 mx-auto mb-2 text-slate-300" />
        <p>No insights generated. Ensure a valid dataset is active.</p>
      </div>
    );
  }

  const unit = insights.target_column.toLowerCase().includes('wh') ? 'Wh' : 'kW';
  const peakHours = insights.peak_hours || [];
  const hourlyData = insights.hourly_breakdown || [];
  const dailyData = insights.daily_breakdown || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-emerald-600" />
            Data-Driven Energy Intelligence & Load Shifting Insights
          </h2>
          <p className="text-xs text-slate-500">
            Empirical peak demand detection, diurnal cycling analysis, and operational efficiency opportunities for <span className="font-semibold text-slate-700">{insights.dataset_name}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 text-xs text-amber-800 flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-600" />
            <span>Peak Window: <strong>{peakHours.map(h => `${h}:00`).join(', ')}</strong></span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
          <span className="text-xs font-semibold uppercase text-slate-500">Peak-to-Average Ratio</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {insights.statistics.peak_to_average_ratio}x
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Ratio of max surge to average load</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
          <span className="text-xs font-semibold uppercase text-slate-500">Weekday Mean Load</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {insights.statistics.weekday_mean.toLocaleString()}{' '}
            <span className="text-xs text-slate-500">{unit}</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Business operating days</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
          <span className="text-xs font-semibold uppercase text-slate-500">Weekend Mean Load</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {insights.statistics.weekend_mean.toLocaleString()}{' '}
            <span className="text-xs text-slate-500">{unit}</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {insights.statistics.weekend_difference_pct > 0 ? '+' : ''}{insights.statistics.weekend_difference_pct}% vs weekdays
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs">
          <span className="text-xs font-semibold uppercase text-slate-500">Detected Consumption Spikes</span>
          <div className="text-2xl font-bold text-rose-600 mt-1">
            {insights.statistics.total_anomalies_detected}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Deviations &gt; 2.8 rolling z-score</p>
        </div>
      </div>

      {/* Hourly and Daily Pattern Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Diurnal Profile */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-600" />
                Diurnal Hourly Consumption Profile (0:00 - 23:00)
              </h3>
              <p className="text-xs text-slate-500">Average energy load by hour of day</p>
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <span className="flex items-center gap-1 font-semibold text-rose-600">
                <span className="w-2.5 h-2.5 bg-rose-500 rounded-sm"></span> Peak Hours
              </span>
              <span className="flex items-center gap-1 font-semibold text-emerald-600">
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-sm"></span> Normal / Off-Peak
              </span>
            </div>
          </div>

          <div className="h-64 w-full mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="label" stroke="#94a3b8" fontSize={10} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} unit={` ${unit}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                />
                <Bar dataKey="mean" name={`Average Load (${unit})`} radius={[3, 3, 0, 0]}>
                  {hourlyData.map((entry) => (
                    <Cell 
                      key={`cell-${entry.hour}`} 
                      fill={peakHours.includes(entry.hour) ? '#ef4444' : '#10b981'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Day of Week Profile */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-600" />
                Day of Week Average Demand
              </h3>
              <p className="text-xs text-slate-500">Weekly operational demand distribution</p>
            </div>
          </div>

          <div className="h-64 w-full mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} unit={` ${unit}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                />
                <Bar dataKey="mean" name={`Average Load (${unit})`} fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Actionable Recommendations List */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
        <h3 className="font-bold text-slate-900 text-sm pb-3 border-b border-slate-100 flex items-center gap-2">
          <Zap className="w-4 h-4 text-emerald-600" />
          Data-Derived Energy Conservation Opportunities
        </h3>

        <div className="mt-4 space-y-4">
          {insights.recommendations.map((rec) => (
            <div 
              key={rec.id}
              className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:border-slate-300 transition-all space-y-2"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    rec.severity === 'High'
                      ? 'bg-rose-100 text-rose-800 border border-rose-200'
                      : rec.severity === 'Medium'
                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}>
                    {rec.severity} Priority
                  </span>
                  <span className="text-xs font-semibold text-slate-500">{rec.category}</span>
                  <span className="text-slate-300">•</span>
                  <span className="text-xs font-mono font-bold text-slate-700">{rec.id}</span>
                </div>

                <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  {rec.potential_impact}
                </div>
              </div>

              <h4 className="font-bold text-slate-900 text-sm">{rec.title}</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong className="text-slate-700">Observed Pattern:</strong> {rec.observation}
              </p>
              <p className="text-xs text-slate-800 leading-relaxed">
                <strong className="text-emerald-700">Recommended Action:</strong> {rec.suggestion}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Consumption Spikes Table */}
      {insights.spikes && insights.spikes.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                Detected High-Magnitude Consumption Spikes (Z-Score &gt; 2.8)
              </h3>
              <p className="text-xs text-slate-500">Statistically significant surges relative to 24-hour moving baseline</p>
            </div>
          </div>

          <div className="overflow-x-auto mt-3">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="px-3.5 py-2">Timestamp</th>
                  <th className="px-3.5 py-2">Recorded Peak ({unit})</th>
                  <th className="px-3.5 py-2">Expected Rolling Mean ({unit})</th>
                  <th className="px-3.5 py-2">Surge Deviation (%)</th>
                  <th className="px-3.5 py-2">Statistical Z-Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {insights.spikes.map((sp, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/70 font-mono">
                    <td className="px-3.5 py-2 font-medium">{sp.timestamp}</td>
                    <td className="px-3.5 py-2 font-bold text-rose-600">{sp.value}</td>
                    <td className="px-3.5 py-2">{sp.expected_mean}</td>
                    <td className="px-3.5 py-2 text-rose-700 font-semibold">+{sp.deviation_pct}%</td>
                    <td className="px-3.5 py-2 font-bold text-slate-800">{sp.z_score}σ</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
