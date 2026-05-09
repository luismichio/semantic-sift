from semantic_sift.kernel import apply_heuristic_sieve


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
    from semantic_sift.telemetry import redact_secrets_for_telemetry

    # Test GitHub PAT — generic label for local logs
    assert (
        redact_secrets_for_telemetry("my key is github_pat_FAKEFAKE00000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        == "my key is [REDACTED]"
    )

    # Test OpenAI Key — generic label for local logs
    assert redact_secrets_for_telemetry("sk-abcdefghijklmnopqrstuvwxyz0123456789") == "[REDACTED]"

    # Test Password pattern
    assert redact_secrets_for_telemetry("password: my_secret_pass") == "password=[REDACTED]"
    assert redact_secrets_for_telemetry("token = some_token_123") == "token=[REDACTED]"

    # Test that normal text is untouched
    assert redact_secrets_for_telemetry("This is a normal sentence.") == "This is a normal sentence."


def test_telemetry_does_not_log_content_secrets(monkeypatch, tmp_path):
    from semantic_sift import telemetry as telemetry_core
    from semantic_sift import telemetry as _telemetry_impl
    import json
    import uuid

    # Enable telemetry opt-in and redirect file to a temp path to avoid cross-test pollution
    telemetry_file = str(tmp_path / "telemetry.json")
    monkeypatch.setattr(_telemetry_impl, "SIFT_TELEMETRY_DISABLED", False)
    monkeypatch.setattr(_telemetry_impl, "TELEMETRY_FILE", telemetry_file)

    # Use a unique session ID to avoid collisions with stale test data in the telemetry file
    session_id = f"test-pat-redaction-{uuid.uuid4().hex}"
    start_time = "now"
    pat = "github_pat_FAKEFAKE00000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    secret_tool = f"sift_chat:grep {pat}"

    telemetry_core.log_telemetry(session_id, start_time, secret_tool, 1000, 500, 10.0)

    with open(telemetry_file, "r") as f:
        data = json.load(f)

    assert session_id in data
    # Generic label — no secret-type hint
    redacted_tool = "sift_chat:grep [REDACTED]"
    assert redacted_tool in data[session_id]["tools"]

    # Scope raw-string checks to this session only, not the whole file
    session_json = json.dumps(data[session_id])
    assert pat not in session_json
    assert "GITHUB_PAT" not in session_json
