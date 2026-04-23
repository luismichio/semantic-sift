# Semantic-Sift: IDE & MCP Integration Wiki

This document serves as the master catalog for how various IDEs, AI coding assistants, and CLI agents handle Model Context Protocol (MCP) tool execution, middleware hooks, and rule configuration. 

Understanding these differences is **critical** for implementing robust tools like `semantic-sift` without causing infinite loops, context corruption, or double-processing.

---

## 1. The Core Architectural Challenges

When an AI agent executes a tool, middleware (like `sift_hook.py`) can intercept the output before it reaches the agent's context window. However, the ecosystem is highly fragmented, leading to several critical vulnerabilities:

*   **The "Blind Hook" vs. "Smart Hook" Gap**: Some environments pass the `tool_name` to the hook script (Smart), allowing for easy routing. Others only pass the raw output `{"result": "..."}` (Blind), making it impossible to know *which* tool generated the text without scanning the content itself.
*   **The "Double-Sifting" Threat**: If a path-native tool (e.g., `sift_read_file`) returns already-compressed text to a Blind Hook, the hook might mistakenly identify the compressed text as raw prose and run it through semantic compression *again*, destroying the data.
*   **The Data-Type Corruption Threat**: Hooks designed for natural language or code snippets will corrupt structured data (like JSON returns from Serena) if they attempt to heuristically or semantically prune it.
*   **The Pre-Tool Security Gateway**: Some IDEs allow users to block tools *before* they run. Custom MCP tools (like `sift_read_file`) will fail silently if the onboarding process doesn't explicitly whitelist them in these gateways.

---

## 2. Integration Matrix & Deep Dives

### Cursor & Roo Code
*   **Hook Mechanism**: Uses a `hooks.json` file (typically `.cursor/hooks.json`).
*   **Execution Lifecycle**: 
    *   `preToolUse` / `beforeMCPExecution`: Fires before tool use. Can block, allow, or ask for user confirmation. (Major risk for custom tools getting blocked by user security gateways).
    *   `postToolUse` / `afterMCPExecution`: Fires after tool use. 
*   **Payload Schema**: **Blind Hook**. Passes JSON via `stdin`, but typically omits the `tool_name` (e.g., `{"result": "<output>"}`).
*   **Rule Infusion**: Relies heavily on `.cursorrules` or `.clinerules`.
*   **Semantic-Sift Strategy**: Must use **Content-Signature Bypass** (`[Semantic-Sift: Native Execution]`) because `tool_name` is missing. Must audit `beforeMCPExecution` during onboarding.

### OpenCode
*   **Hook Mechanism**: Native TypeScript Plugins (`.opencode/plugins/`).
*   **Execution Lifecycle**: Hooks into `tool.execute.after`.
*   **Payload Schema**: **Smart Hook**. Provides rich context including `hook_event_name`, `tool_name`, and `tool_args`.
*   **Semantic-Sift Strategy**: Highly reliable. `sift_onboard` dynamically generates a TS plugin that easily bypasses loops via `if (input.tool.startsWith('sift_')) return;`.

### Gemini CLI
*   **Hook Mechanism**: Native platform event hooks (`AfterTool`, `PreCompress`).
*   **Execution Lifecycle**: Built directly into the CLI's agent loop.
*   **Payload Schema**: **Smart Hook**. Passes `tool_name`, `tool_args`, and `tool_response.llmContent`.
*   **Semantic-Sift Strategy**: Reliable execution. Supports advanced "Compaction" lifecycle events where `semantic-sift` can inject highly-compressed session summaries just before context window limits are reached.

### Google Antigravity
*   **Hook Mechanism**: **Unshielded**. It is a heavily modified IDE focused on multi-agent asynchronous orchestration. It relies purely on the MCP standard without specific post-tool shell hooks.
*   **Execution Lifecycle**: Agents execute tools directly via the integrated "Manager Surface".
*   **Payload Schema**: N/A.
*   **Semantic-Sift Strategy**: Because there is no intercepting hook, if an agent uses `view_file`, it will inevitably flood the context window (as seen in the original bug report). `sift_onboard` MUST inject strict, mandatory Auto-Sift directives into `AGENTS.md` to force the agent to use `sift_read_file` instead.

