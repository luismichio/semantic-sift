# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.7] - 2026-05-07

### Fixed
- **`crates/sift-core/Cargo.toml`**: Pinned `ort` to `=2.0.0-rc.10`. `ort-sys@2.0.0-rc.12` removed `x86_64-apple-darwin` from its prebuilt ONNX Runtime binary table (`dist.txt`), causing all macOS Intel builds to fail at compile time. rc.10 retains prebuilt support for all required targets: Windows MSVC, macOS Intel, macOS ARM, Linux x86_64, Linux aarch64.
- **`crates/sift-core/Cargo.toml`**: Pinned `ndarray` to `=0.16.1`. `ort` rc.10's `OwnedTensorArrayData` trait is implemented for `ndarray 0.16`'s two-parameter `ArrayBase`; `ndarray 0.17` introduced a third generic parameter that breaks the trait bound, causing a compile error on all platforms.
- **CI: `release.yml`**: Replaced `macos-13` (no longer a valid GitHub-hosted runner image) with `macos-14` (ARM64). Added `CIBW_ARCHS_MACOS: "arm64 x86_64"` so both Apple Silicon and Intel wheels are cross-compiled from the single ARM runner. Added `targets: x86_64-apple-darwin` to the `dtolnay/rust-toolchain` step so `cargo` has the cross-compile target registered before cibuildwheel invokes `setup.py` for the Intel wheel.
- **CI: `release.yml`**: Re-enabled Linux wheel builds using `ubuntu-latest` + `manylinux_2_28`. Rust is installed inside the manylinux Docker container via `CIBW_BEFORE_ALL_LINUX` (along with `openssl-devel` required by the `openssl-sys` crate pulled in by `ort`'s `reqwest` dependency). Full image URIs (`quay.io/pypa/manylinux_2_28_x86_64:latest`) used to prevent `cibuildwheel@v2.22.0` from resolving non-existent date-pinned tags. This produces `x86_64` and `aarch64` manylinux wheels on PyPI, eliminating the Rust requirement for Linux users installing from PyPI.
- **CI: `release.yml`**: Removed stale `CIBW_SKIP: *linux*` pattern that was causing cibuildwheel to exit with code 3 on the ubuntu runner when all build identifiers were skipped.
- **CI: `release-binaries.yml`**: Replaced `macos-latest` (resolves to ARM64/macOS 15) with explicit `macos-14` for both macOS matrix entries to make cross-compile intent stable against future `-latest` migrations.

## [0.2.6] - 2026-05-06

### 📦 Packaging & Distribution
- **Cross-Platform Prebuilt Wheels**: Transitioned GitHub Actions release workflow to use `cibuildwheel`. PyPI now hosts pre-compiled binaries for Windows, Linux, and macOS (Intel & Apple Silicon), eliminating the need for end-users to install a Rust compiler.

## [0.2.4] - 2026-05-06

### ✨ New Features
- **Reranking CLI Support**: Added a `rank` command to `semantic-sift-cli` for Top-N context optimization using the neural kernel.
- **High-Fidelity Telemetry Attribution**: The CLI now extracts the actual tool name (e.g., `grep_search`) from environment variables (`SIFT_TOOL_NAME`, `CLAUDE_TOOL_NAME`, `GEMINI_TOOL_NAME`) instead of defaulting to generic `cli_logs`, drastically improving the quality of the ROI dashboard.

### 🛡️ Security & Privacy
- **Anonymous Transient Telemetry**: Fully removed persistent `machine_id` (UUID) tracking and the `.sift_identity` file to align with the Apache 2.0 license and privacy-first principles.
- **Timezone-Aware Pulses**: Telemetry pulses now use `astimezone()` to include the local UTC offset, ensuring accurate global aggregation.
- **Operational Tiers**: Replaced licensing tiers (Commercial/Community) with operational context labels (`Real-World`, `Benchmark`, `Structural`, `Internal-Testing`) to preserve dashboard filtering without licensing baggage.

### 🏗️ Infrastructure & Maintenance
- **CLI Telemetry Integration**: Integrated `telemetry_core` into `semantic_sift/cli.py` and added a `flush_telemetry_pulses()` mechanism to prevent daemon threads from being killed before network requests complete.
- **Onboarding Delegation**: Updated `semantic-sift` onboarding to automatically detect and delegate hook management to the `context-pipe` orchestrator, preventing configuration conflicts in dual-repo setups.
- **Unified Caching**: Standardized echo detection to use the shared `.pipe_cache` directory and a 500-character floor, syncing behavior with Context-Pipe.
- **Environment Standardization**: Adopted the `CPP_` prefix for unified environment variables across the Studio of Two ecosystems.

## [0.2.3] - 2026-05-05

### Fixed
- **Installation instructions** (`README.md`): Sovereign Pattern block now uses `python3.12 -m venv venv312` with dual-OS activate comments (Windows + macOS/Linux). Removed Windows-only `.\venv\Scripts\activate` shortcut.
- **Python environment table** (`README.md`): Updated venv path examples to reference `venv312` (not `venv`) with separate rows for Windows (`Scripts/python.exe`) and macOS/Linux (`bin/python`).
- Added cross-install note: when using Context-Pipe's Sovereign Dual-Repo Pattern, `semantic-sift` is cross-installed into `context-pipe/venv` — `venv312` is only needed for standalone ML runtime use.

### 🏗️ Strategic Milestones
- **Orchestration Decoupling (The Switchboard Shift)**: Formally extracted all IDE orchestration, hook interception, and pipeline management logic into the standalone **[Context-Pipe Platform (CPP)](https://github.com/luismichio/context-pipe)** repository.
    - **Refinery Role**: Semantic-Sift has transitioned from a monolithic server to a specialized **Intelligence Refinery**. It now functions as the flagship "Node" for CPP while remaining fully functional as a standalone kernel.
    - **Transport Separation**: Removed the universal hook interceptor (`sift_hook.py`) and project-onboarding logic from the primary architecture documents, delegating these responsibilities to the CPP Switchboard.

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
