/**
 * Semantic-Sift: Native Sidecar Integration Demo (Node.js)
 * 
 * This script demonstrates how a Tauri or Electron app would "talk" to the
 * sift-core sidecar binary to automatically clean context before sending it to an LLM.
 * 
 * Usage:
 * 1. Build the sidecar: `cargo build --release` inside `crates/sift-core`
 * 2. Run this demo: `node sidecar_demo.js`
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Path to the compiled sidecar binary (relative to this script)
// Note: In a real Tauri app, this would be bundled in src-tauri/bin/
const SIDECAR_PATH = path.join(__dirname, '..', 'crates', 'sift-core', 'target', 'debug', 'sift-core.exe');
const SAMPLE_LOG = path.join(__dirname, 'sample_noise.log');

/**
 * Call the Sift Sidecar binary
 * @param {string} command - 'logs' or 'semantic'
 * @param {string} input - The raw text to clean
 * @returns {Promise<string>} - The distilled context
 */
function callSiftSidecar(command, input) {
    return new Promise((resolve, reject) => {
        const child = spawn(SIDECAR_PATH, [command]);
        let output = '';
        let error = '';

        child.stdout.on('data', (data) => { output += data.toString(); });
        child.stderr.on('data', (data) => { error += data.toString(); });

        child.on('close', (code) => {
            if (code === 0) resolve(output.trim());
            else reject(new Error(`Sidecar failed with code ${code}: ${error}`));
        });

        // Pipe the raw context into the sidecar's stdin
        child.stdin.write(input);
        child.stdin.end();
    });
}

async function runDemo() {
    console.log("==========================================");
    console.log("🚀 SEMANTIC-SIFT: NATIVE SIDECAR DEMO");
    console.log("==========================================\n");

    if (!fs.existsSync(SIDECAR_PATH)) {
        console.error(`❌ Error: Sidecar binary not found at ${SIDECAR_PATH}`);
        console.error("Please run 'cargo build' inside 'crates/sift-core' first.");
        return;
    }

    const rawLogs = fs.readFileSync(SAMPLE_LOG, 'utf-8');
    console.log(`[Input] Raw Logs (${rawLogs.length} chars)`);
    console.log("------------------------------------------");
    console.log(rawLogs.split('\n').slice(0, 5).join('\n') + "\n...");
    console.log("------------------------------------------\n");

    console.log("Sifting context via native sidecar...");
    const startTime = Date.now();
    
    try {
        const distilledLogs = await callSiftSidecar('logs', rawLogs);
        const duration = Date.now() - startTime;

        console.log(`[Output] Distilled Context (${distilledLogs.length} chars)`);
        console.log(`[Stats] Reduction: ${((1 - distilledLogs.length / rawLogs.length) * 100).toFixed(1)}%`);
        console.log(`[Stats] Latency: ${duration}ms`);
        console.log("------------------------------------------");
        console.log(distilledLogs);
        console.log("------------------------------------------");
        console.log("\n✅ SUCCESS: The noise was incinerated locally in milliseconds.");
    } catch (err) {
        console.error("❌ Demo Failed:", err.message);
    }
}

runDemo();
