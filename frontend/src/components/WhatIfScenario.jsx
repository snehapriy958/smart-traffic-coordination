import React, { useState, useEffect } from 'react';
import { Layers, History, Play, CheckCircle2, RotateCcw } from 'lucide-react';
import { api } from '../services/api';

export function WhatIfScenario({ onRunScenario }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Scenario config
  const [scenarioMode, setScenarioMode] = useState('coordinated');
  const [scenarioDuration, setScenarioDuration] = useState(300);
  const [scenarioSeed, setScenarioSeed] = useState(101);
  const [scenarioEmergency, setScenarioEmergency] = useState(true);

  const fetchHistory = async () => {
    try {
      const data = await api.getExperimentsHistory();
      setHistory(data);
    } catch (e) {
      console.warn('Failed fetching history:', e);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleLaunch = () => {
    if (onRunScenario) {
      onRunScenario({
        mode: scenarioMode,
        duration: Number(scenarioDuration),
        seed: Number(scenarioSeed),
        enable_emergency: scenarioEmergency,
      });
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
            What-If Scenario Sandbox & Run History
          </h2>
        </div>
        <button
          onClick={fetchHistory}
          className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          title="Refresh History"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Scenario Config Bar */}
      <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 mb-5">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Configure Custom Corridor Scenario
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-3 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Controller</label>
            <select
              value={scenarioMode}
              onChange={(e) => setScenarioMode(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white rounded px-2.5 py-1.5 outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="coordinated">Coordinated Adaptive</option>
              <option value="baseline">Fixed-Time Baseline</option>
            </select>
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Duration (s)</label>
            <input
              type="number"
              value={scenarioDuration}
              onChange={(e) => setScenarioDuration(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-white rounded px-2.5 py-1.5 outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Demand Seed</label>
            <input
              type="number"
              value={scenarioSeed}
              onChange={(e) => setScenarioSeed(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-white rounded px-2.5 py-1.5 outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
            />
          </div>
          <div className="flex flex-col justify-end">
            <label className="flex items-center gap-2 cursor-pointer bg-slate-800 border border-slate-700 px-3 py-1.5 rounded text-slate-300">
              <input
                type="checkbox"
                checked={scenarioEmergency}
                onChange={(e) => setScenarioEmergency(e.target.checked)}
                className="accent-cyan-500"
              />
              <span>Ambulance Surge</span>
            </label>
          </div>
        </div>

        <button
          onClick={handleLaunch}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition"
        >
          <Play className="h-3.5 w-3.5" />
          <span>Launch Scenario in Simulator</span>
        </button>
      </div>

      {/* Historical Runs Stored in SQLite */}
      <div>
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <History className="h-4 w-4 text-slate-400" />
          <span>Stored SQLite Database Runs ({history.length})</span>
        </h3>

        {history.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-3 text-center border border-dashed border-slate-800 rounded-lg">
            No historical experiment runs stored in database yet.
          </p>
        ) : (
          <div className="overflow-x-auto max-h-60 overflow-y-auto border border-slate-800 rounded-lg">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-800/80 text-slate-300 text-[10px] uppercase border-b border-slate-700 sticky top-0">
                <tr>
                  <th className="py-2 px-3">Run UUID</th>
                  <th className="py-2 px-3">Mode</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Seed</th>
                  <th className="py-2 px-3">Simulated (s)</th>
                  <th className="py-2 px-3">Throughput</th>
                  <th className="py-2 px-3">CO₂ (kg)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-[11px]">
                {history.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-400">{run.run_uuid}</td>
                    <td className="py-2 px-3 font-semibold uppercase text-cyan-300">{run.mode}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        run.status === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : run.status === 'RUNNING'
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          : 'bg-slate-700 text-slate-300'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{run.seed}</td>
                    <td className="py-2 px-3 text-white">{run.duration_simulated.toFixed(1)}s</td>
                    <td className="py-2 px-3 text-slate-300">
                      {run.summary_metrics?.throughput_vehicles ?? '—'}
                    </td>
                    <td className="py-2 px-3 text-teal-400 font-semibold">
                      {run.summary_metrics?.total_co2_kg ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
