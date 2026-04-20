import pytest
from server import apply_heuristic_sieve

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
