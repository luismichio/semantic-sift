from semantic_sift import onboarding


def test_update_gitignore_adds_entries(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("# base\n", encoding="utf-8")

    result = onboarding.update_gitignore(str(tmp_path))
    content = gitignore.read_text(encoding="utf-8")

    assert ".sift_telemetry.json" in content
    assert ".sift_cache/" in content
    assert ".sift_telemetry.json" in content
    assert ".sift_cache/" in content
    assert "Added artifacts" in result or "Already properly ignored." in result


def test_apply_onboarding_dry_run_returns_plan(tmp_path):
    actions = onboarding.apply_onboarding(
        environment="Cursor",
        target_dir=str(tmp_path),
        dry_run=True,
        runtime_python_exe="python",
        runtime_hook_script="sift_hook.py",
        runtime_hook_command='"python" "sift_hook.py"',
    )

    joined = "\n".join(actions)
    assert "dry-run" in joined.lower()
    assert "Planned action" in joined


def test_build_telemetry_disclosure_opted_out(monkeypatch):
    monkeypatch.delenv("SIFT_TELEMETRY_OPTED_IN", raising=False)
    msg = onboarding._build_telemetry_disclosure()
    assert "DISABLED" in msg
    assert "opt-in" in msg
    assert "SIFT_TELEMETRY_OPTED_IN" in msg


def test_build_telemetry_disclosure_opted_in(monkeypatch):
    monkeypatch.setenv("SIFT_TELEMETRY_OPTED_IN", "true")
    msg = onboarding._build_telemetry_disclosure()
    assert "ENABLED" in msg
    assert "opt out" in msg


def test_apply_onboarding_includes_telemetry_disclosure(tmp_path):
    actions = onboarding.apply_onboarding(
        environment="Cursor",
        target_dir=str(tmp_path),
        dry_run=True,
        runtime_python_exe="python",
        runtime_hook_script="sift_hook.py",
        runtime_hook_command='"python" "sift_hook.py"',
    )
    # Disclosure must be the first line
    assert "Telemetry:" in actions[0]
    assert "SIFT_TELEMETRY_OPTED_IN" in actions[0]

