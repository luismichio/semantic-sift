import os
import json
import uuid
import time
import hashlib
import urllib.request
import re
import threading
import logging
from datetime import datetime

# OpenTelemetry Imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
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
    trace = MockTrace()  # type: ignore[assignment]
    OTEL_AVAILABLE = False

# Persistent Configuration
TELEMETRY_FILE = ".sift_telemetry.json"
IDENTITY_FILE = ".sift_identity"


def detect_client_id() -> str:
    """Infer the calling IDE/CLI from environment variables and parent process name.

    Resolution order:
    1. Explicit ``SIFT_CLIENT_ID`` env var (always wins).
    2. IDE-specific env vars set by the host process.
    3. Parent process name match (requires no extra deps — uses ``psutil`` if
       available, otherwise falls back to ``/proc`` on Linux or ``wmic`` on
       Windows via subprocess — skipped silently on failure).
    4. ``"Generic CLI"`` fallback.
    """
    explicit = os.environ.get("SIFT_CLIENT_ID")
    if explicit:
        return explicit

    # Known IDE env var fingerprints
    _ENV_MAP: list[tuple[str, str]] = [
        ("CLAUDE_TOOL_NAME", "Claude"),
        ("CLAUDE_AGENT_NAME", "Claude"),
        ("QWEN_TOOL_NAME", "Qwen"),
        ("CODEX_TOOL_NAME", "Codex"),
        ("GEMINI_SESSION_ID", "Gemini"),
        ("CURSOR_TRACE_ID", "Cursor"),
        ("WINDSURF_TOOL_ARGS", "Windsurf"),
        ("JETBRAINS_IDE_URL", "JetBrains"),
        ("CLINE_TASK_ID", "Cline"),
    ]
    for env_var, label in _ENV_MAP:
        if os.environ.get(env_var):
            return label

    # Parent process name heuristic
    _PROC_MAP: list[tuple[str, str]] = [
        ("opencode", "OpenCode"),
        ("cursor", "Cursor"),
        ("windsurf", "Windsurf"),
        ("claude", "Claude"),
        ("gemini", "Gemini"),
        ("codex", "Codex"),
        ("cline", "Cline"),
        ("jetbrains", "JetBrains"),
    ]
    try:
        import psutil  # type: ignore[import-untyped]
        proc = psutil.Process(os.getpid())
        ancestors = [proc] + proc.parents()
        for ancestor in ancestors:
            try:
                name = ancestor.name().lower()
                for fragment, label in _PROC_MAP:
                    if fragment in name:
                        return label
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        pass  # psutil not installed — skip silently

    return "Generic CLI"


# Identity & Licensing
SIFT_CLIENT_ID = detect_client_id()
SIFT_LICENSE_KEY = os.environ.get("SIFT_LICENSE_KEY", None)
SIFT_TELEMETRY_URL = os.environ.get("SIFT_TELEMETRY_URL", "https://www.luiskobayashi.com/api/sift")
SIFT_TIER = "Commercial" if SIFT_LICENSE_KEY else "Community"

# Privacy Kill-Switch (Meechi Compliance)
SIFT_TELEMETRY_DISABLED = os.environ.get("SIFT_TELEMETRY_DISABLED", "false").lower() == "true"

_PULSE_LOCK = threading.Lock()
_PULSE_LAST_SENT: dict[str, float] = {}
_PULSE_PENDING: dict[str, tuple[str, int, int, float, str | None, str | None, str | None, str | None]] = {}
LOGGER = logging.getLogger("semantic_sift.telemetry")


def _rate_limit_seconds() -> float:
    raw = os.environ.get("SIFT_PULSE_RATE_LIMIT_S", "10")
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 10.0

# --- Privacy Shield (Secret Redaction) ---

_SECRET_PATTERNS: list[tuple[str, str]] = [
    (r'github_pat_[a-zA-Z0-9_]{20,}', '[REDACTED_GITHUB_PAT]'),
    (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_OPENAI_KEY]'),
    (r'xox[bp]-[a-zA-Z0-9-]{10,}', '[REDACTED_SLACK_TOKEN]'),
    (r'\b[a-fA-F0-9]{32,64}\b', '[REDACTED_HASH_OR_KEY]'),
    (r'(password|secret|token|key)\s*[:=]\s*[^\s,]+', r'\1=[REDACTED]'),
]

# Patterns rewritten to use a generic [REDACTED] label — no secret-type hint.
_SECRET_PATTERNS_GENERIC: list[tuple[str, str]] = [
    (r'github_pat_[a-zA-Z0-9_]{20,}', '[REDACTED]'),
    (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED]'),
    (r'xox[bp]-[a-zA-Z0-9-]{10,}', '[REDACTED]'),
    (r'\b[a-fA-F0-9]{32,64}\b', '[REDACTED]'),
    (r'(password|secret|token|key)\s*[:=]\s*[^\s,]+', r'\1=[REDACTED]'),
]


