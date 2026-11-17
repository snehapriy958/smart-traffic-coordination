/**
 * frontend/src/components/ThreeCorridor/TrafficSignals3D.jsx
 *
 * 3D Traffic Signal Gantries with Dynamic Emissive Lamp States.
 * Renders physical cantilever signal structures at J1, J2, and J3 with
 * live Red / Amber / Green aspects reflecting real-time signal controller phases.
 */

import React, { useMemo } from 'react';
import * as THREE from 'three';

const JUNCTION_SIGNAL_CONFIGS = Object.freeze([
  {
    junctionId: 'J1',
    tlsId: '1617743335',
    name: 'J1 Madiwala Checkpost',
    polePosition: [-82.0, 0.0, -122.0],
    armOffset: [3.5, 5.8, -4.5],
    rotationY: Math.PI * 0.65,
  },
  {
    junctionId: 'J2',
    tlsId: 'GS_cluster_34645395_40696222_40696223_40696227',
    name: 'J2 Central Silk Board Rotary',
    polePosition: [-2.0, 0.0, 18.0],
    armOffset: [4.0, 6.2, -4.0],
    rotationY: Math.PI * 0.62,
  },
  {
    junctionId: 'J3',
    tlsId: '6970466614',
    name: 'J3 Rupena Agrahara',
    polePosition: [76.0, 0.0, 128.0],
    armOffset: [3.8, 5.8, 4.2],
    rotationY: Math.PI * 0.60,
  },
]);

/**
 * 3D Traffic Signal Cantilever Gantry with 3-aspect head.
 */
function SignalGantry({ config, signalState, junctionState }) {
  // Determine active signal color from controller state
  const { isRed, isYellow, isGreen } = useMemo(() => {
    const sig = signalState || {};
    const junc = junctionState || {};
    const stateStr = (sig.state || '').toLowerCase();
    const phase = junc.current_phase ?? sig.current_phase ?? 0;

    // Check TraCI state string or phase index
    let green = stateStr.includes('g') || phase === 0 || phase === 2;
    let yellow = stateStr.includes('y') || phase === 1 || phase === 3;
    let red = !green && !yellow;

    if (sig.is_yellow) {
      yellow = true;
      green = false;
      red = false;
    }

    return { isRed: red, isYellow: yellow, isGreen: green };
  }, [signalState, junctionState]);

  const { polePosition, armOffset, rotationY } = config;

  return (
    <group position={polePosition} rotation={[0, rotationY, 0]}>
      {/* Vertical Steel Mast Pole */}
      <mesh position={[0, 3.2, 0]} castShadow>
        <cylinderGeometry args={[0.18, 0.22, 6.4, 12]} />
        <meshStandardMaterial color="#475569" roughness={0.5} metalness={0.7} />
      </mesh>

      {/* Horizontal Cantilever Arm over roadway */}
      <mesh position={[armOffset[0] / 2.0, 6.1, 0]}>
        <cylinderGeometry args={[0.12, 0.15, armOffset[0], 8]} rotation={[0, 0, Math.PI / 2]} />
        <meshStandardMaterial color="#475569" roughness={0.5} metalness={0.7} />
      </mesh>

      {/* Signal Head Housing Box */}
      <group position={[armOffset[0], 5.6, 0]}>
        <mesh castShadow>
          <boxGeometry args={[0.7, 1.8, 0.45]} />
          <meshStandardMaterial color="#0f172a" roughness={0.8} metalness={0.2} />
        </mesh>

        {/* Visor hoods */}
        <mesh position={[0, 0.55, 0.25]}>
          <boxGeometry args={[0.5, 0.1, 0.3]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>
        <mesh position={[0, 0.0, 0.25]}>
          <boxGeometry args={[0.5, 0.1, 0.3]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>
        <mesh position={[0, -0.55, 0.25]}>
          <boxGeometry args={[0.5, 0.1, 0.3]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>

        {/* Red Aspect Light (Top) */}
        <mesh position={[0, 0.55, 0.23]}>
          <sphereGeometry args={[0.18, 12, 12]} />
          <meshStandardMaterial
            color={isRed ? '#ef4444' : '#450a0a'}
            emissive={isRed ? '#ef4444' : '#000000'}
            emissiveIntensity={isRed ? 2.5 : 0.0}
            roughness={0.2}
          />
        </mesh>
        {isRed && (
          <pointLight position={[0, 0.55, 0.6]} color="#ef4444" intensity={1.5} distance={12} />
        )}

        {/* Yellow Aspect Light (Middle) */}
        <mesh position={[0, 0.0, 0.23]}>
          <sphereGeometry args={[0.18, 12, 12]} />
          <meshStandardMaterial
            color={isYellow ? '#f59e0b' : '#451a03'}
            emissive={isYellow ? '#f59e0b' : '#000000'}
            emissiveIntensity={isYellow ? 2.5 : 0.0}
            roughness={0.2}
          />
        </mesh>
        {isYellow && (
          <pointLight position={[0, 0.0, 0.6]} color="#f59e0b" intensity={1.5} distance={12} />
        )}

        {/* Green Aspect Light (Bottom) */}
        <mesh position={[0, -0.55, 0.23]}>
          <sphereGeometry args={[0.18, 12, 12]} />
          <meshStandardMaterial
            color={isGreen ? '#10b981' : '#064e3b'}
            emissive={isGreen ? '#10b981' : '#000000'}
            emissiveIntensity={isGreen ? 2.5 : 0.0}
            roughness={0.2}
          />
        </mesh>
        {isGreen && (
          <pointLight position={[0, -0.55, 0.6]} color="#10b981" intensity={1.5} distance={12} />
        )}
      </group>
    </group>
  );
}

/**
 * 3D Traffic Signals System for Corridor Scene.
 */
export function TrafficSignals3D({ signals = {}, junctions = {} }) {
  return (
    <group name="corridor_3d_traffic_signals">
      {JUNCTION_SIGNAL_CONFIGS.map((cfg) => {
        const sig = signals[cfg.junctionId] || signals[cfg.tlsId] || null;
        const junc = junctions[cfg.junctionId] || null;
        return (
          <SignalGantry
            key={cfg.junctionId}
            config={cfg}
            signalState={sig}
            junctionState={junc}
          />
        );
      })}
    </group>
  );
}
