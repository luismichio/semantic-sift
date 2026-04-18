# 🔍 Semantic-Sift

**The "Sanitation Tier" for high-fidelity agentic workflows.**

Semantic-Sift is a standalone [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server designed to preserve signal and incinerate noise. It acts as an intelligent middleware that distills raw data into high-density context *before* it enters an LLM's context window.

---

## 🧠 The Problem: Context Flooding
In the era of 128k+ token windows, the bottleneck is no longer capacity—it is **Signal-to-Noise Ratio (SNR)**. 
- **Lost in the Middle**: LLMs lose reasoning accuracy when context is filled with repetitive boilerplate.
- **Token Inflation**: Technical logs and chat histories are often 80% noise, wasting thousands of tokens per turn.
- **Hallucination**: Messy data (like OCR artifacts or redundant JSON) triggers false patterns in RAG systems.

**Semantic-Sift solves this by "Sanitizing" the data stream locally on your machine.**

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

---

## 🎯 The Intelligence Tier

### Smart Context Advisory (`sift_analyze`)
Semantic-Sift is self-aware. The `sift_analyze` tool acts as a "Context Consultant" for the agent.
- **Function**: Analyzes a string and calculates an **Estimated Noise %**.
- **Action**: If a log is 90% noise, it tells the agent: *"Recommendation: Run `sift_logs` before reading."*
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

## 📖 Philosophy: The Studio of Two
Semantic-Sift is a product of the **Studio of Two** philosophy: *We build Systems, not Patches.* It is a "Sovereign Sidecar" designed to empower the human-AI partnership.

## 📄 License
MIT. See `LICENSE` for details.
