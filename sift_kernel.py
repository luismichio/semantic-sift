import re
import os
import time
import json
import hashlib
import threading
import difflib
from typing import Any
import telemetry_core

# Cache Configuration
CACHE_DIR = ".sift_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

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
        return requested_path

    root = workspace_root or os.environ.get("SIFT_WORKSPACE_ROOT") or os.getcwd()
    root_path = os.path.realpath(os.path.abspath(os.path.expanduser(root)))

    try:
        in_workspace = os.path.commonpath([requested_path, root_path]) == root_path
    except ValueError:
        in_workspace = False

    if not in_workspace:
        return (
            f"Error: Access denied for path '{path}'. "
            "Use a file path inside the current workspace or set "
            "SIFT_ALLOW_GLOBAL_READS=true to override."
        )

    return requested_path

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
        device_map=get_device()
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
    binary_exts = ['.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.html', '.htm']
    
    if ext not in binary_exts:
        return load_raw_text(path)
        
    md_converter = get_markitdown()
    if not md_converter:
        return f"Error: MarkItDown not installed. Cannot process {ext} files."

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
        with open(cache_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
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
    lines = text.splitlines()
    sifted = []
    # Broad timestamp support: ISO-8601, Legacy (YYMMDD), and Bracketed (Vercel)
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?)|(\d{6}\s\d{6}\s\d+)|(\[\d{2}:\d{2}:\d{2}(\.\d+)?\])')
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')
    metadata_pattern = re.compile(r'\s*(INFO|DEBUG|WARN|ERROR)\s+dfs\..*?:\s*')
    module_pattern = re.compile(r'^\s*[\d\.]+\s+(MB|KB|bytes|B)\s+[\w\-\.\/]+.*$', re.IGNORECASE)
    
    for line in lines:
        clean_line = timestamp_pattern.sub('', line).strip()
        clean_line = metadata_pattern.sub('', clean_line).strip()
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
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f: return f.read()
    return None

def set_cache(key: str, result: str) -> None:
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    with open(cache_path, "w", encoding="utf-8", errors="replace") as f: f.write(result)

def perform_semantic_sift(text: str, rate: float = 0.5) -> str:
    """Performs BERT-based prompt compression."""
    cache_key = get_cache_key("sift_chat", text, rate=rate)
    if cached := check_cache(cache_key): return cached
    
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
            [text], 
            rate=rate, 
            force_tokens=['\n', '?'], 
            chunk_end_tokens=['.', '\n'], 
            return_word_label=False
        )
        result = results.get('compressed_prompt', text)
        set_cache(cache_key, result)
        return result
    except (AttributeError, RuntimeError, ValueError, TypeError) as e:
        return f"Error: {str(e)}"

def perform_ranking(query: str, documents: list[str], top_n: int = 3) -> list[tuple[float, str]]:
    """Performs semantic re-ranking using BGE-Reranker."""
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder('BAAI/bge-reranker-base', device=get_device())
        scores = model.predict([[query, doc] for doc in documents])
        scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)[:top_n]
        return scored_docs
    except (ImportError, RuntimeError, ValueError):
        return []

def perform_doc_sift(text: str, rate: float = 0.4) -> str:
    """Hybrid sifting for long documentation."""
    cleaned = apply_heuristic_sieve(text)
    return perform_semantic_sift(cleaned, rate=rate)

def perform_compaction_summary(text: str) -> str:
    """Sifts session history for structural compaction snapshots."""
    # Heuristically find 'Decision', 'Status', 'File' markers to prioritize them
    # before semantic compression
    priorities = re.findall(r'(?:Decision|Status|File|Task).*?:.*', text, re.IGNORECASE)
    context_hint = "\n".join(priorities) if priorities else ""
    
    # We use a very aggressive rate for compaction (0.2) to save massive space
    summary = perform_semantic_sift(text, rate=0.2)

    # Fidelity signal: vocabulary overlap between original and compressed text
    fidelity_score = calculate_vocabulary_overlap(text, summary)
    raw_threshold = os.environ.get("SIFT_COMPACTION_FIDELITY_THRESHOLD", "0.3")
    try:
        fidelity_threshold = max(0.0, min(1.0, float(raw_threshold)))
    except ValueError:
        fidelity_threshold = 0.3

    if fidelity_score < fidelity_threshold:
        summary = (
            summary
            + f"\n\n[Semantic-Sift: Low fidelity compaction detected - vocabulary overlap: {fidelity_score:.1%}. "
            "Consider reviewing session manually.]"
        )
    
    if context_hint:
        return f"## Structural Snapshot\n{context_hint}\n\n## Semantic Summary\n{summary}"
    return summary

def calculate_vocabulary_overlap(original: str, compressed: str) -> float:
    """Returns vocabulary overlap ratio between original and compressed text."""
    original_words = set(re.findall(r"\w+", original.lower()))
    if not original_words:
        return 1.0
    compressed_words = set(re.findall(r"\w+", compressed.lower()))
    return len(original_words & compressed_words) / len(original_words)


def perform_extraction_cleaning(content: str, show_diff: bool = False) -> str:
    """Sifts raw OCR/Docling extractions."""
    refined = content
    for pattern in [r'Page \d+ of \d+', r'© .*? All rights reserved', r'---+\s*$', r'^\s*·\s*$']:
        refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)

    cleaned = perform_semantic_sift(refined, rate=0.7)
    if not show_diff:
        return cleaned

    diff_lines = list(
        difflib.unified_diff(
            content.splitlines(),
            cleaned.splitlines(),
            fromfile="original",
            tofile="sifted",
            lineterm="",
        )
    )
    removed_lines = [line[1:] for line in diff_lines if line.startswith("-") and not line.startswith("---")]
    removed_section = "\n".join(removed_lines) if removed_lines else "(No explicit line removals detected.)"
    return cleaned + "\n\n--- REMOVED CONTENT ---\n" + removed_section
