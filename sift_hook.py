import sys
import json
import os
import re
import time

# Import Core Logic & Telemetry
import telemetry_core
import sift_kernel

# Logging configuration
LOG_FILE = os.path.join(os.getcwd(), ".gemini", "sift_debug.log")

def log(message):
    try:
        timestamp = time.ctime()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def main():
    raw_input = ""
    try:
        # 1. Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input: return
        
        data = json.loads(raw_input)
        start_t = time.time()
        
        # Identity
        HOOK_SESSION = "Subconscious-Brain"
        START_TIME = time.ctime()

        # 2. Extract Context
        tool_name = "unknown"
        raw_content = ""
        platform = "unknown"

        # Platform Detection
        event_name = data.get("hook_event_name", "unknown")
        tool_name = data.get("tool_name", "unknown")
        raw_content = ""
        platform = "unknown"

        if os.environ.get("CLAUDE_TOOL_NAME"):
            platform = "Claude"
            tool_name = os.environ.get("CLAUDE_TOOL_NAME")
            # Claude Code passes the raw tool output as a string (not a JSON structure) to stdout/stdin 
            # if we are a basic command hook. We assume raw_input IS the content if JSON parsing fails,
            # but since we already parsed data as JSON above, we check if it has a specific key or assume data itself is the result.
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif os.environ.get("QWEN_TOOL_NAME") or ("tool_name" in data and "tool_input" in data and "context" in data):
            platform = "Qwen"
            tool_name = os.environ.get("QWEN_TOOL_NAME", data.get("tool_name", "unknown"))
            # Qwen CLI sends payload directly to stdin. If raw content isn't wrapped, we fallback to the raw input.
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif os.environ.get("CODEX_TOOL_NAME"):
            platform = "Codex"
            tool_name = os.environ.get("CODEX_TOOL_NAME")
            raw_content = data.get("result", "") if "result" in data else json.dumps(data) if isinstance(data, (dict,list)) else raw_input
        elif event_name in ["AfterTool", "PreCompress"]:
            platform = "Gemini"
            # OpenClaw explicitly sends an 'AfterTool' event from our generated plugin, but we can differentiate it by the context keys if needed.
            # The OpenClaw wrapper sends: { hook_event_name: "AfterTool", tool_name, tool_response: { llmContent: rawContent } }
            raw_content = data.get("tool_response", {}).get("llmContent", "")
            if "tool_response" in data and "llmContent" in data["tool_response"] and not os.environ.get("GEMINI_SESSION_ID"):
                # If Gemini session isn't there, but the structure matches our OpenClaw wrapper, it's likely OpenClaw
                platform = "Gemini/OpenClaw"
        elif "tool_response" in data and "llmContent" in data["tool_response"]:
            platform = "VSCode"
            raw_content = data["tool_response"]["llmContent"]
        elif "result" in data and isinstance(data["result"], str):
            platform = "Cursor"
            raw_content = data["result"]
        elif event_name == "Compacting":
            platform = "OpenCode"
            # OpenCode Compacting hook usually passes the context to summarize
            raw_content = data.get("context", "")

        # 3. Structural Lifecycle Routing (Compaction)
        if event_name in ["Compacting", "PreCompress"]:
            log(f"Handling structural {event_name} event for {platform}")
            if event_name == "Compacting" and raw_content:
                summary = sift_kernel.perform_compaction_summary(raw_content)
                # Inject summary into OpenCode output
                data["summary"] = summary
                
                # Log Compaction ROI
                telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, "event_compacting", len(raw_content), len(summary), (time.time() - start_t) * 1000)
                
                sys.stdout.write(json.dumps(data))
                return
            
            # For advisory-only PreCompress, just pulse telemetry
            telemetry_core.send_telemetry_pulse(
                tool_name=f"event_{event_name.lower()}",
                original=len(raw_content),
                final=0, # Advisory only
                latency=0,
                tier_override="Structural"
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
            span.set_attribute("is_echo", is_echo)

            if is_echo:
                log(f"ECHO DETECTED for {tool_name} - Bypassing BERT")
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
            has_md_ext = any(x in raw_content[:200].lower() for x in ['.md', '# ', '---'])
            
            if (is_prose or has_md_ext) and len(raw_content) > 3000:
                log(f"Auto-Semantic sifting prose from {tool_name}")
                sifted = sift_kernel.perform_semantic_sift(raw_content, rate=0.6)
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
            
            # Record accurate telemetry
            telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, sift_type, len(raw_content), len(sifted), latency, client_id_override=platform)

            # Inject back to platform
            msg = f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {len(raw_content) - len(sifted)} chars of noise.]"
            if platform in ["Gemini", "Gemini/OpenClaw"]:
                if "hookSpecificOutput" not in data: data["hookSpecificOutput"] = {}
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

sift_notification = "--- [Distilled by Semantic-Sift] ---\n"

if __name__ == "__main__":
    main()
