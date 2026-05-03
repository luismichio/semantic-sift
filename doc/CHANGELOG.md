# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ✨ New Features
- **Hybrid Engine CLI (`semantic-sift-cli`)**: Added a Python-based CLI router that dynamically switches between low-latency Rust/ONNX execution and high-throughput PyTorch execution (Flash Attention) based on payload size.
- **Native Rust Sift-Core**: Scaffolding and implementation of `crates/sift-core`, a high-performance Rust port of the distillation engine.
    - **Heuristic Sieve (Native)**: Zero-dependency, ultra-fast regex-based log cleaner.
    - **Semantic Engine (ONNX)**: Native inference wrapper for LLMLingua-2 via `onnxruntime-rs`.
    - **Dual Distribution**: Exposes both a public Rust library and a standalone CLI binary designed for Tauri/Electron sidecar integration.
- **Sidecar Performance Benchmarks**: Integrated a `criterion` suite in `crates/sift-core` to verify ultra-low latency (e.g. **<1ms** for heuristic log sifting).
- **Interactive Sidecar Demo**: Added a `demo/` directory with a Node.js proof-of-concept showing how to integrate the Rust sidecar into desktop applications in minutes.
- **Telemetry Management Commands**: Added `semantic-sift-stats` and `semantic-sift-onboard` global terminal CLIs for instant ROI reporting and project initialization. Added `sift_dashboard` MCP Prompt for UI-driven telemetry access.
- **Automated Slash Command Injection**: `sift_onboard()` now automatically configures project-level slash commands:
    - **OpenCode**: Injects `/sift-stats` and `/sift-onboard` into `opencode.json`.
    - **Gemini CLI**: Generates `.gemini/commands/sift-stats.toml`.
- **MarkItDown Multi-Modal Ingestion**: Integrated Microsoft's `MarkItDown` as an optional structural pre-processor (via `[multi-modal]`). Semantic-Sift now supports converting **PDF, DOCX, XLSX, and PPTX** to Markdown before sifting.
- **Subconscious HTML Normalization**: Upgraded the `sift_hook.py` interceptor to automatically detect HTML content (e.g., from web search results) and convert it to clean Markdown using MarkItDown before semantic compression.
- **Multi-Agent & Subagent Shielding**: Implemented a workspace crawler in `server.py` that automatically detects and shields specialized agent folders (`.codex/agents/`, `.cursor/agents/`, `.junie/agents/`) and scoped `AGENTS.md` mandates.
- **OpenTelemetry Tracing**: Integrated OTel with an isolated TracerProvider to provide a traceable "Chain of Custody" for data without interfering with host applications.

### ⚖️ Licensing & Strategy
- **Apache 2.0 Transition**: Formally transitioned from BSL 1.1 to the **Apache License 2.0** to facilitate community adoption and enterprise integration.
    - Updated all 12 source files with `SPDX-License-Identifier: Apache-2.0`.
    - Updated `pyproject.toml` with `License :: OSI Approved :: Apache Software License` classifiers.
- **"Closed Contribution" Policy**: Adopted an "Open Source, Closed Contribution" model (inspired by SQLite) to maintain strict architectural integrity. Permissive use, embedding, and forking are encouraged, but external PRs no longer accepted.
- **Tiered Licensing Documentation**: Documented the ecosystem strategy (MIT for utilities, Apache 2.0 for infrastructure) in the Studio of Two course materials.

### 📊 Benchmarks
- **Realistic Semantic Metrics**: Updated `benchmark_sift.py` to realistically simulate a 50% reduction for Natural Language scenarios (default `rate=0.5`), replacing the previous mocked 99.9% value to ensure metric credibility.
- **Standardized Benchmark Lab**: Replaced simulated data with a suite of real-world "Context Monsters" in `benchmarks/data/`, including authentic failing Vercel build logs and Git merge conflicts.

### 🏗️ Infrastructure & Maintenance
- **Local Quality Gates**: Implemented a comprehensive pre-push strategy:
    - **Git `pre-push` hook**: Automatically runs Ruff, Mypy, Bandit, and Pytest before every push.
    - **Refined `scripts/audit.bat`**: Added Ruff linting and expanded module coverage for type checks.
    - **IDE Automation**: Configured `.vscode/settings.json` for automatic "Fix on Save" using Ruff.
