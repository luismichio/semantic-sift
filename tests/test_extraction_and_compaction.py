from semantic_sift import kernel as sift_kernel
from semantic_sift import kernel as _kernel_impl


def test_extraction_show_diff_includes_removed_section(monkeypatch):
    monkeypatch.setattr(_kernel_impl, "perform_hybrid_sift", lambda text, rate=0.7: "cleaned output")
    content = "Page 1 of 3\nImportant line\nFooter"

    result = sift_kernel.perform_extraction_cleaning(content, show_diff=True)

    assert "cleaned output" in result
    assert "--- REMOVED CONTENT ---" in result


def test_compaction_adds_low_fidelity_warning(monkeypatch):
    monkeypatch.setattr(_kernel_impl, "perform_hybrid_sift", lambda text, rate=0.2: "tiny")
    monkeypatch.setattr(_kernel_impl, "calculate_vocabulary_overlap", lambda original, compressed: 0.1)
    monkeypatch.setenv("SIFT_COMPACTION_FIDELITY_THRESHOLD", "0.3")

    # Input must have both a priority line AND non-priority body text so the
    # semantic compression path (and fidelity check) is actually reached.
    result = sift_kernel.perform_compaction_summary(
        "Decision: Keep architecture stable\nSome additional context that is not a marker"
    )

    assert "Low fidelity compaction detected" in result
    assert "Score: 0.10" in result


def test_compaction_priority_lines_not_duplicated(monkeypatch):
    """Priority lines must appear only in Structural Snapshot, not again in Semantic Summary."""
    priority_line = "Decision: Keep architecture stable"
    body_line = "Some other context line that is not a priority marker"
    text = f"{priority_line}\n{body_line}"

    # Simulate semantic sift returning only the body line (priority was stripped before compression)
    def fake_sift(t: str, rate: float = 0.2) -> str:
        return t  # echo back whatever was passed in

    monkeypatch.setattr(_kernel_impl, "perform_hybrid_sift", fake_sift)
    monkeypatch.setattr(_kernel_impl, "calculate_vocabulary_overlap", lambda a, b: 1.0)

    result = sift_kernel.perform_compaction_summary(text)

    # Priority line must appear in the snapshot section
    assert "## Structural Snapshot" in result
    assert priority_line in result

    # Priority line must NOT appear twice in the output
    assert result.count(priority_line) == 1, (
        f"Priority line appeared {result.count(priority_line)} times — duplicate detected"
    )


def test_compaction_no_negative_token_savings(monkeypatch):
    """Priority lines must not be duplicated — each should appear exactly once in output."""
    text = "Decision: use BSL 1.1\nStatus: license committed\nFile: LICENSE.md updated"

    monkeypatch.setattr(_kernel_impl, "perform_hybrid_sift", lambda t, rate=0.2: t)
    monkeypatch.setattr(_kernel_impl, "calculate_vocabulary_overlap", lambda a, b: 1.0)

    result = sift_kernel.perform_compaction_summary(text)

    for line in text.splitlines():
        count = result.count(line)
        assert count == 1, f"Line '{line}' appeared {count} times in output — duplicate detected"


def test_compaction_structural_snapshot_branch(monkeypatch):
    """With context_hint present, output contains both section headers."""
    monkeypatch.setattr(_kernel_impl, "perform_hybrid_sift", lambda t, rate=0.2: "compressed")
    monkeypatch.setattr(_kernel_impl, "calculate_vocabulary_overlap", lambda a, b: 1.0)

    result = sift_kernel.perform_compaction_summary("Task: write tests\nIrrelevant filler line here")

    assert "## Structural Snapshot" in result
    assert "## Semantic Summary" in result
    assert "compressed" in result