### Kilo Code
*   **Hook Mechanism**: **Unshielded**. Kilo Code is a popular open-source, BYOK fork of Cline available on VS Code/JetBrains/CLI. While it connects seamlessly to MCP, it does not currently employ the same formal `PostToolUse` deterministic shell scripts as Claude Code.
*   **Payload Schema**: N/A.
*   **Semantic-Sift Strategy**: High risk of context flooding during "Vibe Coding" sessions. Similar to Antigravity, defense relies entirely on `sift_onboard` injecting rules to use path-native tools.

### VS Code Copilot
*   **Hook Mechanism**: Uses `.github/hooks/semantic-sift.json`.
*   **Execution Lifecycle**: `PostToolUse` command execution.
*   **Payload Schema**: **Blind Hook**. Passes `{"tool_response": {"llmContent": "..."}}`.
*   **Semantic-Sift Strategy**: Same vulnerability as Cursor. Requires the **Content-Signature Bypass** to prevent double-sifting.

### Claude Code (Anthropic)
*   **Hook Mechanism**: Configured via `.claude/settings.json`.
*   **Execution Lifecycle**: Supports explicit `PreToolUse` and `PostToolUse` deterministic shell commands.
*   **Payload Schema**: Highly structured, supports regex matching for specific MCP tools (e.g., triggering only on `mcp__server__tool`).
*   **Semantic-Sift Strategy**: Powerful formatting and normalization capabilities, but requires explicit configuration during `sift_onboard`.

### Windsurf (Codeium / Cascade)
*   **Hook Mechanism**: Cascade Hooks configured via `mcp_config.json` or dashboard.
*   **Execution Lifecycle**: Shell commands that trigger on specific actions, cascading from System -> User -> Workspace levels.
*   **Semantic-Sift Strategy**: Strong enterprise policy enforcement. Requires specific onboarding checks to ensure workspace-level `sift_` hooks aren't overridden by system-level security blocks.

