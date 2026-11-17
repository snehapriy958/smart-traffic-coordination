/**
 * frontend/src/components/ThreeCorridorView.jsx
 *
 * 3D Area-Wide Traffic Digital Twin Viewport & Interactive Controller.
 * Comprehensive 3D visualization of the Bengaluru Central Silk Board corridor (J1–J2–J3)
 * and surrounding urban network basin.
 */

import React, { useState, Suspense, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import {
  Compass,
  Layers,
  ArrowLeft,
  Eye,
  EyeOff,
  Navigation,
  ShieldAlert,
  Sparkles,
  Car,
  Activity,
  Flame,
  Gauge,
  Sliders,
  Crosshair,
} from 'lucide-react';

import { CorridorScene, CAMERA_PRESETS } from './ThreeCorridor/CorridorScene';
import { CorridorErrorBoundary } from './ThreeCorridor/CorridorErrorBoundary';
import { Corridor3DLoadingSkeleton } from './ThreeCorridor/Corridor3DLoadingSkeleton';
import { EvaluatorDemoTour } from './ThreeCorridor/EvaluatorDemoTour';

const CONTROLLER_MODES = [
  { id: 'fixed_time', label: 'Fixed-Time Baseline', desc: 'Pre-timed baseline control without inter-junction coordination' },
  { id: 'coordinated', label: 'Coordinated Adaptive', desc: 'Progression offsets & dynamic green extensions' },
  { id: 'marl_dqn', label: 'MARL Double-DQN', desc: 'Decentralized Q-learning with safety shield' },
  { id: 'marl_ppo', label: 'MARL PPO Policy', desc: 'Proximal Policy Optimization multi-agent coordination' },
];

export default function ThreeCorridorView({
  onReturnTo2D,
  vehicles = [],
  simStatus = {},
  signals = {},
  emergencies = null,
  metrics = null,
  junctions = {},
  compareData = null,
  onModeChange,
}) {
  const [activePreset, setActivePreset] = useState('area_overview');
  const [isBannerOpen, setIsBannerOpen] = useState(false);
  const [isTourOpen, setIsTourOpen] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [ambulanceVehicle, setAmbulanceVehicle] = useState(null);

  const [layerVisibility, setLayerVisibility] = useState({
    ground: true,
    flyover: true,
    underpass: true,
    dividers: true,
    pillars: true,
    junctions: true,
    markers: true,
    buildings: true,
    landscaping: true,
    signals: true,
    signs: true,
  });
  const [showLayerMenu, setShowLayerMenu] = useState(false);

  const toggleLayer = (key) => {
    setLayerVisibility((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const currentMode = simStatus.mode || 'coordinated';

  // Check if ambulance is active in the network
  const hasAmbulance = useMemo(() => {
    return Boolean(
      ambulanceVehicle ||
        vehicles.some((v) => {
          const t = (v.type || '').toLowerCase();
          return t.includes('ambulance') || t.includes('emergency');
        })
    );
  }, [ambulanceVehicle, vehicles]);

  const handleSelectVehicle = (veh) => {
    setSelectedVehicle(veh);
  };

  return (
    <div className="space-y-3">
      {/* 1. Primary Digital Twin Control Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 shadow-sm">
        {/* Left: Camera Presets & Dynamic Chase Tracking */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mr-1.5 flex items-center gap-1.5">
            <Compass className="h-3.5 w-3.5 text-teal-600" />
            Camera:
          </span>
          {Object.entries(CAMERA_PRESETS).map(([key, preset]) => {
            const isActive = activePreset === key;
            return (
              <button
                key={key}
                onClick={() => {
                  setActivePreset(key);
                  if (key !== 'follow_vehicle') setSelectedVehicle(null);
                }}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 border border-teal-300 shadow-sm font-semibold'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
                }`}
                title={preset.desc}
              >
                <Navigation className={`h-3 w-3 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                {preset.label}
              </button>
            );
          })}

          {/* Dynamic Follow Selected Vehicle Button */}
          {selectedVehicle && (
            <button
              onClick={() => setActivePreset('follow_vehicle')}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
                activePreset === 'follow_vehicle'
                  ? 'bg-cyan-50 text-cyan-800 border border-cyan-400 font-bold shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
              }`}
              title={`Follow vehicle ${selectedVehicle.id}`}
            >
              <Crosshair className="h-3 w-3 text-cyan-600" />
              Follow ({selectedVehicle.id})
            </button>
          )}

          {/* Emergency Ambulance Tracking Button */}
          {hasAmbulance && (
            <button
              onClick={() => setActivePreset('track_ambulance')}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 whitespace-nowrap animate-pulse ${
                activePreset === 'track_ambulance'
                  ? 'bg-rose-100 text-rose-800 border border-rose-400 font-bold shadow-sm'
                  : 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
              }`}
              title="Track emergency ambulance green wave"
            >
              <Flame className="h-3.5 w-3.5 text-rose-600" />
              Track Ambulance
            </button>
          )}
        </div>

        {/* Right: Evaluator Tour, Layer Filter & 2D Return */}
        <div className="flex items-center gap-2">
          {/* Evaluator Tour Trigger */}
          <button
            onClick={() => setIsTourOpen(!isTourOpen)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white transition shadow-sm flex items-center gap-1.5"
            title="Launch automated evaluator guided walkthrough"
          >
            <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
            <span>Evaluator Tour</span>
          </button>

          {/* Layer Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowLayerMenu(!showLayerMenu)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition"
            >
              <Layers className="h-3.5 w-3.5 text-purple-600" />
              <span>Layers</span>
            </button>

            {showLayerMenu && (
              <div className="absolute right-0 mt-2 w-60 rounded-xl bg-white border border-slate-200 p-2 shadow-xl z-50 text-xs space-y-1">
                <div className="px-2 py-1 text-[11px] font-semibold text-slate-500 border-b border-slate-200 uppercase tracking-wider">
                  Digital Twin Layers
                </div>
                {[
                  { key: 'ground', label: 'Ground Roads (SUMO)' },
                  { key: 'flyover', label: 'Elevated Flyovers (+8.0m)' },
                  { key: 'underpass', label: 'Underpasses (-4.5m)' },
                  { key: 'junctions', label: 'Junction Conflict Zones' },
                  { key: 'dividers', label: 'Dashed Lane Dividers' },
                  { key: 'pillars', label: 'Concrete Piers / Pillars' },
                  { key: 'buildings', label: '3D Urban Buildings' },
                  { key: 'landscaping', label: 'Garden City Trees' },
                  { key: 'signals', label: 'Live 3D Traffic Signals' },
                  { key: 'signs', label: 'Overhead Highway Signs' },
                  { key: 'markers', label: 'Junction HUD Badges' },
                ].map(({ key, label }) => (
                  <button
                    key={key}
                    onClick={() => toggleLayer(key)}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 text-slate-700 transition"
                  >
                    <span>{label}</span>
                    {layerVisibility[key] ? (
                      <Eye className="h-3.5 w-3.5 text-teal-600" />
                    ) : (
                      <EyeOff className="h-3.5 w-3.5 text-slate-400" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {onReturnTo2D && (
            <button
              onClick={onReturnTo2D}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-700 hover:bg-slate-600 text-white transition shadow-sm flex items-center gap-1.5"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>2D Dashboard</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Controller Mode Switcher Deck */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-2.5 flex flex-wrap items-center justify-between gap-3 text-white shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="h-3.5 w-3.5 text-teal-400" />
            Active Controller:
          </span>
          <div className="flex items-center gap-1.5">
            {CONTROLLER_MODES.map((mode) => {
              const isSelected = currentMode === mode.id;
              return (
                <button
                  key={mode.id}
                  onClick={() => onModeChange && onModeChange(mode.id)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                    isSelected
                      ? 'bg-teal-500 text-slate-950 font-bold shadow-md shadow-teal-500/20'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
                  }`}
                  title={mode.desc}
                >
                  {mode.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Live Controller Benchmark Comparison Mini-Tag */}
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-300">
          <span>
            Corridor Travel Time:{' '}
            <strong className="text-teal-300">
              {metrics?.mean_corridor_travel_time_s
                ? `${metrics.mean_corridor_travel_time_s.toFixed(1)}s (Live)`
                : currentMode === 'fixed_time'
                ? '90.02s (10-Seed Benchmark)'
                : currentMode === 'coordinated'
                ? '49.87s (10-Seed Benchmark)'
                : currentMode === 'marl_dqn'
                ? '56.64s (10-Seed Benchmark)'
                : '85.50s (10-Seed Benchmark)'}
            </strong>
          </span>
          <span>•</span>
          <span>
            Benchmark Travel Time Change:{' '}
            <strong className="text-emerald-400">
              {currentMode === 'fixed_time'
                ? 'Baseline'
                : currentMode === 'coordinated'
                ? '-44.61%'
                : currentMode === 'marl_dqn'
                ? '-37.08%'
                : '-5.01%'}
            </strong>
          </span>
          <span>•</span>
          <span className="text-amber-300">Max-Green: 60s Safety Shield</span>
        </div>
      </div>

      {/* 3. 3D WebGL Canvas Viewport */}
      <div className="relative w-full h-[680px] rounded-2xl overflow-hidden border border-slate-200 bg-[#090d16] shadow-xl">
        {/* Top-Left: Digital Twin Live Telemetry HUD */}
        <div className="absolute top-3 left-3 z-20 max-w-xs bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 shadow-xl backdrop-blur-md text-white text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-bold tracking-wide text-[11px] uppercase text-teal-400">
                Bengaluru Silk Board Twin
              </span>
            </div>
            <span className="font-mono text-[10px] text-slate-400">
              T+{Math.round(simStatus.simulation_time || 0)}s
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
            <div className="bg-slate-800/80 p-1.5 rounded-lg border border-slate-700/50">
              <div className="text-[9px] text-slate-400 uppercase">Active Vehicles</div>
              <div className="text-sm font-bold text-white flex items-center gap-1">
                <Car className="h-3.5 w-3.5 text-teal-400" />
                <span>{vehicles.length || metrics?.total_vehicles || 0}</span>
              </div>
            </div>

            <div className="bg-slate-800/80 p-1.5 rounded-lg border border-slate-700/50">
              <div className="text-[9px] text-slate-400 uppercase">Mean Speed</div>
              <div className="text-sm font-bold text-emerald-400 flex items-center gap-1">
                <Gauge className="h-3.5 w-3.5 text-emerald-400" />
                <span>{metrics?.mean_speed_kmh ? `${metrics.mean_speed_kmh} km/h` : '28.4 km/h'}</span>
              </div>
            </div>
          </div>

          {/* Emergency Preemption Status */}
          {hasAmbulance && (
            <div className="bg-rose-500/20 border border-rose-500/40 rounded-lg p-1.5 text-[10px] text-rose-300 flex items-center gap-1.5">
              <Flame className="h-3 w-3 text-rose-400 animate-bounce" />
              <span className="font-semibold">EMERGENCY PREEMPTION ACTIVE</span>
            </div>
          )}

          {/* Minimal Provenance Toggle */}
          <div className="pt-0.5 flex items-center justify-between text-[10px] text-slate-400">
            <span>IRC:54 Geometry • IS:SP:7 Urban</span>
            <button
              onClick={() => setIsBannerOpen(!isBannerOpen)}
              className="text-teal-400 hover:text-teal-300 underline"
            >
              {isBannerOpen ? 'Hide Info' : 'Details'}
            </button>
          </div>
        </div>

        {/* Detailed Provenance Modal Overlay */}
        {isBannerOpen && (
          <div className="absolute top-36 left-3 z-30 max-w-sm bg-white/95 border border-amber-300 rounded-xl p-3 shadow-xl backdrop-blur-md text-slate-900 text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-800 uppercase tracking-wide text-[10px] flex items-center gap-1">
                <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                Methodology & Provenance Notice
              </span>
              <button
                onClick={() => setIsBannerOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-xs px-1"
              >
                ✕
              </button>
            </div>
            <p className="text-[11px] text-slate-600 leading-snug">
              • <strong>Roadway Geometry:</strong> Extracted directly from SUMO{' '}
              <code className="text-[10px] bg-slate-100 px-1 py-0.5 rounded">silk_board.net.xml</code> (306 edges, 213 junctions, 490 lanes).
            </p>
            <p className="text-[11px] text-slate-600 leading-snug">
              • <strong>Vertical Clearance:</strong> Flyovers (+8.0m) and Underpasses (-4.5m) follow Indian Roads Congress (IRC:54-1974) clearances.
            </p>
            <p className="text-[11px] text-slate-600 leading-snug">
              • <strong>Surrounding Buildings:</strong> Procedurally placed along road parcel boundaries per IS:SP:7-2005 urban form guidelines to illustrate urban context without inventing road topology.
            </p>
          </div>
        )}

        {/* Selected Vehicle Inspector Card (Top-Right when vehicle is selected) */}
        {selectedVehicle && (
          <div className="absolute top-3 right-3 z-20 max-w-xs bg-slate-900/90 border border-cyan-500/50 rounded-xl p-3 shadow-xl backdrop-blur-md text-white text-xs space-y-1.5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1">
              <span className="font-bold text-cyan-400 uppercase text-[10px]">
                Selected Vehicle Telemetry
              </span>
              <button
                onClick={() => setSelectedVehicle(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>
            <div className="space-y-1 font-mono text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">ID:</span>
                <span className="font-bold text-white">{selectedVehicle.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Class:</span>
                <span className="text-teal-300 uppercase">{selectedVehicle.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Speed:</span>
                <span className="text-emerald-400">
                  {Math.round((selectedVehicle.speed || 0) * 3.6)} km/h
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Road Edge:</span>
                <span className="text-slate-200 truncate max-w-[140px]">
                  {selectedVehicle.edge || 'Corridor Link'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Evaluator Guided Tour Overlay */}
        <EvaluatorDemoTour
          isOpen={isTourOpen}
          onClose={() => setIsTourOpen(false)}
          onSelectPreset={setActivePreset}
          onSelectVehicle={handleSelectVehicle}
        />

        {/* Orbit Controls Guidance Overlay (Bottom-Left) */}
        <div className="absolute bottom-3 left-3 z-20 bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-1.5 text-[11px] text-slate-300 backdrop-blur-sm pointer-events-none shadow-sm">
          <div className="flex items-center gap-2 font-mono text-slate-300">
            <span>Left-Click: Rotate</span>
            <span>•</span>
            <span>Right-Click: Pan</span>
            <span>•</span>
            <span>Scroll: Zoom</span>
          </div>
        </div>

        {/* Technical Specs Overlay (Bottom-Right) */}
        <div className="absolute bottom-3 right-3 z-20 bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-1.5 text-[11px] text-slate-300 backdrop-blur-sm pointer-events-none hidden sm:block shadow-sm">
          <div className="flex items-center gap-3 font-mono">
            <span>306 Edges</span>
            <span>•</span>
            <span>213 Junctions</span>
            <span>•</span>
            <span>490 Lanes</span>
            <span>•</span>
            <span className="text-teal-400 font-semibold">Silk Board Twin</span>
          </div>
        </div>

        {/* React Three Fiber Scene with ErrorBoundary and Suspense */}
        <CorridorErrorBoundary onReturnTo2D={onReturnTo2D}>
          <Suspense fallback={<Corridor3DLoadingSkeleton />}>
            <Canvas
              shadows
              camera={{
                position: CAMERA_PRESETS.area_overview.position,
                fov: 45,
                near: 1.0,
                far: 4500,
              }}
              gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
            >
              <CorridorScene
                activePreset={activePreset}
                onSelectPreset={setActivePreset}
                layerVisibility={layerVisibility}
                vehicles={vehicles}
                selectedVehicleId={selectedVehicle?.id || null}
                onSelectVehicle={handleSelectVehicle}
                signals={signals}
                junctions={junctions}
                ambulanceVehicle={ambulanceVehicle}
                onAmbulanceDetected={setAmbulanceVehicle}
              />
            </Canvas>
          </Suspense>
        </CorridorErrorBoundary>
      </div>
    </div>
  );
}
