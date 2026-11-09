/**
 * frontend/src/utils/roadGeometryBuilder.js
 *
 * Phase 3B Stage 3: 3D Road Geometry Mesh Construction Engine.
 * Converts extracted SUMO network geometry (edges, lanes, junctions, flyovers)
 * into Three.js BufferGeometry meshes for asphalt surfaces, lane markings,
 * junction conflict polygons, and elevated civil infrastructure.
 */

import * as THREE from 'three';
import { sumoToThreeCoords, DEFAULT_SCENE_ANCHOR } from './coordinateTransform.js';

// Visual Material Constants
export const ROAD_STYLE = Object.freeze({
  ASPHALT_GROUND: '#2a313d',      // Crisp dark slate asphalt
  ASPHALT_FLYOVER: '#384252',     // Concrete-deck flyover asphalt
  ASPHALT_UNDERPASS: '#1c212b',   // Depressed underpass asphalt
  ASPHALT_JUNCTION: '#242a35',    // High-wear intersection asphalt
  LANE_MARKING_WHITE: '#ffffff',  // Reflectorized thermoplastic white
  LANE_MARKING_YELLOW: '#f59e0b', // Median amber marking
  SHOULDER_LINE: '#cbd5e1',       // Road boundary edge line / curb
  PILLAR_CONCRETE: '#94a3b8',     // Reinforced concrete piers
  FLYOVER_BARRIER: '#64748b',     // 3D flyover guardrail parapet
  GROUND_TERRAIN: '#11151c',      // Ambient urban terrain
  Z_FIGHT_BIAS: 0.03,             // Elevation bias (meters) for markings above asphalt
});

/**
 * Computes smooth normal vectors along a 3D polyline on the horizontal XZ plane.
 * @param {Array<THREE.Vector3>} points
 * @returns {Array<THREE.Vector3>}
 */
function computePolylineNormals(points) {
  const n = points.length;
  const normals = new Array(n);

  for (let i = 0; i < n; i++) {
    let tangent;
    if (i === 0) {
      tangent = new THREE.Vector3().subVectors(points[1], points[0]);
    } else if (i === n - 1) {
      tangent = new THREE.Vector3().subVectors(points[n - 1], points[n - 2]);
    } else {
      const t1 = new THREE.Vector3().subVectors(points[i], points[i - 1]).normalize();
      const t2 = new THREE.Vector3().subVectors(points[i + 1], points[i]).normalize();
      tangent = new THREE.Vector3().addVectors(t1, t2);
    }
    tangent.y = 0;
    tangent.normalize();

    // Normal in horizontal plane perpendicular to tangent: (-Tz, 0, Tx)
    normals[i] = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
  }

  return normals;
}

/**
 * Generates an extruded 3D ribbon BufferGeometry along a polyline.
 * @param {Array<THREE.Vector3>} points - Centerline vertices
 * @param {number} width - Ribbon width in meters
 * @param {number} [yOffset=0.0] - Vertical offset to prevent z-fighting
 * @returns {THREE.BufferGeometry}
 */
