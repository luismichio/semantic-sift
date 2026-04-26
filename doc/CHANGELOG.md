# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🛠️ Infrastructure & Maintenance
- **Encoding Correction**: Fixed corrupted `.gitignore` and `requirements.txt` files which contained mixed UTF-8 and UTF-16 encoding and non-printable characters.

### 🚀 Multi-Modal & HTML Intelligence
- **MarkItDown Integration**: Integrated Microsoft's `MarkItDown` as a structural pre-processor. Semantic-Sift now natively supports converting **PDF, DOCX, XLSX, and PPTX** to Markdown before sifting.
- **Subconscious HTML Normalization**: Upgraded the `sift_hook.py` interceptor to automatically detect HTML content (e.g., from web search results) and convert it to clean Markdown using MarkItDown before semantic compression.
- **Two-Stage Caching**: Implemented a secondary caching layer in `.sift_cache/` that stores the raw Markdown conversion (`raw_[hash].md`) independently of the sifted result, ensuring lightning-fast re-sifting at different rates.

### 🛰️ High-Fidelity Telemetry & Format Attribution
- **Format Tracking**: Extended the telemetry system and `log_telemetry` function to track the specific file format (e.g., `.pdf`, `.html`, `grep`) being processed.
- **Aggressive Tool Discovery**: Implemented a recursive tool name sniffing engine in `sift_hook.py` that scans for common MCP keys (`tool_name`, `tool`, `call`, etc.) and nested structures to minimize `unknown` telemetry entries.
- **Granular Intercept Attribution**: The "Subconscious Brain" now reports tool-specific ROI using the `{sift_type}:{original_tool_name}` naming convention (e.g., `sift_chat:fetch`), allowing for precise analysis of which external tools generate the most noise.
- **Supabase Compatibility**: Documented the backend requirements for the new `agent_label` and `file_ext` fields for high-fidelity ROI dashboards.

### 🤖 Multi-Agent & Subagent Shielding
- **Recursive Discovery**: Implemented a workspace crawler in `server.py` that automatically detects and shields specialized agent folders (`.codex/agents/`, `.cursor/agents/`, `.junie/agents/`) and scoped `AGENTS.md` mandates.
- **TOML Configuration Injector**: Added specialized support for **Codex CLI** subagents, safely merging the Sift Mandate into `.toml` definitions without breaking syntax.
- **Subagent Telemetry Tracking**: Extended the telemetry system and `sift_hook.py` to "sniff" for subagent identities (e.g., `$CLAUDE_AGENT_NAME`, `threadLabel`, worker prefixes) and attribute context savings to specific threads via a new `agent_label` field.

### 🛡️ Expanded Platform Hook Support
- **Smart Hooks (CLI Agents)**: Implemented native `PostToolUse` shell hook support for **Claude Code**, **Qwen CLI**, and **Codex CLI**, including platform-specific environment variable parsing in `sift_hook.py`.
- **Security Gateways (Inhibitors)**: Added proactive blocking hooks for **Windsurf** and **Cline** that intercept and terminate native file readers (`read_file`, `view_file`) for files > 1KB, forcing adoption of semantic sifting.
- **Dynamic Platform Identification**: Refactored the telemetry layer to dynamically override `client_id` based on the detected IDE/extension platform, providing high-fidelity "Global Pulse" metrics.
- **Native OpenClaw Plugin**: Developed a native TypeScript plugin for **OpenClaw** that hooks into `api.on("tool:after")` for transparent context sanitation.
- **JetBrains Junie Integration**: Added automated configuration discovery for both **Junie CLI** and the **JetBrains AI Assistant** in `server.py`.

### 🤝 Universal Orchestration
- **MCP Synergy Matrix**: Integrated a detailed synergy matrix into the `sift_onboard` mandate, providing agents with explicit recipes for handling Web/HTML, Cloud Logs, and Database data.
- **Official Documentation Index**: Updated the `IDE_MCP_INTEGRATION_WIKI.md` with verified official documentation URLs for 12+ supported environments to serve as a technical reference point.

