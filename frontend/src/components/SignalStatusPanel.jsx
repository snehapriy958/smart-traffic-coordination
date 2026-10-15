import React from 'react';
import { TrafficCone, Clock, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';

export function SignalStatusPanel({ signals, junctions, readingAge }) {
  const junctionList = [
    { id: 'J1', name: 'J1 Hosur Feeder (North)', tls: '1617743335' },
    { id: 'J2', name: 'J2 Silk Board Central', tls: 'GS_cluster_10282769895...' },
    { id: 'J3', name: 'J3 Hosur Feeder (South)', tls: '6970466614' },
  ];

  // Helper: return formatted string if value exists, else '—'
  const val = (v, suffix = '', precision = null) => {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'number') {
      const formatted = precision !== null ? v.toFixed(precision) : v;
      return `${formatted}${suffix}`;
    }
    return `${v}${suffix}`;
  };

  const getPhaseName = (junctionId, phase) => {
    if (phase === null || phase === undefined) {
      return 'Waiting for signal telemetry...';
    }
    if (junctionId === 'J2') {
      if (phase === 0) return 'Phase 0: Hosur Corridor Green';
      if (phase === 1) return 'Phase 1: Hosur Yellow Transition';
      if (phase === 2) return 'Phase 2: Madiwala Road Green';
      if (phase === 3) return 'Phase 3: Madiwala Yellow Transition';
    } else {
      if (phase === 2) return 'Phase 2: Hosur Corridor Green';
      if (phase === 3) return 'Phase 3: Hosur Yellow Transition';
      if (phase === 0) return 'Phase 0: Side Cross Green';
      if (phase === 1) return 'Phase 1: Side Yellow Transition';
    }
    return `Phase ${phase}`;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <TrafficCone className="h-5 w-5 text-amber-500" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Telemetry
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-mono">
            {readingAge != null
              ? (readingAge < 5 ? `Updated ${readingAge}s ago` : `Last reading: ${readingAge}s ago`)
              : 'Awaiting signal feed'}
          </span>
          <span className="text-slate-300">&bull;</span>
          <span className="text-slate-500">
            Min/Max Green Bounds & Yellow Clearance Enforced
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {junctionList.map((junc) => {
          const sig = signals?.[junc.id];
          const st = junctions?.[junc.id];

          // Determine signal state strictly without defaulting to red
          const hasSignalData = sig !== null && sig !== undefined && (sig.is_green !== undefined || sig.is_yellow !== undefined || sig.is_red !== undefined);
          const isGreen = hasSignalData && Boolean(sig.is_green);
          const isYellow = hasSignalData && Boolean(sig.is_yellow);
          const isRed = hasSignalData && (Boolean(sig.is_red) || (!isGreen && !isYellow && sig.current_phase !== undefined));
          
          const isCongested = (st?.total_queue ?? 0) > 10;
          const isEmergencyLocked = Boolean(sig?.emergency_locked);

          return (
            <div
              key={junc.id}
              className={`rounded-xl border p-4 bg-white transition relative ${
                isCongested
                  ? 'border-rose-300 shadow-sm shadow-rose-100 ring-1 ring-rose-200'
                  : isEmergencyLocked
                  ? 'border-rose-400 bg-rose-50/30'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="h-6 w-6 rounded bg-slate-100 text-blue-700 font-mono font-bold text-xs flex items-center justify-center border border-slate-200">
                    {junc.id}
                  </span>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">{junc.name}</h3>
                    <p className="text-[10px] text-slate-500 font-mono truncate">{junc.tls}</p>
                  </div>
                </div>

                {/* Emergency Lock Pill */}
                {isEmergencyLocked ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">
                    EMERGENCY LOCK
                  </span>
                ) : !hasSignalData ? (
                  <span className="px-1.5 py-0.5 rounded text-[10px] text-slate-500 bg-slate-100 border border-slate-200">
                    Awaiting data
                  </span>
                ) : null}
              </div>

              {/* Traffic Light Head Visualizer */}
              <div className="bg-slate-100 border border-slate-200 rounded-lg p-2.5 flex items-center justify-around mb-3">
                {/* Red Light */}
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                      isRed
                        ? 'bg-rose-500 border-rose-600 shadow-md shadow-rose-400/50'
                        : 'bg-slate-200 border-slate-300 opacity-40'
                    }`}
                  />
                  <span className={`text-[9px] uppercase tracking-wider font-semibold ${isRed ? 'text-rose-700' : 'text-slate-400'}`}>
                    Red
                  </span>
                </div>

                {/* Yellow Light */}
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                      isYellow
                        ? 'bg-amber-400 border-amber-500 shadow-md shadow-amber-300/60'
                        : 'bg-slate-200 border-slate-300 opacity-40'
                    }`}
                  />
                  <span className={`text-[9px] uppercase tracking-wider font-semibold ${isYellow ? 'text-amber-700' : 'text-slate-400'}`}>
                    Yellow
                  </span>
                </div>

                {/* Green Light */}
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                      isGreen
                        ? 'bg-emerald-500 border-emerald-600 shadow-md shadow-emerald-400/50'
                        : 'bg-slate-200 border-slate-300 opacity-40'
                    }`}
                  />
                  <span className={`text-[9px] uppercase tracking-wider font-semibold ${isGreen ? 'text-emerald-700' : 'text-slate-400'}`}>
                    Green
                  </span>
                </div>
              </div>

              {/* Phase description */}
              <div className={`rounded px-2.5 py-1 text-xs font-mono mb-3 border text-center ${
                hasSignalData
                  ? 'bg-slate-50 text-slate-800 border-slate-200'
                  : 'bg-slate-100 text-slate-400 border-dashed border-slate-200 italic'
              }`}>
                {getPhaseName(junc.id, sig?.current_phase)}
              </div>

              {/* Timing meters */}
              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-500 block">Elapsed In Phase</span>
                  <span className="font-mono font-bold text-slate-900">
                    {val(sig?.phase_elapsed, 's', 1)}
                  </span>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-500 block">Min / Max Green</span>
                  <span className="font-mono text-slate-700">
                    {sig?.min_green != null ? `${sig.min_green}s / ${sig.max_green}s` : '—'}
                  </span>
                </div>
              </div>

              {/* Approach Queues */}
              <div className="text-xs pt-2 border-t border-slate-100">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-slate-500 text-[11px]">Total Junction Queue:</span>
                  <span className={`font-mono font-bold ${isCongested ? 'text-rose-700' : 'text-slate-800'}`}>
                    {val(st?.total_queue, ' veh')}
                  </span>
                </div>
                {st?.approach_queues ? (
                  Object.entries(st.approach_queues).map(([appr, q]) => (
                    <div key={appr} className="flex justify-between text-[11px] text-slate-600">
                      <span className="truncate max-w-[140px] capitalize">{appr.replace('_', ' ')}:</span>
                      <span className="font-mono">{val(q, ' veh')}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-[10px] text-slate-400 italic">No approach queue breakdown</div>
                )}
              </div>

              {/* Congestion warning banner */}
              {isCongested && (
                <div className="mt-2.5 p-1.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] flex items-center gap-1 font-medium">
                  <AlertTriangle className="h-3 w-3 flex-shrink-0 text-rose-600" />
                  <span>Heavy queue detected (&gt; 10 veh)</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
