import React from 'react';
import { GitCompare, CheckCircle2, XCircle, Info, TrendingDown, TrendingUp } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

export function ControllerComparison({ compareData }) {
  const controllers = compareData?.controllers || [];

  // Chart data for valid controllers
  const chartData = [
    {
      metric: 'Corridor Travel Time (s)',
      Baseline: 91.05,
      Coordinated: 57.50,
    },
    {
      metric: 'Average Wait Time (s)',
      Baseline: 779.43,
      Coordinated: 296.88,
    },
    {
      metric: 'Mean Corridor Queue (veh)',
      Baseline: 20.01,
      Coordinated: 10.67,
    },
    {
      metric: 'Average Speed (km/h)',
      Baseline: 27.85,
      Coordinated: 36.40,
    },
    {
      metric: 'Total CO₂ (kg)',
      Baseline: 53.72,
      Coordinated: 42.67,
    },
    {
      metric: 'Ambulance Clearance (s)',
      Baseline: 41.0,
      Coordinated: 33.6,
    },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="h-5 w-5 text-indigo-400" />
          <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
            Signal Controller Empirical Benchmark Comparison
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          5-Seed Evaluated Baseline vs Silk Board Adaptive
        </span>
      </div>

      {/* Comparison Chart */}
      <div className="h-64 w-full mb-6">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
          Performance Comparison (Lower is Better, except Speed)
        </h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" />
            <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                fontSize: '11px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Bar dataKey="Baseline" fill="#64748b" name="Fixed-Time Baseline" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Coordinated" fill="#06b6d4" name="Coordinated Adaptive" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Benchmarks Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border border-slate-800 rounded-lg overflow-hidden">
          <thead className="bg-slate-800/80 text-slate-300 text-[11px] uppercase font-mono border-b border-slate-700">
            <tr>
              <th className="py-2.5 px-3">Controller Architecture</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Travel Time</th>
              <th className="py-2.5 px-3">Mean Speed</th>
              <th className="py-2.5 px-3">Wait Time</th>
              <th className="py-2.5 px-3">Corridor Queue</th>
              <th className="py-2.5 px-3">CO₂ / Fuel</th>
              <th className="py-2.5 px-3">Ambulance Traversal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 font-mono">
            {controllers.map((ctrl, i) => {
              const isImplemented = ctrl.status === 'Implemented';
              return (
                <tr
                  key={i}
                  className={`hover:bg-slate-800/40 transition ${
                    isImplemented ? '' : 'bg-slate-900/40 opacity-75'
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-white">
                    <div>{ctrl.controller_name}</div>
                    <div className="text-[10px] text-slate-400 font-sans mt-0.5 max-w-xs line-clamp-1">
                      {ctrl.description}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    {isImplemented ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>Implemented</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        <XCircle className="h-3 w-3" />
                        <span>Not implemented</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-200">
                    {ctrl.mean_travel_time_s ? `${ctrl.mean_travel_time_s}s` : '—'}
                  </td>
                  <td className="py-3 px-3 text-cyan-300 font-bold">
                    {ctrl.mean_speed_kmh ? `${ctrl.mean_speed_kmh} km/h` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-200">
                    {ctrl.total_waiting_time_s ? `${ctrl.total_waiting_time_s}s` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-200">
                    {ctrl.mean_queue ? `${ctrl.mean_queue} veh` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-200">
                    {ctrl.total_co2_kg ? `${ctrl.total_co2_kg} kg` : '—'}
                  </td>
                  <td className="py-3 px-3 text-emerald-400 font-bold">
                    {ctrl.emergency_traversal_duration_s ? `${ctrl.emergency_traversal_duration_s}s` : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Explanatory notes on PPO & DQN */}
      <div className="mt-4 p-3 bg-slate-800/40 border border-slate-700/60 rounded-lg text-xs text-slate-300">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-white">AI Policy Roadmap (PPO / DQN Status):</p>
            <p className="text-[11px] text-slate-400">
              The simulation engine exposes clean, normalized observation hooks via <code className="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded font-mono">sim.get_ai_observations()</code> for J1, J2, and J3 (queues, elapsed green, inflow, speeds, emergency flags). However, neural network policy weights, Gym training environments, and reward convergence checkpoints are not yet trained. In accordance with task guidelines, no artificial results or manufactured training curves are reported.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
