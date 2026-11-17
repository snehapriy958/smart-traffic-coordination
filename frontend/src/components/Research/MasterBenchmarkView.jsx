import React from 'react';
import { ControllerComparison } from '../ControllerComparison';
import { ShieldCheck, BookOpen, Layers } from 'lucide-react';

export function MasterBenchmarkView({ compareData, isLoading, error }) {
  return (
    <div className="space-y-6">
      {/* Research Paper Context Banner */}
      <div className="bg-slate-900 border border-slate-700 text-white rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3" /> AUTHORITATIVE BENCHMARK
            </span>
            <span className="text-xs text-slate-400 font-mono">
              N=10 Random Seeds &bull; 900s Evaluation Window &bull; 109 Corridor Trips
            </span>
          </div>
          <h2 className="text-lg font-bold text-white">
            Authoritative 4-Controller Corridor Master Benchmark
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">
            Standardized evaluation comparing Fixed-Time Baseline, Coordinated Adaptive, Double-DQN (Stage A), and PPO (Stage A) across identical seed sequences and network demand.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-lg p-3 text-xs text-slate-200 border border-white/20 space-y-1 shrink-0">
          <div>Bonferroni-corrected significance: <strong className="text-teal-300">&alpha; = 0.0167</strong></div>
          <div>Coordinated Adaptive Speedup: <strong className="text-emerald-300">+44.6% vs Baseline</strong></div>
          <div>Double-DQN Delay Reduction: <strong className="text-amber-300">-35.1% vs Baseline</strong></div>
        </div>
      </div>

      {/* Embedded Controller Comparison Component */}
      <ControllerComparison compareData={compareData} isLoading={isLoading} error={error} />
    </div>
  );
}
