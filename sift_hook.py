# SPDX-License-Identifier: BUSL-1.1
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import sys
import json
import os
import re
import time
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Import Core Logic & Telemetry
import telemetry_core
import sift_kernel

# Module-level constants
sift_notification = "--- [Distilled by Semantic-Sift] ---\n"

# Logging configuration
LOG_FILE = os.environ.get("SIFT_LOG_FILE", os.path.join(os.getcwd(), ".gemini", "sift_debug.log"))
LOG_LEVEL = os.environ.get("SIFT_LOG_LEVEL", "WARNING").upper()


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("semantic_sift_hook")
    if logger.handlers:
        return logger

    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=2, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.WARNING))
    logger.propagate = False
    return logger


LOGGER = _build_logger()

def log(message: str) -> None:
    try:
        # Privacy Shield: Redact secrets before logging to disk
        safe_message = telemetry_core.redact_secrets(message)
        LOGGER.debug(safe_message)
    except (OSError, ValueError):
        return


def _get_hook_timeout_seconds() -> float:
    raw = os.environ.get("SIFT_HOOK_TIMEOUT_MS", "3000")
    try:
        timeout_ms = max(100, int(raw))
    except ValueError:
        timeout_ms = 3000
    return timeout_ms / 1000.0


def _semantic_sift_with_timeout(content: str, rate: float, timeout_s: float) -> tuple[str | None, bool]:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(sift_kernel.perform_semantic_sift, content, rate)
    try:
        result = future.result(timeout=timeout_s)
        executor.shutdown(wait=False, cancel_futures=False)
        return result, False
    except TimeoutError:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        return None, True

