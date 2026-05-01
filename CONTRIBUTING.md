# Contributing to Semantic-Sift

Thank you for your interest in contributing. Before you submit anything, please read this document in full — it is short, but the legal section is not optional.

---

## 1. Inbound Contributions & Licensing

Semantic-Sift is published under the **Apache License 2.0** (see [`LICENSE.md`](LICENSE.md)). 

By submitting a pull request, you agree that any contributions you provide will be licensed under the same Apache 2.0 terms. You retain copyright over your contribution and will be credited in the commit history. 

You must confirm that you have the right to make this grant (i.e., the contribution is your own original work or you have the necessary permissions from your employer).

---

## 2. What We Are Looking For

Contributions that align with the project philosophy:

- **System over Patch**: Changes that follow the architectural patterns in [`doc/ARCHITECTURE.md`](doc/ARCHITECTURE.md).
- **Signal over Noise**: The goal of this project is to reduce noise; do not introduce it into the codebase.
- **Atomic by Default**: Logic must be modular and testable in isolation.

The [`BACKLOG.md`](BACKLOG.md) is the source of truth for planned work. If you want to pick up an item, leave a comment on the relevant GitHub issue first to avoid duplicate effort.

---

## 3. Development Environment Setup

**Requirements**: Python 3.10+, git.

```bash
# Clone the repo
git clone https://github.com/luismichio/semantic-sift.git
cd semantic-sift

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# Install with all dev dependencies
pip install -e ".[dev]"

# Optional: install neural model dependencies (large download ~2GB)
pip install -e ".[neural]"
```

---

## 4. Running the Test Suite

Always run the full suite before submitting a PR:

```bash
# Run tests
python -m pytest

# Run tests with coverage report
python -m pytest --cov=semantic_sift --cov=sift_kernel --cov=telemetry_core --cov-report=term-missing

# Type checking
python -m mypy semantic_sift/ telemetry_core.py sift_kernel.py server.py sift_hook.py

# Linting
python -m ruff check .
```

All four commands must pass with zero errors before a PR will be reviewed.

---

## 5. Code Style

- **Python 3.10+** features and type hints are required. Avoid `typing.Any` where possible.
- **PEP 8** with a line length of 120 characters (`ruff` enforces this).
- **No `print()` statements** in production code — use the `logging` module or the project's `log()` helper in `sift_hook.py`.
- **No model weights in the repo** — models are downloaded and cached via `transformers` at runtime.
- Single-line `if x: return` style is **not permitted** — `ruff` will flag it (`E701`).
- Ambiguous variable names (`l`, `O`, `I`) are **not permitted** — `ruff` will flag them (`E741`).

---

## 6. Adding a New Platform

The hook's platform detection chain is documented in [`BACKLOG.md`](BACKLOG.md) under **Platform Detection Refactor**. Until that refactor is implemented, adding a new platform means:

1. Adding env var fingerprints to `detect_client_id()` in `telemetry_core.py`.
2. Adding a detection branch in `sift_hook.py` (the `if/elif` chain at lines ~104–145).
3. Adding an injection branch in `sift_hook.py` (the `if/elif` chain at lines ~313–327).
4. Adding a test in `tests/test_hook_routing.py` that verifies the platform is correctly detected from a realistic payload.

All four steps are required. A PR that adds detection without a test will not be merged.

---

## 7. Changelog

Every PR that changes behaviour **must** include an entry in [`doc/CHANGELOG.md`](doc/CHANGELOG.md) under `## [Unreleased]`. Use the existing entries as a format reference.

Bug fixes go under `### 🐛 Bug Fixes`. New features go under `### ✨ New Features`. Internal refactors go under `### 🔧 Internal`.

---

## 8. Commit Messages

Follow the existing style visible in `git log`:

```
Short imperative summary (max 72 chars)

Optional longer explanation if the why is not obvious.
Reference finding IDs from doc/bug/ if applicable (e.g. Fixes CI-01).
```

---

## 9. Pull Request Checklist

Before marking a PR as ready for review:

- [ ] `python -m pytest` passes
- [ ] `python -m mypy ...` reports 0 errors
- [ ] `python -m ruff check .` reports 0 violations
- [ ] `doc/CHANGELOG.md` updated under `[Unreleased]`
- [ ] New behaviour has at least one test
- [ ] I have read and agree to the licensing terms in section 1 of this document

---

*Copyright © 2026 Luis Kobayashi. All rights reserved.*
