# Semantic-Sift: Master Documentation Index

This document defines the decoupled structure of the Semantic-Sift documentation system. To prevent data loss through summarization and character limits, technical details are assigned to specialized specification files based strictly on the implemented codebase.

---

## 📂 Documentation Manifest & Content Intent

### 1. [`doc/INDEX.md`](INDEX.md)
*   **Intent**: Navigational roadmap and source of truth for the documentation structure.
*   **Topic Index**:
    *   Documentation Philosophy and File Manifest.
    *   Mapping of documentation files to implemented codebase modules.

### 2. [`doc/ARCHITECTURE.md`](ARCHITECTURE.md)
*   **Intent**: Technical specification of the system's core logic, interceptors, and processing pipelines.
*   **Topic Index**:
    *   **Sift Hook Interceptor (`sift_hook.py`)**: Hook event handling (`AfterTool`, `PreCompress`, `Compacting`), Subconscious Routing Intelligence (Auto-Ranking, Auto-Semantic, Auto-Heuristic), and exemptions for JSON Structured Data.
    *   **Distillation Kernel (`sift_kernel.py`)**: 
        *   Heuristic Engine: RegEx-based noise removal (timestamps, progress bars, module logs).
        *   Semantic Engine: Prompt compression via `microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`.
        *   Ranking Engine: Semantic re-ranking via `BAAI/bge-reranker-base`.
        *   Hybrid Pipelines: Document sifting, extraction cleaning, and compaction summaries (extracting `Decision`, `Status`, `File` markers).
    *   **Caching & Device Management**: Disk-persistent cache (`.sift_cache`) with SHA-256 keys, and lazy CPU/CUDA device detection.

### 3. [`doc/TOOL_REFERENCE.md`](TOOL_REFERENCE.md)
*   **Intent**: Exhaustive operator's manual for all FastMCP tools exposed in `server.py`.
*   **Topic Index**:
    *   **File Analysis & Reading**:
        *   `sift_read_file`: Bypasses standard reading for large files using targeted sifter types (`auto`, `logs`, `chat`, `doc`, `extraction`).
        *   `sift_analyze_file`: Calculates noise ratio and recommends sifting actions.
    *   **Content Distillation**:
        *   `sift_logs`: Cleans raw technical logs.
        *   `sift_chat`: LLMLingua-2 compression on natural language prose.
        *   `sift_doc`: Hybrid structural and semantic distillation for long documents.
        *   `sift_extraction`: Cleans OCR and PDF parsing artifacts.
    *   **Ranking & Utilities**:
        *   `sift_rank`: BGE-Reranker scoring for top-N document matches.
        *   `sift_analyze`: Context health report and noise ratio analysis for text.
    *   **System Operations**:
        *   `sift_onboard`: Configures workspace rules and native IDE hooks.
        *   `get_sift_stats`: Retrieves local telemetry and token savings.

### 4. [`doc/TELEMETRY_SPEC.md`](TELEMETRY_SPEC.md)
*   **Intent**: Technical design of data tracing, privacy controls, and the pulse system (`telemetry_core.py`).
*   **Topic Index**:
    *   **OpenTelemetry (OTel)**: Isolated `TracerProvider`, custom span attributes (`tool.name`, `platform`, `is_echo`, `sift.reduction_pct`, `file.path`), and `ConsoleSpanExporter`.
    *   **Echo Detector**: Disk-based caching (`.sift_cache/echo_*.tmp`) with 30s TTL to prevent duplicate content processing.
    *   **Audit Headers**: Configurable Markdown headers (`SIFT_AUDIT_HEADER`: `silent`, `minimal`, `full`) for logging reductions and execution latency.
    *   **Telemetry Pulse API**: Local logging (`.sift_telemetry.json`), global anonymous metric submission (`SIFT_TELEMETRY_URL` pointing to `luiskobayashi.com`), gated by the `SIFT_TELEMETRY_DISABLED` kill-switch, with anonymous transient pulses and timezone-aware timestamps.

### 5. [`doc/ORCHESTRATION_BLUEPRINTS.md`](ORCHESTRATION_BLUEPRINTS.md)
*   **Intent**: Workflow guides and recipes for maximizing the utility of Semantic-Sift tools.

### 6. [`doc/MCP_CONFIG_EXAMPLES.md`](MCP_CONFIG_EXAMPLES.md)
*   **Intent**: Ready-to-use configuration blocks for all major AI platforms.
*   **Topic Index**:
    *   **Decision Trees**: When to use `sift_read_file` vs standard reading based on `sift_analyze_file` output.
    *   **Context Optimization**: Managing context limits using `sift_rank` and targeted semantic compression.