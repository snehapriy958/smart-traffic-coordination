import React, { useState, useEffect } from 'react';
import { Wind, Fuel, BarChart3, TrendingDown, Info } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

export function EmissionAnalytics({ metrics }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (metrics?.simulation_time > 0) {
      setHistory((prev) => {
        const item = {
          time: Number(metrics.simulation_time.toFixed(0)),
          co2_kg: metrics.total_co2_kg != null ? Number(metrics.total_co2_kg.toFixed(2)) : 0,
          fuel_liters: metrics.total_fuel_liters != null ? Number(metrics.total_fuel_liters.toFixed(2)) : 0,
          nox_g: metrics.total_nox_g != null ? Number(metrics.total_nox_g.toFixed(2)) : 0,
        };
        const updated = [...prev, item];
        // Keep last 30 data points
        return updated.slice(-30);
      });
    }
  }, [metrics?.simulation_time]);

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
      {/* Title & Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Wind className="h-5 w-5 text-teal-600" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Corridor Emissions & Environmental Analytics
          </h2>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
          <span>CO₂: kg</span>
          <span>&bull;</span>
          <span>NOx: g</span>
          <span>&bull;</span>
          <span>Fuel: Liters (SUMO converted)</span>
        </div>
      </div>

      {/* Primary KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Cumulative CO₂</span>
            <Wind className="h-4 w-4 text-teal-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {val(metrics?.total_co2_kg, ' kg')}
          </div>
          <p className="text-[11px] text-teal-700 flex items-center gap-1 mt-1 font-medium">
            <TrendingDown className="h-3 w-3" />
            <span>Benchmark (600s run): 20.6% CO₂ reduction vs baseline</span>
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Cumulative NOx</span>
            <Wind className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {val(metrics?.total_nox_g, ' g')}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            HBEFA 3.1 empirical emission model
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Total Fuel Consumed</span>
            <Fuel className="h-4 w-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900">
            {val(metrics?.total_fuel_liters, ' L')}
          </div>
          <p className="text-[11px] text-purple-700 flex items-center gap-1 mt-1 font-medium">
            <TrendingDown className="h-3 w-3" />
            <span>Benchmark (600s run): 20.5% fuel saved vs baseline</span>
          </p>
        </div>
      </div>

      {/* Chart: BOTH CO2 and Fuel Plotted with Dual Y-Axes */}
      <div className="h-64 w-full">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Real-Time Cumulative CO₂ & Fuel Accumulation Curve
          </h3>
          <span className="text-[11px] text-slate-500 italic">
            Dual Series: CO₂ (kg, left axis) &amp; Fuel (Liters, right axis)
          </span>
        </div>

        {history.length < 2 ? (
          <div className="h-52 flex flex-col items-center justify-center text-xs text-slate-400 italic border border-dashed border-slate-200 rounded-lg bg-slate-50">
            <span>Awaiting simulation telemetry data points...</span>
            <span className="text-[11px] text-slate-400 not-italic mt-1">
              Start simulation from controls above to stream live accumulation curves
            </span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="co2GradLight" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="fuelGradLight" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} unit="s" />
              {/* Left YAxis: CO2 */}
              <YAxis
                yAxisId="left"
                stroke="#0d9488"
                tick={{ fontSize: 10 }}
                label={{ value: 'CO₂ (kg)', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#0d9488' }}
              />
              {/* Right YAxis: Fuel */}
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#7c3aed"
                tick={{ fontSize: 10 }}
                label={{ value: 'Fuel (L)', angle: 90, position: 'insideRight', fontSize: 10, fill: '#7c3aed' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#cbd5e1',
                  borderRadius: '0.5rem',
                  fontSize: '11px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  color: '#0f172a',
                }}
                formatter={(val, name) => [`${val} ${name.includes('CO₂') ? 'kg' : 'L'}`, name]}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
              {/* Series 1: CO2 */}
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="co2_kg"
                name="CO₂ Emissions (kg)"
                stroke="#0d9488"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#co2GradLight)"
              />
              {/* Series 2: Fuel */}
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="fuel_liters"
                name="Fuel Consumed (L)"
                stroke="#7c3aed"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#fuelGradLight)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
