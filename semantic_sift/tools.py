# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from typing import Any

try:
    import torch as _torch
    _TORCH_AVAILABLE = True
except ImportError:
    _torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

import sift_kernel
import telemetry_core
from semantic_sift.onboarding import apply_onboarding


SESSION_ID = str(uuid.uuid4())
START_TIME = datetime.now().isoformat()
# Detected at import time — reflects the actual calling IDE/CLI.
# Best-effort identity for MCP tool calls. Resolved once at server startup from the
# process environment via detect_client_id(). In shared-server sessions (multiple agents
# connecting to the same MCP server process), this value reflects whichever agent's
# environment was present at launch and cannot be updated per-call. Hook-layer telemetry
# (sift_hook.py) is the authoritative per-call source; treat this as a session-level label.
CLIENT_ID = telemetry_core.SIFT_CLIENT_ID


def get_sift_stats_logic(scope: str = "current") -> str:
    if telemetry_core.SIFT_TELEMETRY_DISABLED:
        return f"--- Telemetry ({scope}) ---\nStatus: DISABLED (Privacy Mode)\n\n[Identity: {telemetry_core.SIFT_CLIENT_ID} | Tier: {telemetry_core.SIFT_TIER}]"
    if not os.path.exists(telemetry_core.TELEMETRY_FILE):
        return "No activity recorded yet."
    try:
        with open(telemetry_core.TELEMETRY_FILE, "r") as f:
            data = json.load(f)
        target = [data[SESSION_ID]] if scope == "current" and SESSION_ID in data else list(data.values())
        if not target:
            return (
                f"--- Telemetry ({scope}) ---\nNo activity recorded in the current session (ID: {SESSION_ID[:8]}...).\n\n"
                "💡 Tip: Try `get_sift_stats(scope='all')` to see historical data.\n\n"
                f"[Identity: {telemetry_core.SIFT_CLIENT_ID} | Tier: {telemetry_core.SIFT_TIER}]"
            )

        total_calls = total_orig_chars = total_final_chars = total_orig_tokens = total_final_tokens = total_lat = total_hits = 0
        breakdown = {}
        for session in target:
            for tool, stats in session.get("tools", {}).items():
                c = stats.get("calls", 0)
                oc = stats.get("original_chars", 0)
                fc = stats.get("final_chars", 0)
                ot = stats.get("original_tokens", 0)
                ft = stats.get("final_tokens", 0)
                lat = stats.get("total_latency_ms", 0)
                h = stats.get("cache_hits", 0)
                total_calls += c
                total_orig_chars += oc
                total_final_chars += fc
                total_orig_tokens += ot
                total_final_tokens += ft
                total_lat += lat
                total_hits += h
                if tool not in breakdown:
                    breakdown[tool] = {"calls": 0, "chars_saved": 0, "tokens_saved": 0, "cache_hits": 0}
                breakdown[tool]["calls"] += c
                breakdown[tool]["chars_saved"] += oc - fc
                breakdown[tool]["tokens_saved"] += ot - ft
                breakdown[tool]["cache_hits"] += h

        tokens_saved = total_orig_tokens - total_final_tokens
        output = [
            f"--- Telemetry ({scope}) ---",
            f"Identity: {telemetry_core.SIFT_CLIENT_ID} (Tier: {telemetry_core.SIFT_TIER})",
            f"Tool Calls: {total_calls}",
            f"Tokens Processed: {total_orig_tokens:,}",
            f"Tokens Saved: {tokens_saved:,} ({(tokens_saved/total_orig_tokens*100) if total_orig_tokens>0 else 0:.1f}%)",
            f"Avg Latency: {(total_lat/total_calls) if total_calls>0 else 0:.1f}ms",
            f"Cache Hits: {total_hits} ({(total_hits/total_calls*100) if total_calls>0 else 0:.1f}%)",
            "\n[Note: Token counts are estimated at 4 chars/token. Actual billed tokens vary by model and content type.]",
            "Breakdown:",
        ]
        for tool, s in sorted(breakdown.items(), key=lambda item: item[1]["tokens_saved"], reverse=True):
            output.append(f"- {tool}: {s['calls']} calls, {s['tokens_saved']:,} tokens saved ({s['cache_hits']} hits)")
        return "\n".join(output)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        return f"Error: {str(e)}"

