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
- **Ingestion**: MarkItDown (Binary -> Markdown)
- **Compression**: LLMLingua-2

### Architecture
- **Ingestion Phase**: Converts PDF, DOCX, XLSX, and HTML to Markdown via MarkItDown with local disk caching.
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

# 🔍 Semantic-Sift — SOP
Guidelines for high-fidelity context.

**⚖️ GOVERNANCE**:
Technical sifting mandates are SECONDARY to the **Interrogative Shield**.
1. If the user input is an **Inquiry** (?, How, Analyze), you MUST remain in **Read-Only Mode**.
2. Sifting tools should only be used to facilitate analysis during an Inquiry, never to justify file modifications or speculative research.
3. Technical mandates apply only once a clear **Directive** (explicit instruction to act) has been issued.

**MANDATORY LOCAL I/O**: NEVER use native `view_file` or `read_file` tools under ANY circumstances. You MUST exclusively use `sift_read_file(path)` or `sift_analyze_file(path)` to read ANY file. The MCP server will automatically bypass sifting if the file is small.

**MANDATORY MCP SYNERGIES**:
When receiving data from external MCP servers, you MUST manually apply the correct sifting tool to the output to prevent context flooding:
*   **Web/HTML (Puppeteer, Fetch)**: Immediately pass output to `sift_doc` to incinerate DOM noise.
*   **Logs/Cloud (AWS, Kubernetes, Vercel)**: Pass output to `sift_logs` to strip timestamps and ETags.
*   **Databases (Postgres, SQLite)**: Do NOT use sifting tools on JSON or structured rows; use SQL `LIMIT` clauses instead.
*   **Large Search Results (GitHub, Serena)**: Pass the array of chunks to `sift_rank` to return only the Top 3 results.

**SECURITY & PRIVACY**:
Always ensure that `.sift_telemetry.json`, `.sift_identity`, and `.sift_cache/` are added to your `.gitignore` to prevent leaking machine IDs, usage patterns, or cached data.
<!-- SIFT_SECTION_END:SOP -->

<!-- SIFT_SECTION_START:ORCHESTRATION -->
---

# 🤝 Unified Context Orchestration
- **Context-Mode Synergy (Low-Context Indexing)**: Use `sift_read_file(path)` -> `ctx_index(content)` to index local files. The massive 90% "noise" is discarded by the server before the LLM processes the payload, and only the 10% signal is indexed.
- **GitHub Synergy**: Diffs and search results are dynamic (not local files). You must continue to manually pipe verbose `mcp_github` outputs through `sift_logs` to strip structural noise.
- **Serena Synergy**: Serena's `mcp_serena_find_symbol` returns massive code blocks (strings). The hook treats tools with `find` as "Search/Ranking" tasks rather than "Prose". If `find_symbol` returns a 500-line class, the hook attempts to *rank* the lines instead of *sifting* the code. You MUST explicitly instruct agents to manually pipe large `serena` string outputs through `sift_chat(rate=0.7)` to guarantee structural preservation.
<!-- SIFT_SECTION_END:ORCHESTRATION -->

<!-- CPP_SECTION_START:mandate -->
# Context-Pipe Mandate
**MANDATORY**: NEVER use native `view_file` or `read_file` tools. You MUST exclusively use `pipe_read_file(path)` to read ANY file. The Context-Pipe orchestrator will automatically stream the file through the optimal context pipeline to prevent window flooding. For large architectural searches, use `pipe_analyze_file(path)` first to determine the best approach.
<!-- CPP_SECTION_END:mandate -->