### 🛰️ Guaranteed Telemetry & Efficacy
- **OpenTelemetry Tracing**: Integrated OTel with an isolated TracerProvider to provide a traceable "Chain of Custody" for data without interfering with host applications (like Gemini CLI).
- **Visual Audit Header**: Added a customizable dynamic header (`SIFT_AUDIT_HEADER`) that prepends live ROI stats (Reduction %, Latency, Echo Status) to every sifting result.
- **Cross-Process Echo Detector**: Implemented a disk-persistent SHA-256 hash cache in `.sift_cache` to detect and bypass redundant sifting calls across separate processes (Hooks vs Server).

### 🚀 Zero-Gap Path-Native I/O
- **Path-Native Tools**: Added `sift_read_file(path)` and `sift_analyze_file(path)` to allow agents to read and sift local files directly on the server without polluting their active context windows.
- **Content-Signature Bypass**: Secured the `sift_hook.py` middleware against Double-Sifting loops in "Blind Hook" IDEs (Cursor, VS Code) by injecting and detecting the `[Semantic-Sift: Native Execution]` signature.
- **Structured Data Exemption**: Prevented `sift_hook.py` from corrupting JSON payloads from other tools (like `mcp_serena_find_symbol`) by detecting and bypassing valid dict/list structures.
- **Encoding Resilience**: Added `load_file_content` to `sift_kernel.py` with automatic `utf-8` to `latin-1` fallbacks to handle massive, non-standard system logs without crashing.
- **Proactive Mandate**: Rewrote the `AGENTS.md` and `sift_onboard` rules to explicitly forbid the use of standard IDE reading tools for files over 1KB in Unshielded environments.

### 🚀 Tier 2: Structural Distillation
- **Compaction Hooks**: Implemented native support for OpenCode `experimental.session.compacting` hook, allowing Semantic-Sift to provide a high-fidelity "State Snapshot" during structural context loss.
- **Compression Telemetry**: Registered the `PreCompress` hook for Gemini CLI to track structural distillation ROI and monitor context lifecycle events.
- **Smart Summarizer**: Added `perform_compaction_summary` to `sift_kernel.py` to intelligently prioritize task status, decisions, and active files when summarizing session history.

### Added
- **Unified Telemetry Naming**: Removed all `hook_` prefixes to standardize events as `sift_logs`, `sift_chat`, and `sift_rank` regardless of trigger source.
- **Sift Kernel Extraction**: Refactored core sifting and ranking logic into a standalone `sift_kernel.py` to enable decoupled testing and high-performance background execution.
- **High-Fidelity Tool Instructions**: Rewrote MCP tool metadata in `server.py` with verbose, instruction-heavy descriptions to improve autonomous agent decision-making.
- **Native OpenCode Plugin**: Migrated from legacy shell hooks to a first-class TypeScript plugin (`.opencode/plugins/semantic-sift.ts`) for near-zero latency interception in OpenCode environments.
- **Solid Pulse Global Registry**: Implemented a redundant, high-reliability telemetry pulse system reporting to `https://www.luiskobayashi.com/api/sift`.
- **High-Fidelity Token Metrics**: Upgraded telemetry to report both character and **Estimated Token** (4:1 heuristic) ROI, providing real-world financial and context-window analytics.
- **Benchmark Visual Proof**: The benchmark script now saves visible `_sifted.txt` result files in `benchmarks/results/` for side-by-side comparison. Updated `doc/BENCHMARKS.md` with visual "Before & After" examples.
- **High-Volume & Legacy Support**: Hardened the heuristic sieve with regex support for legacy `YYMMDD` timestamps and enterprise-scale system logs (HDFS, Linux), enabling 70,000+ token sifts.
- **Standardized Benchmark Lab**: Replaced simulated data with a visible, replicable suite of real-world "Context Monsters" in `benchmarks/data/`, including authentic failing Vercel build logs and Git merge conflicts.
- **Privacy Kill-Switch**: Added the `SIFT_TELEMETRY_DISABLED=true` flag for absolute local sovereignty and Meechi-policy compliance.
- **Cybersecurity Tier**: Implemented a comprehensive automated audit suite (`scripts/audit.bat`) including:
    - **Pytest**: 100% logic and privacy coverage.
    - **Bandit (SAST)**: Automated static analysis with protocol enforcement (B310).
    - **Pip-Audit (SCA)**: Supply chain monitoring with 25+ vulnerabilities successfully remediated.
