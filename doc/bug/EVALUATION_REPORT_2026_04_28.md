# Semantic-Sift: Independent Evaluation Report

**Date**: 2026-04-28  
**Evaluator**: OpenCode (claude-sonnet-4.6)  
**Scope**: Full codebase + documentation review  
**Status**: Findings captured — Fix plan in `FIX_PLAN_5_STAR.md`

---

## 1. Code Quality

### Strengths

- **Clear module separation.** `sift_kernel.py`, `telemetry_core.py`, `sift_hook.py`, and `server.py` have well-defined responsibilities. Extracting core logic into `sift_kernel.py` is sound architecture that enables isolated testing.
- **Lazy loading is correctly implemented.** Device detection and MarkItDown imports are deferred — a production-critical concern for an MCP server that must start fast.
- **Caching is thoughtful.** SHA-256 key derivation for disk-persistent semantic cache is correct. The two-stage approach (raw markdown cache + sifted result cache) shows mature thinking about re-sifting costs.
- **Changelog discipline.** `CHANGELOG.md` is detailed, structured, and follows Keep-a-Changelog format. This is uncommon and valuable.

### Weaknesses

| ID | File | Issue | Severity |
|---|---|---|---|
| CQ-01 | `server.py` | File does too much: MCP tools, platform-detection, file injection, hook merging, plugin generation in one module. Violates single responsibility. | High |
| CQ-02 | `server.py` | Hardcoded absolute path `C:\Users\luism\Workbench\GitHub\semantic-sift\venv312\Scripts\python.exe` embedded in generated TypeScript/shell plugins injected into other IDEs. | Critical |
| CQ-03 | `tests/` | No tests for `perform_semantic_sift`, `perform_ranking`, `load_file_content`, `sift_hook.py` routing, or any `server.py` MCP tools. Neural/semantic path has zero test coverage. | High |
| CQ-04 | `sift_kernel.py` | `except Exception: pass` silently swallows errors throughout. Silent failures in an MCP server are untraceable. | Medium |
| CQ-05 | `sift_kernel.py` | Incomplete type hints. Functions like `apply_heuristic_sieve` lack annotations. Contradicts stated PEP 8 / Python 3.10+ standard in `AGENTS.md`. | Low |
| CQ-06 | Root | No `pyproject.toml` or formal packaging. Installation is manual. Not installable by any user other than the original author without editing source code. | High |

---

## 2. Security

### Strengths

- Secret redaction before logging in `telemetry_core.py` covers GitHub PATs, OpenAI keys, Slack tokens, high-entropy hashes, and password/token patterns. Tests confirm coverage.
- `SIFT_TELEMETRY_DISABLED` kill-switch provides full opt-out. Essential for this class of tool.
- HTTP scheme enforcement in `send_telemetry_pulse` with Bandit `# nosec B310` annotation shows vulnerability awareness.
- Telemetry is metadata-only by design (character counts, latency, tool names — not content).

### Weaknesses

| ID | File | Issue | Severity |
|---|---|---|---|
| SEC-01 | `server.py` | `sift_read_file` accepts arbitrary `path` strings with no path traversal protection. An agent can call `sift_read_file(path="../../etc/passwd")` and succeed. | Critical |
| SEC-02 | `server.py` | Hardcoded personal path in generated hook plugins creates a trust boundary — anyone with write access to the project can redirect execution. | High |
| SEC-03 | `sift_hook.py` | Debug log written to `.gemini/sift_debug.log` with no rotation. Long-running sessions grow unbounded. Not documented or configurable. | Medium |
| SEC-04 | `sift_kernel.py` | Windsurf security gateway uses `stat -c %s` (Linux/macOS only). Silently inactive on Windows (win32), the declared primary development platform. | High |
| SEC-05 | `telemetry_core.py` | Telemetry pulses sent to `https://www.luiskobayashi.com/api/sift` (personal domain). Payload schema, data retention, and deletion policy are not documented in `SECURITY.md`. Enterprise trust-boundary concern. | High |
| SEC-06 | `telemetry_core.py` | `.sift_identity` UUID stored in `os.getcwd()`. Can be accidentally committed before `sift_onboard` runs and updates `.gitignore`. | Medium |

---

## 3. Efficiency

### Strengths

- Heuristic sieve is genuinely fast (~14ms). Correct choice for high-frequency, low-stakes log filtering.
- Disk-based semantic cache is the right design. Makes repeat calls near-free (~1ms).
- BGE cross-encoder for reranking is more accurate than embedding-similarity for short document chunks.

