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
    *   **Support**: Full support for standard sifting and lifecycle "Compaction" events. Discovers config at `~/.gemini/settings.json`.
*   **VS Code (Copilot)**:
    *   **Architecture**: `PostToolUse` shell command execution.
    *   **Hook Type**: Blind Hook. Relies on checking for the `tool_response.llmContent` payload structure.
    *   **Support**: Injects hooks into `.github/hooks/semantic-sift.json`. Discovers MCP config at `~/.copilot/mcp-config.json` or `.copilot/mcp-config.json`.
*   **Cursor & Roo Code**:
    *   **Architecture**: `postToolUse` and `beforeMCPExecution` triggers via `hooks.json`.
    *   **Hook Type**: Blind Hook. Passes JSON via standard input, omitting `tool_name` (extracts from `result`).
    *   **Support**: Merges hook execution commands into `.cursor/hooks.json`. Relies on the **Content-Signature Bypass** (`--- [Semantic-Sift: Native Execution] ---`) to prevent double-sifting.
*   **OpenCode**:
    *   **Architecture**: Native TypeScript Plugins.
    *   **Hook Type**: Smart Hook. Hooks into `tool.execute.after`.
    *   **Support**: Generates a custom TypeScript wrapper at `.opencode/plugins/semantic-sift.ts`. Discovers config at `~/.opencode.json` or `.opencode.json`.

### Unshielded / Instruction-Reliant Environments
These platforms either lack robust post-tool shell hooks or act as pass-throughs in `sift_hook.py`. They rely entirely on `sift_onboard` injecting mandatory rules into their system prompts to force the agent to use `sift_read_file` instead of standard file readers.

*   **Google Antigravity**: Discovers MCP config at `~/.gemini/antigravity/mcp_config.json`. Relies on `AGENTS.md` and `GEMINI.md` rule injections.
*   **Claude Desktop / Claude Code**: Discovers config at `~/AppData/Roaming/Claude/claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).
*   **Windsurf (Codeium / Cascade)**: Relies on rules injected into `.windsurfrules`.
*   **Zed & Continue.dev**: Discovers config at `~/.config/zed/settings.json`, `.zed/settings.json`, and `~/.continue/config.json`. High risk of context flooding; relies on aggressive prompt rules.
*   **Cline**: Rule infusion managed via `.clinerules`.
*   **Kilo Code**: Relies on prompt injection to prevent "Vibe Coding" context floods.
*   **JetBrains (IntelliJ IDEA, PyCharm, WebStorm)**: Dependent on the connecting client (e.g., Claude Code).
*   **OpenClaw**: Passes through `sift_hook.py` transparently. Can utilize native plugins via `HOOK.md` and `tool:after` / `agent:reply` handlers.
*   **ForgeCode**: System-level "Context Compaction" hook. Managed via `AGENTS.md` directives.
*   **Qwen CLI (Qwen Code)**: Passes through `sift_hook.py` transparently. Relies on instruction files like `QWEN.md`.

---

## 2. Hook Injector & Onboarding Logic (`server.py`)

The `sift_onboard` tool acts as the automated configuration engine, ensuring that all available security gateways, hook registries, and agent instruction files are primed for Semantic-Sift.

### A. Instruction File Modification
The `update_instruction_files` function targets specific files to enforce the "Path-Native" mandate.
*   **Targets (`INSTRUCTION_TARGETS`)**: `AGENTS.md`, `GEMINI.md`, `.clinerules`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`, `.cursor/hooks.json`, `.github/hooks/semantic-sift.json`.
*   **Mandate Injection**: Injects a strict Markdown block (`<!-- SIFT_SECTION_START:SOP -->`) demanding the use of `sift_read_file` and `sift_analyze_file` for files > 1KB. It also injects an **MCP Synergy Matrix**, which provides explicit prompt-engineering guidelines for the agent to manually apply the correct sifting tools (`sift_doc`, `sift_logs`, `sift_rank`) when receiving data from external MCP servers (e.g., Puppeteer, Postgres, AWS).
*   **Rule Auditing**: Scans these files for contradictory instructions (e.g., "always use view_file", "read the full file"). If found, it appends a warning to the onboarding report and overrides them.

### B. Security Gateway Auditing
*   Scans `.cursor/hooks.json` for `beforeMCPExecution` gateways. If detected, issues a critical alert requiring the user to manually whitelist `sift_read_file` and `sift_analyze_file` to prevent silent execution failures.

### C. Automated Hook Injection
Safely merges the execution command (`python.exe sift_hook.py`) into existing IDE configurations without overwriting other tools:
*   **Cursor**: Merges into `postToolUse` array in `.cursor/hooks.json` (schema `version: 1`).
*   **VS Code (Copilot)**: Merges into `PostToolUse` array with `{"type": "command"}` in `.github/hooks/semantic-sift.json`.
*   **OpenCode**: Dynamically generates and writes a complete TypeScript plugin (`SemanticSiftPlugin`) to `.opencode/plugins/semantic-sift.ts`. This plugin intercepts `tool.execute.after`, constructs a `hook_event_name: "AfterTool"` payload, shells out to `sift_hook.py`, and re-assigns `output.result`.

---

## 3. Payload Structures & Interception Logic (`sift_hook.py`)

The `sift_hook.py` script receives data via `stdin` and writes the modified JSON to `stdout`. Because the input structures vary wildly by IDE, the hook implements specific extraction and reinjection mapping.

