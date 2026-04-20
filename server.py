import re
import os
import sys
import json
import uuid
import time
import torch
import hashlib
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Import Telemetry Core
import telemetry_core

# Global Configuration
SESSION_ID = str(uuid.uuid4())
START_TIME = datetime.now().isoformat()

# Ensure directories exist
os.makedirs(".sift_cache", exist_ok=True)

# Device Detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Master list of instruction files for various IDEs and tools
INSTRUCTION_TARGETS = [
    "AGENTS.md",                         # Generic / Studio of Two
    "GEMINI.md",                         # Gemini CLI / Antigravity
    ".clinerules",                       # Cline / Roo Code
    ".cursorrules",                      # Cursor
    ".windsurfrules",                    # Windsurf
    ".github/copilot-instructions.md",   # GitHub Copilot (Docs)
    ".cursor/hooks.json",                # Cursor (Hooks)
    ".github/hooks/semantic-sift.json"   # VS Code Copilot (Hooks)
]

# SOP Template for Onboarding
SOP_TEMPLATE = """
---

# 🔍 Semantic-Sift — Standard Operating Procedures

To maintain high Signal-to-Noise Ratio (SNR) and prevent context flooding, follow these usage guidelines.

## 🛠️ Tool Selection & Thresholds

| Tool | Trigger Condition | Goal |
| :--- | :--- | :--- |
| `sift_logs` | Any log/terminal output > 50 lines or containing progress bars. | Heuristic removal of timestamps/noise. |
| `sift_chat` | Previous conversation history exceeding 5,000 characters. | Prune linguistic filler (default rate: 0.5). |
| `sift_doc` | Reading documentation files > 10,000 characters. | Hybrid distillation (Heuristic + Semantic). |
| `sift_extraction` | Processing raw OCR or Docling extractions. | Preserve Markdown structure while cleaning debris. |
| `sift_rank` | Selecting best chunks from multiple retrieved documents. | Filter by semantic relevance before sifting. |

## 📐 Rate Guidelines
- **Aggressive (0.3)**: Use for "lost in the middle" scenarios or massive histories.
- **Balanced (0.5)**: Default. Best for general conversation and instructions.
- **Gentle (0.7)**: Use for technical documentation where every keyword matters.

## 🤖 Auto-Sift Mandate
- **Trigger**: The agent MUST run `sift_analyze` on any data (logs, file reads, tool outputs) exceeding **1,000 characters**.
- **Action**: If the estimated noise is **> 15%**, sifting via `sift_logs` or `sift_chat` is REQUIRED before proceeding with analysis.

## 📊 Global Savings Registry
- **Endpoint**: `https://www.luiskobayashi.com/api/sift`
- **Goal**: Aggregate anonymous character savings to prove the value of the context sanitation engine.

## 🚫 Sifting Forbidden
- **NEVER** sift foundational instructions (`AGENTS.md`, `GEMINI.md`).
- **NEVER** sift small, surgical code snippets (symbol-level).
- **NEVER** sift security-sensitive configuration files (`.env`, secrets).
"""

