import os
import json
import uuid
import time
import hashlib
import urllib.request
from datetime import datetime

# Persistent Configuration
TELEMETRY_FILE = ".sift_telemetry.json"
IDENTITY_FILE = ".sift_identity"

# Identity & Licensing
SIFT_CLIENT_ID = os.environ.get("SIFT_CLIENT_ID", "Generic CLI")
SIFT_LICENSE_KEY = os.environ.get("SIFT_LICENSE_KEY", None)
SIFT_TELEMETRY_URL = os.environ.get("SIFT_TELEMETRY_URL", "https://www.luiskobayashi.com/api/sift")
SIFT_TIER = "Commercial" if SIFT_LICENSE_KEY else "Community"

def estimate_tokens(text: str) -> int:
    """Provides a fast, high-fidelity token estimate (Standard 4 chars/token heuristic)."""
    if not text: return 0
    # LLM Industry Standard: ~4 characters per token for English
    return max(1, len(text) // 4)

# Generate or load persistent anonymous Machine ID
def get_machine_id() -> str:
    path = os.path.join(os.getcwd(), IDENTITY_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r") as f: return f.read().strip()
        except: pass
    new_id = str(uuid.uuid4())
    try:
        with open(path, "w") as f: f.write(new_id)
    except: pass
    return new_id

MACHINE_ID = get_machine_id()

def send_telemetry_pulse(tool_name: str, original: int, final: int, latency: float):
    """Sends an anonymous, blocking telemetry pulse with both chars and tokens."""
    if not SIFT_TELEMETRY_URL: return
    
    orig_tokens = estimate_tokens(" " * original) # Estimate based on length
    final_tokens = estimate_tokens(" " * final)
    
    payload = {
        "machine_id": MACHINE_ID,
        "client_id": SIFT_CLIENT_ID,
        "tier": SIFT_TIER,
        "tool_name": tool_name,
        "original_chars": original,
        "final_chars": final,
        "original_tokens": orig_tokens,
        "final_tokens": final_tokens,
        "tokens_saved": orig_tokens - final_tokens,
        "latency_ms": latency,
        "timestamp": datetime.now().isoformat()
    }
    
    urls_to_try = [SIFT_TELEMETRY_URL]
    if not SIFT_TELEMETRY_URL.endswith('/'):
        urls_to_try.append(SIFT_TELEMETRY_URL + '/')

    for url in urls_to_try:
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'Content-Type': 'application/json'}, 
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status in [200, 201]:
                    return 
        except Exception:
            continue

def log_telemetry(session_id: str, start_time: str, tool_name: str, original_chars: int, final_chars: int, latency_ms: float, cache_hit: bool = False):
    """Logs tool performance metrics locally and triggers global pulse."""
    try:
        data = {}
        if os.path.exists(TELEMETRY_FILE):
            with open(TELEMETRY_FILE, "r") as f:
                data = json.load(f)
        
        if session_id not in data:
            data[session_id] = {"start_time": start_time, "tools": {}}
            
        tool_stats = data[session_id]["tools"].get(tool_name, {
            "calls": 0, "original_chars": 0, "final_chars": 0, 
            "original_tokens": 0, "final_tokens": 0,
            "total_latency_ms": 0, "cache_hits": 0
        })
        
        orig_tokens = estimate_tokens(" " * original_chars)
        final_tokens = estimate_tokens(" " * final_chars)

        tool_stats["calls"] += 1
        tool_stats["original_chars"] += original_chars
        tool_stats["final_chars"] += final_chars
        tool_stats["original_tokens"] += orig_tokens
        tool_stats["final_tokens"] += final_tokens
        tool_stats["total_latency_ms"] += latency_ms
        if cache_hit:
            tool_stats["cache_hits"] = tool_stats.get("cache_hits", 0) + 1
            
        data[session_id]["tools"][tool_name] = tool_stats
        
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        if not cache_hit:
            send_telemetry_pulse(tool_name, original_chars, final_chars, latency_ms)
            
    except Exception:
        pass
