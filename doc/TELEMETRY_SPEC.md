# Semantic-Sift: Telemetry & Tracing Specification

This document provides the technical design of data tracing, privacy controls, and the pulse system (`telemetry_core.py`) within the Semantic-Sift architecture. It ensures transparency, debuggability, and compliance with strict data sovereignty standards.

---

## 1. OpenTelemetry (OTel) Integration

To provide a verifiable "Chain of Custody" for all data transformations without interfering with the host application (e.g., the IDE or CLI agent), Semantic-Sift utilizes a heavily isolated OpenTelemetry configuration.

### Tracer Configuration
*   **Provider**: An isolated `TracerProvider` is instantiated specifically for Semantic-Sift to prevent span collision with the host agent's native tracing.
*   **Resource Attributes**: The provider is bound to the `service.name`: `"semantic-sift-mcp"`.
*   **Exporter**: Uses a `SimpleSpanProcessor` with an `InMemorySpanExporter`. This ensures that span data remains isolated and does not pollute standard output streams required by MCP protocols.
*   **Fallback**: If the `opentelemetry` library is unavailable or `SIFT_TELEMETRY_DISABLED=true`, it falls back to a dummy `MockTracer` to prevent runtime crashes.

### Custom Span Attributes
The system injects precise metadata into spans depending on the execution context:
*   **Server Tool Spans (`server.py`)**:
    *   `sift_read_file:<type>` and `sift_analyze_file` spans inject `file.path`.
    *   `sift_read_file` spans calculate and inject `sift.reduction_pct` (`(1 - len(result)/len(content)) * 100`).
*   **Hook Interceptor Spans (`sift_hook.py`)**:
    *   `subconscious_sift` spans inject `tool.name`, `platform`, `agent.label` (e.g., `"Main"`, `"Explore"`, `"researcher"`), and `is_echo` to track routing and bypass events accurately.

---

## 2. Echo Detector (Double-Sifting Prevention)

Because some IDEs (like Cursor and VS Code) utilize "Blind Hooks" that pass the output of `sift_read_file` directly back into `sift_hook.py`, the system must prevent the Semantic Engine from running twice on the same data.

### Disk-Based Hash Caching
*   **Mechanism**: When `sift_hook.py` intercepts a payload, it passes the raw content to `telemetry_core.check_echo(text)`.
*   **Key Generation**: The content is hashed using SHA-256 (`hashlib.sha256(text.encode()).hexdigest()`).
*   **Storage**: An empty marker file is written to the `.sift_cache/` directory as `echo_<hash>.tmp`.
*   **Content Criteria**: Echo detection is skipped if the content length is less than 100 characters.

### TTL (Time-To-Live) Logic
*   **Expiry**: The `.tmp` file stores a timestamp indicating its expiry (`time.time() + 30`).
*   **30-Second Window**: The Echo Detector enforces a strict 30-second TTL. If the same content hash is intercepted within 30 seconds, `check_echo` returns `True`, immediately bypassing BERT and Heuristic processing to save compute. Expired files are automatically deleted.

---

## 3. Audit Headers

Audit Headers are injected directly into the LLM's context window (prepended to the tool output) to explicitly notify the agent of the token savings and processing latency. 

### Configuration (`SIFT_AUDIT_HEADER`)
The header format is controlled via the `SIFT_AUDIT_HEADER` environment variable:
*   **`full` (Default)**:
    ```markdown
    --- [Semantic-Sift Audit] ---
    📊 Reduction: 45.2% (15.2KB -> 8.3KB)
    🛡️ Guard: Trace-Verified (No Echo)
    ⚡ Latency: 120.5ms
    -----------------------------
    ```
    *Note: If `is_echo=True`, the Guard status changes to `🚨 ECHO DETECTED (Bypassed)`.*
*   **`minimal`**:
    ```markdown
    [Semantic-Sift: 45.2% Savings | ⚡ 120.5ms]
    ```
*   **`silent`**: Returns an empty string. Completely hides the sifting action from the LLM context.

---

## 4. Telemetry Pulse API & Privacy Controls

Semantic-Sift implements a dual-layer logging system: Local persistent logging and Global anonymous pulses.

### Local Telemetry (`.sift_telemetry.json`)
*   **Function**: `log_telemetry()` writes aggregated session data to the local disk.
*   **Schema**: Organizes metrics by `session_id` (a UUID generated on server boot).
*   **Metrics Tracked**: `calls`, `original_chars`, `final_chars`, `original_tokens`, `final_tokens`, `total_latency_ms`, and `cache_hits`.
*   **Token Estimation**: Uses a fast heuristic: `max(1, len(text) // 4)`.

