"""
Smoke tests for semantic_sift/hook_injector.py.

Coverage targets:
- build_runtime_hook_command()
- merge_hook_json()
- update_toml_config()
- discover_agent_configs()
- update_instruction_files() — one environment per major platform
"""

import json
import os
import sys


from semantic_sift.hook_injector import (
    build_runtime_hook_command,
    discover_agent_configs,
    merge_hook_json,
    update_instruction_files,
    update_toml_config,
)


# ---------------------------------------------------------------------------
# build_runtime_hook_command
# ---------------------------------------------------------------------------


def test_build_runtime_hook_command_returns_tuple():
    python_exe, hook_script, cmd_str = build_runtime_hook_command()
    assert isinstance(python_exe, str)
    assert isinstance(hook_script, str)
    assert isinstance(cmd_str, str)


def test_build_runtime_hook_command_exe_is_current_python():
    python_exe, _, _ = build_runtime_hook_command()
    assert os.path.isabs(python_exe)
    # Should resolve to the same interpreter we're running under
    assert os.path.normcase(python_exe) == os.path.normcase(os.path.abspath(sys.executable))


def test_build_runtime_hook_command_hook_script_exists():
    _, hook_script, _ = build_runtime_hook_command()
    assert os.path.isfile(hook_script), f"hook script not found: {hook_script}"


def test_build_runtime_hook_command_cmd_str_contains_both_parts():
    python_exe, hook_script, cmd_str = build_runtime_hook_command()
    assert python_exe in cmd_str
    assert hook_script in cmd_str


# ---------------------------------------------------------------------------
# merge_hook_json
# ---------------------------------------------------------------------------


def test_merge_hook_json_creates_file_when_missing(tmp_path):
    target = tmp_path / "hooks.json"
    _, _, cmd_str = build_runtime_hook_command()
    new_hook = {"command": cmd_str}

    result = merge_hook_json(str(target), "postToolUse", new_hook)

    assert result is True
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "hooks" in data
    assert any(h.get("command") == cmd_str for h in data["hooks"]["postToolUse"])


def test_merge_hook_json_idempotent(tmp_path):
    target = tmp_path / "hooks.json"
    _, _, cmd_str = build_runtime_hook_command()
    new_hook = {"command": cmd_str}

    merge_hook_json(str(target), "postToolUse", new_hook)
    result2 = merge_hook_json(str(target), "postToolUse", new_hook)

    # Second call: hook already present → returns False (no duplicate written)
    assert result2 is False
    data = json.loads(target.read_text(encoding="utf-8"))
    hooks = data["hooks"]["postToolUse"]
    matching = [h for h in hooks if h.get("command") == cmd_str]
    assert len(matching) == 1, "Hook must not be duplicated"


def test_merge_hook_json_appends_to_existing_file(tmp_path):
    target = tmp_path / "hooks.json"
    existing = {"hooks": {"postToolUse": [{"command": "other-tool"}]}}
    target.write_text(json.dumps(existing), encoding="utf-8")

    _, _, cmd_str = build_runtime_hook_command()
    merge_hook_json(str(target), "postToolUse", {"command": cmd_str})

    data = json.loads(target.read_text(encoding="utf-8"))
    commands = [h.get("command") for h in data["hooks"]["postToolUse"]]
    assert "other-tool" in commands
    assert cmd_str in commands


# ---------------------------------------------------------------------------
# update_toml_config
# ---------------------------------------------------------------------------


def test_update_toml_config_injects_block_when_missing(tmp_path):
    cfg = tmp_path / "mcp.toml"
    cfg.write_text("[mcp]\nenabled = true\n", encoding="utf-8")

    result = update_toml_config(str(cfg), "TEST_SECTION", "# test content")

    assert result is True
    content = cfg.read_text(encoding="utf-8")
    assert "SIFT_SECTION_START:TEST_SECTION" in content
    assert "# test content" in content


def test_update_toml_config_replaces_existing_block(tmp_path):
    # update_toml_config uses "# SIFT_SECTION_START/END" markers (not HTML comments)
    block_id = "# SIFT_SECTION_START:S1"
    block_end = "# SIFT_SECTION_END:S1"
    cfg = tmp_path / "mcp.toml"
    cfg.write_text(
        f"{block_id}\n# ---\n# old content\n{block_end}",
        encoding="utf-8",
    )

    update_toml_config(str(cfg), "S1", "new content")

    content = cfg.read_text(encoding="utf-8")
    assert "old content" not in content
    assert "new content" in content


