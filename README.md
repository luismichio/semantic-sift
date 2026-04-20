# 🔍 Semantic-Sift

**The "Sanitation Tier" for high-fidelity agentic workflows.**

[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen)](tests/)
[![Security](https://img.shields.io/badge/Security-Bandit%20Inspected-brightgreen)](SECURITY.md)
[![Dependencies](https://img.shields.io/badge/Dependencies-0%20CVEs-brightgreen)](SECURITY.md)
[![License](https://img.shields.io/badge/License-Source--Available-blue)](LICENSE.md)

Semantic-Sift is a standalone [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server designed to preserve signal and incinerate noise. It acts as an intelligent middleware that distills raw data into high-density context *before* it enters an LLM's context window.

---

## 🛡️ Security & Testing

Semantic-Sift is built on a **Zero-Vulnerability Baseline**. We use automated cybersecurity tools to ensure the engine is safe for professional use:
- **Pytest**: 100% pass rate on heuristic integrity and privacy kill-switch math.
- **Bandit (SAST)**: Automated static analysis to prevent insecure Python patterns.
- **Pip-Audit (SCA)**: Real-time supply chain monitoring to ensure 0 known vulnerabilities in our dependencies.

See [SECURITY.md](SECURITY.md) for our full security policy and vulnerability reporting.

---

## 🧠 The Problem: Context Flooding
In the era of 128k+ token windows, the bottleneck is no longer capacity—it is **Signal-to-Noise Ratio (SNR)**. 
- **Lost in the Middle**: LLMs lose reasoning accuracy when context is filled with repetitive boilerplate.
- **Token Inflation**: Technical logs and chat histories are often 80% noise, wasting thousands of tokens per turn.
- **Hallucination**: Messy data (like OCR artifacts or redundant JSON) triggers false patterns in RAG systems.

**Semantic-Sift solves this by "Sanitizing" the data stream locally on your machine.**

---

## 💰 Beyond Cost Savings: Why Sift?

Whether your AI tools charge **per token** or **per request**, Semantic-Sift provides critical operational value:

### 1. Per-Token Billing (Direct ROI)
- **Wallet Benefit**: Every character pruned is money saved. Sift typically reduces token overhead by 30-70%.

### 2. Per-Request Billing (Quality ROI)
- **Attention Precision**: Models don't get "Lost in the Middle." By removing noise, you ensure the LLM's full reasoning power is focused on the signal.
- **Latency reduction**: Smaller, cleaner prompts result in faster "Time to First Token" (TTFT) and snappier interactions.
- **Context Insurance**: Prevents "Context length exceeded" errors on paid requests by ensuring your data always fits the model's hard limits.
- **Tier Optimization**: Stay within "Small/Unlimited" request tiers by compacting "Large" data down to high-density signal.

---

## 🛠️ Core Capabilities

### 1. The Structural Sieve (`sift_logs`)
**Heuristic Distillation for Technical Data.**
`sift_logs` uses high-speed regex engines to strip structural noise from technical outputs.
- **Targets**: **Vercel** build logs, **GitHub Actions** outputs, Webpack/Vite module listings, and NPM/Yarn install progress.
- **The Magic**: It removes repetitive timestamps (`2026-04-17T...`), UUIDs, and progress bars while **preserving** the actual error messages, stack traces, and line numbers.
- **Result**: A 5,000-line log becomes 50 lines of pure actionable signal.

### 2. The Semantic Sift (`sift_chat`)
**AI-Powered Pruning for Natural Language.**
Powered by **LLMLingua-2** (BERT), this tool understands the "meaning" of sentences and prunes linguistic filler.
- **Targets**: **Slack/Discord** threads, **Meeting Transcripts**, and long **Assistant replies**.
- **The Magic**: It identifies "low-entropy" tokens (e.g., "I think that maybe we should perhaps...") and prunes them while keeping "high-entropy" instructions (e.g., "Update the schema"). 
- **Result**: Reduces token load by 30-70% with 95%+ fidelity to the original meaning.

### 3. The Document & RAG Refinery (`sift_doc` | `sift_extraction`)
**Hybrid Signal Extraction.**
A multi-stage pipeline designed for long-form documentation and messy OCR extractions.
- **Targets**: Massive **ARCHITECTURE.md** files, PDF technical papers, and outputs from **Docling** or **LiteParse**.
- **The Magic**: First, it performs a structural sieve to remove footers, page numbers, and copyright notices. Then, it applies a semantic sift to condense the prose into a high-density "Knowledge Map."
- **Result**: Allows an agent to "see" a 50-page document in a single, high-signal context window.

### 4. Subconscious Sifting (Background Hooks)
**Silent Context Sanitation.**
Intercepts data streams *before* they enter the context window for zero-latency reasoning.
- **Deep Integration**: Deeply hooks into **Gemini CLI**, **Claude Code**, and **OpenCode**.
- **Heuristic Interception**: Automatically cleans logs and verbose tool outputs in the background using the high-speed sieve engine.
- **Visibility**: Every background sift is logged as `hook_sift_logs` in your telemetry report.

---

## 🎯 The Intelligence Tier

### Smart Context Advisory (`sift_analyze`)
Semantic-Sift is self-aware. The `sift_analyze` tool acts as a "Context Consultant" for the agent.
- **Function**: Analyzes a string and calculates an **Estimated Noise %**.
- **Environment Aware**: Detects host-level truncation (Gemini CLI) and recommends mandatory sifting of the raw source files.
- **Benefit**: Prevents the agent from wasting time sifting data that is already lean.

### Relevance-First Ranking (`sift_rank`)
Using a local **BGE-Reranker**, Sift can prioritize information *before* it is processed.
- **Function**: Takes a query and a list of chunks (e.g., from a search) and re-orders them by semantic relevance.
- **Benefit**: Ensures the "Sifting" happens only on the most important data, maximizing the agent's reasoning power.

---

## 🤝 Universal Orchestration: The "Chain of Context"

Semantic-Sift is designed to be the **intelligent glue** between all your specialist MCPs. When you run `sift_onboard()`, it automatically detects your active tools and injects high-fidelity collaborative rules into your instruction files.

### Orchestration Blueprints:
*   **Discovery (Serena, Investigator)**: Always pipe code bodies > 100 lines through `sift_chat` after retrieval to prune docstring and comment bloat while preserving logic.
*   **Storage (Context-Mode, Memory)**: Sift all tool outputs > 1,000 characters **before** they are indexed into a searchable database to ensure search results remain high-signal.
*   **Knowledge (Slack, Notion, Discord, Confluence)**: Distill chat history and wiki pages to isolate decisions and action items, ignoring UI noise, block IDs, and system events.
*   **Infrastructure (AWS, Azure, GCP, Kubernetes)**: Apply `sift_logs` to massive cloud resource snapshots (JSON) to strip redundant fields (ETags, Request IDs, Timestamps).
*   **Data (Postgres, SQL, SQLite)**: If a query returns a massive result set, Sift keeps the schema and edge rows while pruning the middle to maintain a lean context.
*   **Browsing (Puppeteer, Playwright, Browser)**: Automatically clean up raw HTML fetches by removing navigation menus, footers, and tracking scripts before analysis.
*   **Workflow (Jira, Linear)**: Sift ticket descriptions and comment chains to focus on the 'State Change' and 'Resolution' logic, ignoring boilerplate status updates.

---

## 🚀 Performance & Sovereignty

- **GPU Accelerated**: Optimized for **Python 3.12** and **CUDA 12.1** (Runs sub-second on an RTX 2070+).
- **Persistent Cache**: Repeat sifts are **instantaneous (~1ms)** thanks to a local SHA-256 disk cache.
- **Unified Telemetry**: Tracks characters saved across both manual tools and automatic background hooks (`hook_sift_logs`).
- **Local Sovereignty**: No data ever leaves your machine. All models (BERT, BGE) run locally to protect your privacy and wallet.

---

## 🚀 Quick Start

1. **Clone & Setup**
   ```bash
   git clone https://github.com/luismichio/semantic-sift.git
   cd semantic-sift
   py -3.12 -m venv venv312
   .\venv312\Scripts\activate
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   pip install -r requirements.txt
   ```

2. **Onboard Your Project**
   Run the following tool once connected to automatically configure your instruction files (`.cursorrules`, `AGENTS.md`, etc.):
   `semantic-sift.sift_onboard()`

---

## 🛰️ Global Telemetry & Proof of Value

Semantic-Sift includes a **"Solid Pulse"** telemetry system that securely and anonymously tracks the value provided by the engine.

- **The Goal**: To aggregate total character and token savings across the entire community to prove the ROI of context sanitation.
- **Privacy First**: The engine **never** transmits raw text or code. It only sends metadata (character counts, tool names, and anonymous machine IDs).
- **The Counter**: See the live impact of the community at [luiskobayashi.com/api/sift](https://www.luiskobayashi.com).

### 🛡️ Privacy Override (Meechi Compliance)
For sensitive environments or projects with a strict non-tracking policy, you can completely disable all telemetry by setting:
`SIFT_TELEMETRY_DISABLED=true`

---

## ⚖️ Dual-License Model

Semantic-Sift is provided under a **Source-Available Dual License**.

1. **Personal Use (FREE)**: Free for individuals, researchers, and non-commercial development.
2. **Commercial Use (PAID)**: A license is required for use in corporate environments, paid client work, or when embedding Sift into commercial software.

### **Commercial Benefits**:
- Legal right to use for profit.
- Access to high-performance **frozen binaries** (no Python required).
- Advanced **Multi-IDE synchronization** and organizational policies.

Obtain a license at [luiskobayashi.com/sift](https://www.luiskobayashi.com/sift).

---

## 📖 Philosophy: The Studio of Two
Semantic-Sift is a product of the **Studio of Two** philosophy: *We build Systems, not Patches.* It is a "Sovereign Sidecar" designed to empower the human-AI partnership.

## 📄 License
Source-Available. See `LICENSE.md` for details.
