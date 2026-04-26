import os
import sys
import json
import uuid
import time
import hashlib
import urllib.request
import re
from datetime import datetime

# OpenTelemetry Imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    import logging
    # Mock trace if not available
    class MockTracer:
        def start_as_current_span(self, name, *args, **kwargs):
            class MockSpan:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def set_attribute(self, *args): pass
            return MockSpan()
    class MockTrace:
        def get_tracer(self, name): return MockTracer()
    trace = MockTrace()
    OTEL_AVAILABLE = False

# Persistent Configuration
TELEMETRY_FILE = ".sift_telemetry.json"
IDENTITY_FILE = ".sift_identity"

# Identity & Licensing
SIFT_CLIENT_ID = os.environ.get("SIFT_CLIENT_ID", "Generic CLI")
SIFT_LICENSE_KEY = os.environ.get("SIFT_LICENSE_KEY", None)
SIFT_TELEMETRY_URL = os.environ.get("SIFT_TELEMETRY_URL", "https://www.luiskobayashi.com/api/sift")
SIFT_TIER = "Commercial" if SIFT_LICENSE_KEY else "Community"

# Privacy Kill-Switch (Meechi Compliance)
SIFT_TELEMETRY_DISABLED = os.environ.get("SIFT_TELEMETRY_DISABLED", "false").lower() == "true"

# --- Privacy Shield (Secret Redaction) ---

def redact_secrets(text: str) -> str:
    """Masks common secret patterns (API keys, PATs, Tokens) in a given string."""
    if not isinstance(text, str): return str(text)
    
    # Patterns for common secrets
    patterns = [
        (r'(github_pat_[a-zA-Z0-9_]{20,})', '[REDACTED_GITHUB_PAT]'),
        (r'(sk-[a-zA-Z0-9]{20,})', '[REDACTED_OPENAI_KEY]'),
        (r'(xox[bp]-[a-zA-Z0-9-]{10,})', '[REDACTED_SLACK_TOKEN]'),
        (r'(\b[a-fA-F0-9]{32,64}\b)', '[REDACTED_HASH_OR_KEY]'), # Generic high-entropy strings
        (r'(password|secret|token|key)\s*[:=]\s*[^\s,]+', r'\1=[REDACTED]')
    ]
    
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted

# --- OTel Initialization (Isolated Provider) ---
_TRACER = None

def get_tracer():
    global _TRACER
    if SIFT_TELEMETRY_DISABLED or not OTEL_AVAILABLE:
        return trace.get_tracer(__name__)
    
    if _TRACER is None:
        # Create an isolated provider to avoid conflict with host apps
        resource = Resource(attributes={"service.name": "semantic-sift-mcp"})
        provider = TracerProvider(resource=resource)
        
        # Simple console exporter for local verification
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        
        _TRACER = provider.get_tracer(__name__)
    
    return _TRACER

# --- Echo Detection (Disk-Based Cache) ---
# Use absolute path to ensure consistency across separate processes
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sift_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def check_echo(text: str) -> bool:
    """Checks if the text content has been processed recently (Disk-persistent)."""
    if SIFT_TELEMETRY_DISABLED or not text or len(text) < 100:
        return False
    
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    echo_path = os.path.join(CACHE_DIR, f"echo_{content_hash}.tmp")
    now = time.time()
    
    if os.path.exists(echo_path):
        try:
            with open(echo_path, "r") as f:
                expiry = float(f.read().strip())
            if now < expiry:
                return True
            else:
                os.remove(echo_path) # Expired
        except: pass
    
    # Record current hash to disk
    try:
        with open(echo_path, "w") as f:
            f.write(str(now + 30)) # 30s TTL
    except: pass
    return False

# --- Audit Header Logic ---

