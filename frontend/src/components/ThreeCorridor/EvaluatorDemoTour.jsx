/**
 * frontend/src/components/ThreeCorridor/EvaluatorDemoTour.jsx
 *
 * Automated Evaluator Walkthrough & Demonstration Mode.
 * Guides evaluators and stakeholders through the 3D digital twin with curated camera angles,
 * architectural and traffic context, AI coordination mechanisms, and live emergency preemption.
 */

import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  ChevronRight,
  ChevronLeft,
  X,
  Sparkles,
  CheckCircle2,
  Activity,
  ShieldCheck,
  Flame,
} from 'lucide-react';

export const DEMO_STAGES = Object.freeze([
  {
    id: 'area_overview',
    preset: 'area_overview',
    title: '1. Area-Wide Urban Network Overview',
    subtitle: 'Bengaluru Central Silk Board Traffic Basin',
    badge: 'Digital Twin Scope',
    icon: Sparkles,
    content:
      'This 3D digital twin models 306 edges, 213 junctions, and 490 lanes covering the Central Silk Board traffic basin in Bengaluru. Notice the multi-tier road hierarchy: ground arterial roads, depressed underpasses, and elevated flyovers (+8.0m elevation).',
    metrics: [
      { label: 'Network Extent', value: '3.3 km × 3.0 km' },
      { label: 'Active Edges', value: '306 Ground Truth' },
      { label: 'Road Lanes', value: '490 Lanes (IRC:54)' },
    ],
  },
  {
    id: 'corridor_arterial',
    preset: 'overview',
    title: '2. Hosur Road Arterial Corridor',
    subtitle: 'J1 Madiwala ➔ J2 Silk Board ➔ J3 Rupena Agrahara',
    badge: '1,250m Corridor',
    icon: Activity,
    content:
      'Hosur Road is Bengaluru’s primary southeastern artery connecting Koramangala, BTM Layout, and Electronic City. Traffic flows sequentially through J1 (Madiwala Checkpost), J2 (Central Silk Board Rotary), and J3 (Rupena Agrahara).',
    metrics: [
      { label: 'Corridor Span', value: '1,250 Meters' },
      { label: 'Controlled TLS', value: '3 Junctions' },
      { label: 'Flow Direction', value: 'North ➔ South Dual' },
    ],
  },
  {
    id: 'j2_bottleneck',
    preset: 'J2',
    title: '3. Central Silk Board Congestion Bottleneck',
    subtitle: 'The Notorious Silk Board Rotary Junction',
    badge: 'Baseline Gridlock',
    icon: Flame,
    content:
      'Central Silk Board is historically notorious for severe congestion. Under uncoordinated Fixed-Time baseline control, lack of progression causes queue spillbacks that lock the rotary, with 10-seed benchmark corridor travel times averaging 90.02s per vehicle and cumulative delays exceeding 12,370 veh·s.',
    metrics: [
      { label: 'Baseline Travel Time', value: '90.02 ± 0.40 s' },
      { label: 'Baseline Mean Speed', value: '28.21 km/h' },
      { label: 'Cumulative Delay', value: '12,373 veh·s' },
    ],
  },
  {
    id: 'ai_coordination',
    preset: 'J2',
    title: '4. AI & Coordinated Adaptive Signal Control',
    subtitle: 'Multi-Agent Reinforcement Learning + Safety Shield',
    badge: 'MARL PPO / DQN',
    icon: ShieldCheck,
    content:
      'The Smart Traffic Coordination System applies MARL (Double-DQN and PPO) alongside Coordinated Adaptive control. Dynamic green waves clear vehicle platoons across signals: Coordinated Adaptive achieves 49.87s (-44.61%), MARL Double-DQN achieves 56.64s (-37.08%), and MARL PPO achieves 85.50s (-5.01%), all benchmarked against the Fixed-Time baseline (90.02s) under a 60-second maximum-green safety shield.',
    metrics: [
      { label: 'Coordinated Adaptive', value: '49.87s (-44.61%)' },
      { label: 'MARL Double-DQN', value: '56.64s (-37.08%)' },
      { label: 'MARL PPO', value: '85.50s (-5.01%)' },
    ],
  },
  {
    id: 'emergency_preemption',
    preset: 'J1',
    title: '5. Emergency Vehicle Green-Wave Priority',
    subtitle: 'Autonomous Upstream Detection & Corridor Clearance',
    badge: 'Emergency Wave',
    icon: Sparkles,
    content:
      'When an ambulance enters the corridor, it is detected 250m upstream. Conflicting green phases execute safe yellow clearance transitions, and downstream signals lock into an unbroken green wave, slashing ambulance corridor transit times by up to 52%.',
    metrics: [
      { label: 'Detection Range', value: '250 Meters Upstream' },
      { label: 'Preemption Mode', value: 'Green-Wave Lock' },
      { label: 'Emergency Transit', value: 'Up to -52.1% Time' },
    ],
  },
  {
    id: 'performance_summary',
    preset: 'area_overview',
    title: '6. Environmental & Operational Performance',
    subtitle: 'Rigorous 10-Seed Benchmark & Microscopic Validation',
    badge: 'Statistically Verified',
    icon: CheckCircle2,
    content:
      'All improvements are backed by our authoritative 10-seed, 40-run master benchmark (statistical_analysis.json). Note: Throughput remains 100% completed across all controllers (378 veh / 900s = 1,512 veh/hr); the 44.61% gain represents travel-time reduction (latency), kept strictly distinct from network throughput.',
    metrics: [
      { label: 'Baseline Travel Time', value: '90.02 ± 0.40 s' },
      { label: 'Best Travel Time', value: '49.87 ± 0.78 s' },
      { label: 'Throughput Served', value: '1,512 veh/h (100%)' },
    ],
  },
]);

