# Semantic-Sift: Integration Encyclopedia

This document serves as the master compatibility map and payload specification authority for the Semantic-Sift system. It details how the system integrates across a highly fragmented ecosystem of IDEs, AI coding assistants, and CLI agents, preventing infinite loops, context corruption, and double-processing.

---

## 1. Supported Environments & Compatibility Map

The ecosystem of MCP clients falls into specific architectural categories regarding how they handle tool execution and middleware interception.

### Explicitly Supported (Smart & Blind Hooks)
These environments have dedicated logic implemented in `sift_hook.py` for payload extraction and reinjection, as well as onboarding logic in `server.py`.

*   **Gemini CLI**: 
    *   **Architecture**: Native platform event hooks (`AfterTool`, `PreCompress`). 
    *   **Hook Type**: Smart Hook. Passes explicit event names and tool arguments.
    *   **Support**: Full support for standard sifting and lifecycle "Compaction" events.
*   **Claude Code, Qwen CLI & Codex CLI**:
    *   **Architecture**: `PostToolUse` deterministic shell command execution with regex matching (`mcp__.*__.*`).
    *   **Hook Type**: Smart Hook. Passes explicit context via environment variables (e.g., `$CLAUDE_TOOL_NAME`, `$QWEN_TOOL_NAME`, `$CODEX_TOOL_NAME`).
    *   **Support**: Injected into `~/.claude/settings.json`, `~/.qwen/settings.json`, or `~/.codex/settings.json`.
*   **VS Code (Copilot)**:
    *   **Architecture**: `PostToolUse` shell command execution.
    *   **Hook Type**: Blind Hook. Relies on checking for the `tool_response.llmContent` payload structure.
    *   **Support**: Injected into `.github/hooks/semantic-sift.json`.
*   **Cursor & Roo Code**:
    *   **Architecture**: `postToolUse` and `beforeMCPExecution` triggers via `hooks.json`.
    *   **Hook Type**: Blind Hook. Passes JSON via standard input, omitting `tool_name`.
    *   **Support**: Merges hook execution commands into `.cursor/hooks.json`. Relies on the **Content-Signature Bypass** to prevent double-sifting.
*   **OpenCode & OpenClaw**:
    *   **Architecture**: Native TypeScript Plugins.
    *   **Hook Type**: Smart Hook. Hooks into `tool.execute.after` (OpenCode) or `api.on("tool:after")` (OpenClaw).
    *   **Support**: Generates custom TypeScript wrappers at `.opencode/plugins/semantic-sift.ts` or `.openclaw/plugins/semantic-sift.ts`.
*   **Windsurf & Cline**:
    *   **Architecture**: Security Gateway.
    *   **Hook Type**: Blocking Hook. Triggers on `pre_mcp_tool_use` (Windsurf) or via `PreToolUse` executable (Cline).
    *   **Support**: Injected into `.windsurf/hooks.json` or `.clinerules/hooks/`. Automatically blocks native file readers > 1KB to force the use of `sift_read_file`.

### Unshielded / Instruction-Reliant Environments
These platforms lack robust post-tool shell hooks or act as pass-throughs. They rely entirely on `sift_onboard` injecting mandatory rules into their system prompts to force the agent to use `sift_read_file` instead of standard file readers.

*   **Google Antigravity**: Relies on `AGENTS.md` and `GEMINI.md` rule injections.
*   **Zed & Continue.dev**: Relies on aggressive prompt rules in `AGENTS.md`.
*   **JetBrains (IDE AI Assistant & Junie CLI)**: Both environments are currently unshielded. Defense relies on the **Path-Native Mandate** in `AGENTS.md`.
*   **Kilo Code**: Relies on prompt injection via `.kilocode/rules/context.md`.
*   **ForgeCode**: System-level "Context Compaction" hook. Managed via `AGENTS.md` directives.

---

## 2. Hook Injector & Onboarding Logic (`server.py`)

The `sift_onboard` tool acts as the automated configuration engine, ensuring that all available security gateways, hook registries, and agent instruction files are primed for Semantic-Sift.

