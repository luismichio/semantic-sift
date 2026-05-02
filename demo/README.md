# Semantic-Sift Native Sidecar Demo

This directory contains a minimal demonstration of how to integrate the **Semantic-Sift Native Rust Sidecar** (`sift-core`) into a Node.js-based desktop environment (like **Tauri** or **Electron**).

## 🚀 How it works

The demo script (`sidecar_demo.js`) simulates a "Subconscious Middleware" workflow:
1. It loads a messy, raw terminal log (`sample_noise.log`).
2. It spawns the compiled `sift-core` binary as a child process.
3. It pipes the raw text into the sidecar's `stdin`.
4. It receives the distilled, noise-free context from `stdout`.

## 🛠️ Prerequisites

1. **Rust** installed on your machine.
2. **Node.js** installed on your machine.

## 🏃 Running the Demo

1. **Build the sidecar**:
   ```bash
   cd ../crates/sift-core
   cargo build
   ```

2. **Run the demo script**:
   ```bash
   cd ../../demo
   node sidecar_demo.js
   ```

## 📊 Expected Output

The demo will print a comparison of the "Before" vs "After" context, along with real-world reduction percentages and processing latency (usually < 20ms).
