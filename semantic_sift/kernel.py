# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

"""Core distillation logic for Semantic-Sift. Canonical import path."""

import re
import os
import json
import hashlib
import threading
import difflib
import subprocess
from typing import Any

# Cache Configuration
CACHE_DIR = ".sift_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Input Size Guard — protects against OOM in the MCP server process.
# Default: 50MB. Override via SIFT_MAX_INPUT_MB environment variable.


def _get_max_input_bytes() -> int:
    raw = os.environ.get("SIFT_MAX_INPUT_MB", "50")
    try:
        return max(1, int(raw)) * 1024 * 1024
    except ValueError:
        return 50 * 1024 * 1024


MAX_INPUT_SIZE_BYTES: int = _get_max_input_bytes()
_SIZE_GUARD_LOGGER = None


def _get_size_guard_logger():  # type: ignore[return]
    global _SIZE_GUARD_LOGGER
    if _SIZE_GUARD_LOGGER is None:
        import logging

        _SIZE_GUARD_LOGGER = logging.getLogger("semantic_sift.input_guard")
    return _SIZE_GUARD_LOGGER


def _enforce_input_size_guard(text: str) -> str:
    """
    Checks that the input does not exceed MAX_INPUT_SIZE_BYTES.
    On breach: logs a warning to stderr, truncates to the limit, and prepends a notice.
    Returns the (possibly truncated) text.
    """
    limit = MAX_INPUT_SIZE_BYTES
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text

    truncated = encoded[:limit].decode("utf-8", errors="replace")
    mb_limit = limit // (1024 * 1024)
    _get_size_guard_logger().warning(
        "Input exceeds maximum size (%dMB). Truncated from %d to %d bytes. "
        "Set SIFT_MAX_INPUT_MB to increase the limit.",
        mb_limit,
        len(encoded),
        limit,
    )
    notice = f"[Semantic-Sift: Input truncated at {mb_limit}MB limit — set SIFT_MAX_INPUT_MB to increase]\n\n"
    return notice + truncated


# Lazy Device Detection
DEVICE = "cpu"
_DEVICE = None
_MARKITDOWN = None
_COMPRESSOR = None
_MODEL_READY = threading.Event()
_MODEL_WARMUP_STARTED = False
_MODEL_WARMUP_LOCK = threading.Lock()
_MODEL_WARMUP_ERROR = None


def resolve_safe_path(path: str, workspace_root: str | None = None) -> str:
    """Resolve a file path and enforce workspace-bound access by default."""
    requested_path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    if os.environ.get("SIFT_ALLOW_GLOBAL_READS", "false").lower() == "true":
        import logging

        logging.getLogger("semantic_sift.security").warning(
            "SIFT_ALLOW_GLOBAL_READS is enabled — workspace path safety checks are BYPASSED. "
            "Path: %s. Set SIFT_ALLOW_GLOBAL_READS=false to re-enable sandboxing.",
            requested_path,
        )
        return requested_path

    # Resolution chain: explicit arg > env var > cwd
    explicit_root = workspace_root or os.environ.get("SIFT_WORKSPACE_ROOT")
    candidate_root = explicit_root or os.getcwd()
    root_path = os.path.realpath(os.path.abspath(os.path.expanduser(candidate_root)))

    def _in_workspace(req: str, root: str) -> bool:
        try:
            return os.path.commonpath([req, root]) == root
        except ValueError:
            return False

    if _in_workspace(requested_path, root_path):
        return requested_path

    # Heuristic fallback: only if no explicit root was provided.
    # Walk up from the requested path looking for workspace markers.
    if explicit_root:
        return (
            f"Error: Access denied for path '{path}'. "
            "Use a file path inside the current workspace, set SIFT_WORKSPACE_ROOT "
            "in your MCP configuration, or set SIFT_ALLOW_GLOBAL_READS=true to override."
        )

    _WORKSPACE_MARKERS = {
        "pyproject.toml",
        ".git",
        "setup.py",
        "setup.cfg",
        "package.json",
        ".vscode",
        ".idea",
        "AGENTS.md",
    }
    probe = os.path.dirname(requested_path)
    while True:
        if any(os.path.exists(os.path.join(probe, m)) for m in _WORKSPACE_MARKERS):
            if _in_workspace(requested_path, probe):
                return requested_path
        parent = os.path.dirname(probe)
        if parent == probe:
            # Reached filesystem root without finding a marker — deny access.
            break
        probe = parent

    return (
        f"Error: Access denied for path '{path}'. "
        "Use a file path inside the current workspace, set SIFT_WORKSPACE_ROOT "
        "in your MCP configuration, or set SIFT_ALLOW_GLOBAL_READS=true to override."
    )


