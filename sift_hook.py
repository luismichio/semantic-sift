import sys
import json
import os
import re
import time

# Ensure the script's directory is in the path so we can import server.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import telemetry from server
try:
    from server import log_telemetry
except ImportError:
    # Fallback if server.py is not in path
    def log_telemetry(*args, **kwargs):
        pass

# Masters of the Sieve: Heuristic logic imported/copied for zero-latency hooks
def apply_heuristic_sieve(text: str) -> str:
    lines = text.splitlines()
    sifted = []
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?\s*')
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')
    module_pattern = re.compile(r'^\s*[\d\.]+\s+[\w\-\.\/]+\s+\d+\s+bytes.*$')
    for line in lines:
        clean_line = timestamp_pattern.sub('', line).strip()
        if not clean_line or progress_pattern.search(clean_line) or module_pattern.match(clean_line):
            continue
        sifted.append(clean_line)
    return "\n".join(sifted)

def main():
    # GOLDEN RULE: Use stderr for heartbeat/logging
    sys.stderr.write(f"Hook triggered at {time.ctime()}\n")
    
    raw_input = ""
    try:
        # 1. Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input:
            return
        
        data = json.loads(raw_input)
        start_t = time.time()
        
        # 2. Identify Platform and Extract Content
        # Platform: Gemini CLI
        if data.get("hook_event_name") == "AfterTool":
            tool_response = data.get("tool_response", {})
            raw_content = tool_response.get("llmContent", "")
            
            # Threshold: 1,000 characters
            if len(raw_content) > 1000:
                sifted_content = apply_heuristic_sieve(raw_content)
                if len(sifted_content) < len(raw_content):
                    # Telemetry
                    latency = (time.time() - start_t) * 1000
                    log_telemetry("hook_sift_logs", len(raw_content), len(sifted_content), latency)
                    
                    # Inject Sifted Content into JSON structure
                    if "hookSpecificOutput" not in data:
                        data["hookSpecificOutput"] = {}
                    data["hookSpecificOutput"]["additionalContext"] = f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {len(raw_content) - len(sifted_content)} chars of noise.]"
                    
                    # Move signature inside the JSON content (Subconscious)
                    data["tool_response"]["llmContent"] = sift_notification + sifted_content
        
        # Platform: Claude Code
        elif "toolUse" in data and "result" in data:
            raw_content = data["result"]
            if isinstance(raw_content, str) and len(raw_content) > 1000:
                sifted_content = apply_heuristic_sieve(raw_content)
                if len(sifted_content) < len(raw_content):
                    # Telemetry
                    latency = (time.time() - start_t) * 1000
                    log_telemetry("hook_sift_logs", len(raw_content), len(sifted_content), latency)
                    data["result"] = f"[Sifted] {sifted_content}"

        # Platform: OpenCode
        elif "output" in data and "args" in data.get("output", {}):
            args = data["output"]["args"]
            for key in ["content", "text", "output", "stdout"]:
                if key in args and isinstance(args[key], str) and len(args[key]) > 1000:
                    raw_content = args[key]
                    sifted = apply_heuristic_sieve(raw_content)
                    if len(sifted) < len(raw_content):
                        # Telemetry
                        latency = (time.time() - start_t) * 1000
                        log_telemetry("hook_sift_logs", len(raw_content), len(sifted), latency)
                        args[key] = sifted

        # 3. Output modified JSON - STRICTLY JSON TO STDOUT
        sys.stdout.write(json.dumps(data))
        
    except Exception as e:
        sys.stderr.write(f"Error in hook: {str(e)}\n")
        # On error, return original input to avoid breaking the tool chain
        sys.stdout.write(raw_input)

sift_notification = "--- [Distilled by Semantic-Sift] ---\n"

if __name__ == "__main__":
    main()