### Zed & Continue.dev
*   **Hook Mechanism**: **Unshielded**. These platforms primarily use MCP for context fetching (like Zed's Context7) and direct tool invocation. They currently lack a robust, deterministic post-tool shell-hook architecture comparable to Cursor or Claude Code.
*   **Payload Schema**: N/A.
*   **Semantic-Sift Strategy**: High risk of context flooding. Because there is no middleware interceptor, `sift_onboard` MUST inject extremely aggressive, mandatory rules into `AGENTS.md` to force the LLM to use `sift_read_file` instead of standard file readers.

### Cline
*   **Hook Mechanism**: Uses formal lifecycle hooks configured via project-specific (`.clinerules/hooks/`) or global directories.
*   **Execution Lifecycle**: `PreToolUse` (blocking/validation), `PostToolUse` (reactive/formatting), and `Notification`.
*   **Payload Schema**: Varies based on configuration but supports active middleware intervention (e.g., rejecting actions).
*   **Rule Infusion**: Managed via `.clinerules`.
*   **Semantic-Sift Strategy**: Must ensure rules injected via `sift_onboard` are prioritized. `PostToolUse` hooks can be configured to call the `semantic-sift` python binary, but must employ Content-Signature Bypasses.

### JetBrains (IntelliJ IDEA, PyCharm, WebStorm)
*   **Hook Mechanism**: Built-in MCP server (2025.2+) with plugin extension points. Connecting clients (Claude Code, Qoder) implement the actual hooks.
*   **Execution Lifecycle**: Executes IDE-native tools like `execute_terminal_command`. Intercepted by the client's `PreToolUse`/`PostToolUse` logic.
*   **Payload Schema**: Dependent entirely on the connecting client (e.g., Claude Code schema).
*   **Semantic-Sift Strategy**: High risk of terminal noise (`execute_terminal_command`). If the client lacks a hook, `sift_onboard` must configure aggressive prompt rules or recommend installing a `semantic-sift` compatible client.

### OpenClaw
*   **Hook Mechanism**: Native plugin system using `HOOK.md` and TypeScript handlers.
*   **Execution Lifecycle**: Extensive coverage: `before_tool_call`, `tool:after`, `agent:prompt`, and `agent:reply`.
*   **Payload Schema**: **Smart Hook**. Rich, structured interception.
*   **Semantic-Sift Strategy**: Highest synergy potential. A native OpenClaw plugin can intercept `tool:after` to sift output and even `agent:reply` to ensure final output is pristine.

### ForgeCode
*   **Hook Mechanism**: Primarily managed via `AGENTS.md` (or `SKILL.md`) prompt directives, or internal custom MCP server logic.
*   **Execution Lifecycle**: Does not heavily rely on deterministic shell scripts for hooks. It features a system-level "Context Compaction" hook that triggers when token limits are reached.
*   **Payload Schema**: N/A for standard hooks.
*   **Semantic-Sift Strategy**: `sift_onboard` must aggressively target `AGENTS.md` to establish the Auto-Sift Mandate. The system-level Compaction feature makes the `sift_chat` tool highly relevant for out-of-band summarization before ForgeCode hits its limits.

### Qwen CLI (Qwen Code)
*   **Hook Mechanism**: Highly compatible with Claude Code/Gemini CLI. Uses deterministic shell scripts for `PreToolUse` and `PostToolUse`.
*   **Execution Lifecycle**: Supports blocking tools via exit codes (e.g., `exit 2`).
*   **Payload Schema**: Assumed **Smart Hook** due to its architectural shared roots with Claude Code and Gemini CLI, passing JSON via `stdin`.
*   **Rule Infusion**: Looks for `QWEN.md` in the project root.
*   **Semantic-Sift Strategy**: `sift_onboard` must target `QWEN.md` and configure the `.qwen/settings.json` hook definitions identically to Claude Code, ensuring Content-Signature Bypasses are respected.

---

## 3. The Universal Implementation Strategy (Zero-Gap)

To build tools that survive across this fragmented ecosystem, `semantic-sift` adheres to the following universal design principles:

### A. The Content-Signature Bypass
Because **Cursor** and **VS Code** are "Blind Hooks," middleware cannot safely rely on checking if `tool_name == "sift_read_file"`.
*   **Rule**: ALL native sifting tools running on the MCP server MUST prepend a unique string to their output: `--- [Semantic-Sift: Native Execution] ---`
*   **Implementation**: `sift_hook.py` must scan `raw_content` for this exact string and instantly `return` to prevent Double-Sifting.

### B. Structured Data Exemption
Middleware must never corrupt JSON or machine-readable outputs.
*   **Rule**: `sift_hook.py` must attempt to parse `raw_content` using `json.loads()`. If successful **AND** the resulting data is a complex structure (`isinstance(parsed_data, (dict, list))`), it must bypass semantic compression (BERT), as compression will destroy the JSON keys and syntax. This prevents false positives on valid JSON primitives like `"true"` or `"string"`.

### C. The Proactive "Path-Native" Mandate
Because platforms like **Zed** and **Continue** are "Unshielded" (no middleware), relying on interceptors is fundamentally flawed.
*   **Rule**: The primary defense against context flooding is Proactive Path-Native execution. Agents must be heavily instructed via `AGENTS.md` to use `sift_read_file(path)` and `sift_analyze_file(path)` for all local I/O, shifting the token burden entirely to the server side.

### D. Setup Verification (`sift_onboard`)
Onboarding cannot just append text to a `.cursorrules` file.
*   **Rule**: `sift_onboard` must act as an active auditor. It must scan IDE configuration files for `preToolUse` / `beforeMCPExecution` security gateways and alert the user if custom `sift_` tools are not whitelisted. It must also scan agent rule files to detect and override contradictory instructions (e.g., "always read the full file").
