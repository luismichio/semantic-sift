# Changelog

All notable changes to the **Semantic-Sift** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] — 2026-05-18

### ✨ Quality Sprint — v0.3.1 Prep

### ✨ Added
- **Nesting-Aware Telemetry Discovery**: Updated the `_check_opt_in()` utility to recursively search for the `SIFT_TELEMETRY_OPTED_IN` key within `.gemini/settings.json`, resolving a pulse gap where cloud telemetry was silenced in Gemini CLI hook subprocesses.
- **`setup.py`**: `setuptools_rust` import is now conditional — falls back to `rust_extensions = []` when the package is absent. Editable installs (`pip install -e .`) and CI test runs no longer require a Rust toolchain; the pre-built `sift-core` binary is bundled in the PyPI wheel and fetched via `scripts/fetch_sift_core.py` for dev clones.
- **`.github/workflows/ci.yml`**: Removed stale mypy targets (`telemetry_core.py`, `sift_kernel.py`, `sift_hook.py`) that were deleted in the Phase 6.2 Root-Module Inversion. Targets updated to `server.py semantic_sift/`.
- **`semantic_sift/cli.py`**: Replaced `import telemetry_core` with `from semantic_sift import telemetry as telemetry_core` — eliminates `ModuleNotFoundError` on Linux CI where the deleted root stub is not on `sys.path`.
- **`semantic_sift/telemetry_cli.py`**: Replaced `from telemetry_core import ...` with `from semantic_sift.telemetry import ...` for the same reason.
- **`semantic_sift/kernel.py`** (`perform_ranking`): Added a TF-IDF cosine-similarity fallback tier (numpy-only, no model download) so `sift_rank` always returns scored results when `sentence_transformers` is not installed. Neural ranking remains the first-choice tier; the fallback is used in standard `[dev]` installs and any environment without `[neural]` extras.

### Quality Sprint — v0.3.0 Prep

### ✨ Added
- **Nesting-Aware Telemetry Discovery**: Updated the `_check_opt_in()` utility to recursively search for the `SIFT_TELEMETRY_OPTED_IN` key within `.gemini/settings.json`, resolving a pulse gap where cloud telemetry was silenced in Gemini CLI hook subprocesses.
- **`semantic_sift/tools.py`** (`sift_onboard`): `environment` parameter is now keyword-only with default `None`. When not supplied, the calling IDE/shell is auto-detected via `telemetry_core.detect_client_id()` and surfaced in the onboarding report as `Detected IDE`.
- **`semantic_sift/tools.py`** (`sift_onboard`): CUDA status line now clearly differentiates three states: available (with device index), unavailable (CPU only), and not installed — with actionable `pip install 'semantic-sift[neural]'` hint.
- **`semantic_sift/tools.py`** (`sift_rank`): `SIFT_RANK_TOP_N` environment variable sets the default value for `top_n` (default `3`). Callers can still override per-call.
- **`semantic_sift/kernel.py`** (atomic cache writes): `set_cache()` and `ensure_markdown_content()` now write to a `.tmp` file and atomically rename via `os.replace()` to prevent corrupt cache entries on crash or concurrent writes.
- **`semantic_sift/telemetry.py`** (atomic telemetry writes): `log_telemetry()` now writes via `.tmp` + `os.replace()` to prevent partial JSON on crash.
- **`semantic_sift/telemetry.py`** (TTL pruning): `log_telemetry()` prunes telemetry sessions older than `SIFT_TELEMETRY_TTL_DAYS` (default `90`) days on every write, preventing unbounded growth of `.pipe_telemetry.json`.

### 🔧 Changed
- **`semantic_sift/tools.py`** (`sift_rank`): `top_n` default is now `None` (resolved at runtime from `SIFT_RANK_TOP_N` env var). No behaviour change for callers who pass the argument explicitly.

