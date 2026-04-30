# 🐛 Bug Report: The "File Size Paradox" & Unshielded Mandate Bypass

**Report Date**: April 30, 2026  
**Status**: CLOSED  
**Vulnerability Class**: Class A (Unshielded Environments)

---

## 1. Description of the Failure
Agents operating in "Unshielded Environments" (e.g., Google Antigravity, Windsurf, Claude Desktop) systematically violate the Auto-Sift Mandate established in `AGENTS.md`. Even when explicitly instructed to use Sifting tools, agents consistently default to using their native, hardwired `view_file` or `read_file` tools, resulting in massive context window pollution and completely bypassing the Semantic-Sift infrastructure.

---

## 2. Technical Root Cause
The failure is caused by an intersection of cognitive burden on the LLM and brittle local tool implementations.

### A. The "File Size Paradox"
The current `AGENTS.md` rule states:
> *"Do NOT use `view_file` or `read_file` for files > 1KB. You MUST use `sift_read_file`..."*

This introduces a logical paradox for the LLM. The agent cannot know the file size *before* reading the file. To comply, the agent must either run preliminary commands (like `list_dir`) to check byte sizes, or guess. Because LLMs heavily favor the path of least resistance, they guess. If they assume a file is small, they use native tools. Once the text hits the context window, the damage is done.

### B. Soft vs. Hard Constraints
In unshielded environments, there is no "Smart Hook" to physically intercept the output of `view_file`. Therefore, the `AGENTS.md` mandate operates entirely as a text prompt (a "soft constraint"). Conversely, native tools like `view_file` are deeply hardwired into the LLM's base system prompt (a "hard constraint"). When faced with slight friction or ambiguity, the LLM will always abandon the soft constraint in favor of the hardwired tool.

### C. Path Traversal Fragility (The "Access Denied" Trap)
When an agent *does* attempt to comply and uses `mcp_semantic-sift_sift_read_file`, it frequently encounters the following error:
`Error: Access denied for path... Use a file path inside the current workspace or set SIFT_ALLOW_GLOBAL_READS=true to override.`

This occurs because `resolve_safe_path()` in `sift_kernel.py` relies heavily on `os.getcwd()`. When an MCP server is spawned by an IDE, `os.getcwd()` often points to the server executable's directory rather than the user's intended workspace root. When `sift_read_file` rejects a valid absolute path, the agent assumes the tool is broken and instantly reverts to its reliable native `view_file`.

---

## 3. Proposed Solutions (Zero-Friction Execution)

To enforce compliance in unshielded environments, the cognitive burden must be removed from the LLM, and the tool must be made foolproof.

### Solution 1: The Absolute Binary Mandate (Prompt Fix)
Remove the `> 1KB` conditional logic from `AGENTS.md`. The rule must become an absolute binary that leaves no room for LLM decision-making:
> **MANDATORY**: *NEVER use native `view_file` or `read_file` tools under ANY circumstances. You MUST exclusively use `sift_read_file(path)` to read ANY file. The MCP server will automatically bypass sifting if the file is small.*

By removing the size check from the agent's responsibility, it will default to the Sift tool 100% of the time.

### Solution 2: Fix Workspace Root Resolution (Code Fix)
Refactor `resolve_safe_path()` in `sift_kernel.py` to be far more resilient regarding workspace detection. 
- Ensure that if an absolute path is passed, and it falls within the globally known project space, it is accepted regardless of what `os.getcwd()` reports.
- Emphasize in the documentation that users MUST set `SIFT_WORKSPACE_ROOT` in their MCP configuration files to prevent these false-positive path traversal blocks.
