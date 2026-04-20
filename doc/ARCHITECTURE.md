# Semantic-Sift: Architecture & Philosophy

## 🧠 Core Philosophy
Semantic-Sift is built on the **"Studio of Two"** principle: We build **Systems, not Patches**. 

In the modern agentic workspace, the primary bottleneck is not processing power, but **Signal-to-Noise Ratio (SNR)** within the LLM's context window. Semantic-Sift acts as a high-fidelity "Sanitation Tier" that ensures the agent only "sees" the meaningful essence of data.

---

## 🏗️ Architectural Overview

Semantic-Sift is a standalone, protocol-compliant **MCP (Model Context Protocol) Server** written in Python. It provides a hybrid approach to data reduction:

### 1. The Sieve (Structural Distillation)
- **Mechanism**: Rule-based heuristic filtering (Regex).
- **Target**: Technical logs (Vercel, GitHub, Console), build outputs, and boilerplate-heavy data.
- **Logic**: 
    - Removes ephemeral noise (Timestamps, UUIDs, Session IDs).
    - Collapses repetitive patterns (Progress bars, "Building..." lines).
    - Strips low-entropy technical metadata.
- **Goal**: ~40-60% reduction with zero semantic risk and near-zero latency.

### 2. The Sift (Semantic Compression)
- **Mechanism**: Model-based compression using **LLMLingua-2** (Prompt Compression).
- **Target**: Natural language conversation logs, long MDX pages, and PDF transcripts.
- **Logic**: Uses a lightweight BERT-based model (`microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`) to calculate token importance. It removes linguistic filler while preserving instruction-carrying tokens and core semantic entities.
- **Goal**: ~20-80% reduction (configurable) while maintaining the 95%+ fidelity of the original meaning.

### 3. Subconscious Sifting (Interceptor Layer)
- **Mechanism**: Universal JSON-based hook interceptor (`sift_hook.py`).
- **Protocol Detection**: Identifies JSON schemas from Gemini CLI (`AfterTool`), Cursor (`postToolUse`), and VS Code (`PostToolUse`).
- **Logic**: Intercepts tool outputs in the background and applies heuristic sifting *before* data enters the agent's context.
- **Benefit**: Ensures zero-latency context hygiene without requiring explicit agent decision-making.

### 4. The "Solid Pulse" Telemetry System
Designed for high-reliability "Proof of Value" tracking across distributed installations.

- **Lightweight Core**: `telemetry_core.py` provides zero-dependency metrics tracking.
- **High-Fidelity Metrics**: Tracks both characters and **Estimated Tokens** (4:1 heuristic) to provide accurate ROI analytics.
- **Redirect Resilience**: Automatically detects and retries canonical URLs (handling HTTP 308 redirects to `www.`).
- **Short-Lived Execution**: In CLI/Hook environments, telemetry pulses are blocking to ensure data delivery before process termination, while maintaining sub-50ms latency.
- **Global Transparency**: Aggregates anonymous savings into a centralized registry for community "Proof of Value."

---

## 🛡️ Privacy & Sovereignty Architecture

Semantic-Sift is built on a **"Local-First, Metadata-Only"** philosophy.

### 1. Data Isolation
No raw text, code, or prompts are ever transmitted outside the local machine. All sifting (BERT, Regex) happens on the local CPU/GPU.

### 2. Anonymous Identity
Each installation generates a persistent, anonymous UUID in `.sift_identity`. This ID is used only for aggregate "Saved Token" counters and contains zero personal information.

### 3. The Privacy Kill-Switch
For users with absolute non-tracking requirements (e.g., **Meechi** users), the engine supports the `SIFT_TELEMETRY_DISABLED=true` flag.
- **Total Silence**: When active, the telemetry module returns immediately.
- **Zero Disk I/O**: No local `.sift_telemetry.json` is created.
- **Zero Network Pulse**: No HTTP requests are attempted.

---

## 🔄 The Refinery Loop (RAG Synergy)