### 📖 Docs (Doc Audit — Phase 6.2 Alignment)
- **`doc/ARCHITECTURE.md`**: Fixed stale section 1 header (`sift_kernel.py` → `semantic_sift/kernel.py`). Added missing sections 2 (Hook Interceptor / `semantic_sift/hook.py`), 3 (Telemetry / `semantic_sift/telemetry.py`), and 4 (Tools, Onboarding & CLI) — bringing the spec to full parity with the implemented package.
- **`doc/TOOL_REFERENCE.md`**: Replaced 6 stale `sift_kernel.` internal references with `kernel.` to reflect the canonical `semantic_sift/kernel.py` module path post-Phase 6.2 Root-Module Inversion.
- **`doc/ORCHESTRATION_BLUEPRINTS.md`**: Added §5 `Ecosystem Integration (Context-Pipe)` — documents the Studio of Two roles/boundaries table, recommended wiring pattern (compress-before-index and distil-after-retrieval), the `semantic-refinery` pipe snippet, and the `PIPE_WINDOW_PRESSURE` → `--rate` forwarding contract.



### ✨ Added
- **`telemetry_core.py`** (`SIFT_TELEMETRY_FALLBACK_URL` — 6.3): New optional env var. When set, a silent secondary telemetry endpoint is attempted if the primary URL (`SIFT_TELEMETRY_URL`) fails (non-2xx, timeout, or any exception). Both attempts are fully async, capped at 2s each, and silently swallowed on failure. Default is empty (disabled). Primary domain `luiskobayashi.com` is unchanged.
- **`telemetry_core.py`** (`_attempt_send()` — 6.3): New internal helper that encapsulates a single HTTP POST attempt, returning `True` on 2xx. Replaces the inline `try/except urllib` block in `_send_telemetry_pulse_now()`.
- **`doc/TELEMETRY_SPEC.md`** (`## Fallback Endpoint` — 6.3): New section documenting `SIFT_TELEMETRY_FALLBACK_URL`, the two-step send logic, timeout behaviour, and operator use cases.

### Phase 6.2 — Root-Module Inversion

### ✨ Added
- **`semantic_sift/kernel.py`** (6.2): Full `sift_kernel` implementation moved here. This is now the canonical source of truth for all distillation logic.
- **`semantic_sift/telemetry.py`** (6.2): Full `telemetry_core` implementation moved here. Includes `_attempt_send()` + fallback logic (6.3).
- **`semantic_sift/hook.py`** (6.2): Full `sift_hook` implementation moved here. Imports `semantic_sift.kernel` and `semantic_sift.telemetry` via canonical paths — no root-module cross-dependency.
- **`semantic_sift/server.py`** (6.2): Full server implementation moved here. Imports `semantic_sift.kernel` directly. Now the canonical `[project.scripts]` entry point.

### 🔧 Changed
- **`pyproject.toml`** (6.2): Entry point updated from `server:main` to `semantic_sift.server:main`.
- **Root stubs** (`sift_kernel.py`, `telemetry_core.py`, `sift_hook.py`, `server.py` — 6.2): Reduced to thin re-export stubs (`from semantic_sift.X import *`). DeprecationWarning removal deadline updated from `v0.4.0` to `v0.3.0`.




### ✨ Added
- **`semantic_sift/tools.py`** (`sift_warmup` — 5.2): New MCP tool registered in `register_tools()`. Explicitly triggers neural model warm-up and returns current readiness status as `{"ready": bool, "latency_ms": float, "error": str|null}`. Polls `sift_kernel._MODEL_READY` (threading.Event) with a 5-second timeout; surfaces `_MODEL_WARMUP_ERROR` on failure. Allows orchestration scripts to pre-warm before first real request.
- **`doc/TOOL_REFERENCE.md`** (`sift_warmup` entry — 5.2): Full reference entry added after `sift_onboard` — documents parameters, return schema, error states, and recommended usage pattern for `onInit` hooks.
- **`README.md`** (`## ⚡ Quickstart (60 seconds)` — 5.3): Added a 4-step "Hello World" path: install, onboard, MCP config snippet, optional warm-up. Inserted after the introductory section, before `## 🏛️ Multidisciplinary Value`.

### Phase 4 - Package Structure & API Clarity

### ⚠️ Deprecated
- **`sift_kernel` (root module — 4.1 → 6.2)**: Root file is now a thin re-export stub; implementation lives in `semantic_sift.kernel`. Emits `DeprecationWarning` on import. Scheduled for removal in v0.3.0.
- **`telemetry_core` (root module — 4.1 → 6.2)**: Root file is now a thin re-export stub; implementation lives in `semantic_sift.telemetry`. Emits `DeprecationWarning` on import. Scheduled for removal in v0.3.0.
- **`sift_hook` (root module — 4.1 → 6.2)**: Root file is now a thin re-export stub; implementation lives in `semantic_sift.hook`. Emits `DeprecationWarning` on import. Scheduled for removal in v0.3.0.

