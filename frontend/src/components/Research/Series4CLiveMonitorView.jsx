import React, { useState } from 'react';
import { Activity, Clock, CheckCircle2, Shield, AlertCircle, RefreshCw, Terminal, TrendingUp, Layers, HardDrive } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

export function Series4CLiveMonitorView({ statusData, historyData, onRefresh, isRefreshing }) {
  const [selectedRunKey, setSelectedRunKey] = useState(null);

  if (!statusData) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-teal-600" />
        <p className="text-sm font-semibold">Connecting to live Series 4C execution monitor...</p>
      </div>
    );
  }

  const currentRun = statusData.current_run || {};
  const currentEp = currentRun.current_episode ?? 1;
  const totalEps = currentRun.total_episodes ?? 150;
  const progressPct = currentRun.progress_pct ?? Math.min(100, Math.round((currentEp / totalEps) * 100));

  const historyEpisodes = historyData?.episodes || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 text-white rounded-xl p-5 shadow-sm border border-slate-700 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 animate-pulse">
              <Activity className="h-3 w-3" /> ACTIVE EXECUTION IN PROGRESS
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Algorithm: MAPPO (14D) &bull; Single Sequential Worker
            </span>
          </div>
          <h2 className="text-lg font-bold text-white">
            Series 4C: Cooperative Reward Coupling Mechanism Ablation
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">
            Investigating multi-intersection coordination across 5 reward coupling ratios (&beta; &isin; {'{'}0.00, 0.25, 0.50, 0.75, 1.00{'}'}), 5 training seeds (101&ndash;105), and 150 confirmatory episodes per run.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 border border-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-teal-400' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh Telemetry'}</span>
          </button>
        </div>
      </div>

      {/* Safety & Protocol Banner */}
      <div className="bg-amber-50 border border-amber-200 text-amber-900 p-3 rounded-xl text-xs flex items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-600 shrink-0" />
          <span>
            <strong>Read-Only Research Monitor:</strong> Series 4C execution is strictly sequential to guarantee deterministic SUMO TraCI port bindings. Training cannot be paused, aborted, or modified from the web interface.
          </span>
        </div>
        <span className="text-[11px] font-mono text-amber-700 font-semibold shrink-0">
          Last Synced: {statusData.last_updated ? new Date(statusData.last_updated).toLocaleTimeString() : 'Live'}
        </span>
      </div>

      {/* Primary KPI & Progress Deck */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Run Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Current Active Run</span>
            <Activity className="h-4 w-4 text-amber-600 animate-spin" />
          </div>
          <div className="text-base font-bold text-slate-900 font-mono">
            {currentRun.run_key || 'beta_000_seed101'}
          </div>
          <div className="text-[11px] text-slate-600 mt-1">
            &beta; = <strong>{currentRun.beta?.toFixed(2) ?? '0.00'}</strong> (Pure Local) &bull; Seed: <strong>{currentRun.train_seed ?? 101}</strong>
          </div>
        </div>

        {/* Episode Progression Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Episode Progression</span>
            <Clock className="h-4 w-4 text-teal-600" />
          </div>
          <div className="text-xl font-bold text-teal-700 font-mono">
            Ep {currentEp} <span className="text-xs text-slate-500 font-sans font-normal">/ {totalEps}</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
            <div
              className="bg-teal-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, progressPct)}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex justify-between">
            <span>Progress: {progressPct}%</span>
            <span>~27s / episode</span>
          </div>
        </div>

        {/* Workload Progress Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Training Runs Completed</span>
            <CheckCircle2 className="h-4 w-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold text-slate-900 font-mono">
            {statusData.completed_training_runs} <span className="text-xs text-slate-500 font-sans font-normal">/ {statusData.total_planned_runs}</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            25 Planned Runs (5 Betas &times; 5 Seeds)
          </div>
        </div>

        {/* Evaluation Runs Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Confirmatory Evaluations</span>
            <Layers className="h-4 w-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold text-slate-900 font-mono">
            {statusData.completed_evaluations} <span className="text-xs text-slate-500 font-sans font-normal">/ {statusData.total_planned_evaluations}</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            10 Seeds / Completed Checkpoint
          </div>
        </div>
      </div>

      {/* Live Reward Progression Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-teal-600" />
              <span>Live Training Progression: {historyData?.run_key || currentRun.run_key || 'beta_000_seed101'}</span>
            </h3>
            <p className="text-[11px] text-slate-500">
              Streaming multi-agent reward curve & travel time progression recorded during training.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded bg-teal-50 text-teal-800 font-mono border border-teal-200">
              Live Stream &bull; Ep 1..{currentEp}
            </span>
          </div>
        </div>

        {historyEpisodes.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="h-56">
              <div className="text-xs font-semibold text-slate-600 mb-2">Mean Mixed Reward (Higher is better)</div>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historyEpisodes} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="episode" tick={{ fontSize: 10, fill: '#475569' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                  <Tooltip
                    formatter={(val) => [Number(val).toFixed(2), 'Reward']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="mean_reward" stroke="#0d9488" fill="#ccfbf1" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="h-56">
              <div className="text-xs font-semibold text-slate-600 mb-2">Corridor Travel Time (s) (Lower is better)</div>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historyEpisodes} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="episode" tick={{ fontSize: 10, fill: '#475569' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                  <Tooltip
                    formatter={(val) => [`${Number(val).toFixed(1)}s`, 'Travel Time']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="travel_time_mean_s" stroke="#6366f1" fill="#e0e7ff" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-8 text-center text-slate-500 text-xs">
            <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-teal-600" />
            <span>Streaming initial episode telemetry for active run... Periodic updates occur at episode milestones.</span>
          </div>
        )}
      </div>

      {/* 25-Run Workload Manifest Matrix */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Series 4C Master Execution Manifest (25 Confirmatory Runs)
            </h3>
            <p className="text-[11px] text-slate-500">
              Complete status matrix across all five &beta; values and training seeds 101&ndash;105.
            </p>
          </div>
          <span className="text-[11px] text-slate-600 font-mono">
            {statusData.completed_training_runs} of 25 Runs Completed
          </span>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100/80 text-slate-700 uppercase font-bold text-[10px] tracking-wider sticky top-0 border-b border-slate-200 z-10">
              <tr>
                <th className="py-2.5 px-4">Run Key</th>
                <th className="py-2.5 px-3">Beta (&beta;)</th>
                <th className="py-2.5 px-3">Coupling Type</th>
                <th className="py-2.5 px-3 text-center">Train Seed</th>
                <th className="py-2.5 px-3">Training Status</th>
                <th className="py-2.5 px-3">Checkpoint Integrity</th>
                <th className="py-2.5 px-3 text-center">Evaluations</th>
                <th className="py-2.5 px-3 text-right">Wall Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {statusData.runs_summary.map((r) => {
                const isTraining = r.training_status === 'TRAINING';
                const isCompleted = r.training_status === 'COMPLETED';
                const couplingLabel =
                  r.beta === 0.0
                    ? 'Pure Local'
                    : r.beta === 0.25
                    ? 'Weak Coupling'
                    : r.beta === 0.5
                    ? 'Balanced (Default)'
                    : r.beta === 0.75
                    ? 'Strong Coupling'
                    : 'Pure Global';

                return (
                  <tr
                    key={r.run_key}
                    className={`hover:bg-slate-50 transition ${
                      isTraining ? 'bg-amber-50/40 font-semibold' : ''
                    }`}
                  >
                    <td className="py-2.5 px-4 font-mono text-slate-900">
                      {r.run_key}
                      {isTraining && (
                        <span className="ml-2 text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-bold">
                          ACTIVE
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-800">{r.beta.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-slate-600">{couplingLabel}</td>
                    <td className="py-2.5 px-3 text-center font-mono text-slate-700">{r.train_seed}</td>
                    <td className="py-2.5 px-3">
                      {isCompleted ? (
                        <span className="text-emerald-700 font-bold flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> COMPLETED
                        </span>
                      ) : isTraining ? (
                        <span className="text-amber-700 font-bold flex items-center gap-1 animate-pulse">
                          <Activity className="h-3 w-3" /> TRAINING (Ep {currentEp}/150)
                        </span>
                      ) : (
                        <span className="text-slate-400 font-medium">PENDING</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      {r.has_checkpoint ? (
                        <span className="text-emerald-700 font-mono text-[11px] flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Verified SHA-256
                        </span>
                      ) : (
                        <span className="text-slate-400 font-mono text-[11px]">&mdash;</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      {r.evaluations_completed} / {r.evaluations_target}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-600">
                      {r.training_wall_time_s > 0 ? `${(r.training_wall_time_s / 60).toFixed(1)}m` : '&mdash;'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Execution Events Terminal Feed */}
      {statusData.recent_events?.length > 0 && (
        <div className="bg-slate-950 text-slate-200 border border-slate-800 rounded-xl p-4 shadow-sm font-mono text-xs">
          <div className="flex items-center gap-2 text-slate-400 text-[11px] border-b border-slate-800 pb-2 mb-2">
            <Terminal className="h-3.5 w-3.5 text-teal-400" />
            <span>Master Execution Log Feed (`series_4c_execution.log`)</span>
          </div>
          <div className="space-y-1 overflow-x-auto max-h-36 text-[11px]">
            {statusData.recent_events.map((ev, i) => (
              <div key={i} className="text-slate-300">
                {ev}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
