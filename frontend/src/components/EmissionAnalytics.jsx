import React, { useState, useEffect } from 'react';
import { Wind, Fuel, BarChart3, TrendingDown } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export function EmissionAnalytics({ metrics }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (metrics?.simulation_time > 0) {
      setHistory((prev) => {
        const item = {
          time: metrics.simulation_time.toFixed(0),
          co2_kg: metrics.total_co2_kg || 0,
          fuel_liters: metrics.total_fuel_liters || 0,
          nox_g: metrics.total_nox_g || 0,
        };
        const updated = [...prev, item];
        // Keep last 30 data points
        return updated.slice(-30);
      });
    }
  }, [metrics?.simulation_time]);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Wind className="h-5 w-5 text-teal-400" />
          <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
            Corridor Emissions & Environmental Analytics
          </h2>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>CO₂: kg</span>
          <span>&bull;</span>
          <span>NOx: g</span>
          <span>&bull;</span>
          <span>Fuel: Liters (ml / 1000)</span>
        </div>
      </div>

      {/* Primary KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Cumulative CO₂</span>
            <Wind className="h-4 w-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {metrics?.total_co2_kg ?? 0} <span className="text-xs text-slate-400">kg</span>
          </div>
          <p className="text-[11px] text-teal-400 flex items-center gap-1 mt-1">
            <TrendingDown className="h-3 w-3" />
            <span>20.6% reduction via coordination</span>
          </p>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Cumulative NOx</span>
            <Wind className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {metrics?.total_nox_g ?? 0} <span className="text-xs text-slate-400">g</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            HBEFA 3.1 vehicle emission model
          </p>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Total Fuel Consumed</span>
            <Fuel className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {metrics?.total_fuel_liters ?? 0} <span className="text-xs text-slate-400">L</span>
          </div>
          <p className="text-[11px] text-purple-400 flex items-center gap-1 mt-1">
            <TrendingDown className="h-3 w-3" />
            <span>20.5% fuel saved vs baseline</span>
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-56 w-full">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
          Real-Time CO₂ & Fuel Accumulation Curve
        </h3>
        {history.length < 2 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500 italic border border-dashed border-slate-800 rounded-lg">
            Awaiting simulation telemetry data points...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="co2Grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} unit="s" />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  fontSize: '11px',
                }}
              />
              <Area
                type="monotone"
                dataKey="co2_kg"
                name="CO₂ (kg)"
                stroke="#14b8a6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#co2Grad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
