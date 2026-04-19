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

# Global Configuration
SESSION_ID = str(uuid.uuid4())
TELEMETRY_FILE = ".sift_telemetry.json"
CACHE_DIR = ".sift_cache"
START_TIME = datetime.now().isoformat()

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Device Detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Master list of instruction files for various IDEs and tools
INSTRUCTION_TARGETS = [
    "AGENTS.md",                         # Generic / Studio of Two
    "GEMINI.md",                         # Gemini CLI / Antigravity
    ".clinerules",                       # Cline / Roo Code
    ".cursorrules",                      # Cursor
    ".windsurfrules",                    # Windsurf
    ".github/copilot-instructions.md"    # GitHub Copilot
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

## 🚫 Sifting Forbidden
- **NEVER** sift foundational instructions (`AGENTS.md`, `GEMINI.md`).
- **NEVER** sift small, surgical code snippets (symbol-level).
- **NEVER** sift security-sensitive configuration files (`.env`, secrets).
"""

# Collaboration Blueprint for known MCPs (Heuristic Matching)
COLLABORATION_MAP = {
    # Discovery & Development
    "serena": {
        "workflow": "Discovery -> Sifting",
        "rule": "- **Serena Synergy**: Always pipe code bodies > 100 lines through `sift_chat` (rate: 0.7) after retrieval to prune docstring/comment bloat while keeping logic."
    },
    "investigator": {
        "workflow": "Research -> Distillation",
        "rule": "- **Investigator Synergy**: Run `sift_doc` on comprehensive architectural reports or file-system scans to identify core patterns quickly."
    },
    # Storage & Memory
    "context-mode": {
        "workflow": "Sifting -> Storage",
        "rule": "- **Context-Mode Synergy**: Run `sift_logs` or `sift_chat` on all tool outputs > 1,000 characters BEFORE calling `context-mode_ctx_index`. This ensures the FTS5 search index remains high-signal."
    },
    "memory": {
        "workflow": "Recall -> Compaction",
        "rule": "- **Memory Synergy**: Periodically call `sift_chat` on retrieved long-term memories to condense historical facts into high-signal summaries."
    },
    # Knowledge & Communication
    "slack": {
        "workflow": "Chat -> Decision",
        "rule": "- **Slack Synergy**: Sift Slack history to keep only the decisions and action items, ignoring linguistic filler, emoji reactions, and system events."
    },
    "discord": {
        "workflow": "History -> Signal",
        "rule": "- **Discord Synergy**: Use `sift_chat` on verbose Discord threads to isolate the technical thread of conversation."
    },
    "notion": {
        "workflow": "Docs -> Cleaning",
        "rule": "- **Notion Synergy**: Use `sift_extraction` on Notion pages to remove redundant block metadata and JSON artifacts, keeping only the documentation prose."
    },
    "confluence": {
        "workflow": "Wiki -> Signal",
        "rule": "- **Confluence Synergy**: Sift Confluence pages to remove enterprise header/footer noise and navigation elements."
    },
    # Infrastructure & Cloud
    "aws": {
        "workflow": "Infra -> Logic",
        "rule": "- **AWS Synergy**: Apply `sift_logs` to cloud resource descriptions (JSON) to strip low-entropy metadata (ETags, Request IDs) and focus on configuration."
    },
    "gcp": {
        "workflow": "Cloud -> Precision",
        "rule": "- **GCP Synergy**: Sift verbose GCloud CLI outputs to isolate error states and resource properties."
    },
    "azure": {
        "workflow": "Cloud -> Logic",
        "rule": "- **Azure Synergy**: Use `sift_logs` on Azure resource snapshots to reduce token-load during environment analysis."
    },
    # Databases
    "postgres": {
        "workflow": "Data -> Sample",
        "rule": "- **Postgres Synergy**: If a query returns > 50 rows, run `sift_logs` to preserve the schema and edge rows while pruning the middle to save tokens."
    },
    "sql": {
        "workflow": "Query -> Signal",
        "rule": "- **SQL Synergy**: Sift large SQL query results to focus on the schema and anomalous data points."
    },
    "sqlite": {
        "workflow": "Local Data -> Density",
        "rule": "- **SQLite Synergy**: Use `sift_logs` on database dumps to maintain a lean context during local data exploration."
    },
    # Execution & Browsing
    "puppeteer": {
        "workflow": "Browser -> Signal",
        "rule": "- **Puppeteer Synergy**: Always run `sift_extraction` on browser text to remove ads, tracking scripts, and navigation menus before analysis."
    },
    "playwright": {
        "workflow": "Browser -> Extraction",
        "rule": "- **Playwright Synergy**: Run `sift_extraction` on raw HTML fetches to ensure the agent only sees high-density content."
    },
    "browser": {
        "workflow": "Web -> Density",
        "rule": "- **Browser Synergy**: Use `sift_extraction` to clean up web content retrieved from browser-based tools."
    },
    # Workflow & Management
    "jira": {
        "workflow": "Task -> Resolution",
        "rule": "- **Jira Synergy**: Sift Jira ticket comments to focus on the 'State Change' and 'Resolution' logic, ignoring boilerplate status updates."
    },
    "linear": {
        "workflow": "Issues -> Signal",
        "rule": "- **Linear Synergy**: Use `sift_chat` on issue descriptions and comment chains to isolate requirements and technical blockers."
    },
    # Source Control
    "github": {
        "workflow": "Search -> Distillation",
        "rule": "- **GitHub Synergy**: Use `sift_logs` on verbose PR diffs or repository search results to focus on actionable code changes."
    },
    "github-copilot": {
        "workflow": "Context -> Precision",
        "rule": "- **Copilot Synergy**: Always sift large context windows (multi-file reads) before presenting to Copilot to reduce 'hallucination' and improve suggestion accuracy."
    },
    # Generic Utilities
    "fetch": {
        "workflow": "Fetch -> Cleaning",
        "rule": "- **Fetch Synergy**: Always sift raw HTML/Markdown fetched from URLs to maintain context density."
    },
    "brave-search": {
        "workflow": "Search -> Signal",
        "rule": "- **Brave Synergy**: When fetching long web pages, run `sift_extraction` to remove technical debris and UI noise."
    }
}

# Create the MCP server
mcp = FastMCP("Semantic-Sift")

# --- Helpers ---

def log_telemetry(tool_name: str, original_chars: int, final_chars: int, latency_ms: float, cache_hit: bool = False):
    """Logs tool performance metrics to a persistent JSON file."""
    try:
        data = {}
        if os.path.exists(TELEMETRY_FILE):
            with open(TELEMETRY_FILE, "r") as f:
                data = json.load(f)
        
        if SESSION_ID not in data:
            data[SESSION_ID] = {
                "start_time": START_TIME,
                "tools": {}
            }
        
        tool_stats = data[SESSION_ID]["tools"].get(tool_name, {
            "calls": 0,
            "original_chars": 0,
            "final_chars": 0,
            "total_latency_ms": 0,
            "cache_hits": 0
        })
        
        tool_stats["calls"] += 1
        tool_stats["original_chars"] += original_chars
        tool_stats["final_chars"] += final_chars
        tool_stats["total_latency_ms"] += latency_ms
        if cache_hit:
            tool_stats["cache_hits"] = tool_stats.get("cache_hits", 0) + 1
        
        data[SESSION_ID]["tools"][tool_name] = tool_stats
        
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def get_cache_key(tool_name: str, text: str, **kwargs) -> str:
    """Generates a unique SHA-256 hash for a sifting request."""
    payload = f"{tool_name}:{text}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()

def check_cache(key: str) -> str | None:
    """Retrieves result from local disk cache if it exists."""
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def set_cache(key: str, result: str):
    """Saves a sifting result to local disk cache."""
    cache_path = os.path.join(CACHE_DIR, f"{key}.txt")
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(result)

def get_global_mcp_configs() -> list[dict]:
    """Attempts to find and parse multiple system-wide MCP configurations."""
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
        if "os" in item and sys.platform != item["os"]:
            continue
        full_path = os.path.expanduser(item["path"])
        if os.path.exists(full_path):
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    configs.append({"data": data, "key": item["key"]})
            except Exception:
                pass
    return configs

def update_instruction_files(section_id: str, header: str, content: str, target_dir: str = None) -> list[str]:
    """Surgically injects or updates a section in all detected instruction files."""
    actions = []
    cwd = target_dir if target_dir else os.getcwd()
    found_any = False
    block_id = f"<!-- SIFT_SECTION_START:{section_id} -->"
    block_end = f"<!-- SIFT_SECTION_END:{section_id} -->"
    full_payload = f"\n{block_id}\n---\n\n{header}\n{content}\n{block_end}\n"
    for filename in INSTRUCTION_TARGETS:
        target_path = os.path.join(cwd, filename)
        if os.path.exists(target_path):
            found_any = True
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                pattern = re.compile(rf'{re.escape(block_id)}.*?{re.escape(block_end)}', re.DOTALL)
                if pattern.search(file_content):
                    new_content = pattern.sub(full_payload.strip(), file_content)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    actions.append(f"Updated `{filename}`.")
                else:
                    with open(target_path, "a", encoding="utf-8") as f:
                        f.write(full_payload)
                    actions.append(f"Injected into `{filename}`.")
            except Exception as e:
                actions.append(f"Error updating `{filename}`: {str(e)}")
    if not found_any:
        fallback = "AGENTS.md"
        try:
            os.makedirs(cwd, exist_ok=True)
            with open(os.path.join(cwd, fallback), "w", encoding="utf-8") as f:
                f.write(f"# Project Instructions\n{full_payload}")
            actions.append(f"Created new `{fallback}` in `{cwd}`.")
        except Exception as e:
            actions.append(f"Error creating `{fallback}`: {str(e)}")
    return actions

# --- Tools ---

@mcp.tool()
async def sift_logs(raw_text: str) -> str:
    """Sifts through raw technical logs to remove noise."""
    start_t = time.time()
    lines = raw_text.splitlines()
    sifted = []
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?\s*')
    progress_pattern = re.compile(r'\[\d+/\d+\]|[\.]{3,}|\d+%\s*')
    module_pattern = re.compile(r'^\s*[\d\.]+\s+[\w\-\.\/]+\s+\d+\s+bytes.*$')
    for line in lines:
        clean_line = timestamp_pattern.sub('', line).strip()
        if not clean_line or progress_pattern.search(clean_line) or module_pattern.match(clean_line):
            continue
        sifted.append(clean_line)
    result = "\n".join(sifted)
    latency = (time.time() - start_t) * 1000
    log_telemetry("sift_logs", len(raw_text), len(result), latency)
    return result

@mcp.tool()
async def sift_chat(text: str, rate: float = 0.5) -> str:
    """Semantically prunes conversation history using LLMLingua-2."""
    start_t = time.time()
    cache_key = get_cache_key("sift_chat", text, rate=rate)
    cached_result = check_cache(cache_key)
    if cached_result:
        log_telemetry("sift_chat", len(text), len(cached_result), (time.time() - start_t) * 1000, cache_hit=True)
        return cached_result
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([text], rate=rate, force_tokens=['\n', '?'], chunk_end_tokens=['.', '\n'], return_word_label=False)
        result = results.get('compressed_prompt', text)
        set_cache(cache_key, result)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_chat", len(text), len(result), latency)
        return result
    except Exception as e:
        return f"Error during semantic sifting: {str(e)}"

@mcp.tool()
async def sift_doc(text: str, budget_tokens: int = 1000) -> str:
    """Condenses long documents using a multi-stage approach."""
    start_t = time.time()
    cache_key = get_cache_key("sift_doc", text, budget_tokens=budget_tokens)
    cached_result = check_cache(cache_key)
    if cached_result:
        log_telemetry("sift_doc", len(text), len(cached_result), (time.time() - start_t) * 1000, cache_hit=True)
        return cached_result
    cleaned = await sift_logs(text)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([cleaned], rate=0.4, force_tokens=['[', ']', '{', '}', '/', '\\', '.', '_'], chunk_end_tokens=['\n', '.', ';'], return_word_label=False)
        result = results.get('compressed_prompt', cleaned)
        set_cache(cache_key, result)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_doc", len(text), len(result), latency)
        return result
    except Exception as e:
        return f"Error during document sifting: {str(e)}"

@mcp.tool()
async def sift_extraction(content: str, source_type: str = "markdown") -> str:
    """Refines outputs from Docling or LiteParse."""
    start_t = time.time()
    cache_key = get_cache_key("sift_extraction", content, source_type=source_type)
    cached_result = check_cache(cache_key)
    if cached_result:
        log_telemetry("sift_extraction", len(content), len(cached_result), (time.time() - start_t) * 1000, cache_hit=True)
        return cached_result
    refined = content
    for pattern in [r'Page \d+ of \d+', r'© .*? All rights reserved', r'---+\s*$', r'^\s*·\s*$']:
        refined = re.sub(pattern, '', refined, flags=re.MULTILINE | re.IGNORECASE)
    try:
        from llmlingua import PromptCompressor
        compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map=DEVICE)
        results = compressor.compress_prompt([refined], rate=0.7, force_tokens=['\n', '|', '-', ':', '#'], chunk_end_tokens=['\n', '.'], return_word_label=False)
        result = results.get('compressed_prompt', refined)
        set_cache(cache_key, result)
        latency = (time.time() - start_t) * 1000
        log_telemetry("sift_extraction", len(content), len(result), latency)
        return result
    except Exception as e:
        return f"Error during extraction sifting: {str(e)}"

@mcp.tool()
async def get_sift_stats(scope: str = "current") -> str:
    """Returns telemetry stats for the sifting process."""
    if not os.path.exists(TELEMETRY_FILE):
        return "No telemetry data found."
    try:
        with open(TELEMETRY_FILE, "r") as f:
            data = json.load(f)
        target_sessions = [data[SESSION_ID]] if scope == "current" and SESSION_ID in data else list(data.values())
        if not target_sessions:
            return "No data found."
        total_calls = total_orig = total_final = total_latency = total_cache_hits = 0
        tool_breakdown = {}
        for session in target_sessions:
            for tool, stats in session.get("tools", {}).items():
                calls = stats.get("calls", 0); orig = stats.get("original_chars", 0); final = stats.get("final_chars", 0); latency = stats.get("total_latency_ms", 0); hits = stats.get("cache_hits", 0)
                total_calls += calls; total_orig += orig; total_final += final; total_latency += latency; total_cache_hits += hits
                if tool not in tool_breakdown: tool_breakdown[tool] = {"calls": 0, "saved": 0, "cache_hits": 0}
                tool_breakdown[tool]["calls"] += calls; tool_breakdown[tool]["saved"] += (orig - final); tool_breakdown[tool]["cache_hits"] += hits
        saved = total_orig - total_final
        reduction = (saved / total_orig * 100) if total_orig > 0 else 0
        avg_lat = (total_latency / total_calls) if total_calls > 0 else 0
        hit_rate = (total_cache_hits / total_calls * 100) if total_calls > 0 else 0
        report = [f"--- Semantic-Sift Telemetry ({scope.capitalize()}) ---", f"Total Sift Calls: {total_calls}", f"Characters Processed: {total_orig:,}", f"Characters Pruned: {saved:,} ({reduction:.1f}% reduction)", f"Avg Latency: {avg_lat:.1f}ms", f"Cache Hit Rate: {hit_rate:.1f}% ({total_cache_hits} hits)", "\nBreakdown by Tool:"]
        for tool, stats in tool_breakdown.items(): report.append(f"- {tool}: {stats['calls']} calls, {stats['saved']:,} chars saved ({stats['cache_hits']} cache hits)")
        return "\n".join(report)
    except Exception as e:
        return f"Error reading telemetry: {str(e)}"

@mcp.tool()
async def sift_onboard(target_dir: str = None) -> str:
    """Automates installation of guidelines into all project instruction files."""
    report = ["# 🔍 Semantic-Sift Onboarding Report\n", "## 💻 Environment", f"- Python: {sys.version.split()[0]}", f"- CUDA Active: {torch.cuda.is_available()}", f"- Device: {DEVICE}\n", "## 📝 Setup"]
    for action in update_instruction_files("SOP", "# 🔍 Semantic-Sift — Standard Operating Procedures", SOP_TEMPLATE.strip(), target_dir=target_dir):
        report.append(f"- {action}")
    report.append("\n**Semantic-Sift is now fully configured.**\n")
    report.append(await sift_orchestrate(target_dir=target_dir))
    return "\n".join(report)

@mcp.tool()
async def sift_orchestrate(manual_tools: list[str] = None, custom_paths: list[str] = None, target_dir: str = None) -> str:
    """Analyzes available MCPs and injects collaborative rules."""
    discovered = set()
    cwd = target_dir if target_dir else os.getcwd()
    if custom_tools := manual_tools:
        for t in custom_tools: discovered.add(t.lower())
    local_settings = os.path.join(cwd, ".gemini", "settings.json")
    if os.path.exists(local_settings):
        try:
            with open(local_settings, "r") as f:
                data = json.load(f)
                for name in data.get("mcpServers", {}).keys(): discovered.add(name.lower())
        except Exception: pass
    for item in get_global_mcp_configs():
        for name in item["data"].get(item["key"], {}).keys(): discovered.add(name.lower())
    if custom_paths:
        for path in custom_paths:
            full_path = os.path.expanduser(path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r") as f:
                        data = json.load(f)
                        for k in ["mcpServers", "context_servers", "servers"]:
                            if k in data:
                                for name in data[k].keys(): discovered.add(name.lower())
                except Exception: pass
    active_rules = set()
    for tool_name in discovered:
        if tool_name in COLLABORATION_MAP: active_rules.add(COLLABORATION_MAP[tool_name]["rule"])
        else:
            for key, config in COLLABORATION_MAP.items():
                if key in tool_name: active_rules.add(config["rule"])
    header = "# 🤝 Unified Context Orchestration"
    if not active_rules:
        content = "- **Discovery Strategy**: Use `sift_chat` (rate: 0.7) on retrieved bodies > 100 lines.\n- **Storage Strategy**: Sift outputs > 1,000 chars before indexing.\n- **Search Strategy**: Run `sift_extraction` on web/search results.\n"
    else:
        content = "\n".join(sorted(list(active_rules)))
    actions = update_instruction_files("ORCHESTRATION", header, content.strip(), target_dir=target_dir)
    summary = f"Analyzed tools in `{cwd}`: {', '.join(discovered)}. Actions:\n"
    for action in actions: summary += f"- {action}\n"
    return summary

@mcp.tool()
async def sift_analyze(text: str) -> str:
    """
    Evaluates context quality (SNR) and recommends appropriate sifting tools.
    Detects if the host environment (e.g. Gemini CLI) has already truncated the output.
    """
    char_count = len(text)
    is_masked = "<tool_output_masked>" in text or "Output too large. Full output available at:" in text
    if is_masked:
        return (
            "## 🛡️ Environment Alert: Host-Level Truncation Detected\n"
            "- **Status**: The host environment (Gemini CLI) has already masked or truncated this output to protect your context.\n"
            "- **Observation**: Because the data is already hidden, a local SNR analysis would be inaccurate.\n"
            "- **Recommendation**: **MANDATORY SIFT**. Locate the raw file path provided by the host and run `sift_logs` or `sift_doc` "
            "directly on that file before attempting to analyze its contents."
        )
    line_count = len(text.splitlines()); avg_line_len = char_count / line_count if line_count > 0 else 0
    timestamps = len(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', text))
    uuids = len(re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', text))
    repetition = len(re.findall(r'[=\-]{5,}|[\.]{3,}', text))
    noise_ratio = min((((timestamps * 10) + (uuids * 5) + (repetition * 2)) / char_count * 100) if char_count > 0 else 0, 100.0)
    report = ["## 📊 Context Analysis Report", f"- Length: {char_count:,} chars", f"- Estimated Noise: {noise_ratio:.1f}%", "\n### 🎯 Recommendation"]
    if noise_ratio > 15.0: report.extend(["- **Action**: Run `sift_logs`.", "- Reason: High structural noise."])
    elif char_count > 8000: report.extend(["- **Action**: Run `sift_doc` or `sift_chat`.", "- Reason: Long-form context."])
    elif char_count < 1000: report.extend(["- **Action**: No sifting required.", "- Reason: Context is concise."])
    else: report.extend(["- **Action**: Optional `sift_chat`.", "- Reason: Moderate length."])
    return "\n".join(report)

@mcp.tool()
async def sift_rank(query: str, documents: list[str], top_n: int = 3) -> str:
    """Ranks multiple text chunks by relevance."""
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
    except Exception as e: return f"Error during reranking: {str(e)}"

if __name__ == "__main__":
    mcp.run()
