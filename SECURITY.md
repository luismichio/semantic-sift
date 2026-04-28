# Security Policy: Semantic-Sift

Semantic-Sift is designed as a local-first MCP sidecar. This policy documents how security, privacy, and telemetry are handled in practice.

## Security Controls

- **Automated audits**: The project runs logic tests (`pytest`), static analysis (`bandit`), and dependency scanning (`pip-audit`).
- **Secret redaction**: Telemetry metadata is sanitized before persistence/transmission by `redact_secrets(...)` in `telemetry_core.py`.
- **Path safety**: Local file tools enforce workspace-bound reads via `resolve_safe_path(...)` in `sift_kernel.py` unless explicitly overridden.
- **Double-sift prevention**: Native signature bypass (`--- [Semantic-Sift: Native Execution] ---`) prevents recursive hook processing.

## Telemetry Model

Semantic-Sift telemetry is metadata-only. Raw tool content, prompt content, and source code payloads are not transmitted by telemetry pulses.

### Data Collected

- Anonymous machine ID (`machine_id`)
- Client ID/tier labels (`client_id`, `tier`)
- Tool metadata (`tool_name`, `agent_label`, `file_ext`)
- Size/performance metrics (`original_chars`, `final_chars`, `saved_chars`, `latency_ms`)
- Timestamp

### Data Not Collected

- Full file contents
- Prompt text
- Raw LLM context windows
- Binary document payloads

### Endpoint

- Default telemetry endpoint: `https://www.luiskobayashi.com/api/sift`
- Override endpoint with `SIFT_TELEMETRY_URL`
- Disable all telemetry with `SIFT_TELEMETRY_DISABLED=true`

## Privacy Configuration

Recommended privacy-first environment:

```bash
SIFT_TELEMETRY_DISABLED=true
```

Optional self-hosted telemetry route:

```bash
SIFT_TELEMETRY_URL=https://your-org.example.com/api/sift
```

## Local Artifacts

Sensitive local operational artifacts should remain ignored by git:

- `.sift_telemetry.json`
- `.sift_identity`
- `.sift_cache/`

## Vulnerability Reporting

If you discover a vulnerability or secret exposure risk, report privately:

- Security lead: Luis Kobayashi
- Contact: https://www.luiskobayashi.com/contact
- Target response: acknowledge within 48h, critical patch target within 7 days
