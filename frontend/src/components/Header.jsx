import React, { useState, useEffect } from 'react';
import { Activity, Radio, Cpu, Clock, AlertTriangle, RefreshCw } from 'lucide-react';

export function Header({ wsStatus, health, simStatus, readingAge, onOpenOverride }) {
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

  // Format reading age text
  const getReadingAgeBadge = () => {
    if (readingAge === null || readingAge === undefined) {
      return { text: 'Awaiting Telemetry', bg: 'bg-slate-100 text-slate-500 border-slate-200' };
    }
    if (readingAge < 5) {
      return { text: `Live (${readingAge}s ago)`, bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    }
    if (readingAge < 15) {
      return { text: `Recent (${readingAge}s ago)`, bg: 'bg-amber-50 text-amber-700 border-amber-200' };
    }
    return { text: `Stale (${readingAge}s ago)`, bg: 'bg-rose-50 text-rose-700 border-rose-200' };
  };

  const readingBadge = getReadingAgeBadge();

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-40 shadow-sm">
      {/* Title & Branding */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm text-white">
          <Activity className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-slate-900 uppercase">
              Bengaluru Traffic Coordination Center
            </h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-50 text-blue-700 border border-blue-200">
              Silk Board Corridor
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Multi-Intersection Adaptive Signal & Emergency Preemption Hub (J1 &rarr; J2 &rarr; J3)
          </p>
        </div>
      </div>

      {/* Status Indicators & Clock */}
      <div className="flex items-center flex-wrap gap-2.5">
        {/* Telemetry Reading Age */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium ${readingBadge.bg}`}>
          <RefreshCw className="h-3 w-3 animate-spin" style={{ animationDuration: '4s' }} />
          <span>Feed: {readingBadge.text}</span>
        </div>

        {/* WebSocket Status */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-xs">
          <Radio className={`h-3.5 w-3.5 ${isWsConnected ? 'text-emerald-600' : 'text-rose-600'}`} />
          <span className="text-slate-500">Stream:</span>
          <span className={`font-semibold ${isWsConnected ? 'text-emerald-700' : 'text-rose-700'}`}>
            {wsStatus}
          </span>
        </div>

        {/* SUMO Status */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-xs">
          <Cpu className="h-3.5 w-3.5 text-blue-600" />
          <span className="text-slate-500">SUMO:</span>
          <span className="font-semibold text-slate-700">
            {health?.sumo_available ? 'Online (v1.26)' : 'Offline'}
          </span>
        </div>

        {/* Simulation State Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-xs">
          <span className="text-slate-500">State:</span>
          <span
            className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
              isSimRunning
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : isSimPaused
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-slate-200 text-slate-700 border border-slate-300'
            }`}
          >
            {isSimRunning ? 'RUNNING' : isSimPaused ? 'PAUSED' : 'STOPPED'}
          </span>
        </div>

        {/* Digital Clock */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-xs text-slate-600">
          <Clock className="h-3.5 w-3.5 text-slate-400" />
          <span className="font-mono">{currentTime}</span>
        </div>

        {/* Manual Override Action */}
        <button
          onClick={onOpenOverride}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 text-xs font-semibold transition shadow-sm"
          title="Operator Manual Phase Override"
        >
          <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
          <span>Manual Override</span>
        </button>
      </div>
    </header>
  );
}
