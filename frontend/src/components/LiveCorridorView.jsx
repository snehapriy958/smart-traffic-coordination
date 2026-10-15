import React from 'react';
import { ShieldAlert, ArrowRight, WifiOff, ArrowDownRight, Layers, AlertTriangle } from 'lucide-react';

export function LiveCorridorView({ junctions, signals, emergencies, isStale, readingAge }) {
  const j1 = junctions?.J1;
  const j2 = junctions?.J2;
  const j3 = junctions?.J3;

  const s1 = signals?.J1;
  const s2 = signals?.J2;
  const s3 = signals?.J3;

  // Format value: if null or undefined, return '—'
  const val = (v, suffix = '', precision = null) => {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'number') {
      const formatted = precision !== null ? v.toFixed(precision) : v;
      return `${formatted}${suffix}`;
    }
    return `${v}${suffix}`;
  };

  const getSignalBadge = (sig) => {
    if (!sig || (sig.is_green === undefined && sig.is_yellow === undefined && sig.is_red === undefined)) {
      return { bg: 'bg-slate-100 text-slate-500 border-slate-300', dot: 'bg-slate-400', label: 'Waiting for signal data' };
    }
    if (sig.is_green) {
      return { bg: 'bg-emerald-50 text-emerald-800 border-emerald-300', dot: 'bg-emerald-500', label: `GREEN (P${sig.current_phase ?? 0})` };
    }
    if (sig.is_yellow) {
      return { bg: 'bg-amber-50 text-amber-800 border-amber-300', dot: 'bg-amber-500', label: `YELLOW (P${sig.current_phase ?? 0})` };
    }
    if (sig.is_red || (!sig.is_green && !sig.is_yellow && sig.current_phase !== undefined)) {
      return { bg: 'bg-rose-50 text-rose-800 border-rose-300', dot: 'bg-rose-500', label: `RED (P${sig.current_phase ?? 0})` };
    }
    return { bg: 'bg-slate-100 text-slate-500 border-slate-300', dot: 'bg-slate-400', label: 'Waiting for signal data' };
  };

  const getDensityBadge = (queue) => {
    if (queue === null || queue === undefined) return 'text-slate-400 bg-slate-100 border-slate-200';
    if (queue <= 2) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (queue <= 7) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200 font-bold';
  };

  const hasEmergency = emergencies?.active_emergency;
  const lockedJunctions = emergencies?.emergency_locked_junctions || [];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-slate-200 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
              Silk Board Corridor Live Topology
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              Directional Progression: J1 &rarr; J2 &rarr; J3
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Hosur Road Arterial &bull; Real SUMO edges: 172853382#2 &rarr; 172853382#3 &rarr; 1148717038#0 &rarr; 40696223#1
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Stale Data Warning */}
          {isStale && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs">
              <WifiOff className="h-3.5 w-3.5 text-amber-600" />
              <span>Connection offline / Stale data</span>
            </div>
          )}

          {/* Emergency Wave Active */}
          {hasEmergency && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 text-rose-800 border border-rose-300 text-xs font-semibold animate-pulse">
              <ShieldAlert className="h-4 w-4 text-rose-600" />
              <span>Emergency Green Wave Active</span>
            </div>
          )}
        </div>
      </div>

      {/* Clear Directional Corridor Progression Diagram */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-4">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-600 mb-2 px-1">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-blue-600" />
            North Corridor Inflow (Hosur Rd)
          </span>
          <span className="flex items-center gap-1 text-blue-700 font-mono">
            <span>TRAFFIC FLOW DIRECTION</span>
            <ArrowRight className="h-4 w-4" />
          </span>
          <span className="flex items-center gap-1.5">
            South Corridor Outflow (Electronic City)
            <span className="h-2 w-2 rounded-full bg-emerald-600" />
          </span>
        </div>

        {/* 3-Junction Horizontal Directional Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-11 gap-3 items-stretch">
          
          {/* =========================================
              JUNCTION 1 (J1 - Upstream North Feeder)
              ========================================= */}
          <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="h-7 w-7 rounded-lg bg-blue-100 text-blue-800 font-mono font-bold text-xs flex items-center justify-center border border-blue-200 shadow-xs">
                    J1
                  </span>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">
                      Hosur Rd North Feeder
                    </h3>
                    <span className="text-[10px] text-slate-500 font-mono">TLS: 1617743335</span>
                  </div>
                </div>
              </div>

              {/* Signal Status */}
              <div className="mb-3">
                <div className={`px-2.5 py-1 rounded border text-xs flex items-center gap-1.5 font-medium ${getSignalBadge(s1).bg}`}>
                  <span className={`h-2 w-2 rounded-full ${getSignalBadge(s1).dot}`} />
                  <span>{getSignalBadge(s1).label}</span>
                </div>
              </div>

              {/* Approach Edges */}
              <div className="bg-slate-50 rounded-lg p-2 text-[10px] space-y-1 mb-3 border border-slate-200">
                <div className="flex justify-between text-slate-600">
                  <span className="font-semibold">Inflow Edge:</span>
                  <span className="font-mono text-slate-800">172853382#2 (North)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span className="font-semibold">Cross Street:</span>
                  <span className="font-mono text-slate-800">-148697299_0 (Side)</span>
                </div>
                <div className="flex justify-between text-blue-700 font-semibold pt-1 border-t border-slate-200">
                  <span>Outflow to J2:</span>
                  <span className="font-mono">172853382#3 &rarr;</span>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs pt-2 border-t border-slate-100">
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Vehicles</span>
                <span className="font-mono font-bold text-slate-900">{val(j1?.vehicle_count)}</span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Queue</span>
                <span className={`px-1 rounded text-[11px] font-mono border inline-block ${getDensityBadge(j1?.total_queue)}`}>
                  {val(j1?.total_queue, ' veh')}
                </span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Avg Speed</span>
                <span className="font-mono text-slate-800">{val(j1?.average_speed_kmh, ' km/h')}</span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Wait Time</span>
                <span className="font-mono text-slate-800">{val(j1?.total_waiting_time, 's')}</span>
              </div>
            </div>

            {lockedJunctions.includes('J1') && (
              <div className="mt-2 text-[10px] text-rose-700 font-semibold bg-rose-50 border border-rose-200 p-1 rounded text-center">
                Emergency Priority Locked
              </div>
            )}
          </div>

          {/* =========================================
              CONNECTING CORRIDOR LINK 1 -> 2
              ========================================= */}
          <div className="lg:col-span-1 flex flex-col items-center justify-center py-2 text-center">
            <div className="hidden lg:flex flex-col items-center gap-1 w-full">
              <div className="text-[9px] font-mono font-bold text-blue-700 uppercase tracking-wider">
                Edge 172853382#3
              </div>
              <div className="w-full flex items-center justify-center gap-1 text-blue-600 my-1">
                <div className="h-0.5 flex-1 bg-gradient-to-r from-blue-300 via-blue-500 to-cyan-500" />
                <ArrowRight className="h-4 w-4 flex-shrink-0 animate-pulse text-blue-600" />
              </div>
              <span className="text-[9px] text-slate-500">400m Link</span>
            </div>
            {/* Mobile / wrap fallback arrow */}
            <div className="lg:hidden flex items-center justify-center gap-2 py-1 text-blue-600 text-xs font-mono font-bold">
              <span>Edge 172853382#3</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>

          {/* =========================================
              JUNCTION 2 (J2 - Central Silk Board Hub)
              ========================================= */}
          <div className="lg:col-span-3 bg-white border-2 border-blue-400 rounded-xl p-4 shadow-sm flex flex-col justify-between relative ring-2 ring-blue-50">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="h-7 w-7 rounded-lg bg-blue-600 text-white font-mono font-bold text-xs flex items-center justify-center shadow-xs">
                    J2
                  </span>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h3 className="text-xs font-bold text-slate-900 uppercase">
                        Silk Board Central
                      </h3>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-blue-100 text-blue-800 border border-blue-300">
                        PRIMARY HUB
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">TLS: GS_cluster_1028...</span>
                  </div>
                </div>
              </div>

              {/* Signal Status */}
              <div className="mb-3">
                <div className={`px-2.5 py-1 rounded border text-xs flex items-center gap-1.5 font-medium ${getSignalBadge(s2).bg}`}>
                  <span className={`h-2 w-2 rounded-full ${getSignalBadge(s2).dot}`} />
                  <span>{getSignalBadge(s2).label}</span>
                </div>
              </div>

              {/* Approach Edges */}
              <div className="bg-blue-50/50 rounded-lg p-2 text-[10px] space-y-1 mb-3 border border-blue-100">
                <div className="flex justify-between text-slate-700">
                  <span className="font-semibold">Corridor Inflow:</span>
                  <span className="font-mono text-blue-800">172853382#3 (from J1)</span>
                </div>
                <div className="flex justify-between text-slate-700">
                  <span className="font-semibold">Cross Feeder:</span>
                  <span className="font-mono text-slate-800">Madiwala Approach</span>
                </div>
                <div className="flex justify-between text-blue-700 font-semibold pt-1 border-t border-blue-200">
                  <span>Outflow to J3:</span>
                  <span className="font-mono">1148717038#0 &rarr;</span>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs pt-2 border-t border-slate-100">
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Vehicles</span>
                <span className="font-mono font-bold text-slate-900">{val(j2?.vehicle_count)}</span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Corridor Queue</span>
                <span className={`px-1 rounded text-[11px] font-mono border inline-block ${getDensityBadge(j2?.approach_queues?.corridor_hosur ?? j2?.total_queue)}`}>
                  {val(j2?.approach_queues?.corridor_hosur ?? j2?.total_queue, ' veh')}
                </span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Madiwala Queue</span>
                <span className={`px-1 rounded text-[11px] font-mono border inline-block ${getDensityBadge(j2?.approach_queues?.madiwala)}`}>
                  {val(j2?.approach_queues?.madiwala, ' veh')}
                </span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Avg Speed</span>
                <span className="font-mono font-bold text-blue-700">{val(j2?.average_speed_kmh, ' km/h')}</span>
              </div>
            </div>

            {/* Inflow Coordination Note */}
            <div className="mt-2 text-[10px] text-slate-600 bg-slate-50 border border-slate-200 p-1.5 rounded flex items-center justify-between">
              <span>Coordinated Inflow: J1 arrivals factored</span>
              {lockedJunctions.includes('J2') ? (
                <span className="text-rose-700 font-bold animate-pulse">&bull; Preemption Locked</span>
              ) : (
                <span className="text-emerald-700 font-semibold">&bull; Active</span>
              )}
            </div>
          </div>

          {/* =========================================
              CONNECTING CORRIDOR LINK 2 -> 3
              ========================================= */}
          <div className="lg:col-span-1 flex flex-col items-center justify-center py-2 text-center">
            <div className="hidden lg:flex flex-col items-center gap-1 w-full">
              <div className="text-[9px] font-mono font-bold text-blue-700 uppercase tracking-wider">
                Edge 1148717038#0
              </div>
              <div className="w-full flex items-center justify-center gap-1 text-blue-600 my-1">
                <div className="h-0.5 flex-1 bg-gradient-to-r from-blue-300 via-blue-500 to-emerald-500" />
                <ArrowRight className="h-4 w-4 flex-shrink-0 animate-pulse text-blue-600" />
              </div>
              <span className="text-[9px] text-slate-500">350m Link</span>
            </div>
            {/* Mobile / wrap fallback arrow */}
            <div className="lg:hidden flex items-center justify-center gap-2 py-1 text-blue-600 text-xs font-mono font-bold">
              <span>Edge 1148717038#0</span>
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>

          {/* =========================================
              JUNCTION 3 (J3 - Downstream South Feeder)
              ========================================= */}
          <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="h-7 w-7 rounded-lg bg-blue-100 text-blue-800 font-mono font-bold text-xs flex items-center justify-center border border-blue-200 shadow-xs">
                    J3
                  </span>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase">
                      Hosur Rd South Feeder
                    </h3>
                    <span className="text-[10px] text-slate-500 font-mono">TLS: 6970466614</span>
                  </div>
                </div>
              </div>

              {/* Signal Status */}
              <div className="mb-3">
                <div className={`px-2.5 py-1 rounded border text-xs flex items-center gap-1.5 font-medium ${getSignalBadge(s3).bg}`}>
                  <span className={`h-2 w-2 rounded-full ${getSignalBadge(s3).dot}`} />
                  <span>{getSignalBadge(s3).label}</span>
                </div>
              </div>

              {/* Approach Edges */}
              <div className="bg-slate-50 rounded-lg p-2 text-[10px] space-y-1 mb-3 border border-slate-200">
                <div className="flex justify-between text-slate-600">
                  <span className="font-semibold">Inflow from J2:</span>
                  <span className="font-mono text-slate-800">1148717038#0 (North)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span className="font-semibold">Local Access:</span>
                  <span className="font-mono text-slate-800">South Approach Feeder</span>
                </div>
                <div className="flex justify-between text-emerald-700 font-semibold pt-1 border-t border-slate-200">
                  <span>Corridor Exit:</span>
                  <span className="font-mono">40696223#1 (Electronic City)</span>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs pt-2 border-t border-slate-100">
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Vehicles</span>
                <span className="font-mono font-bold text-slate-900">{val(j3?.vehicle_count)}</span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Queue</span>
                <span className={`px-1 rounded text-[11px] font-mono border inline-block ${getDensityBadge(j3?.total_queue)}`}>
                  {val(j3?.total_queue, ' veh')}
                </span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Avg Speed</span>
                <span className="font-mono text-slate-800">{val(j3?.average_speed_kmh, ' km/h')}</span>
              </div>
              <div className="bg-slate-50 p-1.5 rounded border border-slate-100">
                <span className="text-[10px] text-slate-500 block">Exit Edge</span>
                <span className="font-mono text-slate-700 text-[10px]">40696223#1</span>
              </div>
            </div>

            {lockedJunctions.includes('J3') && (
              <div className="mt-2 text-[10px] text-rose-700 font-semibold bg-rose-50 border border-rose-200 p-1 rounded text-center">
                Emergency Priority Locked
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
