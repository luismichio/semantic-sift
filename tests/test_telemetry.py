import pytest
import os
import json
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