def test_update_toml_config_idempotent_on_re_run(tmp_path):
    cfg = tmp_path / "mcp.toml"
    cfg.write_text("", encoding="utf-8")

    update_toml_config(str(cfg), "SEC", "payload")
    update_toml_config(str(cfg), "SEC", "payload")

    content = cfg.read_text(encoding="utf-8")
    assert content.count("SIFT_SECTION_START:SEC") == 1


# ---------------------------------------------------------------------------
# discover_agent_configs
# ---------------------------------------------------------------------------


def test_discover_agent_configs_finds_agents_md(tmp_path):
    # discover_agent_configs only picks up AGENTS.md in subdirectories (not root)
    sub = tmp_path / "subproject"
    sub.mkdir()
    agents_md = sub / "AGENTS.md"
    agents_md.write_text("# Agents", encoding="utf-8")

    found = discover_agent_configs(str(tmp_path))

    assert str(agents_md) in found


def test_discover_agent_configs_finds_cursor_rules(tmp_path):
    # discover_agent_configs scans .cursor/agents/ for .toml/.md files
    cursor_dir = tmp_path / ".cursor" / "agents"
    cursor_dir.mkdir(parents=True)
    rule_file = cursor_dir / "sift.toml"
    rule_file.write_text("rule content", encoding="utf-8")

    found = discover_agent_configs(str(tmp_path))

    # Normalise separators for cross-platform comparison
    found_normalised = [os.path.normpath(p) for p in found]
    assert os.path.normpath(str(rule_file)) in found_normalised


def test_discover_agent_configs_returns_empty_for_empty_dir(tmp_path):
    found = discover_agent_configs(str(tmp_path))
    assert found == []


# ---------------------------------------------------------------------------
# update_instruction_files — platform smoke tests
# ---------------------------------------------------------------------------


def _run_onboard(env: str, tmp_path) -> list[str]:
    """Run update_instruction_files for *env* in an isolated tmp directory."""
    python_exe, hook_script, cmd_str = build_runtime_hook_command()
    return update_instruction_files(
        section_id="SOP",
        header="# Sift SOP",
        content="MANDATORY LOCAL I/O: use sift_read_file.",
        instruction_targets=[],
        runtime_python_exe=python_exe,
        runtime_hook_script=hook_script,
        runtime_hook_command=cmd_str,
        target_dir=str(tmp_path),
        environment=env,
    )


def test_onboard_cursor_creates_hooks_json(tmp_path):
    actions = _run_onboard("cursor", tmp_path)
    hooks_path = tmp_path / ".cursor" / "hooks.json"
    assert hooks_path.exists(), f"Expected hooks.json; actions={actions}"
    assert any("Cursor" in a for a in actions)


def test_onboard_vscode_creates_hooks_json(tmp_path):
    # VS Code / GitHub path: .github/hooks/semantic-sift.json
    actions = _run_onboard("vscode", tmp_path)
    vscode_path = tmp_path / ".github" / "hooks" / "semantic-sift.json"
    assert vscode_path.exists(), f"Expected .github/hooks/semantic-sift.json; actions={actions}"
    assert any("VS Code" in a or "vscode" in a.lower() for a in actions)


def test_onboard_opencode_creates_plugin_file(tmp_path):
    # OpenCode plugin path: .opencode/plugins/semantic-sift.ts
    actions = _run_onboard("opencode", tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "semantic-sift.ts"
    assert plugin_path.exists(), f"Expected .opencode/plugins/semantic-sift.ts; actions={actions}"
    assert any("OpenCode" in a or "plugin" in a.lower() for a in actions)


def test_onboard_unknown_environment_does_not_crash(tmp_path):
    actions = _run_onboard("unknown_ide_xyz", tmp_path)
    assert isinstance(actions, list)


def test_onboard_actions_are_all_strings(tmp_path):
    actions = _run_onboard("cursor", tmp_path)
    for a in actions:
        assert isinstance(a, str), f"Non-string action: {a!r}"
