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
- **Operation**: Aggregates metrics from `.sift_telemetry.json` for either the `current` session or `all` historical sessions.
- **Benefit**: Provides transparency into the "incineration" rate of noise and tracks processing overhead.

### `sift_onboard()`
- **Category**: Automation & Setup
- **Best For**: Initial installation and environment verification.
- **Operation**: Scans for agent instruction files and injects the Semantic-Sift SOPs. Provides a diagnostic report of Python/CUDA/GPU status.
- **Benefit**: Ensures every repository is "Sift-Aware" with zero manual effort.

### `sift_analyze(text)`
- **Category**: Context Advisory
- **Best For**: Deciding whether or not a body of text needs sifting.
- **Operation**: Uses heuristic regex to detect timestamps, UUIDs, and repetition. Formulates a recommendation based on noise density and length.
- **Benefit**: Prevents redundant sifting and helps the agent manage its own context window autonomously.

### `sift_rank(query, documents)`
- **Category**: Intelligence Tier
- **Best For**: Multi-document RAG retrieval.
- **Operation**: Uses a local BGE-Reranker model (`BAAI/bge-reranker-base`) to score documents against a query. Returns top-N results.
- **Benefit**: Ensures the most relevant information is prioritized before the sifting/compression stage.

### `sift_orchestrate(custom_tools, custom_paths)`
- **Category**: Universal Orchestration
- **Best For**: Cross-IDE and multi-agent collaboration.
- **Operation**: Performs deep discovery across local (`.gemini`) and global config files (**Claude, Zed, Continue, Copilot, Antigravity, OpenCode**). 
- **Heuristic Matching**: Uses a **Keyword-based Heuristic Engine** to identify tool categories (e.g., Slack, AWS, SQL) and injects specific "Chain of Context" rules.
- **Benefit**: Transforms a fragmented toolset into a unified, high-SNR intelligence system.

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

## 🚀 Deployment Models

### 1. Developer Mode (Current)
Running as a standalone process on the developer machine.
`python server.py`

### 2. The Sidecar (Target)
Frozen into a standalone binary via **PyInstaller/Nuitka** and bundled inside the **Meechi (Tauri) App**.
- **Path**: `src-tauri/binaries/semantic-sift-[platform]`
- **Activation**: Auto-boot on application start via the Tauri Command API.

---

## 🔒 Security & Privacy
- **Local Sovereignty**: All sifting occurs on the local machine. No data is sent to external APIs for compression.
- **Local Model weights**: Models are cached locally in the user's home directory.

---

## 🌟 Future Roadmap
- **WebGPU Port**: Transitioning from PyTorch to `llmlingua-2-js` (ONNX) for browser-native execution.
- **Docling Integration**: Tiered PDF parsing that sifts documents before they ground the agent.
