/**
 * frontend/src/components/ThreeCorridor/CorridorScene.jsx
 *
 * 3D Area-Wide Traffic Digital Twin Scene for Bengaluru Central Silk Board.
 * Features:
 *   - Ground-truth SUMO roadway network (ground, flyovers, underpasses, junctions).
 *   - Procedural urban context (commercial tech towers, office blocks, residential mid-rise).
 *   - Bengaluru Garden City landscaping & tree canopies.
 *   - Real-time 3-aspect traffic signals at J1, J2, J3 reflecting controller phases.
 *   - Live microscopic vehicle layer with smooth 60 FPS motion & emergency strobe lights.
 *   - Authentic IRC highway overhead signage.
 *   - Dynamic chase camera for vehicle following and ambulance tracking.
 */

import React, { useMemo, useRef, useEffect } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';

import corridorData from '../../data/corridorNetworkGeometry.json';
import { buildCorridorSceneGeometries, ROAD_STYLE } from '../../utils/roadGeometryBuilder.js';
import {
  buildUrbanBuildingsGeometries,
  buildUrbanLandscapingGeometries,
  HIGHWAY_SIGNS,
  URBAN_STYLE,
} from '../../utils/urbanEnvironmentBuilder.js';
import {
  sumoToThreeCoords,
  sumoHeadingToThreeYaw,
  DEFAULT_SCENE_ANCHOR,
} from '../../utils/coordinateTransform.js';
import { VehicleLayer } from './VehicleLayer.jsx';
import { TrafficSignals3D } from './TrafficSignals3D.jsx';

export const CAMERA_PRESETS = Object.freeze({
  area_overview: {
    position: [-380, 420, 280],
    target: [0, 0, 10],
    label: 'Area Overview',
    desc: 'Bengaluru Silk Board urban network (High Aerial Oblique)',
  },
  overview: {
    position: [-210, 180, 135],
    target: [0, 0, 5],
    label: 'Corridor Overview',
    desc: 'Full J1–J2–J3 arterial spine view (Aerial 3/4 Perspective)',
  },
  J1: {
    position: [-130, 45, -95],
    target: [-79.8, 0, -125.5],
    label: 'J1 Madiwala Checkpost',
    desc: 'Upstream feeder intersection (Ground / Underpass)',
  },
  J2: {
    position: [-55, 55, 65],
    target: [1.13, 8.0, 16.12],
    label: 'J2 Central Silk Board',
    desc: 'Rotary hub & +8.0m elevated flyover deck',
  },
  J3: {
    position: [30, 45, 175],
    target: [79.63, 0, 132.3],
    label: 'J3 Rupena Agrahara',
    desc: 'Downstream exit signal (Ground)',
  },
});

/**
 * Smooth Camera Animation Controller that responds to preset changes and dynamic target tracking.
 */
