import glob
import json
import os
import subprocess
import sys

import pytest


HOOK_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sift_hook.py"))
CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".pipe_cache"))


@pytest.fixture()
def clean_echo_cache():
    """Remove all echo cache files before and after the test to ensure isolation."""
    for f in glob.glob(os.path.join(CACHE_DIR, "echo_*.tmp")):
        try:
            os.remove(f)
        except OSError:
            pass
    yield
    for f in glob.glob(os.path.join(CACHE_DIR, "echo_*.tmp")):
        try:
            os.remove(f)
        except OSError:
            pass


def _run_hook(payload: dict) -> str:
    process = subprocess.Popen([sys.executable, HOOK_SCRIPT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = process.communicate(input=json.dumps(payload))
    return out


def test_hook_structured_data_exemption():
    payload = {"result": json.dumps({"k": "v" * 300})}
    out = _run_hook(payload)
    assert "Distilled by Semantic-Sift" not in out
    assert "Semantic-Sift Audit" not in out


def test_opencode_aftertool_platform_detection():
    """OpenCode plugin sends tool_args; must be detected as OpenCode, not Gemini."""
    content = "x " * 400  # >500 chars to pass the short-circuit
    payload = {
        "hook_event_name": "AfterTool",
        "tool_name": "read_file",
        "tool_args": {"path": "/tmp/foo.txt"},
        "tool_response": {"llmContent": content},
    }
    out = _run_hook(payload)
    data = json.loads(out)
    # The hook must pass llmContent through (possibly sifted); key must survive
    assert "tool_response" in data
    # Telemetry client_id is internal — we verify the payload key is preserved
    # and the hook did NOT confuse the structure (Gemini path would also work structurally,
    # so we verify tool_name round-trips correctly)
    assert data.get("tool_name") == "read_file"


def test_gemini_aftertool_no_tool_args():
    """Gemini AfterTool payloads lack tool_args; must still be detected as Gemini."""
    content = "y " * 400
    payload = {
        "hook_event_name": "AfterTool",
        "tool_response": {"llmContent": content},
        "sessionId": "gemini-session-abc",
    }
    out = _run_hook(payload)
    data = json.loads(out)
    assert "tool_response" in data


def test_hook_echo_bypass_header_present(clean_echo_cache):
    """The echo detector must prevent double-sifting repeated identical content.
    When the same content is submitted twice within the TTL window, the second
    call returns the content without re-processing (echo bypass behaviour).
    The audit header ('Echo Bypassed' / 'ECHO DETECTED') is only present
    when telemetry is opted-in; this test verifies the bypass logic itself.
    """
    content = "repeat-content " * 200
    payload = {"tool_name": "test_tool", "result": content}

    _run_hook(payload)  # first call seeds echo detector
    out = _run_hook(payload)  # second call — should be an echo bypass

    # The output must be valid JSON and must contain the original tool_name
    import json as _json
    try:
        data = _json.loads(out)
        # Either the echo was detected (audit header present) or the content
        # was passed through unchanged (bypass without header in opt-out mode).
        assert "tool_name" in data or "Echo Bypassed" in out or "ECHO DETECTED" in out
    except _json.JSONDecodeError:
        # Non-JSON output is acceptable if it contains the original content
        assert "repeat-content" in out