### Global Telemetry Pulse
*   **Function**: `send_telemetry_pulse()` fires a **non-blocking, async** POST request dispatched on a daemon thread. The call returns immediately so it never adds latency to the MCP tool response.
*   **Rate Limiting**: A token-bucket limiter enforces a minimum interval of `SIFT_PULSE_RATE_LIMIT_S` seconds (default: `10`) between pulses. If a pulse arrives within the rate window, it is queued and sent after the window expires, ensuring high-frequency agent use does not saturate the network.
*   **Endpoint**: Defined by `SIFT_TELEMETRY_URL` (default: `https://www.luiskobayashi.com/api/sift`).
*   **High-Fidelity Intercept Attribution**: When sifting is triggered by the `sift_hook.py` interceptor (the "Subconscious Brain"), the `tool_name` is reported using the convention `{sift_type}:{original_tool_name}` (e.g., `sift_rank:grep_search` or `sift_chat:fetch`). 
*   **Format Attribution**: The `file_ext` field identifies the format of the processed data (e.g., `.pdf`, `.xlsx`, `.html`, `grep`), allowing for ROI analysis across different content types.
*   **Security Constraint**: Enforces `http://` or `https://` schemes only (Bandit B310 compliance).
*   **Payload Schema**:
    ```json
    {
        "client_id": "Claude",
        "agent_label": "researcher-subagent",
        "tool_name": "sift_chat:fetch",
        "file_ext": "html",
        "original_chars": 15000,
        "final_chars": 5000,
        "original_tokens": 3750,
        "final_tokens": 1250,
        "tokens_saved": 2500,
        "latency_ms": 145.2,
        "timestamp": "2026-04-25T10:00:00.000+02:00"
    }
    ```

### Licensing & Identity
*   **`SIFT_CLIENT_ID`**: Resolved once at MCP server startup via `telemetry_core.detect_client_id()`. Identifies the host application for MCP tool calls (`sift_chat`, `sift_read_file`, etc.).
*   **Platform Identity Resolution** (`detect_client_id()`): Uses a four-step priority chain, shared by both the MCP server process and every hook subprocess:
    1.  Explicit `SIFT_CLIENT_ID` env var (always wins).
    2.  Ambient IDE env var fingerprints (`_ENV_MAP`) — checked in priority order. Google Antigravity vars (`ANTIGRAVITY_AGENT`, `ANTIGRAVITY_EDITOR_APP_ROOT`, `ANTIGRAVITY_TRAJECTORY_ID`) are checked **before** `VSCODE_PID` because Antigravity inherits VS Code's process environment. Per-call hook vars (`CLAUDE_TOOL_NAME`, `GEMINI_SESSION_ID`, etc.) are checked last — they are only present in hook subprocesses, not the long-running MCP server process.
    3.  Parent process name heuristic via `psutil` (fragment match against known process names).
    4.  `"Generic CLI"` fallback.
*   **Hook-Layer Identity**: `sift_hook.py` calls `telemetry_core.detect_client_id()` once per invocation (Phase 1) to resolve `platform` from the subprocess environment. This is the **authoritative per-call identity source**. Payload structure parsing (Phase 2 — extracting `raw_content` and `agent_label`) is strictly separate and does not influence the platform label.
*   **Shared-Server Limitation**: When multiple agents connect to the same MCP server process (e.g., Zed running Gemini CLI + OpenCode simultaneously), `SIFT_CLIENT_ID` reflects whichever agent's environment was present at server launch and cannot be updated per-call. MCP tool calls in such sessions carry a best-effort session-level identity. Hook-layer telemetry (resolved independently per subprocess) remains accurate per-call.
*   **Aggressive Tool Sniffing**: To minimize `unknown` tool entries, the interceptor uses a recursive discovery engine that searches for tool names across common JSON keys (`tool_name`, `tool`, `call`, etc.) and nested payload structures.
*   **Subagent Tracking (`agent_label`)**: The interceptor further "sniffs" the payload for subagent markers (e.g., `CLAUDE_AGENT_NAME`, `threadLabel`, or result prefixes like `[Explore]`) to attribute context savings to specific specialized agent threads.
*   **Anonymous Pulses**: All telemetry is fully transient and anonymous. No machine identifiers or license keys are stored or transmitted.
*   **Git Protection**: During the `sift_onboard` process, `.sift_telemetry.json` is automatically added to the project's `.gitignore` to prevent accidental exposure of usage patterns.

### Retention and Deletion

- Local telemetry registry: `.sift_telemetry.json` in the workspace directory.
- The file contains only aggregated counts and timestamps — no content, no prompts, no file paths.
- To delete local telemetry data, remove `.sift_telemetry.json` from your workspace.
- For global telemetry policy or deletion requests: https://www.luiskobayashi.com/contact

---

### The Privacy Kill-Switch
*   **Variable**: `SIFT_TELEMETRY_DISABLED=true` (Meechi Compliance).
*   **Effect**: 
    *   Instantly disables OpenTelemetry (`get_tracer` returns a basic pass-through).
    *   Disables Echo Detection (`check_echo` returns `False`).
    *   Forces Audit Headers to return empty (`""`).
    *   Blocks all local writing to `.sift_telemetry.json`.
    *   Blocks all network traffic to `SIFT_TELEMETRY_URL`.
    *   Forces `get_machine_id()` to return `"anonymous-user"`.
