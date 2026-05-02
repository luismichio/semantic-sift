// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Luis Kobayashi. All rights reserved.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use semantic_sift_core::{apply_heuristic_sieve, SemanticEngine};
use std::path::Path;

fn criterion_benchmark(c: &mut Criterion) {
    // Sample high-noise log content (simulating 100 lines)
    let log_line = "2026-05-01T12:00:00.123Z INFO dfs.DataNode: Receiving block BP-12345:blk_67890 src: /127.0.0.1:54321 dest: /127.0.0.1:9876\n";
    let massive_logs = log_line.repeat(100);

    c.bench_function("heuristic_sieve_100_lines", |b| {
        b.iter(|| apply_heuristic_sieve(black_box(&massive_logs)))
    });

    // Semantic Benchmark (only if model exists)
    let model_path = Path::new("models/llmlingua2");
    if model_path.exists() {
        let mut engine = SemanticEngine::new(model_path).expect("failed to load engine");
        let prose = "This is a long test sentence that we will use to verify that the ONNX model is correctly performing token classification and sifting the text. We want to see how much it can reduce while keeping the core meaning.".repeat(5);
        
        c.bench_function("semantic_sift_prose", |b| {
            b.iter(|| engine.compress(black_box(&prose), 0.5))
        });
    }
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
