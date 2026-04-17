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
