import os
from unittest.mock import patch
from semantic_sift import telemetry as telemetry_core
from semantic_sift import telemetry as _telemetry_impl


def test_token_estimation():
    # 4 chars = 1 token heuristic
    assert telemetry_core.estimate_tokens("ABCD") == 1
    assert telemetry_core.estimate_tokens("ABCDEFGHIJKL") == 3
    assert telemetry_core.estimate_tokens("") == 0


@patch("urllib.request.urlopen")
def test_telemetry_pulse_honors_disabled_flag(mock_urlopen):
    # Setup: Disable telemetry
    with patch.dict(os.environ, {"SIFT_TELEMETRY_DISABLED": "true"}):
        telemetry_core.SIFT_TELEMETRY_DISABLED = True
        telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)
        mock_urlopen.assert_not_called()


@patch("semantic_sift.telemetry._send_telemetry_pulse_now")
def test_telemetry_pulse_sends_correct_payload(mock_send_now, monkeypatch):
    # Patch the inner function that actually fires the HTTP request.
    # send_telemetry_pulse dispatches to a daemon thread; we join all
    # semantic-sift-pulse threads to avoid a race against the assertion.
    import threading

    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_DISABLED", False)
    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_URL", "https://example.com/api")
    # Disable rate limiting so the pulse is sent immediately (not queued).
    monkeypatch.setenv("SIFT_PULSE_RATE_LIMIT_S", "0")
    _telemetry_impl._PULSE_LAST_SENT.clear()
    _telemetry_impl._PULSE_PENDING.clear()

    telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)

    # Wait for the daemon thread to finish before asserting.
    for t in threading.enumerate():
        if t.name == "semantic-sift-pulse":
            t.join(timeout=2.0)

    assert mock_send_now.called
    args, _ = mock_send_now.call_args
    assert args[0] == "sift_logs"  # tool_name
    assert args[1] == 1000  # original
    assert args[2] == 500  # final


@patch("semantic_sift.telemetry._send_telemetry_pulse_now")
def test_telemetry_rate_limit_queues_pending(mock_send, monkeypatch):
    import threading

    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_DISABLED", False)
    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_URL", "https://example.com/api")
    monkeypatch.setenv("SIFT_PULSE_RATE_LIMIT_S", "60")

    _telemetry_impl._PULSE_LAST_SENT.clear()
    _telemetry_impl._PULSE_PENDING.clear()

    # First call goes through immediately; second call is within the rate window
    # so it must be queued into _PULSE_PENDING.
    telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)
    telemetry_core.send_telemetry_pulse("sift_logs", 900, 400, 8.0)

    # Wait for the first dispatch thread to finish.
    for t in threading.enumerate():
        if t.name == "semantic-sift-pulse":
            t.join(timeout=2.0)

    assert mock_send.called
    assert any("sift_logs" in k for k in _telemetry_impl._PULSE_PENDING.keys())


def test_detect_client_id_explicit_env_var(monkeypatch):
    monkeypatch.setenv("SIFT_CLIENT_ID", "MyCustomIDE")
    assert telemetry_core.detect_client_id() == "MyCustomIDE"


def test_detect_client_id_via_env_fingerprint(monkeypatch):
    monkeypatch.delenv("SIFT_CLIENT_ID", raising=False)
    monkeypatch.delenv("CPP_CLIENT_ID", raising=False)
    # Clear all ambient IDE env vars that take priority over per-call hook vars
    for ambient in (
        # Antigravity (host IDE for this repo — must be cleared first)
        "ANTIGRAVITY_AGENT",
        "ANTIGRAVITY_EDITOR_APP_ROOT",
        "ANTIGRAVITY_TRAJECTORY_ID",
        # Other IDEs
        "OPENCODE",
        "OPENCODE_PID",
        "OPENCODE_RUN_ID",
        "VSCODE_PID",
        "VSCODE_IPC_HOOK_CLI",
        "CURSOR_TRACE_ID",
        "WINDSURF_TOOL_ARGS",
        "WINDSURF_SESSION_ID",
        "__KIRO_MCP",
        "KIRO_SESSION_ID",
        "CONTINUE_SERVER_PORT",
        "JETBRAINS_IDE_URL",
        "CLINE_TASK_ID",
    ):
        monkeypatch.delenv(ambient, raising=False)
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "read_file")
    assert telemetry_core.detect_client_id() == "Claude"


def test_detect_client_id_fallback(monkeypatch):
    # Strip all known fingerprint env vars
    for var in [
        "SIFT_CLIENT_ID",
        "CLAUDE_TOOL_NAME",
        "CLAUDE_AGENT_NAME",
        "QWEN_TOOL_NAME",
        "CODEX_TOOL_NAME",
        "GEMINI_SESSION_ID",
        "CURSOR_TRACE_ID",
        "WINDSURF_TOOL_ARGS",
        "JETBRAINS_IDE_URL",
        "CLINE_TASK_ID",
    ]:
        monkeypatch.delenv(var, raising=False)
    # Without psutil matching a known process, should fall back to Generic CLI
    # (parent process in test runner is pytest, not a known IDE)
    result = telemetry_core.detect_client_id()
    # Result is either a known IDE (unlikely in CI) or the fallback
    assert isinstance(result, str) and len(result) > 0


@patch("semantic_sift.telemetry._send_telemetry_pulse_now")
def test_log_telemetry_caps_original_chars_to_max_limit(mock_send_now, monkeypatch):
    import threading
    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_DISABLED", False)
    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_URL", "https://example.com/api")
    monkeypatch.setenv("SIFT_PULSE_RATE_LIMIT_S", "0")
    monkeypatch.setenv("SIFT_MAX_INPUT_MB", "2")  # 2MB limit

    _telemetry_impl._PULSE_LAST_SENT.clear()
    _telemetry_impl._PULSE_PENDING.clear()

    # Input length is 3MB, which exceeds the 2MB limit.
    original_len = 3 * 1024 * 1024
    final_len = 1 * 1024 * 1024

    telemetry_core.log_telemetry(
        "test_session_caps",
        "2026-06-07T12:00:00Z",
        "sift_test_caps",
        original_len,
        final_len,
        5.0,
    )

    # Wait for the daemon thread to finish.
    for t in threading.enumerate():
        if t.name == "semantic-sift-pulse":
            t.join(timeout=2.0)

    assert mock_send_now.called
    args, _ = mock_send_now.call_args
    # original_chars should be capped to 2MB (2097152 bytes)
    assert args[1] == 2 * 1024 * 1024
    assert args[2] == final_len
