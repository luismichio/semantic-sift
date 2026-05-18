# Semantic-Sift: Orchestration Blueprints

This document provides definitive workflow guides and operational recipes for maximizing the utility of the Semantic-Sift tool suite. These blueprints are designed to help AI agents and orchestrators maintain a high Signal-to-Noise Ratio (SNR) within their context windows.

---

## 1. Decision Trees: File Ingestion Strategy

When interacting with a new codebase or investigating an unknown file, agents face a choice: read the file natively (risking context flooding) or use Semantic-Sift. 

The optimal workflow utilizes `sift_analyze_file` as an exploratory "radar" before committing tokens to reading.

### The Ingestion Decision Tree

1.  **Target Identification**: The agent identifies a file required for the task (e.g., `app.log`, `README.md`, `large_config.json`).
2.  **Scouting Phase**: Execute `sift_analyze_file(path)`.
    *   *Result*: The tool returns a lightweight Markdown report detailing the character count and estimated `Noise Ratio`.
3.  **Action Phase**: Based on the recommendation from `sift_analyze_file`, the agent takes one of the following actions:
    *   **Scenario A: High Noise (> 15.0%)**
        *   *Action*: Execute `sift_read_file(path, type="logs")`.
        *   *Rationale*: The Heuristic Engine will incinerate timestamps and progress bars before the text ever hits the context window, saving up to 80% of token costs.
    *   **Scenario B: Massive Length (> 8000 characters)**
        *   *Action*: Execute `sift_read_file(path, type="doc")` or `sift_read_file(path, type="chat")`.
        *   *Rationale*: The file is too large for raw ingestion. The Semantic Engine will apply BERT-based prompt compression to distill the prose to its core meaning.
    *   **Scenario C: Short & Concise (< 1000 characters)**
        *   *Action*: Read the file natively (using standard IDE tools) or use `sift_read_file(path, type="auto")`.
        *   *Rationale*: The overhead of sifting is unnecessary for tiny configurations or scripts.
    *   **Scenario D: Moderate Length (1000 - 8000 characters)**
        *   *Action*: Optional `sift_read_file` based on the agent's current available context budget.

---

## 2. Context Optimization: Managing Token Limits

As conversations grow and multiple tools are executed, context limits become a hard ceiling on reasoning capabilities. These recipes define how to use `sift_rank` and targeted semantic compression to preserve analytical depth.

### Blueprint A: Multi-Document RAG (Retrieval-Augmented Generation)
When an agent performs broad searches (e.g., finding all files matching "Authentication"), the resulting payload can easily exceed 50,000 tokens.

*   **Step 1: Retrieve**: Execute search queries and collect the raw document chunks.
*   **Step 2: Rank & Prune**: Instead of reading all chunks, execute `sift_rank(query, documents, top_n=3)`.
    *   *Logic*: The internal `BAAI/bge-reranker-base` model will score each document chunk against the specific user query.
*   **Step 3: Ingest**: Only ingest the top 3 results returned by `sift_rank`. Discard the rest.
    *   *Result*: Context window remains uncluttered; the agent focuses only on the highest-signal code paths.

### Blueprint B: The "Out-of-Band" History Compaction
For agents executing long, multi-step reasoning chains, the chat history itself becomes the primary source of noise.

*   **Trigger**: The agent realizes the context window is nearing its limit (or a `Compacting` hook is fired natively by the IDE).
*   **Action**: Execute `sift_chat(text, rate=0.3)`.
*   **Logic**: 
    *   Pass the older portions of the conversation history or verbose tool outputs into `sift_chat` with an aggressive `0.3` rate.
    *   The Semantic Engine strips conversational filler ("I will now check...", "Based on the results...") while preserving factual assertions, file paths, and decisions.
*   **Result**: The agent replaces the verbose history with the compressed summary, freeing up tokens for the next analytical step without losing the "thread" of the investigation.

### Blueprint C: Post-Extraction Refining
When utilizing OCR tools or PDF parsers (like Docling), the raw output is often riddled with page numbers, copyright footers, and corrupted tables.

*   **Trigger**: A raw extraction string is returned from a parsing tool.
*   **Action**: Execute `sift_extraction(content)`.
*   **Logic**: 
    *   The tool first runs RegEx to surgically remove repetitive OCR artifacts (`Page X of Y`).
    *   It then applies a gentle Semantic Sift (`rate=0.7`) to compress the surrounding text while explicitly protecting Markdown structures like `| Tables |` and `# Headers`.
*   **Result**: A pristine, token-efficient Markdown document ready for grounding or indexing.

---