### 1. Gemini CLI
*   **Event Detection**: `data["hook_event_name"]` is `"AfterTool"` or `"PreCompress"`.
*   **Content Extraction**: `data["tool_response"]["llmContent"]`
*   **Reinjection**: 
    *   Modifies `data["tool_response"]["llmContent"]` with the sifted text (prepended with `--- [Distilled by Semantic-Sift] ---`).
    *   **Context Notification**: Creates or updates `data["hookSpecificOutput"]["additionalContext"]` with a string: `[NOTE: This tool output was automatically distilled by Semantic-Sift to remove X chars of noise.]`.

### 2. VS Code (Copilot / Native)
*   **Event Detection**: Checks for the existence of `data["tool_response"]["llmContent"]` when no explicit `hook_event_name` is provided.
*   **Content Extraction**: `data["tool_response"]["llmContent"]`
*   **Reinjection**: Modifies `data["tool_response"]["llmContent"]` with the sifted text.

### 3. Cursor & Roo Code
*   **Event Detection**: Checks for the existence of `data["result"]` as a string.
*   **Content Extraction**: `data["result"]`
*   **Reinjection**: Modifies `data["result"]` by prepending `[Sifted] ` (or `[Echo Bypassed] ` if the Echo Detector fired) to the sifted text.

### 4. OpenCode (Compacting Event)
*   **Event Detection**: `data["hook_event_name"]` is `"Compacting"`.
*   **Content Extraction**: `data["context"]` (The full conversation history).
*   **Reinjection**: Extracts structural markers, applies extreme semantic compression (`rate=0.2`), and injects the result into a new root key: `data["summary"]`.

### 5. Unrecognized / Generic Payloads
*   **Event Detection**: None of the above keys match, or parsing fails.
*   **Action**: The hook acts as a transparent pass-through, writing the raw `stdin` directly back to `stdout`. This ensures that unshielded clients or unknown schema variants do not crash the agent's tool execution loop.

---

## 4. The Content-Signature Bypass

Because several IDEs (Cursor, VS Code) utilize "Blind Hooks" that do not pass the executing `tool_name` to the shell script, `sift_hook.py` cannot easily distinguish between a raw `cat` command and a `sift_read_file` command.

To prevent "Double-Sifting" (running BERT on already-compressed text, which destroys data):
1.  Native MCP tools in `server.py` prepend their output with the global signature: `\n\n--- [Semantic-Sift: Native Execution] ---`.
2.  `sift_hook.py` explicitly scans `raw_content` for `--- [Semantic-Sift Audit] ---` (part of the audit header). If found, it immediately bypasses all processing and echoes the payload back, logging "Bypassing Native Execution for {tool_name}".

---

## 5. Master Configuration Matrix (MCP Server Installation)

While `sift_onboard` handles configuring hooks and prompts, the initial installation of the Semantic-Sift MCP server requires adding it to the host IDE's configuration file. The `get_global_mcp_configs()` function actively parses these exact locations to discover the environment.

| Software | Configuration Path (Parsed by Server) | Target Key | Expected Schema Style |
| :--- | :--- | :--- | :--- |
| **Claude Desktop** | `~/AppData/Roaming/Claude/claude_desktop_config.json` (Win)<br>`~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) | `mcpServers` | Standard |
| **Continue.dev** | `~/.continue/config.json` | `mcpServers` | Standard |
| **Zed** | `~/.config/zed/settings.json` or `.zed/settings.json` | `context_servers` | Standard |
| **VS Code Copilot**| `~/.copilot/mcp-config.json` or `.copilot/mcp-config.json` | `mcpServers` | Standard |
| **Cursor** | `~/.mcp.json` (Generic fallback / Custom definition) | `mcpServers` | Standard |
| **OpenCode** | `~/.opencode.json` or `.opencode.json` | `mcpServers` | Local Array |
| **Google Antigravity**| `~/.gemini/antigravity/mcp_config.json` | `mcpServers` | Standard |

### A. Standard Schema (Gemini, Claude Desktop, Cursor, Copilot, Zed)
The standard MCP JSON implementation.
```json
"semantic-sift": {
  "command": "python",
  "args": ["/absolute/path/to/server.py"]
}
```

### B. Local Array Schema (OpenCode, Kilo Code)
Certain strict environments require the command and arguments to be unified into a single array under a `local` type.
```json
"semantic-sift": {
  "type": "local",
  "command": [
    "python",
    "/absolute/path/to/server.py"
  ]
}
```

### C. Extended Schema (Cline / Roo Code)
Includes the `autoApprove` key to prevent manual confirmation loops during background sifting.
```json
"semantic-sift": {
  "command": "python",
  "args": ["/absolute/path/to/server.py"],
  "autoApprove": ["sift_read_file", "sift_analyze_file", "sift_logs", "sift_chat"]
}
```

### D. TOML Schema (Codex CLI)
Used exclusively by TOML-based configurations.
```toml
[mcp_servers.semantic-sift]
command = "python"
args = ["/absolute/path/to/server.py"]
```

### E. Unified Schema (Continue, Windsurf)
Requires explicit `type: "stdio"` inside the object block.
```json
"semantic-sift": {
  "type": "stdio",
  "command": "python",
  "args": ["/absolute/path/to/server.py"]
}
```