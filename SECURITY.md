# Security Policy: Semantic-Sift

Semantic-Sift is designed as a local-first MCP sidecar. This policy documents how security, privacy, and telemetry are handled in practice.

## Security Controls

- **Automated audits**: The project runs logic tests (`pytest`), static analysis (`bandit`), and dependency scanning (`pip-audit`).
- **Secret redaction**: Telemetry metadata is sanitized before persistence/transmission by `redact_secrets_for_telemetry(...)` in `telemetry_core.py`.
- **Path safety**: Local file tools enforce workspace-bound reads via `resolve_safe_path(...)` in `sift_kernel.py` unless explicitly overridden.
- **Double-sift prevention**: Native signature bypass (`--- [Semantic-Sift: Native Execution] ---`) prevents recursive hook processing.

---

## Telemetry Model

### Consent Policy (Opt-In, as of v0.3.2)

Telemetry is **opt-in** by default. No usage data is collected unless you explicitly enable it.

To enable anonymous telemetry:

```bash
export SIFT_TELEMETRY_OPTED_IN=true
```

To disable telemetry (legacy kill-switch, still supported):

```bash
export SIFT_TELEMETRY_DISABLED=true
```

### Data Collected (when opted in)

Telemetry is metadata-only. Raw tool content, prompt content, and source code payloads are never transmitted.

| Field | Example | Notes |
|---|---|---|
| `client_id` | `"Cursor"` | IDE/CLI detection, never contains username |
| `tool_name` | `"grep_search"` | MCP tool name only — **never file contents** |
| `original_chars` | `4200` | Size metrics only |
| `final_chars` | `2100` | Size metrics only |
| `latency_ms` | `44.2` | Performance only |
| `tier` | `"Real-World"` | Context classification |
| `timestamp` | `"2026-01-01T00:00:00+01:00"` | Timezone-aware ISO-8601 |

### Data NOT Collected

- Full file contents, prompt text, or raw LLM context windows
- File paths, workspace names, or binary document payloads
- User names, machine names, or hostnames
- API keys or credentials (actively redacted via `redact_secrets_for_telemetry()`)

### Endpoint

- Default: `https://www.luiskobayashi.com/api/sift`
- Override: `SIFT_TELEMETRY_URL=https://your-org.example.com/api/sift`

The HTTP client enforces a **2-second hard timeout** covering DNS resolution, connection, and read. Any failure is silently swallowed and never blocks the main flow.

### GDPR / CCPA Compliance

- All telemetry is anonymous by design — no PII is collected.
- No persistent machine identity (`machine_id`) is stored or transmitted.
- Opting out is the **default**; no action required.

---

## Path Safety — `SIFT_ALLOW_GLOBAL_READS`

By default, Semantic-Sift enforces **workspace-bound file access**. Files outside the detected workspace root are denied.

Setting `SIFT_ALLOW_GLOBAL_READS=true` **bypasses all path safety checks**. When this flag is active:

- A warning is emitted to `stderr` via the `semantic_sift.security` logger for every access.
- The warning includes the full resolved path.
- The data stream (`stdout`) is not affected.

> **Recommendation**: Do not set this flag in shared, multi-user, or CI environments.

---

## Input Size Limits

To protect against memory exhaustion in the MCP server process, Semantic-Sift enforces an input size cap:

| Variable | Default | Effect |
|---|---|---|
| `SIFT_MAX_INPUT_MB` | `50` | Maximum input size in megabytes |

On breach, the input is **truncated** (not rejected) and a truncation notice is prepended to the output. A warning is emitted to `stderr` via the `semantic_sift.input_guard` logger.

---

## Privacy Configuration

Recommended privacy-first environment:

```bash
SIFT_TELEMETRY_DISABLED=true
```

Optional self-hosted telemetry route:

```bash
SIFT_TELEMETRY_URL=https://your-org.example.com/api/sift
```

---

## Local Artifacts

Sensitive local operational artifacts should remain ignored by git:

- `.sift_telemetry.json`
- `.sift_cache/`
- `.pipe_cache/`

---

## Vulnerability Reporting

If you discover a vulnerability or secret exposure risk, report privately:

- Security lead: Luis Kobayashi
- Contact: https://www.luiskobayashi.com/contact
- Target response: acknowledge within 48h, critical patch target within 7 days