function CameraController({
  activePreset,
  controlsRef,
  selectedVehicle,
  ambulanceVehicle,
}) {
  const { camera } = useThree();
  const targetPos = useRef(new THREE.Vector3(...CAMERA_PRESETS.overview.position));
  const targetLook = useRef(new THREE.Vector3(...CAMERA_PRESETS.overview.target));
  const isTransitioning = useRef(false);

  useEffect(() => {
    if (activePreset === 'follow_vehicle' || activePreset === 'track_ambulance') {
      isTransitioning.current = false;
      return;
    }
    const preset = CAMERA_PRESETS[activePreset] || CAMERA_PRESETS.overview;
    targetPos.current.set(...preset.position);
    targetLook.current.set(...preset.target);
    isTransitioning.current = true;
  }, [activePreset]);

  useFrame((_, delta) => {
    // Dynamic vehicle chase camera tracking
    if (activePreset === 'follow_vehicle' && selectedVehicle) {
      const c = sumoToThreeCoords(
        selectedVehicle.x,
        selectedVehicle.y,
        selectedVehicle.z,
        0,
        DEFAULT_SCENE_ANCHOR
      );
      const yaw = sumoHeadingToThreeYaw(selectedVehicle.angle);
      const camX = c.x - 16 * Math.sin(yaw);
      const camY = c.y + 8.5;
      const camZ = c.z - 16 * Math.cos(yaw);

      camera.position.lerp(new THREE.Vector3(camX, camY, camZ), 0.08);
      if (controlsRef.current) {
        controlsRef.current.target.lerp(new THREE.Vector3(c.x, c.y + 1.2, c.z), 0.08);
        controlsRef.current.update();
      }
      return;
    }

    // Dynamic ambulance emergency green-wave tracking
    if (activePreset === 'track_ambulance' && ambulanceVehicle) {
      const c = sumoToThreeCoords(
        ambulanceVehicle.x,
        ambulanceVehicle.y,
        ambulanceVehicle.z,
        0,
        DEFAULT_SCENE_ANCHOR
      );
      const yaw = sumoHeadingToThreeYaw(ambulanceVehicle.angle);
      const camX = c.x - 20 * Math.sin(yaw);
      const camY = c.y + 11.0;
      const camZ = c.z - 20 * Math.cos(yaw);

      camera.position.lerp(new THREE.Vector3(camX, camY, camZ), 0.08);
      if (controlsRef.current) {
        controlsRef.current.target.lerp(new THREE.Vector3(c.x, c.y + 1.5, c.z), 0.08);
        controlsRef.current.update();
      }
      return;
    }

    if (!isTransitioning.current) return;

    // Smooth exponential lerp
    const lerpSpeed = Math.min(delta * 4.0, 0.2);
    camera.position.lerp(targetPos.current, lerpSpeed);

    if (controlsRef.current) {
      controlsRef.current.target.lerp(targetLook.current, lerpSpeed);
      controlsRef.current.update();
    }

    if (
      camera.position.distanceTo(targetPos.current) < 0.2 &&
      (!controlsRef.current || controlsRef.current.target.distanceTo(targetLook.current) < 0.2)
    ) {
      camera.position.copy(targetPos.current);
      if (controlsRef.current) {
        controlsRef.current.target.copy(targetLook.current);
      }
      isTransitioning.current = false;
    }
  });

  return null;
}

/**
 * 3D Html Junction Marker badge.
 */
function JunctionMarker({ code, name, elevation, position, onSelect }) {
  return (
    <Html position={position} center zIndexRange={[100, 0]}>
      <button
        onClick={onSelect}
        className="group flex flex-col items-center cursor-pointer transition transform hover:scale-105 focus:outline-none pointer-events-auto"
      >
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/95 border border-teal-500 shadow-md backdrop-blur-sm text-teal-800 hover:border-teal-600 text-xs select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-ping" />
          <span className="font-bold tracking-wider">{code}</span>
          <span className="text-[10px] text-slate-700 font-semibold whitespace-nowrap">{name}</span>
          <span className="text-[9px] px-1 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200 font-mono font-medium">
            {elevation}
          </span>
        </div>
        <div className="w-0.5 h-2 bg-teal-500 shadow-sm" />
        <div className="w-1 h-1 rounded-full bg-teal-600" />
      </button>
    </Html>
  );
}

/**
 * Overhead Direction Highway Signboard Component.
 */
function HighwaySignboard({ sign }) {
  const { position, rotationY, mainText, subText, width, height } = sign;

  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      {/* Supporting Vertical Gantry Columns */}
      <mesh position={[-width / 2.0, -height / 2.0, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.24, 7.5, 8]} />
        <meshStandardMaterial color={URBAN_STYLE.SIGN_FRAME_STEEL} roughness={0.5} metalness={0.7} />
      </mesh>
      <mesh position={[width / 2.0, -height / 2.0, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.24, 7.5, 8]} />
        <meshStandardMaterial color={URBAN_STYLE.SIGN_FRAME_STEEL} roughness={0.5} metalness={0.7} />
      </mesh>

      {/* Overhead Signboard Plate */}
      <mesh castShadow>
        <boxGeometry args={[width, height, 0.35]} />
        <meshStandardMaterial color={URBAN_STYLE.SIGN_PANEL_GREEN} roughness={0.4} metalness={0.2} />
      </mesh>

      {/* Reflective Sign Border */}
      <mesh position={[0, 0, 0.19]}>
        <planeGeometry args={[width - 0.4, height - 0.4]} />
        <meshBasicMaterial color="#ffffff" wireframe />
      </mesh>

      {/* HTML Typography Overlay */}
      <Html position={[0, 0, 0.22]} center transform distanceFactor={18}>
        <div
          className="bg-emerald-800/90 border-2 border-white rounded px-4 py-2 text-white font-sans text-center shadow-lg pointer-events-none select-none"
          style={{ width: `${width * 32}px` }}
        >
          <div className="font-black text-sm tracking-wider uppercase drop-shadow">{mainText}</div>
          <div className="text-[11px] font-bold text-amber-300 tracking-wide mt-0.5 drop-shadow">
            {subText}
          </div>
        </div>
      </Html>
    </group>
  );
}

