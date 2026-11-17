import { after, describe, it } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const vite = await createServer({
  configFile: resolve(frontendRoot, 'vite.config.js'),
  root: frontendRoot,
  server: { middlewareMode: true },
  appType: 'custom',
  logLevel: 'error',
});

const [{ OverviewKPIs }, { EmissionAnalytics }, { SimulationControls }, { ControllerComparison }, { ResearchOverviewView }, { Series4BView }, { Series4CLiveMonitorView }, { Series4EView }] = await Promise.all([
  vite.ssrLoadModule('/src/components/OverviewKPIs.jsx'),
  vite.ssrLoadModule('/src/components/EmissionAnalytics.jsx'),
  vite.ssrLoadModule('/src/components/SimulationControls.jsx'),
  vite.ssrLoadModule('/src/components/ControllerComparison.jsx'),
  vite.ssrLoadModule('/src/components/Research/ResearchOverviewView.jsx'),
  vite.ssrLoadModule('/src/components/Research/Series4BView.jsx'),
  vite.ssrLoadModule('/src/components/Research/Series4CLiveMonitorView.jsx'),
  vite.ssrLoadModule('/src/components/Research/Series4EView.jsx'),
]);

after(async () => vite.close());

function render(Component, props) {
  return renderToStaticMarkup(React.createElement(Component, props));
}