### Weaknesses

| ID | File | Issue | Severity |
|---|---|---|---|
| EFF-01 | `sift_hook.py` | Hook runs synchronously in the IDE tool response pipeline. LLMLingua inference (measured: 8562ms) blocks the entire IDE tool response. No async path, no timeout, no heuristic-only fallback. | Critical |
| EFF-02 | `sift_kernel.py` | First cold call triggers Transformers model download and load (30–120s) with no progress feedback. MCP server appears to hang. | High |
| EFF-03 | `sift_hook.py` | HTML normalization writes to a temp file on disk and calls `MarkItDown.convert(temp_path)` synchronously in the hot path. In-memory approach would be more appropriate. | Medium |
| EFF-04 | `sift_kernel.py` | Compaction at 0.2 rate with no mechanism to detect meaning loss. User has no signal when a compaction degraded fidelity. | Medium |
| EFF-05 | `telemetry_core.py` | `send_telemetry_pulse` called on every non-cached invocation with a 5s network timeout. Under high-frequency agent use, this adds latency to every response and can saturate the network. | Medium |

---

## 4. User Evaluation by Persona

### Senior Engineer ★★★☆☆

**What works:** The value proposition is clear. The heuristic sieve is immediately useful for log-heavy workflows. The `sift_read_file` / `sift_analyze_file` API pattern is correct — advisory before action.

**What blocks:** The 8-second blocking hook stall in Cursor/VS Code is not acceptable for daily use. The hardcoded personal venv path makes this impossible to install on a team machine. No formal packaging means no `pip install`. Path traversal on `sift_read_file` would need to be closed before use on any shared machine.

**Verdict:** Usable solo after manual configuration. Not team-deployable in current state.

---

### Researcher / Data Scientist ★★★★☆

**What works:** `sift_doc` over a 14MB PDF in a single turn is genuinely useful. MarkItDown XLSX integration preserving table structure is a meaningful differentiator. Two-stage cache makes re-reading the same paper fast.

**What blocks:** No `pip install`. No rate override on `sift_doc` — the global 0.4 rate may lose methodology details in dense technical papers. Cold-start model download with no progress bar amplifies onboarding friction for non-systems users.

**Verdict:** Best-fit persona. High ceiling once set up. Onboarding friction is the main barrier.

---

### Project Manager / Stakeholder ★★★☆☆

**What works:** `get_sift_stats` is the right feature — a dashboard in natural language. Audit headers provide visible reduction percentages that are easy to report.

**What blocks:** Token counts use a 4-chars/token heuristic, not actual billed tokens. Diverges from billing reality for code-heavy content. Telemetry to a personal domain without a documented retention/deletion policy raises questions in any enterprise procurement conversation.

**Verdict:** Good instrumentation story. Enterprise-readiness requires a formal privacy policy and configurable telemetry endpoint.

---

### Knowledge Writer / Documentation Author ★★★☆☆

**What works:** `sift_doc` / `sift_extraction` pipeline for distilling PDFs, Word docs, and cluttered HTML is the right tool for reference material ingestion. Compaction hook concept for session history is useful.

**What blocks:** Compression is lossy and non-deterministic on first run. For writing workflows, losing a precise definition or number is a serious error. No diff-based "what was removed" output. The `sift_onboard` tool modifying instruction files in other IDEs without a dry-run or confirmation is a significant trust ask.

**Verdict:** Useful for rough ingestion and summarization. Not reliable enough for source-faithful extraction without a verification step.

---

## 5. Summary

| Dimension | Rating | Primary Blocker |
|---|---|---|
| Code Quality | ★★★☆☆ | Hardcoded paths, thin test coverage, `server.py` bloat |
| Security | ★★★☆☆ | Path traversal on `sift_read_file`, undocumented telemetry endpoint |
| Efficiency | ★★★☆☆ | Blocking 8s hook latency, no async path, no cold-start UX |
| Senior Engineer | ★★★☆☆ | Not portably installable, no team deploy path |
| Researcher | ★★★★☆ | Strong fit, minor rate control gap |
| Project Manager | ★★★☆☆ | Token heuristic imprecision, no privacy policy |
| Knowledge Writer | ★★★☆☆ | No faithfulness check, aggressive mandate injection |

The core concepts — heuristic sieve, semantic compression, reranking, hook interception — are sound and address a real problem. The gap to 5 stars is operational maturity, not conceptual redesign. See `FIX_PLAN_5_STAR.md` for the remediation roadmap.
