import React from 'react';
import { BookOpen, CheckCircle2, Clock, AlertCircle, Shield, Cpu, Activity, GitBranch, ArrowRight } from 'lucide-react';

export function ResearchOverviewView({ data, onSelectSeries }) {
  if (!data) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETE_AND_FROZEN':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="h-3 w-3" /> Complete & Frozen
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300 animate-pulse">
            <Clock className="h-3 w-3" /> Active Training (Series 4C)
          </span>
        );
      case 'COMPLETED_PRELIMINARY':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-300">
            <Activity className="h-3 w-3" /> Preliminary Complete
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-300">
            <GitBranch className="h-3 w-3" /> Planned Protocol
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 text-white rounded-xl p-6 shadow-md border border-slate-700">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <BookOpen className="h-4 w-4" />
              <span>Phase 4 Research Program</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white mb-2">
              {data.title}
            </h1>
            <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
              {data.description}
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-lg p-3.5 border border-white/20 text-xs space-y-1.5 shrink-0">
            <div className="flex justify-between gap-4 text-slate-200">
              <span>Evaluations Completed:</span>
              <strong className="text-teal-300 font-mono text-sm">{data.overall_progress?.total_evaluations_completed ?? 446}</strong>
            </div>
            <div className="flex justify-between gap-4 text-slate-200">
              <span>Frozen Checkpoints:</span>
              <strong className="text-teal-300 font-mono text-sm">{data.overall_progress?.total_checkpoints_preserved ?? 70}</strong>
            </div>
            <div className="flex justify-between gap-4 text-slate-200">
              <span>Active Workload:</span>
              <strong className="text-amber-300 font-mono text-sm">Series 4C (25 Runs)</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Series Matrix Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.series_list.map((s) => (
          <div
            key={s.series_id}
            className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-bold text-teal-700 uppercase tracking-wider">
                  {s.series_id}
                </span>
                {getStatusBadge(s.status)}
              </div>
              <h3 className="text-sm font-bold text-slate-900 mb-1.5 leading-snug">
                {s.name}
              </h3>
              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                {s.hypothesis}
              </p>
            </div>

            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>Algorithm: <strong className="text-slate-800">{s.algorithm}</strong></span>
                <span>Workload: <strong className="text-slate-800">{s.runs_total} runs / {s.evals_total} evals</strong></span>
              </div>
              {s.key_findings && (
                <div className="bg-slate-50 rounded p-2 text-[11px] text-slate-700 border border-slate-200/60">
                  <span className="font-semibold text-slate-900">Key Finding:</span> {s.key_findings}
                </div>
              )}
              {onSelectSeries && (
                <button
                  onClick={() => {
                    if (s.series_id === 'Series 4B') onSelectSeries('series4b');
                    else if (s.series_id === 'Series 4C') onSelectSeries('series4c');
                    else if (s.series_id === 'Series 4E') onSelectSeries('series4e');
                  }}
                  className="w-full mt-1 py-1.5 px-3 bg-slate-50 hover:bg-teal-50 hover:text-teal-700 text-slate-700 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition border border-slate-200"
                >
                  <span>Explore Empirical Findings</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
