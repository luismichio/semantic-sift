# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-04-29

### 🏗️ Infrastructure & CI/CD
- **GitHub Actions CI**: Added `.github/workflows/ci.yml` — matrix build on Python 3.10/3.11/3.13; runs ruff → mypy → pytest with coverage on every push/PR to `main`.
- **Automated Release Workflow**: Added `.github/workflows/release.yml` — gates on full quality pipeline, builds distribution, publishes to PyPI via OIDC trusted publishing, creates GitHub Release with CHANGELOG section as release notes.
- **Dev Dependencies**: Added `pytest`, `pytest-cov`, `ruff`, `mypy` to `[dev]` optional extra in `pyproject.toml`.
- **Ruff & Coverage Config**: Added `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.coverage.run]`, `[tool.coverage.report]` sections to `pyproject.toml`.

### 🧹 Code Quality
- **22 Ruff Violations Fixed**: 10 auto-fixed; 12 manual — `E701` multi-statement lines in `sift_hook.py`, `sift_kernel.py`, `telemetry_core.py`; `E741` ambiguous `l` variable renamed `lat` in `tools.py`; `F541` f-string without placeholder in `benchmark_sift.py`.
- **mypy Clean**: Zero type errors across all modules.

### 🧪 Test Coverage
- **Hook Integration Tests** (`tests/test_hook_integration.py`): 12 new tests covering all platform detection paths (Claude, OpenCode, Gemini, Cursor, VSCode) + bypass, pass-through, and sifting-reduction assertions.
- **MCP Tool Tests** (`tests/test_server_tools.py`): Expanded from 3 to 11 tests — added `sift_logs`, `sift_chat`, `sift_doc`, `sift_extraction`, `sift_rank`, full `get_sift_stats` table, and `sift_onboard` None-environment guard.
- **Hook Injector Smoke Tests** (`tests/test_hook_injector.py`): 18 new tests covering `build_runtime_hook_command`, `merge_hook_json` (create/idempotent/append), `update_toml_config` (inject/replace/idempotent), `discover_agent_configs`, and `update_instruction_files` for Cursor, VS Code, OpenCode, unknown IDE.
- **Total: 84 passing tests** (up from 46).

### 📋 Legal & Community
- **CONTRIBUTING.md**: Added at repo root with CLA notice, dev setup, test commands, code style rules, platform-addition guide, and PR checklist.
- **SECURITY.md**: Confirmed at repo root (GitHub-discoverable).

### 🏷️ README Badges
- Replaced static badge row with CI, Tests, Coverage, PyPI version, Python versions, Security, and License badges.

### 🐛 Bug Fixes
- **Client ID Always `"Generic CLI"` for MCP Tools**: `telemetry_core.SIFT_CLIENT_ID` was resolved once at module load from `os.environ.get("SIFT_CLIENT_ID", "Generic CLI")`. No IDE sets that env var, so every `sift_chat`, `sift_doc`, `sift_logs`, etc. call logged as `"Generic CLI"`, making per-IDE analytics blind. Added `detect_client_id()` in `telemetry_core.py` that resolves the client via (1) `SIFT_CLIENT_ID` env var, (2) known IDE env var fingerprints, (3) parent-process name via `psutil` (optional), (4) `"Generic CLI"` fallback. `SIFT_CLIENT_ID` is now set from this function at module load. `semantic_sift/tools.py` now passes `client_id_override=CLIENT_ID` to all 8 `log_telemetry` calls. The `Compacting` event in `sift_hook.py` was also missing `client_id_override=platform` — fixed.
- **OpenCode Platform Detection**: Fixed `sift_hook.py` incorrectly classifying OpenCode tool calls as `Gemini` in telemetry. Both platforms emit `hook_event_name: "AfterTool"`, but the OpenCode native plugin always includes a top-level `tool_args` key which Gemini never sends. The `AfterTool` branch now checks for `tool_args` first and routes to `OpenCode`; payloads without it fall through to the existing Gemini path. Two regression tests added in `tests/test_hook_routing.py`.
- **Telemetry Secret-Type Metadata Leakage**: `telemetry_core.py` was logging type-specific redaction labels (`[REDACTED_GITHUB_PAT]`, `[REDACTED_OPENAI_KEY]`, `[REDACTED_SLACK_TOKEN]`) into `.sift_telemetry.json` and remote pulses. Even though the raw secret was masked, the label itself reveals secret type, which tool surfaces it, and frequency. Added `redact_secrets_for_telemetry()` which normalises all labels to a generic `[REDACTED]`. The descriptive labels are preserved in local debug logs (`sift_hook.py`) where the operator owns the output.

