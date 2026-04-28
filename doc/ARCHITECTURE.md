# Semantic-Sift: Architecture Specification

This document provides the technical specification of the Semantic-Sift system's core logic, interceptors, and processing pipelines. It is strictly aligned with the implemented codebase.

### Package Structure

As of the FIX-12 refactor, the codebase is organized as follows:

```
server.py                   # Thin MCP entrypoint (~30 lines); calls register_tools() + start_model_warmup()
sift_kernel.py              # Core distillation logic (heuristic, semantic, ranking, caching, path guard)
sift_hook.py                # IDE hook interceptor (stdin/stdout JSON pipeline)
telemetry_core.py           # Async telemetry pulse, rate limiter, echo detector, gitignore protection
semantic_sift/
  __init__.py               # Package namespace
  tools.py                  # All MCP tool implementations (register_tools())
  onboarding.py             # Gitignore updates, instruction file injection, apply_onboarding()
  hook_injector.py          # Multi-IDE hook injection, platform gateway, build_runtime_hook_command()
  kernel.py                 # Compatibility re-export wrapper
  hook.py                   # Compatibility re-export wrapper
  telemetry.py              # Compatibility re-export wrapper
  server.py                 # Compatibility re-export wrapper
pyproject.toml              # Formal packaging; [neural] and [dev] optional extras
```

Root-level files (`sift_kernel.py`, `sift_hook.py`, `telemetry_core.py`) are retained for backward compatibility. The `semantic_sift/` package wraps and extends them.

---

## 1. Sift Hook Interceptor (`sift_hook.py`)

The Sift Hook Interceptor acts as the "Subconscious Brain" of the system, intercepting JSON payloads from various IDEs and agents via standard input, processing them, and returning the modified payload via standard output.

### Async Timeout Guard
All semantic processing in the hook is wrapped in a `ThreadPoolExecutor`-based timeout guard (`_semantic_sift_with_timeout`). If the neural path exceeds `SIFT_HOOK_TIMEOUT_MS` (default: `3000` ms), the hook falls back to the heuristic sieve and appends a `[Semantic-Sift: Heuristic Fallback - timeout]` marker. This ensures the IDE tool response pipeline is never blocked indefinitely.

### Hook Event Handling & Platform Detection
The interceptor reads `sys.stdin` for a JSON payload. It infers the host platform based on specific structural keys, environment variables, or event names.

*   **Aggressive Tool Discovery**: To ensure high-fidelity telemetry, the hook implements a recursive discovery function (`find_tool_name`) that scans the payload for common MCP keys including `tool_name`, `tool`, `name`, `call`, `command`, and `mcp_tool`. It also inspects nested objects to ensure tool names are captured even in complex client responses.
*   **Gemini (`AfterTool` / `PreCompress`)**:
    *   **Detection**: Checks if `hook_event_name` is `"AfterTool"` or `"PreCompress"`.
    *   **Extraction**: Targets `data["tool_response"]["llmContent"]`.
    *   **Injection**: Modifies `data["tool_response"]["llmContent"]` with the distilled text and injects an informational string into `data["hookSpecificOutput"]["additionalContext"]` to notify the LLM of the noise reduction.
*   **Claude Code, Qwen CLI & Codex CLI**:
    *   **Detection**: Checks for platform-specific environment variables (`$CLAUDE_TOOL_NAME`, `$QWEN_TOOL_NAME`, or `$CODEX_TOOL_NAME`).
    *   **Extraction**: Reads the raw tool output from standard input.
    *   **Injection**: Modifies the JSON structure (targeting `tool_response.llmContent` or `result`) and returns the payload via standard output.
*   **VSCode (Copilot / Native)**:
    *   **Detection**: Checks for the existence of `data["tool_response"]["llmContent"]` when no specific `hook_event_name` matches.
    *   **Extraction**: Targets `data["tool_response"]["llmContent"]`.
    *   **Injection**: Modifies `data["tool_response"]["llmContent"]` directly.
*   **Cursor**:
    *   **Detection**: Checks if `data["result"]` exists and is a string.
    *   **Extraction**: Targets `data["result"]`.
    *   **Injection**: Prepends `[Sifted]` or `[Echo Bypassed]` to the modified `data["result"]`.
*   **OpenCode & OpenClaw**:
    *   **Detection**: Triggered via native TypeScript plugins (`tool.execute.after` or `api.on("tool:after")`).
    *   **Extraction**: Receives a unified `AfterTool` JSON structure constructed by the plugin wrapper.
    *   **Injection**: Reassigns the sifted content directly to the plugin's output context.
