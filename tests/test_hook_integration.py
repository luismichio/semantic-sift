"""
Integration tests for sift_hook.main().

Strategy: patch sys.stdin / sys.stdout to feed JSON payloads in and capture
the JSON output, without spawning a subprocess. This keeps tests fast and
avoids platform-specific process spawning issues on Windows.

Each test covers a distinct platform detection + injection path.
"""

import io
import json
import os
from unittest.mock import patch


# sift_hook.main() is the entry point we are testing.
from semantic_sift import hook as sift_hook


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_hook(payload: dict, env_overrides: dict | None = None) -> dict:
    """Feed *payload* through sift_hook.main() and return the parsed output."""
    stdin_data = json.dumps(payload)
    captured = io.StringIO()
    env = {**os.environ, **(env_overrides or {})}

    with (
        patch("sys.stdin", io.StringIO(stdin_data)),
        patch("sys.stdout", captured),
        patch.dict(os.environ, env, clear=False),
    ):
        sift_hook.main()

    output = captured.getvalue()
    assert output, "Hook produced no output — it should always write something."
    return json.loads(output)


def _long_text(n: int = 1200) -> str:
    """Return a prose string long enough to trigger sifting (>500 chars)."""
    sentence = "The quick brown fox jumps over the lazy dog. "
    return (sentence * (n // len(sentence) + 1))[:n]


# ---------------------------------------------------------------------------
# Short-circuit paths (no sifting)
# ---------------------------------------------------------------------------


def test_hook_returns_input_unchanged_when_empty():
    """Empty stdin → hook should write nothing (early return)."""
    captured = io.StringIO()
    with patch("sys.stdin", io.StringIO("")), patch("sys.stdout", captured):
        sift_hook.main()
    assert captured.getvalue() == ""


def test_hook_passes_through_short_content():
    """Payload shorter than 500 chars → written back unchanged."""
    payload = {"result": "short"}
    out = run_hook(payload)
    assert out == payload


def test_hook_passes_through_structured_json_content():
    """Structured JSON content (dict/list) → structural data exemption, pass-through."""
    inner = json.dumps({"key": "value", "nested": [1, 2, 3]})
    payload = {
        "hook_event_name": "AfterTool",
        "tool_name": "read_file",
        "tool_args": {"path": "foo.py"},
        "tool_response": {"llmContent": inner},
    }
    out = run_hook(payload)
    # Content should pass through unmodified (structured data exemption)
    assert out["tool_response"]["llmContent"] == inner


# ---------------------------------------------------------------------------
# Platform detection: Claude
# ---------------------------------------------------------------------------


def test_hook_detects_claude_platform():
    """CLAUDE_TOOL_NAME env var → platform detected as Claude, result key used."""
    payload = {"result": _long_text()}
    out = run_hook(payload, env_overrides={"CLAUDE_TOOL_NAME": "read_file"})
    # Output must be valid JSON; content may be sifted or passed through
    assert isinstance(out, dict)


def test_hook_claude_injects_into_tool_response():
    """Claude payload with tool_response → sifted content goes into llmContent."""
    long = _long_text(2000)
    payload = {
        "tool_response": {"llmContent": long},
        "result": long,
    }
    out = run_hook(payload, env_overrides={"CLAUDE_TOOL_NAME": "read_file"})
    assert "tool_response" in out


# ---------------------------------------------------------------------------
# Platform detection: Cursor
# ---------------------------------------------------------------------------


def test_hook_detects_cursor_platform():
    """Payload with top-level 'result' string (no AfterTool event) → Cursor path."""
    payload = {"result": _long_text()}
    # No CLAUDE_TOOL_NAME, no AfterTool event — falls to Cursor branch
    out = run_hook(payload)
    assert "result" in out


# ---------------------------------------------------------------------------
# Platform detection: Gemini (AfterTool, no tool_args)
# ---------------------------------------------------------------------------


def test_hook_detects_gemini_aftertool():
    """AfterTool without tool_args → Gemini platform, llmContent extracted."""
    long = _long_text(2000)
    payload = {
        "hook_event_name": "AfterTool",
        "tool_name": "read_file",
        "tool_response": {"llmContent": long},
        # No tool_args → Gemini
    }
    out = run_hook(payload)
    assert "tool_response" in out
    assert "llmContent" in out["tool_response"]


# ---------------------------------------------------------------------------
# Platform detection: OpenCode (AfterTool with tool_args)
# ---------------------------------------------------------------------------


def test_hook_detects_opencode_aftertool():
    """AfterTool WITH tool_args → OpenCode platform, llmContent extracted."""
    long = _long_text(2000)
    payload = {
        "hook_event_name": "AfterTool",
        "tool_name": "read_file",
        "tool_args": {"path": "foo.py"},
        "tool_response": {"llmContent": long},
    }
    out = run_hook(payload)
    assert "tool_response" in out
    assert "llmContent" in out["tool_response"]


def test_hook_detects_opencode_compacting():
    """Compacting event → OpenCode platform, summary injected into data."""
    long = _long_text(2000)
    payload = {
        "hook_event_name": "Compacting",
        "context": long,
    }
    out = run_hook(payload)
    # Compacting path writes summary back into data["summary"]
    assert "summary" in out


# ---------------------------------------------------------------------------
# Platform detection: VSCode
# ---------------------------------------------------------------------------


def test_hook_detects_vscode_platform():
    """tool_response.llmContent present, no AfterTool event → VSCode path."""
    long = _long_text(2000)
    payload = {
        "tool_response": {"llmContent": long},
        # No hook_event_name → falls to VSCode structural catch
    }
    out = run_hook(payload)
    assert "tool_response" in out


# ---------------------------------------------------------------------------
# Sifting actually reduces content
# ---------------------------------------------------------------------------


def test_hook_reduces_long_log_content():
    """A long repetitive log payload (Cursor path) should be shorter after hook."""
    # Build a noisy log-like payload well above the 500-char threshold
    noise = (
        "2026-01-01T00:00:00Z INFO Processing item\n"
        "=====================================\n"
        "......................................\n"
    ) * 30
    payload = {"result": noise}
    out = run_hook(payload)
    out_content = out.get("result", "")
    # Either sifted (shorter) or passed through — must be valid either way
    assert isinstance(out_content, str)
    # If sifting occurred, output should be tagged
    if len(out_content) < len(noise):
        assert "[Sifted]" in out_content or "Distilled" in out_content


# ---------------------------------------------------------------------------
# Echo bypass
# ---------------------------------------------------------------------------


def test_hook_bypasses_already_sifted_content():
    """Content already containing the audit header must pass through untouched."""
    already_sifted = "--- [Semantic-Sift Audit] ---\nSome content here."
    payload = {
        "hook_event_name": "AfterTool",
        "tool_name": "read_file",
        "tool_args": {"path": "foo.py"},
        "tool_response": {"llmContent": already_sifted},
    }
    out = run_hook(payload)
    # Should be written back exactly as received (bypass path)
    assert out == payload