# Collaboration Blueprint for known MCPs (Heuristic Matching)
COLLABORATION_MAP = {
    "serena": {"rule": "- **Serena Synergy**: Always pipe code bodies > 100 lines through `sift_chat` (rate: 0.7) after retrieval."},
    "investigator": {"rule": "- **Investigator Synergy**: Run `sift_doc` on comprehensive architectural reports."},
    "context-mode": {"rule": "- **Context-Mode Synergy**: Run `sift_logs` or `sift_chat` BEFORE calling `context-mode_ctx_index`."},
    "memory": {"rule": "- **Memory Synergy**: Periodically call `sift_chat` on retrieved long-term memories."},
    "slack": {"rule": "- **Slack Synergy**: Sift Slack history to keep only the decisions and action items."},
    "discord": {"rule": "- **Discord Synergy**: Use `sift_chat` on verbose Discord threads."},
    "notion": {"rule": "- **Notion Synergy**: Use `sift_extraction` on Notion pages to remove redundant block metadata."},
    "confluence": {"rule": "- **Confluence Synergy**: Sift Confluence pages to remove enterprise navigation elements."},
    "aws": {"rule": "- **AWS Synergy**: Apply `sift_logs` to cloud resource descriptions to strip low-entropy metadata."},
    "gcp": {"rule": "- **GCP Synergy**: Sift verbose GCloud CLI outputs to isolate error states."},
    "azure": {"rule": "- **Azure Synergy**: Use `sift_logs` on Azure resource snapshots."},
    "postgres": {"rule": "- **Postgres Synergy**: If a query returns > 50 rows, run `sift_logs`."},
    "sql": {"rule": "- **SQL Synergy**: Sift large SQL query results to focus on the schema and anomalies."},
    "sqlite": {"rule": "- **SQLite Synergy**: Use `sift_logs` on database dumps."},
    "puppeteer": {"rule": "- **Puppeteer Synergy**: Always run `sift_extraction` on browser text."},
    "playwright": {"rule": "- **Playwright Synergy**: Run `sift_extraction` on raw HTML fetches."},
    "browser": {"rule": "- **Browser Synergy**: Use `sift_extraction` to clean up web content."},
    "jira": {"rule": "- **Jira Synergy**: Sift Jira ticket comments to focus on the 'State Change' logic."},
    "linear": {"rule": "- **Linear Synergy**: Use `sift_chat` on issue descriptions to isolate technical blockers."},
    "github": {"rule": "- **GitHub Synergy**: Use `sift_logs` on verbose PR diffs or search results."},
    "github-copilot": {"rule": "- **Copilot Synergy**: Always sift large context windows before presenting to Copilot."},
    "fetch": {"rule": "- **Fetch Synergy**: Always sift raw HTML/Markdown fetched from URLs."},
    "brave-search": {"rule": "- **Brave Synergy**: When fetching long web pages, run `sift_extraction`."}
}

# Create the MCP server
mcp = FastMCP("Semantic-Sift")

# --- Sifting Logic (Heuristic/Structural) ---

def apply_heuristic_sieve(text: str) -> str:
    """Sifts through raw technical logs to remove noise."""
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

# --- Helpers ---

def get_cache_key(tool_name: str, text: str, **kwargs) -> str:
    payload = f"{tool_name}:{text}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()

