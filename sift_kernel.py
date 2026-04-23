import re
import os
import time
import json
import hashlib
import telemetry_core

# Cache Configuration
CACHE_DIR = ".sift_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Lazy Device Detection
DEVICE = "cpu"
_DEVICE = None
def get_device():
    global _DEVICE, DEVICE
    if _DEVICE is None:
        try:
            import torch
            _DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        except:
            _DEVICE = "cpu"
        DEVICE = _DEVICE
    return _DEVICE

def load_file_content(path: str) -> str:
    """Safely loads file content with encoding fallbacks."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file (latin-1 fallback failed): {str(e)}"
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

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

def get_cache_key(tool_name: str, text: str, **kwargs) -> str:
    payload = f"{tool_name}:{text}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()

def check_cache(key: str) -> str | None:
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f: return f.read()
    return None

def set_cache(key: str, result: str):
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    with open(cache_path, "w", encoding="utf-8", errors="replace") as f: f.write(result)

def perform_semantic_sift(text: str, rate: float = 0.5) -> str:
    """Performs BERT-based prompt compression."""
    cache_key = get_cache_key("sift_chat", text, rate=rate)
    if cached := check_cache(cache_key): return cached
    
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", 
            use_llmlingua2=True, 
            device_map=get_device()
        )
        results = compressor.compress_prompt(
            [text], 
            rate=rate, 
            force_tokens=['\n', '?'], 
            chunk_end_tokens=['.', '\n'], 
            return_word_label=False
        )
        result = results.get('compressed_prompt', text)
        set_cache(cache_key, result)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def perform_ranking(query: str, documents: list[str], top_n: int = 3) -> list[tuple[float, str]]:
    """Performs semantic re-ranking using BGE-Reranker."""
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder('BAAI/bge-reranker-base', device=get_device())
        scores = model.predict([[query, doc] for doc in documents])
        scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)[:top_n]
        return scored_docs
    except Exception:
        return []

def perform_doc_sift(text: str) -> str:
    """Hybrid sifting for long documentation."""
    cleaned = apply_heuristic_sieve(text)
    return perform_semantic_sift(cleaned, rate=0.4)

def perform_compaction_summary(text: str) -> str:
    """Sifts session history for structural compaction snapshots."""
    # Heuristically find 'Decision', 'Status', 'File' markers to prioritize them
    # before semantic compression
    priorities = re.findall(r'(?:Decision|Status|File|Task).*?:.*', text, re.IGNORECASE)
    context_hint = "\n".join(priorities) if priorities else ""
    
    # We use a very aggressive rate for compaction (0.2) to save massive space
    summary = perform_semantic_sift(text, rate=0.2)
    
    if context_hint:
        return f"## Structural Snapshot\n{context_hint}\n\n## Semantic Summary\n{summary}"
    return summary

def perform_extraction_cleaning(content: str) -> str:
    """Sifts raw OCR/Docling extractions."""
    refined = content
    for pattern in [r'Page \d+ of \d+', r'© .*? All rights reserved', r'---+\s*$', r'^\s*·\s*$']:
        refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)
    return perform_semantic_sift(refined, rate=0.7)
