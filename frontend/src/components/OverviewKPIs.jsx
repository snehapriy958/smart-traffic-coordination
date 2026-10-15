import React from 'react';
import { Car, Gauge, Clock, GitCommit, Wind, Fuel, MapPin, Hourglass } from 'lucide-react';

export function OverviewKPIs({ metrics, simStatus, readingAge }) {
  const isRunning = simStatus?.running && !simStatus?.paused;

  // Helper: return formatted string if value exists (including 0), else return em dash '—'
  const val = (v, suffix = '', precision = null) => {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'number') {
      const formatted = precision !== null ? v.toFixed(precision) : v;
      return `${formatted}${suffix}`;
    }
    return `${v}${suffix}`;
  };

  // Calculate average waiting time per vehicle if both metrics exist
  const avgWaitPerVehicle =
    metrics?.total_corridor_waiting_time_s != null &&
    metrics?.total_vehicles != null &&
    metrics.total_vehicles > 0
      ? (metrics.total_corridor_waiting_time_s / metrics.total_vehicles).toFixed(1)
      : null;

  const kpis = [
    {
      title: 'Intersections',
      value: '3 / 3',
      sub: 'J1, J2 (Silk Board), J3',
      icon: MapPin,
      color: 'text-blue-600',
      border: 'border-blue-200',
      bg: 'bg-blue-50/50',
    },
    {
      title: 'Active Vehicles',
      value: val(metrics?.total_vehicles),
      sub: isRunning ? 'Real-time observation' : (metrics ? 'Simulation paused/stopped' : 'Waiting for telemetry'),
      icon: Car,
      color: 'text-indigo-600',
      border: 'border-indigo-200',
      bg: 'bg-indigo-50/50',
    },
    {
      title: 'Throughput',
      value: val(metrics?.throughput_vehicles),
      sub: 'Completed corridor trips',
      icon: GitCommit,
      color: 'text-emerald-600',
      border: 'border-emerald-200',
      bg: 'bg-emerald-50/50',
    },
    {
      title: 'Average Speed',
      value: val(metrics?.mean_speed_kmh, ' km/h'),
      sub: 'Corridor progression rate',
      icon: Gauge,
      color: 'text-cyan-600',
      border: 'border-cyan-200',
      bg: 'bg-cyan-50/50',
    },
    {
      title: 'Total Waiting Time',
      value: val(metrics?.total_corridor_waiting_time_s, 's'),
      sub: avgWaitPerVehicle ? `Avg: ${avgWaitPerVehicle}s / veh` : `Queue: ${val(metrics?.mean_corridor_queue, ' veh')}`,
      icon: Clock,
      color: 'text-amber-600',
      border: 'border-amber-200',
      bg: 'bg-amber-50/50',
    },
    {
      title: 'CO₂ Emissions',
      value: val(metrics?.total_co2_kg, ' kg'),
      sub: `NOx: ${val(metrics?.total_nox_g, ' g')}`,
      icon: Wind,
      color: 'text-teal-600',
      border: 'border-teal-200',
      bg: 'bg-teal-50/50',
    },
    {
      title: 'Fuel Consumed',
      value: val(metrics?.total_fuel_liters, ' L'),
      sub: 'SUMO converted liters',
      icon: Fuel,
      color: 'text-purple-600',
      border: 'border-purple-200',
      bg: 'bg-purple-50/50',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        const isMissing = kpi.value === '—';
        return (
          <div
            key={index}
            className={`p-3.5 rounded-xl border ${kpi.border} ${kpi.bg} bg-white shadow-sm flex flex-col justify-between transition hover:shadow-md`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {kpi.title}
              </span>
              <Icon className={`h-4 w-4 ${kpi.color}`} />
            </div>
            <div>
              <div className={`text-xl font-bold tracking-tight font-mono ${isMissing ? 'text-slate-400 font-normal' : 'text-slate-900'}`}>
                {kpi.value}
              </div>
              <p className="text-[11px] text-slate-500 truncate mt-0.5">
                {kpi.sub}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
