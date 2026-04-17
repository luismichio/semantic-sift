import re
import os
import json
import uuid
import time
import torch
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Global Telemetry Config
SESSION_ID = str(uuid.uuid4())
TELEMETRY_FILE = ".sift_telemetry.json"
START_TIME = datetime.now().isoformat()

# Device Detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Create the MCP server
mcp = FastMCP("Semantic-Sift")

def log_telemetry(tool_name: str, original_chars: int, final_chars: int, latency_ms: float):
    """Logs tool performance metrics to a persistent JSON file."""
    try:
        data = {}
        if os.path.exists(TELEMETRY_FILE):
            with open(TELEMETRY_FILE, "r") as f:
                data = json.load(f)
        
        if SESSION_ID not in data:
            data[SESSION_ID] = {
                "start_time": START_TIME,
                "tools": {}
            }
        
        tool_stats = data[SESSION_ID]["tools"].get(tool_name, {
            "calls": 0,
            "original_chars": 0,
            "final_chars": 0,
            "total_latency_ms": 0
        })
        
        tool_stats["calls"] += 1
        tool_stats["original_chars"] += original_chars
        tool_stats["final_chars"] += final_chars
        tool_stats["total_latency_ms"] += latency_ms
        
        data[SESSION_ID]["tools"][tool_name] = tool_stats
        
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        # Silently fail for telemetry to avoid breaking primary tool functionality
        pass

@mcp.tool()
async def sift_logs(raw_text: str) -> str:
    """
    Sifts through raw technical logs (Vercel, GitHub, Console) 
    to remove noise and keep only the instructional signal.
    """
    start_t = time.time()
    lines = raw_text.splitlines()
    sifted = []
    
    # Common noise patterns to remove
    # 1. Timestamps (e.g., 2026-04-13T02:18:19Z)
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?\s*')
    
    # 2. Progress bars or repetitive build status lines
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')

    # 3. Webpacker/Vite successful module listings (too noisy)
    module_pattern = re.compile(r'^\s*[\d\.]+\s+[\w\-\.\/]+\s+\d+\s+bytes.*$')

    for line in lines:
        # Clean timestamp
        clean_line = timestamp_pattern.sub('', line).strip()
        
        # Skip if empty or matches noise
        if not clean_line:
            continue
        if progress_pattern.search(clean_line):
            continue
        if module_pattern.match(clean_line):
            continue
            
        sifted.append(clean_line)
        
    result = "\n".join(sifted)
    latency = (time.time() - start_t) * 1000
    log_telemetry("sift_logs", len(raw_text), len(result), latency)
    return result

@mcp.tool()
async def sift_chat(text: str, rate: float = 0.5) -> str:
    """
    Semantically prunes conversation history using LLMLingua-2.
    Preserves instructions while stripping verbal filler.
    """
    start_t = time.time()
    try:
        from llmlingua import PromptCompressor
        
        # Initialize compressor with LLMLingua-2 model
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True,
            device_map=DEVICE
        )
        
        # Perform compression
        results = compressor.compress_prompt(
            [text],
            rate=rate,
            force_tokens=['\n', '?'], # Protect structure and questions
            chunk_end_tokens=['.', '\n'],
            return_word_label=False
        )
        
        result = results.get('compressed_prompt', text)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_chat", len(text), len(result), latency)
        return result
    except Exception as e:
        return f"Error during semantic sifting: {str(e)}"