def redact_secrets(text: str) -> str:
    """Masks secret patterns with descriptive labels. Use for local debug logs only."""
    if not isinstance(text, str):
        return str(text)
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def redact_secrets_for_telemetry(text: str) -> str:
    """Masks secret patterns with a generic [REDACTED] label.

    Use this in all telemetry paths (remote pulses, .sift_telemetry.json) to
    avoid leaking secret-type metadata to observers of the telemetry stream.
    """
    if not isinstance(text, str):
        return str(text)
    result = text
    for pattern, replacement in _SECRET_PATTERNS_GENERIC:
        result = re.sub(pattern, replacement, result)
    return result

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
        except (OSError, ValueError) as exc:
            LOGGER.debug("Failed reading echo marker '%s': %s", echo_path, exc)

    # Record current hash to disk
    try:
        with open(echo_path, "w") as f:
            f.write(str(now + 30)) # 30s TTL
    except OSError as exc:
        LOGGER.debug("Failed writing echo marker '%s': %s", echo_path, exc)
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
    if not text:
        return 0
    return max(1, len(text) // 4)


def _ensure_identity_ignored() -> None:
    gitignore_path = os.path.join(os.getcwd(), ".gitignore")
    try:
        content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        if IDENTITY_FILE not in content:
            prefix = "\n" if content and not content.endswith("\n") else ""
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(f"{prefix}{IDENTITY_FILE}\n")
    except OSError as exc:
        LOGGER.debug("Failed ensuring identity ignore entry in '.gitignore': %s", exc)

# Generate or load persistent anonymous Machine ID
def get_machine_id() -> str:
    if SIFT_TELEMETRY_DISABLED:
        return "anonymous-user"
    _ensure_identity_ignored()
    path = os.path.join(os.getcwd(), IDENTITY_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except OSError as exc:
            LOGGER.debug("Failed reading identity file '%s': %s", path, exc)
    new_id = str(uuid.uuid4())
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_id)
    except OSError as exc:
        LOGGER.debug("Failed writing identity file '%s': %s", path, exc)
    return new_id

MACHINE_ID = get_machine_id()

def _send_telemetry_pulse_now(tool_name: str, original: int, final: int, latency: float, tier_override: str | None = None, client_id_override: str | None = None, agent_label: str | None = None, file_ext: str | None = None) -> None:
    """Sends an anonymous telemetry pulse immediately (internal)."""
    if SIFT_TELEMETRY_DISABLED or not SIFT_TELEMETRY_URL:
        return

    # Safety: Redact any potential secrets in metadata.
    # Use generic [REDACTED] label (not type-specific) to avoid leaking
    # secret-type hints to telemetry observers.
    safe_tool = redact_secrets_for_telemetry(tool_name)
    safe_label = redact_secrets_for_telemetry(agent_label) if agent_label else None

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


def send_telemetry_pulse(tool_name: str, original: int, final: int, latency: float, tier_override: str | None = None, client_id_override: str | None = None, agent_label: str | None = None, file_ext: str | None = None) -> None:
    """Queues an anonymous telemetry pulse and sends it asynchronously with rate limiting."""
    if SIFT_TELEMETRY_DISABLED or not SIFT_TELEMETRY_URL:
        return

    key = f"{client_id_override or SIFT_CLIENT_ID}:{tool_name}"
    now = time.time()
    interval = _rate_limit_seconds()

    with _PULSE_LOCK:
        last_sent = _PULSE_LAST_SENT.get(key, 0.0)
        if interval > 0 and (now - last_sent) < interval:
            _PULSE_PENDING[key] = (tool_name, original, final, latency, tier_override, client_id_override, agent_label, file_ext)
            return
        _PULSE_LAST_SENT[key] = now

    def _worker(payload):
        _send_telemetry_pulse_now(*payload)
        if interval <= 0:
            return
        with _PULSE_LOCK:
            pending = _PULSE_PENDING.pop(key, None)
            if pending:
                _PULSE_LAST_SENT[key] = time.time()
        if pending:
            _send_telemetry_pulse_now(*pending)

    payload = (tool_name, original, final, latency, tier_override, client_id_override, agent_label, file_ext)
    threading.Thread(target=_worker, args=(payload,), daemon=True, name="semantic-sift-pulse").start()

def log_telemetry(session_id: str, start_time: str, tool_name: str, original_chars: int, final_chars: int, latency_ms: float, cache_hit: bool = False, client_id_override: str | None = None, agent_label: str | None = None, file_ext: str | None = None) -> None:
    """Logs tool performance metrics locally and triggers global pulse (skipped if disabled)."""
    if SIFT_TELEMETRY_DISABLED:
        return

    # Safety: Redact metadata. Generic label only — no secret-type hints in stored logs.
    safe_tool = redact_secrets_for_telemetry(tool_name)
    safe_label = redact_secrets_for_telemetry(agent_label) if agent_label else None

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
        LOGGER.exception("Failed to write telemetry record for tool '%s'", safe_tool)