### A. Instruction File Modification
The `update_instruction_files` function targets specific files to enforce the "Path-Native" mandate and MCP Synergy Matrix.
*   **Targets**: `AGENTS.md`, `GEMINI.md`, `.clinerules`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`, `.kilocode/rules/context.md`.
*   **Mandate Injection**: Injects a strict Markdown block demanding the use of `sift_read_file` for files > 1KB and providing recipes for Web, Logs, and Search data.

### B. Security Gateway Auditing
*   Scans `.cursor/hooks.json` for `beforeMCPExecution` gateways. If detected, issues a critical alert requiring the user to whitelist sifting tools.

### C. Automated Hook Injection
Safely merges execution commands into existing IDE configurations:
*   **Post-Tool Shell Hooks**: Injects `sift_hook.py` into Cursor, VS Code, Claude Code, Qwen CLI, and Codex CLI.
*   **Pre-Tool Security Gateways**: Injects blocking logic into Windsurf (`hooks.json`) and Cline (`.clinerules/hooks/PreToolUse.ps1`).
*   **Native Plugins**: Generates TypeScript wrappers for OpenCode and OpenClaw.

---

## 3. Payload Structures & Interception Logic (`sift_hook.py`)

### 1. Smart Hooks (CLI Agents & Plugins)
*   **Gemini/OpenCode/OpenClaw**: Detects `AfterTool` or `Compacting` event names. Extracts `tool_response.llmContent`.
*   **Claude/Qwen/Codex**: Checks environment variables (`$CLAUDE_TOOL_NAME`, etc.). Extracts the raw tool output from standard input.
*   **Reinjection**: Injects a notification into Gemini's `additionalContext` or prepends `--- [Distilled by Semantic-Sift] ---` to the text result.

### 2. Blind Hooks (IDEs)
*   **VS Code & Cursor**: Scans the incoming JSON for keys like `result` or `tool_response.llmContent`.
*   **Reinjection**: Overwrites the found key with the distilled text, often prepending `[Sifted]`.

---

## 4. The Content-Signature Bypass

To prevent "Double-Sifting" (running BERT on already-compressed text):
1.  Native MCP tools in `server.py` prepend their output with: `\n\n--- [Semantic-Sift: Native Execution] ---`.
2.  `sift_hook.py` explicitly scans `raw_content` for `--- [Semantic-Sift Audit] ---`. If found, it instantly bypasses all processing.

---

## 5. Master Configuration Matrix (MCP Server Installation)

| Software | Configuration Path (Parsed by Server) | Target Key | Expected Schema Style |
| :--- | :--- | :--- | :--- |
| **Claude Desktop** | `~/AppData/Roaming/Claude/claude_desktop_config.json` | `mcpServers` | Standard |
| **Claude Code** | `~/.claude/settings.json` | `mcp_servers` | Standard |
| **Qwen CLI** | `~/.qwen/settings.json` | `mcp_servers` | Standard |
| **Codex CLI** | `~/.codex/mcp-config.json` | `mcpServers` | Standard |
| **Junie CLI** | `~/.junie/mcp/mcp.json` | `mcpServers` | Standard |
| **Continue.dev** | `~/.continue/config.json` | `mcpServers` | Unified |
| **Zed** | `~/.config/zed/settings.json` | `context_servers` | Standard |
| **VS Code Copilot**| `~/.copilot/mcp-config.json` | `mcpServers` | Standard |
| **OpenCode** | `~/.opencode.json` | `mcpServers` | Local Array |
| **Google Antigravity**| `~/.gemini/antigravity/mcp_config.json` | `mcpServers` | Standard |

### A. Standard Schema (Gemini, Claude, Cursor, Copilot, Zed, Codex, Junie)
```json
"semantic-sift": {
  "command": "python",
  "args": ["/absolute/path/to/server.py"]
}
```

### B. Local Array Schema (OpenCode, Kilo Code)
```json
"semantic-sift": {
  "type": "local",
  "command": ["python", "/absolute/path/to/server.py"]
}
```

### C. Extended Schema (Cline / Roo Code)
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
```json
"semantic-sift": {
  "type": "stdio",
  "command": "python",
  "args": ["server.py"]
}
```
