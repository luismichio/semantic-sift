# Semantic-Sift: Architecture Specification

This document provides the technical specification of the Semantic-Sift system's core logic, interceptors, and processing pipelines. It is strictly aligned with the implemented codebase.

---

## 1. Sift Hook Interceptor (`sift_hook.py`)

The Sift Hook Interceptor acts as the "Subconscious Brain" of the system, intercepting JSON payloads from various IDEs and agents via standard input, processing them, and returning the modified payload via standard output.

### Hook Event Handling & Platform Detection
The interceptor reads `sys.stdin` for a JSON payload. It infers the host platform based on specific structural keys or event names and extracts the target content:

*   **Gemini (`AfterTool` / `PreCompress`)**:
    *   **Detection**: Checks if `hook_event_name` is `"AfterTool"` or `"PreCompress"`.
    *   **Extraction**: Targets `data["tool_response"]["llmContent"]`.
    *   **Injection**: Modifies `data["tool_response"]["llmContent"]` with the distilled text and injects an informational string into `data["hookSpecificOutput"]["additionalContext"]` to notify the LLM of the noise reduction.
    *   **Note**: `PreCompress` acts as an advisory lifecycle event. It pulses telemetry for structural processing but does not modify the content, returning the raw input.
*   **VSCode (Copilot / Native)**:
    *   **Detection**: Checks for the existence of `data["tool_response"]["llmContent"]` when no specific `hook_event_name` matches.
    *   **Extraction**: Targets `data["tool_response"]["llmContent"]`.
    *   **Injection**: Modifies `data["tool_response"]["llmContent"]` directly with the distilled text.
*   **Cursor**:
    *   **Detection**: Checks if `data["result"]` exists and is a string.
    *   **Extraction**: Targets `data["result"]`.
    *   **Injection**: Prepends `[Sifted]` or `[Echo Bypassed]` to the modified `data["result"]`.
*   **OpenCode (`Compacting`)**:
    *   **Detection**: Checks if `hook_event_name` is `"Compacting"`.
    *   **Extraction**: Targets `data["context"]` (the conversation history).
    *   **Injection**: Creates a new key `data["summary"]` containing the structural snapshot and semantic compression, which is then parsed by the OpenCode native plugin wrapper (`.opencode/plugins/semantic-sift.ts`).
*   **Generic & Unshielded Clients (e.g., Qwen CLI, OpenClaw)**:
    *   **Fallback Logic**: If a client does not match the specific `hook_event_name` or payload shapes above, the content extraction safely fails (`raw_content = ""`).
    *   **Pass-Through**: The interceptor acts as a transparent pass-through, writing the untouched original JSON directly back to `sys.stdout` to prevent breaking unsupported IDEs.

### Subconscious Routing Intelligence
When a payload is intercepted and the extracted content is larger than 500 characters, the hook applies an intelligent routing cascade to determine the optimal sifting strategy:

1.  **Exemptions for JSON Structured Data**:
    Before any sifting occurs, the interceptor attempts to parse the raw content as JSON using `json.loads()`. If the content is valid structured data (`dict` or `list`), it logs a "Structured Data Exemption" and bypasses all semantic processing to prevent breaking programmatic syntax.
2.  **Echo Detection Bypass**:
    Consults `telemetry_core.check_echo()`. If the exact content was recently processed, it bypasses the BERT/Heuristic models to save compute, injecting only an audit header.
3.  **Auto-Ranking (Search Tools)**:
    If the `tool_name` implies a search (e.g., `search`, `grep`, `find`), and the payload contains a search query (`pattern`, `query`, or `substring_pattern` found in `tool_args`), it splits the content by file delimiters (`\n(?=File: |Path: |---)`) and routes to `sift_rank` (Ranking Engine) to return only the top 5 most relevant chunks.
4.  **Auto-Semantic (Prose/Docs)**:
    If the tool implies reading prose or documentation (e.g., `read`, `fetch`, `extraction`, `chat`), or if the content has Markdown extensions (`.md`, `# `, `---`), and the content exceeds 3000 characters, it routes to `sift_chat` (Semantic Engine) with a `0.6` compression rate.
5.  **Auto-Heuristic (Default/Logs)**:
    If neither Ranking nor Semantic routing applies, it defaults to the Heuristic Engine. If the regex sieve successfully reduces the character count, it is classified as `sift_logs`.

---

## 2. Distillation Kernel (`sift_kernel.py`)

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
Combines engines for specialized use cases:
*   **Document Sifting (`perform_doc_sift`)**: First applies the Heuristic Engine to clean structural noise, then applies the Semantic Engine at a `0.4` rate.
*   **Extraction Cleaning (`perform_extraction_cleaning`)**: Uses RegEx to strip OCR artifacts (e.g., "Page X of Y", copyright notices, empty bullet points) before applying the Semantic Engine at a `0.7` rate to protect Markdown structures like tables.
*   **Compaction Summaries (`perform_compaction_summary`)**: Used specifically for the `Compacting` hook event. It uses RegEx to explicitly find and extract critical markers (`Decision:`, `Status:`, `File:`, `Task:`) into a "Structural Snapshot", and then aggressively compresses the rest of the text with the Semantic Engine at a `0.2` rate.

---

## 3. Caching & Device Management

To ensure high performance and prevent redundant compute, the system implements local caching and hardware-aware execution.

### Disk-Persistent Cache (`.sift_cache`)
*   **Logic**: The Semantic Engine (`perform_semantic_sift`) wraps its execution in a caching layer.
*   **Key Generation**: Keys are generated using an SHA-256 hash of the `tool_name`, the raw `text`, and the configuration `kwargs` (like the compression `rate`).
*   **Storage**: Cached results are written to `.sift_cache/<hash>.txt` and retrieved instantly on subsequent identical calls.

### Lazy CPU/CUDA Device Detection
*   **Logic**: The `get_device()` function delays the importation of `torch` and the checking of `torch.cuda.is_available()` until the exact moment an ML model is invoked.
*   **Benefit**: This prevents the heavy overhead of initializing PyTorch during fast heuristic operations or cache hits, falling back to `cpu` gracefully if `torch` is unavailable or hardware acceleration is absent.