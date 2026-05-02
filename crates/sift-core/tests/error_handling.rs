// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Luis Kobayashi. All rights reserved.

use semantic_sift_core::SemanticEngine;
use std::fs;
use tempfile::tempdir;

#[test]
fn test_engine_fails_on_missing_model() {
    let tmp_dir = tempdir().unwrap();
    // No files created in tmp_dir
    let result = SemanticEngine::new(tmp_dir.path());
    match result {
        Err(e) => assert!(e.contains("Model not found")),
        _ => panic!("Expected error for missing model"),
    }
}

#[test]
fn test_engine_fails_on_missing_tokenizer() {
    let tmp_dir = tempdir().unwrap();
    let model_path = tmp_dir.path().join("model.onnx");
    fs::write(model_path, "dummy model").unwrap();
    
    let result = SemanticEngine::new(tmp_dir.path());
    match result {
        Err(e) => assert!(e.contains("Tokenizer not found")),
        _ => panic!("Expected error for missing tokenizer"),
    }
}

#[test]
fn test_heuristic_sieve_empty_input() {
    use semantic_sift_core::apply_heuristic_sieve;
    assert_eq!(apply_heuristic_sieve(""), "");
}

#[test]
fn test_heuristic_sieve_whitespace_only() {
    use semantic_sift_core::apply_heuristic_sieve;
    assert_eq!(apply_heuristic_sieve("   \n  \t "), "");
}
