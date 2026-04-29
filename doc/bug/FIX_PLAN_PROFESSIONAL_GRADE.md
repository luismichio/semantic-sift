# Fix Plan: Semantic-Sift → Professional Grade

**Date**: 2026-04-29
**Closed**: 2026-04-29
**Status**: ✅ All 11 fixes completed — CI green on Python 3.10 / 3.11 / 3.13

> This document is closed. See `doc/CHANGELOG.md` for the `[0.2.0]` release entry.

---

## Phase 0 — Legal & Governance (Do First)

These must be resolved before any external code contribution is accepted.

---

### FIX-A01 · Create `CONTRIBUTING.md` with CLA notice `[LEGAL-01, DOC-02]`

**Problem**: No `CONTRIBUTING.md` exists. Under the Source-Available Dual License, any merged PR creates a copyright ambiguity that puts the commercial license at legal risk. GitHub also shows no contribution guidance without this file.

**Fix**:
- Create `CONTRIBUTING.md` at the repo root.
- Include a plain-language CLA statement: contributors agree their code may be included in free and commercial tiers, they retain copyright, and they will be credited.
- Include: dev environment setup (`pip install .[dev]`), how to run tests (`pytest`), how to run type checks (`mypy`), how to run the linter (`ruff check .`), how to add a new platform (reference `BACKLOG.md` Registry Pattern item), commit message convention.
- Reference `LICENSE.md` explicitly so contributors cannot claim ignorance of the commercial model.

**Files**: `CONTRIBUTING.md` (new)
**Effort**: 1 hour

---

### FIX-A02 · Verify `SECURITY.md` is GitHub-discoverable `[LEGAL-02]`

**Problem**: GitHub only surfaces `SECURITY.md` as the repo's official security policy if it is at the root, in `docs/`, or in `.github/`. Current location needs verification.

**Fix**:
- Confirm `SECURITY.md` is at the repo root. If it is in `doc/`, move it or add a symlink.
- Verify GitHub shows the "Security Policy" tab on the repo's Security page after the move.

**Files**: `SECURITY.md`
**Effort**: 15 minutes

---

## Phase 1 — CI/CD Infrastructure (Foundation for Everything Else)

No badge, no release workflow, and no coverage enforcement is possible without this phase.

---

### FIX-B01 · GitHub Actions CI pipeline `[CI-01]`

**Problem**: No `.github/workflows/` directory. Tests, mypy, and ruff are only run manually. A 6-error mypy regression went undetected until manual audit.

**Fix**:
Create `.github/workflows/ci.yml` that triggers on every push and pull request to `main`:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install .[dev]
      - run: python -m pytest --tb=short -q --cov=semantic_sift --cov=sift_kernel --cov=telemetry_core --cov-report=term-missing
      - run: python -m mypy semantic_sift/ telemetry_core.py sift_kernel.py server.py sift_hook.py
      - run: python -m ruff check .