@mcp.tool()
async def sift_doc(text: str, budget_tokens: int = 1000) -> str:
    """
    Condenses long documents (MDX, PDF text) using a multi-stage approach:
    1. Heuristic Sieve (Removes structural noise)
    2. LLMLingua-2 Sift (Semantically prunes to the token budget)
    """
    start_t = time.time()
    # Stage 1: Structural cleaning
    cleaned = await sift_logs(text)
    
    # Stage 2: Calculate target rate if text is still too long
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True,
            device_map=DEVICE
        )
        
        # We protect technical tokens to ensure we don't break code/entities
        results = compressor.compress_prompt(
            [cleaned],
            rate=0.4, # Target aggressive 60% reduction for long docs
            force_tokens=['[', ']', '{', '}', '/', '\\', '.', '_'], # Protect paths/JSON
            chunk_end_tokens=['\n', '.', ';'],
            return_word_label=False
        )
        result = results.get('compressed_prompt', cleaned)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_doc", len(text), len(result), latency)
        return result
    except Exception as e:
        return f"Error during document sifting: {str(e)}"

@mcp.tool()
async def sift_extraction(content: str, source_type: str = "markdown") -> str:
    """
    Specifically designed to refine outputs from Docling or LiteParse.
    Removes extraction-specific noise (debris) and prunes dense technical docs
    for high-quality RAG indexing.
    """
    start_t = time.time()
    # 1. Targeted Document Debris Removal (Heuristic)
    debris_patterns = [
        r'Page \d+ of \d+',
        r'© .*? All rights reserved',
        r'---+\s*$', # Empty separator lines
        r'^\s*·\s*$', # Single bullets on lines
    ]
    
    refined = content
    for pattern in debris_patterns:
        refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)

    # 2. Semantic Sift (Keep important signal)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(
            model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
            use_llmlingua2=True,
            device_map=DEVICE
        )
        
        results = compressor.compress_prompt(
            [refined],
            rate=0.7, # Keep 70% (gentle sift for indexing)
            force_tokens=['\n', '|', '-', ':', '#'], # Protect Markdown structure
            chunk_end_tokens=['\n', '.'],
            return_word_label=False
        )
        result = results.get('compressed_prompt', refined)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_extraction", len(content), len(result), latency)
        return result
    except Exception as e:
        return f"Error during extraction sifting: {str(e)}"

@mcp.tool()
async def get_sift_stats(scope: str = "current") -> str:
    """
    Returns telemetry stats for the sifting process.
    'scope' can be 'current' (active session) or 'all' (historical).
    """
    if not os.path.exists(TELEMETRY_FILE):
        return "No telemetry data found."
    
    try:
        with open(TELEMETRY_FILE, "r") as f:
            data = json.load(f)
        
        target_sessions = []
        if scope == "current":
            if SESSION_ID in data:
                target_sessions.append(data[SESSION_ID])
        else:
            target_sessions = list(data.values())
        
        if not target_sessions:
            return "No data found for the specified scope."
        
        total_calls = 0
        total_orig = 0
        total_final = 0
        total_latency = 0
        tool_breakdown = {}
        
        for session in target_sessions:
            for tool, stats in session.get("tools", {}).items():
                total_calls += stats["calls"]
                total_orig += stats["original_chars"]
                total_final += stats["final_chars"]
                total_latency += stats["total_latency_ms"]
                
                if tool not in tool_breakdown:
                    tool_breakdown[tool] = {"calls": 0, "saved": 0}
                tool_breakdown[tool]["calls"] += stats["calls"]
                tool_breakdown[tool]["saved"] += (stats["original_chars"] - stats["final_chars"])

        saved = total_orig - total_final
        ratio = (saved / total_orig * 100) if total_orig > 0 else 0
        avg_latency = (total_latency / total_calls) if total_calls > 0 else 0
        
        output = [
            f"--- Semantic-Sift Telemetry ({scope.capitalize()}) ---",
            f"Total Sift Calls: {total_calls}",
            f"Characters Processed: {total_orig:,}",
            f"Characters Pruned: {saved:,} ({ratio:.1f}% reduction)",
            f"Avg Latency: {avg_latency:.1f}ms",
            "\nBreakdown by Tool:"
        ]
        
        for tool, stats in tool_breakdown.items():
            output.append(f"- {tool}: {stats['calls']} calls, {stats['saved']:,} chars saved")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error reading telemetry: {str(e)}"

if __name__ == "__main__":
    mcp.run()
