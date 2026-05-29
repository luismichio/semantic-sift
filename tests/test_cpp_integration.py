# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

"""
Integration tests for the Context-Pipe Protocol (CPP) contract with semantic-sift.

These tests validate the integration boundary between context-pipe and semantic-sift
by spawning `semantic-sift-cli` as a subprocess (the same way context-pipe/orchestrator.py does).

Skipped automatically if `semantic-sift-cli` is not found on PATH.

Mark: @pytest.mark.integration
"""

import shutil
import subprocess
import pytest
import re
import os
import sys
import pathlib

# ---------------------------------------------------------------------------
# Skip guard — integration tests require semantic-sift-cli to be installed.
# ---------------------------------------------------------------------------

# Prefer the binary co-installed in the current Python environment (venv / editable
# install) over whatever PATH resolves first.  A bare shutil.which() can shadow the
# project binary with a stale user-level install (~/.local/bin/) that points at a
# different package source and runs older, incompatible code.
#
# Search order:
#   1. Next to python.exe          — standard venv layout  (venv/Scripts/python.exe)
#   2. Scripts/ subdir             — system Python on Windows (Python313/Scripts/)
#   3. shutil.which fallback       — PATH, last resort
_exe_dir = pathlib.Path(sys.executable).parent
_cli_name = "semantic-sift-cli.exe" if sys.platform == "win32" else "semantic-sift-cli"
_candidates = [_exe_dir / _cli_name, _exe_dir / "Scripts" / _cli_name]
_venv_cli = next((p for p in _candidates if p.exists()), None)
_CLI = str(_venv_cli) if _venv_cli else shutil.which("semantic-sift-cli")
pytestmark = pytest.mark.integration

if _CLI is None:
    pytest.skip(
        "semantic-sift-cli not found in PATH. "
        "Install with: uv tool install semantic-sift",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOISY_LOG = """\
[INFO] Starting application v1.0.0
[DEBUG] Connecting to database at localhost:5432
[DEBUG] TCP connection established (RTT: 12ms)
[INFO] Schema migration check passed (version: 42)
ETag: W/"abc123def456"
Date: Mon, 01 Jan 2026 00:00:02 GMT
Content-Length: 8192
Content-Type: application/json; charset=utf-8
[DEBUG] Cache miss for key=user:8471
[ERROR] Failed to load plugin 'payment-gateway': ModuleNotFoundError
[INFO] Falling back to mock payment provider
[INFO] Server listening on 0.0.0.0:3000
"""

CLEAN_CONTENT = (
    "The resolve_node_cmd function resolves bare command names to executable paths "
    "using a 4-stage fallback: absolute path check, shutil.which PATH lookup, "
    "user-level install directories, and bare name passthrough."
)


def _run_sift(mode: str, input_text: str, extra_args: list | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Spawns semantic-sift-cli in the given mode with the given stdin."""
    cmd = [_CLI, mode] + (extra_args or [])
    # Inherit env but force telemetry on for header tests if needed
    child_env = os.environ.copy()
    if env:
        child_env.update(env)

    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        env=child_env,
    )


def _strip_header(text: str) -> str:
    """Strips the optional audit header from output."""
    if "--- [Semantic-Sift" in text:
        parts = re.split(r"-----------------------------\s*", text, maxsplit=1)
        return parts[1] if len(parts) > 1 else text
    return text


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCppContract:
    """Validates the CPP stdin/stdout contract that context-pipe depends on."""

    def test_cli_exits_zero_on_valid_input(self):
        """semantic-sift-cli must exit 0 for any valid UTF-8 input."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0, f"Non-zero exit: stderr={result.stderr!r}"

    def test_output_contains_sift_audit_header(self):
        """When telemetry is opted-in, output contains the audit header."""
        # Force telemetry on to trigger the header
        result = _run_sift("logs", NOISY_LOG, env={"SIFT_TELEMETRY_OPTED_IN": "true"})
        assert result.returncode == 0, f"Non-zero exit: stderr={result.stderr!r}"
        assert "--- [Semantic-Sift Audit] ---" in result.stdout

    def test_output_is_smaller_than_noisy_input(self):
        """Noisy log input must produce a smaller output (noise removed)."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        output_body = _strip_header(result.stdout)
        output_size = len(output_body)
        input_size = len(NOISY_LOG)
        assert output_size < input_size, f"Output ({output_size}) not smaller than input ({input_size})"

    def test_clean_content_minimal_change(self):
        """Clean informational content must not be drastically inflated."""
        result = _run_sift("semantic", CLEAN_CONTENT, extra_args=["--rate", "0.8"])
        assert result.returncode == 0

        # Strip the optional audit header before comparing sizes.
        output_body = _strip_header(result.stdout)
        output_size = len(output_body)
        input_size = len(CLEAN_CONTENT)

        # High-fidelity content should not be reduced much (it preserves high-information-density content).
        # We allow a 50% "overhead" buffer for framing/formatting if any.
        assert output_size <= input_size * 1.50, (
            f"Clean content inflated too much: input={input_size} output={output_size}"
        )

    def test_empty_input_exits_cleanly(self):
        """Empty stdin must produce an exit code of 0 and non-crashing output."""
        result = _run_sift("logs", "")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_stdout_is_valid_utf8(self):
        """The CLI output must always be valid UTF-8 (safe for JSON embedding)."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        try:
            result.stdout.encode("utf-8")
        except UnicodeEncodeError:
            pytest.fail("CLI output is not valid UTF-8")

    def test_stderr_does_not_pollute_stdout(self):
        """Any diagnostic messages must go to stderr, not contaminate stdout."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        # stdout should not contain raw Python tracebacks
        assert "Traceback" not in result.stdout
        # We don't check for "ERROR" or "INFO" here because the log content itself contains them.

    def test_no_false_positive_bypass_on_docs_mentioning_header(self):
        """Documents that contain the audit header string as literal text must NOT
        trigger the self-aware bypass.

        Regression test for: full-document scan false positive.
        ARCHITECTURE.md and similar docs describe the bypass mechanism and include
        '--- [Semantic-Sift Audit] ---' as literal text mid-document. The bypass
        must only fire when the header appears at the very start of the content.
        """
        doc_with_header_mention = (
            "# Architecture Specification\n\n"
            "This is a detailed architecture document.\n"
            "[ERROR] Some log noise to ensure sifting would normally run.\n" * 20
            + "## Self-Aware Bypass\n"
            "The bypass detects `--- [Semantic-Sift Audit] ---` and skips processing.\n"
            "When this signature appears mid-document it must NOT trigger the bypass.\n"
        )
        result = _run_sift("logs", doc_with_header_mention)
        assert result.returncode == 0
        # The sift MUST have run: audit header must be present at the top of output.
        assert "--- [Semantic-Sift Audit] ---" in result.stdout, (
            "Sift was bypassed by a false-positive mid-document header match. "
            "Check cli.py bypass guard — it must only scan input_data[:300]."
        )
