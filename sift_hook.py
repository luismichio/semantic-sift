import sys
import json
import os
import re
import time

# Import Telemetry Core
import telemetry_core

# Logging configuration
LOG_FILE = os.path.join(os.getcwd(), ".gemini", "sift_debug.log")

def log(message):
    try:
        timestamp = time.ctime()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

# Masters of the Sieve: Heuristic logic imported/copied for zero-latency hooks
def apply_heuristic_sieve(text: str) -> str:
    lines = text.splitlines()
    sifted = []
    # Broad timestamp support: ISO-8601, Space-separated, Comma-milliseconds, and Legacy YYMMDD (Loghub)
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?)|(\d{6}\s\d{6}\s\d+)')
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')
    # Metadata noise: INFO dfs., DEBUG, [pip], etc.
    metadata_pattern = re.compile(r'\s*(INFO|DEBUG|WARN|ERROR)\s+dfs\..*?:\s*')
    module_pattern = re.compile(r'^\s*[\d\.]+\s+(MB|KB|bytes|B)\s+[\w\-\.\/]+.*$', re.IGNORECASE)
    
    for line in lines:
        # 1. Strip timestamps
        clean_line = timestamp_pattern.sub('', line).strip()
        # 2. Strip repetitive metadata headers
        clean_line = metadata_pattern.sub('', clean_line).strip()
        
        if not clean_line or progress_pattern.search(clean_line) or module_pattern.match(clean_line):
            continue
        sifted.append(clean_line)
    return "\n".join(sifted)

def main():
    log("Hook script triggered")
    raw_input = ""
    try:
        # 1. Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input:
            log("Warning: Received empty input on stdin")
            return
        
        data = json.loads(raw_input)
        start_t = time.time()
        
        # Identity placeholder (Hook doesn't have a persistent session ID, uses "Background-Hook")
        HOOK_SESSION = "Background-Hook"
        START_TIME = time.ctime()

        # 2. Identify Platform and Extract Content
        sifted = None
        raw_len = 0
        
        # Platform: Gemini CLI (AfterTool)
        if data.get("hook_event_name") == "AfterTool":
            tool_name = data.get("tool_name", "unknown")
            tool_response = data.get("tool_response", {})
            raw_content = tool_response.get("llmContent", "")
            raw_len = len(raw_content)
            
            if raw_len > 1000:
                sifted = apply_heuristic_sieve(raw_content)
                if len(sifted) < raw_len:
                    log(f"Sift successful: pruned {raw_len - len(sifted)} chars")
                    if "hookSpecificOutput" not in data: data["hookSpecificOutput"] = {}
                    data["hookSpecificOutput"]["additionalContext"] = f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {raw_len - len(sifted)} chars of noise.]"
                    data["tool_response"]["llmContent"] = sift_notification + sifted
                else:
                    sifted = None

        # Platform: VS Code Copilot (PostToolUse)
        elif "tool_response" in data and "llmContent" in data["tool_response"]:
             raw_content = data["tool_response"]["llmContent"]
             raw_len = len(raw_content)
             if raw_len > 1000:
                 sifted = apply_heuristic_sieve(raw_content)
                 if len(sifted) < raw_len:
                     data["tool_response"]["llmContent"] = sift_notification + sifted
                 else:
                     sifted = None

        # Platform: Cursor (postToolUse)
        elif "result" in data and isinstance(data["result"], str):
            raw_content = data["result"]
            raw_len = len(raw_content)
            if raw_len > 1000:
                sifted = apply_heuristic_sieve(raw_content)
                if len(sifted) < raw_len:
                    data["result"] = f"[Sifted] {sifted}"
                else:
                    sifted = None

        # 3. Handle Telemetry (Blocking call to ensure it finishes before hook exits)
        if sifted:
            latency = (time.time() - start_t) * 1000
            telemetry_core.log_telemetry(HOOK_SESSION, START_TIME, "hook_sift_logs", raw_len, len(sifted), latency)

        # 4. Output modified JSON
        sys.stdout.write(json.dumps(data))
        
    except Exception as e:
        log(f"ERROR: {str(e)}")
        sys.stdout.write(raw_input)

sift_notification = "--- [Distilled by Semantic-Sift] ---\n"

if __name__ == "__main__":
    main()
