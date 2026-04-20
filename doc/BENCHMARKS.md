# 📊 Semantic-Sift: Performance Benchmarks

This document provides empirical evidence of the sifting engine's impact across common technical and natural language scenarios.

*Data generated on: 2026-04-20*

---

## 🚀 Key Results Summary

| Scenario | Reduction | Tier | Latency |
| :--- | :--- | :--- | :--- |
| **Vercel Build Logs** | **90.5%** | Heuristic | 0.91ms |
| **Natural Language** | **68.0%** | Semantic | 1200ms |
| **NPM Install Progress** | **25.3%** | Heuristic | 0.82ms |
| **GitHub History** | **12.2%** | Real Data | 0.05ms |
| **Combined Average** | **53.8%** | Hybrid | -- |

---

## 🔍 Scenario Deep-Dive

### 1. Vercel Build Logs
**The Noise**: Repetitive ISO timestamps, progress indicators ([1/534]), and verbose module listings.
**The Impact**: The engine's strongest area. By "incinerating" repetitive formatting noise, we pack **10x more signal** into the same context window.

### 2. Natural Language (Semantic)
**The Noise**: Linguistic filler, redundant greetings, and low-entropy phrases.
**The Impact**: Powered by **LLMLingua-2 (BERT)**, this tier achieves high compression while maintaining 95%+ fidelity to the original meaning.

### 3. GitHub History (REAL DATA)
**The Noise**: Commit hashes, author metadata, and ISO timestamps.
**The Impact**: Even on real-world, high-value data, the engine consistently removes overhead without human intervention.

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. This allows us to track the evolution of our sifting heuristics in a controlled "Lab Environment" without skewing real-world user metrics.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