def get_device() -> str:
    global _DEVICE, DEVICE
    if _DEVICE is None:
        try:
            import torch

            _DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            _DEVICE = "cpu"
    DEVICE = _DEVICE
    return _DEVICE


def get_markitdown() -> Any | None:
    global _MARKITDOWN
    if _MARKITDOWN is None:
        try:
            from markitdown import MarkItDown

            _MARKITDOWN = MarkItDown()
        except ImportError:
            _MARKITDOWN = None
    return _MARKITDOWN


def _build_prompt_compressor() -> Any:
    from llmlingua import PromptCompressor

    return PromptCompressor(
        model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
        use_llmlingua2=True,
        device_map=get_device(),
    )


def _warm_up_models() -> None:
    global _COMPRESSOR, _MODEL_WARMUP_ERROR
    try:
        _COMPRESSOR = _build_prompt_compressor()
    except (ImportError, RuntimeError, OSError, ValueError) as e:
        _MODEL_WARMUP_ERROR = str(e)
    finally:
        _MODEL_READY.set()


def start_model_warmup() -> None:
    global _MODEL_WARMUP_STARTED
    if _MODEL_WARMUP_STARTED:
        return
    with _MODEL_WARMUP_LOCK:
        if _MODEL_WARMUP_STARTED:
            return
        _MODEL_WARMUP_STARTED = True
        thread = threading.Thread(target=_warm_up_models, daemon=True, name="semantic-sift-model-warmup")
        thread.start()


def get_file_hash(path: str) -> str:
    """Generates a stable hash for a file's content."""
    try:
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError:
        return hashlib.sha256(path.encode()).hexdigest()


