# 📋 Semantic-Sift Backlog & Tasks

This document tracks identified challenges, real-world usage observations, and planned improvements for the Semantic-Sift ecosystem.

---

## 🔴 Open Challenges (To be Addressed)

### 1. `sift_analyze` Trigger Blindness
**Observation**: During long implementation sessions, the agent may skip sifting for surgical reads that fall just below current thresholds.

**Proposed Solutions**:
- [ ] **Adaptive Thresholds**: Implement dynamic thresholds in `sift_analyze` (e.g., triggering at 500 chars for high-noise logs but keeping 2000+ for high-signal source code).
- [ ] **Foundational Sanitization**: Implement a non-semantic "comment stripper" for foundational files (`AGENTS.md`) that preserves instructions but reduces character count without violating the "Never Sift" rule.

---

## 🟡 In Progress

### 2. Analytical Feedback Loop
- [ ] **Local LLM Feedback**: Allow the agent to "downvote" a sift if it loses too much meaning, updating local heuristic rules.
- [ ] **Automatic Rate Adjustment**: Dynamically adjust compression rates based on the observed "Meaning Loss" telemetry.

---

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
- [ ] **WebGPU/ONNX Port**: Native browser execution for the Meechi PWA.
- [ ] **Subconscious Entropy Mapping**: Use the BERT attention maps to "highlight" high-signal segments in the UI.
