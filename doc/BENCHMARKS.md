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

### 3. Natural Language (Semantic)
**The Impact**: Achieves near-total reduction on low-entropy boilerplate while preserving instructions. 

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. Every sample used in these tests is visible and auditable in the **`benchmarks/data/`** directory.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
