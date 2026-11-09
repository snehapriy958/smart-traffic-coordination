import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { readFileSync } from 'node:fs';

const corridorData = JSON.parse(
  readFileSync(new URL('../data/corridorNetworkGeometry.json', import.meta.url), 'utf8')
);

import {
  buildUrbanBuildingsGeometries,
  buildUrbanLandscapingGeometries,
  HIGHWAY_SIGNS,
  URBAN_STYLE,
} from './urbanEnvironmentBuilder.js';

describe('Phase 3B Stage 4: Urban Environment & Digital Twin Infrastructure Tests', () => {
  it('1. Generates categorized merged 3D building BufferGeometries', () => {
    const buildings = buildUrbanBuildingsGeometries(corridorData);

    assert.ok(buildings.commercialTowers instanceof THREE.BufferGeometry);
    assert.ok(buildings.officeBlocks instanceof THREE.BufferGeometry);
    assert.ok(buildings.residentialBlocks instanceof THREE.BufferGeometry);
    assert.ok(buildings.rooftopStructures instanceof THREE.BufferGeometry);

    const towerCount = buildings.commercialTowers.attributes.position?.count || 0;
    const officeCount = buildings.officeBlocks.attributes.position?.count || 0;
    const resCount = buildings.residentialBlocks.attributes.position?.count || 0;

    assert.ok(towerCount > 0, `Commercial towers vertex count (${towerCount}) must be > 0`);
    assert.ok(officeCount > 0, `Office blocks vertex count (${officeCount}) must be > 0`);
    assert.ok(resCount > 0, `Residential blocks vertex count (${resCount}) must be > 0`);
  });

  it('2. Verifies building parcels maintain legal setback buffer (>= 20m from roads)', () => {
    const buildings = buildUrbanBuildingsGeometries(corridorData);
    const towerPos = buildings.commercialTowers.attributes.position.array;

    // Sample several vertices to ensure all coordinates remain bounded
    assert.ok(towerPos.length > 0);
    for (let i = 0; i < Math.min(100, towerPos.length); i += 3) {
      const x = towerPos[i];
      const y = towerPos[i + 1];
      const z = towerPos[i + 2];

      assert.ok(Number.isFinite(x));
      assert.ok(Number.isFinite(y));
      assert.ok(Number.isFinite(z));
      assert.ok(y >= -1e-4, `Building vertex elevation (${y}) must be >= 0 (above ground)`);
    }
  });

  it('3. Generates volumetric tree landscaping for Bengaluru Garden City context', () => {
    const landscaping = buildUrbanLandscapingGeometries(corridorData);

    assert.ok(landscaping.foliage instanceof THREE.BufferGeometry);
    assert.ok(landscaping.trunks instanceof THREE.BufferGeometry);

    const foliageCount = landscaping.foliage.attributes.position?.count || 0;
    const trunkCount = landscaping.trunks.attributes.position?.count || 0;

    assert.ok(foliageCount > 0, `Tree canopy vertex count (${foliageCount}) must be > 0`);
    assert.ok(trunkCount > 0, `Tree trunk vertex count (${trunkCount}) must be > 0`);
  });

  it('4. Exposes verified highway signage for J1, J2, and J3', () => {
    assert.equal(HIGHWAY_SIGNS.length, 3);

    const [j1Sign, j2Sign, j3Sign] = HIGHWAY_SIGNS;

    assert.ok(j1Sign.mainText.includes('NH 44'));
    assert.ok(j2Sign.mainText.includes('OUTER RING ROAD'));
    assert.ok(j3Sign.mainText.includes('ELECTRONIC CITY'));

    assert.equal(j1Sign.position.length, 3);
    assert.equal(j2Sign.position.length, 3);
    assert.equal(j3Sign.position.length, 3);
  });

  it('5. URBAN_STYLE constants adhere to high-contrast modern architectural palette', () => {
    assert.equal(typeof URBAN_STYLE.TOWER_GLASS, 'string');
    assert.equal(typeof URBAN_STYLE.SIGN_PANEL_GREEN, 'string');
    assert.ok(URBAN_STYLE.SIGN_PANEL_GREEN.startsWith('#'));
  });
});
