import sys

from semantic_sift import server


def test_windsurf_gateway_command_windows():
    original_platform = sys.platform
    try:
        sys.platform = "win32"
        cmd = server._get_windsurf_gateway_command()
        assert "pwsh -NoProfile -Command" in cmd
        assert "Get-Item" in cmd
        assert "WINDSURF_TOOL_ARGS" in cmd
    finally:
        sys.platform = original_platform


def test_windsurf_gateway_command_posix():
    original_platform = sys.platform
    try:
        sys.platform = "linux"
        cmd = server._get_windsurf_gateway_command()
        assert "stat -c %s" in cmd or "stat -f %z" in cmd
        assert "WINDSURF_TOOL_ARGS" in cmd
    finally:
        sys.platform = original_platform
