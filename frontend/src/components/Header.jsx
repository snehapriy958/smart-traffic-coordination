import React, { useState, useEffect } from 'react';
import { Activity, Radio, Cpu, Clock, AlertTriangle } from 'lucide-react';

export function Header({ wsStatus, health, simStatus, onOpenOverride }) {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const isWsConnected = wsStatus === 'CONNECTED';
  const isSimRunning = simStatus?.running && !simStatus?.paused;
  const isSimPaused = simStatus?.paused;

  return (
    <header className="border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-40">
      {/* Title & Branding */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Activity className="h-6 w-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white uppercase">
              Bengaluru Traffic Coordination Center
            </h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              Silk Board Corridor
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Multi-Intersection Adaptive Signal & Emergency Preemption Hub (J1 &rarr; J2 &rarr; J3)
          </p>
        </div>
      </div>

      {/* Status Indicators & Clock */}
      <div className="flex items-center flex-wrap gap-4">
        {/* WebSocket Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs">
          <Radio className={`h-4 w-4 ${isWsConnected ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}`} />
          <span className="text-slate-400">Stream:</span>
          <span className={`font-semibold ${isWsConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
            {wsStatus}
          </span>
        </div>

        {/* SUMO Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs">
          <Cpu className="h-4 w-4 text-blue-400" />
          <span className="text-slate-400">SUMO:</span>
          <span className="font-semibold text-slate-200">
            {health?.sumo_available ? 'Online (v1.26)' : 'Offline'}
          </span>
        </div>

        {/* Simulation State Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs">
          <span className="text-slate-400">Status:</span>
          <span
            className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
              isSimRunning
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                : isSimPaused
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                : 'bg-slate-700/50 text-slate-400 border border-slate-600'
            }`}
          >
            {isSimRunning ? 'RUNNING' : isSimPaused ? 'PAUSED' : 'STOPPED'}
          </span>
        </div>

        {/* Digital Clock */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <Clock className="h-4 w-4 text-slate-400" />
          <span className="font-mono">{currentTime}</span>
        </div>

        {/* Manual Override Action */}
        <button
          onClick={onOpenOverride}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-semibold transition"
          title="Operator Manual Phase Override"
        >
          <AlertTriangle className="h-4 w-4" />
          <span>Manual Override</span>
        </button>
      </div>
    </header>
  );
}