### 🛠️ Runtime Portability & Safety Hardening
- **Runtime Hook Command**: Removed hardcoded local interpreter and script paths from `server.py`; hook commands are now derived from `sys.executable` and `server.py`-relative `sift_hook.py` at runtime.
- **Startup Validation**: Added explicit startup guard that fails fast with a clear error when `sift_hook.py` is not found next to `server.py`.
- **Workspace Path Guard**: Added `resolve_safe_path(...)` in `sift_kernel.py` and integrated it into `sift_read_file` and `sift_analyze_file` to block out-of-workspace path traversal by default.
- **Controlled Override**: Added `SIFT_ALLOW_GLOBAL_READS=true` environment override for advanced workflows that intentionally read files outside the workspace.
- **Packaging Bootstrap**: Added `pyproject.toml` with a `semantic-sift` console entry point and updated quick-start docs with package install instructions.
- **Windsurf Windows Gateway**: Replaced Linux-only Windsurf file-size guard command with platform-aware command generation that supports Windows (`pwsh`) and POSIX shells.
- **Security Policy Expansion**: Rewrote `SECURITY.md` with concrete telemetry schema, privacy controls (`SIFT_TELEMETRY_DISABLED`, `SIFT_TELEMETRY_URL`), and local artifact handling guidance.
- **Hook Timeout Fallback**: Added `SIFT_HOOK_TIMEOUT_MS` guard in `sift_hook.py`; semantic hook execution now times out safely and falls back to heuristic sifting with explicit fallback marker.
- **Model Warm-Up Guardrails**: Added background semantic model warm-up on server startup with bounded wait (`SIFT_MODEL_READY_WAIT_MS`) and automatic heuristic-mode fallback during cold starts.
- **Async Telemetry Pulses**: Refactored telemetry pulse dispatch to non-blocking background threads with configurable rate limiting (`SIFT_PULSE_RATE_LIMIT_S`) to avoid tool-call latency coupling.
- **Hook Log Rotation**: Replaced raw append logging in `sift_hook.py` with rotating file logs and configurable path/verbosity (`SIFT_LOG_FILE`, `SIFT_LOG_LEVEL`).
- **Identity Git Protection**: `telemetry_core.py` now proactively ensures `.sift_identity` is listed in `.gitignore` before creating/updating machine identity.
- **Doc Sift Rate Control**: Exposed `rate` parameter on `sift_doc` and propagated it to kernel doc sifting for precision-sensitive workflows.
- **Onboarding Dry-Run**: Added `dry_run` support to `sift_onboard` so users can preview file/hook changes without applying writes.
- **Stats Accuracy Note**: `get_sift_stats` now includes explicit disclaimer that token counts are 4 chars/token estimates and may differ from provider billing.
- **In-Memory HTML Path**: `sift_hook.py` now prefers `MarkItDown.convert_stream(...)` for HTML normalization and falls back to temp-file conversion with guaranteed cleanup.
- **Telemetry Reference Doc**: Added `doc/TELEMETRY.md` with endpoint overrides, payload schema, privacy guarantees, and retention/deletion contact.
- **Gateway Regression Test**: Added tests validating Windsurf gateway command generation for both Windows (`pwsh`) and POSIX shell paths.
- **Neural Extras Packaging**: Added optional `neural` dependency group in `pyproject.toml` and documented `pip install .[neural]` in README.
- **Phase-3 Module Scaffold**: Added `semantic_sift/` package wrappers (`server`, `kernel`, `telemetry`, `hook`) plus extraction placeholders (`tools`, `onboarding`, `hook_injector`) to enable staged `server.py` decomposition without runtime breakage.
- **Server Decomposition (Step 2)**: Split monolithic `server.py` responsibilities into `semantic_sift/tools.py`, `semantic_sift/onboarding.py`, and `semantic_sift/hook_injector.py`, and reduced root `server.py` to a thin FastMCP entrypoint.
- **Coverage Expansion (Phase 3)**: Added focused test modules for semantic kernel behavior, ranking behavior, hook routing/exemptions, server tool registration behavior, onboarding flow, and telemetry identity/rate-limit paths.
- **Typing & CI Gate**: Added `mypy` development dependency and configuration in `pyproject.toml`, included `py.typed` marker, and extended `scripts/audit.bat` to run static type checks as part of the security/quality audit pipeline.
- **Exception Handling Hardening**: Replaced remaining silent telemetry exception-swallowing paths with targeted exception handling and structured logger diagnostics in `telemetry_core.py`.
- **Type Hint Expansion**: Added/expanded function annotations across `sift_kernel.py`, `sift_hook.py`, `semantic_sift/tools.py`, and `semantic_sift/hook_injector.py` as groundwork for stricter static analysis.
- **Exception Scope Tightening**: Replaced additional broad catches in kernel/hook paths with narrower exception classes and diagnostic-safe fallbacks.
- **Injector Error Narrowing**: Tightened exception classes across `semantic_sift/hook_injector.py` and `semantic_sift/onboarding.py` for JSON I/O, filesystem operations, and pattern updates to reduce masked failures.
- **Extraction Diff View**: Added `show_diff` support to `sift_extraction` via `perform_extraction_cleaning(..., show_diff=True)` with a `--- REMOVED CONTENT ---` section for source-fidelity review.
- **Compaction Fidelity Signal**: Added vocabulary-overlap scoring in `perform_compaction_summary` with threshold control (`SIFT_COMPACTION_FIDELITY_THRESHOLD`) and low-fidelity warning injection.

### 🛠️ Infrastructure & Maintenance
- **Security Cleanup**: Removed `.gemini/` and other sensitive directories from Git tracking.
- **History Scrubbing**: Sanitized Git history to remove a compromised GitHub token while maintaining configuration integrity.
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

### 🛡️ Automated Security & Privacy
- **Automated `.gitignore` Protection**: Upgraded `sift_onboard` to automatically detect and update the project's `.gitignore` file, shielding `.sift_identity`, `.sift_telemetry.json`, and `.sift_cache/` from accidental version control exposure.
- **Onboarding Security Mandate**: Integrated explicit **SECURITY & PRIVACY** instructions into the onboarding mandate, ensuring agents and users are aware of best practices for protecting local identity and telemetry data.

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
