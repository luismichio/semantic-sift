# Semantic-Sift: Architecture Specification

This document provides the technical specification of the Semantic-Sift system's core logic, interceptors, and processing pipelines. It is strictly aligned with the implemented codebase.

### Package Structure

As of the Phase 6.2 Root-Module Inversion refactor, all canonical implementations live inside `semantic_sift/`. Root-level stubs were deleted; the `semantic_sift/` package is the single source of truth.

```
server.py                   # Thin MCP entrypoint (~30 lines); calls register_tools() + start_model_warmup()
semantic_sift/
  __init__.py               # Package namespace
  tools.py                  # All MCP tool implementations (register_tools())
  kernel.py                 # Canonical distillation logic (heuristic, semantic, ranking, atomic caching, path guard)
  telemetry.py              # Canonical async telemetry pulse, rate limiter, TTL pruning, echo detector
  hook.py                   # Canonical IDE hook interceptor (stdin/stdout JSON pipeline)
  onboarding.py             # Gitignore updates, instruction file injection, apply_onboarding()
  hook_injector.py          # Multi-IDE hook injection, platform gateway, build_runtime_hook_command()
  server.py                 # Thin re-export; registers MCP server entry point
  cli.py                    # Terminal CLI (semantic-sift-stats, semantic-sift-onboard, semantic-sift-cli)
pyproject.toml              # Formal packaging; [neural], [multi-modal], and [dev] optional extras
```

---

## 0. Native Rust Sidecar (`sift-core`)

To support high-performance, local-first desktop applications (like **Meechi**), Semantic-Sift provides a standalone Rust-based distribution located in `crates/sift-core`.

### Heuristic Sieve (Native)
The Rust core implements a high-fidelity port of the Heuristic Sieve using the `regex` crate. It provides instant, zero-dependency log cleaning suitable for short-lived subprocess execution.

The Rust core utilizes **ONNX Runtime** (via the `ort` crate) to execute the **LLMLingua-2** token classification model. This allows for neural context distillation without a Python interpreter or a massive PyTorch footprint.
- **Model Format**: Standard `.onnx` model file + `tokenizer.json`.
- **Inference Strategy**: Tokenizes input, performs a single-pass classification, and reconstructs the string based on a probability threshold derived from the target `rate`.

### Dual Distribution Model
- **Python MCP**: The **"Full-Featured"** distribution. Primary path for IDE integration and developer workflows. Supports the **MarkItDown** multi-modal ingestion pipeline via the `[multi-modal]` optional extra for binary file support (.pdf, .xlsx, etc.).
- **Rust Sidecar**: The **"High-Performance"** engine. Optimized for native application embedding, sidecars, and CI/CD pipelines. Currently limited to **Text-only** ingestion; assumes format conversion has already occurred in the host application or a previous pipeline stage.

### The Hybrid Engine (`semantic-sift-cli`)
To provide the best of both worlds, the Python package exposes the `semantic-sift-cli` command. This acts as an **Intelligent Router**:
- For **short tasks** (<30,000 chars), it instantly shells out to the low-latency Rust `sift-core` (ONNX).
- For **massive batch tasks**, it dynamically loads the high-throughput PyTorch framework with Flash Attention to prevent memory explosion, leveraging $O(n)$ memory scaling.

---

## 1. Distillation Kernel (`semantic_sift/kernel.py`)

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
*   **Atomic Writes**: Cache entries are written via a `.tmp` file and atomically renamed with `os.replace()`. This prevents corrupted cache reads if the process crashes mid-write or if two concurrent requests attempt to write the same key simultaneously.

### Lazy CPU/CUDA Device Detection
*   **Logic**: The `get_device()` function delays the importation of `torch` and the checking of `torch.cuda.is_available()` until the exact moment an ML model is invoked.
*   **Benefit**: This prevents the heavy overhead of initializing PyTorch during fast heuristic operations or cache hits, falling back to `cpu` gracefully if `torch` is unavailable or hardware acceleration is absent.

---

## 2. IDE Hook Interceptor (`semantic_sift/hook.py`)

The Hook Interceptor provides transparent, "subconscious" sifting by intercepting IDE tool events without requiring explicit agent calls.

### Hook Protocol
The interceptor reads a JSON event from `stdin` on every IDE `PostToolUse` or `Compacting` event. The event payload contains `tool_name`, `tool_input`, and `tool_output`.

### Routing Logic
*   **`Compacting` event**: Routes the full conversation history to `perform_compaction_summary` (aggressive `0.2` rate). Preserves critical markers (`Decision:`, `Status:`, `File:`, `Task:`) via RegEx extraction into a "Structural Snapshot" before compressing the remainder.
*   **`PostToolUse` — large output** (> `SIFT_HOOK_THRESHOLD_CHARS`, default `8000`): Routes to the appropriate distillation tool based on `tool_name` heuristics (e.g., log-producing tools → heuristic sieve; doc tools → doc sift).
*   **`PostToolUse` — small output**: Passes through unchanged; no sifting applied.