/**
 * React Three Fiber Scene Component for Bengaluru Silk Board Digital Twin.
 */
export function CorridorScene({
  activePreset = 'overview',
  onSelectPreset,
  layerVisibility = {
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
  },
  vehicles = [],
  selectedVehicleId = null,
  onSelectVehicle,
  signals = {},
  junctions = {},
  ambulanceVehicle = null,
  onAmbulanceDetected,
}) {
  const controlsRef = useRef();

  // Build merged corridor BufferGeometries once
  const geometries = useMemo(() => {
    return buildCorridorSceneGeometries(corridorData);
  }, []);

  // Build procedural urban buildings once
  const urbanGeoms = useMemo(() => {
    return buildUrbanBuildingsGeometries(corridorData);
  }, []);

  // Build procedural tree landscaping once
  const landscapingGeoms = useMemo(() => {
    return buildUrbanLandscapingGeometries(corridorData);
  }, []);

  const selectedVehicle = useMemo(() => {
    if (!selectedVehicleId || !vehicles) return null;
    return vehicles.find((v) => v.id === selectedVehicleId) || null;
  }, [selectedVehicleId, vehicles]);

  return (
    <>
      {/* Interactive OrbitControls */}
      <OrbitControls
        ref={controlsRef}
        makeDefault
        target={[0, 0, 5]}
        enableDamping
        dampingFactor={0.08}
        minDistance={10}
        maxDistance={2200}
        maxPolarAngle={Math.PI / 2.05} // Prevent camera from dipping beneath terrain
      />

      {/* Smooth Camera Preset Transitions & Dynamic Chase Tracking */}
      <CameraController
        activePreset={activePreset}
        controlsRef={controlsRef}
        selectedVehicle={selectedVehicle}
        ambulanceVehicle={ambulanceVehicle}
      />

      {/* High-Fidelity Lighting Rig */}
      <ambientLight intensity={0.85} />
      <directionalLight
        position={[250, 400, 200]}
        intensity={1.6}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-near={10}
        shadow-camera-far={1200}
        shadow-camera-left={-400}
        shadow-camera-right={400}
        shadow-camera-top={400}
        shadow-camera-bottom={-400}
      />
      <directionalLight position={[-250, 180, -180]} intensity={0.65} />
      <hemisphereLight args={['#60a5fa', '#0f172a', 0.45]} />

      {/* Expanded Ground Terrain Plane (Covers entire Silk Board basin) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.15, 0]} receiveShadow>
        <planeGeometry args={[3600, 3600]} />
        <meshStandardMaterial color={ROAD_STYLE.GROUND_TERRAIN} roughness={0.95} metalness={0.05} />
      </mesh>

      {/* Focused Coordinate Grid Guide */}
      <gridHelper args={[1200, 40, '#334155', '#1e293b']} position={[0, -0.1, 0]} />

      {/* 1. Static Infrastructure Road Meshes */}
      {layerVisibility.ground && geometries.groundRoads.attributes?.position && (
        <mesh geometry={geometries.groundRoads} receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.ASPHALT_GROUND}
            roughness={0.82}
            metalness={0.12}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {layerVisibility.flyover && geometries.flyoverRoads.attributes?.position && (
        <mesh geometry={geometries.flyoverRoads} castShadow receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.ASPHALT_FLYOVER}
            roughness={0.70}
            metalness={0.18}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* 3D Parapet Barriers for elevated flyovers */}
      {layerVisibility.flyover && geometries.barriers?.attributes?.position && (
        <mesh geometry={geometries.barriers} castShadow receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.FLYOVER_BARRIER}
            roughness={0.65}
            metalness={0.25}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {layerVisibility.underpass && geometries.underpassRoads.attributes?.position && (
        <mesh geometry={geometries.underpassRoads} receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.ASPHALT_UNDERPASS}
            roughness={0.88}
            metalness={0.08}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {layerVisibility.junctions && geometries.junctions.attributes?.position && (
        <mesh geometry={geometries.junctions} receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.ASPHALT_JUNCTION}
            roughness={0.85}
            metalness={0.10}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* Solid outer shoulder / curb boundary markings */}
      {layerVisibility.dividers && geometries.roadBorders?.attributes?.position && (
        <mesh geometry={geometries.roadBorders}>
          <meshBasicMaterial color={ROAD_STYLE.SHOULDER_LINE} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Dashed Lane Dividers */}
      {layerVisibility.dividers && geometries.laneDividers.attributes?.position && (
        <mesh geometry={geometries.laneDividers}>
          <meshBasicMaterial color={ROAD_STYLE.LANE_MARKING_WHITE} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Concrete Support Pillars */}
      {layerVisibility.pillars && geometries.pillars.attributes?.position && (
        <mesh geometry={geometries.pillars} castShadow receiveShadow>
          <meshStandardMaterial
            color={ROAD_STYLE.PILLAR_CONCRETE}
            roughness={0.60}
            metalness={0.25}
          />
        </mesh>
      )}

      {/* 2. Procedural 3D Urban Buildings */}
      {layerVisibility.buildings && (
        <group name="urban_buildings">
          {/* Commercial Glass Towers */}
          {urbanGeoms.commercialTowers.attributes?.position && (
            <mesh geometry={urbanGeoms.commercialTowers} castShadow receiveShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.TOWER_GLASS}
                roughness={0.25}
                metalness={0.75}
              />
            </mesh>
          )}

          {/* Corporate Office Mid-Rise Blocks */}
          {urbanGeoms.officeBlocks.attributes?.position && (
            <mesh geometry={urbanGeoms.officeBlocks} castShadow receiveShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.OFFICE_SLATE}
                roughness={0.65}
                metalness={0.35}
              />
            </mesh>
          )}

          {/* Residential Urban Blocks */}
          {urbanGeoms.residentialBlocks.attributes?.position && (
            <mesh geometry={urbanGeoms.residentialBlocks} castShadow receiveShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.RESIDENTIAL_ZINC}
                roughness={0.80}
                metalness={0.20}
              />
            </mesh>
          )}

          {/* Rooftop Penthouse & Mechanical Infrastructure */}
          {urbanGeoms.rooftopStructures.attributes?.position && (
            <mesh geometry={urbanGeoms.rooftopStructures} castShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.ROOFTOP_HVAC}
                roughness={0.50}
                metalness={0.50}
              />
            </mesh>
          )}
        </group>
      )}

      {/* 3. Bengaluru Garden City Landscaping Trees */}
      {layerVisibility.landscaping && (
        <group name="urban_landscaping">
          {landscapingGeoms.foliage.attributes?.position && (
            <mesh geometry={landscapingGeoms.foliage} castShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.TREE_FOLIAGE_2}
                roughness={0.85}
                metalness={0.10}
              />
            </mesh>
          )}
          {landscapingGeoms.trunks.attributes?.position && (
            <mesh geometry={landscapingGeoms.trunks} castShadow>
              <meshStandardMaterial
                color={URBAN_STYLE.TREE_TRUNK}
                roughness={0.90}
                metalness={0.10}
              />
            </mesh>
          )}
        </group>
      )}

      {/* 4. Overhead Direction Highway Signboards */}
      {layerVisibility.signs && (
        <group name="highway_signboards">
          {HIGHWAY_SIGNS.map((s) => (
            <HighwaySignboard key={s.id} sign={s} />
          ))}
        </group>
      )}

      {/* 5. 3D Live Traffic Signals at J1, J2, and J3 */}
      {layerVisibility.signals && (
        <TrafficSignals3D signals={signals} junctions={junctions} />
      )}

      {/* 6. Microscopic Live SUMO Vehicles */}
      <VehicleLayer
        vehicles={vehicles}
        selectedVehicleId={selectedVehicleId}
        onSelectVehicle={onSelectVehicle}
        onAmbulanceDetected={onAmbulanceDetected}
      />

      {/* 7. 3D Junction Markers */}
      {layerVisibility.markers && (
        <>
          <JunctionMarker
            code="J1"
            name="Madiwala Checkpost"
            elevation="0.0m / -4.5m"
            position={[-79.8, 8.0, -125.5]}
            onSelect={() => onSelectPreset && onSelectPreset('J1')}
          />
          <JunctionMarker
            code="J2"
            name="Silk Board Rotary"
            elevation="+8.0m Flyover"
            position={[1.13, 16.0, 16.12]}
            onSelect={() => onSelectPreset && onSelectPreset('J2')}
          />
          <JunctionMarker
            code="J3"
            name="Rupena Agrahara"
            elevation="0.0m Ground"
            position={[79.63, 8.0, 132.3]}
            onSelect={() => onSelectPreset && onSelectPreset('J3')}
          />
        </>
      )}
    </>
  );
}
