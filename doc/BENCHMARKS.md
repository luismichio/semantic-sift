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

## 🔍 Visual Proof: The "Clean File" Evidence

To avoid the perception of data manipulation, we provide direct access to the raw inputs and the resulting "clean" files. Seeing the actual logs stripped of noise is the ultimate proof of Semantic-Sift's surgical precision.

### 🔦 Featured Example: Vercel Build Failure
Below is a realistic comparison of a Vercel deployment log. Notice how the engine identifies and incinerates the bracketed timestamps and repetitive boilerplate while preserving the exact error trace.

#### **Raw Log (Noise)**
```text
[14:22:05.123] Running build in "production"
[14:22:05.456] Detected Next.js version: 14.1.0
[14:22:05.789] Running "npm run build"
[14:22:06.111] > my-app@0.1.0 build
[14:22:06.111] > next build
[14:22:06.450]  ▲ Next.js 14.1.0
[14:22:06.450] 
[14:22:07.890] Creating an optimized production build ...
[14:22:15.234] Failed to compile.
[14:22:15.235] ./src/components/UserCard.tsx:14:22
[14:22:15.235] Type error: Property 'email' does not exist on type 'UserProps'.
```

#### **Sifted Result (Signal)**
```text
Running build in "production"
Detected Next.js version: 14.1.0
Running "npm run build"
> my-app@0.1.0 build
> next build
▲ Next.js 14.1.0
Failed to compile.
./src/components/UserCard.tsx:14:22
Type error: Property 'email' does not exist on type 'UserProps'.
```

### 🧪 Full Benchmark Lab (Audit Yourself)
You can inspect the full "Before & After" for every scenario by opening the source files directly in this repository:

| Scenario | Raw Input (Noise) | Sifted Result (Clean) |
| :--- | :--- | :--- |
| **HDFS System Logs** | [hdfs_system_logs.txt](../benchmarks/data/hdfs_system_logs.txt) | [hdfs_system_logs_sifted.txt](../benchmarks/results/hdfs_system_logs_sifted.txt) |
| **Git Merge Conflict** | [git_diff.txt](../benchmarks/data/git_diff.txt) | [git_diff_sifted.txt](../benchmarks/results/git_diff_sifted.txt) |
| **GitHub Actions (CI)** | [github_actions.txt](../benchmarks/data/github_actions.txt) | [github_actions_sifted.txt](../benchmarks/results/github_actions_sifted.txt) |
| **NPM Install** | [npm_install.txt](../benchmarks/data/npm_install.txt) | [npm_install_sifted.txt](../benchmarks/results/npm_install_sifted.txt) |
| **Git History** | [git_history.txt](../benchmarks/data/git_history.txt) | [git_history_sifted.txt](../benchmarks/results/git_history_sifted.txt) |
| **Natural Language** | [natural_language.txt](../benchmarks/data/natural_language.txt) | [natural_language_sifted.txt](../benchmarks/results/natural_language_sifted.txt) |

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. Every sample used in these tests is visible and auditable in the **`benchmarks/data/`** directory.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