### Echo Guard
Prevents re-sifting content that has already been processed. The guard computes an SHA-256 hash scoped to `pipe_name:node_index:content`. If the hash matches a recently-seen entry, the output is returned as-is with a `[Sift: Echo Detected]` marker.

### Multi-IDE Platform Gateway (`semantic_sift/hook_injector.py`)
`build_runtime_hook_command()` generates the correct hook invocation string per IDE:
- **OpenCode**: `tool.execute.after` hook (currently a no-op for MCP tools; tracked upstream).
- **Cursor / Gemini / Cline**: `PostToolUse` file-based hook.
- **Generic fallback**: `stdin`/`stdout` subprocess pipe.

---

## 3. Telemetry (`semantic_sift/telemetry.py`)

Telemetry is strictly opt-in, local-first, and never blocks the main processing path.

### Local Telemetry Store (`.pipe_telemetry.json`)
*   **Atomic Writes**: `log_telemetry()` writes to a `.tmp` file then atomically renames via `os.replace()`, preventing partial JSON on crash or concurrent writes.
*   **TTL Pruning**: On every write, sessions older than `SIFT_TELEMETRY_TTL_DAYS` (default `90`) days are pruned to prevent unbounded growth.
*   **Schema**: Each session record contains `timestamp`, `tool_name`, `input_chars`, `output_chars`, `compression_ratio`, and `device`.

### Rate Limiter
Prevents telemetry flooding during rapid sequential tool calls. A minimum inter-pulse interval is enforced; calls within the window are silently skipped.

### Remote Pulse (Optional)
*   **Opt-In**: Only fires if `SIFT_TELEMETRY_OPT_IN=true` is set.
*   **Fallback URL**: `SIFT_TELEMETRY_FALLBACK_URL` env var enables silent retry on primary endpoint failure.
*   **IDE Detection**: `detect_client_id()` inspects IDE env vars and parent process name to tag each pulse with the active environment. OpenCode `AfterTool` events are correctly identified and not misclassified as Gemini.

### Privacy Constraints
*   Telemetry never includes raw content, file paths, or secrets.
*   Type-specific redaction labels are replaced with generic `[REDACTED]` to prevent metadata leakage.
*   `.pipe_telemetry.json` and `.pipe_identity` are added to `.gitignore` during `sift_onboard`.

---

## 4. Tools, Onboarding & CLI (`semantic_sift/tools.py`, `onboarding.py`, `hook_injector.py`, `cli.py`)

### MCP Tool Registration (`semantic_sift/tools.py`)
All MCP tools are registered inside `register_tools(mcp)` as inner closures bound to the FastMCP server instance. The public surface is:

| Tool | Intent |
| :--- | :--- |
| `sift_read_file` | File ingestion with auto-routing by content type |
| `sift_analyze_file` | Context health report (SNR) for files |
| `sift_logs` | Heuristic log cleaning |
| `sift_chat` | Semantic chat/conversation compaction |
| `sift_doc` | Hybrid HTML/Markdown distillation |
| `sift_extraction` | OCR artifact removal + diff |
| `sift_rank` | Semantic re-ranking of document chunks |
| `sift_analyze` | Context health report for memory-resident strings |
| `get_sift_stats` | Context Balance Sheet (ROI telemetry) |
| `sift_dashboard` | Prompt: rich stats dashboard |
| `sift_onboard` | IDE onboarding, hook injection, mandate injection |
| `sift_warmup` | Explicit neural model pre-warm; returns readiness status |

### Onboarding Engine (`semantic_sift/onboarding.py`)
`apply_onboarding()` performs the following in order:
1. Updates `.gitignore` with telemetry and identity artifact patterns.
2. Injects the **Sift Mandate** into IDE instruction files (`AGENTS.md`, `.cursorrules`, etc.).
3. Injects the **MCP Synergy Matrix** from `ORCHESTRATION_BLUEPRINTS.md` as an auto-appended SOP block.
4. Detects specialized agent sub-folders and recursively shields worker agents (Blueprint D).
5. Surfaces a telemetry consent disclosure via `_build_telemetry_disclosure()`.

`dry_run=True` returns the planned action list without writing any files.

### CLI (`semantic_sift/cli.py`)
Three entry points registered in `pyproject.toml`:
*   **`semantic-sift-cli`**: The Hybrid Engine router. Dispatches short tasks (<30,000 chars) to the Rust `sift-core` ONNX sidecar; large tasks to the PyTorch backend with Flash Attention.
*   **`semantic-sift-stats`**: Prints the local Context Balance Sheet from `.pipe_telemetry.json`.
*   **`semantic-sift-onboard`**: Terminal-friendly wrapper for `apply_onboarding()` with `--dry-run` flag.
