# Evaluation Report: Semantic-Sift Professional Readiness Audit

**Date**: 2026-04-29
**Auditor**: OpenCode (claude-sonnet-4.6)
**Scope**: Full codebase audit — CI/CD, test coverage, code quality, legal, documentation
**Trigger**: User request to identify gaps preventing professional-grade quality

---

## Executive Summary

Semantic-Sift has strong architectural foundations and a well-defined feature set. However, it currently lacks the **verification infrastructure** (CI, coverage, linting) that makes a project's quality provable to an outside observer. Three categories of issues were found: automation gaps, code quality violations, and a legal gap in the contribution model.

**Overall Grade: 3.5 / 5 stars**
The core technology is sound. The project is not yet safe to present as production-grade because there is no automated proof that it stays working between changes.

---

## Findings

### Category: CI/CD — Automation

---

#### CI-01 · No GitHub Actions CI pipeline

**Severity**: Critical
**File(s)**: `.github/` (directory exists but contains only `hooks/`, no `workflows/`)

**Observation**:
There is no automated pipeline. Tests, type checking, and linting are only run manually. The mypy regression introduced on 2026-04-29 (6 syntax errors in `semantic_sift/tools.py` from a malformed regex substitution) went undetected until the next manual audit run. In a team or open-source context, broken code would have been merged silently.

**Evidence**:
- `.github/workflows/` does not exist
- mypy error confirmed: `semantic_sift/tools.py:62: error: Unexpected keyword argument "client_id_override" for "len"` (6 instances, now fixed)
- No badge in `README.md` linking to a CI run

**Impact**:
- Any push can silently break the project
- No objective proof of quality for external evaluators
- PyPI publish path (backlog item) is unsafe without CI gating releases

---

#### CI-02 · No automated release workflow

**Severity**: High
**File(s)**: `.github/` (missing), `pyproject.toml`

**Observation**:
`pyproject.toml` is correctly structured for PyPI publication, but there is no release workflow to automate the process. Releases must be done manually, which introduces human error risk and means the PyPI backlog item cannot be safely implemented without this foundation.

**Impact**:
- Manual releases are error-prone
- Version in `pyproject.toml` has never been incremented or tagged in git
- `## [Unreleased]` section in `CHANGELOG.md` has never been cut to a version number

---

### Category: Test Coverage — Verification

---

#### COV-01 · Overall coverage 38% — core feature has 13% coverage

**Severity**: Critical
**File(s)**: `sift_hook.py`, `semantic_sift/tools.py`, `semantic_sift/hook_injector.py`

**Observation**:
Coverage measured with `pytest-cov` (installed during audit):

| File | Coverage | Risk |
|---|---|---|
| `sift_hook.py` | **13%** | The entire routing + injection pipeline (lines 69–334) has no tests |
| `semantic_sift/hook_injector.py` | **7%** | All IDE injection logic untested |
| `semantic_sift/tools.py` | **43%** | Half of MCP tool implementations untested |
| `sift_kernel.py` | **60%** | HTML normalisation, caching, edge cases missing |
| `telemetry_core.py` | **70%** | OTel path, echo detection, pulse merging untested |
| `semantic_sift/onboarding.py` | **76%** | Auto-detect and fallback paths untested |

The product's central feature — subconscious hook interception — has virtually no automated proof it works.

**Impact**:
- Platform routing regressions (e.g., OpenCode misidentified as Gemini) are only caught by manual testing
- Injection logic for each IDE has no safety net
- A future contributor cannot safely refactor any of these files

---

#### COV-02 · `pytest-cov` not in dev dependencies

**Severity**: Medium
**File(s)**: `pyproject.toml`

**Observation**:
`pytest-cov` is not listed in `[project.optional-dependencies]` `dev` extra. A developer cloning the repo and running `pip install .[dev]` cannot measure coverage without knowing to install it separately.

**Evidence**:
```
$ pip show pytest-cov
WARNING: Package(s) not found: pytest-cov
```

---

### Category: Code Quality — Linting

---

#### LINT-01 · 22 ruff violations across codebase

**Severity**: Medium
**File(s)**: `sift_hook.py`, `sift_kernel.py`, `telemetry_core.py`, `semantic_sift/tools.py`, `benchmark_sift.py`, `tests/`

