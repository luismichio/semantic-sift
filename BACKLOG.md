# 📋 Semantic-Sift Backlog & Tasks

This document tracks identified challenges, real-world usage observations, and planned improvements for the Semantic-Sift ecosystem.

---

## 🔴 Open Challenges (To be Addressed)

### 1. `sift_analyze` Trigger Blindness
**Observation**: During long implementation sessions, the agent may skip sifting for surgical reads that fall just below current thresholds.

**Proposed Solutions**:
- [ ] **Adaptive Thresholds**: Implement dynamic thresholds in `sift_analyze` (e.g., triggering at 500 chars for high-noise logs but keeping 2000+ for high-signal source code).
- [ ] **Foundational Sanitization**: Implement a non-semantic "comment stripper" for foundational files (`AGENTS.md`) that preserves instructions but reduces character count without violating the "Never Sift" rule.

### 2. `sift_onboard` Environment Auto-Detection
**Observation**: The MCP tool already accepts `environment: str | None = None` (no crash). However when `None` is passed, `apply_onboarding()` receives `""` and proceeds without inferring the actual environment — so injection targets for the current IDE are silently skipped. The direct Python call (`apply_onboarding()`) still requires `environment` as a positional arg and will `TypeError` if called without it.

**Proposed Solutions**:
- [ ] **Environment Auto-Detection in `apply_onboarding`**: Inspect `sys.argv`, `os.environ`, and parent process name (via `psutil` or `/proc`) to infer environment (`opencode`, `cursor`, `claude`, etc.) when `environment` is empty/None. Fall back to `"generic"`.
- [ ] **Make `environment` keyword-only with default `None`** in `apply_onboarding()` signature to prevent direct-call `TypeError`.

---

## 🟡 In Progress

### 3. Analytical Feedback Loop
- [ ] **Local LLM Feedback**: Allow the agent to "downvote" a sift if it loses too much meaning, updating local heuristic rules.
- [ ] **Automatic Rate Adjustment**: Dynamically adjust compression rates based on the observed "Meaning Loss" telemetry.

---

## 🔵 Suggested Improvements

### Platform Detection Refactor
**Observation**: `sift_hook.py` platform detection is 8+ `elif` branches. As more CLIs are added (Gemini CLI, Codex CLI, slash commands) this becomes a maintenance liability.
- [ ] **Registry Pattern**: Replace `elif` chain with a list of `PlatformDetector` objects each implementing `matches(data, event_name, env) -> bool`. New platforms register themselves without touching the routing logic.

### Telemetry File Pruning
**Observation**: `.sift_telemetry.json` grows unbounded. Old sessions accumulate indefinitely.
- [ ] **TTL-based pruning**: On each `log_telemetry` call, prune sessions older than a configurable `SIFT_TELEMETRY_TTL_DAYS` (default 90). Zero disk impact on normal usage.

### VSCode Platform Detection Tightening
**Observation**: The VSCode branch (`"tool_response" in data and "llmContent" in data["tool_response"]`) is a structural catch-all — any unrecognised IDE with a similar payload silently becomes `"VSCode"` in telemetry.
- [ ] Add a tighter discriminator (e.g. `VSCODE_IPC_HOOK` env var) or emit a `"Unknown"` platform label with a warning log when falling through.

