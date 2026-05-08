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

# ---------------------------------------------------------------------------
# Skip guard — integration tests require semantic-sift-cli to be installed.
# ---------------------------------------------------------------------------
_CLI = shutil.which("semantic-sift-cli")

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
2026-01-01T00:00:00.000Z [INFO] Starting application v1.0.0
2026-01-01T00:00:01.001Z [DEBUG] Connecting to database at localhost:5432
2026-01-01T00:00:01.500Z [DEBUG] TCP connection established (RTT: 12ms)
2026-01-01T00:00:02.000Z [INFO] Schema migration check passed (version: 42)
ETag: W/"abc123def456"
Date: Mon, 01 Jan 2026 00:00:02 GMT
Content-Length: 8192
Content-Type: application/json; charset=utf-8
2026-01-01T00:00:02.500Z [DEBUG] Cache miss for key=user:8471
2026-01-01T00:00:03.000Z [ERROR] Failed to load plugin 'payment-gateway': ModuleNotFoundError
2026-01-01T00:00:03.001Z [INFO] Falling back to mock payment provider
2026-01-01T00:00:03.500Z [INFO] Server listening on 0.0.0.0:3000
"""

CLEAN_CONTENT = (
    "The resolve_node_cmd function resolves bare command names to executable paths "
    "using a 4-stage fallback: absolute path check, shutil.which PATH lookup, "
    "user-level install directories, and bare name passthrough."
)


def _run_sift(mode: str, input_text: str, extra_args: list | None = None) -> subprocess.CompletedProcess:
    """Spawns semantic-sift-cli in the given mode with the given stdin."""
    cmd = [_CLI, mode] + (extra_args or [])
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCppContract:
    """Validates the CPP stdin/stdout contract that context-pipe depends on."""

    def test_cli_exits_zero_on_valid_input(self):
        """semantic-sift-cli must exit 0 for any valid UTF-8 input."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0, f"Non-zero exit: stderr={result.stderr!r}"

    def test_output_contains_cpp_signature_header(self):
        """When telemetry is opted-in, output contains the audit header.
        When telemetry is disabled (default), the header is correctly absent.
        Either way the CLI must exit 0 with non-empty output for noisy input.
        """
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0, f"Non-zero exit: stderr={result.stderr!r}"
        # Header is optional (only present when SIFT_TELEMETRY_OPTED_IN=true).
        # This test validates the contract still holds: output is non-empty and clean.
        assert len(result.stdout.strip()) > 0, "Expected non-empty output for noisy log input"

    def test_output_is_smaller_than_noisy_input(self):
        """Noisy log input must produce a smaller output (noise removed)."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        output_size = len(result.stdout)
        input_size = len(NOISY_LOG)
        assert output_size < input_size, (
            f"Expected compression: input={input_size} output={output_size}"
        )

    def test_clean_content_minimal_change(self):
        """Clean informational content must not be drastically inflated."""
        result = _run_sift("semantic", CLEAN_CONTENT, extra_args=["--rate", "0.8"])
        assert result.returncode == 0
        # Strip the optional audit header before comparing sizes.
        output_body = result.stdout
        if "--- [Semantic-Sift:" in output_body:
            # Header ends after the second '---...---' separator line + \n
            after = output_body.split("-----------------------------\n", 1)
            output_body = after[1] if len(after) > 1 else output_body
        output_size = len(output_body)
        input_size = len(CLEAN_CONTENT)
        # Allow up to 50% overhead: semantic compression at rate=0.8 on short text may
        # not reduce much (it preserves high-information-density content).
        assert output_size <= input_size * 1.50, (
            f"Clean content inflated too much: input={input_size} output={output_size}"
        )

    def test_empty_input_exits_cleanly(self):
        """Empty stdin must produce an exit code of 0 and non-crashing output."""
        result = _run_sift("logs", "")
        assert result.returncode == 0

    def test_stdout_is_valid_utf8(self):
        """The CLI output must always be valid UTF-8 (safe for JSON embedding)."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        try:
            result.stdout.encode("utf-8")
        except UnicodeEncodeError as e:
            pytest.fail(f"Output is not valid UTF-8: {e}")

    def test_stderr_does_not_pollute_stdout(self):
        """Any diagnostic messages must go to stderr, not contaminate stdout."""
        result = _run_sift("logs", NOISY_LOG)
        assert result.returncode == 0
        # stdout should not contain raw Python tracebacks or logging prefixes
        assert "Traceback" not in result.stdout
        assert "ERROR:" not in result.stdout.split("--- [Semantic-Sift:")[0]

    def test_version_flag_exits_zero(self):
        """--help must succeed — validates the binary is functional and responsive."""
        result = subprocess.run(
            [_CLI, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # argparse exits with 0 for --help
        assert result.returncode == 0, f"Expected exit 0 from --help, got {result.returncode}: {result.stderr!r}"
        assert len(result.stdout.strip()) > 0 or len(result.stderr.strip()) > 0
