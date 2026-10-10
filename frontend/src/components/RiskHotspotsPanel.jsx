import React from 'react';
import { AlertOctagon, Flame, Shield, MapPin, Info } from 'lucide-react';

export function RiskHotspotsPanel({ riskData }) {
  const zones = riskData?.risk_zones || [];
  const hotspots = riskData?.hotspots || [];

  const getRiskBadge = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <AlertOctagon className="h-5 w-5 text-rose-400" />
          <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
            Accident Blackspots & MoRTH Risk Zones
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-rose-400 font-bold">{riskData?.critical_zones || 0} Critical</span>
          <span className="text-slate-500">&bull;</span>
          <span className="text-amber-400 font-bold">{riskData?.high_zones || 0} High</span>
          <span className="text-slate-500">&bull;</span>
          <span className="text-slate-400">{riskData?.total_zones || 0} Zones</span>
        </div>
      </div>

      {/* Methodology Notice */}
      <div className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-xs text-slate-300 mb-4 flex items-start gap-2">
        <Info className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-white">IRC / MoRTH Road Safety Audit Methodology</p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Risk scores represent Composite Risk Index (CRI = Fatal &times; 5.0 + Non-Fatal &times; 2.0 + corridor proximity weight) derived from Bengaluru Traffic Police records.
            <span className="text-cyan-300 font-medium"> Note: Evaluated on historical spatial observations; no unverified predictive AI claims.</span>
          </p>
        </div>
      </div>

      {/* Risk Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
        {zones.map((zone) => (
          <div
            key={zone.zone_id}
            className="p-3.5 rounded-xl border border-slate-700/80 bg-slate-800/40 hover:bg-slate-800 transition"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div>
                <h3 className="text-xs font-bold text-white uppercase">{zone.zone_name}</h3>
                <span className="text-[10px] text-slate-400 font-mono">ID: {zone.zone_id}</span>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${getRiskBadge(zone.risk_level)}`}>
                {zone.risk_level} (CRI: {zone.composite_risk_score})
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs bg-slate-900/60 p-2 rounded-lg border border-slate-700/40 mb-2 font-mono">
              <div>
                <span className="text-[10px] text-slate-400 block">Total Crashes</span>
                <span className="text-white font-semibold">{zone.total_crashes}</span>
              </div>
              <div>
                <span className="text-[10px] text-rose-400 block">Fatal Crashes</span>
                <span className="text-rose-400 font-bold">{zone.fatal_crashes}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Target TLS</span>
                <span className="text-cyan-300">{zone.associated_junction || 'Corridor Link'}</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-300 italic border-l-2 border-slate-600 pl-2">
              &ldquo;{zone.safety_advisory}&rdquo;
            </p>
          </div>
        ))}
      </div>

      {/* Spatial Hotspots Table */}
      {hotspots.length > 0 && (
        <div>
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            DBSCAN Spatial Hotspot Clusters ({hotspots.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-800/60 text-slate-400 text-[10px] uppercase border-b border-slate-700">
                <tr>
                  <th className="py-1.5 px-3">Cluster ID</th>
                  <th className="py-1.5 px-3">Relevance</th>
                  <th className="py-1.5 px-3">Total Crashes</th>
                  <th className="py-1.5 px-3">Fatal</th>
                  <th className="py-1.5 px-3">Severity Score</th>
                  <th className="py-1.5 px-3">Coordinates (Lat, Lon)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-[11px]">
                {hotspots.map((hs) => (
                  <tr key={hs.hotspot_id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-semibold text-white">{hs.hotspot_id}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${hs.corridor_relevance === 'CORRIDOR' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400'}`}>
                        {hs.corridor_relevance}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-200">{hs.total_crashes}</td>
                    <td className="py-2 px-3 text-rose-400 font-bold">{hs.fatal_crashes}</td>
                    <td className="py-2 px-3 text-amber-300 font-semibold">{hs.severity_score}</td>
                    <td className="py-2 px-3 text-slate-400">
                      {hs.center_latitude.toFixed(4)}, {hs.center_longitude.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
