from semantic_sift.kernel import apply_heuristic_sieve


def test_sieve_removes_timestamps():
    noisy = "2026-04-19T20:30:15Z Build started\n2026-04-19T20:30:16Z Compiling components"
    expected = "Build started\nCompiling components"
    assert apply_heuristic_sieve(noisy) == expected


def test_sieve_removes_progress_bars():
    noisy = "[1/534] Building...\n[50/534] Done\n42% processed\n99% complete\nReal Error Found"
    expected = "Real Error Found"
    assert apply_heuristic_sieve(noisy) == expected


def test_sieve_removes_repetitive_dots():
    noisy = "Processing..........\nLoading...\nFinished"
    expected = "Finished"
    assert apply_heuristic_sieve(noisy) == expected


def test_sieve_preserves_error_messages():
    noisy = '2026-04-19T21:00:00Z ERROR: File not found at /src/main.py\nTraceback (most recent call last):\n  File "main.py", line 10'
    # Timestamps should go, but the ERROR and Traceback must stay
    result = apply_heuristic_sieve(noisy)
    assert "ERROR: File not found at /src/main.py" in result
    assert "Traceback (most recent call last):" in result
    assert "line 10" in result


def test_sieve_removes_module_listings():
    noisy = "  12.5 MB  node_modules/react/dist/index.js\n  500 bytes  .gitignore\nImportant Log Message"
    expected = "Important Log Message"
    assert apply_heuristic_sieve(noisy) == expected