*   **Security Gateways (Windsurf & Cline)**:
    *   **Architecture**: Unlike reactive hooks, these are **proactive inhibitors**.
    *   **Mechanism**: A `pre_mcp_tool_use` hook (Windsurf) or `PreToolUse` executable (Cline) intercepts native file readers (`read_file`, `view_file`) before they execute.
    *   **Logic**: If the target file size > 1KB, the gateway terminates the process with an error message, physically forcing the agent to use `sift_read_file`.
    *   **Platform-Aware**: The gateway command is generated by `semantic_sift/hook_injector.py::get_windsurf_gateway_command()`. On `win32` it uses `pwsh -NoProfile -Command "Get-Item ..."`. On POSIX it uses `stat -c %s / stat -f %z / wc -c` chain. Silently-inactive-on-Windows is no longer a concern.

### Subconscious Routing Intelligence
When a payload is intercepted and the extracted content is larger than 500 characters, the hook applies an intelligent routing cascade:

1.  **Exemptions for JSON Structured Data**:
    Before sifting, the interceptor attempts to parse the raw content as JSON. If the content is valid structured data (`dict` or `list`), it bypasses all semantic processing to prevent breaking programmatic syntax.
2.  **Echo Detection Bypass**:
    Consults `telemetry_core.check_echo()`. If the exact content was recently processed, it bypasses the BERT/Heuristic models to save compute, injecting only a 30s TTL audit header.
3.  **Subagent Identification ("Sniffing")**:
    The hook scans for identification markers (e.g., `$CLAUDE_AGENT_NAME`, `threadLabel`, or task-specific prefixes like `[Explore]`) to attribute the transformation to a specific specialized agent thread in the telemetry logs.
4.  **Auto-Ranking (Search Tools)**:
    If the `tool_name` implies a search (e.g., `search`, `grep`, `find`), it splits the content by file delimiters (`\n(?=File: |Path: |---)`) and routes to the Ranking Engine to return only the Top 5 results.
5.  **Auto-Semantic (Prose/Docs)**:
    If the tool implies reading prose or documentation (e.g., `read`, `fetch`, `extraction`), or if the content has Markdown extensions and exceeds 3000 characters, it routes to the Semantic Engine with a `0.6` compression rate.
6.  **Auto-Heuristic (Default/Logs)**:
    Default fallback. If the regex sieve reduces the character count, it is classified as `sift_logs`.

---

## 2. Recursive Subagent Discovery (`semantic_sift/onboarding.py`)

A critical component of the architecture is the **Recursive Discovery Engine**, which ensures that even isolated background threads are shielded by Semantic-Sift.

### Discovery Logic
During the `sift_onboard` process, the system performs a recursive crawl of the project workspace (up to 3 levels deep):
*   **Known Folders**: Specifically targets `.codex/agents/`, `.cursor/agents/`, `.junie/agents/`, and `.agents/`.
*   **Scoped Mandates**: Identifies any `AGENTS.md` files located in subdirectories.
*   **Multi-Format Support**:
    *   **Markdown/Rules**: Injects the mandate into standard `.md` or `.cursorrules` files.
    *   **TOML**: Utilizes a specialized `update_toml_config` injector for Codex agents, safely merging the mandate into the `instructions` key without breaking TOML syntax.

## 3. Multi-Modal Ingestion Engine (`sift_kernel.py`)

To support complex corporate environments, Semantic-Sift includes a structural pre-processing layer that transforms binary files into siftable text.

### Path Traversal Protection
All file read operations go through `resolve_safe_path(path)` before any I/O. This function resolves the real path and verifies it falls within the current workspace root. Attempts to traverse outside (e.g., `../../etc/passwd`) return an `Error: Access denied` response. Set `SIFT_ALLOW_GLOBAL_READS=true` to disable the guard for research workflows that legitimately read files outside the workspace.

### MarkItDown Integration
The kernel utilizes Microsoft's `MarkItDown` to handle non-text formats.
*   **Supported Formats**: PDF, DOCX, XLSX, PPTX, ZIP, and HTML.
*   **Structural Awareness**: MarkItDown preserves tables (Excel/Word) and document hierarchies (Headings), which improves the accuracy of the subsequent Semantic Engine.

### Two-Stage Ingestion Pipeline
When a binary file is read via `sift_read_file` or intercepted by the hook:
1.  **Stage 1 (Extraction)**:
    *   Generates a SHA-256 hash of the binary file content.
    *   Checks `.sift_cache/` for `raw_[hash].md`.
    *   If missing, converts the file to Markdown and caches the result.
