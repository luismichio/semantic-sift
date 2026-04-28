# 🔍 Semantic-Sift

**The Reasoning-First Middleware for High-Fidelity Agentic Workflows.**

[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen)](tests/)
[![Security](https://img.shields.io/badge/Security-Bandit%20Inspected-brightgreen)](SECURITY.md)
[![License](https://img.shields.io/badge/License-Source--Available-blue)](LICENSE.md)

> **"It saves tokens while preserving context—maximizing reasoning, minimizing hallucination."**

Semantic-Sift is a local [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that acts as an intelligent "Sanitation Tier" between your raw data and your AI’s context window. 

While modern LLMs have massive context windows, their reasoning accuracy often degrades as noise increases. Semantic-Sift solves this by distilling technical logs, long-form documents, and chat histories into high-density context. It treats your context window as a precious resource—optimizing for **Signal-to-Noise Ratio (SNR)** so your models spend more time reasoning and less time navigating boilerplate.

### 🧠 Philosophy: The Studio of Two
Semantic-Sift is grounded in the **Studio of Two** philosophy: the belief that the future of engineering is a high-fidelity partnership between a human architect and a sovereign AI sidecar. By managing the friction of raw data ingestion, Sift allows this "Studio" to focus on building *systems*, not just applying *patches*. It acts as a cognitive filter that ensures both you and your agent are collaborating on the cleanest, most relevant representation of the technical truth.

---

## 🏛️ Multidisciplinary Value

Semantic-Sift is a strategic layer designed to manage attention across four key professional personas:

*   **For the Senior Engineer:** A local-first, low-latency middleware using a dual-engine approach (Heuristic Sieve + Neural Reranker). It refined timestamps, repetitive boilerplate, and redundant JSON before they hit the wire, reducing latency and preventing "Lost in the Middle" reasoning failures.
*   **For the Project Manager:** "Context Insurance." By reducing token overhead by 30-70%, Sift provides direct ROI on API costs and reduces the "retry loop" caused by model hallucinations in messy data environments.
*   **For the Researcher:** Data integrity at scale. Native **MarkItDown** integration converts complex `.pdf`, `.docx`, and `.xlsx` into structured, distilled Markdown, allowing for the rapid synthesis of massive technical repositories without losing critical semantic anchors.
*   **For the Knowledge Partner:** Cognitive Load Management. Sift manages the friction of raw data ingestion, allowing the human-AI partnership to focus on high-level strategy and architectural decisions rather than manual data triage.

---

## 💰 Value Engineering: Operational vs. Economic ROI

Semantic-Sift provides a dual-layer of value. While the economic benefits depend on your billing plan, the operational benefits apply to every professional workflow.

#### 1. The Economic ROI (Direct Savings)
*Target: Users on Per-Token API plans (GPT-4o, Claude 3.5).*
*   **Wallet Protection:** Sift acts as a local filter, typically reducing outgoing token volume by 30-70%. 
*   **Compound Interest:** In iterative agentic loops, these savings compound rapidly. Every character pruned is money that stays in your budget.

#### 2. The Operational ROI (Quality & Performance)
*Target: EVERYONE (including "Unlimited" or Per-Request subscription users).*
*   **Attention Precision:** Even with "infinite" context, LLMs suffer from "Lost in the Middle" syndrome. By removing noise, you ensure the model's full reasoning power is focused on the technical signal, resulting in higher-quality code and fewer hallucinations.
*   **Latency Reduction:** Smaller prompts = Faster "Time to First Token" (TTFT). You spend less time waiting for the "cloud" to process boilerplate and more time in your flow state.
*   **Context Insurance:** Prevents "Context length exceeded" errors on complex tasks. Sift ensures that 100% of your model's limit is filled with **information**, not formatting.

---

## 📚 Master Documentation Index

All technical details, architectural logic, and integration guides are strictly maintained in the `doc/` directory to prevent data loss through summarization.

*   **[doc/INDEX.md](doc/INDEX.md)**: The navigational roadmap and source of truth for the documentation structure.
*   **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)**: Specifications of the Sift Hook Interceptor, the Distillation Kernel (Heuristic/Semantic/Ranking engines), and Caching.
*   **[doc/TOOL_REFERENCE.md](doc/TOOL_REFERENCE.md)**: Exhaustive operator's manual for all FastMCP tools (e.g., `sift_read_file`, `sift_logs`, `sift_chat`, `sift_rank`).
*   **[doc/INTEGRATION_ENCYCLOPEDIA.md](doc/INTEGRATION_ENCYCLOPEDIA.md)**: Master Compatibility Map, Hook Injector logic, Payload Structures, and the **Master Configuration Matrix** for connecting IDEs (Cursor, Gemini, VS Code, OpenCode, etc.).
*   **[doc/TELEMETRY_SPEC.md](doc/TELEMETRY_SPEC.md)**: Design of the OpenTelemetry tracing, Echo-Detector (Double-Sifting Prevention), Audit Headers, and Privacy controls.
*   **[doc/ORCHESTRATION_BLUEPRINTS.md](doc/ORCHESTRATION_BLUEPRINTS.md)**: Actionable workflows for AI agents, including File Ingestion decision trees, Multi-Document RAG, and History Compaction.

---

## 🎯 High-Impact Use Cases

### 📚 The Knowledge Hunter (Researchers & Architects)
*   **The Pain**: Reading 50-page PDFs, complex Word specs, or cluttered documentation sites.
*   **The Sift**: Uses **MarkItDown** to natively ingest `.pdf`, `.docx`, and `.xlsx`. It converts corporate "noise" into structured Markdown, allowing your agent to synthesize multiple 14MB documents in a single turn.

### 🛠️ The Log Hunter (DevOps & SREs)
*   **The Pain**: Finding a single error in 100,000 lines of technical logs.
*   **The Sift**: The **Heuristic Sieve** refines timestamps and boilerplate in milliseconds. The **Subconscious Hook** automatically reranks results, so your agent only sees the most relevant data blocks.

### 🧠 The Context Strategist (AI Engineers)
*   **The Pain**: LLM hallucination and reasoning degradation caused by messy data streams.
*   **The Sift**: By delivering high-density context with 95% of the meaning preserved, Sift acts as a **Cognitive Bridge**. It ensures your LLM's attention is focused exclusively on the signal.

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/luismichio/semantic-sift.git
cd semantic-sift
py -3.12 -m venv venv312
.\venv312\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Or install as a package after cloning:
```bash
pip install .
```

For full semantic/reranking features, install neural extras:
```bash
pip install .[neural]
```

### 2. Connect the MCP

> **CRITICAL**: For exact configuration paths for Cursor, Gemini, OpenCode, VS Code, and Claude, reference the **[Master Configuration Matrix in the Integration Encyclopedia](doc/INTEGRATION_ENCYCLOPEDIA.md#5-master-configuration-matrix-mcp-server-installation)**.

### 3. Auto-Onboard
Once connected, ask your AI Assistant:
> *"Run `sift_onboard()` to configure this project."*

---

## 🤖 For AI Agents: Operational Protocol

If you are an AI Agent (e.g., Gemini CLI, Cursor, Claude Code) reading this repository, follow this protocol:

1. **Initialization**: Call `sift_onboard()` to register background hooks.
2. **Context Advisory**: Before reading large files (>1,000 chars), call `sift_analyze_file(path)` to determine the noise ratio.
3. **Mandatory Sifting**: If noise > 15%, pipe data through `sift_logs` or `sift_chat` before inclusion in reasoning.
4. **Ranking**: Use `sift_rank` to identify the most semantically relevant chunks for the user's prompt.

---

## 🛡️ Security & Testing

Semantic-Sift is built on a **Zero-Vulnerability Baseline**:
- **Pytest**: 100% pass rate on heuristic integrity.
- **Bandit (SAST)**: Automated static analysis for Python patterns.
- **Pip-Audit (SCA)**: Real-time supply chain monitoring for 0 known vulnerabilities.

Privacy and telemetry controls:
- Set `SIFT_TELEMETRY_DISABLED=true` to disable telemetry entirely.
- Set `SIFT_TELEMETRY_URL=https://your-endpoint` to route metadata pulses to your own endpoint.
- Set `SIFT_PULSE_RATE_LIMIT_S=10` (default) to control async telemetry pulse frequency.

Performance controls:
- Set `SIFT_HOOK_TIMEOUT_MS=3000` to cap hook semantic latency before heuristic fallback.
- Set `SIFT_MODEL_READY_WAIT_MS=1200` to control semantic model warm-up wait time before returning heuristic-mode output.

Hook logging controls:
- Set `SIFT_LOG_FILE` to override the hook log path (default: `.gemini/sift_debug.log`).
- Set `SIFT_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`) to control hook log verbosity.

See [SECURITY.md](SECURITY.md) for our full security policy.

Telemetry schema and endpoint details are documented in [doc/TELEMETRY.md](doc/TELEMETRY.md).

---

## ⚖️ Dual-License Model

1. **Personal Use (FREE)**: For individuals, researchers, and non-commercial development.
2. **Commercial Use (PAID)**: Required for corporate environments or commercial software embedding.

Obtain a license at [www.luiskobayashi.com](https://www.luiskobayashi.com).

## 📄 License
Source-Available. See `LICENSE.md` for details.