export function EvaluatorDemoTour({
  isOpen,
  onClose,
  onSelectPreset,
  onSelectVehicle,
}) {
  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  const stage = DEMO_STAGES[currentStageIdx];
  const IconComponent = stage.icon;

  // Sync camera whenever stage changes
  useEffect(() => {
    if (!isOpen) return;
    if (stage && onSelectPreset) {
      onSelectPreset(stage.preset);
    }
  }, [isOpen, currentStageIdx, stage, onSelectPreset]);

  // Auto-play timer (7 seconds per stage)
  useEffect(() => {
    if (!isOpen || !isAutoPlaying) return;

    const timer = setInterval(() => {
      setCurrentStageIdx((prev) => {
        if (prev >= DEMO_STAGES.length - 1) {
          setIsAutoPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 7000);

    return () => clearInterval(timer);
  }, [isOpen, isAutoPlaying]);

  if (!isOpen) return null;

  const handleNext = () => {
    if (currentStageIdx < DEMO_STAGES.length - 1) {
      setCurrentStageIdx((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStageIdx > 0) {
      setCurrentStageIdx((prev) => prev - 1);
    }
  };

  return (
    <div className="absolute top-4 right-4 z-40 max-w-md w-full bg-slate-900/95 border border-teal-500/50 rounded-2xl shadow-2xl backdrop-blur-md p-4 text-white animate-in fade-in slide-in-from-top-3 duration-300">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30">
            <IconComponent className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-bold tracking-widest text-teal-400 uppercase">
              Evaluator Tour • Step {currentStageIdx + 1} of {DEMO_STAGES.length}
            </span>
            <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
              <span>{stage.title}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          title="Exit Tour"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Narrative content card */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-[11px] text-teal-300 font-medium">
          <span>{stage.subtitle}</span>
          <span className="px-2 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-[9px] font-mono font-bold text-teal-300 uppercase">
            {stage.badge}
          </span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-normal">
          {stage.content}
        </p>

        {/* Highlight Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 pt-1">
          {stage.metrics.map((m, idx) => (
            <div
              key={idx}
              className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-2 text-center"
            >
              <div className="text-[9px] text-slate-400 font-medium uppercase tracking-wider">
                {m.label}
              </div>
              <div className="text-xs font-bold text-teal-300 font-mono mt-0.5">
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden mt-3.5 mb-3">
        <div
          className="bg-gradient-to-r from-teal-500 to-cyan-400 h-full transition-all duration-300"
          style={{
            width: `${((currentStageIdx + 1) / DEMO_STAGES.length) * 100}%`,
          }}
        />
      </div>

      {/* Controls Footer */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
              isAutoPlaying
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
            title={isAutoPlaying ? 'Pause Auto-Tour' : 'Auto-Play Tour'}
          >
            {isAutoPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            <span className="text-[11px]">{isAutoPlaying ? 'Pause' : 'Auto-Play'}</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handlePrev}
            disabled={currentStageIdx === 0}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-300 border border-slate-700 transition"
            title="Previous Step"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <button
            onClick={handleNext}
            disabled={currentStageIdx === DEMO_STAGES.length - 1}
            className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-40 disabled:hover:bg-teal-600 text-white font-semibold text-xs flex items-center gap-1 transition shadow"
            title="Next Step"
          >
            <span>Next</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
