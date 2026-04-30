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
*   **Official Docs**: [Cursor Docs](https://docs.cursor.com) / [Roo Code Docs](https://docs.roocode.com)
*   **Hook Mechanism**: Uses a `hooks.json` file (typically `.cursor/hooks.json`).
*   **Execution Lifecycle**: 
    *   `preToolUse` / `beforeMCPExecution`: Fires before tool use. Can block, allow, or ask for user confirmation. (Major risk for custom tools getting blocked by user security gateways).
    *   `postToolUse` / `afterMCPExecution`: Fires after tool use. 
*   **Payload Schema**: **Blind Hook**. Passes JSON via `stdin`, but typically omits the `tool_name` (e.g., `{"result": "<output>"}`).
*   **Rule Infusion**: Relies heavily on `.cursorrules` or `.clinerules`.
*   **Semantic-Sift Strategy**: Must use **Content-Signature Bypass** (`[Semantic-Sift: Native Execution]`) because `tool_name` is missing. Must audit `beforeMCPExecution` during onboarding.
*   **Subagents & Multi-Agent**: Uses an Orchestrator-Worker model. Subagents (Workers) are defined via Markdown files in `.cursor/agents/`. They have isolated contexts but inherit global **Lifecycle Hooks** from `.cursor/hooks.json`, ensuring subconscious sifting applies to subagent edits.

### OpenCode
*   **Official Docs**: [OpenCode Documentation](https://opencode.ai/docs/mcp-servers/)
*   **Hook Mechanism**: Native TypeScript Plugins (`.opencode/plugins/`).
*   **Execution Lifecycle**: Hooks into `tool.execute.after`.
*   **Payload Schema**: **Smart Hook**. Provides rich context including `hook_event_name`, `tool_name`, and `tool_args`.
*   **Config Schema**: **Strict Local Array**. Unlike Gemini, OpenCode requires `"type": "local"` and expects the executable and arguments to be combined into a single `"command": []` array.
*   **Semantic-Sift Strategy**: Highly reliable. `sift_onboard` dynamically generates a TS plugin that easily bypasses loops via `if (input.tool.startsWith('sift_')) return;`.
*   **Subagents & Multi-Agent**: Plugin-driven architecture. A spawned subagent triggers the same `tool.execute.after` hooks as the parent, providing consistent shielding across all agent threads.

### Gemini CLI
*   **Official Docs**: [Gemini CLI Documentation](https://geminicli.com)
*   **Hook Mechanism**: Native platform event hooks (`AfterTool`, `PreCompress`).
*   **Execution Lifecycle**: Built directly into the CLI's agent loop.
*   **Payload Schema**: **Smart Hook**. Passes `tool_name`, `tool_args`, and `tool_response.llmContent`.
*   **Semantic-Sift Strategy**: Reliable execution. Supports advanced "Compaction" lifecycle events where `semantic-sift` can inject highly-compressed session summaries just before context window limits are reached.
*   **Subagents & Multi-Agent**: Uses YAML-frontmatter Markdown agents in `.gemini/agents/`. Subagents **inherit the entire parent toolset** (including all MCP servers) by default. They can also define **Inline MCP Servers** private to the subagent thread.

### Google Antigravity
*   **Official Docs**: [Antigravity IDE](https://antigravity.google)
*   **Hook Mechanism**: **Unshielded**. It is a heavily modified IDE focused on multi-agent asynchronous orchestration. It relies purely on the MCP standard without specific post-tool shell hooks.
*   **Execution Lifecycle**: Agents execute tools directly via the integrated "Manager Surface".
*   **Payload Schema**: N/A.
*   **Semantic-Sift Strategy**: Because there is no intercepting hook, if an agent uses `view_file`, it will inevitably flood the context window (as seen in the original bug report). `sift_onboard` MUST inject strict, mandatory Auto-Sift directives into `AGENTS.md` to force the agent to use `sift_read_file` instead.
*   **Subagents & Multi-Agent**: Antigravity is a native multi-agent environment. Subagents inherit the full parent toolset by default. Directives injected into `AGENTS.md` are critical as they are the primary mechanism to enforce context sanitation across asynchronous agent threads.
*   **Telemetry Identity**: Antigravity's process environment inherits `VSCODE_PID` from its VS Code framework host. `telemetry_core.detect_client_id()` checks `ANTIGRAVITY_AGENT`, `ANTIGRAVITY_EDITOR_APP_ROOT`, and `ANTIGRAVITY_TRAJECTORY_ID` **before** `VSCODE_PID`, ensuring MCP tool calls are attributed to `"Google Antigravity"` rather than `"VSCode"`. If none of the Antigravity env vars are set in a given subprocess, attribution falls back to `"Generic CLI"` — this is a runtime env contract that `semantic-sift` cannot enforce unilaterally.

### Kilo Code
*   **Official Docs**: [Kilo Code Documentation](https://kilo.ai)
*   **Hook Mechanism**: **Unshielded**. Kilo Code lacks native deterministic shell hooks for MCP out-of-the-box.
*   **Semantic-Sift Strategy**: Rule Infusion. `sift_onboard` generates a strict `.kilocode/rules/context.md` file containing the explicit MCP Synergy Matrix and Path-Native mandates to shield the context window manually.
*   **Subagents & Multi-Agent**: Limited native subagent spawning. Rely on shared rule files (`.kilocode/rules/`) to ensure any parallel tasks follow the context sanitation protocol.

### VS Code Copilot
*   **Official Docs**: [VS Code Copilot Documentation](https://code.visualstudio.com/docs/copilot)
*   **Hook Mechanism**: Uses `.github/hooks/semantic-sift.json`.
*   **Execution Lifecycle**: `PostToolUse` command execution.
*   **Payload Schema**: **Blind Hook**. Passes `{"tool_response": {"llmContent": "..."}}`.
*   **Semantic-Sift Strategy**: Same vulnerability as Cursor. Requires the **Content-Signature Bypass** to prevent double-sifting.
*   **Subagents & Multi-Agent**: Spawns internal background workers for indexing and symbol retrieval. While these are not user-defined subagents, the `PostToolUse` hook ensures that any tool output they generate is intercepted and distilled before reaching the primary model's context.

### Claude Code (Anthropic)
*   **Official Docs**: [Claude Code Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
*   **Hook Mechanism**: Uses a deterministic `PostToolUse` shell script configured via `~/.claude/settings.json` or `.claude/settings.json`.
*   **Execution Lifecycle**: Supports explicit `PreToolUse` (blocking) and `PostToolUse` (reactive/formatting) hooks.
*   **Payload Schema**: **Smart Hook**. Passes explicit context like `$CLAUDE_TOOL_NAME` via environment variables and accepts modified output via `stdout`.
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` automatically injects a `PostToolUse` array matching `"mcp__.*__.*"` to invoke the `sift_hook.py` interceptor.
*   **Subagents & Multi-Agent**: Utilizes sub-agents for complex task decomposition. Sub-agents inherit the session's configuration layers, meaning the global `PostToolUse` hooks are automatically active for all child processes.

### OpenClaw
*   **Official Docs**: [OpenClaw Hooks Documentation](https://openclaw.ai)
*   **Hook Mechanism**: Native plugin system via `api.on("tool:after")`.
*   **Execution Lifecycle**: Extensive coverage including `tool:after` for payload modification.
*   **Payload Schema**: **Smart Hook**. Provides rich context (e.g. `ctx.toolName`, `ctx.result`).
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` generates a native `.openclaw/plugins/semantic-sift.ts` plugin wrapper that intercepts the `tool:after` event and pipes it through the Python interceptor.

### Codex CLI (OpenAI)
*   **Official Docs**: [Codex CLI Hooks](https://developers.openai.com/codex/hooks)
*   **Hook Mechanism**: Uses deterministic `PreToolUse` and `PostToolUse` shell scripts configured via `~/.codex/settings.json`.
*   **Execution Lifecycle**: Identical to Claude Code. Supports blocking tools and modifying outputs via standard streams.
*   **Payload Schema**: **Smart Hook**. Passes context like `$CODEX_TOOL_NAME` via environment variables.
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` automatically injects a `PostToolUse` array matching `"mcp__.*__.*"` to invoke the `sift_hook.py` interceptor.
*   **Subagents & Multi-Agent**: Official support for subagents via `.codex/agents/*.toml`. Subagents **inherit MCP server configurations and hooks** from the parent session by default, ensuring subconscious sifting is active across all specialized agent threads.

### ForgeCode
*   **Official Docs**: N/A (Internal / Proprietary orchestration)
*   **Hook Mechanism**: Primarily managed via `AGENTS.md` (or `SKILL.md`) prompt directives, or internal custom MCP server logic.
*   **Execution Lifecycle**: Does not heavily rely on deterministic shell scripts for hooks. It features a system-level "Context Compaction" hook that triggers when token limits are reached.
*   **Payload Schema**: N/A for standard hooks.
*   **Semantic-Sift Strategy**: `sift_onboard` must aggressively target `AGENTS.md` to establish the Auto-Sift Mandate. The system-level Compaction feature makes the `sift_chat` tool highly relevant for out-of-band summarization before ForgeCode hits its limits.
*   **Subagents & Multi-Agent**: Proprietary multi-agent orchestration. Relies on the global `AGENTS.md` directives to ensure that any spawned sub-processes follow the context sanitation protocol.

### Qwen CLI (Qwen Code)
*   **Official Docs**: N/A (Relies on Claude Code architectural compatibility)
*   **Hook Mechanism**: Uses a deterministic `PostToolUse` shell script configured via `~/.qwen/settings.json` or `.qwen/settings.json`.
*   **Execution Lifecycle**: Supports blocking tools via exit codes and modifying outputs via standard out.
*   **Payload Schema**: **Smart Hook**. Passes explicit context like `$QWEN_TOOL_NAME` via environment variables and standard in.
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` automatically injects a `PostToolUse` array identically to Claude Code to invoke the `sift_hook.py` interceptor.
*   **Subagents & Multi-Agent**: Multi-agent decomposition. Like Claude Code, sub-agents inherit the global `PostToolUse` hooks, providing consistent context shielding.

### Windsurf (Codeium / Cascade)
*   **Official Docs**: [Windsurf Hooks Documentation](https://windsurf.com)
*   **Hook Mechanism**: Cascade Hooks configured via `.windsurf/hooks.json`.
*   **Execution Lifecycle**: Triggered via `pre_mcp_tool_use`. Uses shell exit codes (e.g., `exit 2`) to block execution.
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` injects a Security Gateway hook that automatically blocks standard MCP file readers (`read_file`, `view_file`) if the file size exceeds 1KB, advising the agent via `stderr` to use `sift_read_file` instead.
*   **Subagents & Multi-Agent**: Utilizes a sophisticated Orchestrator-Worker architecture (e.g. Planning vs. Coder agents). Hooks in `hooks.json` apply to the entire session, ensuring the security gateway blocks native reading for all background sub-agents.

### Cline
*   **Official Docs**: [Cline Customization & Hooks](https://docs.cline.bot/customization/hooks)
*   **Hook Mechanism**: Executable files in `.clinerules/hooks/` (e.g., `PreToolUse.ps1` or `PreToolUse`).
*   **Execution Lifecycle**: Uses standard streams (stdin/stdout) exchanging strict JSON (`{"cancel": boolean}`). It does not allow mutating the actual tool output strings via `PostToolUse`.
*   **Payload Schema**: **Smart Hook**. Passes explicit context via standard streams.
*   **Semantic-Sift Strategy**: Explicitly supported. `sift_onboard` generates a `PreToolUse` security gateway hook that blocks native file readers (`read_file`, `view_file`) if the file size exceeds 1KB, forcing the agent to use `sift_read_file` instead.
*   **Subagents & Multi-Agent**: Supports "Parallel Tasks" and sub-agents. The executable hooks in `.clinerules/hooks/` are session-wide and trigger for all tool calls, providing unified enforcement of the sifting protocol.

### Zed & Continue.dev
*   **Official Docs**: [Zed AI Documentation](https://zed.dev/docs) / [Continue.dev Documentation](https://docs.continue.dev)
*   **Hook Mechanism**: **Unshielded**. These platforms primarily use MCP for context fetching and direct tool invocation. They currently lack robust, deterministic post-tool shell-hook architectures.
*   **Semantic-Sift Strategy**: Rule Infusion. `sift_onboard` MUST inject extremely aggressive, mandatory rules into `AGENTS.md` to force the LLM to use `sift_read_file` instead of standard file readers.
*   **Subagents & Multi-Agent**:
    *   **Zed**: Uses the Agent Client Protocol (ACP) for multi-agent orchestration. MCP servers (and thus Sift tools) are shared across all active agent threads. **Telemetry implication**: because all agents share one MCP server process, `SIFT_CLIENT_ID` is frozen at server launch and reflects whichever agent's environment was present at that moment. In mixed-agent sessions (e.g., Gemini CLI + OpenCode running simultaneously in Zed), MCP tool calls (`sift_chat`, `sift_read_file`, etc.) will all report the same startup-time identity. This is a known shared-server limitation — see `doc/TELEMETRY_SPEC.md §4` for details.
    *   **Continue**: Features a `subagent` tool for task delegation. Each subagent has an isolated context window but shares access to the parent's MCP registry.

### JetBrains (IntelliJ IDEA, PyCharm, WebStorm & AI Assistant)
*   **Official Docs**: [JetBrains MCP Documentation](https://www.jetbrains.com/help/idea/mcp-server.html)
*   **Hook Mechanism**: **Unshielded**. The JetBrains AI Assistant (Client) connects via internal Settings UI. Connecting to JetBrains as a Server relies on external clients (like Claude Code) implementing hooks.
*   **Semantic-Sift Strategy**: High risk of terminal noise. Because there are no internal `sift_hook.py` interceptors available, `sift_onboard` must configure aggressive prompt rules (Path-Native Mandate) in `AGENTS.md` to force the AI Assistant to use `sift_read_file`.
*   **Subagents & Multi-Agent**: Support for specialized sub-agents defined in `.junie/agents/` or `.agents/`. They inherit the `AGENTS.md` mandates, ensuring consistent context sanitation across agent threads.

### JetBrains Junie (CLI Agent)
*   **Official Docs**: [Junie Documentation](https://www.jetbrains.com/junie/)
*   **Hook Mechanism**: **Unshielded**. The Junie autonomous CLI agent currently lacks a native deterministic shell hook like Claude Code's `PostToolUse`.
*   **Semantic-Sift Strategy**: Rule Infusion. `sift_onboard` relies on injecting the explicit MCP Synergy Matrix and Path-Native mandates directly into workspace files like `AGENTS.md` to manually shield the context window.
*   **Subagents & Multi-Agent**: Inherits mandates from the global/workspace `AGENTS.md`, providing a unified reasoning base for any spawned tasks.

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

### D. Trace-Verified Reliability (OTel)
To ensure the telemetry math is honest and debuggable across all IDEs:
*   **Echo-Detector**: All middleware (Python/Node) uses a shared disk-based hash cache to detect if the same content was already sifted.
*   **Chain of Custody**: Every data transformation is wrapped in an **OpenTelemetry** span, proving exactly where characters were removed in the pipeline.

### E. Setup Verification (`sift_onboard`)

---

## 4. Master Configuration Matrix (By Software)

This section provides the exact file paths and schema requirements for each platform to ensure a zero-gap connection.

| Software | Config File Location (Default) | Transport Key | Schema Style |
| :--- | :--- | :--- | :--- |
| **Cursor** | `.cursor/mcp.json` | `mcpServers` | Standard |
| **Gemini CLI**| `.gemini/settings.json` | `mcpServers` | Standard |
| **OpenCode** | `opencode.json` | `mcp` | Local Array |
| **Cline** | `cline_mcp_settings.json` | `mcpServers` | Extended |
| **Continue** | `config.yaml` / `config.json` | `mcpServers` | Unified |
| **Windsurf** | `mcp_config.json` | `mcpServers` | Unified |
| **Codex CLI** | `config.toml` | `[mcp_servers]` | TOML |
| **Kilo Code** | `.kilocode/mcp.json` | `mcpServers` | Local Array |
| **Zed** | `settings.json` | `context_servers` | Standard |
| Claude Code| `.claude/settings.json` | `mcp_servers` | Standard |
| **Junie CLI**| `~/.junie/mcp/mcp.json` or `.junie/mcp/mcp.json` | `mcpServers` | Standard |
| **Codex CLI**| `~/.codex/settings.json` or `.codex/settings.json` | `mcpServers` | Standard |

---

### A. Standard Schema (Cursor, Gemini, Zed, Roo Code, VS Code)
```json
"semantic-sift": {
  "type": "stdio",
  "command": "python",
  "args": ["/path/to/semantic-sift/server.py"]
}
```
> Use `python3` on Linux/macOS or the full path to your interpreter if `python` is not on PATH. No venv path required — `pip install .` makes the package available to whichever interpreter you point to.

### B. Local Array Schema (OpenCode, Kilo Code)
**MANDATORY**: Combine executable and script into one `command` array. **Do not use `args` key.**
```json
"semantic-sift": {
  "type": "local",
  "command": [
    "python",
    "/path/to/semantic-sift/server.py"
  ]
}
```

### C. Extended Schema (Cline / Roo Code)
Includes `autoApprove` to prevent manual confirmation loops during sifting.
```json
"semantic-sift": {
  "command": "python",
  "args": ["server.py"],
  "autoApprove": ["sift_read_file", "sift_analyze_file", "sift_logs", "sift_chat"]
}
```

### D. TOML Schema (Codex CLI)
```toml
[mcp_servers.semantic-sift]
command = "python"
args = ["server.py"]
```

### E. Unified Schema (Continue, Windsurf)
Requires explicit `type: "stdio"` in the object or YAML block.
```json
{
  "name": "semantic-sift",
  "type": "stdio",
  "command": "python",
  "args": ["server.py"]
}
```