```

**Files**: `.github/workflows/ci.yml` (new)
**Effort**: 1 hour

---

### FIX-B02 · Add `pytest-cov` and `ruff` to dev dependencies `[COV-02, LINT-01]`

**Problem**: Both tools are used in the project but not listed in `pyproject.toml` dev extras. A fresh `pip install .[dev]` does not install them.

**Fix**:
Add to `[project.optional-dependencies]` `dev` section in `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",   # add
    "ruff",         # add
    "mypy",
    ...
]
```

Also add `[tool.ruff]` configuration section to `pyproject.toml`:
```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501"]  # line length handled separately
```

And add `[tool.coverage.run]` section:
```toml
[tool.coverage.run]
source = ["semantic_sift", "sift_kernel", "telemetry_core", "sift_hook"]
omit = ["tests/*", "benchmark_sift.py"]
```

**Files**: `pyproject.toml`
**Effort**: 30 minutes

---

### FIX-B03 · Automated release workflow `[CI-02]`

**Problem**: No release workflow. The PyPI backlog item cannot be safely implemented without an automated, gated release process.

**Fix**:
Create `.github/workflows/release.yml` that triggers on version tag push (`v*`):
- Runs full CI (test + mypy + ruff) as a gate
- Builds the package with `python -m build`
- Publishes to PyPI using `pypa/gh-action-pypi-publish`
- Creates a GitHub Release with the relevant `CHANGELOG.md` section as the release notes

**Files**: `.github/workflows/release.yml` (new)
**Effort**: 1 hour

---

## Phase 2 — Code Quality (Linting & Formatting)

Fast, low-risk, high-signal fixes. Makes the codebase look and behave professionally.

---

### FIX-C01 · Fix all 22 ruff violations `[LINT-01]`

**Problem**: 22 ruff violations across production code and tests. 10 are auto-fixable. `E741` (ambiguous `l` variable) is a real readability hazard.

**Fix**:
1. Run `ruff check . --fix` to auto-resolve the 10 fixable violations (unused imports, f-string prefix).
2. Manually fix the remaining 12:
   - `E701` (8 instances): expand `if x: return` to two lines in `sift_hook.py`, `sift_kernel.py`, `telemetry_core.py`
   - `E741` (1 instance): rename `l` → `latency_ms` in `semantic_sift/tools.py:172`
   - `F541` (1 instance): remove `f` prefix from plain string in `benchmark_sift.py:142`
3. Verify `python -m ruff check .` reports 0 violations.

**Files**: `sift_hook.py`, `sift_kernel.py`, `telemetry_core.py`, `semantic_sift/tools.py`, `benchmark_sift.py`, `tests/`
**Effort**: 1 hour

---

## Phase 3 — Test Coverage (Core Feature Safety Net)

Ordered by risk: the hook is the most critical untested component.

---

### FIX-D01 · Hook integration test — pipe payload through `main()` `[COV-01]`

**Problem**: `sift_hook.py` is at 13% coverage. The entire routing + injection pipeline has no automated proof it works end-to-end.

**Fix**:
Add `tests/test_hook_integration.py`. For each major platform, construct a realistic JSON payload, pipe it through `sift_hook.main()` via `subprocess` or by patching `sys.stdin`/`sys.stdout`, and assert:
- The correct platform is detected (check telemetry log or log output)
- `raw_content` is extracted from the correct key
- Sifted output is injected back into the correct key
- The output is valid JSON

Minimum platform coverage required: Claude, Gemini, OpenCode (AfterTool), OpenCode (Compacting), Cursor, VSCode, Qwen.

**Files**: `tests/test_hook_integration.py` (new)
**Effort**: 3 hours

---

### FIX-D02 · `tools.py` MCP tool tests `[COV-01]`

**Problem**: `semantic_sift/tools.py` is at 43% coverage. The MCP tool implementations — the public API of the server — are only partially tested.

**Fix**:
Expand `tests/test_server_tools.py` to cover:
- `sift_logs`: verify heuristic sieve is applied and result is shorter than input
- `sift_chat`: mock `sift_kernel.perform_semantic_sift`, verify result and telemetry call
- `sift_doc`: same pattern as `sift_chat`
- `sift_extraction`: verify extraction cleaning is applied
- `sift_rank`: verify top-N results returned
- `get_sift_stats(scope="all")`: verify markdown table format when telemetry data exists
- `sift_onboard` with `environment=None`: verify auto-detection fallback (links to backlog item `sift_onboard` Environment Auto-Detection)

**Files**: `tests/test_server_tools.py`
**Effort**: 2 hours

---

### FIX-D03 · `hook_injector.py` smoke tests `[COV-01]`

**Problem**: `semantic_sift/hook_injector.py` is at 7% coverage. All IDE injection logic is untested.

**Fix**:
Add `tests/test_hook_injector.py` with `tmp_path`-based filesystem tests:
- `build_runtime_hook_command()` returns a command containing `sys.executable` and an existing `sift_hook.py` path
- Claude injection: creates `.claude/hooks/` with correct JSON structure
- OpenCode injection: creates `.opencode/plugins/semantic-sift.ts` with correct content
- `dry_run=True` returns planned actions without writing any files (already partially tested in `test_onboarding.py` — expand scope)

**Files**: `tests/test_hook_injector.py` (new)
**Effort**: 2 hours

---

## Phase 4 — Documentation & Badges

Depends on Phase 1 (CI must exist before a CI badge can be added).

---

### FIX-E01 · Add badge row to `README.md` `[DOC-01]`

**Problem**: No visual proof of project health. Badges are the first signal an evaluator reads.

**Fix**:
Add immediately below the project title in `README.md`:
```markdown
![CI](https://github.com/luiskobayashi/semantic-sift/workflows/CI/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-TBD-brightgreen)
![License](https://img.shields.io/badge/license-Source--Available-blue)
![PyPI](https://img.shields.io/pypi/v/semantic-sift)
```
Update coverage badge to use `codecov.io` or `shields.io` dynamic badge once CI uploads coverage reports.

**Files**: `README.md`
**Effort**: 30 minutes

---

## Phase 5 — Versioning (Prerequisite for PyPI)

---

### FIX-F01 · Cut first versioned release `[CI-02]`

**Problem**: `CHANGELOG.md` has only an `[Unreleased]` section. No git tag has been created. The project has no public version identity.

**Fix**:
1. Move all `[Unreleased]` CHANGELOG content to a new `## [0.2.0] - 2026-04-29` section (0.1.0 is considered the pre-audit baseline).
2. Update `version = "0.2.0"` in `pyproject.toml`.
3. Create and push git tag: `git tag v0.2.0 && git push origin v0.2.0`.
4. The release workflow from FIX-B03 will then publish to PyPI automatically.

**Files**: `doc/CHANGELOG.md`, `pyproject.toml`
**Effort**: 30 minutes (after Phase 1 CI is green)

---

## Summary

| Phase | Fix ID | Finding | Effort | Depends On |
|---|---|---|---|---|
| 0 | FIX-A01 | LEGAL-01, DOC-02 | 1h | — |
| 0 | FIX-A02 | LEGAL-02 | 15min | — |
| 1 | FIX-B01 | CI-01 | 1h | FIX-C01 (violations must be clean first) |
| 1 | FIX-B02 | COV-02, LINT-01 | 30min | — |
| 1 | FIX-B03 | CI-02 | 1h | FIX-B01 |
| 2 | FIX-C01 | LINT-01 | 1h | — |
| 3 | FIX-D01 | COV-01 | 3h | — |
| 3 | FIX-D02 | COV-01 | 2h | — |
| 3 | FIX-D03 | COV-01 | 2h | — |
| 4 | FIX-E01 | DOC-01 | 30min | FIX-B01 |
| 5 | FIX-F01 | CI-02 | 30min | FIX-B01, FIX-B03 |

**Total estimated effort: ~13 hours**
**Recommended execution order**: A01 → A02 → B02 → C01 → B01 → D01 → D02 → D03 → B03 → E01 → F01
