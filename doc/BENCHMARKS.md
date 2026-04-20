# 📊 Semantic-Sift: Performance Benchmarks

This document provides empirical evidence of the sifting engine's impact across common technical and natural language scenarios.

*Data generated on: 2026-04-20*

---

## 🚀 Key Results Summary

| Scenario | Reduction | Tier | Goal |
| :--- | :--- | :--- | :--- |
| **Vercel Build Logs** | **82.2%** | Heuristic | Incinerate formatting boilerplate. |
| **GitHub Action (CI)** | **77.8%** | Heuristic | Remove setup/teardown debris. |
| **NPM Install** | **25.3%** | Heuristic | Prune progress bars/dots. |
| **Git History (REAL)** | **1.7%** | Surgical | Remove ISO timestamps only. |
| **Git Diff (REAL)** | **0.7%** | Surgical | Remove hunk metadata only. |
| **Natural Language** | **68.0%** | Semantic | Prune linguistic filler (BERT). |

---

## 🔍 Scenario Deep-Dive

### 1. CI/CD Logs (GitHub Actions & Vercel)
**The Noise**: Repetitive ISO timestamps, progress indicators, and verbose environment setup.
**The Impact**: This is where Semantic-Sift provides the highest economic ROI. By removing ~80% of CI noise, you can fit **5x more log data** into a single turn, allowing for faster debugging of build failures.

### 2. Git Metadata (History & Diffs)
**The Impact**: Unlike CI logs, Git history is high-signal. The engine takes a **Surgical** approach here, only removing repetitive ISO timestamps and hunk headers. This ensures that the actual commit messages and code changes remain 100% intact while slightly reducing context overhead.

### 3. Natural Language (Semantic)
**The Impact**: Powered by **LLMLingua-2 (BERT)**, this tier achieves high compression on chat histories by identifying and removing low-entropy phrases while preserving instructions.

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
