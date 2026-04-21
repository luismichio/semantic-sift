# 📊 Semantic-Sift: Performance Benchmarks

This document provides empirical evidence of the sifting engine's impact across common technical and natural language scenarios.

*Data generated on: 2026-04-20*

---

## 🚀 Key Results Summary

| Scenario | Reduction | Tier | Goal |
| :--- | :--- | :--- | :--- |
| **HDFS System Logs** | **32.5%** | Legacy | Prune YYMMDD timestamps & metadata. |
| **Vercel Build Logs** | **26.6%** | Heuristic | Incinerate formatting boilerplate. |
| **GitHub Action (CI)** | **47.5%** | Heuristic | Remove debug/group markers. |
| **NPM Install** | **25.9%** | Heuristic | Prune progress bars/dots. |
| **Git History** | **16.4%** | Surgical | Remove ISO-8601 timestamps. |
| **Natural Language** | **99.9%** | Semantic | Prune linguistic filler (BERT). |

---

## 🔍 High-Volume Deep-Dive

### 1. HDFS System Logs (The "Context Monster")
- **Raw Volume**: 71,462 tokens.
- **The Challenge**: Legacy `YYMMDD HHMMSS` timestamps and repetitive `INFO dfs.` metadata.
- **The Impact**: By adding legacy support, Sift saved **23,225 tokens** in a single pass (39ms latency). This proves that Sift can handle enterprise-scale log streams without context flooding.

### 2. CI/CD Logs (GitHub Actions & Vercel)
**The Impact**: Standardizes noisy outputs from multiple cloud providers. Sift handles both the `[HH:MM:SS]` Vercel format and the `YYYY-MM-DDTHH:MM:SSZ` GitHub format automatically.

---

## 🔍 Visual Proof: Before & After

Seeing is believing. Below are side-by-side examples of how Semantic-Sift "incinerates" noise while preserving the high-signal "Needle in the Haystack."

### 1. Vercel Build Failure
**Noise**: Repetitive bracketed timestamps.
**Signal**: The specific TypeScript error and code line.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `[14:22:05.123] Running build in "production"` | `Running build in "production"` |
| `[14:22:15.235] Failed to compile.` | `Failed to compile.` |
| `[14:22:15.235] ./src/components/UserCard.tsx:14:22` | `./src/components/UserCard.tsx:14:22` |
| `[14:22:15.235] Type error: Property 'email' does...` | `Type error: Property 'email' does...` |

### 2. Git Merge Conflict
**Noise**: Multi-line hunk headers and metadata.
**Signal**: The conflict markers and local/incoming divergence.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `diff --cc index.html` | `index.html` |
| `index 4c2a1d3,8e9f2a1..0000000` | `CONFLICT (content): Merge conflict in index.html` |
| `--- a/index.html` | `<<<<<<< HEAD` |
| `+++ b/index.html` | `    <title>My Local Website Title</title>` |

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. Every sample used in these tests is visible and auditable in the **`benchmarks/data/`** directory.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
