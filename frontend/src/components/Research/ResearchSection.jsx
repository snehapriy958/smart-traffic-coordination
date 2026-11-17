import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { ResearchOverviewView } from './ResearchOverviewView';
import { Series4BView } from './Series4BView';
import { Series4CLiveMonitorView } from './Series4CLiveMonitorView';
import { Series4EView } from './Series4EView';
import { MasterBenchmarkView } from './MasterBenchmarkView';
import { BookOpen, Layers, Activity, Users, ShieldCheck, RefreshCw, AlertCircle } from 'lucide-react';

export function ResearchSection({ compareData, compareLoading, compareError }) {
  const [subTab, setSubTab] = useState('overview'); // 'overview', 'series4b', 'series4c', 'series4e', 'master'

  // Research data states
  const [overviewData, setOverviewData] = useState(null);
  const [series4BData, setSeries4BData] = useState(null);
  const [series4CStatus, setSeries4CStatus] = useState(null);
  const [series4CHistory, setSeries4CHistory] = useState(null);
  const [series4EData, setSeries4EData] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing4C, setIsRefreshing4C] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Load all research endpoints
  const loadResearchData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [ov, s4b, s4c, s4cHist, s4e] = await Promise.allSettled([
        api.getResearchOverview(),
        api.getSeries4BResults(),
        api.getSeries4CLiveStatus(),
        api.getSeries4CHistory(),
        api.getSeries4EResults(),
      ]);

      if (ov.status === 'fulfilled') setOverviewData(ov.value);
      if (s4b.status === 'fulfilled') setSeries4BData(s4b.value);
      if (s4c.status === 'fulfilled') setSeries4CStatus(s4c.value);
      if (s4cHist.status === 'fulfilled') setSeries4CHistory(s4cHist.value);
      if (s4e.status === 'fulfilled') setSeries4EData(s4e.value);
    } catch (err) {
      console.warn('Research data loading warning:', err);
      setLoadError(err.message || 'Failed to fetch research telemetry');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Targeted refresh for Series 4C live monitor
  const refreshSeries4C = useCallback(async () => {
    setIsRefreshing4C(true);
    try {
      const [s4c, s4cHist] = await Promise.allSettled([
        api.getSeries4CLiveStatus(),
        api.getSeries4CHistory(),
      ]);
      if (s4c.status === 'fulfilled') setSeries4CStatus(s4c.value);
      if (s4cHist.status === 'fulfilled') setSeries4CHistory(s4cHist.value);
    } catch (err) {
      console.warn('Series 4C refresh error:', err);
    } finally {
      setIsRefreshing4C(false);
    }
  }, []);

  useEffect(() => {
    loadResearchData();
  }, [loadResearchData]);

  // Periodic polling only when active on Series 4C monitor
  useEffect(() => {
    if (subTab !== 'series4c') return;
    const interval = setInterval(() => {
      refreshSeries4C();
    }, 10000);
    return () => clearInterval(interval);
  }, [subTab, refreshSeries4C]);

  return (
    <div className="space-y-6">
      {/* Sub-navigation tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-2">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSubTab('overview')}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              subTab === 'overview'
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Overview & Matrix</span>
          </button>

          <button
            onClick={() => setSubTab('series4b')}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              subTab === 'series4b'
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Series 4B (Dimensionality)</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">
              Frozen
            </span>
          </button>

          <button
            onClick={() => setSubTab('series4c')}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              subTab === 'series4c'
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Activity className="h-3.5 w-3.5 text-amber-500" />
            <span>Series 4C Live Monitor</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 font-bold border border-amber-300 animate-pulse">
              Active Run
            </span>
          </button>

          <button
            onClick={() => setSubTab('series4e')}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              subTab === 'series4e'
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            <span>Series 4E (Passenger Reward)</span>
          </button>

          <button
            onClick={() => setSubTab('master')}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 ${
              subTab === 'master'
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5 text-purple-500" />
            <span>Master Benchmark (N=10)</span>
          </button>
        </div>

        <button
          onClick={loadResearchData}
          disabled={isLoading}
          className="px-2.5 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs font-medium flex items-center gap-1 shadow-sm transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin text-teal-600' : ''}`} />
          <span>Reload</span>
        </button>
      </div>

      {/* Global Error Banner if initial fetch fails */}
      {loadError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
            <span>Error connecting to research data source: {loadError}</span>
          </div>
          <button
            onClick={loadResearchData}
            className="px-2 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded font-semibold text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Tab 1: Research Overview */}
      {subTab === 'overview' && (
        <ResearchOverviewView
          data={overviewData}
          onSelectSeries={(seriesKey) => setSubTab(seriesKey)}
        />
      )}

      {/* Tab 2: Series 4B Results */}
      {subTab === 'series4b' && <Series4BView data={series4BData} />}

      {/* Tab 3: Series 4C Live Monitor */}
      {subTab === 'series4c' && (
        <Series4CLiveMonitorView
          statusData={series4CStatus}
          historyData={series4CHistory}
          onRefresh={refreshSeries4C}
          isRefreshing={isRefreshing4C}
        />
      )}

      {/* Tab 4: Series 4E Passenger Reward */}
      {subTab === 'series4e' && <Series4EView data={series4EData} />}

      {/* Tab 5: Authoritative Master Benchmark */}
      {subTab === 'master' && (
        <MasterBenchmarkView
          compareData={compareData}
          isLoading={compareLoading}
          error={compareError}
        />
      )}
    </div>
  );
}
