# 🧠 Project Identity

- **Project Name**: Semantic-Sift
- **Philosophy**: "Studio of Two" (Partnership, not servitude)
- **Timezone**: CET/CEST
- **Docs Entry Point**: `README.md` & `doc/ARCHITECTURE.md`

---

# 🧠 Core Philosophy: The Studio of Two

We build **Systems, not Patches**.
- **Atomic by Default**: Logic must be modular and testable in isolation.
- **System over Patch**: Always follow the architectural patterns defined in `doc/ARCHITECTURE.md`.
- **Signal over Noise**: The goal of this project is to reduce noise; do not introduce it into the codebase.

---

# 🤖 Working Protocol (Plan → Execute)

Before acting on any non-trivial task, produce a plan first.

**Planning Requirements**:
- Break work into phases with distinct steps.
- Include specific file paths, function names, and line ranges where changes occur.
- Document edge cases, error handling, and validation requirements.
- **Changelog First**: Every feature or fix MUST be accompanied by an entry in `doc/CHANGELOG.md` under `## [Unreleased]`.
- The plan must be self-contained — no clarifying questions should be needed during execution.

**Execution Guidelines**:
- **Pythonic Excellence**: Use Python 3.10+ features, type hints, and follow PEP 8.
- **MCP Compliance**: Ensure all new tools follow the Model Context Protocol standards and use `fastmcp`.
- **Verification**: Run the server and test tools using an MCP inspector or test scripts.
- **Deviations**: Document the reason, explain the alternative, and ask for approval before proceeding.
- **Ambiguities**: STOP and request clarification rather than making assumptions.
- After implementation: provide a concise summary and flag any deviations with reasoning.

---

# 🏗️ Tech Stack & Architecture

### Stack
- **Language**: Python 3.10+
- **Framework**: FastMCP
- **AI Core**: PyTorch, Transformers (Hugging Face)
- **Compression**: LLMLingua-2

### Architecture
- **The Sieve**: Heuristic-based regex filtering for structural noise.
- **The Sift**: Semantic-based model pruning for natural language.
- **The Refinery Loop**: Integration point for Docling/LlamaIndex.

---

# 🛡️ Operational Constraints

### 🛑 The Interrogative Shield
If user input contains questions (`?`, `How`, `Why`, `Analyze`), enter **READ-ONLY MODE**.
Do NOT write or modify files unless explicitly told to "Execute".

### 🛑 Loop Prevention Protocol
> If you fail a test twice, or find yourself suggesting the same fix twice, STOP. Raise your hand: "I am struggling. Here is what I've tried, and here is where I am blocked. I need your expertise."

### 🛑 Anti-patterns
- **No `any` equivalents**: Use proper type hints. Avoid `typing.Any` where possible.
- **No Console Logs**: Use proper logging or remove debugging `print` statements before final submission.
- **No Heavy Weights in Repo**: Do not commit model weights; ensure they are downloaded/cached via `transformers`.

---

# ⚙️ context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Use `web_fetch` or sandbox execution instead.

### Inline HTTP — BLOCKED
Use `run_shell_command` with caution or sandbox execution.

## REDIRECTED tools — use sandbox equivalents

### Shell (>20 lines output)
Use `run_shell_command` only for brief tasks. For heavy analysis, summarize findings.

### File reading (for analysis)
If reading for **analysis/summarization**, use targeted `read_file` with `start_line` and `end_line`.

### grep / search (large results)
Use `grep_search` with conservative `total_max_matches`.

## Output constraints
- Keep responses concise and direct.
- Write artifacts (code, configs) to FILES — never return them as inline text.

<!-- SIFT_SECTION_START:SOP -->
---

# 🔍 Semantic-Sift — Standard Operating Procedures
---

# 🔍 Semantic-Sift — Standard Operating Procedures

To maintain high Signal-to-Noise Ratio (SNR) and prevent context flooding, follow these usage guidelines.

## 🛠️ Tool Selection & Thresholds

| Tool | Trigger Condition | Goal |
| :--- | :--- | :--- |
| `sift_logs` | Any log/terminal output > 50 lines or containing progress bars. | Heuristic removal of timestamps/noise. |
| `sift_chat` | Previous conversation history exceeding 5,000 characters. | Prune linguistic filler (default rate: 0.5). |
| `sift_doc` | Reading documentation files > 10,000 characters. | Hybrid distillation (Heuristic + Semantic). |
| `sift_extraction` | Processing raw OCR or Docling extractions. | Preserve Markdown structure while cleaning debris. |
| `sift_rank` | Selecting best chunks from multiple retrieved documents. | Filter by semantic relevance before sifting. |

## 📐 Rate Guidelines
- **Aggressive (0.3)**: Use for "lost in the middle" scenarios or massive histories.
- **Balanced (0.5)**: Default. Best for general conversation and instructions.
- **Gentle (0.7)**: Use for technical documentation where every keyword matters.

## 🤖 Auto-Sift Mandate
- **Trigger**: The agent MUST run `sift_analyze` on any data (logs, file reads, tool outputs) exceeding **2,000 characters**.
- **Action**: If the estimated noise is **> 15%**, sifting via `sift_logs` or `sift_chat` is REQUIRED before proceeding with analysis.

## 🚫 Sifting Forbidden
- **NEVER** sift foundational instructions (`AGENTS.md`, `GEMINI.md`).
- **NEVER** sift small, surgical code snippets (symbol-level).
- **NEVER** sift security-sensitive configuration files (`.env`, secrets).
<!-- SIFT_SECTION_END:SOP -->

<!-- SIFT_SECTION_START:ORCHESTRATION -->
---

# 🤝 Unified Context Orchestration
- **Context-Mode Synergy**: Run `sift_logs` or `sift_chat` on all tool outputs > 1,000 characters BEFORE calling `context-mode_ctx_index`. This ensures the FTS5 search index remains high-signal.
- **GitHub Synergy**: Use `sift_logs` on verbose PR diffs or repository search results to focus on actionable code changes.
- **Serena Synergy**: Always pipe code bodies > 100 lines through `sift_chat` (rate: 0.7) after retrieval to prune docstring/comment bloat while keeping logic.
<!-- SIFT_SECTION_END:ORCHESTRATION -->