- **Rust Reliability Tests**: Added integration tests for `sift-core` covering error handling for missing models, empty inputs, and CLI stability.
- **Monolithic Decomposition**: Completed Phase 3 of server extraction, splitting monolithic `server.py` into encapsulated modules: `semantic_sift/tools.py`, `onboarding.py`, and `hook_injector.py`. Established `sift_kernel.py` as the standalone engine.
- **Dependency Stability**: Aligned `pyproject.toml` and `requirements.txt` with floor version pins (`mcp>=1.0`, `numpy>=1.24`, `opentelemetry-api>=1.20`, etc.) to prevent silent breakage on future releases.
- **Zero-Vulnerability Pipeline**: Integrated `bandit` (SAST) and `pip-audit` (SCA) into the mandatory security audit suite.

### 🐛 Bug Fixes
- **Google Antigravity telemetry misattribution**: Replaced mixed identity parsing in `sift_hook.py` with a two-phase design using `telemetry_core.detect_client_id()`. This eliminates env-var pollution (e.g. `VSCODE_PID`) leaking from parent shells and ensures correct attribution to `"Google Antigravity"`.
- **Unshielded Env Mandate Bypass — File Size Paradox**: Removed the `> 1KB` conditional from the `AGENTS.md` Auto-Sift Mandate. Agents now use `sift_read_file` for all files unconditionally, with the server bypassing sifting automatically for small content.
- **Path Traversal Guard Hardening**: Refactored `resolve_safe_path()` in `sift_kernel.py` to block out-of-workspace reads while providing a heuristic walk-up fallback for IDE-spawned servers. Updated logic to skip the fallback if an explicit `SIFT_WORKSPACE_ROOT` is provided.
- **Negative Token Savings**: Fixed a bug where priority lines (Decision/Status/File markers) were duplicated in compaction summaries. They are now stripped from the source before semantic compression to guarantee output is always smaller than input.
- **Lazy MACHINE_ID**: Replaced import-time identity resolution with a thread-safe lazy singleton to eliminate side-effect file writes in read-only environments.

## [0.2.0] - 2026-04-29

### 🏗️ Infrastructure & CI/CD
- **GitHub Actions CI**: Added `.github/workflows/ci.yml` — matrix build on Python 3.10/3.11/3.13; runs ruff → mypy → pytest with coverage on every push/PR.
- **Automated Release Workflow**: Added `.github/workflows/release.yml` — gates on full quality pipeline and publishes to PyPI via OIDC trusted publishing.
- **Test Coverage Expansion**: Increased suite from 46 to 84 passing tests, covering all platform detection paths, hook routing, and server tool behavior.

### 🧹 Code Quality
- **22 Ruff Violations Fixed**: Resolved multi-statement lines (`E701`), ambiguous variables (`E741`), and unnecessary f-strings (`F541`).
- **mypy Clean**: Achieved zero type errors across all core modules.

### 🛡️ Security & Privacy
- **Security Policy Expansion**: Rewrote `SECURITY.md` with concrete telemetry schemas and privacy controls (`SIFT_TELEMETRY_DISABLED`, `SIFT_TELEMETRY_URL`).
- **Telemetry Secret Redaction**: Added `redact_secrets_for_telemetry()` to normalize all secret-type labels to a generic `[REDACTED]` before they touch the network.
- **Identity Git Protection**: Proactively ensures `.sift_identity` is listed in `.gitignore` before creation.

## [1.0.0] - 2026-04-13

### Added
- **Initial Release**: The birth of the "Sanitation Tier" for agentic workflows.
- **Server Core**: Implemented as a standalone Python FastMCP server.
- **The Sieve**: Heuristic regex-based log distillation (`sift_logs`).
- **The Sift**: Semantic BERT-based natural language pruning (`sift_chat`).
- **Hybrid Sift**: Multi-stage distillation for long documentation (`sift_doc`).
- **RAG Refinery**: OCR/PDF artifact cleaning for LlamaIndex synergy (`sift_extraction`).
