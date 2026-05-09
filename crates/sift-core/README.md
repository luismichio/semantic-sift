# 🦀 sift-core

**High-performance context distillation for local-first AI applications.**

`sift-core` is the native Rust heart of the Semantic-Sift ecosystem. It provides ultra-low-latency text distillation and noise removal, designed specifically to be embedded as a library in Rust applications or bundled as a **Sidecar** for desktop frameworks like **Tauri**.

---

## 🚀 Why sift-core?

`sift-core` was born to sift unnecessary tokens from the context window. It originated as a critical component of [**Meechi**](https://meechi.me)—a local-first, symbiotic space designed for the **"Studio of Two."**

Because local-first AI relies on smaller LLMs, context size is a precious resource. To keep reasoning accurate and avoid **"context rot,"** a condensed and concise context is necessary. `sift-core` provides this distillation without the "Python distribution tax," ensuring high-fidelity intelligence on local hardware.

Since its inception, it has grown into a tool for developers who want to:
- **💰 Save Tokens**: Dramatically reduce API costs and local compute overhead.
- **✨ Preserve Quality**: Prune the noise without sacrificing the semantic signal or reasoning accuracy.
- **📦 Ship Native**: Add sophisticated sifting to any app (Tauri, Electron, CLI) via a single, compact Rust binary.

- **📦 Zero Python Dependencies**: No `pip install`, no virtual environments, no runtime bloat.
- **⚡ Built for Speed**: Heuristic sifting is near-instant; semantic distillation is optimized via **ONNX Runtime**.
- **🛠️ Tauri-Ready**: Designed and battle-tested as a high-performance **Sidecar**.
- **🧠 Intelligent Compression**: Implements **LLMLingua-2** locally to ensure every token is pure signal.

---

## 🛠️ Installation

### As a Rust Library
Add to your `Cargo.toml`:

```toml
[dependencies]
semantic-sift-core = { git = "https://github.com/your-repo/semantic-sift", path = "crates/sift-core" }
```

### As a CLI / Sidecar
Build the binary:

```bash
cargo build --release --bin sift-core
```

The resulting binary in `target/release/sift-core` can be used as a standalone tool or a Tauri sidecar.

---

## 📖 Usage

### 1. Heuristic Sifting (Logs & Noise)
Instantly strip timestamps, progress bars, and metadata from technical logs.

```rust
use semantic_sift_core::apply_heuristic_sieve;

let raw_logs = "2026-05-01T12:00:00Z INFO [1/42] Compiling... some signal";
let clean_signal = apply_heuristic_sieve(raw_logs);
// Result: "some signal"
```

### 2. Semantic Distillation (Prose & Chat)
Use the neural engine to prune tokens while keeping 95% of the "meaning." Requires an ONNX model directory.

```rust
use semantic_sift_core::SemanticEngine;

let mut engine = SemanticEngine::new("path/to/model_dir")?;
let distilled = engine.compress("Your long prompt here...", 0.5)?; // 50% compression
```

---

## 📊 Performance

`sift-core` is benchmarked to handle high-throughput scenarios:

- **Heuristic Sieve**: ~100 lines of logs sifted in <1ms.
- **Semantic Engine**: Sub-100ms inference for standard context blocks (on modern CPUs).

To run benchmarks yourself:
```bash
cargo bench -p semantic-sift-core
```

---

## 🏗️ Architecture: The Hybrid Edge

`sift-core` uses a unique hybrid architecture to solve the speed-vs-intelligence trade-off in local-first AI. Instead of running every character through a heavy neural network, it operates in two distinct, coordinated phases:

### Phase 1: The Heuristic Sieve (Deterministic)
The first layer is a high-speed, native Rust regex engine that identifies and incinerates **"Structural Noise."**
- **What it catches**: Timestamps, progress bars, hex IDs, ISO-8601 dates, and repetitive log boilerplate.
- **The Benefit**: This runs in microseconds with zero AI overhead. By cleaning the easy noise first, we reduce the token load on the next phase by up to 40% before it even touches a model.

### Phase 2: The Semantic Sift (Probabilistic)
The second layer uses the **LLMLingua-2** token-classification model running on **ONNX Runtime**.
- **What it catches**: Natural language "filler," redundant prose, and low-entropy tokens that don't contribute to the model's reasoning.
- **The Benefit**: It focuses its intelligence only on the "Signal" left behind by the Sieve. This ensures that the limited context window of a local LLM is filled with pure semantic value, preventing the **"Context Rot"** that typically degrades smaller models.

**Why Hybrid?**
Pure neural distillation is too slow for real-time logs; pure regex is too "dumb" for natural language. The hybrid approach gives you **instant responses** for technical data and **deep intelligence** for prose, all while keeping your CPU and GPU free for your main application logic.

---

## 🤖 The Intelligent Router

`sift-core` is the high-performance engine for the entire ecosystem. The main Python-based `semantic-sift` package (and its `semantic-sift-cli` command) acts as an **Intelligent Router** that picks the right tool for the job:

### ⚡ Rust (`sift-core`): Optimized for Latency
- **Use Case**: Short-to-medium tasks (<30,000 chars), IDE hooks, and real-time chat.
- **Why**: It shells out instantly with near-zero cold-start time. By using the ONNX Runtime, it provides a "zero-lag" experience for interactive sifting without waking up a heavy ML framework.

### 🐘 Python (`PyTorch`): Optimized for Throughput
- **Use Case**: Massive batch tasks, entire codebases, and multi-gigabyte logs.
- **Why**: While Rust is faster for single-pass tasks, the Python backend leverages the full **PyTorch** ecosystem for massive scaling. It utilizes specialized kernels like **Flash Attention** and **$O(n)$ memory scaling** that provide better stability and throughput for multi-million token batches.
- **Stability**: For industrial-scale data, the mature memory-management and specialized hardware kernels in the PyTorch stack prevent memory explosion where a standard ONNX session might struggle.

By using `sift-core`, you are using the same high-speed engine that guarantees a "zero-lag" experience for real-time agents, while knowing that the system can still scale to massive datasets when needed.

---

## ⚖️ License

Apache-2.0. Developed as part of the **Studio of Two** philosophy: *Systems, not Patches.*

Copyright (c) 2026 Luis Kobayashi. All rights reserved.
