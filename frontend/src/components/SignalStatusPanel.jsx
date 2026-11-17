import React, { useState } from 'react';
import { TrafficCone, Clock, AlertTriangle, ShieldCheck, Brain, Activity, ChevronDown, ChevronUp } from 'lucide-react';

export function SignalStatusPanel({ signals, junctions, decisions = [], simStatus = {} }) {
  const [expandedJunctions, setExpandedJunctions] = useState({ J1: false, J2: true, J3: false });

  const toggleJunction = (jId) => {
    setExpandedJunctions((prev) => ({
      ...prev,
      [jId]: !prev[jId],
    }));
  };

  const junctionList = [
    { id: 'J1', name: 'J1 Hosur Feeder (North)', tls: '1617743335' },
    { id: 'J2', name: 'J2 Silk Board Central', tls: 'GS_cluster_10282769895...' },
    { id: 'J3', name: 'J3 Hosur Feeder (South)', tls: '6970466614' },
  ];

  const getPhaseName = (junctionId, phase) => {
    if (phase == null) return 'N/A';
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

  const isRunning = Boolean(simStatus?.running);
  const isPaused = Boolean(simStatus?.paused);
  const activeMode = simStatus?.mode ? String(simStatus.mode).toUpperCase() : 'COORDINATED';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      {/* Top Header & Simulation Status Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <TrafficCone className="h-5 w-5 text-amber-600" />
          <h2 className="text-sm font-bold tracking-wide text-slate-900 uppercase">
            Signal Controller Telemetry & Causal Intelligence
          </h2>
        </div>

        {/* Visible Simulation Status Indicator */}
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
              isRunning
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300 animate-pulse'
                : isPaused
                ? 'bg-amber-50 text-amber-700 border-amber-300'
                : 'bg-slate-100 text-slate-700 border-slate-300'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isRunning ? 'bg-emerald-500' : isPaused ? 'bg-amber-500' : 'bg-slate-400'
              }`}
            />
            {isRunning ? 'LIVE SIMULATION' : isPaused ? 'SIMULATION PAUSED' : 'SIMULATION STOPPED'}
          </span>
          <span className="text-xs text-slate-600 font-mono bg-slate-100 px-2 py-1 rounded border border-slate-200">
            Mode: {activeMode}
          </span>
        </div>
      </div>

      {!isRunning && (
        <div className="mb-4 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-600 flex items-center justify-between">
          <span>Simulation stopped: displaying last recorded snapshot state. Live decisions update during active simulation.</span>
          <span className="text-slate-400 font-mono">Min 15s / Max 60s Bounds Enforced</span>
        </div>
      )}

      {/* Junction Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {junctionList.map((junc) => {
          const sig = signals?.[junc.id];
          const st = junctions?.[junc.id];

          const isGreen = sig?.is_green ?? false;
          const isYellow = sig?.is_yellow ?? false;
          const isRed = !isGreen && !isYellow;
          const isCongested = (st?.total_queue || 0) > 10;
          const isEmergencyLocked = sig?.emergency_locked || false;

          // Find decisions relevant to this junction
          const junctionDecisions = (decisions || []).filter(
            (d) => d.junction_id === junc.id || (junc.id === 'J2' && d.junction_id === 'CORRIDOR')
          );
          const latestDecision =
            junctionDecisions.length > 0 ? junctionDecisions[junctionDecisions.length - 1] : null;
          const isExpanded = Boolean(expandedJunctions[junc.id]);

          // Action badge styling
          const getActionBadge = (act) => {
            if (!act) return null;
            const a = String(act).toUpperCase();
            if (a === 'KEEP') {
              return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-300">KEEP</span>;
            }
            if (a === 'EXTEND') {
              return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">EXTEND</span>;
            }
            if (a === 'SWITCH') {
              return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">SWITCH</span>;
            }
            if (a.includes('EMERGENCY')) {
              return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">EMERGENCY PREEMPTION</span>;
            }
            return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">{a}</span>;
          };

          return (
            <div
              key={junc.id}
              className={`rounded-xl border p-4 transition relative flex flex-col justify-between ${
                isCongested
                  ? 'border-rose-400 bg-rose-50/30 shadow-md'
                  : isEmergencyLocked
                  ? 'border-rose-400 bg-rose-50/40'
                  : 'border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300 hover:shadow-sm'
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="h-6 w-6 rounded bg-teal-100 text-teal-800 font-mono font-bold text-xs flex items-center justify-center border border-teal-200">
                      {junc.id}
                    </span>
                    <div>
                      <h3 className="text-xs font-bold text-slate-900">{junc.name}</h3>
                      <p className="text-[10px] text-slate-500 font-mono truncate">{junc.tls}</p>
                    </div>
                  </div>

                  {/* Emergency Lock Pill */}
                  {isEmergencyLocked && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-300 animate-pulse">
                      EMERGENCY LOCK
                    </span>
                  )}
                </div>

                {/* Traffic Light Head Visualizer */}
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-2.5 flex items-center justify-around mb-3 shadow-inner">
                  {/* Red Light */}
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                        isRed
                          ? 'bg-rose-500 border-rose-400 shadow-lg shadow-rose-500/50'
                          : 'bg-rose-950/40 border-rose-900/30 opacity-30'
                      }`}
                    />
                    <span className="text-[9px] uppercase tracking-wider text-slate-400">Red</span>
                  </div>

                  {/* Yellow Light */}
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                        isYellow
                          ? 'bg-amber-400 border-amber-300 shadow-lg shadow-amber-400/50'
                          : 'bg-amber-950/40 border-amber-900/30 opacity-30'
                      }`}
                    />
                    <span className="text-[9px] uppercase tracking-wider text-slate-400">Yellow</span>
                  </div>

                  {/* Green Light */}
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={`h-7 w-7 rounded-full border transition-all duration-300 ${
                        isGreen
                          ? 'bg-emerald-500 border-emerald-400 shadow-lg shadow-emerald-500/50'
                          : 'bg-emerald-950/40 border-emerald-900/30 opacity-30'
                      }`}
                    />
                    <span className="text-[9px] uppercase tracking-wider text-slate-400">Green</span>
                  </div>
                </div>

                {/* Phase description */}
                <div className="bg-slate-100 rounded px-2.5 py-1 text-xs text-slate-800 font-mono mb-3 border border-slate-200 text-center font-medium">
                  {getPhaseName(junc.id, sig?.current_phase ?? 0)}
                </div>

                {/* Timing meters */}
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                  <div className="bg-white p-2 rounded border border-slate-200">
                    <span className="text-[10px] text-slate-500 block">Elapsed In Phase</span>
                    <span className="font-mono font-bold text-slate-900">
                      {sig?.phase_elapsed ? `${sig.phase_elapsed.toFixed(1)}s` : '0.0s'}
                    </span>
                  </div>
                  <div className="bg-white p-2 rounded border border-slate-200">
                    <span className="text-[10px] text-slate-500 block">Min / Max Green</span>
                    <span className="font-mono text-slate-700 font-semibold">
                      {sig?.min_green || 15}s / {sig?.max_green || 60}s
                    </span>
                  </div>
                </div>

                {/* Approach Queues */}
                <div className="text-xs pt-2 border-t border-slate-200 mb-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-slate-500 text-[11px]">Total Junction Queue:</span>
                    <span className={`font-mono font-bold ${isCongested ? 'text-rose-600' : 'text-slate-900'}`}>
                      {st?.total_queue != null ? `${st.total_queue} veh` : 'Observation pending'}
                    </span>
                  </div>
                  {st?.approach_queues &&
                    Object.entries(st.approach_queues).map(([appr, q]) => (
                      <div key={appr} className="flex justify-between text-[11px] text-slate-600">
                        <span className="truncate max-w-[140px] capitalize">{appr.replace('_', ' ')}:</span>
                        <span className="font-mono font-semibold">{q} veh</span>
                      </div>
                    ))}
                </div>

                {/* Congestion warning banner */}
                {isCongested && (
                  <div className="mb-2.5 p-1.5 rounded bg-rose-50 border border-rose-200 text-rose-700 text-[10px] flex items-center gap-1 font-medium">
                    <AlertTriangle className="h-3 w-3 flex-shrink-0 text-rose-600" />
                    <span>Heavy queue detected (&gt; 10 veh)</span>
                  </div>
                )}
              </div>

              {/* Expandable Decision Rationale & Causal Chain Panel */}
              <div className="mt-2 pt-2 border-t border-slate-200/80">
                <button
                  type="button"
                  onClick={() => toggleJunction(junc.id)}
                  className="w-full flex items-center justify-between text-left text-xs font-semibold text-slate-700 hover:text-indigo-600 py-1 transition"
                >
                  <span className="flex items-center gap-1.5">
                    <Brain className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Decision Rationale & Causal Chain</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-normal flex items-center gap-0.5">
                    {isExpanded ? (
                      <>
                        Hide <ChevronUp className="h-3 w-3" />
                      </>
                    ) : (
                      <>
                        Show <ChevronDown className="h-3 w-3" />
                      </>
                    )}
                  </span>
                </button>

                {isExpanded && (
                  <div className="mt-2 p-2.5 bg-white rounded-lg border border-slate-200 text-xs shadow-inner">
                    {latestDecision ? (
                      <div className="space-y-2">
                        {/* Status Tag & Controller */}
                        <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
                          <span className="text-[10px] text-slate-500 font-mono">
                            Controller: <strong className="text-slate-800">{latestDecision.controller ? String(latestDecision.controller).toUpperCase() : activeMode}</strong>
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                            {isRunning ? 'LIVE DECISION' : 'SNAPSHOT RECORD'}
                          </span>
                        </div>

                        {/* Action & Phase Transition */}
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] text-slate-500">Selected Action:</span>
                          {getActionBadge(latestDecision.action)}
                        </div>

                        <div className="bg-slate-50 p-1.5 rounded border border-slate-100 text-[11px]">
                          <span className="text-slate-500 block text-[10px] mb-0.5">Phase Transition:</span>
                          <span className="font-mono text-slate-800 font-medium">
                            {getPhaseName(junc.id, latestDecision.current_phase)}
                            {' → '}
                            {getPhaseName(junc.id, latestDecision.target_phase ?? latestDecision.current_phase)}
                          </span>
                        </div>

                        {/* Decision Reason */}
                        <div className="bg-indigo-50/60 p-2 rounded border border-indigo-100">
                          <span className="text-[10px] font-bold text-indigo-900 block mb-0.5">Decision Reason:</span>
                          <p className="text-[11px] text-indigo-950 font-normal leading-relaxed italic">
                            "{latestDecision.reason}"
                          </p>
                        </div>

                        {/* Traffic Response: Observed Queue & Delta */}
                        <div className="grid grid-cols-2 gap-1.5 text-[10px] pt-1 border-t border-slate-100">
                          <div>
                            <span className="text-slate-500 block">Observed Queue:</span>
                            <span className="font-mono font-semibold text-slate-800">
                              {latestDecision.observed_queue != null
                                ? `${latestDecision.observed_queue} veh`
                                : st?.total_queue != null
                                ? `${st.total_queue} veh`
                                : 'Observation pending'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Traffic Response (ΔQ):</span>
                            <span className="font-mono font-semibold">
                              {latestDecision.queue_after != null && latestDecision.observed_queue != null ? (
                                (() => {
                                  const delta = latestDecision.queue_after - latestDecision.observed_queue;
                                  return (
                                    <span className={delta <= 0 ? 'text-emerald-600' : 'text-rose-600'}>
                                      {delta > 0 ? `+${delta}` : delta} veh ({latestDecision.observed_queue} → {latestDecision.queue_after})
                                    </span>
                                  );
                                })()
                              ) : (
                                <span className="text-slate-400 font-normal">Pending next cycle</span>
                              )}
                            </span>
                          </div>
                        </div>

                        {/* Timestamp */}
                        <div className="text-[9px] text-slate-400 flex justify-between pt-1 border-t border-slate-100">
                          <span>Sim Time: {latestDecision.simulation_time != null ? `${latestDecision.simulation_time.toFixed(1)}s` : '0.0s'}</span>
                          <span>Logged: {latestDecision.timestamp ? new Date(latestDecision.timestamp).toLocaleTimeString() : 'N/A'}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-3 text-slate-400 text-[11px]">
                        <Brain className="h-5 w-5 mx-auto mb-1 text-slate-300" />
                        <p className="font-medium text-slate-500">No decision recorded yet</p>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          Start simulation to observe real-time controller decisions and causal responses.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
