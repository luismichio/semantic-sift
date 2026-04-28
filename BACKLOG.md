# 📋 Semantic-Sift Backlog & Tasks

This document tracks identified challenges, real-world usage observations, and planned improvements for the Semantic-Sift ecosystem.

---

## 🔴 Open Challenges (To be Addressed)

### 1. `sift_analyze` Trigger Blindness
**Observation**: During long implementation sessions, the agent may skip sifting for surgical reads that fall just below current thresholds.

**Proposed Solutions**:
- [ ] **Adaptive Thresholds**: Implement dynamic thresholds in `sift_analyze` (e.g., triggering at 500 chars for high-noise logs but keeping 2000+ for high-signal source code).
- [ ] **Foundational Sanitization**: Implement a non-semantic "comment stripper" for foundational files (`AGENTS.md`) that preserves instructions but reduces character count without violating the "Never Sift" rule.

### 2. `sift_onboard` Auto-Detection
**Observation**: `apply_onboarding()` requires `environment` as a mandatory positional argument. Calling the MCP tool without it throws a `TypeError`. The function should auto-detect the environment from the running process tree or fall back to a safe default.

**Proposed Solutions**:
- [ ] **Environment Auto-Detection**: Inspect `sys.argv`, `os.environ`, and parent process name to infer environment (`opencode`, `cursor`, `claude`, etc.) when not explicitly provided.
- [ ] **MCP Tool Default**: Make `environment` optional in the MCP-exposed `sift_onboard` tool with `None` triggering auto-detection.

---

## 🟡 In Progress

### 3. Analytical Feedback Loop
- [ ] **Local LLM Feedback**: Allow the agent to "downvote" a sift if it loses too much meaning, updating local heuristic rules.
- [ ] **Automatic Rate Adjustment**: Dynamically adjust compression rates based on the observed "Meaning Loss" telemetry.

---

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

---

## 🔗 Out of Scope (Tracked in Meechi)

- **Subconscious Entropy Mapping**: Use BERT attention maps to highlight high-signal segments in the Meechi PWA UI. Depends on the ONNX port above. → Tracked in [meechi.me](https://meechi.me).
