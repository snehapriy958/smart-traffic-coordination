/**
 * frontend/src/components/ThreeCorridor/VehicleLayer.jsx
 *
 * Microscopic 3D Traffic Flow & Vehicle Tracking Engine.
 * Renders real moving SUMO vehicles (Cars, BMTC Buses, Motorcycles, Heavy Trucks, Ambulances)
 * with smooth 60 FPS spatial interpolation, heading rotation, and active emergency beacons.
 */

import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

import {
  sumoToThreeCoords,
  sumoHeadingToThreeYaw,
  DEFAULT_SCENE_ANCHOR,
} from '../../utils/coordinateTransform.js';

// Deterministic vehicle color generator from string ID
function getVehicleColor(id, type) {
  const t = (type || '').toLowerCase();
  if (t.includes('ambulance') || t.includes('emergency')) return '#ffffff';
  if (t.includes('bus') || t.includes('bmtc')) return '#2563eb'; // BMTC Blue
  if (t.includes('heavy') || t.includes('truck')) return '#ea580c'; // Commercial Orange
  if (t.includes('motorcycle') || t.includes('bike')) return '#0f172a'; // Dark Charcoal

  // Palette for passenger cars
  const carColors = [
    '#f8fafc', // Glacier White
    '#64748b', // Slate Gray
    '#1e293b', // Midnight Black
    '#dc2626', // Crimson Red
    '#2563eb', // Royal Blue
    '#059669', // Emerald Green
    '#d97706', // Amber Gold
    '#9333ea', // Deep Violet
  ];
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  return carColors[Math.abs(hash) % carColors.length];
}

/**
 * Individual 3D Vehicle Mesh with Smooth Lerp Animation.
 */
