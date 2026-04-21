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
        if data.get("hook_event_name") == "AfterTool":
            platform = "Gemini"
            tool_name = data.get("tool_name", "unknown")
            raw_content = data.get("tool_response", {}).get("llmContent", "")
        elif "tool_response" in data and "llmContent" in data["tool_response"]:
            platform = "VSCode"
            tool_name = data.get("tool_name", "unknown")
            raw_content = data["tool_response"]["llmContent"]
        elif "result" in data and isinstance(data["result"], str):
            platform = "Cursor"
            raw_content = data["result"]

        if not raw_content or len(raw_content) < 500:
            sys.stdout.write(raw_input)
            return

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
                        sift_type = "hook_sift_rank"

        # --- B. Auto-Semantic (Prose/Docs) ---
        if not sifted:
            is_prose = any(x in tool_name.lower() for x in ['read', 'fetch', 'extraction', 'chat'])
            has_md_ext = any(x in raw_content[:200].lower() for x in ['.md', '# ', '---'])
            
            if (is_prose or has_md_ext) and len(raw_content) > 3000:
                log(f"Auto-Semantic sifting prose from {tool_name}")
                sifted = sift_kernel.perform_semantic_sift(raw_content, rate=0.6)
                sift_type = "hook_sift_semantic"

        # --- C. Auto-Heuristic (Default / Logs) ---
        if not sifted:
            sifted = sift_kernel.apply_heuristic_sieve(raw_content)
            if len(sifted) < len(raw_content):
                sift_type = "hook_sift_logs"
            else:
                sifted = None

        # 4. Handle Injection & Telemetry
        if sifted and len(sifted) < len(raw_content):
            latency = (time.time() - start_t) * 1000
            log(f"Subconscious {sift_type} successful: saved {len(raw_content) - len(sifted)} chars")
            
            # Record accurate telemetry
            telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, sift_type, len(raw_content), len(sifted), latency)

            # Inject back to platform
            msg = f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {len(raw_content) - len(sifted)} chars of noise.]"
            if platform == "Gemini":
                if "hookSpecificOutput" not in data: data["hookSpecificOutput"] = {}
                data["hookSpecificOutput"]["additionalContext"] = msg
                data["tool_response"]["llmContent"] = sift_notification + sifted
            elif platform == "VSCode":
                data["tool_response"]["llmContent"] = sift_notification + sifted
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
