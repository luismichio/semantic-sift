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

## 0. Native Rust Sidecar (`sift-core`)

To support high-performance, local-first desktop applications (like **Meechi**), Semantic-Sift provides a standalone Rust-based distribution located in `crates/sift-core`.

### Heuristic Sieve (Native)
The Rust core implements a high-fidelity port of the Heuristic Sieve using the `regex` crate. It provides instant, zero-dependency log cleaning suitable for short-lived subprocess execution.

### Semantic Engine (ONNX)
The Rust core utilizes **ONNX Runtime** (via the `ort` crate) to execute the **LLMLingua-2** token classification model. This allows for neural context distillation without a Python interpreter or a massive PyTorch footprint.
- **Model Format**: Standard `.onnx` model file + `tokenizer.json`.
- **Inference Strategy**: Tokenizes input, performs a single-pass classification, and reconstructs the string based on a probability threshold derived from the target `rate`.

### Dual Distribution Model
- **Python MCP**: The **"Full-Featured"** distribution. Primary path for IDE integration and developer workflows. Includes the **MarkItDown** multi-modal ingestion pipeline for binary file support (.pdf, .xlsx, etc.).
- **Rust Sidecar**: The **"High-Performance"** engine. Optimized for native application embedding, sidecars, and CI/CD pipelines. Currently limited to **Text-only** ingestion; assumes format conversion has already occurred in the host application or a previous pipeline stage.

---

## 1. Distillation Kernel (`sift_kernel.py`)

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