def main() -> None:
    raw_input = ""
    try:
        # 1. Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input:
            return

        data = json.loads(raw_input)
        start_t = time.time()

        # Identity
        HOOK_SESSION = "Subconscious-Brain"
        START_TIME = time.ctime()

        # 2. Extract Context
        tool_name = "unknown"
        raw_content = ""
        platform = "unknown"
        agent_label = None

        # Platform Detection
        event_name = data.get("hook_event_name", "unknown")

        # Aggressive Tool Name Discovery
        def find_tool_name(d):
            # Check common keys in order of likelihood
            for key in ["tool_name", "tool", "name", "call", "command", "mcp_tool"]:
                if key in d and isinstance(d[key], str):
                    return d[key]
            # Check nested call info if present
            if "call" in d and isinstance(d["call"], dict):
                return find_tool_name(d["call"])
            return None

        tool_name = find_tool_name(data) or "unknown"

        if os.environ.get("CLAUDE_TOOL_NAME"):
            platform = "Claude"
            tool_name = os.environ.get("CLAUDE_TOOL_NAME", tool_name)
            # Subagent detection for Claude
            agent_label = os.environ.get("CLAUDE_AGENT_NAME") or os.environ.get("CLAUDE_SUBAGENT_ID")
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif os.environ.get("QWEN_TOOL_NAME") or ("tool_name" in data and "tool_input" in data and "context" in data):
            platform = "Qwen"
            tool_name = os.environ.get("QWEN_TOOL_NAME", tool_name)
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif os.environ.get("CODEX_TOOL_NAME"):
            platform = "Codex"
            tool_name = os.environ.get("CODEX_TOOL_NAME", tool_name)
            # Subagent detection for Codex
            agent_label = data.get("context", {}).get("agent_name")
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif event_name in ["AfterTool", "PreCompress"]:
            # OpenCode native plugin sends tool_args alongside tool_name; Gemini never does.
            if "tool_args" in data:
                platform = "OpenCode"
                tool_name = data.get("tool_name", tool_name)
                raw_content = data.get("tool_response", {}).get("llmContent", "")
            else:
                platform = "Gemini"
                # Subagent detection for Gemini/OpenClaw
                agent_label = data.get("hookSpecificOutput", {}).get("threadLabel") or data.get("sessionId")
                raw_content = data.get("tool_response", {}).get("llmContent", "")
                if "tool_response" in data and "llmContent" in data["tool_response"] and not os.environ.get("GEMINI_SESSION_ID"):
                    platform = "Gemini/OpenClaw"
        elif "tool_response" in data and "llmContent" in data["tool_response"]:
            platform = "VSCode"
            raw_content = data["tool_response"]["llmContent"]
        elif "result" in data and isinstance(data["result"], str):
            platform = "Cursor"
            # Subagent detection for Cursor (sniff from result prefix or metadata)
            if data["result"].startswith("[Explore]"):
                agent_label = "Explore"
            elif data["result"].startswith("[Bash]"):
                agent_label = "Bash"
            raw_content = data["result"]
        elif event_name == "Compacting":
            platform = "OpenCode"
            tool_name = "internal_compacting"
            raw_content = data.get("context", "")

        # 3. Structural Lifecycle Routing (Compaction)
        if event_name in ["Compacting", "PreCompress"]:
            log(f"Handling structural {event_name} event for {platform}")
            if event_name == "Compacting" and raw_content:
                summary = sift_kernel.perform_compaction_summary(raw_content)
                # Inject summary into OpenCode output
                data["summary"] = summary

                # Log Compaction ROI
                telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, "event_compacting", len(raw_content), len(summary), (time.time() - start_t) * 1000, client_id_override=platform, agent_label=agent_label)

                sys.stdout.write(json.dumps(data))
                return

            # For advisory-only PreCompress, just pulse telemetry
            telemetry_core.send_telemetry_pulse(
                tool_name=f"event_{event_name.lower()}",
                original=len(raw_content),
                final=0, # Advisory only
                latency=0,
                tier_override="Structural",
                client_id_override=platform,
                agent_label=agent_label
            )
            sys.stdout.write(raw_input)
            return

        if not raw_content or len(raw_content) < 500:
            sys.stdout.write(raw_input)
            return

        # --- New: Echo Detector & OTel Integration ---
        is_echo = telemetry_core.check_echo(raw_content)
        tracer = telemetry_core.get_tracer()

        with tracer.start_as_current_span("subconscious_sift") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("platform", platform)
            span.set_attribute("agent.label", agent_label or "Main")
            span.set_attribute("is_echo", is_echo)

            if is_echo:
                log(f"ECHO DETECTED for {tool_name} (Agent: {agent_label or 'Main'}) - Bypassing BERT")
                # Even for echoes, we inject the header so the user knows why it bypassed
                header = telemetry_core.generate_audit_header(len(raw_content), len(raw_content), 0, is_echo=True)

                # Re-wrap in the correct JSON schema for the platform
                bypassed_content = header + raw_content
                if platform == "Gemini":
                    data["tool_response"]["llmContent"] = bypassed_content
                elif platform == "VSCode":
                    data["tool_response"]["llmContent"] = bypassed_content
                elif platform == "Cursor" or platform == "unknown":
                    # For Cursor or generic payloads, use the 'result' key
                    data["result"] = f"[Echo Bypassed] {bypassed_content}"

                sys.stdout.write(json.dumps(data))
                return

            if "--- [Semantic-Sift Audit] ---" in raw_content:
                log(f"Bypassing Native Execution for {tool_name}")
                sys.stdout.write(raw_input)
                return

            try:
                parsed = json.loads(raw_content)
                if isinstance(parsed, (dict, list)):
                    log(f"Structured Data Exemption for {tool_name}")
                    sys.stdout.write(raw_input)
                    return
            except json.JSONDecodeError:
                pass

            # 3. Subconscious Routing Intelligence
            sifted = None
            sift_type = "none"
            is_html = False
            timed_out_semantic = False

            # --- A. Auto-Ranking (Search Tools) ---
            if any(x in tool_name.lower() for x in ['search', 'grep', 'find']):
                # If we have query info (Gemini AfterTool includes args)
                args = data.get("tool_args", {})
                query = args.get("pattern") or args.get("query") or args.get("substring_pattern")
                if query and isinstance(raw_content, str):
                    # Try to split by common chunk delimiters if it looks like multi-file output
                    chunks = re.split(r'\n(?=File: |Path: |---)', raw_content)
                    if len(chunks) > 2:
                        log(f"Auto-Ranking {len(chunks)} search results for query: {query}")
                        scored = sift_kernel.perform_ranking(query, chunks, top_n=5)
                        if scored:
                            sifted = "\n---\n".join([doc for _, doc in scored])
                            sift_type = "sift_rank"

            # --- B. Auto-Semantic (Prose/Docs) ---
            if not sifted:
                is_prose = any(x in tool_name.lower() for x in ['read', 'fetch', 'extraction', 'chat'])
                is_html = "<html" in raw_content.lower()[:500] or "<!doctype html" in raw_content.lower()[:500]
                has_md_ext = any(x in raw_content[:200].lower() for x in ['.md', '# ', '---'])

                # Normalize HTML to Markdown first if needed
                working_content = raw_content
                if is_html:
                    md_converter = sift_kernel.get_markitdown()
                    if md_converter:
                        try:
                            log(f"Normalizing HTML to Markdown for {tool_name}")
                            import io
                            if hasattr(md_converter, "convert_stream"):
                                result = md_converter.convert_stream(io.StringIO(raw_content), file_extension=".html")
                                working_content = result.text_content
                            else:
                                import tempfile
                                temp_path = None
                                try:
                                    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
                                        tf.write(raw_content)
                                        temp_path = tf.name
                                    result = md_converter.convert(temp_path)
                                    working_content = result.text_content
                                finally:
                                    if temp_path and os.path.exists(temp_path):
                                        os.remove(temp_path)
                        except Exception as e:
                            log(f"HTML Normalization failed: {e}")

                if (is_prose or has_md_ext or is_html) and len(working_content) > 3000:
                    log(f"Auto-Semantic sifting prose from {tool_name}")
                    timeout_s = _get_hook_timeout_seconds()
                    semantic_output, timed_out_semantic = _semantic_sift_with_timeout(working_content, rate=0.6, timeout_s=timeout_s)
                    if timed_out_semantic:
                        log(f"Semantic timeout for {tool_name} after {timeout_s:.2f}s. Falling back to heuristic sieve.")
                        fallback = sift_kernel.apply_heuristic_sieve(raw_content)
                        if len(fallback) < len(raw_content):
                            sifted = "[Semantic-Sift: Heuristic Fallback - timeout]\n" + fallback
                            sift_type = "sift_logs"
                    elif semantic_output:
                        sifted = semantic_output
                        sift_type = "sift_chat"

            # --- C. Auto-Heuristic (Default / Logs) ---
            if not sifted:
                sifted = sift_kernel.apply_heuristic_sieve(raw_content)
                if len(sifted) < len(raw_content):
                    sift_type = "sift_logs"
                else:
                    sifted = None

            # 4. Handle Injection & Telemetry
            if sifted and len(sifted) < len(raw_content):
                latency = (time.time() - start_t) * 1000
                log(f"Subconscious {sift_type} successful: saved {len(raw_content) - len(sifted)} chars")

                # Combine sift type with intercepted tool name for high-fidelity telemetry
                telemetry_name = f"{sift_type}:{tool_name}"

                # Detect extension for telemetry
                hook_file_ext = "html" if is_html else "txt"
                if any(x in tool_name.lower() for x in ['search', 'grep', 'find']):
                    hook_file_ext = "grep"

                # Record accurate telemetry
                telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, telemetry_name, len(raw_content), len(sifted), latency, client_id_override=platform, agent_label=agent_label, file_ext=hook_file_ext)

                # Inject back to platform
                msg = f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {len(raw_content) - len(sifted)} chars of noise.]"
                if platform in ["Gemini", "Gemini/OpenClaw"]:
                    if "hookSpecificOutput" not in data:
                        data["hookSpecificOutput"] = {}
                    data["hookSpecificOutput"]["additionalContext"] = msg
                    data["tool_response"]["llmContent"] = sift_notification + sifted
                elif platform in ["VSCode", "Claude", "Qwen"]:
                    # Claude and Qwen act essentially identically to VSCode in terms of payload manipulation for basic JSON structures
                    if "tool_response" in data:
                        data["tool_response"]["llmContent"] = sift_notification + sifted
                    elif "result" in data:
                        data["result"] = f"[Sifted] {sifted}"
                    else:
                        # If it's a pure string payload wrapped in JSON
                        data = f"{sift_notification}{sifted}"
                elif platform == "Cursor":
                    data["result"] = f"[Sifted] {sifted}"

            # 5. Output modified JSON
            sys.stdout.write(json.dumps(data))

    except Exception as e:
        log(f"ERROR in Subconscious Brain: {str(e)}")
        sys.stdout.write(raw_input)

if __name__ == "__main__":
    main()