Semantic-Sift is designed to sit between **Extraction** (Docling/LiteParse) and **Grounding** (LlamaIndex/Meechi Core). This creates a high-density information loop:

1. **Extraction**: Raw PDF/HTML is converted to Markdown via Docling.
2. **Refinery (Semantic-Sift)**: 
    - The `sift_extraction` tool strips repeating footers, metadata noise, and linguistic filler.
    - Markdown structure (Tables, Headers) is preserved via protected tokens.
3. **Grounding**: The "Sifted" Markdown is indexed by LlamaIndex.

### Benefits of the Refinery Loop:
- **Clean Embeddings**: Vector models only see pure semantic signal, reducing retrieval hallucinations.
- **Context Density**: ~30% more information can be packed into each RAG retrieved chunk.
- **Cost Reduction**: Lower token usage during both ingestion and query phases.

---

## 🛠️ Tool Reference

### `sift_logs(raw_text)`
- **Category**: Structural Sieve
- **Best For**: Vercel/GitHub build logs, terminal outputs, and repetitive CLI data.
- **Operation**: Strips ISO timestamps, collapses progress bars, and filters out boilerplate module/file listings.
- **Benefit**: Near-instant cleanup of "log-bloat" for fast debugging analysis.

### `sift_chat(text, rate)`
- **Category**: Semantic Sift
- **Best For**: Conversation history, meeting transcripts, and natural language instructions.
- **Operation**: Powered by LLMLingua-2 (BERT) to identify instructional signal and prune linguistic filler.
- **Benefit**: Reduces the token-load of long conversation logs while preserving 95%+ of the core meaning.

### `sift_doc(text, budget_tokens)`
- **Category**: Hybrid Signal Extractor
- **Best For**: Large PDFs, MDX articles, and long-form research.
- **Operation**: A multi-stage process that first structural-distills noise and then semantically-compresses the remaining prose.
- **Benefit**: Allows the agent to "see" entire documents in a high-density format that fits comfortably in a standard context window.

### `sift_extraction(content, source_type)`
- **Category**: RAG Refinery
- **Best For**: Outputs from Docling, LiteParse, or other OCR/PDF extractors.
- **Operation**: Specifically tuned to prune OCR artifacts and metadata debris while protecting Markdown structure (tables, headers) and technical entities.
- **Benefit**: Transforms "noisy" raw extractions into "lean" signal for high-accuracy LlamaIndex grounding.

### `get_sift_stats(scope)`
- **Category**: Telemetry Tier
- **Best For**: Monitoring efficiency and quantifying token savings.
- **Operation**: Aggregates metrics from `.sift_telemetry.json` for either the `current` session or `all` historical sessions. Tracks both manual calls and background hooks (`hook_sift_logs`).
- **Benefit**: Provides transparency into the "incineration" rate of noise and tracks processing overhead.

### `sift_onboard(target_dir)`
- **Category**: Automation & Setup
- **Best For**: Initial installation and environment verification across multiple repositories.
- **Operation**: Scans for agent instruction files and injects the Semantic-Sift SOPs. Provides a diagnostic report of Python/CUDA/GPU status.
- **Benefit**: Ensures every repository is "Sift-Aware" with zero manual effort.

### `sift_analyze(text)`
- **Category**: Context Advisory
- **Best For**: Deciding whether or not a body of text needs sifting.
- **Operation**: Uses heuristic regex to detect timestamps, UUIDs, and host-level truncation (Gemini CLI). Formulates a recommendation based on noise density and environment awareness.
- **Benefit**: Prevents redundant sifting and helps the agent manage its own context window autonomously.

### `sift_rank(query, documents)`
- **Category**: Intelligence Tier
- **Best For**: Multi-document RAG retrieval.
- **Operation**: Uses a local BGE-Reranker model (`BAAI/bge-reranker-base`) to score documents against a query. Returns top-N results.
- **Benefit**: Ensures the most relevant information is prioritized before the sifting/compression stage.

