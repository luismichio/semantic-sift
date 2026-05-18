# 🐛 [RESOLVED] Bug Report: Architectural Friction Causing Auto-Sift Mandate Violation

**Resolution Date**: April 23, 2026  
**Status**: CLOSED  
**Fix Implemented**: Phase 1-4 Zero-Gap implementation (Content-Signature Bypass + Path-Native Tools)

---

## 9. Final Resolution & Technical Post-Mortem

The architectural friction was resolved by shifting the data ingestion burden from the agent's context window to the MCP server.

### The "Node" Middleware Fix (OpenCode Integration)
A critical part of the resolution involved the **OpenCode Native Plugin**. 
*   **What it was**: OpenCode uses a **Node.js / TypeScript** environment for its middleware (`.opencode/plugins/semantic-sift.ts`).
*   **The Fix**: We patched this Node.js logic to scan for the unique Content-Signature. Because OpenCode is a "Smart Hook" platform, it *could* have used the `tool_name`, but we standardized it to use the **Content-Signature Bypass** to ensure that the Node.js plugin behaves identically to the Python-based `sift_hook.py` used in Cursor and VS Code.

### The Self-Aware Node Bypass
To solve the "Double-Sifting" threat across all platforms (regardless of whether they are Node.js, Python, or Shell-based), we implemented a self-aware bypass mechanism:
`--- [Semantic-Sift Audit] ---`

1.  **Ingestion**: `sift_read_file` (Python MCP) sifts the file and prepends this audit header.
2.  **Interception**: The engine (both the **Node.js** OpenCode plugin and the **Python** `sift_hook.py`) detects this existing header in the input and instantly returns the content unmodified.

### Final Verification
- **Verified**: Unit tests pass (12/12).
- **Verified**: Security audit clean (0 Bandit issues).
- **Verified**: ROI confirmed (22.7% context savings unlocked for all IDEs).
- **Verified**: Sift-Centric architecture implemented (Orchestrator silence verified).

The "Antigravity Gap" is officially closed. Agents are now mandated to use proactive path-native sifting, preventing context flooding before it starts.

---

## 1. Description of the Failure
The agent systematically violated the `AGENTS.md` directive known as the **Auto-Sift Mandate**, which states:
> *The agent MUST run `sift_analyze` on any data (logs, file reads, tool outputs) exceeding 1,000 characters.*

When instructed to read the 4,998-character `FAILURE_ANALYSIS_REPORT.md`, the agent used the standard `view_file` tool. The raw file contents were injected directly into the context window, and the agent proceeded to analyze the raw text, bypassing `sift_analyze` and `sift_doc` entirely.

## 2. Technical Root Cause
The failure is not a localized prompt misunderstanding, but a structural friction between the LLM's autoregressive nature and the current MCP tool signatures. 

The root cause consists of three intersecting issues:

### A. The "Echo Chamber" Token Penalty
Currently, the tools exposed by `semantic-sift` (`sift_analyze`, `sift_doc`, `sift_logs`, `sift_chat`) require the target payload to be passed as a string parameter (`"text": "..."`). 
Because the agent lacks an overarching file-system tool that reads *and* sifts simultaneously, it must execute a sequential workflow:
1. Call `view_file("report.md")`.
2. The host environment returns 5,000 characters of raw text **into the agent's active context window**.
3. To comply with the mandate, the agent must then generate a new tool call to `sift_analyze`, echoing all 5,000 characters from its context back into the tool's JSON payload.

Large Language Models are fundamentally trained to avoid massive, exact-string duplication. Generating a 5,000-character payload of text that already exists in the immediate context creates massive friction. The attention mechanism naturally biases toward processing the text that is already visible, effectively treating the `AGENTS.md` mandate as a soft constraint that is "too expensive" to follow.

### B. Lack of Pipeline Middleware
The Model Context Protocol (MCP) does not currently support host-side tool chaining or "piping" (e.g., `view_file | sift_doc`). Every tool execution must round-trip through the LLM's context window. The sifter can only process data that the LLM explicitly echoes back to it.

### C. Post-Hoc Realization
The agent only knows the character count of a file *after* reading it. By the time the agent realizes the output exceeded the 1,000-character threshold, the payload has already polluted the context window. Sifting it retroactively doubles the token usage before yielding any compression benefits, defeating the purpose of the optimization.

---

## 3. Proposed Solutions

To achieve deterministic compliance with the Auto-Sift Mandate, the developer must resolve the token-duplication friction. Here are three grounded, realistic architectural fixes:

### Solution 1: File-System Native Sifting Tools (Recommended)
Update the `semantic-sift` MCP server to accept file URIs/paths rather than raw strings. 
**Proposed Tool Signatures**:
- `sift_read_file(path: string, rate: number)`
- `sift_analyze_file(path: string)`