## 3. Multi-Agent Orchestration & Subagent Shielding

Modern agentic workflows often involve spawning specialized subagents (Workers) from a primary Orchestrator. These subagents frequently start with an isolated context window ("blank slate"), making them prone to flooding their context while trying to "understand" the codebase.

### Blueprint D: The "Shielded Worker" (Recursive Onboarding)
To ensure every agent thread follows the context sanitation protocol:

1.  **Orchestrator Setup**: The human developer runs `sift_onboard()` in the project root.
2.  **Recursive Shielding**: Semantic-Sift automatically discovers specialized agent folders (`.cursor/agents/`, `.codex/agents/`, etc.) and injects the **Sift Mandate** directly into their system instructions.
3.  **Inheritance**:
    *   **Hooks**: In Smart Hook environments (Gemini, Claude, OpenCode), subagents automatically inherit the `PostToolUse` interceptors, ensuring "Subconscious Sifting" occurs even if the subagent ignores its prompt instructions.
    *   **Prompt Mandates**: By explicitly shielding the subagent's configuration file, the worker agent is commanded to use `sift_read_file` for its own investigative steps, preventing context crashes in background threads.

---

## 4. The MCP Synergy Matrix (Operational Recipes)

AI agents must manually apply specific sifting tools based on the *source* of the data to avoid context corruption (e.g., BERT destroying JSON syntax).

| Data Source | MCP Tool Example | Recommended Recipe |
| :--- | :--- | :--- |
| **Web / HTML** | Puppeteer, Fetch | Use `sift_doc` to incinerate JS/CSS and keep clean text. |
| **Cloud Logs** | AWS, Vercel, GHA | Use `sift_logs` to strip timestamps, ETags, and progress bars. |
| **Databases** | Postgres, SQLite | **DO NOT** use semantic sifting. Use SQL `LIMIT` or `sift_analyze` to verify density. |
| **Discovery** | Serena, Investigator | Use `sift_chat(rate=0.7)` on retrieved code bodies > 100 lines. |
| **Broad Search** | GitHub, Ripgrep | Collect all chunks and pass to `sift_rank` to return Top-3 results. |
| **Long Chat** | Conversation Hist. | Use `sift_chat(rate=0.3)` Aggressive to compact analytical investigations. |

*Note: These synergies are automatically injected into agent system prompts during the `sift_onboard` process.*
---

## 5. `Ecosystem Integration (Context-Pipe)`

Semantic-Sift is one half of the **Studio of Two** ecosystem. The other half is **[Context-Pipe](https://github.com/luismichio/context-pipe)** (`mcp-context-pipe` on PyPI), which handles OS-level pipe orchestration, shadow MCP tool routing, and dynamic multi-node pipeline execution.

### Roles & Boundaries

| Concern | Context-Pipe | Semantic-Sift |
| :--- | :--- | :--- |
| **Token Reduction** | No | Yes (`sift_*` tools) |
| **Pipe Orchestration** | Yes (`run_pipe`, `run_dynamic_pipe`) | No |
| **Shadow MCP Routing** | Yes (`pipe_list_shadow_tools`) | No |
| **IDE Onboarding** | Yes (`pipe_onboard`) | Yes (`sift_onboard`) |
| **Context Balance Sheet** | Yes (pipe-level ROI) | Yes (sift-level ROI) |
| **Hook Interception** | Yes (`pipe_hook.py`) | Yes (`hook.py`) |

### Recommended Wiring Pattern

For maximum context efficiency, run semantic-sift **both sides** of a context-pipe node:

1. **Before indexing**: Compress large documents with `sift_doc` or `sift_chat` before passing to `context-mode_index`.
2. **After retrieval**: Distil retrieved code bodies > 100 lines with `sift_chat(rate=0.7)` via the `semantic-refinery` pipe.

In this model, the **orchestrator remains silent**. Visible identity and audit headers are provided by `semantic-sift-cli` nodes, ensuring a clean context window.

```json
// pipes.json — semantic-refinery pipe
{
  "pipes": [
    {
      "name": "semantic-refinery",
      "nodes": [
        { "cmd": "semantic-sift-cli", "args": ["semantic", "--rate", "0.7"] }
      ]
    }
  ]
}
```

### Context-Pipe → Semantic-Sift Call Pattern
When a context-pipe dynamic node needs to compress content on-the-fly, it calls `semantic-sift-cli` as a subprocess node (Type B). The `PIPE_WINDOW_PRESSURE` env var (0.0–1.0) is forwarded to each node; `semantic-sift-cli` reads it to automatically override `--rate` when context pressure is high.