### `sift_orchestrate(custom_tools, custom_paths, target_dir)`
- **Category**: Universal Orchestration
- **Best For**: Cross-IDE and multi-agent collaboration.
- **Operation**: Performs deep discovery across local and global config files (Claude, Zed, Continue, etc.). Injects tool-specific or category-based "Chain of Context" rules.
- **Benefit**: Transforms a fragmented toolset into a unified, high-SNR intelligence system.

## 🤝 Collaboration Blueprints

The orchestrator maps discovered tools to specific high-fidelity workflows. Below are the primary blueprints currently active in the engine:

| Category | Targeted Tools | Orchestration Pattern |
| :--- | :--- | :--- |
| **Discovery** | Serena, Investigator | **Discovery -> Sifting**: Prunes boilerplate from code bodies immediately after retrieval. |
| **Storage** | Context-Mode, Memory | **Sifting -> Storage**: Ensures context databases are only indexed with high-signal "lean" data. |
| **Cloud Infra** | AWS, GCP, Azure | **Metadata Distillation**: Strips redundant JSON fields (ETags, IDs) from cloud resource snapshots. |
| **Communication** | Slack, Discord | **History Compaction**: Filters out conversational filler and system events from chat logs. |
| **Data** | Postgres, SQL, SQLite | **Sample Pruning**: Keeps the schema and relevant rows while pruning massive result sets. |
| **Browsing** | Puppeteer, Playwright | **Web Cleaning**: Removes navigation, footers, and tracking noise from raw HTML extractions. |

### Universal Fallback Strategy
If no specific tools are recognized, the engine injects a set of **Category-Based Agnostic Rules**. These teach the agent how to categorize its own tools (e.g., "If you find a tool that fetches the web, run `sift_extraction` first") ensuring that even proprietary or niche MCPs benefit from the sifting pipeline.

---

## 🛠️ Technical Stack

- **Kernel**: Python 3.12 (Optimized for CUDA stability).
- **Communication**: FastMCP (Standardized I/O for AI Agents).
- **AI Core**: PyTorch + Hugging Face Transformers.
- **Models**: 
    - **LLMLingua-2**: Semantic Compression.
    - **BGE-Reranker**: Relevance ranking.
- **Orchestration**: Agnostic Path Discovery + Heuristic Keyword Synergy.
- **Caching**: Local SHA-256 persistent disk cache for instantaneous repeat sifts.

---

## 💰 Economic & Operational Impact

Semantic-Sift is designed to be "Agnostic to the Bill." Its value scales regardless of the provider's pricing model:

### 1. Token-Based Efficiency
For providers like OpenAI or Google (Gemini API), the ROI is linear. By maintaining a high compression ratio, Sift directly reduces the monthly spend on agentic workflows.

### 2. Request-Based Reliability
For tools with flat-fee per-request billing, Sift shifts the focus from **Cost** to **Quality**:
- **Focus Guard**: Prevents "Signal Dilution" where models ignore crucial data due to surrounding noise.
- **Fail-Safe Capacity**: Ensures that complex contexts (History + RAG + Logs) stay within the model's hard window limit, preventing wasted requests.
- **Latency Optimization**: Compressing data locally before transmission reduces server-side pre-fill time, resulting in a faster perceived UX.

---

## 🚀 Deployment Models

### 1. Developer Mode (Current)
Running as a standalone process on the developer machine.
`python server.py`

### 2. The Sidecar (Target)
Frozen into a standalone binary via **PyInstaller/Nuitka** and bundled inside the **Meechi (Tauri) App**.
- **Path**: `src-tauri/binaries/semantic-sift-[platform]`
- **Activation**: Auto-boot on application start via the Tauri Command API.

## 🌟 Future Roadmap
- **WebGPU Port**: Transitioning from PyTorch to `llmlingua-2-js` (ONNX) for browser-native execution.
- **Docling Integration**: Tiered PDF parsing that sifts documents before they ground the agent.
