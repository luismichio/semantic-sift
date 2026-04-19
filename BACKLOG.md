# 📋 Semantic-Sift Backlog & Tasks

This document tracks identified challenges, real-world usage observations, and planned improvements for the Semantic-Sift ecosystem.

---

## 🔴 Open Challenges (To be Addressed)

### 1. `sift_analyze` Trigger Blindness
**Observation**: During a long-running implementation session (e.g., Soft-NAM Core DSP), the mandatory `sift_analyze` trigger was rarely hit despite high activity.

**Identified Causes**:
- **Environment-Level Pre-Truncation**: The hosting environment (Gemini CLI) often heuristically truncates or masks verbose tool outputs (e.g., `<tool_output_masked>`) *before* they reach the agent's context. This removes the "wall of noise" that would typically trigger a semantic analysis.
- **SOP Conflict (Foundational Protection)**: Standard Operating Procedures (SOPs) explicitly forbid sifting foundational instruction files (`AGENTS.md`, `GEMINI.md`). Since these are often the largest files in a repo, the agent skips analysis even if they exceed the 2,000-character threshold.
- **Surgical Task Focus**: In the implementation phase, the agent frequently performs targeted reads (e.g., specific line ranges). These high-signal reads often fall just below the 2,000-character mandatory trigger.

**Proposed Solutions**:
- [ ] **Adaptive Thresholds**: Lower the `sift_analyze` trigger to ~1,000 characters for technical logs while keeping it higher for source code.
- [ ] **Environment Awareness**: Detect when the host has already performed brute-force truncation and adjust the recommendation accordingly.
- [ ] **Foundational Sanitization**: Implement a non-semantic "comment stripper" for foundational files that preserves instructions but reduces character count without violating the "Never Sift" rule.

---

## 🟡 In Progress

### 2. Multi-IDE Orchestration
- [x] Heuristic keyword discovery for standard config paths.
- [x] Injection of "Context-Mode" specific synergy rules.
- [ ] Support for **Zed** and **Continue.dev** specific tool schemas.

---

## 🟢 Completed (Phase 0)
- [x] **`sift_analyze` Trigger Blindness**: Implemented environment awareness to detect host-level truncation (Gemini CLI) and lowered the mandatory trigger threshold to 1,000 characters.
- [x] **Kernel Implementation**: LLMLingua-2 integration via FastMCP.
- [x] **Telemetry Tier**: Local JSON performance tracking.
- [x] **Structural Sieve**: Regex-based log distillation.
- [x] **Refinery Loop**: `sift_extraction` for Docling parity.

---

## ⚪ Long-term Vision
- [ ] **WebGPU/ONNX Port**: Native browser execution for the Meechi PWA.
- [ ] **Local LLM Feedback**: Allow the agent to "downvote" a sift if it loses too much meaning, updating local heuristic rules.
