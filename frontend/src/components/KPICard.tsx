import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeLabel?: string;
  subtitle?: string;
  icon: React.ReactNode;
  variant?: 'emerald' | 'blue' | 'amber' | 'purple' | 'slate';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  change,
  changeLabel = 'vs previous period',
  subtitle,
  icon,
  variant = 'emerald',
}) => {
  const getBadgeStyle = () => {
    switch (variant) {
      case 'emerald':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'blue':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'amber':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'purple':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getIconContainerStyle = () => {
    switch (variant) {
      case 'emerald':
        return 'bg-emerald-500/10 text-emerald-600';
      case 'blue':
        return 'bg-blue-500/10 text-blue-600';
      case 'amber':
        return 'bg-amber-500/10 text-amber-600';
      case 'purple':
        return 'bg-purple-500/10 text-purple-600';
      default:
        return 'bg-slate-500/10 text-slate-600';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        <div className={`p-2 rounded-lg ${getIconContainerStyle()}`}>
          {icon}
        </div>
      </div>

      <div className="flex items-baseline gap-1.5 mb-2">
        <span className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          {value}
        </span>
        {unit && (
          <span className="text-sm font-semibold text-slate-500">{unit}</span>
        )}
      </div>

      {change !== undefined ? (
        <div className="flex items-center gap-1.5 text-xs">
          <span
            className={`inline-flex items-center font-semibold px-1.5 py-0.5 rounded border text-[11px] ${
              change > 0
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : change < 0
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-slate-50 text-slate-700 border-slate-200'
            }`}
          >
            {change > 0 ? (
              <ArrowUpRight className="w-3 h-3 mr-0.5" />
            ) : change < 0 ? (
              <ArrowDownRight className="w-3 h-3 mr-0.5" />
            ) : (
              <Minus className="w-3 h-3 mr-0.5" />
            )}
            {Math.abs(change)}%
          </span>
          <span className="text-slate-400 font-medium">{changeLabel}</span>
        </div>
      ) : subtitle ? (
        <p className="text-xs text-slate-500 font-medium truncate">{subtitle}</p>
      ) : null}
    </div>
  );
};
