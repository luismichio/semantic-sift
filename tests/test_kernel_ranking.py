from semantic_sift import kernel as sift_kernel


class _FakeCrossEncoder:
    def __init__(self, *args, **kwargs):
        pass

    def predict(self, pairs):
        scores = []
        for _, doc in pairs:
            scores.append(float(len(doc)))
        return scores


def test_perform_ranking_sorts_desc(monkeypatch):
    monkeypatch.setattr(sift_kernel, "get_device", lambda: "cpu")

    class _FakeST:
        CrossEncoder = _FakeCrossEncoder

    import sys

    sys.modules["sentence_transformers"] = _FakeST()
    try:
        result = sift_kernel.perform_ranking("query", ["a", "long-doc", "mid"], top_n=2)
        assert len(result) == 2
        assert result[0][1] == "long-doc"
        assert result[1][1] == "mid"
    finally:
        sys.modules.pop("sentence_transformers", None)


def test_perform_ranking_handles_failure(monkeypatch):
    import sys

    if "sentence_transformers" in sys.modules:
        sys.modules.pop("sentence_transformers", None)

    result = sift_kernel.perform_ranking("query", ["a"], top_n=1)
    assert isinstance(result, list)
