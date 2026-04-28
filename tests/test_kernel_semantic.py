import os

import sift_kernel


class _FakeCompressor:
    def compress_prompt(self, prompts, rate, force_tokens, chunk_end_tokens, return_word_label):
        return {"compressed_prompt": f"compressed:{rate}:{prompts[0]}"}


def test_perform_semantic_sift_uses_cached_result(monkeypatch):
    monkeypatch.setattr(sift_kernel, "check_cache", lambda _: "cached-value")
    result = sift_kernel.perform_semantic_sift("hello", rate=0.5)
    assert result == "cached-value"


def test_perform_semantic_sift_warmup_fallback(monkeypatch):
    monkeypatch.setenv("SIFT_MODEL_READY_WAIT_MS", "0")
    monkeypatch.setattr(sift_kernel, "check_cache", lambda _: None)
    monkeypatch.setattr(sift_kernel, "apply_heuristic_sieve", lambda text: "heuristic-fallback")
    monkeypatch.setattr(sift_kernel, "start_model_warmup", lambda: None)
    sift_kernel._MODEL_READY.clear()

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.5)

    assert result.startswith("[Semantic-Sift: Models warming up - heuristic mode active]")
    assert "heuristic-fallback" in result


def test_perform_semantic_sift_unavailable_model_fallback(monkeypatch):
    monkeypatch.setattr(sift_kernel, "check_cache", lambda _: None)
    monkeypatch.setattr(sift_kernel, "start_model_warmup", lambda: None)
    monkeypatch.setattr(sift_kernel, "apply_heuristic_sieve", lambda text: "fallback-text")

    sift_kernel._MODEL_READY.set()
    sift_kernel._COMPRESSOR = None
    sift_kernel._MODEL_WARMUP_ERROR = "boom"

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.5)

    assert result.startswith("[Semantic-Sift: Semantic model unavailable - heuristic mode active]")
    assert "fallback-text" in result


def test_perform_semantic_sift_uses_ready_compressor(monkeypatch):
    monkeypatch.setattr(sift_kernel, "check_cache", lambda _: None)
    monkeypatch.setattr(sift_kernel, "start_model_warmup", lambda: None)
    captured = {}

    def _set_cache(key, value):
        captured["value"] = value

    monkeypatch.setattr(sift_kernel, "set_cache", _set_cache)

    sift_kernel._MODEL_READY.set()
    sift_kernel._MODEL_WARMUP_ERROR = None
    sift_kernel._COMPRESSOR = _FakeCompressor()

    result = sift_kernel.perform_semantic_sift("input-text", rate=0.6)

    assert result == "compressed:0.6:input-text"
    assert captured["value"] == "compressed:0.6:input-text"