**Why it works**: The agent can pass a short file path (e.g., `"docs/report.md"`). The MCP server reads the file directly from the disk, processes it through the BERT compression/heuristic engine, and returns *only* the condensed output to the LLM's context window. This prevents the initial 5,000-character pollution.

### Solution 2: Host-Side Interception (The "Context Gate")
Implement a middleware interceptor in the host application (the IDE or the primary MCP client) that automatically intercepts any tool output (e.g., from `view_file`, `run_command`, or `mcp_serena_execute_shell_command`).
- **Logic**: If `response.length > 1000`, the host automatically pipes the response through the local `semantic-sift` daemon before returning the data to the LLM. 
- **Why it works**: It completely removes the burden of manual tool chaining from the LLM, making the 1,000-character mandate physically enforced by the environment rather than a behavioral suggestion in a markdown file.

### Solution 3: Context-Mode Execution Synergy
The `context-mode` server already has a `ctx_execute_file` tool that prevents content from entering the context window (reading it into a sandbox instead). 
- **Integration**: Update `context-mode` to expose a `ctx_sift_and_index` tool. 
- **Why it works**: The agent could trigger a sandboxed script that reads the file, passes it to the `semantic-sift` binary locally, and indexes the distilled output, keeping the raw data permanently out of the token stream.

---

## 4. Conclusion
As long as the sifting tools require the LLM to provide the raw text as a string argument, the agent will inherently resist using them on large, already-read documents to conserve generation tokens. Implementing **Solution 1** (Path-based tool inputs) is the most immediate and realistic fix to restore compliance with the `AGENTS.md` protocol.

---

## 5. Comprehensive Client Integration Matrix

Mapping how each IDE/Agent executes tools, passes data to the middleware, and enforces rules reveals massive fragmentation. This fragmentation directly impacts the implementation of **Solution 1** (Path-Native Tools).

| Environment / Agent | MCP Config Route | Rule Infusion Target | Middleware / Hook Mechanism | Hook Payload Schema | Vulnerability Class |
|---|---|---|---|---|---|
| **Gemini CLI** | `~/.gemini/settings.json` | `GEMINI.md` | Native Platform Events (`AfterTool`, `PreCompress`) | Rich: `hook_event_name`, `tool_name`, `tool_response.llmContent` | **Smart Hook** |
| **Google Antigravity** | `~/.gemini/antigravity/mcp_config.json` | `AGENTS.md` | **NONE** (Relies on pure MCP) | N/A | **Unshielded** |
| **OpenCode** | `~/.opencode.json` | `AGENTS.md` | TypeScript Plugin (`.opencode/plugins/semantic-sift.ts`) | Rich: Synthesizes Gemini payload for `sift_hook.py`. | **Smart Hook** |
| **Cursor / Roo Code** | (Global config) | `.cursorrules`, `.clinerules` | `postToolUse` via `.cursor/hooks.json` | Blind: `{"result": "<raw_output>"}` | **Blind Hook** |
| **VS Code Copilot** | `~/.copilot/mcp-config.json` | `.github/copilot-instructions.md` | `PostToolUse` via `.github/hooks/semantic-sift.json` | Blind: `{"tool_response": {"llmContent": "<raw_output>"}}` | **Blind Hook** |
| **Windsurf** | (Global config) | `.windsurfrules` | **NONE** | N/A | **Unshielded** |
| **Claude Desktop** | `claude_desktop_config.json` | N/A | **NONE** | N/A | **Unshielded** |
| **Zed / Continue** | `settings.json` / `config.json` | N/A | **NONE** | N/A | **Unshielded** |
| **Kilo Code** | (Extension/CLI config) | `.clinerules` / Prompts | **NONE** (Standard MCP) | N/A | **Unshielded** |
| **Cline** | Project / Global | `.clinerules` | Formal Hooks (`PreToolUse`, `PostToolUse`) | Rich | **Smart Hook** |
| **OpenClaw** | Plugin System | `HOOK.md` | Native TypeScript Handlers (`tool:after`, `agent:reply`) | Rich | **Smart Hook** |
| **ForgeCode** | `AGENTS.md` / `SKILL.md` | `AGENTS.md` | System-Level Context Compaction | N/A | **Unshielded** |
| **Qwen CLI** | `~/.qwen/settings.json` | `QWEN.md` | Shell scripts (`PostToolUse`) | Assumed Rich | **Smart Hook** |
| **JetBrains** | `Settings | MCP Server` | Varies by Client | Relies on connecting client | Varies by Client | **Dependent** |

---

## 6. Vulnerability Classes & Mitigation Strategies

Based on the matrix, the ecosystem is divided into distinct vulnerability classes. Implementing Path-Native Tools requires addressing all simultaneously to prevent catastrophic loops or context flooding.