### `sift_analyze` Confidence Score
**Observation**: `sift_analyze` returns a binary recommendation (sift / don't sift). A `0.0–1.0` confidence score would allow smarter routing — auto-sift above 0.8, prompt user between 0.5–0.8, skip below 0.5. Feeds directly into the Analytical Feedback Loop item.
- [ ] Return `confidence` float alongside the recommendation.

### Per-File-Extension Compression Profiles
**Observation**: `rate` is a single global float. Different file types warrant different compression aggressiveness (logs vs. source code vs. markdown).
- [ ] Support a `.sift_profiles.json` in the workspace defining per-extension defaults (e.g. `{"*.log": 0.2, "*.ts": 0.6, "*.md": 0.8}`). Hook picks the profile automatically from `file_ext` (already tracked in telemetry).

### `get_sift_stats` Markdown Table Output
**Observation**: `.sift_telemetry.json` contains rich data but `get_sift_stats` returns a raw summary. A structured markdown table of compression ratios, latency, and platform distribution would make the data visible directly in-IDE.
- [ ] Add a `format: "markdown" | "json"` param to `get_sift_stats`; default to markdown table.

### `sift_rank` Configurable Default
**Observation**: `sift_rank` exposes `top_n` in the MCP tool but `AGENTS.md` SOP hardcodes "Top 3". The server-side default is also hardcoded.
- [ ] Add `SIFT_RANK_TOP_N` env var (default `3`) respected by the tool when `top_n` is not explicitly passed.

### PyPI Publish
**Observation**: `pyproject.toml` is already in place. Publishing to PyPI would allow `pip install semantic-sift` and significantly lower the adoption barrier. Also a prerequisite for the npm wrapper path.
- [ ] Publish to PyPI. Add a GitHub Actions workflow for automated release on tag push.



## 🟢 Completed (Phase 2: Production Hardening — FIX_PLAN_5_STAR)
- [x] **Runtime Hook Portability**: Hook command derived from `sys.executable` at runtime; no hardcoded paths.
- [x] **Startup Validation**: Server fails fast with a clear error if `sift_hook.py` is missing.
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

## 🟢 Completed (Phase 2: Bug Fixes)
- [x] **OpenCode Platform Detection**: `AfterTool` events from OpenCode plugin (which carry `tool_args`) no longer misidentified as Gemini in telemetry. (`4f9a319`)
- [x] **Telemetry Secret-Type Metadata Leakage**: Type-specific redaction labels (`[REDACTED_GITHUB_PAT]`, etc.) replaced with generic `[REDACTED]` in all telemetry paths. Descriptive labels retained in local debug logs only. (`655cb9e`)

## 🟢 Completed (Phase 1: Multi-Agent & Platform Shielding)
- [x] **Recursive Subagent Discovery**: Implemented workspace crawling to identify and shield specialized agent folders.
- [x] **Multi-IDE Hook Support**: Implemented native integrations for Claude, Qwen, Codex, Windsurf, Cline, OpenClaw, and JetBrains.
- [x] **Security Gateways**: Implemented proactive inhibitors for Windsurf and Cline.
- [x] **Subagent Telemetry**: Integrated platform "sniffing" and `agent_label` tracking.
- [x] **MCP Synergy Matrix**: Integrated as a prompt-engineered mandate (Supersedes "Intelligent Tool Awareness").
- [x] **Environment Awareness**: `sift_analyze` now detects host-level truncation (`<tool_output_masked>`) and adjusts recommendations.

## 🟢 Completed (Phase 0)
- [x] **Threshold Optimization**: Lowered the mandatory trigger threshold to 1,000 characters globally.
- [x] **Kernel Implementation**: LLMLingua-2 integration via FastMCP.
- [x] **Telemetry Tier**: Local JSON performance tracking.
- [x] **Structural Sieve**: Regex-based log distillation.
- [x] **Refinery Loop**: `sift_extraction` for Docling parity.

---

## ⚪ Long-term Vision

- [ ] **Tauri Sidecar / ONNX Port**: Bundle Semantic-Sift as a Tauri sidecar. The neural model (LLMLingua-2 / BERT) would be exported to ONNX and loaded via ONNX Runtime, eliminating the PyTorch/Python dependency for desktop distribution. WebGPU would serve as the acceleration backend in the WebView context.

- [ ] **Standalone Binary Distribution (PyInstaller / Nuitka)**: Compile the server and hook into a single self-contained executable so users without a Python environment can run Semantic-Sift. Would unblock the Tauri sidecar path and simplify onboarding significantly.

- [ ] **npm Distribution**: Investigate whether Semantic-Sift can be published as an npm package. Options include: (a) a thin npm wrapper that installs and invokes the Python binary, (b) a full JS/TS reimplementation of the heuristic sieve for Node-native use, or (c) an MCP-compatible JS server wrapping a compiled binary via Nuitka/PyInstaller. Feasibility depends on the binary compilation milestone above.

- [ ] **Custom Slash Commands per CLI**: Register `/sift`, `/sift-analyze`, and related commands in the config of each supported CLI tool (Gemini CLI, OpenCode, Codex CLI, Claude CLI, etc.) so users can invoke sift tools directly from the chat prompt without relying solely on the automatic hook. Would be wired into `sift_onboard` as an additional injection target.

---

## 🔗 Out of Scope (Tracked in Meechi)

- **Subconscious Entropy Mapping**: Use BERT attention maps to highlight high-signal segments in the Meechi PWA UI. Depends on the ONNX port above. → Tracked in [meechi.me](https://meechi.me).
