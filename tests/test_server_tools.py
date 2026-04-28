import asyncio
import os

import semantic_sift.tools as tools
import telemetry_core


class _DummySpan:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, *_args, **_kwargs):
        return None


class _DummyTracer:
    def start_as_current_span(self, _name):
        return _DummySpan()


class _DummyMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def _decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return _decorator


def _register(monkeypatch):
    mcp = _DummyMCP()
    monkeypatch.setattr(telemetry_core, "get_tracer", lambda: _DummyTracer())
    tools.register_tools(mcp, "python", "sift_hook.py", '"python" "sift_hook.py"')
    return mcp


def test_sift_read_file_path_traversal_rejected(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)

    result = asyncio.run(mcp.tools["sift_read_file"]("..\\outside.txt"))
    assert "Access denied" in result


def test_get_sift_stats_includes_estimate_note(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(telemetry_core, "SIFT_TELEMETRY_DISABLED", False)

    with open(telemetry_core.TELEMETRY_FILE, "w", encoding="utf-8") as f:
        f.write(
            '{"session": {"tools": {"sift_logs": {"calls": 1, "original_chars": 1000, "final_chars": 500, "original_tokens": 250, "final_tokens": 125, "total_latency_ms": 10, "cache_hits": 0}}}}'
        )

    result = asyncio.run(mcp.tools["get_sift_stats"]("all"))
    assert "Token counts are estimated at 4 chars/token" in result


def test_sift_onboard_dry_run_reports_no_writes(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)

    result = asyncio.run(mcp.tools["sift_onboard"]("Cursor", str(tmp_path), True))
    assert "Dry-run mode" in result
