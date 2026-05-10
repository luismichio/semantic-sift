# 📋 Semantic-Sift Backlog

This document tracks identified challenges, real-world usage observations, and planned improvements for the Semantic-Sift ecosystem.

Last PyPI release: **v0.2.7**. Next publish target: **v0.3.0** (unreleased).

---

## 🔴 Open — High Priority

### `sift_analyze` Trigger Blindness
**Observation**: During long implementation sessions, the agent may skip sifting for surgical reads that fall just below current thresholds.

- [ ] **Adaptive Thresholds**: Implement dynamic thresholds in `sift_analyze` (e.g., triggering at 500 chars for high-noise logs but keeping 2000+ for high-signal source code).
- [ ] **Foundational Sanitization**: Implement a non-semantic "comment stripper" for foundational files (`AGENTS.md`) that preserves instructions but reduces character count without violating the "Never Sift" rule.

### `sift_analyze` Confidence Score
**Observation**: `sift_analyze` returns a binary recommendation (sift / don't sift). A `0.0–1.0` confidence score would allow smarter routing — auto-sift above 0.8, prompt user between 0.5–0.8, skip below 0.5. Feeds directly into the Analytical Feedback Loop item.

- [ ] Return `confidence` float alongside the recommendation.

### Analytical Feedback Loop
- [ ] **Local LLM Feedback**: Allow the agent to "downvote" a sift if it loses too much meaning, updating local heuristic rules.
- [ ] **Automatic Rate Adjustment**: Dynamically adjust compression rates based on the observed "Meaning Loss" telemetry.

### `sift_rank` Configurable Default
**Observation**: `sift_rank` exposes `top_n` in the MCP tool but the server-side default is hardcoded.

- [x] Add `SIFT_RANK_TOP_N` env var (default `3`) respected by the tool when `top_n` is not explicitly passed.

### `get_sift_stats` Markdown Table Output
**Observation**: `.sift_telemetry.json` contains rich data but `get_sift_stats` returns a raw summary.

- [ ] Add a `format: "markdown" | "json"` param to `get_sift_stats`; default to markdown table showing compression ratios, latency, and platform distribution.

### Per-File-Extension Compression Profiles
**Observation**: `rate` is a single global float. Different file types warrant different compression aggressiveness (logs vs. source code vs. markdown).

- [ ] Support a `.sift_profiles.json` in the workspace defining per-extension defaults (e.g. `{"*.log": 0.2, "*.ts": 0.6, "*.md": 0.8}`). Hook picks the profile automatically from `file_ext` (already tracked in telemetry).

### Model "Cold Start" Warmup Command
**Observation**: The `llmlingua-2` model downloads silently in the background via `_warm_up_models()`. Users executing semantic tools for the first time will hit the 1200ms timeout and fall back to heuristics, assuming the tool is broken.

- [ ] Add a dedicated CLI command (e.g., `semantic-sift warmup` or `--download-weights`) for explicit local caching during installation.
- [ ] Add explicit terminal logging when `_MODEL_WARMUP_STARTED` finishes so users know the semantic engine is online.

### Workspace Root Resolution (IDE Path Traversal Guard)
**Observation**: `resolve_safe_path` falls back to `os.getcwd()`. When an MCP server is booted by IDEs (like Cursor or Claude Desktop), `os.getcwd()` is often the server's executable directory, not the user's workspace root, causing the path traversal guard to block legitimate reads.

- [ ] Update documentation to explicitly instruct users to pass the `--workspace-root` flag or set the `SIFT_WORKSPACE_ROOT` environment variable in their IDE's `mcp.json` config.

### Custom Slash Commands per CLI
**Observation**: Users must rely solely on the automatic hook — there is no way to invoke sift tools directly from the chat prompt.

- [ ] Register `/sift`, `/sift-analyze`, and related commands in the config of each supported CLI tool (Gemini CLI, OpenCode, Codex CLI, Claude CLI, etc.). Wire into `sift_onboard` as an additional injection target.

---

## 🔵 Open — Architectural / Long-term

### Platform Detector Registry Refactor
**Observation**: `semantic_sift/hook.py` platform detection is a monolithic `if/elif` chain spanning two separate phases: detection (lines 104–145) and injection (lines 313–327). Each branch simultaneously handles: (1) detecting the platform, (2) extracting `raw_content`, and (3) extracting `agent_label`/`tool_name` overrides. Adding a new IDE requires editing both chains.

**Concrete problems today**:
- `VSCode` branch is a structural catch-all: any unrecognised payload with `tool_response.llmContent` silently becomes `"VSCode"`. No warning is emitted.
- `OpenCode` is detected in two separate branches (AfterTool with `tool_args` and Compacting event). If one is updated without the other, they drift.
- `Gemini/OpenClaw` sub-detection is a nested conditional inside the Gemini branch — easy to miss.
- The injection phase uses string-grouped `elif` (`["Gemini", "Gemini/OpenClaw"]`, `["VSCode", "Claude", "Qwen"]`) which couples platform identity to payload write logic non-obviously.

**Proposed Solution — Registry Pattern**:

Replace both `elif` chains with a list of `PlatformDetector` dataclasses. Each detector encapsulates all platform-specific knowledge: how to recognise it, how to read from it, and how to write back to it.

```python
# semantic_sift/platforms/_base.py
from dataclasses import dataclass
from typing import Callable

@dataclass
class PlatformDetector:
    label: str
    matches: Callable[[dict, str, dict], bool]       # (data, event_name, env) -> bool
    extract: Callable[[dict, str], tuple[str, str | None, str | None]]
    inject: Callable[[dict, str, str], dict]         # (data, sifted, notification) -> data
```

Each platform lives in its own file (`semantic_sift/platforms/opencode.py`, etc.) and registers one or more detectors. `hook.py` detection loop becomes:

```python
from semantic_sift.platforms import all_detectors

detector = next((d for d in all_detectors() if d.matches(data, event_name, os.environ)), None)
platform = detector.label if detector else "Unknown"
raw_content, tool_name_override, agent_label = detector.extract(data, event_name) if detector else ("", None, None)
data = detector.inject(data, sifted, sift_notification) if detector else data
```

**Constraints**:
- `matches()` must be evaluated in priority order; env-var detectors (Claude, Qwen, Codex) must be checked before structural detectors (Gemini, OpenCode).
- `detect_client_id()` in `semantic_sift/telemetry.py` is a separate concern (startup-time, not per-hook) and must not be merged into this registry.
- All existing tests in `tests/test_hook_routing.py` must remain green.

**Effort estimate**: Medium — structural reorganisation, not new behaviour.

- [ ] Implement `PlatformDetector` base + registry in `semantic_sift/platforms/`.
- [ ] Migrate all existing platform branches (OpenCode, Gemini, OpenClaw, VSCode, Claude, Qwen, Codex, Windsurf, Cline) to individual detector files.
- [ ] Replace both `elif` chains in `hook.py` with registry lookup.
- [ ] Emit explicit `"Unknown"` warning log when no detector matches.

### VSCode Platform Detection Tightening
**Observation**: The VSCode branch (`"tool_response" in data and "llmContent" in data["tool_response"]`) is a structural catch-all — any unrecognised IDE with a similar payload silently becomes `"VSCode"` in telemetry.

- [ ] Add a tighter discriminator (e.g. `VSCODE_IPC_HOOK` env var) or emit an `"Unknown"` platform label with a warning log when falling through. *(Subsumes into Platform Detector Registry refactor above.)*

### Context-Aware Thresholding (Adaptive Rate)
**Observation**: Sifting `rate` is static. As the agent's context window fills, a harder compression pass would recover headroom automatically.

- [ ] Consume `PIPE_WINDOW_PRESSURE` env var (0.0–1.0) in `semantic_sift/kernel.py` and override `--rate` when set.
  > 🔗 **Cross-project dependency**: `context-pipe` backlog (Phase 3 — Adaptive Thresholding) tracks the triggering side — passing `PIPE_WINDOW_PRESSURE` to each node.

### Dynamic Backend Routing (Hybrid Engine)
**Observation**: ONNX suffers $O(n^2)$ memory scaling for documents >8K tokens. PyTorch with Flash Attention handles these better.

- [ ] Refactor the Python MCP server to dynamically switch between the Rust `sift-core` (ONNX) backend for daily tasks and PyTorch for massive documents.

### Advanced Neural Kernels
- [ ] **Knapsack Context Optimizer (`sift_pack`)**: 0/1 Knapsack DP algorithm to select the optimal combination of text chunks maximising semantic relevance within a token limit.
- [ ] **`reranker-core` (Rust/ONNX)**: Port the BGE-Reranker to a standalone Rust sidecar to complete the zero-Python Intelligence Tier.

### Native Mobile Integration (Capacitor)
**Observation**: Meechi is a multi-platform digital space (Desktop/Mobile). On Desktop, it uses `sift-core` as a sidecar, but OS security on mobile (iOS/Android) prevents this architectural pattern.

- [ ] **Native Mobile Plugin**: Refactor `sift-core` to be compiled as a static library (`.a` for iOS) or dynamic library (`.so` for Android).
- [ ] **UniFFI Bindings**: Use UniFFI to generate Swift and Kotlin bindings for the `SemanticEngine` and `apply_heuristic_sieve`.
- [ ] **Capacitor Bridge**: Implement a Capacitor Native Plugin that wraps the Rust library, enabling zero-Python context distillation in the mobile version of Meechi.
- [ ] **Mobile Execution Providers**: Enable `CoreML` (iOS) and `NNAPI` (Android) execution providers in the `ort` crate configuration to leverage mobile NPUs.

### Multi-Parser Registry
- [ ] Implement dynamic discovery engine in both Python and Rust to support `markitdown`, `pandoc`, and `LlamaIndex` as swappable ingestion nodes.

### Chain-Aware Telemetry
- [ ] Extend ROI reporting to track the entire "Chain of Custody" (e.g., Ingest → Rank → Sift) and report cumulative savings.

### npm Distribution
- [ ] Investigate publishing as an npm package: (a) thin npm wrapper invoking the Python binary, (b) full JS/TS reimplementation of the heuristic sieve, or (c) MCP-compatible JS server wrapping a compiled binary via Nuitka/PyInstaller.

---

## ⚫ Out of Scope (Tracked in Meechi)

- **Subconscious Entropy Mapping**: Use BERT attention maps to highlight high-signal segments in the Meechi PWA UI. Depends on the ONNX port. → Tracked in [meechi.me](https://meechi.me).

---

## ✅ Completed

### v0.3.0 (unreleased — next publish target)
- [x] **crates.io Publication**: `semantic-sift-core` v0.3.0 published as a standalone high-performance primitive.
- [x] **Native Engine Documentation**: Created comprehensive `crates/sift-core/README.md` with hybrid architecture details, Meechi origin story, and promotion-ready badges.
- [x] **Tauri Promotion Manifest**: Drafted engineering-focused community promotion material in `doc/posts/tauri_show_and_tell.md`.
- [x] **OpenCode Plugin Shape-Awareness**: Refactored the generated OpenCode TypeScript plugin to be "shape-aware," handling both Native tool (`output.result`) and MCP tool (`output.content`) response formats. Resolves silent failures for MCP tools (sst/opencode#25918).
- [x] **Root-Module Inversion**: Canonical implementations moved to `semantic_sift/`; root stub files (`sift_kernel.py`, `sift_hook.py`, `telemetry_core.py`) deleted. All test imports updated. Zero DeprecationWarnings.
- [x] **Telemetry Consent UX**: `_build_telemetry_disclosure()` surfaces opt-in/opt-out notice in every `apply_onboarding()` response.
- [x] **Telemetry Fallback URL**: `SIFT_TELEMETRY_FALLBACK_URL` env var; silent retry on primary endpoint failure.
- [x] **CPP Contract Test Suite**: Mock-subprocess suite in `tests/test_cpp_contract.py` validating `run_pipe()` stdin/stdout/error/timeout contract.
- [x] **`sift_onboard` Environment Auto-Detection**: `environment` is now keyword-only (`*`) with default `None`; auto-detected via `detect_client_id()` when omitted; shown as `Detected IDE:` in the report.
- [x] **`[neural]` Extra Hint in CUDA Status**: Not-installed state now shows `pip install 'semantic-sift[neural]'` actionable hint.
- [x] **Atomic Cache Writes**: `set_cache()`, `ensure_markdown_content()`, and `log_telemetry()` use `.tmp` + `os.replace()` — no corrupt files on crash or concurrent writes.
- [x] **Telemetry TTL Pruning**: `log_telemetry()` prunes sessions older than `SIFT_TELEMETRY_TTL_DAYS` (default `90` days) on every write.
- [x] **`SIFT_RANK_TOP_N` Env Var**: `sift_rank` `top_n` default resolved at runtime from env var; explicit callers unaffected.

### v0.2.7 (released)
- [x] **Phase 3 Security Hardening**: `shell=False` enforced; metacharacter guard; `SIFT_ALLOW_GLOBAL_READS` opt-out for path traversal guard.
- [x] **Opt-In Telemetry**: Telemetry is now a no-op unless `CPP_TELEMETRY_OPTED_IN=true` is explicitly set.
- [x] **`sift_warmup` MCP Tool**: Explicit neural model warm-up; returns `{"ready": bool, "latency_ms": float, "error": str|null}`.

### v0.2.x — Production Hardening (FIX_PLAN_5_STAR)
- [x] **Runtime Hook Portability**: Hook command derived from `sys.executable` at runtime; no hardcoded paths.
- [x] **Startup Validation**: Server fails fast with a clear error if canonical hook is missing.
- [x] **Path Traversal Guard**: `resolve_safe_path()` blocks out-of-workspace reads; `SIFT_ALLOW_GLOBAL_READS` opt-out.
- [x] **Packaging Bootstrap**: `pyproject.toml` with `semantic-sift` console entry point; `pip install .` / `.[neural]` / `.[dev]`.
- [x] **Platform-Aware Windsurf Gateway**: Windows (`pwsh`) and POSIX shell command generation.
- [x] **Hook Timeout Fallback**: `SIFT_HOOK_TIMEOUT_MS` guard; semantic timeout falls back to heuristic sifting.
- [x] **Model Warm-Up Guardrails**: Background warm-up on startup with bounded wait (`SIFT_MODEL_READY_WAIT_MS`).
- [x] **Async Telemetry Pulses**: Non-blocking background threads with rate limiting (`SIFT_PULSE_RATE_LIMIT_S`).
- [x] **Hook Log Rotation**: Rotating file logs with configurable path/verbosity (`SIFT_LOG_FILE`, `SIFT_LOG_LEVEL`).
- [x] **Identity Git Protection**: `.sift_identity` proactively added to `.gitignore` before creation.
- [x] **`semantic_sift/` Package**: Decomposed monolith into typed package; `py.typed` marker; mypy clean (12 files, 0 errors).
- [x] **Security Policy**: `SECURITY.md` rewritten with telemetry schema, privacy controls, and local artifact guidance.
- [x] **`sift_doc` rate param**: Exposed `rate` parameter in MCP tool signature.
- [x] **`sift_extraction` show_diff**: `show_diff` param added; unified diff output on request.
- [x] **`sift_onboard` dry_run**: `dry_run=True` returns planned actions without writing files.
- [x] **Compaction Fidelity Threshold**: `SIFT_COMPACTION_FIDELITY_THRESHOLD` guards against over-compression.
- [x] **`sift_chat` Fidelity Warning**: Emits warning when output fidelity drops below threshold.
- [x] **OpenCode Platform Detection**: `AfterTool` events from OpenCode plugin no longer misidentified as Gemini in telemetry.
- [x] **Telemetry Secret-Type Metadata Leakage**: Type-specific redaction labels replaced with generic `[REDACTED]` in all telemetry paths.

### Phase 3 — The Native Transition
- [x] **Native Rust Sift-Core**: Scaffolding and implementation of `crates/sift-core`.
- [x] **Heuristic Sieve (Native)**: Zero-dependency, ultra-fast regex-based log cleaner.
- [x] **Semantic Engine (ONNX)**: Native inference wrapper for LLMLingua-2 via `onnxruntime-rs`.
- [x] **Automated Cross-Platform Releases**: GitHub Actions workflow for Windows/macOS/Linux binaries.
- [x] **Sidecar Performance Benchmarks**: `criterion` suite verifying <1ms log sifting.
- [x] **Interactive Sidecar Demo**: Node.js proof-of-concept for native app integration.
- [x] **Agentic Chain Protocol (ACP)**: Defined the universal piping standard for modular context distillation.
- [x] **Management Commands**: Added `semantic-sift-stats` CLI and `/sift-stats` / `/sift-onboard` slash commands.
- [x] **Apache 2.0 Transition**: Formally transitioned from BSL 1.1 to the Apache License 2.0.

### Phase 1 — Multi-Agent & Platform Shielding
- [x] **Recursive Subagent Discovery**: Workspace crawling to identify and shield specialized agent folders.
- [x] **Multi-IDE Hook Support**: Native integrations for Claude, Qwen, Codex, Windsurf, Cline, OpenClaw, and JetBrains.
- [x] **Security Gateways**: Proactive inhibitors for Windsurf and Cline.
- [x] **Subagent Telemetry**: Platform "sniffing" and `agent_label` tracking.
- [x] **MCP Synergy Matrix**: Integrated as a prompt-engineered mandate.
- [x] **Environment Awareness**: `sift_analyze` detects host-level truncation (`<tool_output_masked>`) and adjusts recommendations.

### Phase 0 — Foundation
- [x] **Threshold Optimization**: Lowered mandatory trigger threshold to 1,000 characters globally.
- [x] **Kernel Implementation**: LLMLingua-2 integration via FastMCP.
- [x] **Telemetry Tier**: Local JSON performance tracking.
- [x] **Structural Sieve**: Regex-based log distillation.
- [x] **Refinery Loop**: `sift_extraction` for Docling parity.
