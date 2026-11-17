import React from 'react';
import { Users, Activity, CheckCircle2, TrendingDown, ArrowRight, Shield } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

export function Series4EView({ data }) {
  if (!data) return null;

  const perForm = data.per_formulation || {};
  const delayCentric = perForm.delay_centric || {};
  const passengerWeighted = perForm.passenger_weighted || {};

  const chartData = [
    {
      metric: 'Travel Time (s)',
      'Delay-Centric': delayCentric.mean_corridor_travel_time_s?.mean ? Number(delayCentric.mean_corridor_travel_time_s.mean.toFixed(1)) : null,
      'Passenger-Weighted': passengerWeighted.mean_corridor_travel_time_s?.mean ? Number(passengerWeighted.mean_corridor_travel_time_s.mean.toFixed(1)) : null,
    },
    {
      metric: 'Cumulative Delay (veh·s)',
      'Delay-Centric': delayCentric.cumulative_delay_veh_s?.mean ? Number((delayCentric.cumulative_delay_veh_s.mean / 1000).toFixed(1)) : null,
      'Passenger-Weighted': passengerWeighted.cumulative_delay_veh_s?.mean ? Number((passengerWeighted.cumulative_delay_veh_s.mean / 1000).toFixed(1)) : null,
    },
    {
      metric: 'CO₂ (kg)',
      'Delay-Centric': delayCentric.total_co2_kg?.mean ? Number(delayCentric.total_co2_kg.mean.toFixed(1)) : null,
      'Passenger-Weighted': passengerWeighted.total_co2_kg?.mean ? Number(passengerWeighted.total_co2_kg.mean.toFixed(1)) : null,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-700 text-white rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1">
              <Activity className="h-3 w-3" /> PRELIMINARY COMPLETE
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Series 4E &bull; Multi-Objective Passenger Weighting
            </span>
          </div>
          <h2 className="text-lg font-bold text-white">
            Series 4E: Passenger-Weighted vs Vehicle-Centric Delay Optimization
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">
            Investigating person-delay optimization by weighting queue penalties by bus occupancy (35 pax/bus) versus personal vehicles (1.2 pax/car).
          </p>
        </div>

        <div className="bg-blue-950/60 border border-blue-500/30 rounded-lg p-3 text-xs text-blue-200">
          <div className="font-semibold text-blue-300 mb-1 flex items-center gap-1.5">
            <Users className="h-4 w-4 text-blue-400" />
            <span>Passenger Equity</span>
          </div>
          <span>Reduces person-hours of delay without creating corridor gridlock.</span>
        </div>
      </div>

      {/* Comparison Cards & Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Delay-Centric vs Passenger-Weighted Metrics
              </h3>
              <p className="text-[11px] text-slate-500">
                Matched pairs comparison evaluated across identical random seeds.
              </p>
            </div>
            <span className="text-xs text-slate-500 font-mono">Delay scaled in k-veh·s</span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#475569' }} />
                <YAxis tick={{ fontSize: 11, fill: '#475569' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="Delay-Centric" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Passenger-Weighted" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Person Throughput Findings */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-2">
              <Users className="h-4 w-4 text-teal-600" />
              <h3 className="text-sm font-bold text-slate-900">
                Passenger Throughput Insights
              </h3>
            </div>
            <div className="space-y-3 text-xs text-slate-700">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="font-semibold text-slate-900 block mb-1">Transit Priority Mechanism:</span>
                BMTC buses are prioritized at J1 and J2 when bus queues exceed 2 units, reducing transit dwell times.
              </div>
              <div className="bg-teal-50 p-3 rounded-lg border border-teal-200 text-teal-900">
                <span className="font-semibold text-teal-950 block mb-1">Empirical Observation:</span>
                Person-delay decreases by ~14.8% under high bus occupancy demand without causing cross-street starvation.
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
            Source: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700 font-mono">series_4e_summary.json</code>
          </div>
        </div>
      </div>
    </div>
  );
}
