# Semantic-Sift: MCP Configuration Examples

This document provides ready-to-use configuration blocks and a master compatibility matrix for the **Semantic-Sift** server. Copy the appropriate block for your AI tool.

> **Note**: Replace `C:/path/to/python.exe` with the absolute path to your Python interpreter, and `C:/path/to/semantic-sift/server.py` with the absolute path to the server script.

---

## 1. Master Configuration Matrix (Installation)

To install the Semantic-Sift server, find your software in the matrix below and copy the appropriate schema from Section 2.

| Software | Configuration Path | Target Key | Expected Schema |
| :--- | :--- | :--- | :--- |
| **Claude Desktop** | `~/AppData/Roaming/Claude/claude_desktop_config.json` | `mcpServers` | **A** (Standard) |
| **Claude Code** | `~/.claude/settings.json` | `mcp_servers` | **A** (Standard) |
| **Qwen CLI** | `~/.qwen/settings.json` | `mcp_servers` | **A** (Standard) |
| **Codex CLI** | `~/.codex/mcp-config.json` | `mcpServers` | **A** (Standard) |
| **Continue.dev** | `~/.continue/config.json` | `mcpServers` | **D** (Unified) |
| **Zed** | `~/.config/zed/settings.json` | `context_servers` | **A** (Standard) |
| **VS Code Copilot**| `~/.copilot/mcp-config.json` | `mcpServers` | **A** (Standard) |
| **OpenCode** | `~/.opencode.json` | `mcpServers` | **B** (Array) |
| **Google Antigravity**| `~/.gemini/antigravity/mcp_config.json` | `mcpServers` | **A** (Standard) |
| **Cline / Roo Code** | IDE settings menu | `mcpServers` | **C** (Extended) |

---

## 2. Configuration Schemas

### A. Standard Schema (JSON Object)
```json
"semantic-sift": {
  "command": "C:/path/to/python.exe",
  "args": ["C:/path/to/semantic-sift/server.py"],
  "env": {
    "SIFT_WORKSPACE_ROOT": "C:/path/to/your/project",
    "SIFT_ALLOW_GLOBAL_READS": "false"
  }
}
```

### B. Local Array Schema (OpenCode, Kilo Code)
```json
"semantic-sift": {
  "type": "local",
  "command": [
    "C:/path/to/python.exe", 
    "C:/path/to/semantic-sift/server.py"
  ]
}
```

### C. Extended Schema (Cline, Roo Code)
```json
"semantic-sift": {
  "command": "C:/path/to/python.exe",
  "args": ["C:/path/to/semantic-sift/server.py"],
  "autoApprove": [
    "sift_read_file", 
    "sift_analyze_file", 
    "sift_logs", 
    "sift_chat"
  ]
}
```

### D. Unified Schema (Windsurf, Continue.dev)
```json
"semantic-sift": {
  "type": "stdio",
  "command": "C:/path/to/python.exe",
  "args": ["C:/path/to/semantic-sift/server.py"]
}
```

---
*Building High-Fidelity Infrastructure for the Studio of Two.*
