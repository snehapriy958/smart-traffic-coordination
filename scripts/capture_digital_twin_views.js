/**
 * scripts/capture_digital_twin_views.js
 *
 * Automated High-Resolution Visual Verification for 3D Area-Wide Digital Twin.
 * Launches Chrome via CDP, navigates to the 3D Digital Twin tab, cycles through
 * camera presets, launches Evaluator Demo Tour, starts simulation, and captures
 * high-resolution PNG snapshots.
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9222;
const ARTIFACTS_DIR = 'C:\\Users\\Sneha Singh\\.gemini\\antigravity\\brain\\1bc986a7-c556-43f9-8c53-6ea55756f37e\\screenshots';
const OUTPUT_DIR = path.resolve('outputs/screenshots');

for (const dir of [ARTIFACTS_DIR, OUTPUT_DIR]) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

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
  console.log(`Launching headless Chrome on port ${PORT}...`);
  const tempProfile = path.resolve('outputs/temp_chrome_twin_profile');
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
  if (!pageTarget || !pageTarget.webSocketDebuggerUrl) {
    chromeProc.kill();
    throw new Error('No page target found in Chrome');
  }

  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });

  const consoleLogs = [];
  const errors = [];

  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(event.data.toString());
    if (msg.method === 'Runtime.consoleAPICalled') {
      const text = msg.params.args.map((a) => a.value || JSON.stringify(a)).join(' ');
      consoleLogs.push({ type: msg.params.type, text });
      if (msg.params.type === 'error') errors.push(text);
    } else if (msg.method === 'Runtime.exceptionThrown') {
      errors.push(msg.params.exceptionDetails.text);
    }
  });

  await sendCDP(ws, 'Runtime.enable');
  await sendCDP(ws, 'Page.enable');

  console.log('Navigating to http://localhost:5173/...');
  await sendCDP(ws, 'Page.navigate', { url: 'http://localhost:5173/' });
  await sleep(2000);

  console.log('Setting desktop viewport 1920x1080...');
  await sendCDP(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false,
  });

  await sleep(2000);

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

  // 1. Switch to 3D Digital Twin Tab
  console.log('Switching to 3D Digital Twin Tab...');
  await clickButtonWithText('3D Digital Twin');
  await sleep(3500); // Allow Three.js canvas & WebGL shaders to initialize

  // 2. Capture Area Overview (Default Preset)
  console.log('Capturing Area Overview...');
  await captureScreen(ws, 'digital_twin_area_overview.png');

  // 3. Capture Corridor Overview
  console.log('Selecting Corridor Overview...');
  await clickButtonWithText('Corridor Overview');
  await sleep(1500);
  await captureScreen(ws, 'digital_twin_corridor_overview.png');

  // 4. Capture J2 Silk Board Close-up
  console.log('Selecting J2 Central Silk Board...');
  await clickButtonWithText('J2 Central Silk Board');
  await sleep(1500);
  await captureScreen(ws, 'digital_twin_j2_rotary.png');

  // 5. Capture J1 Madiwala Close-up
  console.log('Selecting J1 Madiwala Checkpost...');
  await clickButtonWithText('J1 Madiwala Checkpost');
  await sleep(1500);
  await captureScreen(ws, 'digital_twin_j1_madiwala.png');

  // 6. Capture J3 Rupena Agrahara Close-up
  console.log('Selecting J3 Rupena Agrahara...');
  await clickButtonWithText('J3 Rupena Agrahara');
  await sleep(1500);
  await captureScreen(ws, 'digital_twin_j3_rupena.png');

  // 7. Open Evaluator Tour
  console.log('Opening Evaluator Demonstration Tour...');
  await clickButtonWithText('Evaluator Tour');
  await sleep(1500);
  await captureScreen(ws, 'digital_twin_evaluator_tour.png');

  // 8. Close Tour and Return to Area Overview
  await clickButtonWithText('Exit Tour');
  await sleep(500);
  await clickButtonWithText('Area Overview');
  await sleep(1500);

  // Clean shutdown
  ws.close();
  chromeProc.kill();

  console.log('\n--- Digital Twin Visual Verification Complete ---');
  console.log(`Console Logs: ${consoleLogs.length}`);
  console.log(`Errors: ${errors.length}`);
  if (errors.length > 0) {
    console.error('Errors encountered:');
    errors.forEach((e) => console.error('  - ' + e));
  } else {
    console.log('Zero errors detected in 3D WebGL execution.');
  }
}

main().catch((err) => {
  console.error('Digital Twin capture failed:', err);
  process.exit(1);
});
