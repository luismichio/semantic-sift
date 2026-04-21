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

### 2. Git Merge Conflict
**Noise**: Multi-line hunk headers and metadata.
**Signal**: The conflict markers and local/incoming divergence.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `index 4c2a1d3,8e9f2a1..0000000` | `CONFLICT (content): Merge conflict in index.html` |
| `--- a/index.html` | `<<<<<<< HEAD` |
| `+++ b/index.html` | `    <title>My Local Website Title</title>` |

### 3. HDFS System Logs (The Monster)
**Noise**: Legacy `YYMMDD` timestamps and repetitive `INFO dfs.` boilerplate.
**Signal**: The specific block operation and status.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `081109 203615 148 INFO dfs.DataNode$PacketResponder: ...` | `PacketResponder 1 for block blk_38865... terminating` |
| `081109 204005 35 INFO dfs.FSNamesystem: BLOCK* ...` | `BLOCK* NameSystem.addStoredBlock: blockMap updated...` |

### 4. GitHub Actions (CI)
**Noise**: Group/section markers and debug environment variables.
**Signal**: Actual test pass/fail results.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `2024-06-17T16:29:41Z ##[group]Run dotnet test` | `dotnet test --configuration Release --no-build` |
| `2024-06-17T16:30:52Z [FAIL] IntegrationTests...` | `[FAIL] IntegrationTests.WebTests.GetAccounts...` |

### 5. NPM Install
**Noise**: Long progress strings and funding boilerplate.
**Signal**: Package count and installation status.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `npm install --save semantic-sift` | `npm install --save semantic-sift` |
| `........................................` | `added 124 packages in 5s` |
| `34 packages are looking for funding` | `run npm fund for details` |

### 6. Natural Language (Semantic)
**Noise**: Repetitive Markdown links, badge formatting, and conversational filler.
**Signal**: Core technical features and value proposition.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `FastAPI framework, high performance...` | `FastAPI: fast high-performance framework` |
| `<a href="..."><img src="..."></a>` | `Python type hints based` |
| `Fast to code: Increase speed by 200%` | `Increases dev speed 200-300%` |

### 7. Git History
**Noise**: ISO-8601 timestamps and multi-line author/committer headers.
**Signal**: Commit hash, author name, and the core message.

| Raw Input (Noise) | Sifted Output (Signal) |
| :--- | :--- |
| `Author: John Keeping <john@...>` | `Author: John Keeping` |
| `Date: 2015-09-03 17:12:23 +0100` | `date: make "local" orthogonal to date format` |
| `CommitDate: 2015-10-05 14:30:00 -0700` | `Git 2.45.0-rc1` |

---

## 🛰️ Global Verification
All benchmark pulses are transmitted to the global registry with the `[Tier: Benchmark]` flag. Every sample used in these tests is visible and auditable in the **`benchmarks/data/`** directory.

**Live Lab Dashboard**: [www.luiskobayashi.com](https://www.luiskobayashi.com)

---
*Building high-fidelity context for the Studio of Two.*