### Class A: Unshielded Environments (Windsurf, Claude Desktop, Zed, Kilo Code, Google Antigravity, ForgeCode)
*   **The Gap**: These platforms do not support post-tool execution hooks that intercept MCP output, or they rely entirely on native IDE tools (like Antigravity's `view_file`) which bypass MCP entirely. `sift_hook.py` will never run.
*   **The Threat**: If an agent on these platforms uses a standard reading tool, 100% of the raw text hits the context window. The original Auto-Sift Mandate is fundamentally flawed here because the context penalty is paid before the agent can react.
*   **The Fix**: `sift_onboard` must inject extremely aggressive instructions into the respective rule files (e.g., `.windsurfrules`, `AGENTS.md`) explicitly FORBIDDING the use of standard file reading tools for files over 1KB, mandating the new `sift_read_file` tool.

### Class B: Blind Hooks (Cursor, Roo Code, VS Code Copilot)
*   **The Gap**: These platforms support hooks, but they pipe the raw output to `sift_hook.py` without including the `tool_name`.
*   **The Threat (Double-Sifting)**: If an agent uses `sift_read_file`, the MCP server returns compressed text. The Blind Hook intercepts this. Because it lacks `tool_name`, it relies on heuristic sniffing (`len > 500`, `has_md_ext`). Since the sifted output usually contains Markdown, the hook will incorrectly identify it as raw prose and run it through semantic compression again (Double-Sifting).
*   **The Fix (Self-Aware Bypass)**: We CANNOT rely on `tool_name.startswith("sift_")` in the hook. Instead, `sift_read_file` and all MCP-side sifting tools MUST prepend their own audit header: `--- [Semantic-Sift Audit] ---`. `sift_hook.py` must scan `raw_content` for this header and instantly bypass processing. This ensures unified, deterministic bypassing across all platforms.

### Class C: Smart Hooks (Gemini CLI, OpenCode, Cline, OpenClaw, Qwen CLI)
*   **The Gap**: These platforms correctly provide the `tool_name` in the hook payload.
*   **The Threat**: While we *could* use `tool_name.startswith("sift_")` here, maintaining divergent bypass logic for different IDEs introduces severe maintenance overhead. Furthermore, hooks must not corrupt JSON outputs from other tools.
*   **The Fix**: Standardize on the Content-Signature Bypass (Class B fix) to ensure unified, deterministic bypassing across all hook-supported platforms. Implement a **Structured Data Exemption** in the hook (`isinstance(json.loads(raw_content), (dict, list))`) to protect Serena outputs.

---

## 7. Operational Synergies & Workflow Gaps

While resolving local file I/O friction is paramount, several missing workflows still force the agent into the "Read-then-React" token trap.

### Missing Synergies to Address:
1. **URI / Web Context (`sift_fetch_url`)**: 
   - *Gap:* Agents use `web_fetch`, polluting context with 20k+ chars of DOM boilerplate, then manually call `sift_doc`.
   - *Requirement:* A native URI-sifting tool to perform out-of-band web scraping and sifting.
2. **Git / Shell Context (`sift_shell_execute`)**:
   - *Gap:* Commands like `npm install`, `git diff`, or `pytest` generate massive terminal noise.
   - *Requirement:* A tool that wraps shell execution, capturing stdout into a sandbox, piping it through the heuristic sieve, and returning only critical errors/diffs.
3. **Context-Mode Integration**:
   - *Synergy:* Implementing `sift_read_file` allows an agent to pipe heavily distilled context into an indexer (e.g., `sift_read_file(path)` -> `ctx_index(content)`), minimizing the context footprint of the payload before it is indexed.
4. **Serena Tool Synergy (The "Find" Trap)**:
   - *Gap:* `mcp_serena_find_symbol` returns massive code blocks (strings). The hook treats tools with `find` as "Search/Ranking" tasks rather than "Prose". If `find_symbol` returns a 500-line class, the hook attempts to *rank* the lines instead of *sifting* the code.
   - *Workflow Fix:* `AGENTS.md` must explicitly instruct agents to manually pipe large `serena` string outputs through `sift_chat(rate=0.7)` to guarantee structural preservation.

## 8. Final Execution Strategy (Zero-Gap Implementation)
1. **Patch the Shields (Middleware Protocol)**: Implement Self-Aware Bypass in `sift_hook.py` so it ignores payloads containing `--- [Semantic-Sift Audit] ---`. Update `sift_hook.py` with Structured Data Exemptions. Update `sift_onboard` to verify hook compatibility.
2. **Build Path-Native Core**: Update `sift_kernel.py` with robust `load_file_content(path)` logic (handling UTF-8/Latin-1 encoding fallbacks).
3. **Expose Tools**: Add `sift_read_file` and `sift_analyze_file` to `server.py`, ensuring they prepend the Audit Header.
4. **Update Protocol**: Rewrite the Auto-Sift Mandate in all infused `.rules` files to strictly prioritize the new proactive tool suite over reactive sifting, particularly targeting "Unshielded" environments like Antigravity.
5. **Architectural Silence**: Silence the `context-pipe` orchestrator to remove redundant metadata and signatures, fulfilling the Sift-Centric model.