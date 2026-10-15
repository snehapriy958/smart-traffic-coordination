import React from 'react';
import { GitCompare, CheckCircle2, XCircle, Info, Clock, AlertCircle } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

export function ControllerComparison({ compareData }) {
  const controllers = compareData?.controllers || [];
  const networkName = compareData?.network || 'Silk Board Corridor (J1 -> J2 -> J3)';
  const durationS = compareData?.benchmark_duration_s || 600;

  // Build chart dynamically from the EXACT same API response as the table
  const metricConfigs = [
    { key: 'mean_travel_time_s', label: 'Travel Time (s)', unit: 's' },
    { key: 'total_waiting_time_s', label: 'Waiting Time (s)', unit: 's' },
    { key: 'mean_queue', label: 'Mean Queue (veh)', unit: 'veh' },
    { key: 'mean_speed_kmh', label: 'Mean Speed (km/h)', unit: 'km/h' },
    { key: 'total_co2_kg', label: 'Total CO₂ (kg)', unit: 'kg' },
    { key: 'emergency_traversal_duration_s', label: 'Ambulance Clearance (s)', unit: 's' },
  ];

  const chartData = metricConfigs.map(({ key, label, unit }) => {
    const row = { metric: label, unit };
    controllers.forEach((ctrl) => {
      // Leave unavailable/prototype values blank (null)
      const val = ctrl[key];
      row[ctrl.controller_name] = val !== null && val !== undefined ? val : null;
    });
    return row;
  });

  // Color mapping for controllers
  const getControllerColor = (name) => {
    if (name.includes('Baseline')) return '#64748b'; // Slate gray
    if (name.includes('Coordinated')) return '#2563eb'; // Royal blue
    if (name.includes('PPO')) return '#0d9488'; // Teal
    if (name.includes('DQN')) return '#7c3aed'; // Purple
    return '#3b82f6';
  };

  const val = (v, suffix = '', precision = null) => {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'number') {
      const formatted = precision !== null ? v.toFixed(precision) : v;
      return `${formatted}${suffix}`;
    }
    return `${v}${suffix}`;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      {/* Header with Benchmark Source & Duration */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="h-5 w-5 text-blue-600" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Empirical Benchmark Comparison
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <Clock className="h-3.5 w-3.5 text-blue-600" />
          <span className="font-semibold text-slate-800">Source:</span>
          <span>{networkName} &bull; {durationS}s Multi-Seed SUMO Benchmark</span>
        </div>
      </div>

      {/* Comparison Chart — Built Dynamically from API Response */}
      <div className="h-72 w-full mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Verified Controller Performance Comparison (Lower is Better, except Speed)
          </h3>
          <span className="text-[11px] text-slate-500 italic">
            Chart data bound to unified API endpoint (/api/experiments/compare)
          </span>
        </div>

        {controllers.length === 0 ? (
          <div className="h-56 flex items-center justify-center text-xs text-slate-400 italic border border-dashed border-slate-200 rounded-lg">
            Loading benchmark dataset...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 10 }} angle={-10} textAnchor="end" />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#cbd5e1',
                  borderRadius: '0.5rem',
                  fontSize: '11px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  color: '#0f172a',
                }}
                formatter={(value, name) => [
                  value !== null && value !== undefined ? `${value}` : 'Prototype (Evaluation Pending)',
                  name,
                ]}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              {/* Render bars for implemented controllers with measured values */}
              {controllers.map((ctrl) => {
                const isMeasured = ctrl.mean_travel_time_s !== null && ctrl.mean_travel_time_s !== undefined;
                if (!isMeasured) return null; // Leave unverified prototype bars blank
                return (
                  <Bar
                    key={ctrl.controller_name}
                    dataKey={ctrl.controller_name}
                    fill={getControllerColor(ctrl.controller_name)}
                    radius={[4, 4, 0, 0]}
                  />
                );
              })}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Benchmarks Table — Single Source of Truth */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
          <thead className="bg-slate-50 text-slate-700 text-[11px] uppercase font-semibold border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Controller Architecture</th>
              <th className="py-2.5 px-3">Implementation Status</th>
              <th className="py-2.5 px-3">Travel Time</th>
              <th className="py-2.5 px-3">Mean Speed</th>
              <th className="py-2.5 px-3">Wait Time</th>
              <th className="py-2.5 px-3">Corridor Queue</th>
              <th className="py-2.5 px-3">CO₂ / Fuel</th>
              <th className="py-2.5 px-3">Ambulance Traversal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {controllers.map((ctrl, i) => {
              const isImplemented = ctrl.status === 'Implemented';
              const isPrototype = ctrl.status.toLowerCase().includes('prototype');
              return (
                <tr
                  key={i}
                  className={`hover:bg-slate-50 transition ${
                    isImplemented ? 'bg-white' : 'bg-slate-50/60'
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-slate-900 font-sans">
                    <div className="text-xs font-bold">{ctrl.controller_name}</div>
                    <div className="text-[10px] text-slate-500 font-normal mt-0.5 max-w-xs line-clamp-1">
                      {ctrl.description}
                    </div>
                  </td>
                  <td className="py-3 px-3 font-sans">
                    {isImplemented ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                        <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                        <span>Implemented (Measured)</span>
                      </span>
                    ) : isPrototype ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-300">
                        <AlertCircle className="h-3 w-3 text-blue-600" />
                        <span>Prototype (Eval Pending)</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-300">
                        <XCircle className="h-3 w-3 text-rose-600" />
                        <span>Not Implemented</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-800 font-medium">
                    {val(ctrl.mean_travel_time_s, 's')}
                  </td>
                  <td className="py-3 px-3 text-blue-700 font-bold">
                    {val(ctrl.mean_speed_kmh, ' km/h')}
                  </td>
                  <td className="py-3 px-3 text-slate-800">
                    {val(ctrl.total_waiting_time_s, 's')}
                  </td>
                  <td className="py-3 px-3 text-slate-800">
                    {val(ctrl.mean_queue, ' veh')}
                  </td>
                  <td className="py-3 px-3 text-slate-800">
                    {ctrl.total_co2_kg != null ? `${ctrl.total_co2_kg} kg` : '—'}
                  </td>
                  <td className="py-3 px-3 text-emerald-700 font-bold">
                    {val(ctrl.emergency_traversal_duration_s, 's')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Explanatory notes on Provenance and Prototypes */}
      <div className="p-3 bg-blue-50/50 border border-blue-200 rounded-lg text-xs text-slate-700">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold text-slate-900">Academic &amp; Technical Integrity Statement:</p>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Baseline and Coordinated Adaptive metrics are empirically measured from 5-seed SUMO simulation runs along the Silk Board corridor (Hosur Rd J1 &rarr; J2 &rarr; J3).
              The MARL decision architectures (PPO Actor-Critic and Dueling Double-DQN) are fully implemented in <code className="text-blue-700 bg-white px-1 py-0.5 rounded border border-blue-200 font-mono">traffic_service/ai/</code> with replay buffer, observation vectorizer, GAE advantages, and action masking.
              In accordance with research integrity standards, their benchmark metrics remain unverified prototypes (displayed as blank / em dash) until actual multi-seed simulation training runs and converged checkpoints are evaluated.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
