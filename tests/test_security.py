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

    # Test GitHub PAT — descriptive label for local logs
    assert redact_secrets("my key is github_pat_FAKEFAKE00000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA") == "my key is [REDACTED_GITHUB_PAT]"

    # Test OpenAI Key — descriptive label for local logs
    assert redact_secrets("sk-abcdefghijklmnopqrstuvwxyz0123456789") == "[REDACTED_OPENAI_KEY]"

    # Test Password pattern
    assert redact_secrets("password: my_secret_pass") == "password=[REDACTED]"
    assert redact_secrets("token = some_token_123") == "token=[REDACTED]"

    # Test that normal text is untouched
    assert redact_secrets("This is a normal sentence.") == "This is a normal sentence."


def test_secret_redaction_for_telemetry_generic_label():
    from telemetry_core import redact_secrets_for_telemetry

    pat = "github_pat_FAKEFAKE00000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    result = redact_secrets_for_telemetry(f"sift_chat:grep {pat}")
    assert result == "sift_chat:grep [REDACTED]"
    assert "GITHUB" not in result
    assert "PAT" not in result

    # OpenAI key — generic label
    assert redact_secrets_for_telemetry("sk-abcdefghijklmnopqrstuvwxyz0123456789") == "[REDACTED]"

    # Password pattern — key name kept, value masked
    assert redact_secrets_for_telemetry("password: my_secret_pass") == "password=[REDACTED]"

    # Normal text untouched
    assert redact_secrets_for_telemetry("sift_chat:read_file") == "sift_chat:read_file"

def test_telemetry_does_not_log_content_secrets():
    import telemetry_core
    import json
    import uuid

    # Use a unique session ID to avoid collisions with stale test data in the telemetry file
    session_id = f"test-pat-redaction-{uuid.uuid4().hex}"
    start_time = "now"
    pat = "github_pat_FAKEFAKE00000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    secret_tool = f"sift_chat:grep {pat}"

    telemetry_core.log_telemetry(session_id, start_time, secret_tool, 1000, 500, 10.0)

    with open(telemetry_core.TELEMETRY_FILE, "r") as f:
        data = json.load(f)

    assert session_id in data
    # Generic label — no secret-type hint
    redacted_tool = "sift_chat:grep [REDACTED]"
    assert redacted_tool in data[session_id]["tools"]

    # Scope raw-string checks to this session only, not the whole file
    session_json = json.dumps(data[session_id])
    assert pat not in session_json
    assert "GITHUB_PAT" not in session_json

