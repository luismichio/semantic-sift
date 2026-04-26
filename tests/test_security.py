import pytest
from sift_kernel import apply_heuristic_sieve

def test_sieve_does_not_mangle_api_keys():
    # Heuristics should remove the noise around a key, but leave the key itself untouched.
    # We use a pattern that looks like a secret but isn't real.
    secret = "sk-ant-api03-abcdef1234567890-GHIJKLMN"
    noisy = f"2026-04-19T22:00:00Z INFO: Setting key {secret}\n[50/100] Progress..."
    
    result = apply_heuristic_sieve(noisy)
    
    assert secret in result
    assert "INFO: Setting key" in result
    assert "Progress" not in result

def test_sieve_handles_empty_input():
    assert apply_heuristic_sieve("") == ""

def test_sieve_handles_single_line_no_noise():
    assert apply_heuristic_sieve("Hello World") == "Hello World"

def test_sieve_removes_multiple_timestamps_per_line():
    noisy = "2026-04-19T22:00:00Z Starting 2026-04-19T22:00:01Z"
    # Logic should strip the first one and potentially the second if it matches the pattern
    result = apply_heuristic_sieve(noisy)
    assert "Starting" in result
    assert "2026-04-19" not in result

def test_secret_redaction_logic():
    from telemetry_core import redact_secrets
    
    # Test GitHub PAT
    assert redact_secrets("my key is ***REDACTED***") == "my key is [REDACTED_GITHUB_PAT]"
    
    # Test OpenAI Key
    assert redact_secrets("sk-abcdefghijklmnopqrstuvwxyz0123456789") == "[REDACTED_OPENAI_KEY]"
    
    # Test Password pattern
    assert redact_secrets("password: my_secret_pass") == "password=[REDACTED]"
    assert redact_secrets("token = some_token_123") == "token=[REDACTED]"
    
    # Test that normal text is untouched
    assert redact_secrets("This is a normal sentence.") == "This is a normal sentence."

def test_telemetry_does_not_log_content_secrets():
    import telemetry_core
    import os
    import json
    
    # We want to ensure that log_telemetry only logs counts, not content
    # and that tool_name is redacted if it accidentally contains a secret
    session_id = "test-session"
    start_time = "now"
    pat = "***REDACTED***"
    secret_tool = f"sift_chat:grep {pat}"
    
    # Ensure any previous data for this session is cleared or use a unique session
    telemetry_core.log_telemetry(session_id, start_time, secret_tool, 1000, 500, 10.0)
    
    with open(telemetry_core.TELEMETRY_FILE, "r") as f:
        data = json.load(f)
        
    # Check if the secret tool name was logged and if it was REDACTED
    assert session_id in data
    # The tool name should have been redacted
    redacted_tool = "sift_chat:grep [REDACTED_GITHUB_PAT]"
    assert redacted_tool in data[session_id]["tools"]
    # Ensure the raw PAT is NOT in the file at all
    with open(telemetry_core.TELEMETRY_FILE, "r") as f:
        raw_log = f.read()
    assert pat not in raw_log

