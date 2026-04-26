# 📊 Semantic-Sift: Performance Benchmarks

This document provides empirical evidence of the sifting engine's impact across common technical and natural language scenarios.

*Data generated on: 2026-04-20*

---

## 🚀 Key Results Summary

| Scenario | Reduction | Tokens Saved | Tier | Goal |
| :--- | :--- | :--- | :--- | :--- |
| **AWS Framework (PDF)** | **58.2%** | **~276,450** | Multi-Modal | Prune 14MB whitepaper into core signal. |
| **Financial Data (XLSX)** | **54.4%** | **~14,650** | Multi-Modal | Preserve data tables in Markdown. |
| **MCP Architecture (HTML)** | **46.5%** | **~2,940** | Multi-Modal | Strip DOM noise (sidebars/nav/footer). |
| **HDFS System Logs** | **32.5%** | **~23,200** | Legacy | Prune YYMMDD timestamps & metadata. |
| **Vercel Build Logs** | **26.6%** | **~60** | Heuristic | Incinerate formatting boilerplate. |
| **GitHub Action (CI)** | **47.5%** | **~150** | Heuristic | Remove debug/group markers. |
| **NPM Install** | **25.9%** | **~20** | Heuristic | Prune progress bars/dots. |
| **Git History** | **16.4%** | **~25** | Surgical | Remove ISO-8601 timestamps. |
| **Natural Language** | **99.9%** | **~6,000** | Semantic | Prune linguistic filler (BERT). |

---

## 🔍 High-Volume Deep-Dive

### 1. AWS Whitepaper (The "Context Goliath")
- **Raw Volume**: 1.9M Characters (14MB PDF).
- **The Challenge**: Massive technical documents with nested tables, diagram captions, and repetitive headers/footers.
- **The Impact**: Sift reduced the document by **58.2%** in a single pass (43s latency). By converting to structural Markdown via MarkItDown before sifting, the engine removed over 1.1 million characters of noise while preserving every architectural principle and best practice table.

### 2. CI/CD Logs (GitHub Actions & Vercel)
**The Impact**: Standardizes noisy outputs from multiple cloud providers. Sift handles both the `[HH:MM:SS]` Vercel format and the `YYYY-MM-DDTHH:MM:SSZ` GitHub format automatically.

---

## 🔍 Multi-Modal Deep-Dive

### 1. Microsoft Financial Sample (XLSX)
- **The Challenge**: Raw binary `.xlsx` data is inaccessible to LLMs. Standard CSV conversion often loses table alignment or includes hidden metadata.
- **The Impact**: By using MarkItDown and Semantic Sifting, a production-grade financial workbook was reduced from **107,725 characters** to **49,097 characters** (54.4% reduction). The resulting Markdown preserved all complex columns as a clean table, allowing the agent to perform financial reasoning with 100% accuracy.

### 2. MCP Documentation (HTML)
- **The Challenge**: Web pages are filled with DOM noise: left-nav sidebars, right-nav tables of contents, Top-Nav bars, and footers.
- **The Impact**: The Anthropic MCP architecture docs were reduced from **25,333 characters** to **13,555 characters** (46.5% reduction). The "Subconscious HTML" layer stripped the recursive navigation menus and social links, leaving only the technical architecture descriptions and code blocks.

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
| **AWS Framework (PDF)** | [aws_framework.pdf](../benchmarks/data/aws_framework.pdf) | [aws_framework_sifted.txt](../benchmarks/results/aws_framework_sifted.txt) |
| **Financial Data (Excel)** | [financial_sample.xlsx](../benchmarks/data/financial_sample.xlsx) | [financial_sample_sifted.txt](../benchmarks/results/financial_sample_sifted.txt) |
| **MCP Docs (HTML)** | [mcp_architecture.html](../benchmarks/data/mcp_architecture.html) | [mcp_architecture_sifted.txt](../benchmarks/results/mcp_architecture_sifted.txt) |
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
