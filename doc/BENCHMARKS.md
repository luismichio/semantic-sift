# 📊 Semantic-Sift: Performance Benchmarks

This document provides empirical evidence of the sifting engine's impact across common technical and natural language scenarios.

*Data generated on: 2026-04-20*

---

## 🚀 Key Results Summary

| Scenario | Raw Tokens | Sifted Tokens | 🚀 Reduction | Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Vercel Build Logs** | 3,287 | 312 | **90.5%** | 1.61ms |
| **NPM Install Progress** | 4,050 | 3,024 | **25.3%** | 1.33ms |
| **Combined Average** | **7,337** | **3,336** | **54.5%** | **1.47ms** |

---

## 🔍 Scenario Deep-Dive

### 1. Vercel Build Logs
**The Noise**: Repetitive ISO timestamps, progress indicators ([1/534]), and verbose module listings.
**The Impact**: This is the engine's strongest area. By "incinerating" the repetitive formatting noise, we pack **10x more signal** into the same context window.

### 2. NPM Install Progress
**The Noise**: Long strings of dots (................) and boilerplate funding/package messages.
**The Impact**: While less aggressive than build logs, the 25% reduction ensures that large dependency installs don't "flood" the conversation, keeping the agent focused on the code.

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. This allows us to track the evolution of our sifting heuristics in a controlled "Lab Environment" without skewing real-world user metrics.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
