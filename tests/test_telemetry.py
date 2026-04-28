import pytest
import os
import json
import time
from unittest.mock import patch, MagicMock
import telemetry_core

def test_token_estimation():
    # 4 chars = 1 token heuristic
    assert telemetry_core.estimate_tokens("ABCD") == 1
    assert telemetry_core.estimate_tokens("ABCDEFGHIJKL") == 3
    assert telemetry_core.estimate_tokens("") == 0

@patch('urllib.request.urlopen')
def test_telemetry_pulse_honors_disabled_flag(mock_urlopen):
    # Setup: Disable telemetry
    with patch.dict(os.environ, {"SIFT_TELEMETRY_DISABLED": "true"}):
        telemetry_core.SIFT_TELEMETRY_DISABLED = True
        telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)
        mock_urlopen.assert_not_called()

@patch('urllib.request.urlopen')
def test_telemetry_pulse_sends_correct_payload(mock_urlopen):
    # Setup: Enable telemetry
    with patch.dict(os.environ, {"SIFT_TELEMETRY_DISABLED": "false"}):
        telemetry_core.SIFT_TELEMETRY_DISABLED = False
        telemetry_core.SIFT_TELEMETRY_URL = "https://example.com/api"
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)
        
        assert mock_urlopen.called
        args, kwargs = mock_urlopen.call_args
        request = args[0]
        payload = json.loads(request.data.decode())
        
        assert payload["tool_name"] == "sift_logs"
        assert payload["original_chars"] == 1000
        assert payload["tokens_saved"] == (1000 // 4) - (500 // 4)


def test_machine_identity_is_added_to_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("# test\n", encoding="utf-8")
    monkeypatch.setattr(telemetry_core, "SIFT_TELEMETRY_DISABLED", False)

    _ = telemetry_core.get_machine_id()

    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".sift_identity" in content


@patch("telemetry_core._send_telemetry_pulse_now")
def test_telemetry_rate_limit_queues_pending(mock_send, monkeypatch):
    monkeypatch.setattr(telemetry_core, "SIFT_TELEMETRY_DISABLED", False)
    monkeypatch.setattr(telemetry_core, "SIFT_TELEMETRY_URL", "https://example.com/api")
    monkeypatch.setenv("SIFT_PULSE_RATE_LIMIT_S", "60")

    telemetry_core._PULSE_LAST_SENT.clear()
    telemetry_core._PULSE_PENDING.clear()

    telemetry_core.send_telemetry_pulse("sift_logs", 1000, 500, 10.0)
    telemetry_core.send_telemetry_pulse("sift_logs", 900, 400, 8.0)

    time.sleep(0.1)
    assert mock_send.called
    assert any("sift_logs" in k for k in telemetry_core._PULSE_PENDING.keys())
