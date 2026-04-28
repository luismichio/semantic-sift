from semantic_sift import onboarding


def test_update_gitignore_adds_entries(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("# base\n", encoding="utf-8")

    result = onboarding.update_gitignore(str(tmp_path))
    content = gitignore.read_text(encoding="utf-8")

    assert ".sift_identity" in content
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
