# Semantic-Sift: MCP Configuration Examples

This document provides ready-to-use configuration blocks and a master compatibility matrix for the **Semantic-Sift** server. Copy the appropriate block for your AI tool.

> **Note**: Replace the Python path and server path with the absolute paths on your machine.
> - **Windows example**: `C:/Users/you/semantic-sift/venv312/Scripts/python.exe`
> - **macOS/Linux example**: `/home/you/semantic-sift/venv312/bin/python`

---

## 1. Master Configuration Matrix (Installation)

To install the Semantic-Sift server, find your software in the matrix below and copy the appropriate schema from Section 2.

| Software | Configuration Path | Target Key | Expected Schema |
| :--- | :--- | :--- | :--- |
| **Claude Desktop** | Win: `%APPDATA%\Claude\claude_desktop_config.json` / Mac: `~/Library/Application Support/Claude/claude_desktop_config.json` | `mcpServers` | **A** (Standard) |
| **Claude Code** | `~/.claude/settings.json` | `mcp_servers` | **A** (Standard) |
| **Cursor** | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) | `mcpServers` | **A** (Standard) |
| **Qwen CLI** | `~/.qwen/settings.json` | `mcp_servers` | **A** (Standard) |
| **Codex CLI** | `~/.codex/mcp-config.json` | `mcpServers` | **A** (Standard) |
| **Continue.dev** | `~/.continue/config.json` | `mcpServers` | **D** (Unified) |
| **Zed** | `~/.config/zed/settings.json` | `context_servers` | **A** (Standard) |
| **VS Code Copilot** | `~/.copilot/mcp-config.json` | `mcpServers` | **A** (Standard) |
| **OpenCode** | `<project-root>/opencode.json` (project) or `%APPDATA%/opencode/opencode.json` (global, Win) / `~/.config/opencode/opencode.json` (global, Mac/Linux) | `mcp` | **B** (Array) |
| **Google Gemini CLI** | `~/.gemini/settings.json` | `mcpServers` | **A** (Standard) |
| **Cline / Roo Code** | IDE settings menu | `mcpServers` | **C** (Extended) |

---

## 2. Configuration Schemas

### A. Standard Schema (Claude Desktop, Claude Code, Cursor, Gemini CLI, Zed, VS Code)

**Windows:**
```json
"semantic-sift": {
  "command": "C:/Users/you/semantic-sift/venv312/Scripts/python.exe",
  "args": ["C:/Users/you/semantic-sift/server.py"],
  "env": {
    "SIFT_WORKSPACE_ROOT": "C:/Users/you/your-project",
    "SIFT_ALLOW_GLOBAL_READS": "false"
  }
}
```

**macOS/Linux:**
```json
"semantic-sift": {
  "command": "/home/you/semantic-sift/venv312/bin/python",
  "args": ["/home/you/semantic-sift/server.py"],
  "env": {
    "SIFT_WORKSPACE_ROOT": "/home/you/your-project",
    "SIFT_ALLOW_GLOBAL_READS": "false"
  }
}
```

### B. Local Array Schema (OpenCode)

**Windows:**
```json
"semantic-sift": {
  "type": "local",
  "command": [
    "C:/Users/you/semantic-sift/venv312/Scripts/python.exe",
    "C:/Users/you/semantic-sift/server.py"
  ],
  "environment": {
    "SIFT_WORKSPACE_ROOT": "C:/Users/you/your-project",
    "SIFT_ALLOW_GLOBAL_READS": "false"
  }
}
```

**macOS/Linux:**
```json
"semantic-sift": {
  "type": "local",
  "command": [
    "/home/you/semantic-sift/venv312/bin/python",
    "/home/you/semantic-sift/server.py"
  ],
  "environment": {
    "SIFT_WORKSPACE_ROOT": "/home/you/your-project",
    "SIFT_ALLOW_GLOBAL_READS": "false"
  }
}
```

### C. Extended Schema (Cline, Roo Code)

**Windows:**
```json
"semantic-sift": {
  "command": "C:/Users/you/semantic-sift/venv312/Scripts/python.exe",
  "args": ["C:/Users/you/semantic-sift/server.py"],
  "autoApprove": [
    "sift_read_file",
    "sift_analyze_file",
    "sift_logs",
    "sift_chat"
  ]
}
```

### D. Unified Schema (Windsurf, Continue.dev)

**Windows:**
```json
"semantic-sift": {
  "type": "stdio",
  "command": "C:/Users/you/semantic-sift/venv312/Scripts/python.exe",
  "args": ["C:/Users/you/semantic-sift/server.py"]
}
```

**macOS/Linux:**
```json
"semantic-sift": {
  "type": "stdio",
  "command": "/home/you/semantic-sift/venv312/bin/python",
  "args": ["/home/you/semantic-sift/server.py"]
}
```

---
*Building High-Fidelity Infrastructure for the Studio of Two.*