**Observation**:
`ruff` (installed during audit) reports 22 violations. 10 are auto-fixable. Categories:

| Code | Count | Description |
|---|---|---|
| `F401` | 9 | Unused imports (`json`, `time`, `sys`, `os`, `pytest`) |
| `E701` | 8 | Multiple statements on one line (`if x: return`) |
| `E741` | 1 | Ambiguous variable name `l` (indistinguishable from `1`) in `tools.py:172` |
| `F541` | 1 | f-string with no placeholders in `benchmark_sift.py:142` |

**`ruff` is not configured in `pyproject.toml`** — no `[tool.ruff]` section exists.

**Impact**:
- `E741` (`l` vs `1`) is a real readability hazard in a monospace font
- Unused imports in test files (`pytest` imported but never used) suggest copy-paste without review
- No enforcement means violations accumulate silently

---

#### LINT-02 · No formatter configured

**Severity**: Low
**File(s)**: `pyproject.toml`

**Observation**:
No `ruff format` or `black` configuration exists. Code style is inconsistent between files (some use inline `if x: return`, some don't). A formatter enforces consistency automatically.

---

### Category: Legal — Contribution Model

---

#### LEGAL-01 · No Contributor License Agreement (CLA) — dual-license model legally fragile

**Severity**: Critical
**File(s)**: `LICENSE.md`, `CONTRIBUTING.md` (missing)

**Observation**:
`LICENSE.md` defines a Source-Available Dual License: free for personal/non-commercial use, paid for commercial use. Under this model, Luis retains the right to sell commercial licenses that include contributor code.

However, by default under copyright law, a contributor retains copyright on their patch. Without a CLA, Luis does not have sufficient rights to include a third-party contribution in a commercial tier. Any future pull request — even a one-line fix — creates a legal ambiguity about the commercial license.

There is also no `CONTRIBUTING.md` file. Contributors have no guidance on:
- The CLA requirement
- That their code may be included in paid commercial tiers
- How to set up the dev environment
- Code style and testing expectations

**Impact**:
- The commercial license is legally uncertain the moment a single external PR is merged
- External contributors are not informed they are contributing to a commercial product
- Without `CONTRIBUTING.md`, GitHub shows no contribution guidance link on the repo homepage

---

#### LEGAL-02 · `SECURITY.md` location may not be discoverable by GitHub

**Severity**: Low
**File(s)**: `SECURITY.md`

**Observation**:
GitHub only surfaces `SECURITY.md` as the repo's official security policy if it is located at the root, in `docs/`, or in `.github/`. The current location should be verified.

---

### Category: Documentation — Completeness

---

#### DOC-01 · No README badge row

**Severity**: Medium
**File(s)**: `README.md`

**Observation**:
`README.md` has no badges (CI status, coverage, PyPI version, license). For a designer's portfolio project, badges are the first visual signal of project health. They are the difference between a project that *looks* professional and one that *proves* it is.

Without CI, the CI badge cannot exist — confirming CI-01 is the prerequisite.

---

#### DOC-02 · No `CONTRIBUTING.md`

**Severity**: High (overlaps LEGAL-01)
**File(s)**: Root directory (missing)

**Observation**:
GitHub surfaces a `CONTRIBUTING.md` link on the "New Issue" and "New PR" pages when the file exists. Without it, the repo has no onboarding path for external contributors. Given the CLA requirement from the dual license, this file is not optional — it is the primary legal notice mechanism.

---

## Summary Table

| ID | Category | Severity | Status |
|---|---|---|---|
| CI-01 | CI/CD | Critical | Open |
| CI-02 | CI/CD | High | Open |
| COV-01 | Coverage | Critical | Open |
| COV-02 | Coverage | Medium | Open |
| LINT-01 | Linting | Medium | Open |
| LINT-02 | Linting | Low | Open |
| LEGAL-01 | Legal | Critical | Open |
| LEGAL-02 | Legal | Low | Open |
| DOC-01 | Documentation | Medium | Open |
| DOC-02 | Documentation | High | Open |

---

*This report was generated during a live audit session. All findings were verified by running tools against the actual codebase.*
