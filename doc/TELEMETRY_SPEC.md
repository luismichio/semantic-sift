# Semantic-Sift: Telemetry & Tracing Specification

This document provides the technical design of data tracing, privacy controls, and the pulse system (`telemetry_core.py`) within the Semantic-Sift architecture. It ensures transparency, debuggability, and compliance with strict data sovereignty standards.

---

## 1. OpenTelemetry (OTel) Integration

To provide a verifiable "Chain of Custody" for all data transformations without interfering with the host application (e.g., the IDE or CLI agent), Semantic-Sift utilizes a heavily isolated OpenTelemetry configuration.

### Tracer Configuration
*   **Provider**: An isolated `TracerProvider` is instantiated specifically for Semantic-Sift to prevent span collision with the host agent's native tracing.
*   **Resource Attributes**: The provider is bound to the `service.name`: `"semantic-sift-mcp"`.
*   **Exporter**: Uses a `SimpleSpanProcessor` with a `ConsoleSpanExporter`. This ensures that span data is printed directly to the standard error/output stream for local verification by the developer, validating the exact character reduction at runtime.
*   **Fallback**: If the `opentelemetry` library is unavailable or `SIFT_TELEMETRY_DISABLED=true`, it falls back to a dummy `MockTracer` to prevent runtime crashes.

### Custom Span Attributes
The system injects precise metadata into spans depending on the execution context:
*   **Server Tool Spans (`server.py`)**:
    *   `sift_read_file:<type>` and `sift_analyze_file` spans inject `file.path`.
    *   `sift_read_file` spans calculate and inject `sift.reduction_pct` (`(1 - len(result)/len(content)) * 100`).
*   **Hook Interceptor Spans (`sift_hook.py`)**:
    *   `subconscious_sift` spans inject `tool.name`, `platform`, and `is_echo` to track routing and bypass events accurately.

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
*   **Function**: `send_telemetry_pulse()` fires a non-blocking POST request for aggregate analytics.
*   **Endpoint**: Defined by `SIFT_TELEMETRY_URL` (default: `https://www.luiskobayashi.com/api/sift`).
*   **Security Constraint**: Enforces `http://` or `https://` schemes only (Bandit B310 compliance).
*   **Payload Schema**:
    ```json
    {
        "machine_id": "anonymous-uuid",
        "client_id": "Generic CLI",
        "tier": "Community",
        "tool_name": "sift_logs",
        "original_chars": 15000,
        "final_chars": 5000,
        "original_tokens": 3750,
        "final_tokens": 1250,
        "tokens_saved": 2500,
        "latency_ms": 145.2,
        "timestamp": "2026-04-25T10:00:00.000"
    }
    ```

### Licensing & Identity
*   **`SIFT_CLIENT_ID`**: Defaults to `"Generic CLI"`. Identifies the host application.
*   **Dynamic Client Identification**: The `sift_hook.py` interceptor automatically detects the platform (e.g., `"Claude"`, `"Gemini"`, `"Cursor"`) and passes it as a `client_id_override` to the telemetry system, ensuring high-fidelity reporting even if the global environment variable is unset.
*   **`SIFT_LICENSE_KEY`**: If present, sets the `tier` payload attribute to `"Commercial"`. Otherwise, it defaults to `"Community"`. Testing/Diagnostic tools automatically override the tier to `"Internal-Testing"`.
*   **`.sift_identity`**: Generates and stores a persistent, anonymous `uuid.uuid4()` machine ID to prevent metric duplication across sessions without storing PII.

### The Privacy Kill-Switch
*   **Variable**: `SIFT_TELEMETRY_DISABLED=true` (Meechi Compliance).
*   **Effect**: 
    *   Instantly disables OpenTelemetry (`get_tracer` returns a basic pass-through).
    *   Disables Echo Detection (`check_echo` returns `False`).
    *   Forces Audit Headers to return empty (`""`).
    *   Blocks all local writing to `.sift_telemetry.json`.
    *   Blocks all network traffic to `SIFT_TELEMETRY_URL`.
    *   Forces `get_machine_id()` to return `"anonymous-user"`.