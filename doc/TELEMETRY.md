# Telemetry Specification

This document defines the telemetry behavior for Semantic-Sift.

## Endpoint

- Default: `https://www.luiskobayashi.com/api/sift`
- Override with: `SIFT_TELEMETRY_URL`
- Disable completely: `SIFT_TELEMETRY_DISABLED=true`

## Payload Schema

Telemetry pulses use JSON with the following fields:

- `machine_id` (string): local anonymous ID from `.sift_identity`
- `client_id` (string): client label (`SIFT_CLIENT_ID` or runtime override)
- `tier` (string): `Community`, `Commercial`, or explicit override
- `agent_label` (string|null): optional subagent label
- `tool_name` (string): redacted tool identifier
- `file_ext` (string|null): optional file type hint
- `original_chars` (int): input size in characters
- `final_chars` (int): output size in characters
- `original_tokens` (int): estimated tokens (4 chars/token)
- `final_tokens` (int): estimated tokens (4 chars/token)
- `tokens_saved` (int): `original_tokens - final_tokens`
- `latency_ms` (float): processing latency
- `timestamp` (ISO-8601 string): event time

## Retention and Deletion

- Local telemetry registry: `.sift_telemetry.json` in the workspace.
- Contact for telemetry policy/deletion requests: https://www.luiskobayashi.com/contact

## Privacy Guarantees

- Raw file/document text is not sent in telemetry pulses.
- Prompt content is not sent in telemetry pulses.
- Secret-like values in metadata are redacted before dispatch.

## Operational Notes

- Pulse dispatch is asynchronous.
- Rate limiting is controlled by `SIFT_PULSE_RATE_LIMIT_S` (default: `10`).
