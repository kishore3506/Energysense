import React from 'react';
import { 
  LayoutDashboard, 
  TrendingUp, 
  Database, 
  Cpu, 
  Lightbulb, 
  FileText, 
  Zap,
  CheckCircle2,
  AlertCircle,
  Award,
  Cloud
} from 'lucide-react';

export type NavPage = 'overview' | 'forecasting' | 'dataset' | 'training' | 'benchmark' | 'insights' | 'deployment' | 'reports';

interface SidebarProps {
  currentPage: NavPage;
  onSelectPage: (page: NavPage) => void;
  backendOnline: boolean;
  activeDataset: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  backendOnline,
  activeDataset
}) => {
  const navItems: { id: NavPage; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'forecasting', label: 'Energy Forecasting', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'dataset', label: 'Data Eng & PCA', icon: <Database className="w-4 h-4" />, badge: 'Rubric 1' },
    { id: 'training', label: 'Modeling & Tuning', icon: <Cpu className="w-4 h-4" />, badge: 'Rubric 2' },
    { id: 'benchmark', label: 'Benchmark & Errors', icon: <Award className="w-4 h-4" />, badge: 'Rubric 3' },
    { id: 'insights', label: 'Energy Insights', icon: <Lightbulb className="w-4 h-4" /> },
    { id: 'deployment', label: 'Deployment & Cloud', icon: <Cloud className="w-4 h-4" />, badge: 'Rubric 4' },
    { id: 'reports', label: 'Reports & History', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 h-screen sticky top-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white shadow-lg shadow-emerald-950/40">
          <Zap className="w-5 h-5 fill-white" />
        </div>
        <div>
          <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
            EnergySense
            <span className="text-[9px] uppercase font-semibold px-1 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              AI/ML
            </span>
          </h1>
          <p className="text-[11px] text-slate-400">Temporal Deep Learning</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2.5 space-y-1 overflow-y-auto">
        <div className="px-3 py-1.5 text-[10px] font-semibold tracking-wider text-slate-500 uppercase">
          Platform Evaluation
        </div>
        {navItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-xs'
                  : 'hover:bg-slate-800/70 text-slate-300 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className={isActive ? 'text-emerald-400' : 'text-slate-400'}>
                  {item.icon}
                </span>
                <span className="text-left">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-mono ${
                  isActive ? 'bg-emerald-500/30 text-emerald-300' : 'bg-slate-800 text-slate-500'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/50">
        <div className="rounded-lg bg-slate-800/80 p-2.5 border border-slate-700/60 text-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-[11px]">Backend API</span>
            <span className={`inline-flex items-center gap-1 font-semibold text-[11px] ${backendOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {backendOnline ? (
                <>
                  <CheckCircle2 className="w-3 h-3" />
                  Active
                </>
              ) : (
                <>
                  <AlertCircle className="w-3 h-3" />
                  Offline
                </>
              )}
            </span>
          </div>
          <div className="pt-1 border-t border-slate-700/50">
            <div className="text-[10px] text-slate-400 truncate">Active Dataset:</div>
            <div className="text-[11px] text-slate-200 font-mono font-medium truncate" title={activeDataset}>
              {activeDataset || 'None loaded'}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