def generate_audit_header(original_len: int, sifted_len: int, latency_ms: float, is_echo: bool = False) -> str:
    """Generates a Markdown audit header based on SIFT_AUDIT_HEADER preference."""
    if SIFT_TELEMETRY_DISABLED:
        return ""
    
    style = os.environ.get("SIFT_AUDIT_HEADER", "full").lower()
    if style == "silent":
        return ""
        
    reduction = (1 - (sifted_len / original_len)) * 100 if original_len > 0 else 0
    guard_status = "Trace-Verified (No Echo)" if not is_echo else "🚨 ECHO DETECTED (Bypassed)"
    
    if style == "minimal":
        return f"[Semantic-Sift: {reduction:.1f}% Savings | ⚡ {latency_ms:.1f}ms]\n\n"
        
    # Default: Full
    header = [
        "--- [Semantic-Sift Audit] ---",
        f"📊 Reduction: {reduction:.1f}% ({original_len/1024:.1f}KB -> {sifted_len/1024:.1f}KB)",
        f"🛡️ Guard: {guard_status}",
        f"⚡ Latency: {latency_ms:.1f}ms",
        "-----------------------------\n"
    ]
    return "\n".join(header)

def estimate_tokens(text: str) -> int:
    """Provides a fast, high-fidelity token estimate (Standard 4 chars/token heuristic)."""
    if not text: return 0
    return max(1, len(text) // 4)

# Generate or load persistent anonymous Machine ID
def get_machine_id() -> str:
    if SIFT_TELEMETRY_DISABLED: return "anonymous-user"
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

def send_telemetry_pulse(tool_name: str, original: int, final: int, latency: float, tier_override: str = None, client_id_override: str = None, agent_label: str = None, file_ext: str = None):
    """Sends an anonymous, blocking telemetry pulse (skipped if disabled)."""
    if SIFT_TELEMETRY_DISABLED or not SIFT_TELEMETRY_URL: return
    
    # Safety: Redact any potential secrets in metadata
    safe_tool = redact_secrets(tool_name)
    safe_label = redact_secrets(agent_label) if agent_label else None
    
    # Safety: If tool_name indicates a test/handshake, force it out of Real-World tiers
    is_test = any(word in safe_tool.lower() for word in ['test', 'handshake', 'diag', 'bench'])
    final_tier = tier_override if tier_override else (SIFT_TIER if not is_test else "Internal-Testing")
    final_client = client_id_override if client_id_override else SIFT_CLIENT_ID
    
    orig_tokens = estimate_tokens(" " * original)
    final_tokens = estimate_tokens(" " * final)
    
    payload = {
        "machine_id": MACHINE_ID,
        "client_id": final_client,
        "tier": final_tier,
        "agent_label": safe_label,
        "tool_name": safe_tool,
        "file_ext": file_ext,
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
        # Security: Enforce HTTP/HTTPS schemes only (Bandit B310)
        if not url.startswith(('http://', 'https://')):
            continue
            
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'Content-Type': 'application/json'}, 
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as r: # nosec B310
                if r.status in [200, 201]:
                    return 
        except Exception:
            continue

def log_telemetry(session_id: str, start_time: str, tool_name: str, original_chars: int, final_chars: int, latency_ms: float, cache_hit: bool = False, client_id_override: str = None, agent_label: str = None, file_ext: str = None):
    """Logs tool performance metrics locally and triggers global pulse (skipped if disabled)."""
    if SIFT_TELEMETRY_DISABLED: return

    # Safety: Redact metadata
    safe_tool = redact_secrets(tool_name)
    safe_label = redact_secrets(agent_label) if agent_label else None

    try:
        data = {}
        if os.path.exists(TELEMETRY_FILE):
            with open(TELEMETRY_FILE, "r") as f:
                data = json.load(f)
        
        if session_id not in data:
            data[session_id] = {"start_time": start_time, "tools": {}}
            
        tool_stats = data[session_id]["tools"].get(safe_tool, {
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
            
        data[session_id]["tools"][safe_tool] = tool_stats
        
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        if not cache_hit:
            send_telemetry_pulse(safe_tool, original_chars, final_chars, latency_ms, client_id_override=client_id_override, agent_label=safe_label, file_ext=file_ext)
            
    except Exception:
        pass