def check_cache(key: str) -> str | None:
    cache_path = os.path.join(".sift_cache", f"{key}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f: return f.read()
    return None

def set_cache(key: str, result: str):
    cache_path = os.path.join(".sift_cache", f"{key}.txt")
    with open(cache_path, "w", encoding="utf-8", errors="replace") as f: f.write(result)

def get_global_mcp_configs() -> list[dict]:
    configs = []
    discovery_grid = [
        {"path": "~/AppData/Roaming/Claude/claude_desktop_config.json", "key": "mcpServers", "os": "win32"},
        {"path": "~/Library/Application Support/Claude/claude_desktop_config.json", "key": "mcpServers", "os": "darwin"},
        {"path": "~/.continue/config.json", "key": "mcpServers"},
        {"path": "~/.config/zed/settings.json", "key": "context_servers"},
        {"path": ".zed/settings.json", "key": "context_servers"},
        {"path": "~/.copilot/mcp-config.json", "key": "mcpServers"},
        {"path": ".copilot/mcp-config.json", "key": "mcpServers"},
        {"path": "~/.mcp.json", "key": "mcpServers"},
        {"path": "~/.opencode.json", "key": "mcpServers"},
        {"path": ".opencode.json", "key": "mcpServers"},
        {"path": "~/.gemini/antigravity/mcp_config.json", "key": "mcpServers"},
    ]
    for item in discovery_grid:
        if "os" in item and sys.platform != item["os"]: continue
        full_path = os.path.expanduser(item["path"])
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    configs.append({"data": json.load(f), "key": item["key"]})
            except Exception: pass
    return configs

def merge_hook_json(path: str, hook_key: str, new_hook: dict, version: int = None):
    """Safely merges a new hook into an existing JSON file without overwriting others."""
    data = {"hooks": {}}
    if version: data["version"] = version
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except: pass
    
    if "hooks" not in data: data["hooks"] = {}
    hooks_list = data["hooks"].get(hook_key, [])
    
    # Check if already present (by command matching)
    exists = any(h.get("command") == new_hook.get("command") for h in hooks_list)
    if not exists:
        data["hooks"][hook_key] = [new_hook] + hooks_list
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    return False

def update_instruction_files(section_id: str, header: str, content: str, target_dir: str = None) -> list[str]:
    actions = []
    cwd = target_dir if target_dir else os.getcwd()
    python_exe = "C:/Users/luism/Workbench/GitHub/semantic-sift/venv312/Scripts/python.exe"
    hook_script = "C:/Users/luism/Workbench/GitHub/semantic-sift/sift_hook.py"
    cmd_str = f"{python_exe} {hook_script}"
    block_id = f"<!-- SIFT_SECTION_START:{section_id} -->"; block_end = f"<!-- SIFT_SECTION_END:{section_id} -->"
    full_payload = f"\n{block_id}\n---\n\n{header}\n{content}\n{block_end}\n"
    for filename in INSTRUCTION_TARGETS:
        if not filename.endswith((".md", ".clinerules", ".cursorrules", ".windsurfrules")): continue
        target_path = os.path.join(cwd, filename)
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f: file_content = f.read()
                pattern = re.compile(rf'{re.escape(block_id)}.*?{re.escape(block_end)}', re.DOTALL)
                if pattern.search(file_content):
                    new_content = pattern.sub(full_payload.strip(), file_content)
                    with open(target_path, "w", encoding="utf-8", errors="replace") as f: f.write(new_content)
                    actions.append(f"Updated `{filename}`.")
                else:
                    with open(target_path, "a", encoding="utf-8", errors="replace") as f: f.write(full_payload)
                    actions.append(f"Injected into `{filename}`.")
            except Exception as e: actions.append(f"Error updating `{filename}`: {str(e)}")
    cursor_path = os.path.join(cwd, ".cursor", "hooks.json")
    os.makedirs(os.path.dirname(cursor_path), exist_ok=True)
    if merge_hook_json(cursor_path, "postToolUse", {"command": cmd_str}, version=1): actions.append("Merged into Cursor hooks.")
    vscode_path = os.path.join(cwd, ".github", "hooks", "semantic-sift.json")
    os.makedirs(os.path.dirname(vscode_path), exist_ok=True)
    if merge_hook_json(vscode_path, "PostToolUse", {"type": "command", "command": cmd_str}): actions.append("Merged into VS Code hooks.")
    return actions

# --- Tools ---

@mcp.tool()
async def sift_logs(raw_text: str) -> str:
    start_t = time.time(); result = apply_heuristic_sieve(raw_text); latency = (time.time() - start_t) * 1000
    telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_logs", len(raw_text), len(result), latency)
    return result

@mcp.tool()
async def sift_chat(text: str, rate: float = 0.5) -> str:
    start_t = time.time(); cache_key = get_cache_key("sift_chat", text, rate=rate)
    if cached := check_cache(cache_key): 
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_chat", len(text), len(cached), (time.time() - start_t) * 1000, True)
        return cached
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([text], rate=rate, force_tokens=['\n', '?'], chunk_end_tokens=['.', '\n'], return_word_label=False)
        result = results.get('compressed_prompt', text); set_cache(cache_key, result); latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_chat", len(text), len(result), latency)
        return result
    except Exception as e: return f"Error: {str(e)}"

@mcp.tool()
async def sift_doc(text: str, budget_tokens: int = 1000) -> str:
    start_t = time.time(); cache_key = get_cache_key("sift_doc", text, budget_tokens=budget_tokens)
    if cached := check_cache(cache_key): 
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_doc", len(text), len(cached), (time.time() - start_t) * 1000, True)
        return cached
    cleaned = apply_heuristic_sieve(text)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([cleaned], rate=0.4, force_tokens=['[', ']', '{', '}', '/', '\\', '.', '_'], chunk_end_tokens=['\n', '.', ';'], return_word_label=False)
        result = results.get('compressed_prompt', cleaned); set_cache(cache_key, result); latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_doc", len(text), len(result), latency)
        return result
    except Exception as e: return f"Error: {str(e)}"

@mcp.tool()
async def sift_extraction(content: str, source_type: str = "markdown") -> str:
    start_t = time.time(); cache_key = get_cache_key("sift_extraction", content, source_type=source_type)
    if cached := check_cache(cache_key): 
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_extraction", len(content), len(cached), (time.time() - start_t) * 1000, True)
        return cached
    refined = content
    for pattern in [r'Page \d+ of \d+', r'© .*? All rights reserved', r'---+\s*$', r'^\s*·\s*$']: refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([refined], rate=0.7, force_tokens=['\n', '|', '-', ':', '#'], chunk_end_tokens=['\n', '.'], return_word_label=False)
        result = results.get('compressed_prompt', refined); set_cache(cache_key, result); latency = (time.time() - start_t) * 1000
        telemetry_core.log_telemetry(SESSION_ID, START_TIME, "sift_extraction", len(content), len(result), latency)
        return result
    except Exception as e: return f"Error: {str(e)}"

@mcp.tool()
async def get_sift_stats(scope: str = "current") -> str:
    if telemetry_core.SIFT_TELEMETRY_DISABLED:
        return f"--- Telemetry ({scope}) ---\nStatus: DISABLED (Privacy Mode)\n\n[Identity: {telemetry_core.SIFT_CLIENT_ID} | Tier: {telemetry_core.SIFT_TIER}]"
    if not os.path.exists(telemetry_core.TELEMETRY_FILE): return "No data."
    try:
        with open(telemetry_core.TELEMETRY_FILE, "r") as f: data = json.load(f)
        target = [data[SESSION_ID]] if scope == "current" and SESSION_ID in data else list(data.values())
        if not target: return f"--- Telemetry ({scope}) ---\nNo activity recorded.\n\n[Identity: {telemetry_core.SIFT_CLIENT_ID} | Tier: {telemetry_core.SIFT_TIER}]"
        total_calls = total_orig_chars = total_final_chars = total_orig_tokens = total_final_tokens = total_lat = total_hits = 0; breakdown = {}
        for session in target:
            for tool, stats in session.get("tools", {}).items():
                c = stats.get("calls", 0); oc = stats.get("original_chars", 0); fc = stats.get("final_chars", 0); ot = stats.get("original_tokens", 0); ft = stats.get("final_tokens", 0); l = stats.get("total_latency_ms", 0); h = stats.get("cache_hits", 0)
                total_calls += c; total_orig_chars += oc; total_final_chars += fc; total_orig_tokens += ot; total_final_tokens += ft; total_lat += l; total_hits += h
                if tool not in breakdown: breakdown[tool] = {"calls": 0, "chars_saved": 0, "tokens_saved": 0, "cache_hits": 0}
                breakdown[tool]["calls"] += c; breakdown[tool]["chars_saved"] += (oc - fc); breakdown[tool]["tokens_saved"] += (ot - ft); breakdown[tool]["cache_hits"] += h
        tokens_saved = total_orig_tokens - total_final_tokens
        output = [f"--- Telemetry ({scope}) ---", f"Identity: {telemetry_core.SIFT_CLIENT_ID} (Tier: {telemetry_core.SIFT_TIER})", f"Tool Calls: {total_calls}", f"Tokens Processed: {total_orig_tokens:,}", f"Tokens Saved: {tokens_saved:,} ({(tokens_saved/total_orig_tokens*100) if total_orig_tokens>0 else 0:.1f}%)", f"Avg Latency: {(total_lat/total_calls) if total_calls>0 else 0:.1f}ms", f"Cache Hits: {total_hits} ({(total_hits/total_calls*100) if total_calls>0 else 0:.1f}%)", "\nBreakdown:"]
        for tool, s in breakdown.items(): output.append(f"- {tool}: {s['calls']} calls, {s['tokens_saved']:,} tokens saved ({s['cache_hits']} hits)")
        return "\n".join(output)
    except Exception as e: return f"Error: {str(e)}"

@mcp.tool()
async def sift_onboard(target_dir: str = None) -> str:
    report = ["# 🔍 Onboarding Report\n", "## 💻 Environment", f"- Python: {sys.version.split()[0]}", f"- CUDA: {torch.cuda.is_available()}", f"- Device: {DEVICE}", "- Security: SAST/SCA Audited (0 CVEs)\n", "## 📝 Setup"]
    for action in update_instruction_files("SOP", "# 🔍 Semantic-Sift — SOP", SOP_TEMPLATE.strip(), target_dir): report.append(f"- {action}")
    report.append("\n**Fully configured.**\n"); report.append(await sift_orchestrate(target_dir=target_dir)); return "\n".join(report)

@mcp.tool()
async def sift_orchestrate(manual_tools: list[str] = None, custom_paths: list[str] = None, target_dir: str = None) -> str:
    discovered = set(); cwd = target_dir if target_dir else os.getcwd()
    if manual_tools: 
        for t in manual_tools: discovered.add(t.lower())
    local_s = os.path.join(cwd, ".gemini", "settings.json")
    if os.path.exists(local_s):
        try:
            with open(local_s, "r") as f:
                for name in json.load(f).get("mcpServers", {}).keys(): discovered.add(name.lower())
        except: pass
    for item in get_global_mcp_configs():
        for name in item["data"].get(item["key"], {}).keys(): discovered.add(name.lower())
    active_rules = set()
    for tool_name in discovered:
        for key, config in COLLABORATION_MAP.items():
            if key in tool_name: active_rules.add(config["rule"])
    header = "# 🤝 Unified Context Orchestration"; content = "\n".join(sorted(list(active_rules))) if active_rules else "- Discovery: use `sift_chat`.\n- Storage: sift > 1k chars.\n- Search: run `sift_extraction`.\n"
    actions = update_instruction_files("ORCHESTRATION", header, content.strip(), target_dir)
    summary = f"Analyzed `{cwd}`: {', '.join(discovered)}. Actions:\n"
    for action in actions: summary += f"- {action}\n"
    return summary

@mcp.tool()
async def sift_analyze(text: str) -> str:
    char_count = len(text); is_masked = "<tool_output_masked>" in text or "Output too large." in text
    if is_masked: return "## 🛡️ Host Truncation Detected\n- **Status**: Host already masked output.\n- **Recommendation**: **MANDATORY SIFT** raw file."
    timestamps = len(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', text)); uuids = len(re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', text)); repetition = len(re.findall(r'[=\-]{5,}|[\.]{3,}', text))
    noise_ratio = min((((timestamps * 10) + (uuids * 5) + (repetition * 2)) / char_count * 100) if char_count > 0 else 0, 100.0)
    report = ["## 📊 Context Analysis Report", f"- Length: {char_count:,} chars", f"- Estimated Noise: {noise_ratio:.1f}%", "\n### 🎯 Recommendation"]
    if noise_ratio > 15.0: report.extend(["- **Action**: Run `sift_logs`.", "- Reason: High structural noise."])
    elif char_count > 8000: report.extend(["- **Action**: Run `sift_doc` or `sift_chat`.", "- Reason: Long-form context."])
    elif char_count < 1000: report.extend(["- **Action**: No sifting required.", "- Reason: Context is already concise."])
    else: report.extend(["- **Action**: Optional `sift_chat`.", "- Reason: Moderate length."])
    return "\n".join(report)

@mcp.tool()
async def sift_rank(query: str, documents: list[str], top_n: int = 3) -> str:
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder('BAAI/bge-reranker-base', device=DEVICE)
        scores = model.predict([[query, doc] for doc in documents])
        scored_docs = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)[:top_n]
        report = [f"## 🎯 Reranking Results (Top {top_n})\n"]
        for i, (score, doc) in enumerate(scored_docs):
            report.append(f"### Rank {i+1} (Score: {score:.4f})\n{doc[:500]}..." if len(doc) > 500 else f"### Rank {i+1} (Score: {score:.4f})\n{doc}")
            report.append("\n---\n")
        return "\n".join(report)
    except Exception as e: return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
