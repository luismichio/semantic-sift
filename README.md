# 🔍 Semantic-Sift

**The Reasoning-First Middleware for High-Fidelity Agentic Workflows.**

[![CI](https://github.com/luismichio/semantic-sift/actions/workflows/ci.yml/badge.svg)](https://github.com/luismichio/semantic-sift/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-84%20Passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-measured-blue)](https://github.com/luismichio/semantic-sift/actions)
[![PyPI](https://img.shields.io/pypi/v/semantic-sift)](https://pypi.org/project/semantic-sift/)
[![Python](https://img.shields.io/pypi/pyversions/semantic-sift)](https://pypi.org/project/semantic-sift/)
[![Security](https://img.shields.io/badge/Security-Bandit%20Inspected-brightgreen)](SECURITY.md)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue)](LICENSE.md)
[![OSI](https://img.shields.io/badge/OSI-Approved-brightgreen)](https://opensource.org/licenses/Apache-2.0)

> **"It saves tokens while preserving context - maximizing reasoning, minimizing hallucination."**

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
Clone the repository and install:
```bash
git clone https://github.com/luismichio/semantic-sift.git
cd semantic-sift
pip install .
```

For full semantic/reranking features (LLMLingua, Transformers, sentence-transformers):
```bash
pip install .[neural]
```

> **Note on Orchestration:** Semantic-Sift is an "Intelligence Kernel." For complex multi-tool workflows, we strongly recommend installing [Context-Pipe](https://github.com/luismichio/context-pipe), the universal switchboard that natively routes data to Semantic-Sift without blocking your IDE.

For development tools (mypy, pytest):
```bash
pip install .[dev]
```

### 2. Connect the MCP

> **CRITICAL**: For exact configuration paths for Cursor, Gemini, OpenCode, VS Code, and Claude, reference the **[Master Configuration Matrix in the Context-Pipe Documentation](https://github.com/luismichio/context-pipe/blob/main/doc/INTEGRATION_ENCYCLOPEDIA.md#5-master-configuration-matrix-mcp-server-installation)**.

### 3. Auto-Onboard
Once connected, ask your AI Assistant:
> *"Run `sift_onboard()` to configure this project."*

---

## 📊 Telemetry & Management Commands

Semantic-Sift operates invisibly, but you can always audit its performance and token savings without burning LLM tokens to do so.

*   **Terminal CLI**: 
    *   Run `semantic-sift-stats` to print a global dashboard of your token savings, latency, and cache hits.
    *   Run `semantic-sift-onboard` to manually initialize Sift in any project (supports `--env` and `--dry-run`).
*   **MCP Prompts**: Compatible clients (Claude Desktop, Cursor, Zed) will surface a `sift_dashboard` prompt in their UI (often via a slash command or button) to instantly inject your telemetry stats into the chat.
*   **OpenCode & Gemini CLI**: The `sift_onboard()` tool automatically injects native `/sift-stats` and `/sift-onboard` custom slash commands into your IDE configuration.

---

## 🦀 Native Rust Sidecar (Meechi & Desktop Apps)

For high-performance, local-first applications (like [Meechi](https://meechi.me)), Semantic-Sift provides a native Rust binary (`sift-core`). This sidecar is optimized for portability and speed, with zero Python dependencies.

### 🔀 The Hybrid Engine (`semantic-sift-cli`)
To provide the best of both worlds, installing the Python package also exposes the `semantic-sift-cli` command. This acts as an **Intelligent Router**:
- For **short tasks** (<30,000 chars), it instantly shells out to the low-latency Rust `sift-core` (ONNX).
- For **massive batch tasks**, it dynamically loads the high-throughput PyTorch framework with Flash Attention to prevent memory explosion.

### Feature Comparison

| Feature | Python MCP Server | Rust Sift-Core (Sidecar) |
| :--- | :---: | :---: |
| **Heuristic Log Sifting** | ✅ | ✅ (Native) |
| **Semantic Compression** | ✅ (PyTorch) | ✅ (ONNX) |
| **Multi-Modal Ingestion** | ✅ (**MarkItDown**) | ❌ (Text Only) |
| **Supported Formats** | .pdf, .xlsx, .docx, .html, .txt | .txt, .log, .out (Text) |
| **Startup Latency** | 3-5 seconds | **~10ms** |
| **Binary Size** | ~1.5GB (bundled) | **~15MB** |

> **Note**: For native apps like Meechi, we recommend a **Tiered Ingestion** strategy: use the app's frontend (e.g., `pdf.js`) to extract text, then pipe it to the Rust sidecar for high-speed semantic sifting.

**[✨ View Native Sidecar Demo](./demo/)**

**Usage:**
```bash
# Sift a log file instantly
cat app.log | sift-core logs

# Perform neural semantic compression
cat document.txt | sift-core semantic --model ./models/llmlingua2 --rate 0.4
```

---

## 🤖 For AI Agents: Operational Protocol

If you are an AI Agent (e.g., Gemini CLI, Cursor, Claude Code) reading this repository, follow this protocol:

1. **Initialization**: Call `sift_onboard()` to register background hooks. Use `sift_onboard(dry_run=True)` to preview all planned actions without writing any files.
2. **Context Advisory**: Before reading large files (>1,000 chars), call `sift_analyze_file(path)` to determine the noise ratio.
3. **Mandatory Sifting**: If noise > 15%, pipe data through `sift_logs` or `sift_chat` before inclusion in reasoning. For documents, use `sift_doc(text, rate=0.4)` — adjust `rate` (0.1–0.9) to trade compression depth against fidelity.
4. **Ranking**: Use `sift_rank` to identify the most semantically relevant chunks for the user's prompt.
5. **Extraction**: When distilling PDFs or scraped content, use `sift_extraction(content, show_diff=True)` to see exactly what was removed and verify faithfulness.

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

Security controls:
- Set `SIFT_ALLOW_GLOBAL_READS=true` to permit `sift_read_file` / `sift_analyze_file` outside the workspace root (path traversal guard is on by default).

Performance controls:
- Set `SIFT_HOOK_TIMEOUT_MS=3000` to cap hook semantic latency before heuristic fallback.
- Set `SIFT_MODEL_READY_WAIT_MS=1200` to control semantic model warm-up wait time before returning heuristic-mode output.
- Set `SIFT_COMPACTION_FIDELITY_THRESHOLD=0.3` (default) to control the vocabulary-overlap threshold below which a low-fidelity compaction warning is emitted.

Hook logging controls:
- Set `SIFT_LOG_FILE` to override the hook log path (default: `.gemini/sift_debug.log`).
- Set `SIFT_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`) to control hook log verbosity.

See [SECURITY.md](SECURITY.md) for our full security policy.

Telemetry schema and endpoint details are documented in [doc/TELEMETRY_SPEC.md](doc/TELEMETRY_SPEC.md).

---

## License

Apache License 2.0. See [LICENSE.md](LICENSE.md) for details.

## Contributing

**Semantic-Sift is Open Source, but Closed to Contributions.**

To maintain the strict architectural vision of the "Studio of Two" and keep maintenance overhead at absolute zero, this repository does not accept external pull requests. We encourage you to use, embed, and fork the code under the permissive Apache 2.0 license, but please do not submit PRs for new features or bug fixes. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