function SingleVehicle({
  veh,
  isSelected,
  onSelect,
}) {
  const meshRef = useRef();
  const strobeRef = useRef();

  // Three.js target coordinate conversion
  const targetCoords = useMemo(() => {
    return sumoToThreeCoords(veh.x, veh.y, veh.z, 0.0, DEFAULT_SCENE_ANCHOR);
  }, [veh.x, veh.y, veh.z]);

  const targetYaw = useMemo(() => {
    return sumoHeadingToThreeYaw(veh.angle);
  }, [veh.angle]);

  // Persistent motion state for 60 FPS interpolation between 1 Hz SUMO ticks
  const currentPos = useRef(new THREE.Vector3(targetCoords.x, targetCoords.y, targetCoords.z));
  const currentYaw = useRef(targetYaw);

  const vType = (veh.type || 'car').toLowerCase();
  const isAmbulance = vType.includes('ambulance') || vType.includes('emergency');
  const isBus = vType.includes('bus') || vType.includes('bmtc');
  const isTruck = vType.includes('heavy') || vType.includes('truck');
  const isMotorcycle = vType.includes('motorcycle') || vType.includes('bike');

  const baseColor = useMemo(() => getVehicleColor(veh.id, veh.type), [veh.id, veh.type]);

  useFrame((state, delta) => {
    if (!meshRef.current) return;

    // Smooth position interpolation
    const lerpSpeed = Math.min(delta * 9.0, 0.35);
    currentPos.current.lerp(
      new THREE.Vector3(targetCoords.x, targetCoords.y, targetCoords.z),
      lerpSpeed
    );
    meshRef.current.position.copy(currentPos.current);

    // Smooth heading angle unwrapped interpolation
    const diff = ((targetYaw - currentYaw.current + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    currentYaw.current += diff * lerpSpeed;
    meshRef.current.rotation.y = currentYaw.current;

    // Emergency ambulance dual-tone strobe beacon animation
    if (isAmbulance && strobeRef.current) {
      const t = state.clock.getElapsedTime() * 8.0;
      const flash = Math.sin(t) > 0;
      strobeRef.current.material.color.set(flash ? '#ef4444' : '#3b82f6');
      strobeRef.current.material.emissive.set(flash ? '#ef4444' : '#3b82f6');
    }
  });

  return (
    <group
      ref={meshRef}
      position={[targetCoords.x, targetCoords.y, targetCoords.z]}
      rotation={[0, targetYaw, 0]}
      onClick={(e) => {
        e.stopPropagation();
        onSelect && onSelect(veh);
      }}
      cursor="pointer"
    >
      {/* 1. Passenger Car Model */}
      {!isBus && !isTruck && !isMotorcycle && !isAmbulance && (
        <group>
          {/* Lower Chassis */}
          <mesh position={[0, 0.4, 0]} castShadow>
            <boxGeometry args={[1.8, 0.55, 4.2]} />
            <meshStandardMaterial color={baseColor} roughness={0.3} metalness={0.7} />
          </mesh>
          {/* Cabin Roof */}
          <mesh position={[0, 0.95, -0.2]} castShadow>
            <boxGeometry args={[1.5, 0.6, 2.3]} />
            <meshStandardMaterial color="#0f172a" roughness={0.1} metalness={0.9} />
          </mesh>
          {/* Headlights (Front is +Z in canonical orientation) */}
          <mesh position={[0.65, 0.45, 2.11]}>
            <boxGeometry args={[0.3, 0.15, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
          <mesh position={[-0.65, 0.45, 2.11]}>
            <boxGeometry args={[0.3, 0.15, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
          {/* Taillights */}
          <mesh position={[0.65, 0.45, -2.11]}>
            <boxGeometry args={[0.3, 0.15, 0.05]} />
            <meshBasicMaterial color="#ef4444" />
          </mesh>
          <mesh position={[-0.65, 0.45, -2.11]}>
            <boxGeometry args={[0.3, 0.15, 0.05]} />
            <meshBasicMaterial color="#ef4444" />
          </mesh>
        </group>
      )}

      {/* 2. BMTC Bus Model */}
      {isBus && (
        <group>
          {/* Main Bus Body */}
          <mesh position={[0, 1.6, 0]} castShadow>
            <boxGeometry args={[2.6, 2.8, 11.5]} />
            <meshStandardMaterial color="#2563eb" roughness={0.4} metalness={0.5} />
          </mesh>
          {/* White Upper Band / Roof */}
          <mesh position={[0, 3.05, 0]}>
            <boxGeometry args={[2.55, 0.3, 11.4]} />
            <meshStandardMaterial color="#f8fafc" roughness={0.5} />
          </mesh>
          {/* Window Strip */}
          <mesh position={[0, 2.1, 0]}>
            <boxGeometry args={[2.64, 0.8, 10.5]} />
            <meshStandardMaterial color="#0f172a" roughness={0.1} metalness={0.8} />
          </mesh>
          {/* Headlights */}
          <mesh position={[0.9, 0.8, 5.76]}>
            <boxGeometry args={[0.4, 0.25, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
          <mesh position={[-0.9, 0.8, 5.76]}>
            <boxGeometry args={[0.4, 0.25, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
        </group>
      )}

      {/* 3. Motorcycle / 2-Wheeler */}
      {isMotorcycle && (
        <group>
          {/* Bike Chassis */}
          <mesh position={[0, 0.45, 0]} castShadow>
            <boxGeometry args={[0.6, 0.6, 2.0]} />
            <meshStandardMaterial color="#1e293b" roughness={0.5} metalness={0.8} />
          </mesh>
          {/* Rider Torso & Helmet */}
          <mesh position={[0, 1.1, -0.1]} castShadow>
            <boxGeometry args={[0.55, 0.7, 0.6]} />
            <meshStandardMaterial color="#0284c7" roughness={0.6} />
          </mesh>
          <mesh position={[0, 1.6, -0.05]}>
            <sphereGeometry args={[0.26, 8, 8]} />
            <meshStandardMaterial color="#f1f5f9" roughness={0.2} metalness={0.6} />
          </mesh>
          {/* Headlight */}
          <mesh position={[0, 0.65, 1.02]}>
            <boxGeometry args={[0.2, 0.2, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
        </group>
      )}

      {/* 4. Heavy Commercial Truck */}
      {isTruck && (
        <group>
          {/* Driver Cab */}
          <mesh position={[0, 1.5, 3.2]} castShadow>
            <boxGeometry args={[2.5, 2.6, 2.8]} />
            <meshStandardMaterial color="#ea580c" roughness={0.5} metalness={0.6} />
          </mesh>
          {/* Cargo Container Box */}
          <mesh position={[0, 1.8, -1.5]} castShadow>
            <boxGeometry args={[2.5, 3.0, 7.0]} />
            <meshStandardMaterial color="#64748b" roughness={0.7} metalness={0.3} />
          </mesh>
          {/* Headlights */}
          <mesh position={[0.85, 0.8, 4.62]}>
            <boxGeometry args={[0.35, 0.2, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
          <mesh position={[-0.85, 0.8, 4.62]}>
            <boxGeometry args={[0.35, 0.2, 0.05]} />
            <meshBasicMaterial color="#fef08a" />
          </mesh>
        </group>
      )}

      {/* 5. Emergency Ambulance */}
      {isAmbulance && (
        <group>
          {/* Van Body */}
          <mesh position={[0, 1.15, 0]} castShadow>
            <boxGeometry args={[2.1, 1.9, 5.2]} />
            <meshStandardMaterial color="#ffffff" roughness={0.2} metalness={0.4} />
          </mesh>
          {/* Red Cross Stripes on sides */}
          <mesh position={[1.06, 1.2, 0]}>
            <boxGeometry args={[0.02, 0.45, 1.6]} />
            <meshBasicMaterial color="#dc2626" />
          </mesh>
          <mesh position={[1.06, 1.2, 0]}>
            <boxGeometry args={[0.02, 1.4, 0.45]} />
            <meshBasicMaterial color="#dc2626" />
          </mesh>
          <mesh position={[-1.06, 1.2, 0]}>
            <boxGeometry args={[0.02, 0.45, 1.6]} />
            <meshBasicMaterial color="#dc2626" />
          </mesh>
          <mesh position={[-1.06, 1.2, 0]}>
            <boxGeometry args={[0.02, 1.4, 0.45]} />
            <meshBasicMaterial color="#dc2626" />
          </mesh>
          {/* High-intensity Roof Strobe Light */}
          <mesh ref={strobeRef} position={[0, 2.25, 0.6]}>
            <boxGeometry args={[0.7, 0.25, 0.35]} />
            <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={2.5} />
          </mesh>
          {/* Dual Flashing Point Light */}
          <pointLight position={[0, 2.8, 0.6]} color="#ef4444" intensity={3.5} distance={25} />
          {/* Pulsing 3D Emergency Aura Ring */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.2, 0]}>
            <ringGeometry args={[2.5, 3.2, 24]} />
            <meshBasicMaterial color="#ef4444" transparent opacity={0.4} side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}

      {/* Target Reticle Indicator for Selected Vehicle */}
      {isSelected && (
        <group position={[0, isBus ? 4.2 : 2.6, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[1.5, 1.9, 24]} />
            <meshBasicMaterial color="#06b6d4" side={THREE.DoubleSide} />
          </mesh>
          <Html position={[0, 1.2, 0]} center zIndexRange={[120, 0]}>
            <div className="bg-slate-900/90 border border-cyan-400 text-cyan-200 px-2 py-0.5 rounded shadow-lg text-[10px] whitespace-nowrap font-mono pointer-events-none">
              <span className="font-bold text-white uppercase">{veh.id}</span>
              <span className="text-cyan-400 ml-1.5">{Math.round((veh.speed || 0) * 3.6)} km/h</span>
            </div>
          </Html>
        </group>
      )}
    </group>
  );
}

/**
 * Microscopic Vehicle Layer for React Three Fiber.
 */
export function VehicleLayer({
  vehicles = [],
  selectedVehicleId = null,
  onSelectVehicle,
  onAmbulanceDetected,
}) {
  // Track active ambulance presence
  useEffect(() => {
    const amb = vehicles.find((v) => {
      const t = (v.type || '').toLowerCase();
      return t.includes('ambulance') || t.includes('emergency');
    });
    if (amb && onAmbulanceDetected) {
      onAmbulanceDetected(amb);
    }
  }, [vehicles, onAmbulanceDetected]);

  return (
    <group name="microscopic_vehicles_layer">
      {vehicles.map((veh) => (
        <SingleVehicle
          key={veh.id}
          veh={veh}
          isSelected={selectedVehicleId === veh.id}
          onSelect={onSelectVehicle}
        />
      ))}
    </group>
  );
}
