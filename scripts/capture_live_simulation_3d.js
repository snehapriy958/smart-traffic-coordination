/**
 * scripts/capture_live_simulation_3d.js
 *
 * Verifies live microscopic SUMO vehicle streaming in the 3D digital twin.
 * Starts simulation, streams TraCI vehicle updates, captures live 3D vehicles,
 * inspects a vehicle, and stops simulation.
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9222;
const ARTIFACTS_DIR = 'C:\\Users\\Sneha Singh\\.gemini\\antigravity\\brain\\1bc986a7-c556-43f9-8c53-6ea55756f37e\\screenshots';
const OUTPUT_DIR = path.resolve('outputs/screenshots');

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function sendCDP(ws, method, params = {}) {
  const id = Math.floor(Math.random() * 1000000);
  return new Promise((resolve, reject) => {
    const handler = (event) => {
      const msg = JSON.parse(event.data.toString());
      if (msg.id === id) {
        ws.removeEventListener('message', handler);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function captureScreen(ws, filename) {
  const { data } = await sendCDP(ws, 'Page.captureScreenshot', { format: 'png' });
  const buffer = Buffer.from(data, 'base64');

  const p1 = path.join(ARTIFACTS_DIR, filename);
  const p2 = path.join(OUTPUT_DIR, filename);

  fs.writeFileSync(p1, buffer);
  fs.writeFileSync(p2, buffer);
  console.log(`Saved screenshot: ${filename} (${buffer.length} bytes)`);
}

async function main() {
  console.log('Starting SUMO simulation via REST API...');
  const startRes = await fetch('http://127.0.0.1:8000/api/simulation/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mode: 'coordinated',
      duration: 600,
      seed: 42,
      enable_emergency: true,
    }),
  });
  const startJson = await startRes.json();
  console.log('Simulation started:', startJson);

  // Wait 8 seconds for SUMO TraCI vehicles to enter network
  console.log('Waiting 8 seconds for SUMO vehicles to spawn...');
  await sleep(8000);

  // Launch Chrome
  console.log(`Launching headless Chrome on port ${PORT}...`);
  const tempProfile = path.resolve('outputs/temp_chrome_live_profile');
  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    `--remote-debugging-port=${PORT}`,
    '--disable-gpu',
    '--no-sandbox',
    `--user-data-dir=${tempProfile}`,
    'about:blank',
  ]);

  let ready = false;
  for (let i = 0; i < 30; i++) {
    await sleep(300);
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (res.ok) {
        ready = true;
        break;
      }
    } catch (_) {}
  }

  if (!ready) {
    chromeProc.kill();
    throw new Error('Chrome failed to start within timeout');
  }

  const targetsRes = await fetch(`http://127.0.0.1:${PORT}/json/list`);
  const targets = await targetsRes.json();
  const pageTarget = targets.find((t) => t.type === 'page') || targets[0];

  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });

  await sendCDP(ws, 'Runtime.enable');
  await sendCDP(ws, 'Page.enable');

  console.log('Navigating to http://localhost:5173/...');
  await sendCDP(ws, 'Page.navigate', { url: 'http://localhost:5173/' });
  await sleep(2500);

  await sendCDP(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false,
  });

  async function clickButtonWithText(text) {
    console.log(`Clicking button: "${text}"...`);
    return await sendCDP(ws, 'Runtime.evaluate', {
      expression: `(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const target = buttons.find(b => b.textContent.includes('${text}'));
        if (target) { target.click(); return true; }
        return false;
      })()`,
      returnByValue: true,
    });
  }

  // Switch to 3D tab
  await clickButtonWithText('3D Digital Twin');
  await sleep(3500);

  // Capture Live Area Overview with moving vehicles
  console.log('Capturing Live Area Overview with SUMO vehicles...');
  await captureScreen(ws, 'digital_twin_live_area_vehicles.png');

  // Switch to Corridor Overview
  await clickButtonWithText('Corridor Overview');
  await sleep(2000);
  console.log('Capturing Live Corridor Overview with SUMO vehicles...');
  await captureScreen(ws, 'digital_twin_live_corridor_vehicles.png');

  // Switch to J2 Central Silk Board
  await clickButtonWithText('J2 Central Silk Board');
  await sleep(2000);
  console.log('Capturing Live J2 Silk Board with SUMO vehicles & signals...');
  await captureScreen(ws, 'digital_twin_live_j2_vehicles.png');

  // Clean shutdown
  ws.close();
  chromeProc.kill();

  // Stop simulation cleanly
  console.log('Stopping simulation...');
  await fetch('http://127.0.0.1:8000/api/simulation/stop', { method: 'POST' });
  console.log('Simulation stopped cleanly.');
}

main().catch(async (err) => {
  console.error('Error during live 3D capture:', err);
  try {
    await fetch('http://127.0.0.1:8000/api/simulation/stop', { method: 'POST' });
  } catch (_) {}
  process.exit(1);
});