2.  **Stage 2 (Distillation)**:
    *   The cached Markdown is passed to the Heuristic or Semantic engines based on the requested `type` and `rate`.
    *   The final sifted result is cached separately as `sift_[hash]_[params].txt`.

### Subconscious HTML Normalization
The `sift_hook.py` middleware automatically detects HTML tags in tool outputs. It utilizes the kernel's `MarkItDown` instance to strip DOM noise (scripts, styles, nav) and convert the content to clean Markdown before it ever reaches the sifting models.

---

## 4. Distillation Kernel (`sift_kernel.py`)

The Distillation Kernel contains the mathematical and logical engines that physically reduce the character and token footprint of text.

### Heuristic Engine
A high-speed, RegEx-based text cleaner designed to incinerate structural noise without using neural networks. It targets:
*   **Timestamps**: Strips ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`), legacy (`YYMMDD HHMMSS`), and bracketed (`[HH:MM:SS]`) timestamps.
*   **Progress Bars**: Removes `[1/10]` or `...` or percentage indicators `100%`.
*   **Module Logs**: Strips file size listings and boilerplate debug prefixes (e.g., `INFO dfs.`).

### Semantic Engine
Performs intelligent prompt compression using a local Small Language Model (SLM).
*   **Model**: `microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`.
*   **Logic**: Utilizes the `llmlingua` PromptCompressor to evaluate token entropy. It identifies and prunes low-value filler tokens while strictly preserving core entities and instructions.
*   **Configuration**: Forces preservation of specific structural tokens (`\n`, `?`) and defines chunk boundaries (`.`, `\n`) to maintain readability.

### Ranking Engine
Performs semantic re-ranking of chunked documents against a specific user query.
*   **Model**: `BAAI/bge-reranker-base` via `sentence_transformers.CrossEncoder`.
*   **Logic**: Scores pairs of `[query, document_chunk]` and sorts them, returning only the top-N results to ensure the context window is filled with the highest-signal data.

### Hybrid Pipelines
*   **Document Sifting (`perform_doc_sift`)**: First applies the Heuristic Engine to clean structural noise, then applies the Semantic Engine at the caller-specified `rate` (default `0.4`).
*   **Extraction Cleaning (`perform_extraction_cleaning`)**: Uses RegEx to strip OCR artifacts (e.g., "Page X of Y", copyright notices) before applying the Semantic Engine at a `0.7` rate to protect Markdown structures like tables. When `show_diff=True`, appends a `--- REMOVED CONTENT ---` section listing stripped text.
*   **Compaction Summaries (`perform_compaction_summary`)**: Used specifically for the `Compacting` hook event. It uses RegEx to extract critical markers (`Decision:`, `Status:`, `File:`, `Task:`) into a "Structural Snapshot", and then aggressively compresses the rest of the text with the Semantic Engine at a `0.2` rate. If vocabulary overlap between input and output falls below `SIFT_COMPACTION_FIDELITY_THRESHOLD` (default `0.3`), a low-fidelity warning is appended.

---

## 5. Cold-Start & Model Warm-Up

On MCP server startup, `server.py` calls `sift_kernel.start_model_warmup()`, which launches a background daemon thread to pre-load the LLMLingua and BGE-Reranker models. A threading `Event` (`_MODEL_READY`) gates the first semantic call:

*   If the models finish loading before the first real request, the full neural path is used immediately.
*   If the first request arrives before loading completes, the kernel waits up to `SIFT_MODEL_READY_WAIT_MS` (default `1200` ms) for the models. If still not ready, it falls back to the heuristic sieve and appends a `[Semantic-Sift: Models warming up - heuristic mode active]` marker.

This eliminates the "MCP server appears to hang" cold-start experience while ensuring agents always get a useful response.

---

## 6. Caching & Device Management

### Disk-Persistent Cache (`.sift_cache`)
*   **Logic**: The Semantic Engine wraps its execution in a caching layer.
*   **Key Generation**: Keys are generated using an SHA-256 hash of the `tool_name`, the raw `text`, and the configuration `kwargs` (like the compression `rate`).
*   **Retrieval**: Results are retrieved instantly (~1ms) for repeat tool calls.

### Lazy CPU/CUDA Device Detection
*   **Logic**: The `get_device()` function delays the importation of `torch` and the checking of `torch.cuda.is_available()` until the exact moment an ML model is invoked.
*   **Benefit**: This prevents the heavy overhead of initializing PyTorch during fast heuristic operations or cache hits, falling back to `cpu` gracefully if `torch` is unavailable or hardware acceleration is absent.