export function createRibbonGeometry(points, width, yOffset = 0.0) {
  if (!points || points.length < 2) {
    return new THREE.BufferGeometry();
  }

  const normals = computePolylineNormals(points);
  const halfWidth = width / 2.0;
  const n = points.length;

  const positions = new Float32Array(n * 2 * 3);
  const uvs = new Float32Array(n * 2 * 2);
  const indices = [];

  let accumulatedDist = 0.0;

  for (let i = 0; i < n; i++) {
    const p = points[i];
    const norm = normals[i];

    if (i > 0) {
      accumulatedDist += points[i].distanceTo(points[i - 1]);
    }

    // Left vertex
    const lx = p.x - norm.x * halfWidth;
    const ly = p.y + yOffset;
    const lz = p.z - norm.z * halfWidth;

    // Right vertex
    const rx = p.x + norm.x * halfWidth;
    const ry = p.y + yOffset;
    const rz = p.z + norm.z * halfWidth;

    const leftIdx = i * 2;
    const rightIdx = i * 2 + 1;

    positions[leftIdx * 3] = lx;
    positions[leftIdx * 3 + 1] = ly;
    positions[leftIdx * 3 + 2] = lz;

    positions[rightIdx * 3] = rx;
    positions[rightIdx * 3 + 1] = ry;
    positions[rightIdx * 3 + 2] = rz;

    // UV coordinates (U across width: 0 to 1, V along length)
    uvs[leftIdx * 2] = 0.0;
    uvs[leftIdx * 2 + 1] = accumulatedDist / 10.0;

    uvs[rightIdx * 2] = 1.0;
    uvs[rightIdx * 2 + 1] = accumulatedDist / 10.0;

    if (i < n - 1) {
      const nextLeft = (i + 1) * 2;
      const nextRight = (i + 1) * 2 + 1;
      // Two triangles per segment
      indices.push(leftIdx, nextLeft, rightIdx);
      indices.push(rightIdx, nextLeft, nextRight);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geom.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geom.setIndex(indices);
  geom.computeVertexNormals();

  return geom;
}

/**
 * Calculates elevation along a ramp edge, smoothly interpolating between
 * ground level and elevated deck height using cubic smoothstep curve.
 *
 * @param {number} t - Normalized progress along edge [0, 1]
 * @param {number} targetElev - Target deck elevation (e.g. +8.0m or -4.5m)
 * @param {boolean} isAscending - True if entering ramp (0 -> target), False if exiting
 * @returns {number} Interpolated elevation in meters
 */
export function interpolateRampElevation(t, targetElev, isAscending = true) {
  const clampedT = Math.max(0.0, Math.min(1.0, t));
  // Cubic smoothstep: 3t^2 - 2t^3 (zero derivative at endpoints)
  const factor = clampedT * clampedT * (3.0 - 2.0 * clampedT);
  return isAscending ? targetElev * factor : targetElev * (1.0 - factor);
}

/**
 * Converts a SUMO lane shape into an array of Three.js Vector3 points,
 * applying illustrative grade-separation elevation profiles.
 *
 * @param {object} edgeData - Edge object from corridorNetworkGeometry.json
 * @param {object} laneData - Specific lane object
 * @param {object} [anchor=DEFAULT_SCENE_ANCHOR]
 * @returns {Array<THREE.Vector3>}
 */
export function getLaneThreePoints(edgeData, laneData, anchor = DEFAULT_SCENE_ANCHOR) {
  const shape = laneData.shape;
  const n = shape.length;
  const pts = [];

  const isRamp = edgeData.isRamp === true;
  const assumedElev = edgeData.assumedElevation || 0.0;

  // Total polyline horizontal length for ramp interpolation
  let totalLen = 0.0;
  if (isRamp) {
    for (let i = 0; i < n - 1; i++) {
      totalLen += Math.hypot(shape[i + 1][0] - shape[i][0], shape[i + 1][1] - shape[i][1]);
    }
  }

  let cumDist = 0.0;
  for (let i = 0; i < n; i++) {
    const [sx, sy, sz] = shape[i];

    let elev = assumedElev;
    if (isRamp && totalLen > 0) {
      if (i > 0) {
        cumDist += Math.hypot(shape[i][0] - shape[i - 1][0], shape[i][1] - shape[i - 1][1]);
      }
      const progress = cumDist / totalLen;
      // Off-ramp descends from deck to ground; on-ramp ascends from ground to deck
      const isAscending = !edgeData.id.includes('AddedOffRampEdge');
      elev = interpolateRampElevation(progress, assumedElev, isAscending);
    }

    const t = sumoToThreeCoords(sx, sy, sz, elev, anchor);
    pts.push(new THREE.Vector3(t.x, t.y, t.z));
  }

  return pts;
}

/**
 * Builds dashed lane divider markings between adjacent lanes.
 *
 * @param {Array<THREE.Vector3>} leftLanePts
 * @param {Array<THREE.Vector3>} rightLanePts
 * @param {number} [dashLen=3.0] - Length of painted dash (meters)
 * @param {number} [gapLen=3.0] - Length of gap (meters)
 * @param {number} [lineWidth=0.15] - Dash width in meters
 * @returns {THREE.BufferGeometry}
 */
export function createDashedDividerGeometry(leftLanePts, rightLanePts, dashLen = 3.0, gapLen = 3.0, lineWidth = 0.15) {
  const n = Math.min(leftLanePts.length, rightLanePts.length);
  if (n < 2) return new THREE.BufferGeometry();

  // Compute boundary centerline between the two lanes
  const centerline = [];
  for (let i = 0; i < n; i++) {
    centerline.push(new THREE.Vector3().addVectors(leftLanePts[i], rightLanePts[i]).multiplyScalar(0.5));
  }

  // Create discrete dash segments along the centerline
  const dashGeometries = [];
  let currentDist = 0.0;
  let inDash = true;
  let segStartDist = 0.0;

  // Sample points at 1-meter intervals along centerline
  const totalLength = centerline.reduce((acc, p, idx) => {
    return idx === 0 ? 0 : acc + p.distanceTo(centerline[idx - 1]);
  }, 0);

  if (totalLength < dashLen) return new THREE.BufferGeometry();

  const numSamples = Math.max(10, Math.ceil(totalLength));
  const curve = new THREE.CatmullRomCurve3(centerline);

  const dashSegments = [];
  let currentSegment = [];

  for (let i = 0; i <= numSamples; i++) {
    const t = i / numSamples;
    const pt = curve.getPoint(t);
    const dist = t * totalLength;
    const cyclePos = dist % (dashLen + gapLen);

    if (cyclePos <= dashLen) {
      currentSegment.push(pt);
    } else {
      if (currentSegment.length >= 2) {
        dashSegments.push(currentSegment);
      }
      currentSegment = [];
    }
  }
  if (currentSegment.length >= 2) {
    dashSegments.push(currentSegment);
  }

  // Combine dash ribbons into a single merged BufferGeometry
  const geometries = dashSegments.map(pts => createRibbonGeometry(pts, lineWidth, ROAD_STYLE.Z_FIGHT_BIAS));
  return mergeBufferGeometries(geometries);
}

/**
 * Creates 3D concrete supporting pillars beneath elevated flyover spans.
 *
 * @param {Array<THREE.Vector3>} centerlinePts
 * @param {number} [spacing=30.0] - Distance between pillars in meters
 * @param {number} [radius=0.6] - Pillar radius in meters
 * @returns {THREE.BufferGeometry} Merged pillar cylinders
 */
export function createPillarsGeometry(centerlinePts, spacing = 30.0, radius = 0.6) {
  if (!centerlinePts || centerlinePts.length < 2) {
    return new THREE.BufferGeometry();
  }

  const curve = new THREE.CatmullRomCurve3(centerlinePts);
  const totalLength = centerlinePts.reduce((acc, p, idx) => {
    return idx === 0 ? 0 : acc + p.distanceTo(centerlinePts[idx - 1]);
  }, 0);

  if (totalLength < spacing) {
    return new THREE.BufferGeometry();
  }

  const numPillars = Math.floor(totalLength / spacing);
  const pillarGeometries = [];

  for (let i = 1; i <= numPillars; i++) {
    const t = (i * spacing) / totalLength;
    const pt = curve.getPoint(t);

    // Only instantiate pillars if elevated above ground level (> 2.5m)
    if (pt.y > 2.5) {
      const height = pt.y;
      const cyl = new THREE.CylinderGeometry(radius, radius, height, 16);
      cyl.translate(pt.x, height / 2.0, pt.z);
      pillarGeometries.push(cyl);

      // Top pier cap / crosshead supporting the flyover deck
      const cap = new THREE.BoxGeometry(radius * 3.8, 0.6, radius * 2.4);
      cap.translate(pt.x, height - 0.3, pt.z);
      pillarGeometries.push(cap);
    }
  }

  return mergeBufferGeometries(pillarGeometries);
}

/**
 * Generates solid shoulder line ribbons along the outer left and right boundaries of an edge.
 * @param {Array<Array<THREE.Vector3>>} lanePoints - Points for all lanes of the edge
 * @param {Array<object>} lanes - Lane definitions with widths
 * @param {number} [lineWidth=0.35] - Shoulder line width in meters
 * @returns {Array<THREE.BufferGeometry>}
 */
export function createRoadBorderGeometries(lanePoints, lanes, lineWidth = 0.35) {
  if (!lanePoints || lanePoints.length === 0) return [];
  const borders = [];

  // Outermost left boundary of first lane
  const firstLanePts = lanePoints[0];
  const firstLaneWidth = lanes[0]?.width || 3.20;
  if (firstLanePts && firstLanePts.length >= 2) {
    const normals = computePolylineNormals(firstLanePts);
    const halfW = firstLaneWidth / 2.0;
    const outerLeftPts = firstLanePts.map((p, idx) => {
      const norm = normals[idx];
      return new THREE.Vector3(
        p.x - norm.x * halfW,
        p.y,
        p.z - norm.z * halfW
      );
    });
    borders.push(createRibbonGeometry(outerLeftPts, lineWidth, ROAD_STYLE.Z_FIGHT_BIAS));
  }

  // Outermost right boundary of last lane
  const lastLaneIdx = lanePoints.length - 1;
  const lastLanePts = lanePoints[lastLaneIdx];
  const lastLaneWidth = lanes[lastLaneIdx]?.width || 3.20;
  if (lastLanePts && lastLanePts.length >= 2) {
    const normals = computePolylineNormals(lastLanePts);
    const halfW = lastLaneWidth / 2.0;
    const outerRightPts = lastLanePts.map((p, idx) => {
      const norm = normals[idx];
      return new THREE.Vector3(
        p.x + norm.x * halfW,
        p.y,
        p.z + norm.z * halfW
      );
    });
    borders.push(createRibbonGeometry(outerRightPts, lineWidth, ROAD_STYLE.Z_FIGHT_BIAS));
  }

  return borders;
}

/**
 * Extrudes continuous 3D parapet barriers along a 3D polyline (e.g. flyover guardrails).
 * @param {Array<THREE.Vector3>} points
 * @param {number} [height=1.1]
 * @param {number} [width=0.35]
 * @returns {THREE.BufferGeometry}
 */
export function createBarrierGeometry(points, height = 1.1, width = 0.35) {
  if (!points || points.length < 2) return new THREE.BufferGeometry();
  const normals = computePolylineNormals(points);
  const halfW = width / 2.0;
  const n = points.length;
  const positions = new Float32Array(n * 4 * 3);
  const indices = [];

  for (let i = 0; i < n; i++) {
    const p = points[i];
    const norm = normals[i];
    const bl_x = p.x - norm.x * halfW;
    const bl_y = p.y;
    const bl_z = p.z - norm.z * halfW;

    const br_x = p.x + norm.x * halfW;
    const br_y = p.y;
    const br_z = p.z + norm.z * halfW;

    const tl_x = bl_x;
    const tl_y = bl_y + height;
    const tl_z = bl_z;

    const tr_x = br_x;
    const tr_y = br_y + height;
    const tr_z = br_z;

    const base = i * 4;
    positions[(base + 0) * 3 + 0] = bl_x;
    positions[(base + 0) * 3 + 1] = bl_y;
    positions[(base + 0) * 3 + 2] = bl_z;

    positions[(base + 1) * 3 + 0] = br_x;
    positions[(base + 1) * 3 + 1] = br_y;
    positions[(base + 1) * 3 + 2] = br_z;

    positions[(base + 2) * 3 + 0] = tl_x;
    positions[(base + 2) * 3 + 1] = tl_y;
    positions[(base + 2) * 3 + 2] = tl_z;

    positions[(base + 3) * 3 + 0] = tr_x;
    positions[(base + 3) * 3 + 1] = tr_y;
    positions[(base + 3) * 3 + 2] = tr_z;

    if (i < n - 1) {
      const next = (i + 1) * 4;
      // Top face
      indices.push(base + 2, next + 2, base + 3);
      indices.push(base + 3, next + 2, next + 3);
      // Left outer face
      indices.push(base + 0, base + 2, next + 0);
      indices.push(next + 0, base + 2, next + 2);
      // Right inner face
      indices.push(base + 1, next + 1, base + 3);
      indices.push(base + 3, next + 1, next + 3);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geom.setIndex(indices);
  geom.computeVertexNormals();
  return geom;
}

/**
 * Triangulates a 2D junction boundary polygon in the Three.js XZ plane
 * into a flat horizontal 3D asphalt mesh.
 *
 * @param {Array<Array<number>>} sumoPolygon - Array of [x, y] coordinates
 * @param {number} [elevation=0.0] - Elevation in meters
 * @param {object} [anchor=DEFAULT_SCENE_ANCHOR]
 * @returns {THREE.BufferGeometry}
 */
export function createJunctionGeometry(sumoPolygon, elevation = 0.0, anchor = DEFAULT_SCENE_ANCHOR) {
  if (!sumoPolygon || sumoPolygon.length < 3) {
    return new THREE.BufferGeometry();
  }

  // Convert to Three.js coordinates (X, Z)
  const threePts = sumoPolygon.map(pt => {
    const t = sumoToThreeCoords(pt[0], pt[1], 0.0, elevation, anchor);
    return new THREE.Vector2(t.x, t.z);
  });

  // Triangulate using THREE.ShapeUtils
  const shape = new THREE.Shape(threePts);
  const geom2d = new THREE.ShapeGeometry(shape);

  // ShapeGeometry creates vertices in XY plane with normal (0, 0, 1).
  // Rotate by -PI/2 around X axis so normal points UP to (0, 1, 0) in Three.js world space.
  geom2d.rotateX(-Math.PI / 2);
  // Shift to elevation with slight positive bias to avoid z-fighting with terrain
  geom2d.translate(0, elevation + 0.015, 0);
  geom2d.computeVertexNormals();

  return geom2d;
}

/**
 * Merges multiple BufferGeometries into one to minimize GPU draw calls.
 * @param {Array<THREE.BufferGeometry>} geometries
 * @returns {THREE.BufferGeometry}
 */
export function mergeBufferGeometries(geometries) {
  const validGeoms = geometries.filter(g => g && g.attributes?.position?.count > 0);
  if (validGeoms.length === 0) return new THREE.BufferGeometry();
  if (validGeoms.length === 1) return validGeoms[0];

  let totalPos = 0;
  let totalNorm = 0;
  let totalUv = 0;
  let totalIndices = 0;

  for (const g of validGeoms) {
    totalPos += g.attributes.position.array.length;
    if (g.attributes.normal) totalNorm += g.attributes.normal.array.length;
    if (g.attributes.uv) totalUv += g.attributes.uv.array.length;
    if (g.index) totalIndices += g.index.array.length;
  }

  const mergedPos = new Float32Array(totalPos);
  const mergedNorm = totalNorm > 0 ? new Float32Array(totalNorm) : null;
  const mergedUv = totalUv > 0 ? new Float32Array(totalUv) : null;
  const mergedIndices = totalIndices > 0 ? [] : null;

  let posOffset = 0;
  let normOffset = 0;
  let uvOffset = 0;
  let indexVertexOffset = 0;

  for (const g of validGeoms) {
    mergedPos.set(g.attributes.position.array, posOffset);
    posOffset += g.attributes.position.array.length;

    if (mergedNorm && g.attributes.normal) {
      mergedNorm.set(g.attributes.normal.array, normOffset);
      normOffset += g.attributes.normal.array.length;
    }

    if (mergedUv && g.attributes.uv) {
      mergedUv.set(g.attributes.uv.array, uvOffset);
      uvOffset += g.attributes.uv.array.length;
    }

    if (mergedIndices && g.index) {
      const idxArr = g.index.array;
      for (let i = 0; i < idxArr.length; i++) {
        mergedIndices.push(idxArr[i] + indexVertexOffset);
      }
      indexVertexOffset += g.attributes.position.count;
    }
  }

  const merged = new THREE.BufferGeometry();
  merged.setAttribute('position', new THREE.BufferAttribute(mergedPos, 3));
  if (mergedNorm) merged.setAttribute('normal', new THREE.BufferAttribute(mergedNorm, 3));
  if (mergedUv) merged.setAttribute('uv', new THREE.BufferAttribute(mergedUv, 2));
  if (mergedIndices) merged.setIndex(mergedIndices);

  return merged;
}

/**
 * Builds all categorized corridor 3D geometries (ground roads, flyovers,
 * underpasses, junctions, lane dividers, road borders, barriers, pillars) into
 * merged draw-call optimized BufferGeometries for rendering in React Three Fiber.
 *
 * @param {object} networkData - Raw or loaded corridorNetworkGeometry JSON
 * @param {object} [anchor=DEFAULT_SCENE_ANCHOR] - Georeferencing anchor
 * @returns {object} Map of merged BufferGeometries
 */
export function buildCorridorSceneGeometries(networkData, anchor = DEFAULT_SCENE_ANCHOR) {
  if (!networkData || !networkData.edges) {
    return {
      groundRoads: new THREE.BufferGeometry(),
      flyoverRoads: new THREE.BufferGeometry(),
      underpassRoads: new THREE.BufferGeometry(),
      junctions: new THREE.BufferGeometry(),
      laneDividers: new THREE.BufferGeometry(),
      roadBorders: new THREE.BufferGeometry(),
      barriers: new THREE.BufferGeometry(),
      pillars: new THREE.BufferGeometry(),
    };
  }

  const edges = Array.isArray(networkData.edges) ? networkData.edges : Object.values(networkData.edges);
  const junctions = Array.isArray(networkData.junctions) ? networkData.junctions : Object.values(networkData.junctions || {});

  const groundRibbons = [];
  const flyoverRibbons = [];
  const underpassRibbons = [];
  const dividerGeoms = [];
  const borderGeoms = [];
  const barrierGeoms = [];
  const pillarGeoms = [];

  for (const edge of edges) {
    const lanePoints = [];
    for (const lane of edge.lanes) {
      const pts = getLaneThreePoints(edge, lane, anchor);
      lanePoints.push(pts);
      const ribbon = createRibbonGeometry(pts, lane.width || 3.20);
      if (edge.isFlyover) {
        flyoverRibbons.push(ribbon);
      } else if (edge.isUnderpass) {
        underpassRibbons.push(ribbon);
      } else {
        groundRibbons.push(ribbon);
      }
    }

    // Lane divider dashed lines between adjacent lanes (0.30m width for crisp resolution)
    for (let i = 0; i < lanePoints.length - 1; i++) {
      const div = createDashedDividerGeometry(lanePoints[i], lanePoints[i + 1], 3.0, 3.0, 0.30);
      if (div.attributes?.position?.count > 0) {
        dividerGeoms.push(div);
      }
    }

    // Solid outer shoulder / curb boundary markings along road edges
    const borders = createRoadBorderGeometries(lanePoints, edge.lanes, 0.35);
    for (const b of borders) {
      if (b.attributes?.position?.count > 0) {
        borderGeoms.push(b);
      }
    }

    // 3D Parapet barriers and pillars for elevated flyovers (> 2.5m elevation)
    if (edge.isFlyover && (edge.assumedElevation || 0) > 2.5 && lanePoints.length > 0) {
      const firstLanePts = lanePoints[0];
      const lastLanePts = lanePoints[lanePoints.length - 1];
      const firstWidth = edge.lanes[0]?.width || 3.20;
      const lastWidth = edge.lanes[lanePoints.length - 1]?.width || 3.20;

      if (firstLanePts.length >= 2) {
        const normFirst = computePolylineNormals(firstLanePts);
        const leftOuter = firstLanePts.map((p, idx) => {
          const norm = normFirst[idx];
          return new THREE.Vector3(p.x - norm.x * (firstWidth / 2.0), p.y, p.z - norm.z * (firstWidth / 2.0));
        });
        const b1 = createBarrierGeometry(leftOuter, 1.1, 0.35);
        if (b1.attributes?.position?.count > 0) barrierGeoms.push(b1);
      }

      if (lastLanePts.length >= 2) {
        const normLast = computePolylineNormals(lastLanePts);
        const rightOuter = lastLanePts.map((p, idx) => {
          const norm = normLast[idx];
          return new THREE.Vector3(p.x + norm.x * (lastWidth / 2.0), p.y, p.z + norm.z * (lastWidth / 2.0));
        });
        const b2 = createBarrierGeometry(rightOuter, 1.1, 0.35);
        if (b2.attributes?.position?.count > 0) barrierGeoms.push(b2);
      }

      // Concrete pillars beneath elevated flyover deck
      const centerLaneIdx = Math.floor(lanePoints.length / 2);
      const pil = createPillarsGeometry(lanePoints[centerLaneIdx], 25.0, 0.85);
      if (pil.attributes?.position?.count > 0) {
        pillarGeoms.push(pil);
      }
    }
  }

  // Triangulate junction conflict polygons
  const junctionGeoms = [];
  for (const junc of junctions) {
    if (junc.shape && junc.shape.length >= 3) {
      const jg = createJunctionGeometry(junc.shape, 0.0, anchor);
      if (jg.attributes?.position?.count > 0) {
        junctionGeoms.push(jg);
      }
    }
  }

  return {
    groundRoads: mergeBufferGeometries(groundRibbons),
    flyoverRoads: mergeBufferGeometries(flyoverRibbons),
    underpassRoads: mergeBufferGeometries(underpassRibbons),
    junctions: mergeBufferGeometries(junctionGeoms),
    laneDividers: mergeBufferGeometries(dividerGeoms),
    roadBorders: mergeBufferGeometries(borderGeoms),
    barriers: mergeBufferGeometries(barrierGeoms),
    pillars: mergeBufferGeometries(pillarGeoms),
  };
}