def ensure_markdown_content(path: str) -> str:
    """Converts binary files to Markdown using MarkItDown with local caching."""
    ext = os.path.splitext(path)[1].lower()
    binary_exts = [".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".html", ".htm"]
    if ext not in binary_exts:
        return load_raw_text(path)

    md_converter = get_markitdown()
    if not md_converter:
        return f"Error: Multi-modal dependencies not installed. Cannot process {ext} files. Please run 'pip install semantic-sift[multi-modal]' to enable PDF/Office support."

    file_hash = get_file_hash(path)
    cache_path = os.path.join(CACHE_DIR, f"raw_{file_hash}.md")

    # Check Cache
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    # Perform Conversion
    try:
        result = md_converter.convert(path)
        content = result.text_content
        tmp_path = cache_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            os.replace(tmp_path, cache_path)
        except OSError:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return content
    except (OSError, AttributeError, RuntimeError, ValueError) as e:
        return f"Error converting {ext} file: {str(e)}"


def load_raw_text(path: str) -> str:
    """Safely loads plain text with encoding fallbacks."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except OSError as e:
            return f"Error reading file (latin-1 fallback failed): {str(e)}"
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except OSError as e:
        return f"Error reading file: {str(e)}"


def load_file_content(path: str) -> str:
    """Main ingestion entry point supporting both text and binary formats."""
    return ensure_markdown_content(path)


# --- Core Heuristic Logic ---


def apply_heuristic_sieve(text: str) -> str:
    """Sifts through raw technical logs to remove noise."""
    text = _enforce_input_size_guard(text)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in text:
        return text

    lines = text.splitlines()
    sifted = []
    # Broad timestamp support: ISO-8601, Legacy (YYMMDD), and Bracketed (Vercel)
    timestamp_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?)|(\d{6}\s\d{6}\s\d+)|(\[\d{2}:\d{2}:\d{2}(\.\d+)?\])"
    )
    progress_pattern = re.compile(r"\[\d+/\d+\]|[\.]{3,}|\d+%\s*")
    metadata_pattern = re.compile(r"\s*(INFO|DEBUG|WARN|ERROR)\s+dfs\..*?:\s*")
    module_pattern = re.compile(r"^\s*[\d\.]+\s+(MB|KB|bytes|B)\s+[\w\-\.\/]+.*$", re.IGNORECASE)

    for line in lines:
        clean_line = timestamp_pattern.sub("", line).strip()
        clean_line = metadata_pattern.sub("", clean_line).strip()
        if not clean_line or progress_pattern.search(clean_line) or module_pattern.match(clean_line):
            continue
        sifted.append(clean_line)
    return "\n".join(sifted)


# --- Core Semantic Logic ---


def get_cache_key(tool_name: str, text: str, **kwargs: Any) -> str:
    payload = f"{tool_name}:{text}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def check_cache(key: str) -> str | None:
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return None


def set_cache(key: str, result: str) -> None:
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    tmp_path = cache_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(result)
        os.replace(tmp_path, cache_path)
    except OSError:
        # Clean up the temp file if the atomic rename failed.
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _call_rust_sifter(text: str, rate: float) -> str | None:
    """Shells out to the Rust sift-core binary for low-latency ONNX sifting."""
    try:
        process = subprocess.Popen(
            ["sift-core", "semantic", "--rate", str(rate)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=text)
        if process.returncode == 0:
            return stdout
        return None
    except FileNotFoundError:
        return None


def perform_hybrid_sift(text: str, rate: float = 0.5) -> str:
    """
    Intelligent router that chooses the optimal engine:
    1. Small/Medium texts (<30,000 chars) -> Rust/ONNX (Fast, low RAM).
    2. Large texts (>30,000 chars) -> Python/PyTorch (Flash Attention).
    """
    text = _enforce_input_size_guard(text)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in text:
        return text

    if len(text) < 30000:
        rust_result = _call_rust_sifter(text, rate)
        if rust_result:
            return rust_result
    # Fallback to PyTorch for large text or if Rust is missing
    return perform_semantic_sift(text, rate=rate)


def perform_semantic_sift(text: str, rate: float = 0.5) -> str:
    """Performs BERT-based prompt compression using PyTorch."""
    text = _enforce_input_size_guard(text)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in text:
        return text

    cache_key = get_cache_key("sift_chat", text, rate=rate)
    if cached := check_cache(cache_key):
        return cached

    start_model_warmup()
    wait_ms_raw = os.environ.get("SIFT_MODEL_READY_WAIT_MS", "1200")
    try:
        wait_ms = max(0, int(wait_ms_raw))
    except ValueError:
        wait_ms = 1200

    if not _MODEL_READY.wait(wait_ms / 1000.0):
        fallback = apply_heuristic_sieve(text)
        return "[Semantic-Sift: Models warming up - heuristic mode active]\n" + (fallback if fallback else text)

    if _COMPRESSOR is None:
        fallback = apply_heuristic_sieve(text)
        if _MODEL_WARMUP_ERROR:
            return f"[Semantic-Sift: Semantic model unavailable - heuristic mode active]\n{fallback if fallback else text}"
        return fallback if fallback else text

    try:
        results = _COMPRESSOR.compress_prompt(
            [text], rate=rate, force_tokens=["\n", "?"], chunk_end_tokens=[".", "\n"], return_word_label=False
        )
        result = results.get("compressed_prompt", text)
        set_cache(cache_key, result)
        return result
    except (AttributeError, RuntimeError, ValueError, TypeError) as e:
        return f"Error: {str(e)}"


def _bm25_fallback_ranking(query: str, documents: list[str], top_n: int) -> list[tuple[float, str]]:
    """
    Lightweight TF-IDF cosine-similarity ranking using only numpy + stdlib.
    Used as a fallback when sentence_transformers is not installed.
    Sufficient for keyword-dominant queries; no model download required.
    """
    import numpy as np

    def tokenize(text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    corpus = [query] + documents
    tokenized = [tokenize(t) for t in corpus]

    # Build vocabulary
    vocab: dict[str, int] = {}
    for tokens in tokenized:
        for tok in tokens:
            if tok not in vocab:
                vocab[tok] = len(vocab)

    N = len(corpus)
    V = len(vocab)

    # Term frequency matrix (N x V)
    tf = np.zeros((N, V), dtype=float)
    for i, tokens in enumerate(tokenized):
        for tok in tokens:
            tf[i, vocab[tok]] += 1
        if tf[i].sum() > 0:
            tf[i] /= tf[i].sum()

    # IDF vector
    df = (tf > 0).sum(axis=0).astype(float)
    idf = np.log((N + 1) / (df + 1)) + 1.0
    tfidf = tf * idf

    # Cosine similarity of each document against the query vector
    query_vec = tfidf[0]
    query_norm = float(np.linalg.norm(query_vec))

    scores: list[tuple[float, str]] = []
    for i, doc in enumerate(documents):
        doc_vec = tfidf[i + 1]
        doc_norm = float(np.linalg.norm(doc_vec))
        if query_norm > 0 and doc_norm > 0:
            score = float(np.dot(query_vec, doc_vec) / (query_norm * doc_norm))
        else:
            score = 0.0
        scores.append((score, doc))

    return sorted(scores, key=lambda x: x[0], reverse=True)[:top_n]


def perform_ranking(query: str, documents: list[str], top_n: int = 3) -> list[tuple[float, str]]:
    """
    Performs re-ranking with a three-tier strategy:
    1. Neural (sentence_transformers CrossEncoder) — highest fidelity, requires [neural] extra.
    2. TF-IDF cosine-similarity fallback (numpy only) — always available, no model download.
    Returns an empty list only on unexpected errors.
    """
    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder("BAAI/bge-reranker-base", device=get_device())
        scores = model.predict([[query, doc] for doc in documents])
        scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)[:top_n]
        return scored_docs
    except ImportError:
        # Neural extras not installed — fall through to TF-IDF
        pass
    except (RuntimeError, ValueError):
        pass

    try:
        return _bm25_fallback_ranking(query, documents, top_n)
    except Exception:
        return []


def perform_doc_sift(text: str, rate: float = 0.4) -> str:
    """Hybrid sifting for long documentation."""
    text = _enforce_input_size_guard(text)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in text:
        return text

    cleaned = apply_heuristic_sieve(text)
    return perform_hybrid_sift(cleaned, rate=rate)


def perform_compaction_summary(text: str) -> str:
    """Sifts session history for structural compaction snapshots."""
    text = _enforce_input_size_guard(text)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in text:
        return text

    priorities = re.findall(r"(?:Decision|Status|File|Task).*?:.*", text, re.IGNORECASE)
    context_hint = "\n".join(priorities) if priorities else ""
    priority_set = set(priorities)
    remaining_lines = [line for line in text.splitlines() if line.strip() not in priority_set]
    text_for_summary = "\n".join(remaining_lines).strip()

    if not text_for_summary:
        return f"## Structural Snapshot\n{context_hint}" if context_hint else text

    summary = perform_hybrid_sift(text_for_summary, rate=0.2)
    fidelity_score = calculate_vocabulary_overlap(text, summary)

    raw_threshold = os.environ.get("SIFT_COMPACTION_FIDELITY_THRESHOLD", "0.3")
    try:
        fidelity_threshold = max(0.0, min(1.0, float(raw_threshold)))
    except ValueError:
        fidelity_threshold = 0.3

    output = summary
    if context_hint:
        output = f"## Structural Snapshot\n{context_hint}\n\n## Semantic Summary\n{summary}"

    if fidelity_score < fidelity_threshold:
        output = f"🚨 Low fidelity compaction detected (Score: {fidelity_score:.2f})\n\n" + output

    return output


def calculate_vocabulary_overlap(original: str, compressed: str) -> float:
    """Returns vocabulary overlap ratio between original and compressed text."""
    original_words = set(re.findall(r"\w+", original.lower()))
    if not original_words:
        return 1.0
    compressed_words = set(re.findall(r"\w+", compressed.lower()))
    return len(original_words & compressed_words) / len(original_words)


def perform_extraction_cleaning(content: str, show_diff: bool = False) -> str:
    """Sifts raw OCR/Docling extractions."""
    content = _enforce_input_size_guard(content)

    # Self-Aware Bypass
    if "--- [Semantic-Sift Audit] ---" in content:
        return content

    refined = content
    for pattern in [r"Page \d+ of \d+", r"© .*? All rights reserved", r"---+\s*$", r"^\s*·\s*$"]:
        refined = re.sub(pattern, "", refined, flags=re.MULTILINE | re.IGNORECASE)

    cleaned = perform_hybrid_sift(refined, rate=0.7)

    if not show_diff:
        return cleaned

    diff_lines = list(
        difflib.unified_diff(content.splitlines(), cleaned.splitlines(), fromfile="original", tofile="sifted", lineterm="")
    )
    removed_lines = [line[1:] for line in diff_lines if line.startswith("-") and not line.startswith("---")]
    removed_section = "\n".join(removed_lines) if removed_lines else "(No explicit line removals detected.)"

    return cleaned + "\n\n--- REMOVED CONTENT ---\n" + removed_section

# --- [Semantic-Sift Audit] ---
