import React, { useState } from 'react';
import { GitCompare, CheckCircle2, XCircle, Info, AlertCircle, Layers } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

const METRIC_DEFINITIONS = [
  { key: 'mean_travel_time_s', label: 'Corridor Travel Time (s)' },
  { key: 'mean_speed_kmh', label: 'Average Speed (km/h)' },
  { key: 'cumulative_delay_veh_s', label: 'Cumulative Delay (veh·s)' },
  { key: 'mean_queue', label: 'Mean Corridor Queue (veh)' },
  { key: 'total_co2_kg', label: 'Total CO₂ (kg)' },
  { key: 'total_fuel_liters', label: 'Estimated Fuel Volume (L)' },
  { key: 'completed_trips', label: 'Completed Corridor Trips' },
];

const CONTROLLER_COLORS = [
  '#64748b', // Slate for baseline
  '#0d9488', // Teal for coordinated
  '#d97706', // Amber for DQN
  '#7c3aed', // Violet/Purple for PPO
  '#059669', // Emerald
];

export function ControllerComparison({ compareData, isLoading = false, error = null }) {
  const [activeTab, setActiveTab] = useState('master_10s'); // 'master_10s' or 'hist_5s'

  // 1. Error state: API unavailable or call failed
  if (error) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3 mb-4">
          <GitCompare className="h-5 w-5 text-purple-600" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Empirical Benchmark Comparison
          </h2>
        </div>
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-full mb-3 text-rose-600">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">Benchmark Data Unavailable</h3>
          <p className="text-xs text-slate-500 max-w-md">
            {typeof error === 'string' ? error : 'Unable to retrieve controller benchmark comparison from backend API.'}
          </p>
        </div>
      </div>
    );
  }

  // 2. Loading state: Waiting for API response
  if (isLoading || (!compareData && !error)) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3 mb-4">
          <GitCompare className="h-5 w-5 text-purple-600 animate-pulse" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Empirical Benchmark Comparison
          </h2>
        </div>
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-teal-600 border-t-transparent mb-3" />
          <p className="text-xs font-mono text-slate-500">Loading empirical benchmark metrics...</p>
        </div>
      </div>
    );
  }

  const isMaster10s = activeTab === 'master_10s';
  const controllers = (isMaster10s ? compareData?.controllers : compareData?.historical_5seed_controllers) || compareData?.controllers || [];

  // 3. Empty state: API succeeded but no controllers returned
  if (controllers.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3 mb-4">
          <GitCompare className="h-5 w-5 text-purple-600" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Empirical Benchmark Comparison
          </h2>
        </div>
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <Info className="h-6 w-6 text-slate-400 mb-2" />
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No Benchmark Records Found</h3>
          <p className="text-xs text-slate-500">
            No controller benchmark records are currently registered for this corridor network.
          </p>
        </div>
      </div>
    );
  }

  // Filter controllers that have empirical data or are implemented
  const activeControllers = controllers.filter(
    (ctrl) => (ctrl.is_implemented ?? (ctrl.status?.toLowerCase().includes('implemented') || ctrl.status?.toLowerCase().includes('historical artifact'))) || ctrl.mean_travel_time_s != null
  );

  // Derive dynamic chart metrics from the active controllers
  const chartData = METRIC_DEFINITIONS.map(({ key, label }) => {
    const row = { metric: label };
    let hasValue = false;
    activeControllers.forEach((ctrl) => {
      const val = ctrl[key];
      if (val !== null && val !== undefined && !Number.isNaN(Number(val))) {
        row[ctrl.controller_name] = Number(val);
        hasValue = true;
      } else {
        row[ctrl.controller_name] = null;
      }
    });
    return hasValue ? row : null;
  }).filter(Boolean);

  const hasHistorical = compareData?.historical_5seed_controllers && compareData.historical_5seed_controllers.length > 0;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="h-5 w-5 text-purple-600" />
          <div>
            <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
              Signal Controller Empirical Benchmark Comparison
            </h2>
            <div className="text-[11px] text-slate-500 font-mono">
              {isMaster10s
                ? `Authoritative 10-Seed Master Benchmark • N=10 seeds • ${compareData?.benchmark_duration_s || 900}s duration • 109 corridor trips`
                : 'Historical Phase 2 Benchmark • N=5 seeds • 600s duration (Preserved)'}
            </div>
          </div>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {compareData?.network || 'Silk Board Corridor (J1 -> J2 -> J3)'}
        </span>
      </div>

      {/* Dataset Selection Tabs */}
      {hasHistorical && (
        <div className="flex items-center gap-2 mb-4 p-1 bg-slate-100 rounded-lg w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('master_10s')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              isMaster10s
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Authoritative 10-Seed Master Benchmark (N=10, 900s)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('hist_5s')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
              !isMaster10s
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Historical 5-Seed Benchmark (N=5, 600s Preserved)
          </button>
        </div>
      )}

      {/* Comparison Chart */}
      <div className="h-64 w-full mb-6">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
          Performance Comparison ({isMaster10s ? '10-Seed Master Benchmark' : 'Historical 5-Seed Benchmark'})
        </h3>
        <p className="text-[10px] text-slate-500 mb-2">
          Note: Fuel volumes are estimated gasoline equivalents (ρ = 0.75 kg/L). Lower is better for all metrics except Average Speed and Completed Trips.
        </p>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} angle={-15} textAnchor="end" />
              <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#e2e8f0',
                  color: '#0f172a',
                  borderRadius: '0.5rem',
                  fontSize: '11px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              {activeControllers.map((ctrl, idx) => (
                <Bar
                  key={ctrl.controller_name}
                  dataKey={ctrl.controller_name}
                  fill={CONTROLLER_COLORS[idx % CONTROLLER_COLORS.length]}
                  name={ctrl.controller_name}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs font-mono border border-dashed border-slate-200 rounded-lg">
            <Info className="h-5 w-5 mb-2 text-slate-400" />
            <span>No numeric performance metrics available to chart for current controllers.</span>
          </div>
        )}
      </div>

      {/* Benchmarks Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
          <thead className="bg-slate-100 text-slate-700 text-[11px] uppercase font-mono border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Controller Architecture</th>
              <th className="py-2.5 px-3">Implementation Status</th>
              <th className="py-2.5 px-3">Travel Time</th>
              <th className="py-2.5 px-3">Mean Speed</th>
              <th className="py-2.5 px-3">Delay</th>
              <th className="py-2.5 px-3">Queue</th>
              <th className="py-2.5 px-3">Completed Trips</th>
              <th className="py-2.5 px-3">CO₂ / Fuel Volume (L)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {controllers.map((ctrl, i) => {
              const isImplemented = Boolean(ctrl.is_implemented ?? (ctrl.status?.toLowerCase().startsWith('implemented') || ctrl.status === 'Implemented'));
              const isHistoricalArtifact = ctrl.status === 'Historical Artifact' || ctrl.status?.toLowerCase().includes('historical artifact');

              return (
                <tr
                  key={i}
                  className={`hover:bg-slate-50 transition ${
                    isImplemented ? 'bg-white' : 'bg-slate-50/50 opacity-75'
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-slate-900">
                    <div>{ctrl.controller_name}</div>
                    <div className="text-[10px] text-slate-500 font-sans mt-0.5 max-w-xs line-clamp-1">
                      {ctrl.description}
                    </div>
                    {/* Capability Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 mt-1 font-sans">
                      {ctrl.available_for_inference && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-sky-50 text-sky-700 border border-sky-200">
                          Live Inference
                        </span>
                      )}
                      {ctrl.has_trained_checkpoint && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-purple-50 text-purple-700 border border-purple-200">
                          Trained Checkpoint
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    {isHistoricalArtifact ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-300">
                        <Info className="h-3 w-3" />
                        <span>Historical Artifact</span>
                      </span>
                    ) : isImplemented ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>Implemented</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-300">
                        <XCircle className="h-3 w-3" />
                        <span>Not implemented</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-700">
                    {ctrl.mean_travel_time_s != null ? `${ctrl.mean_travel_time_s}s` : '—'}
                  </td>
                  <td className="py-3 px-3 text-teal-700 font-bold">
                    {ctrl.mean_speed_kmh != null ? `${ctrl.mean_speed_kmh} km/h` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-700">
                    {ctrl.cumulative_delay_veh_s != null ? `${ctrl.cumulative_delay_veh_s} veh·s` : (ctrl.total_waiting_time_s != null ? `${ctrl.total_waiting_time_s}s` : '—')}
                  </td>
                  <td className="py-3 px-3 text-slate-700">
                    {ctrl.mean_queue != null ? `${ctrl.mean_queue} veh` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-700 font-semibold">
                    {ctrl.completed_trips != null ? `${ctrl.completed_trips} / 109` : '—'}
                  </td>
                  <td className="py-3 px-3 text-slate-700">
                    {ctrl.total_co2_kg != null ? (
                      <div>
                        <div>{ctrl.total_co2_kg} kg CO₂</div>
                        {ctrl.total_fuel_liters != null && (
                          <div className="text-[10px] text-amber-700 font-semibold" title="Gasoline equivalent (ρ = 0.75 kg/L)">
                            {ctrl.total_fuel_liters} L (est. fuel)
                          </div>
                        )}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Benchmark Documentation & Context Note */}
      <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-teal-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-slate-900">
              {isMaster10s
                ? 'Authoritative 10-Seed Master Benchmark (N=10 seeds, 900s duration, 109 corridor trips):'
                : 'Historical 5-Seed Benchmark (N=5 seeds, 600s duration, Preserved):'}
            </p>
            <p className="text-[11px] text-slate-600">
              {isMaster10s
                ? 'Empirically evaluated across 10 random seeds with full network clearance (100% of 378 vehicles arrived; 109 arterial trips). Coordinated Adaptive achieves 49.87s travel time (-44.6% vs baseline). Double-DQN (Stage A) achieves 56.64s travel time (-37.1% vs baseline) with zero starvation. PPO (Stage A) achieves 85.50s with central junction J2 policy saturation. Note: MAPPO is evaluated in the Series 4 research ablation studies, not the 4-controller master benchmark.'
                : 'Preserved historical benchmark from Phase 2 development. In this early 8-episode prototype, DQN experienced side-street starvation (0 completed trips), which was subsequently resolved in the Stage A master benchmark.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