### 🔧 Changed
- **`pyproject.toml`** (4.2): Removed `setuptools-rust>=1.8.0` from `[build-system] requires`. The Rust `sift-core` binary is pre-compiled and bundled in the PyPI wheel; end-users installing from PyPI never need a Rust toolchain. Editable/dev installs continue to use `python scripts/fetch_sift_core.py`. Added `native = []` as a no-op optional dependency group for tooling that requires an explicit handle.
- **`README.md`** (4.2): Added `## Performance Tiers` section documenting the Python MCP Server vs Rust CLI Sidecar comparison table, the PyPI wheel bundling guarantee, the `fetch_sift_core.py` editable-install path, and the `[native]` optional extra.

### 🛡️ Security & Privacy
- **Opt-In Telemetry (3.1)**: Flipped telemetry default from opt-out to **opt-in**. Telemetry is now a no-op unless `SIFT_TELEMETRY_OPTED_IN=true` is set. Legacy `SIFT_TELEMETRY_DISABLED=true` kill-switch is retained for backward compatibility. GDPR/CCPA alignment complete.
- **Telemetry Endpoint Hardening (3.3)**: Reduced HTTP timeout from 5s to 2s. Exception scope explicitly covers `urllib.error.URLError`, `socket.timeout`, `OSError`, and `ConnectionRefusedError`. Telemetry failures are fully silent and never block the main flow.
- **Path Bypass Audit Log (3.2)**: `resolve_safe_path()` now emits a `WARNING` via the `semantic_sift.security` logger to `stderr` whenever `SIFT_ALLOW_GLOBAL_READS=true` bypasses workspace sandboxing. Log includes the full resolved path.
- **Input Size Guard (3.4)**: Added `_enforce_input_size_guard()` to `sift_kernel.py`. All public processing entry points (`apply_heuristic_sieve`, `perform_hybrid_sift`, `perform_semantic_sift`, `perform_doc_sift`, `perform_compaction_summary`, `perform_extraction_cleaning`) now enforce a configurable input cap (default 50MB). Inputs exceeding the limit are truncated with a notice prepended; a warning is emitted via `semantic_sift.input_guard` logger. Override: `SIFT_MAX_INPUT_MB`.
- **SECURITY.md Rewrite**: Updated `SECURITY.md` to document opt-in consent model, path-bypass audit log, input size limits, 2s timeout guarantee, and GDPR/CCPA compliance stance.

## [0.2.7] - 2026-05-07

### Added
- **`scripts/fetch_sift_core.py`**: New helper script for editable/dev installs. Downloads the pre-built `sift-core` binary for the current platform from the matching GitHub release and installs it into the active Python environment's `Scripts`/`bin` directory — no Rust compiler required. Run once after `pip install -e .`: `python scripts/fetch_sift_core.py`.

### Fixed
- **`crates/sift-core/Cargo.toml`**: Pinned `ort` to `=2.0.0-rc.10`. `ort-sys@2.0.0-rc.12` removed `x86_64-apple-darwin` from its prebuilt ONNX Runtime binary table (`dist.txt`), causing all macOS Intel builds to fail at compile time. rc.10 retains prebuilt support for all required targets: Windows MSVC, macOS Intel, macOS ARM, Linux x86_64, Linux aarch64.
- **`crates/sift-core/Cargo.toml`**: Pinned `ndarray` to `=0.16.1`. `ort` rc.10's `OwnedTensorArrayData` trait is implemented for `ndarray 0.16`'s two-parameter `ArrayBase`; `ndarray 0.17` introduced a third generic parameter that breaks the trait bound, causing a compile error on all platforms.
- **CI: `release.yml`**: Upgraded `cibuildwheel` from `v2.22.0` to `v3.4.1` — v2.22.0's internal manylinux_2_28 image tag mapping resolves to a date-pinned quay.io tag that no longer exists; v3.4.1 uses current valid tags.
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
