# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

"""Telemetry, tracing, and privacy controls for Semantic-Sift. Canonical import path."""

import os
import json
import time
import hashlib
import urllib.request
import re
import threading
import logging
from datetime import datetime
from typing import Optional

# OpenTelemetry Imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from opentelemetry.sdk.resources import Resource

    OTEL_AVAILABLE = True
except ImportError:
    # Mock trace if not available
    class MockTracer:
        def start_as_current_span(self, name, *args, **kwargs):
            class MockSpan:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def set_attribute(self, *args):
                    pass

            return MockSpan()

    class MockTrace:
        def get_tracer(self, name):
            return MockTracer()

    trace = MockTrace()  # type: ignore[assignment]
    OTEL_AVAILABLE = False

# Persistent Configuration
_TELEMETRY_LOCK = threading.Lock()  # Guards concurrent read-modify-write on TELEMETRY_FILE


def detect_client_id() -> str:
    """Infer the calling IDE/CLI from environment variables and parent process name."""
    explicit = os.environ.get("SIFT_CLIENT_ID") or os.environ.get("CPP_CLIENT_ID")
    if explicit:
        return explicit

    # Known IDE env var fingerprints.
    _ENV_MAP: list[tuple[str, str]] = [
        ("ANTIGRAVITY_AGENT", "Google Antigravity"),
        ("ANTIGRAVITY_EDITOR_APP_ROOT", "Google Antigravity"),
        ("ANTIGRAVITY_TRAJECTORY_ID", "Google Antigravity"),
        ("OPENCODE", "OpenCode"),
        ("OPENCODE_PID", "OpenCode"),
        ("VSCODE_PID", "VSCode"),
        ("VSCODE_IPC_HOOK_CLI", "VSCode"),
        ("CURSOR_TRACE_ID", "Cursor"),
        ("WINDSURF_TOOL_ARGS", "Windsurf"),
        ("WINDSURF_SESSION_ID", "Windsurf"),
        ("__KIRO_MCP", "Kiro"),
        ("KIRO_SESSION_ID", "Kiro"),
        ("CONTINUE_SERVER_PORT", "Continue"),
        ("JETBRAINS_IDE_URL", "JetBrains"),
        ("CLINE_TASK_ID", "Cline"),
        ("CLAUDE_TOOL_NAME", "Claude"),
        ("CLAUDE_AGENT_NAME", "Claude"),
        ("GEMINI_SESSION_ID", "Gemini"),
    ]

    for env_var, label in _ENV_MAP:
        if os.environ.get(env_var):
            return label

    # Parent process name heuristic
    _PROC_MAP: list[tuple[str, str]] = [
        ("antigravity", "Google Antigravity"),
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
        pass

    return "Generic CLI"


# Identity & Protocol standard normalization
SIFT_CLIENT_ID = detect_client_id()

SIFT_TELEMETRY_URL = os.environ.get("CPP_TELEMETRY_URL") or os.environ.get(
    "SIFT_TELEMETRY_URL", "https://www.luiskobayashi.com/api/sift"
)

# Optional silent fallback endpoint. Only attempted when the primary URL fails.
# Never hardcoded — user-supplied via env var. Default: no fallback.
SIFT_TELEMETRY_FALLBACK_URL: str = os.environ.get("SIFT_TELEMETRY_FALLBACK_URL", "")

# Telemetry Consent Gate (Opt-In by Default)
# Telemetry runs ONLY when SIFT_TELEMETRY_OPTED_IN=true is explicitly set.
# Legacy kill-switch SIFT_TELEMETRY_DISABLED=true is still respected for backward compat.
def _check_opt_in() -> bool:
    # 1. Environment variable (Highest priority)
    if os.environ.get("SIFT_TELEMETRY_OPTED_IN", "").lower() == "true":
        return True

    # 2. Local .gemini/settings.json (Fallback for IDE hook subprocesses)
    try:
        def find_in_dict(d: dict, key: str) -> Optional[str]:
            if key in d:
                return str(d[key])
            for v in d.values():
                if isinstance(v, dict):
                    res = find_in_dict(v, key)
                    if res:
                        return res
            return None

        # Search project root from CWD
        curr = os.path.abspath(os.getcwd())
        while True:
            settings_path = os.path.join(curr, ".gemini", "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    val = find_in_dict(settings, "SIFT_TELEMETRY_OPTED_IN")
                    if val and val.lower() == "true":
                        return True
            ...
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent
    except Exception:
        pass
    return False

_OPTED_IN = _check_opt_in()
_LEGACY_DISABLED = (
    os.environ.get("CPP_TELEMETRY_DISABLED", "").lower() == "true"
    or os.environ.get("SIFT_TELEMETRY_DISABLED", "").lower() == "true"
)
SIFT_TELEMETRY_DISABLED = not _OPTED_IN or _LEGACY_DISABLED

# Unified Telemetry File (CPP Standard)
TELEMETRY_FILE = os.environ.get("CPP_TELEMETRY_FILE", ".pipe_telemetry.json")

_PULSE_LOCK = threading.Lock()
_PULSE_LAST_SENT: dict[str, float] = {}
_PULSE_PENDING: dict[str, tuple[str, int, int, float, str | None, str | None, str | None, str | None, str | None]] = {}
_PULSE_THREADS: list[threading.Thread] = []

LOGGER = logging.getLogger("semantic_sift.telemetry")


def flush_telemetry_pulses(timeout: float = 2.0) -> None:
    """Waits for all active telemetry pulse threads to complete."""
    with _PULSE_LOCK:
        threads = list(_PULSE_THREADS)

    for t in threads:
        if t.is_alive():
            t.join(timeout=timeout)

    with _PULSE_LOCK:
        _PULSE_THREADS.clear()


def _rate_limit_seconds() -> float:
    raw = os.environ.get("CPP_PULSE_RATE_LIMIT_S") or os.environ.get("SIFT_PULSE_RATE_LIMIT_S", "10")
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 10.0


# --- Privacy Shield ---
_SECRET_PATTERNS_GENERIC: list[tuple[str, str]] = [
    (r"github_pat_[a-zA-Z0-9_]{20,}", "[REDACTED]"),
    (r"sk-[a-zA-Z0-9]{20,}", "[REDACTED]"),
    (r"xox[bp]-[a-zA-Z0-9-]{10,}", "[REDACTED]"),
    (r"\b[a-fA-F0-9]{32,64}\b", "[REDACTED]"),
    (r"(password|secret|token|key)\s*[:=]\s*[^\s,]+", r"\1=[REDACTED]"),
]


def redact_secrets_for_telemetry(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    result = text
    for pattern, replacement in _SECRET_PATTERNS_GENERIC:
        result = re.sub(pattern, replacement, result)
    return result


# --- OTel ---
_TRACER = None


def get_tracer():
    global _TRACER
    if SIFT_TELEMETRY_DISABLED or not OTEL_AVAILABLE:
        return trace.get_tracer(__name__)

    if _TRACER is None:
        resource = Resource(attributes={"service.name": "semantic-sift-mcp"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(InMemorySpanExporter()))
        _TRACER = provider.get_tracer(__name__)

    return _TRACER


# --- Echo Detection (Unified .pipe_cache) ---
CACHE_DIR = os.path.join(os.getcwd(), ".pipe_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def check_echo(text: str) -> bool:
    if SIFT_TELEMETRY_DISABLED or not text or len(text) < 500:
        return False

    content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    echo_path = os.path.join(CACHE_DIR, f"echo_{content_hash}.tmp")
    now = time.time()

    if os.path.exists(echo_path):
        try:
            with open(echo_path, "r") as f:
                expiry = float(f.read().strip())
            if now < expiry:
                return True
        except (OSError, ValueError):
            pass

    try:
        with open(echo_path, "w") as f:
            f.write(str(now + 30))
    except OSError:
        pass

    return False


# --- Audit Header ---
def generate_audit_header(original_len: int, sifted_len: int, latency_ms: float, is_echo: bool = False) -> str:
    if SIFT_TELEMETRY_DISABLED:
        return ""

    style = os.environ.get("SIFT_AUDIT_HEADER", "full").lower()
    if style == "silent":
        return ""

    reduction = (1 - (sifted_len / original_len)) * 100 if original_len > 0 else 0
    guard_status = "Trace-Verified (No Echo)" if not is_echo else "🚨 ECHO DETECTED"

    if style == "minimal":
        return f"[Semantic-Sift: {reduction:.1f}% Savings | ⚡ {latency_ms:.1f}ms]\n\n"

    header = [
        "--- [Semantic-Sift Audit] ---",
        f"📊 Reduction: {reduction:.1f}% ({original_len / 1024:.1f}KB -> {sifted_len / 1024:.1f}KB)",
        f"🛡️ Guard: {guard_status}",
        f"⚡ Latency: {latency_ms:.1f}ms",
        "-----------------------------\n",
    ]
    return "\n".join(header)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _attempt_send(url: str, data: bytes) -> bool:
    """POSTs pre-encoded JSON to `url`. Returns True on HTTP 2xx. All exceptions silently swallowed."""
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        # Hard 5s timeout per attempt: covers DNS, connect, and read hangs.
        with urllib.request.urlopen(req, timeout=5) as r:  # nosec B310
            return r.status in [200, 201, 202, 204]
    except Exception:
        return False


def _send_telemetry_pulse_now(
    tool_name: str,
    original: int,
    final: int,
    latency: float,
    tier_override: str | None = None,
    client_id_override: str | None = None,
    agent_label: str | None = None,
    file_ext: str | None = None,
    reason: str | None = None,
) -> None:
    if SIFT_TELEMETRY_DISABLED or not SIFT_TELEMETRY_URL:
        return

    safe_tool = redact_secrets_for_telemetry(tool_name)
    safe_label = redact_secrets_for_telemetry(agent_label) if agent_label else None

    is_test = any(word in safe_tool.lower() for word in ["test", "handshake", "diag", "bench"])
    final_tier = tier_override or ("Internal-Testing" if is_test else "Real-World")
    final_client = client_id_override if client_id_override else SIFT_CLIENT_ID

    orig_tokens = estimate_tokens(" " * original)
    final_tokens = estimate_tokens(" " * final)

    payload = {
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
        "timestamp": datetime.now().astimezone().isoformat(),
        "reason": reason,
    }

    data = json.dumps(payload).encode()
    if not _attempt_send(SIFT_TELEMETRY_URL, data) and SIFT_TELEMETRY_FALLBACK_URL:
        _attempt_send(SIFT_TELEMETRY_FALLBACK_URL, data)


def send_telemetry_pulse(
    tool_name: str,
    original: int,
    final: int,
    latency: float,
    tier_override: str | None = None,
    client_id_override: str | None = None,
    agent_label: str | None = None,
    file_ext: str | None = None,
    reason: str | None = None,
) -> None:
    if SIFT_TELEMETRY_DISABLED or not SIFT_TELEMETRY_URL:
        return

    key = f"{client_id_override or SIFT_CLIENT_ID}:{tool_name}"
    now = time.time()
    interval = _rate_limit_seconds()

    with _PULSE_LOCK:
        last_sent = _PULSE_LAST_SENT.get(key, 0.0)
        if interval > 0 and (now - last_sent) < interval:
            _PULSE_PENDING[key] = (
                tool_name,
                original,
                final,
                latency,
                tier_override,
                client_id_override,
                agent_label,
                file_ext,
                reason,
            )
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

    payload = (tool_name, original, final, latency, tier_override, client_id_override, agent_label, file_ext, reason)
    t = threading.Thread(target=_worker, args=(payload,), daemon=True, name="semantic-sift-pulse")
    with _PULSE_LOCK:
        _PULSE_THREADS.append(t)
    t.start()


def log_telemetry(
    session_id: str,
    start_time: str,
    tool_name: str,
    original_chars: int,
    final_chars: int,
    latency_ms: float,
    cache_hit: bool = False,
    tier_override: str | None = None,
    client_id_override: str | None = None,
    agent_label: str | None = None,
    file_ext: str | None = None,
    skip_pulse: bool = False,
) -> None:
    if SIFT_TELEMETRY_DISABLED:
        return

    safe_tool = redact_secrets_for_telemetry(tool_name)
    safe_label = redact_secrets_for_telemetry(agent_label) if agent_label else None
    try:
        with _TELEMETRY_LOCK:
            data = {}
            if os.path.exists(TELEMETRY_FILE):
                with open(TELEMETRY_FILE, "r") as f:
                    data = json.load(f)

            # --- TTL Pruning ---
            try:
                ttl_days = int(os.environ.get("SIFT_TELEMETRY_TTL_DAYS", "90"))
            except ValueError:
                ttl_days = 90

            cutoff = time.time() - ttl_days * 86400
            expired = []
            for sid, sdata in data.items():
                if not isinstance(sdata, dict):
                    continue
                start_str = sdata.get("start_time", "1970-01-01")
                try:
                    # Handle both isoformat and ctime formats
                    try:
                        ts = datetime.fromisoformat(start_str).timestamp()
                    except ValueError:
                        # Fallback for ctime: 'Sun May 17 15:58:26 2026'
                        ts = time.mktime(time.strptime(start_str))

                    if ts < cutoff:
                        expired.append(sid)
                except (ValueError, TypeError, OSError):
                    # If date is unparseable, prune it to be safe
                    expired.append(sid)

            for sid in expired:
                del data[sid]
            # --- End TTL Pruning ---

            if session_id not in data:
                data[session_id] = {"start_time": start_time, "tools": {}}

            tool_stats = data[session_id]["tools"].get(
                safe_tool,
                {
                    "calls": 0,
                    "original_chars": 0,
                    "final_chars": 0,
                    "original_tokens": 0,
                    "final_tokens": 0,
                    "total_latency_ms": 0,
                    "cache_hits": 0,
                },
            )

            orig_tokens, final_tokens = estimate_tokens(" " * original_chars), estimate_tokens(" " * final_chars)
            tool_stats["calls"] += 1
            tool_stats["original_chars"] += original_chars
            tool_stats["final_chars"] += final_chars
            tool_stats["original_tokens"] += orig_tokens
            tool_stats["final_tokens"] += final_tokens
            tool_stats["total_latency_ms"] += latency_ms
            if cache_hit:
                tool_stats["cache_hits"] = tool_stats.get("cache_hits", 0) + 1

            data[session_id]["tools"][safe_tool] = tool_stats

            import uuid
            tmp_path = f"{TELEMETRY_FILE}.{uuid.uuid4().hex}.tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp_path, TELEMETRY_FILE)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise

        if not cache_hit and not skip_pulse:
            send_telemetry_pulse(
                safe_tool,
                original_chars,
                final_chars,
                latency_ms,
                tier_override=tier_override,
                client_id_override=client_id_override,
                agent_label=safe_label,
                file_ext=file_ext,
            )
    except Exception:
        LOGGER.exception("Failed to write telemetry record for tool '%s'", safe_tool)

# --- [Semantic-Sift Audit] ---
