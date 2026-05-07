import asyncio
import json
import os

import semantic_sift.tools as tools
import sift_kernel
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
        self.prompts = {}

    def tool(self):
        def _decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return _decorator

    def prompt(self):
        def _decorator(fn):
            self.prompts[fn.__name__] = fn
            return fn

        return _decorator


def _register(monkeypatch):
    mcp = _DummyMCP()
    monkeypatch.setattr(telemetry_core, "get_tracer", lambda: _DummyTracer())
    tools.register_tools(mcp, "python", "sift_hook.py", '"python" "sift_hook.py"')
    return mcp


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------


def test_sift_read_file_path_traversal_rejected(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SIFT_WORKSPACE_ROOT", str(tmp_path))

    # Create the file outside to ensure we test the security guard, not existence
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("Secret data")

    result = asyncio.run(mcp.tools["sift_read_file"](os.path.join("..", "outside.txt")))
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


# ---------------------------------------------------------------------------
# sift_logs
# ---------------------------------------------------------------------------


def test_sift_logs_reduces_noisy_input(monkeypatch):
    mcp = _register(monkeypatch)
    noisy = (
        "2026-01-01T00:00:00Z INFO Processing\n"
        "======================================\n"
        "......................................\n"
    ) * 20
    result = asyncio.run(mcp.tools["sift_logs"](noisy))
    assert isinstance(result, str)
    assert len(result) < len(noisy), "sift_logs should reduce noisy log content"


def test_sift_logs_returns_string_for_empty_input(monkeypatch):
    mcp = _register(monkeypatch)
    result = asyncio.run(mcp.tools["sift_logs"](""))
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# sift_chat
# ---------------------------------------------------------------------------


def test_sift_chat_calls_semantic_sift(monkeypatch):
    mcp = _register(monkeypatch)
    called_with = {}

    def fake_semantic_sift(text, rate=0.5):
        called_with["text"] = text
        called_with["rate"] = rate
        return "compressed"

    monkeypatch.setattr(sift_kernel, "perform_hybrid_sift", fake_semantic_sift)
    result = asyncio.run(mcp.tools["sift_chat"]("some long prose", rate=0.4))
    assert called_with["text"] == "some long prose"
    assert called_with["rate"] == 0.4
    assert result == "compressed"


# ---------------------------------------------------------------------------
# sift_doc
# ---------------------------------------------------------------------------


def test_sift_doc_calls_doc_sift(monkeypatch):
    mcp = _register(monkeypatch)
    called_with = {}

    def fake_doc_sift(text, rate=0.4):
        called_with["rate"] = rate
        return "doc_compressed"

    monkeypatch.setattr(sift_kernel, "perform_doc_sift", fake_doc_sift)
    result = asyncio.run(mcp.tools["sift_doc"]("# Title\nContent", rate=0.3))
    assert called_with["rate"] == 0.3
    assert result == "doc_compressed"


# ---------------------------------------------------------------------------
# sift_extraction
# ---------------------------------------------------------------------------


def test_sift_extraction_calls_extraction_cleaning(monkeypatch):
    mcp = _register(monkeypatch)

    def fake_extraction(content, show_diff=False):
        return "cleaned"

    monkeypatch.setattr(sift_kernel, "perform_extraction_cleaning", fake_extraction)
    result = asyncio.run(mcp.tools["sift_extraction"]("raw extraction content"))
    assert result == "cleaned"


# ---------------------------------------------------------------------------
# sift_rank
# ---------------------------------------------------------------------------


def test_sift_rank_returns_top_n_results(monkeypatch):
    mcp = _register(monkeypatch)
    docs = [f"Document about topic {i}" for i in range(10)]
    result = asyncio.run(mcp.tools["sift_rank"]("topic 3", docs, top_n=3))
    assert isinstance(result, str)
    # Should contain at most 3 documents worth of content
    assert result.count("Document about") <= 3


# ---------------------------------------------------------------------------
# get_sift_stats — scope="all" markdown table
# ---------------------------------------------------------------------------


def test_get_sift_stats_all_scope_returns_table(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(telemetry_core, "SIFT_TELEMETRY_DISABLED", False)

    session_data = {
        "sess-1": {
            "tools": {
                "sift_chat": {
                    "calls": 5,
                    "original_chars": 5000,
                    "final_chars": 2000,
                    "original_tokens": 1250,
                    "final_tokens": 500,
                    "total_latency_ms": 150,
                    "cache_hits": 1,
                }
            }
        }
    }
    with open(telemetry_core.TELEMETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f)

    result = asyncio.run(mcp.tools["get_sift_stats"]("all"))
    assert "sift_chat" in result
    assert "5" in result  # calls
    assert "60.0%" in result or "60%" in result  # compression ratio


# ---------------------------------------------------------------------------
# sift_onboard — environment=None falls back gracefully
# ---------------------------------------------------------------------------


def test_sift_onboard_none_environment_does_not_crash(tmp_path, monkeypatch):
    mcp = _register(monkeypatch)
    monkeypatch.chdir(tmp_path)

    # Should not raise TypeError even with environment=None
    result = asyncio.run(mcp.tools["sift_onboard"](None, str(tmp_path), True))
    assert isinstance(result, str)