- **Subconscious Telemetry**: Integrated the universal hook interceptor (`sift_hook.py`) with the telemetry tier, allowing background sifting events to be tracked as `hook_sift_logs`.
- **Environment Awareness**: Upgraded `sift_analyze` to detect host-level truncation/masking (e.g. Gemini CLI's `<tool_output_masked>`) and recommend mandatory sifting of the raw source files.
- **Adaptive Thresholds**: Lowered the Auto-Sift Mandate trigger to 1,000 characters (from 2,000) to more effectively capture dense technical noise.
- **Multi-Target Injection**: Refactored the onboarding system to automatically sync rules across all detected IDE instruction files (`.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`, etc.).
- **Heuristic Orchestration**: Refactored `sift_orchestrate` to use keyword-based heuristic matching, allowing it to identify tool categories (e.g., `mcp-server-postgres` matches `postgres`).
- **Expanded Synergies**: Added 15+ new specialized collaboration rules for **Slack**, **Notion**, **AWS**, **Postgres**, **Puppeteer**, **Jira**, **Linear**, and more.
- **Super-Agnostic Orchestration**: Upgraded `sift_orchestrate` to automatically discover tools from **Continue**, **Zed**, **GitHub Copilot**, **OpenCode**, and **Antigravity** across Windows and macOS.
- **Custom Configuration**: `sift_orchestrate` now accepts `custom_tools` and `custom_paths` for tailored environment discovery.
- **Intelligence Tier**: New `sift_rank` tool using **BGE-Reranker** (`BAAI/bge-reranker-base`) to prioritize the most relevant text chunks from multiple documents before sifting.
- **Persistent Semantic Cache**: Implemented a local disk cache (`.sift_cache/`) that stores sifting results. Repeat calls for the same text and parameters now have near-zero latency (~1ms).
- **Context Advisory**: New `sift_analyze` tool that evaluates context quality (SNR) and recommends appropriate sifting actions based on noise heuristics and document length.
- **Automated Onboarding**: New `sift_onboard` tool that automatically injects Semantic-Sift usage guidelines into project instruction files (`AGENTS.md`, `.clinerules`, etc.) and provides an environment diagnostic report.
- **GPU Acceleration**: Migrated to Python 3.12 environment (`venv312`) to enable CUDA 12.1 support for RTX 2070 Super.
- **Device-Aware Resilience**: Added automatic torch device detection (CUDA/CPU) to prevent crashes when GPU support is missing.
- **Telemetry Tier**: Implemented a persistent telemetry system (`.sift_telemetry.json`) that tracks compression ratios, character savings, and processing latency across sessions.
- **get_sift_stats**: New MCP tool to query session-based or global performance metrics.
- **MCP Configuration**: Integrated `context-mode`, `serena`, and `github` MCP servers into the workspace via `.gemini/settings.json`.
- **Serena Project Configuration**: Added `.serena/project.yml` and `.serena/project.local.yml` for local agent orchestration.
- **Agent Guidelines**: Created `AGENTS.md` to define project-specific standards and philosophy.

## [1.0.0] - 2026-04-13

### Added
- **Initial Release**: The birth of the "Sanitation Tier" for agentic workflows.
- **Server Core**: Implemented as a standalone Python FastMCP server.
- **The Sieve**: Heuristic regex-based log distillation (`sift_logs`).
- **The Sift**: Semantic BERT-based natural language pruning (`sift_chat`).
- **Hybrid Sift**: Multi-stage distillation for long documentation (`sift_doc`).
- **RAG Refinery**: OCR/PDF artifact cleaning for LlamaIndex synergy (`sift_extraction`).

### Fixed
- Corrected Hugging Face model identifier for LLMLingua-2 from `-instruct` to `-meetingbank`.

### Security
- **Local Sovereignty**: All processing is performed locally; no data is sent to external APIs for compression.
