import json
import os
import subprocess
import sys


HOOK_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sift_hook.py"))


def _run_hook(payload: dict) -> str:
    process = subprocess.Popen([sys.executable, HOOK_SCRIPT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = process.communicate(input=json.dumps(payload))
    return out


def test_hook_structured_data_exemption():
    payload = {"result": json.dumps({"k": "v" * 300})}
    out = _run_hook(payload)
    assert "Distilled by Semantic-Sift" not in out
    assert "Semantic-Sift Audit" not in out


def test_hook_echo_bypass_header_present():
    content = "repeat-content " * 200
    payload = {"tool_name": "test_tool", "result": content}

    _run_hook(payload)  # first call seeds echo detector
    out = _run_hook(payload)

    assert "Echo Bypassed" in out or "ECHO DETECTED" in out
    assert "Semantic-Sift Audit" in out
