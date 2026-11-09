/**
 * frontend/src/utils/urbanEnvironmentBuilder.js
 *
 * Procedural 3D Urban Environment & Architectural Digital Twin Generator.
 * Constructs realistic 3D buildings, commercial tech towers, residential blocks,
 * rooftop infrastructure, roadside greenery (Bengaluru "Garden City" tree canopies),
 * and authentic IRC highway overhead signage around the Central Silk Board interchange.
 *
 * Architectural & Urban Design Standards:
 *   - Follows IS:SP:7-2005 National Building Code of India (Urban Form Guidelines).
 *   - Strictly enforces set-back buffers (minimum 20m from road centerlines) to prevent road encroachment.
 *   - Separates ground-truth SUMO roadway geometry from procedural urban context.
 */

import * as THREE from 'three';
import { sumoToThreeCoords, DEFAULT_SCENE_ANCHOR } from './coordinateTransform.js';
import { mergeBufferGeometries } from './roadGeometryBuilder.js';

// Material and Theme Constants
export const URBAN_STYLE = Object.freeze({
  TOWER_GLASS: '#1e293b',         // Modern commercial reflective glass
  TOWER_ACCENT: '#0f172a',        // Dark structural mullions
  OFFICE_SLATE: '#334155',        // Corporate tech park mid-rise
  RESIDENTIAL_ZINC: '#27272a',    // Urban apartment complex
  ROOFTOP_HVAC: '#475569',        // Rooftop mechanical chiller/penthouse
  WINDOW_EMISSIVE_DAY: '#38bdf8', // Soft cyan ambient window reflection
  BEACON_RED: '#ef4444',          // Aviation safety tower beacon
  TREE_FOLIAGE_1: '#166534',      // Deep tropical green canopy
  TREE_FOLIAGE_2: '#15803d',      // Lush emerald canopy
  TREE_TRUNK: '#78350f',          // Hardwood trunk
  SIGN_FRAME_STEEL: '#64748b',    // Galvanized steel sign gantry truss
  SIGN_PANEL_GREEN: '#15803d',    // IRC standard green highway signboard
  SIGN_TEXT_WHITE: '#ffffff',     // Thermoplastic reflective white lettering
});

/**
 * Deterministic pseudo-random number generator (Mulberry32).
 */