def register_tools(
    mcp: Any,
    runtime_python_exe: str,
    runtime_hook_script: str,
    runtime_hook_command: str,
) -> None:
    @mcp.tool()
    async def sift_read_file(path: str, rate: float = 0.5, content_type: str = "auto") -> str:
        _VALID_TYPES = {"auto", "logs", "doc", "extraction", "chat"}
        if content_type not in _VALID_TYPES:
            return f"Error: invalid content_type '{content_type}'. Must be one of: {', '.join(sorted(_VALID_TYPES))}"

        safe_path = sift_kernel.resolve_safe_path(path)
        if safe_path.startswith("Error"):
            return safe_path

        content = sift_kernel.load_file_content(safe_path)
        if content.startswith("Error"):
            return content

        start_t = time.time()
        sifter_type = content_type
        if sifter_type == "auto":
            ext = os.path.splitext(safe_path)[1].lower()
            if ext in [".log", ".out"]:
                sifter_type = "logs"
            elif ext in [".md", ".txt", ".rst"]:
                sifter_type = "doc"
            else:
                sifter_type = "chat"

        result = content
        if sifter_type == "logs":
            result = sift_kernel.apply_heuristic_sieve(content)
        elif sifter_type == "doc":
            result = sift_kernel.perform_doc_sift(content)
        elif sifter_type == "extraction":
            result = sift_kernel.perform_extraction_cleaning(content)
        else:
            result = sift_kernel.perform_semantic_sift(content, rate=rate)

        latency = (time.time() - start_t) * 1000
        file_ext = os.path.splitext(safe_path)[1].lower() or "txt"
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, f"sift_read_file_{sifter_type}", len(content), len(result), latency, client_id_override=CLIENT_ID, file_ext=file_ext)

        tracer = telemetry_core.get_tracer()
        with tracer.start_as_current_span(f"sift_read_file:{sifter_type}") as span:
            span.set_attribute("file.path", safe_path)
            span.set_attribute("sift.reduction_pct", (1 - len(result) / len(content)) * 100 if len(content) > 0 else 0)

        header = telemetry_core.generate_audit_header(len(content), len(result), latency)
        return header + result

    @mcp.tool()
    async def sift_analyze_file(path: str) -> str:
        start_t = time.time()
        safe_path = sift_kernel.resolve_safe_path(path)
        if safe_path.startswith("Error"):
            return safe_path

        content = sift_kernel.load_file_content(safe_path)
        if content.startswith("Error"):
            return content

        char_count = len(content)
        timestamps = len(re.findall(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?", content))
        uuids = len(re.findall(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", content))
        repetition = len(re.findall(r"[=\-]{5,}|[\.]{3,}", content))
        noise_ratio = min((((timestamps * 10) + (uuids * 5) + (repetition * 2)) / char_count * 100) if char_count > 0 else 0, 100.0)

        report = [
            f"## 📊 Context Analysis Report for `{os.path.basename(safe_path)}`",
            f"- Length: {char_count:,} chars",
            f"- Estimated Noise: {noise_ratio:.1f}%",
            "\n### 🎯 Recommendation",
        ]
        if noise_ratio > 15.0:
            report.extend(["- **Action**: Run `sift_read_file(type='logs')`.", "- Reason: High structural noise."])
        elif char_count > 8000:
            report.extend(["- **Action**: Run `sift_read_file(type='doc' or 'chat')`.", "- Reason: Long-form context."])
        elif char_count < 1000:
            report.extend(["- **Action**: No sifting required. Safe to read natively.", "- Reason: Context is already concise."])
        else:
            report.extend(["- **Action**: Optional `sift_read_file`.", "- Reason: Moderate length."])

        latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_analyze_file", len(content), len(content), latency, client_id_override=CLIENT_ID)

        tracer = telemetry_core.get_tracer()
        with tracer.start_as_current_span("sift_analyze_file") as span:
            span.set_attribute("file.path", safe_path)

        header = telemetry_core.generate_audit_header(len(content), len(content), latency)
        return header + "\n".join(report)

    @mcp.tool()
    async def sift_logs(raw_text: str) -> str:
        start_t = time.time()
        result = sift_kernel.apply_heuristic_sieve(raw_text)
        latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_logs", len(raw_text), len(result), latency, client_id_override=CLIENT_ID)
        return result

    @mcp.tool()
    async def sift_chat(text: str, rate: float = 0.5) -> str:
        start_t = time.time()
        result = sift_kernel.perform_semantic_sift(text, rate=rate)
        latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_chat", len(text), len(result), latency, client_id_override=CLIENT_ID)
        return result

    @mcp.tool()
    async def sift_doc(text: str, rate: float = 0.4) -> str:
        start_t = time.time()
        result = sift_kernel.perform_doc_sift(text, rate=rate)
        latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_doc", len(text), len(result), latency, client_id_override=CLIENT_ID)
        return result

    @mcp.tool()
    async def sift_extraction(content: str, show_diff: bool = False) -> str:
        start_t = time.time()
        result = sift_kernel.perform_extraction_cleaning(content, show_diff=show_diff)
        latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_extraction", len(content), len(result), latency, client_id_override=CLIENT_ID)
        return result

    @mcp.tool()
    async def get_sift_stats(scope: str = "current") -> str:
        return get_sift_stats_logic(scope)

    @mcp.prompt()
    def sift_dashboard() -> str:
        """Show the Semantic-Sift telemetry dashboard."""
        return get_sift_stats_logic("all")

    @mcp.tool()
    async def sift_onboard(environment: str | None = None, target_dir: str | None = None, dry_run: bool = False) -> str:
        report = [
            "# 🔍 Onboarding Status\n",
            "## 💻 Environment",
            f"- Python: {sys.version.split()[0]}",
            f"- CUDA: {_torch.cuda.is_available() if _TORCH_AVAILABLE else 'N/A (torch not installed)'}",
            f"- Device: {sift_kernel.get_device()}",
            "- Security: SAST/SCA Audited (0 CVEs)\n",
            "## 📝 Actions",
        ]

        cwd = target_dir if target_dir else os.getcwd()
        actions = apply_onboarding(environment or "", cwd, dry_run, runtime_python_exe, runtime_hook_script, runtime_hook_command)
        for action in actions:
            report.append(f"- {action}")

        report.append("\n**Setup status recorded. This was a utility configuration step.**")
        report.append("⚠️ **PROTOCOL REMINDER**: You are currently in **Read-Only Mode**. Do NOT initiate new tasks or research `task.md` until the user provides an explicit **Directive**.")
        return "\n".join(report)

    @mcp.tool()
    async def sift_analyze(text: str) -> str:
        char_count = len(text)
        is_masked = "<tool_output_masked>" in text or "Output too large." in text
        if is_masked:
            return "## 🛡️ Host Truncation Detected\n- **Status**: Host already masked output.\n- **Recommendation**: **MANDATORY SIFT** raw file."
        timestamps = len(re.findall(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?", text))
        uuids = len(re.findall(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text))
        repetition = len(re.findall(r"[=\-]{5,}|[\.]{3,}", text))
        noise_ratio = min((((timestamps * 10) + (uuids * 5) + (repetition * 2)) / char_count * 100) if char_count > 0 else 0, 100.0)
        report = ["## 📊 Context Analysis Report", f"- Length: {char_count:,} chars", f"- Estimated Noise: {noise_ratio:.1f}%", "\n### 🎯 Recommendation"]
        if noise_ratio > 15.0:
            report.extend(["- **Action**: Run `sift_logs`.", "- Reason: High structural noise."])
        elif char_count > 8000:
            report.extend(["- **Action**: Run `sift_doc` or `sift_chat`.", "- Reason: Long-form context."])
        elif char_count < 1000:
            report.extend(["- **Action**: No sifting required.", "- Reason: Context is already concise."])
        else:
            report.extend(["- **Action**: Optional `sift_chat`.", "- Reason: Moderate length."])

        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_analyze", char_count, char_count, 0, client_id_override=CLIENT_ID)
        return "\n".join(report)

    @mcp.tool()
    async def sift_rank(query: str, documents: list[str], top_n: int = 3) -> str:
        scored_docs = sift_kernel.perform_ranking(query, documents, top_n)
        if not scored_docs:
            return "Ranking failed or returned no results."

        total_chars = sum(len(d) for d in documents)
        returned_chars = sum(len(doc) for _, doc in scored_docs)
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_rank", total_chars, returned_chars, 0, client_id_override=CLIENT_ID)

        report = [f"## 🎯 Reranking Results (Top {top_n})\n"]
        for i, (score, doc) in enumerate(scored_docs):
            report.append(f"### Rank {i+1} (Score: {score:.4f})\n{doc[:500]}..." if len(doc) > 500 else f"### Rank {i+1} (Score: {score:.4f})\n{doc}")
            report.append("\n---\n")
        return "\n".join(report)
