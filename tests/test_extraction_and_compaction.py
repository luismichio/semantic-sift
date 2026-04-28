import sift_kernel


def test_extraction_show_diff_includes_removed_section(monkeypatch):
    monkeypatch.setattr(sift_kernel, "perform_semantic_sift", lambda text, rate=0.7: "cleaned output")
    content = "Page 1 of 3\nImportant line\nFooter"

    result = sift_kernel.perform_extraction_cleaning(content, show_diff=True)

    assert "cleaned output" in result
    assert "--- REMOVED CONTENT ---" in result


def test_compaction_adds_low_fidelity_warning(monkeypatch):
    monkeypatch.setattr(sift_kernel, "perform_semantic_sift", lambda text, rate=0.2: "tiny")
    monkeypatch.setattr(sift_kernel, "calculate_vocabulary_overlap", lambda original, compressed: 0.1)
    monkeypatch.setenv("SIFT_COMPACTION_FIDELITY_THRESHOLD", "0.3")

    result = sift_kernel.perform_compaction_summary("Decision: Keep architecture stable")

    assert "Low fidelity compaction detected" in result
    assert "vocabulary overlap" in result