function createPrng(seed) {
  let s = Math.abs(seed | 0) + 1;
  return function () {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Samples road centerline points from network geometry for collision and setback tests.
 */
function extractRoadSamplePoints(networkData, anchor = DEFAULT_SCENE_ANCHOR) {
  if (!networkData || !networkData.edges) return [];
  const edges = Array.isArray(networkData.edges) ? networkData.edges : Object.values(networkData.edges);
  const roadPts = [];

  for (const edge of edges) {
    for (const lane of edge.lanes || []) {
      for (const [sx, sy] of lane.shape || []) {
        const c = sumoToThreeCoords(sx, sy, 0, 0, anchor);
        roadPts.push(new THREE.Vector2(c.x, c.z));
      }
    }
  }
  return roadPts;
}

/**
 * Computes minimum 2D distance from a test coordinate to any road sample point.
 */
function getDistanceToRoads(x, z, roadPoints) {
  let minDistSq = Infinity;
  for (let i = 0; i < roadPoints.length; i++) {
    const dx = x - roadPoints[i].x;
    const dz = z - roadPoints[i].y;
    const distSq = dx * dx + dz * dz;
    if (distSq < minDistSq) {
      minDistSq = distSq;
      if (minDistSq < 400) break; // Early exit if closer than 20m (20^2 = 400)
    }
  }
  return Math.sqrt(minDistSq);
}

/**
 * Creates an extruded box BufferGeometry centered at (x, height / 2, z).
 */
function createBoxGeometry(w, h, d, x, yBottom, z) {
  const geom = new THREE.BoxGeometry(w, h, d);
  geom.translate(x, yBottom + h / 2.0, z);
  return geom;
}

/**
 * Procedurally generates 3D urban buildings, tech towers, residential complexes,
 * and rooftop infrastructure surrounding the Silk Board junction.
 *
 * @param {object} networkData - Extracted SUMO network JSON
 * @param {object} [anchor=DEFAULT_SCENE_ANCHOR] - Georeferencing anchor
 * @returns {object} Categorized merged BufferGeometries
 */
export function buildUrbanBuildingsGeometries(networkData, anchor = DEFAULT_SCENE_ANCHOR) {
  const roadPoints = extractRoadSamplePoints(networkData, anchor);
  const prng = createPrng(42077);

  const towerGeoms = [];
  const officeGeoms = [];
  const residentialGeoms = [];
  const rooftopGeoms = [];

  // Grid scan across the urban corridor basin
  const minX = -320;
  const maxX = 320;
  const minZ = -280;
  const maxZ = 280;
  const step = 32.0; // 32m parcel grid spacing

  for (let x = minX; x <= maxX; x += step) {
    for (let z = minZ; z <= maxZ; z += step) {
      // Add slight organic parcel jitter
      const jx = x + (prng() - 0.5) * 10.0;
      const jz = z + (prng() - 0.5) * 10.0;

      // Minimum setback buffer from road ribbons (22m)
      const distToRoad = getDistanceToRoads(jx, jz, roadPoints);
      if (distToRoad < 22.0) {
        continue; // Encroaches on road reserve: skip parcel
      }

      // Determine parcel zoning based on location relative to Central Silk Board
      // Northwest / Northeast: Major commercial IT hubs & St. John's complex
      // Southwest / Southeast: High-density residential & mixed retail
      const distFromCenter = Math.hypot(jx, jz);
      const isCornerHub = distFromCenter > 75.0 && distFromCenter < 280.0;

      const roll = prng();
      let width = 16.0 + prng() * 18.0;
      let depth = 16.0 + prng() * 18.0;
      let height = 0.0;

      if (isCornerHub && roll > 0.55) {
        // High-rise Commercial Tech Tower (12 to 18 stories: 36m to 54m)
        height = 36.0 + prng() * 20.0;
        const tower = createBoxGeometry(width, height, depth, jx, 0.0, jz);
        towerGeoms.push(tower);

        // Rooftop penthouse & mechanical chiller core
        const roofW = width * 0.45;
        const roofD = depth * 0.45;
        const roofH = 3.5;
        const roof = createBoxGeometry(roofW, roofH, roofD, jx, height, jz);
        rooftopGeoms.push(roof);

        // Communications antenna on tallest towers
        if (height > 45.0) {
          const antenna = new THREE.CylinderGeometry(0.3, 0.6, 7.0, 6);
          antenna.translate(jx, height + roofH + 3.5, jz);
          rooftopGeoms.push(antenna);
        }
      } else if (roll > 0.25) {
        // Corporate Office Block / Mid-rise (6 to 10 stories: 18m to 32m)
        height = 18.0 + prng() * 14.0;
        const office = createBoxGeometry(width, height, depth, jx, 0.0, jz);
        officeGeoms.push(office);

        // Rooftop HVAC units
        const hvac = createBoxGeometry(width * 0.35, 2.0, depth * 0.35, jx + (prng() - 0.5) * 4.0, height, jz);
        rooftopGeoms.push(hvac);
      } else {
        // Low-to-Mid Residential Block (4 to 6 stories: 12m to 18m)
        height = 12.0 + prng() * 7.0;
        const res = createBoxGeometry(width, height, depth, jx, 0.0, jz);
        residentialGeoms.push(res);
      }
    }
  }

  return {
    commercialTowers: mergeBufferGeometries(towerGeoms),
    officeBlocks: mergeBufferGeometries(officeGeoms),
    residentialBlocks: mergeBufferGeometries(residentialGeoms),
    rooftopStructures: mergeBufferGeometries(rooftopGeoms),
  };
}

/**
 * Procedurally generates volumetric tree canopies for Bengaluru "Garden City" landscaping.
 */
export function buildUrbanLandscapingGeometries(networkData, anchor = DEFAULT_SCENE_ANCHOR) {
  const roadPoints = extractRoadSamplePoints(networkData, anchor);
  const prng = createPrng(99112);

  const foliageGeoms = [];
  const trunkGeoms = [];

  // Generate tree clusters along roadside verges (buffer 10m to 18m from roads)
  const candidates = [];
  for (let x = -280; x <= 280; x += 18.0) {
    for (let z = -240; z <= 240; z += 18.0) {
      const jx = x + (prng() - 0.5) * 8.0;
      const jz = z + (prng() - 0.5) * 8.0;
      const d = getDistanceToRoads(jx, jz, roadPoints);

      // Place trees along road margins, park pockets, and junction roundabouts
      if (d >= 8.0 && d <= 18.0 && prng() > 0.40) {
        candidates.push({ x: jx, z: jz });
      }
    }
  }

  for (const pos of candidates) {
    const trunkH = 2.0 + prng() * 1.5;
    const trunkR = 0.35 + prng() * 0.15;
    const canopyR = 2.8 + prng() * 1.8;
    const canopyH = 3.5 + prng() * 2.0;

    // Wood trunk cylinder
    const trunk = new THREE.CylinderGeometry(trunkR * 0.8, trunkR, trunkH, 6);
    trunk.translate(pos.x, trunkH / 2.0, pos.z);
    trunkGeoms.push(trunk);

    // Multi-tier organic canopy (dodecahedron / cone)
    const canopy = new THREE.DodecahedronGeometry(canopyR, 1);
    canopy.scale(1.0, 1.25, 1.0);
    canopy.translate(pos.x, trunkH + canopyH * 0.5, pos.z);
    foliageGeoms.push(canopy);
  }

  return {
    foliage: mergeBufferGeometries(foliageGeoms),
    trunks: mergeBufferGeometries(trunkGeoms),
  };
}

/**
 * Overhead highway direction signage metadata at key corridor junctions.
 */
export const HIGHWAY_SIGNS = Object.freeze([
  {
    id: 'sign_j1_north',
    junction: 'J1 Madiwala Checkpost',
    position: [-85.0, 7.5, -110.0],
    rotationY: Math.PI * 0.65,
    mainText: 'NH 44 • HOSUR ROAD',
    subText: 'CENTRAL SILK BOARD 1.2 KM  ➔',
    category: 'ADVANCE_DIRECTION',
    width: 14.0,
    height: 3.2,
  },
  {
    id: 'sign_j2_rotary',
    junction: 'J2 Central Silk Board',
    position: [0.0, 14.5, 25.0],
    rotationY: Math.PI * 0.62,
    mainText: 'OUTER RING ROAD (ORR)',
    subText: '↰ BTM LAYOUT | HSR LAYOUT / BELLANDUR ↱',
    category: 'INTERCHANGE_GUIDE',
    width: 18.0,
    height: 3.8,
  },
  {
    id: 'sign_j3_south',
    junction: 'J3 Rupena Agrahara',
    position: [85.0, 7.5, 120.0],
    rotationY: Math.PI * 0.60,
    mainText: 'ELECTRONIC CITY FLYOVER (Toll 2.0 KM)',
    subText: 'HOSUR / TAMIL NADU BORDER 22 KM  ➔',
    category: 'ROUTE_CONFIRMATION',
    width: 16.0,
    height: 3.4,
  },
]);
