import React from 'react';
import { Database, RefreshCw, Zap, Sparkles } from 'lucide-react';
import { DatasetItem } from '../services/api';

interface NavbarProps {
  title: string;
  subtitle: string;
  datasets: DatasetItem[];
  activeDataset: string;
  onSelectDataset: (name: string) => void;
  onRefresh: () => void;
  onQuickForecast?: () => void;
  loading?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  title,
  subtitle,
  datasets,
  activeDataset,
  onSelectDataset,
  onRefresh,
  onQuickForecast,
  loading = false,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sticky top-0 z-20">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
        <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* Dataset Selector Dropdown */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 shadow-xs">
          <Database className="w-4 h-4 text-emerald-600" />
          <span className="text-xs text-slate-500 font-medium hidden md:inline">Dataset:</span>
          <select
            value={activeDataset}
            onChange={(e) => onSelectDataset(e.target.value)}
            className="text-xs font-semibold text-slate-700 bg-transparent border-none focus:outline-hidden cursor-pointer"
          >
            {datasets.map((d) => (
              <option key={d.name} value={d.name}>
                {d.name} ({d.size_kb} KB)
              </option>
            ))}
          </select>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          disabled={loading}
          title="Refresh current data"
          className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
        </button>

        {/* Quick forecast trigger */}
        {onQuickForecast && (
          <button
            onClick={onQuickForecast}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-sm transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate 24h Forecast</span>
          </button>
        )}
      </div>
    </header>
  );
};
