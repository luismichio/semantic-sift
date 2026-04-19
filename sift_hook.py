import sys
import json
import os
import re

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
    try:
        # 1. Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input:
            return
        
        data = json.loads(raw_input)
        
        # 2. Identify Platform and Extract Content
        # Platform: Gemini CLI
        if data.get("hook_event_name") == "AfterTool":
            tool_response = data.get("tool_response", {})
            raw_content = tool_response.get("llmContent", "")
            
            # Threshold: 1,000 characters
            if len(raw_content) > 1000:
                sifted_content = apply_heuristic_sieve(raw_content)
                if len(sifted_content) < len(raw_content):
                    # Inject Sifted Content
                    data["hookSpecificOutput"] = {
                        "additionalContext": f"\n\n[NOTE: This tool output was automatically distilled by Semantic-Sift to remove {len(raw_content) - len(sifted_content)} chars of noise.]"
                    }
                    data["tool_response"]["llmContent"] = sift_notification + sifted_content
        
        # Platform: Claude Code
        elif "toolUse" in data and "result" in data:
            raw_content = data["result"]
            if isinstance(raw_content, str) and len(raw_content) > 1000:
                sifted_content = apply_heuristic_sieve(raw_content)
                if len(sifted_content) < len(raw_content):
                    data["result"] = f"[Sifted] {sifted_content}"

        # Platform: OpenCode
        elif "output" in data and "args" in data.get("output", {}):
            # OpenCode structure varies by tool, we target common output text fields
            args = data["output"]["args"]
            for key in ["content", "text", "output", "stdout"]:
                if key in args and isinstance(args[key], str) and len(args[key]) > 1000:
                    sifted = apply_heuristic_sieve(args[key])
                    args[key] = sifted

        # 3. Output modified JSON
        sys.stdout.write(json.dumps(data))
        
    except Exception:
        # On error, return original input to avoid breaking the tool chain
        sys.stdout.write(raw_input)

sift_notification = "--- [Distilled by Semantic-Sift] ---\n"

if __name__ == "__main__":
    main()
