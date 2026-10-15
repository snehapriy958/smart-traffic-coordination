import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { OverviewKPIs } from './components/OverviewKPIs';
import { SimulationControls } from './components/SimulationControls';
import { LiveCorridorView } from './components/LiveCorridorView';
import { SignalStatusPanel } from './components/SignalStatusPanel';
import { EmergencyPanel } from './components/EmergencyPanel';
import { RiskHotspotsPanel } from './components/RiskHotspotsPanel';
import { EmissionAnalytics } from './components/EmissionAnalytics';
import { ControllerComparison } from './components/ControllerComparison';
import { WhatIfScenario } from './components/WhatIfScenario';
import { api } from './services/api';
import { trafficWS } from './services/websocket';
import { AlertTriangle, X, CheckCircle, ShieldAlert, WifiOff, RefreshCw, AlertCircle, PlayCircle, Radio } from 'lucide-react';

export default function App() {
  // Connection and system health
  const [wsStatus, setWsStatus] = useState('DISCONNECTED');
  const [health, setHealth] = useState({ sumo_available: false, sumo_version: '' });
  const [simStatus, setSimStatus] = useState({
    running: false,
    paused: false,
    simulation_time: 0,
    duration: 600,
    mode: 'coordinated',
    seed: 42,
  });

  // Telemetry state
  const [metrics, setMetrics] = useState(null);
  const [junctions, setJunctions] = useState({});
  const [signals, setSignals] = useState({});
  const [emergencies, setEmergencies] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [compareData, setCompareData] = useState(null);

  // Reading freshness / age tracking (seconds elapsed since last reading)
  const [lastTelemetryTimestamp, setLastTelemetryTimestamp] = useState(null);
  const [readingAge, setReadingAge] = useState(null);

  // Loading and Error States
  const [initialLoading, setInitialLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // Active view tab
  const [activeTab, setActiveTab] = useState('live'); // 'live', 'analytics', 'safety', 'sandbox'

  // Manual Override Modal
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);
  const [overrideJunction, setOverrideJunction] = useState('J2');
  const [overridePhase, setOverridePhase] = useState(0);
  const [overrideConfirmed, setOverrideConfirmed] = useState(false);
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [overrideMessage, setOverrideMessage] = useState({ type: null, text: '' });

  // Reading age ticker
  useEffect(() => {
    const timer = setInterval(() => {
      if (lastTelemetryTimestamp) {
        setReadingAge(Math.max(0, Math.floor((Date.now() - lastTelemetryTimestamp) / 1000)));
      } else {
        setReadingAge(null);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [lastTelemetryTimestamp]);

  // Initial data loader with visible error handling
  const loadInitialData = useCallback(async () => {
    setInitialLoading(true);
    setApiError(null);
    setIsRetrying(true);

    try {
      const results = await Promise.allSettled([
        api.getHealth(),
        api.getSimulationStatus(),
        api.getTrafficMetrics(),
        api.getTrafficLive(),
        api.getSignals(),
        api.getEmergencies(),
        api.getRisks(),
        api.getExperimentsCompare(),
      ]);

      const [h, s, m, j, sig, em, r, comp] = results;
      const failed = results.filter((res) => res.status === 'rejected');

      if (h.status === 'fulfilled') setHealth(h.value);
      if (s.status === 'fulfilled') setSimStatus(s.value);
      if (m.status === 'fulfilled') {
        setMetrics(m.value);
        setLastTelemetryTimestamp(Date.now());
      }
      if (j.status === 'fulfilled' && j.value?.junctions) setJunctions(j.value.junctions);
      if (sig.status === 'fulfilled' && sig.value?.signals) setSignals(sig.value.signals);
      if (em.status === 'fulfilled') setEmergencies(em.value);
      if (r.status === 'fulfilled') setRiskData(r.value);
      if (comp.status === 'fulfilled') setCompareData(comp.value);

      if (failed.length >= 3) {
        setApiError(`Could not reach backend services (${failed.length} endpoints failed). Verify that FastAPI is running on http://127.0.0.1:8000.`);
      }
    } catch (err) {
      setApiError(`Failed to connect to backend API: ${err.message || 'Network error'}. Check that the backend server is running.`);
    } finally {
      setInitialLoading(false);
      setIsRetrying(false);
    }
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.getSimulationStatus();
      setSimStatus(s);
    } catch (_) {}
  }, []);

  // Set up WebSocket and listeners
  useEffect(() => {
    loadInitialData();

    // WebSocket status listener
    const unsubStatus = trafficWS.onStatusChange((status) => {
      setWsStatus(status);
    });

    // WebSocket message listener
    const unsubMsg = trafficWS.subscribe((data) => {
      if (data?.type === 'INITIAL_STATE' || data?.type === 'TRAFFIC_UPDATE') {
        setLastTelemetryTimestamp(Date.now());
        if (data.status) {
          setSimStatus((prev) => ({
            ...prev,
            running: data.status === 'RUNNING',
            paused: data.status === 'PAUSED',
            simulation_time: data.simulation_time ?? prev.simulation_time,
            mode: data.mode ?? prev.mode,
          }));
        }
        if (data.metrics) setMetrics(data.metrics);
        if (data.junctions) setJunctions(data.junctions);
        if (data.signals) setSignals(data.signals);
        if (data.emergencies) setEmergencies(data.emergencies);
      }
    });

    trafficWS.connect();

    return () => {
      unsubStatus();
      unsubMsg();
      trafficWS.disconnect();
    };
  }, [loadInitialData]);

  // Handle Manual Override submission
  const handleApplyOverride = async (e) => {
    e.preventDefault();
    if (!overrideConfirmed) {
      setOverrideMessage({ type: 'error', text: 'You must confirm the safety override acknowledgment.' });
      return;
    }
    setOverrideLoading(true);
    setOverrideMessage({ type: null, text: '' });
    try {
      const res = await api.overrideSignal(overrideJunction, Number(overridePhase), true);
      setOverrideMessage({ type: 'success', text: res.message || 'Signal phase overridden successfully.' });
      setTimeout(() => {
        setIsOverrideOpen(false);
        setOverrideMessage({ type: null, text: '' });
        setOverrideConfirmed(false);
      }, 1500);
    } catch (err) {
      setOverrideMessage({ type: 'error', text: err.message || 'Manual override failed.' });
    } finally {
      setOverrideLoading(false);
    }
  };

  const handleLaunchScenario = async (params) => {
    try {
      await api.startSimulation(params);
      await refreshStatus();
    } catch (err) {
      alert(`Failed to launch scenario: ${err.message}`);
    }
  };

  const isWsConnected = wsStatus === 'CONNECTED';
  const isSimRunning = simStatus?.running && !simStatus?.paused;
  const isSimPaused = simStatus?.paused;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <Header
        wsStatus={wsStatus}
        health={health}
        simStatus={simStatus}
        readingAge={readingAge}
        onOpenOverride={() => setIsOverrideOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-5">
        
        {/* Visible System & Stream Status Ribbon */}
        {apiError ? (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
              <div>
                <span className="font-bold">Backend Connection Failure: </span>
                <span>{apiError}</span>
              </div>
            </div>
            <button
              onClick={loadInitialData}
              disabled={isRetrying}
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
              <span>Retry</span>
            </button>
          </div>
        ) : !isWsConnected ? (
          <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <WifiOff className="h-4 w-4 text-amber-600 flex-shrink-0" />
              <div>
                <span className="font-bold">Live WebSocket Stream Disconnected: </span>
                <span>Real-time telemetry stream is offline. Displaying last cached readings — attempting auto-reconnect...</span>
              </div>
            </div>
            <button
              onClick={() => trafficWS.connect()}
              className="px-2.5 py-1 rounded bg-amber-200 hover:bg-amber-300 text-amber-900 font-semibold text-[11px] transition"
            >
              Reconnect
            </button>
          </div>
        ) : !isSimRunning ? (
          <div className="p-2.5 rounded-xl bg-blue-50/70 border border-blue-200 text-blue-900 text-xs flex items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <PlayCircle className="h-4 w-4 text-blue-600 flex-shrink-0" />
              <div>
                <span className="font-semibold">
                  {isSimPaused ? 'Simulation Paused: ' : 'Simulation Idle / Stopped: '}
                </span>
                <span className="text-blue-800">
                  {isSimPaused
                    ? `Execution halted at t = ${simStatus?.simulation_time?.toFixed(1) || '0.0'}s. Click Resume to continue.`
                    : 'Corridor readings reflect the baseline snapshot. Start a simulation run from the control deck below to observe live multi-intersection dynamics.'}
                </span>
              </div>
            </div>
            <span className="font-mono text-[11px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold">
              Mode: {simStatus?.mode || 'coordinated'}
            </span>
          </div>
        ) : (
          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-emerald-600 animate-pulse flex-shrink-0" />
              <div>
                <span className="font-semibold">Active Live Stream: </span>
                <span className="text-emerald-800">
                  Simulation running at 1.0s step resolution (t = {simStatus?.simulation_time?.toFixed(1) || '0.0'}s, Mode: {simStatus?.mode || 'coordinated'}).
                </span>
              </div>
            </div>
            <span className="font-mono text-[11px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">
              Feed Active
            </span>
          </div>
        )}

        {/* KPI Overview Ribbon */}
        <OverviewKPIs metrics={metrics} simStatus={simStatus} readingAge={readingAge} />

        {/* Simulation Controls Deck */}
        <SimulationControls simStatus={simStatus} onStatusRefresh={refreshStatus} />

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 gap-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab('live')}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition border-b-2 rounded-t-lg ${
              activeTab === 'live'
                ? 'border-blue-600 text-blue-700 bg-blue-50/60'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
            }`}
          >
            Live Corridor &amp; Signals
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition border-b-2 rounded-t-lg ${
              activeTab === 'analytics'
                ? 'border-blue-600 text-blue-700 bg-blue-50/60'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
            }`}
          >
            Emissions &amp; Benchmarks
          </button>
          <button
            onClick={() => setActiveTab('safety')}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition border-b-2 rounded-t-lg ${
              activeTab === 'safety'
                ? 'border-blue-600 text-blue-700 bg-blue-50/60'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
            }`}
          >
            Accident Hotspots &amp; Risk Zones
          </button>
          <button
            onClick={() => setActiveTab('sandbox')}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition border-b-2 rounded-t-lg ${
              activeTab === 'sandbox'
                ? 'border-blue-600 text-blue-700 bg-blue-50/60'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
            }`}
          >
            What-If Sandbox &amp; History
          </button>
        </div>

        {/* Tab 1: Live Corridor & Signal Status */}
        {activeTab === 'live' && (
          <div className="space-y-6">
            <LiveCorridorView
              junctions={junctions}
              signals={signals}
              emergencies={emergencies}
              isStale={wsStatus === 'DISCONNECTED'}
              readingAge={readingAge}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SignalStatusPanel signals={signals} junctions={junctions} readingAge={readingAge} />
              <EmergencyPanel emergencies={emergencies} />
            </div>
          </div>
        )}

        {/* Tab 2: Emissions & Controller Benchmarks */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <ControllerComparison compareData={compareData} />
            <EmissionAnalytics metrics={metrics} />
          </div>
        )}

        {/* Tab 3: Risk Hotspots & Blackspots */}
        {activeTab === 'safety' && (
          <div className="space-y-6">
            <RiskHotspotsPanel riskData={riskData} />
          </div>
        )}

        {/* Tab 4: What-If Sandbox & Experiment Run History */}
        {activeTab === 'sandbox' && (
          <div className="space-y-6">
            <WhatIfScenario onRunScenario={handleLaunchScenario} />
          </div>
        )}
      </main>

      {/* Manual Override Modal */}
      {isOverrideOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setIsOverrideOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-700"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-6 w-6 text-amber-500" />
              <h2 className="text-base font-bold text-slate-900 uppercase">
                Operator Signal Phase Override
              </h2>
            </div>

            <p className="text-xs text-slate-600 mb-4">
              Intervene directly in signal controllers. Yellow transition clearance and min/max phase boundaries will still be safely enforced by the controller safety shield.
            </p>

            <form onSubmit={handleApplyOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Intersection
                </label>
                <select
                  value={overrideJunction}
                  onChange={(e) => setOverrideJunction(e.target.value)}
                  className="w-full bg-white border border-slate-300 text-slate-800 rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-blue-500 outline-none font-medium"
                >
                  <option value="J1">J1: Hosur North Feeder (TLS 1617743335)</option>
                  <option value="J2">J2: Silk Board Central (TLS GS_cluster)</option>
                  <option value="J3">J3: Hosur South Feeder (TLS 6970466614)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Signal Phase
                </label>
                <select
                  value={overridePhase}
                  onChange={(e) => setOverridePhase(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 text-slate-800 rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-blue-500 outline-none font-medium"
                >
                  {overrideJunction === 'J2' ? (
                    <>
                      <option value={0}>Phase 0: Hosur Road Arterial Green</option>
                      <option value={1}>Phase 1: Hosur Yellow Clearance</option>
                      <option value={2}>Phase 2: Madiwala Cross Green</option>
                      <option value={3}>Phase 3: Madiwala Yellow Clearance</option>
                    </>
                  ) : (
                    <>
                      <option value={0}>Phase 0: Side Cross Green</option>
                      <option value={1}>Phase 1: Side Cross Yellow Clearance</option>
                      <option value={2}>Phase 2: Hosur Corridor Green</option>
                      <option value={3}>Phase 3: Hosur Corridor Yellow Clearance</option>
                    </>
                  )}
                </select>
              </div>

              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={overrideConfirmed}
                    onChange={(e) => setOverrideConfirmed(e.target.checked)}
                    className="mt-0.5 accent-amber-500 rounded"
                  />
                  <span>
                    I confirm this manual signal override is authorized and required for traffic operations.
                  </span>
                </label>
              </div>

              {overrideMessage.text && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-center gap-2 font-medium ${
                    overrideMessage.type === 'success'
                      ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border border-rose-200 text-rose-800'
                  }`}
                >
                  {overrideMessage.type === 'success' ? (
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-rose-600" />
                  )}
                  <span>{overrideMessage.text}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsOverrideOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideLoading || !overrideConfirmed}
                  className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs"
                >
                  {overrideLoading ? 'Applying...' : 'Confirm & Apply Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
        Bengaluru Traffic Coordination Center &bull; Silk Board Hosur Road Continuous Corridor &bull; Powered by Eclipse SUMO &amp; FastAPI
      </footer>
    </div>
  );
}
