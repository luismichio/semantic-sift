from semantic_sift import kernel as sift_kernel
from semantic_sift import kernel as _kernel_impl


class _FakeCompressor:
    def compress_prompt(self, prompts, rate, force_tokens, chunk_end_tokens, return_word_label):
        return {"compressed_prompt": f"compressed:{rate}:{prompts[0]}"}


def test_perform_semantic_sift_uses_cached_result(monkeypatch):
    monkeypatch.setattr(_kernel_impl, "check_cache", lambda _: "cached-value")
    result = sift_kernel.perform_semantic_sift("hello", rate=0.5)
    assert result == "cached-value"


def test_perform_semantic_sift_warmup_fallback(monkeypatch):
    monkeypatch.setenv("SIFT_MODEL_READY_WAIT_MS", "0")
    monkeypatch.setattr(_kernel_impl, "check_cache", lambda _: None)
    monkeypatch.setattr(_kernel_impl, "apply_heuristic_sieve", lambda text: "heuristic-fallback")
    monkeypatch.setattr(_kernel_impl, "start_model_warmup", lambda: None)
    _kernel_impl._MODEL_READY.clear()

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.5)

    assert result.startswith("[Semantic-Sift: Models warming up - heuristic mode active]")
    assert "heuristic-fallback" in result


def test_perform_semantic_sift_unavailable_model_fallback(monkeypatch):
    monkeypatch.setattr(_kernel_impl, "check_cache", lambda _: None)
    monkeypatch.setattr(_kernel_impl, "start_model_warmup", lambda: None)
    monkeypatch.setattr(_kernel_impl, "apply_heuristic_sieve", lambda text: "fallback-text")

    _kernel_impl._MODEL_READY.set()
    _kernel_impl._COMPRESSOR = None
    _kernel_impl._MODEL_WARMUP_ERROR = "boom"

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.5)

    assert result.startswith("[Semantic-Sift: Semantic model unavailable - heuristic mode active]")
    assert "fallback-text" in result


def test_perform_semantic_sift_uses_ready_compressor(monkeypatch):
    monkeypatch.setattr(_kernel_impl, "check_cache", lambda _: None)
    monkeypatch.setattr(_kernel_impl, "start_model_warmup", lambda: None)
    captured = {}

    def _set_cache(key, value):
        captured["value"] = value

    monkeypatch.setattr(_kernel_impl, "set_cache", _set_cache)

    _kernel_impl._MODEL_READY.set()
    _kernel_impl._MODEL_WARMUP_ERROR = None
    _kernel_impl._COMPRESSOR = _FakeCompressor()

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.6)

    assert result == "compressed:0.6:input-text"
    assert captured["value"] == "compressed:0.6:input-text"