describe('dashboard metric components', () => {
  it('formats metrics with units and distinguishes snapshot wait from cumulative delay', () => {
    const html = render(OverviewKPIs, {
      metrics: {
        total_vehicles: 27,
        throughput_vehicles: 101,
        mean_speed_kmh: 43.087,
        mean_instantaneous_waiting_time_s: 353.63,
        cumulative_delay_veh_s: 7657,
        total_co2_kg: 45.2659,
        total_nox_g: 36.9753,
        total_fuel_liters: 19.5378,
      },
      simStatus: { running: true, paused: false },
    });

    for (const text of [
      '3 / 3', 'Active Vehicles', '27', 'Completed corridor trips', '43.09 km/h',
      'Mean Snapshot Wait', '353.63 s', 'Cumulative Delay', '7657.00 veh·s',
      '45.2659 kg', '36.9753 g', '19.5378 L',
      'Vehicles currently in network', 'Gasoline equivalent',
    ]) assert.ok(html.includes(text), `expected dashboard markup to include ${text}`);
    assert.ok(html.includes('Estimated gasoline equivalent using ρ = 0.75 kg/L'));
    assert.ok(!html.includes('truncate'));
    assert.ok(!html.includes('Last completed simulation snapshot'));
  });

  it('renders unavailable KPI and emissions values as unavailable, not zero', () => {
    const kpis = render(OverviewKPIs, { metrics: null, simStatus: { running: false } });
    const stoppedSnapshot = render(OverviewKPIs, {
      metrics: { total_vehicles: 0 },
      simStatus: { status: 'STOPPED', running: false, paused: false },
    });
    const analytics = render(EmissionAnalytics, { metrics: null, history: [] });

    assert.ok(kpis.includes('—'));
    assert.ok(stoppedSnapshot.includes('Last completed simulation snapshot'));
    assert.ok(analytics.includes('—'));
    assert.ok(!analytics.includes('0.0000'));
    assert.ok(analytics.includes('Awaiting simulation telemetry data points'));
  });

  it('renders the chart state for accumulated history and the single-snapshot state', () => {
    const onePoint = render(EmissionAnalytics, {
      metrics: { total_co2_kg: 1, total_fuel_liters: 0.4 },
      history: [{ time: '1.0', co2_kg: 1, fuel_liters: 0.4, nox_g: null }],
    });
    const multiplePoints = render(EmissionAnalytics, {
      metrics: { total_co2_kg: 2, total_fuel_liters: 0.8 },
      history: [
        { time: '1.0', co2_kg: 1, fuel_liters: 0.4, nox_g: null },
        { time: '2.0', co2_kg: 2, fuel_liters: 0.8, nox_g: null },
      ],
    });

    assert.ok(onePoint.includes('One current snapshot is available'));
    assert.ok(!multiplePoints.includes('One current snapshot is available'));
    assert.ok(!multiplePoints.includes('Awaiting simulation telemetry data points'));
  });

  it('exposes start controls after stopped and completed runs, and stop controls while running', () => {
    for (const status of ['STOPPED', 'COMPLETED']) {
      const html = render(SimulationControls, {
        simStatus: { status, running: false, paused: false, simulation_time: 600, duration: 600 },
      });
      assert.ok(html.includes('Start Simulation'));
      assert.ok(!html.includes('>Stop</span>'));
    }

    const running = render(SimulationControls, {
      simStatus: { status: 'RUNNING', running: true, paused: false, simulation_time: 12, duration: 600 },
    });
    assert.ok(running.includes('Pause'));
    assert.ok(running.includes('>Stop</span>'));
    assert.ok(!running.includes('Start Simulation'));
  });
  it('renders controller comparison with implemented badges, capabilities, and 10-seed master metrics', () => {
    const mockCompareData = {
      network: 'Silk Board Corridor (J1 -> J2 -> J3)',
      benchmark_name: 'Authoritative 10-Seed Master Benchmark',
      benchmark_duration_s: 900,
      seeds_count: 10,
      controllers: [
        {
          controller_name: 'Fixed-Time Baseline',
          status: 'Implemented',
          description: 'Standard pre-timed cycle plan',
          is_implemented: true,
          available_for_inference: true,
          has_trained_checkpoint: false,
          mean_travel_time_s: 90.02,
          mean_speed_kmh: 28.21,
          cumulative_delay_veh_s: 12373.2,
          mean_queue: 13.75,
          completed_trips: 109.0,
          total_co2_kg: 55.58,
          total_fuel_liters: 23.99,
        },
        {
          controller_name: 'Coordinated Adaptive Controller',
          status: 'Implemented',
          description: 'Dynamic queue-proportional phase allocation',
          is_implemented: true,
          available_for_inference: true,
          has_trained_checkpoint: false,
          mean_travel_time_s: 49.87,
          mean_speed_kmh: 37.98,
          cumulative_delay_veh_s: 5836.8,
          mean_queue: 6.49,
          completed_trips: 109.0,
          total_co2_kg: 42.72,
          total_fuel_liters: 18.44,
        },
        {
          controller_name: 'Double-DQN (Stage A)',
          status: 'Implemented',
          description: 'Multi-agent Double-DQN with dueling architecture',
          is_implemented: true,
          available_for_inference: true,
          has_trained_checkpoint: true,
          mean_travel_time_s: 56.64,
          mean_speed_kmh: 31.46,
          cumulative_delay_veh_s: 8024.4,
          mean_queue: 8.92,
          completed_trips: 109.0,
          total_co2_kg: 47.15,
          total_fuel_liters: 20.35,
        },
        {
          controller_name: 'PPO (Stage A)',
          status: 'Implemented',
          description: 'Multi-agent discrete actor-critic policy',
          is_implemented: true,
          available_for_inference: true,
          has_trained_checkpoint: true,
          mean_travel_time_s: 85.50,
          mean_speed_kmh: 25.56,
          cumulative_delay_veh_s: 12163.6,
          mean_queue: 13.52,
          completed_trips: 109.0,
          total_co2_kg: 55.03,
          total_fuel_liters: 23.76,
        },
      ],
      historical_5seed_controllers: [
        {
          controller_name: 'Double-DQN (Historical 8-Ep Prototype)',
          status: 'Historical Artifact',
          description: 'Early non-converged prototype',
          is_implemented: true,
          available_for_inference: true,
          has_trained_checkpoint: true,
          mean_travel_time_s: null,
          completed_trips: 0.0,
        },
      ],
    };

    const html = render(ControllerComparison, { compareData: mockCompareData });

    // 1. All four controllers present
    assert.ok(html.includes('Fixed-Time Baseline'));
    assert.ok(html.includes('Coordinated Adaptive Controller'));
    assert.ok(html.includes('Double-DQN (Stage A)'));
    assert.ok(html.includes('PPO (Stage A)'));

    // 2. All display Implemented, none display Not implemented
    assert.ok(!html.includes('Not implemented'), 'No controller should display Not implemented');
    assert.ok(html.includes('Implemented'));

    // 3. Capability badges rendered
    assert.ok(html.includes('Live Inference'));
    assert.ok(html.includes('Trained Checkpoint'));

    // 4. Benchmark metadata rendered
    assert.ok(html.includes('Authoritative 10-Seed Master Benchmark'));
    assert.ok(html.includes('N=10 seeds'));
    assert.ok(html.includes('900s duration'));

    // 5. DQN Stage A metrics verified
    assert.ok(html.includes('56.64s'));
    assert.ok(html.includes('31.46 km/h'));
    assert.ok(html.includes('109 / 109'));

    // 6. MAPPO is not presented as part of the 4-controller comparison
    assert.ok(!html.includes('MAPPO (Stage A)'), 'MAPPO should not be in the 4-controller table');
  });

  it('renders research overview with all series and freeze statuses', () => {
    const mockOverview = {
      title: 'Bengaluru Silk Board Research Program',
      phase: 'Phase 4: Confirmatory MARL Experimental Program',
      description: 'Comprehensive empirical research program.',
      overall_progress: {
        total_evaluations_completed: 446,
        total_checkpoints_preserved: 70,
      },
      series_list: [
        {
          series_id: 'Series 4A',
          name: 'Safety Shielding Formal Verification',
          hypothesis: 'Shield prevents collisions.',
          status: 'COMPLETE_AND_FROZEN',
          algorithm: 'MAPPO + Shield',
          runs_total: 5,
          evals_total: 40,
        },
        {
          series_id: 'Series 4B',
          name: 'Observation Space Dimensionality Ablation',
          hypothesis: '14D provides optimal state representation.',
          status: 'COMPLETE_AND_FROZEN',
          algorithm: 'MAPPO vs Double-DQN',
          runs_total: 30,
          evals_total: 300,
        },
        {
          series_id: 'Series 4C',
          name: 'Cooperative Reward Coupling Mechanism Ablation',
          hypothesis: 'Balanced reward coupling yields superior coordination.',
          status: 'IN_PROGRESS',
          algorithm: 'MAPPO (14D)',
          runs_total: 25,
          evals_total: 250,
        },
      ],
    };

    const html = render(ResearchOverviewView, { data: mockOverview });
    assert.ok(html.includes('Series 4A'));
    assert.ok(html.includes('Series 4B'));
    assert.ok(html.includes('Series 4C'));
    assert.ok(html.includes('Complete &amp; Frozen'));
    assert.ok(html.includes('Active Training (Series 4C)'));
    assert.ok(html.includes('446'));
  });

  it('renders Series 4B view with complete and frozen status and LMM variance', () => {
    const mock4B = {
      series: 'Series 4B',
      status: 'COMPLETE_AND_FROZEN',
      configurations: {
        MAPPO_14D: { metrics: { mean_corridor_travel_time_s: { mean: 71.97, std: 6.30 } } },
        DQN_14D: { metrics: { mean_corridor_travel_time_s: { mean: 74.07, std: 11.20 } } },
      },
      hierarchical_inference: {
        variance_decomposition: { between_model_variance: 15.42, residual_variance: 18.91, icc: 0.449 },
      },
    };

    const html = render(Series4BView, { data: mock4B });
    assert.ok(html.includes('COMPLETE AND FROZEN'));
    assert.ok(html.includes('Series 4B: Observation Space Dimensionality Ablation'));
    assert.ok(html.includes('Variance Decomposition (LMM)'));
    assert.ok(html.includes('0.449'));
    assert.ok(html.includes('MAPPO_14D'));
  });

  it('renders Series 4C live monitor with active run and safety notice', () => {
    const mock4C = {
      series: 'Series 4C',
      status: 'IN_PROGRESS',
      completed_training_runs: 0,
      total_planned_runs: 25,
      completed_evaluations: 0,
      total_planned_evaluations: 250,
      current_run: {
        run_key: 'beta_000_seed101',
        beta: 0.0,
        train_seed: 101,
        current_episode: 66,
        total_episodes: 150,
        progress_pct: 44.0,
      },
      runs_summary: [
        {
          run_key: 'beta_000_seed101',
          beta: 0.0,
          train_seed: 101,
          training_status: 'TRAINING',
          training_wall_time_s: 0.0,
          has_checkpoint: false,
          evaluations_completed: 0,
          evaluations_target: 10,
        },
      ],
      recent_events: ['Ep 50/150: Reward=-33.30'],
    };

    const html = render(Series4CLiveMonitorView, { statusData: mock4C, historyData: { episodes: [] } });
    assert.ok(html.includes('ACTIVE EXECUTION IN PROGRESS'));
    assert.ok(html.includes('beta_000_seed101'));
    assert.ok(html.includes('Ep 66'));
    assert.ok(html.includes('Read-Only Research Monitor'));
  });

  it('renders Series 4E passenger weighting view with matched pairs', () => {
    const mock4E = {
      series: 'Series 4E',
      status: 'COMPLETED_PRELIMINARY',
      per_formulation: {
        delay_centric: { mean_corridor_travel_time_s: { mean: 82.3 } },
        passenger_weighted: { mean_corridor_travel_time_s: { mean: 79.1 } },
      },
    };

    const html = render(Series4EView, { data: mock4E });
    assert.ok(html.includes('PRELIMINARY COMPLETE'));
    assert.ok(html.includes('Passenger-Weighted vs Vehicle-Centric'));
    assert.ok(html.includes('Delay-Centric'));
    assert.ok(html.includes('Passenger-Weighted'));
  });
});
