# 🐛 Bug Report: Google Antigravity Telemetry Misattribution

**Report Date**: April 30, 2026  
**Status**: RESOLVED  
**Vulnerability Class**: Telemetry & Analytics

---

## 1. Description of the Failure
Supabase telemetry dashboards are incorrectly reporting the `client_id` for "Google Antigravity" environments as "VS Code". This results in inaccurate platform usage distribution metrics and completely masks the true adoption rate and ROI of the Antigravity agent.

---

## 2. Technical Root Cause
Google Antigravity is built on top of the VS Code framework (or utilizes its extension host). As a result, its background processes inherently set standard VS Code environment variables, such as `VSCODE_PID`, `VSCODE_IPC_HOOK`, and `VSCODE_CWD`.

In `telemetry_core.py`, the `detect_client_id()` function iterates through a prioritized list (`_ENV_MAP`) to sniff the host IDE. Because there is currently no explicit check for Google Antigravity, the detection logic falls through until it reaches the `VSCODE_PID` check. It matches the inherited VS Code variables and halts, incorrectly assigning the `"VS Code"` label to the session.

---

## 3. Proposed Solution
We must add a specific detection rule for Google Antigravity that intercepts the platform identification *before* it triggers the generic VS Code fallbacks.

A dump of the local environment reveals that Antigravity uniquely exposes several variables:
- `ANTIGRAVITY_AGENT=1`
- `ANTIGRAVITY_EDITOR_APP_ROOT=...`
- `ANTIGRAVITY_TRAJECTORY_ID=...`

**Code Fix:**
Update the `_ENV_MAP` list in `telemetry_core.py` to check for `ANTIGRAVITY_AGENT` prior to the VS Code checks:

```python
    _ENV_MAP: list[tuple[str, str]] = [
        # Google Antigravity (must precede VS Code due to inherited VSCODE_PID)
        ("ANTIGRAVITY_AGENT", "Google Antigravity"),
        
        # OpenCode
        ("OPENCODE", "OpenCode"),
        ("OPENCODE_PID", "OpenCode"),
        
        # VS Code
        ("VSCODE_PID", "VS Code"),
        # ...
    ]
```
