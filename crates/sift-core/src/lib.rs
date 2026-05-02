// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Luis Kobayashi. All rights reserved.

use regex::Regex;
use once_cell::sync::Lazy;
use std::path::Path;
use ndarray::Array2;
use ort::session::Session;
use tokenizers::Tokenizer;

pub struct SemanticEngine {
    session: Session,
    tokenizer: Tokenizer,
}

impl SemanticEngine {
    /// Initialize the semantic engine with the ONNX model and tokenizer.
    pub fn new<P: AsRef<Path>>(model_dir: P) -> Result<Self, String> {
        let model_dir = model_dir.as_ref();
        let model_path = model_dir.join("model.onnx");
        let tokenizer_path = model_dir.join("tokenizer.json");

        if !model_path.exists() {
            return Err(format!("Model not found at {:?}", model_path));
        }
        if !tokenizer_path.exists() {
            return Err(format!("Tokenizer not found at {:?}", tokenizer_path));
        }

        let session = Session::builder()
            .map_err(|e: ort::Error| e.to_string())?
            .commit_from_file(model_path)
            .map_err(|e: ort::Error| e.to_string())?;

        let tokenizer = Tokenizer::from_file(tokenizer_path)
            .map_err(|e: Box<dyn std::error::Error + Send + Sync>| e.to_string())?;

        Ok(Self { session, tokenizer })
    }

    /// Perform semantic distillation on the given text at the specified rate.
    pub fn compress(&mut self, text: &str, rate: f32) -> Result<String, String> {
        let encoding = self.tokenizer.encode(text, true)
            .map_err(|e: Box<dyn std::error::Error + Send + Sync>| e.to_string())?;
        
        let ids = encoding.get_ids();
        let attention_mask = encoding.get_attention_mask();
        let seq_len = ids.len();

        if seq_len == 0 {
            return Ok(String::new());
        }

        let input_ids_array = Array2::from_shape_vec((1, seq_len), ids.iter().map(|&x| x as i64).collect())
            .map_err(|e: ndarray::ShapeError| e.to_string())?;
        let attention_mask_array = Array2::from_shape_vec((1, seq_len), attention_mask.iter().map(|&x| x as i64).collect())
            .map_err(|e: ndarray::ShapeError| e.to_string())?;
        let token_type_ids_array = Array2::from_shape_vec((1, seq_len), vec![0i64; seq_len])
            .map_err(|e: ndarray::ShapeError| e.to_string())?;

        // In ort 2.x, we must create Value objects from arrays
        let input_ids_value = ort::value::Value::from_array(input_ids_array)
            .map_err(|e: ort::Error| e.to_string())?;
        let attention_mask_value = ort::value::Value::from_array(attention_mask_array)
            .map_err(|e: ort::Error| e.to_string())?;
        let token_type_ids_value = ort::value::Value::from_array(token_type_ids_array)
            .map_err(|e: ort::Error| e.to_string())?;

        let inputs = ort::inputs![
            "input_ids" => &input_ids_value,
            "attention_mask" => &attention_mask_value,
            "token_type_ids" => &token_type_ids_value,
        ];

        let outputs = self.session.run(inputs).map_err(|e: ort::Error| e.to_string())?;
        
        // Extract raw data and shape
        let logits_data = outputs["logits"].try_extract_tensor::<f32>()
            .map_err(|e: ort::Error| e.to_string())?;
        
        let (_shape, data) = logits_data;
        
        // Extract probabilities for the "preserve" class (index 1)
        let mut scores = Vec::with_capacity(seq_len);
        for i in 0..seq_len {
            let offset_discard = i * 2;
            let offset_preserve = i * 2 + 1;
            
            let logit_discard = data[offset_discard];
            let logit_preserve = data[offset_preserve];
            
            let exp_discard = logit_discard.exp();
            let exp_preserve = logit_preserve.exp();
            let prob_preserve = exp_preserve / (exp_discard + exp_preserve);
            scores.push(prob_preserve);
        }

        // Determine threshold based on rate
        let mut sorted_scores = scores.clone();
        sorted_scores.sort_by(|a: &f32, b: &f32| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        
        let threshold_idx = ((1.0 - rate) * seq_len as f32) as usize;
        let threshold = if threshold_idx < seq_len {
            sorted_scores[threshold_idx]
        } else {
            0.0
        };

        // Reconstruct text with preserved tokens
        let mut result_ids = Vec::new();
        for (i, &score) in scores.iter().enumerate() {
            if score >= threshold {
                result_ids.push(ids[i]);
            }
        }

        self.tokenizer.decode(&result_ids, true).map_err(|e: Box<dyn std::error::Error + Send + Sync>| e.to_string())
    }
}

/// Heuristic Sieve: Ported from Python sift_kernel.py
/// Sifts through raw technical logs to remove noise.
pub fn apply_heuristic_sieve(text: &str) -> String {
    static TIMESTAMP_PATTERN: Lazy<Regex> = Lazy::new(|| {
        Regex::new(r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?)|(\d{6}\s\d{6}\s\d+)|(\[\d{2}:\d{2}:\d{2}(\.\d+)?\])").unwrap()
    });
    static PROGRESS_PATTERN: Lazy<Regex> = Lazy::new(|| {
        Regex::new(r"\[\d+/\d+\]|[\.]{3,}|\d+%\s*").unwrap()
    });
    static METADATA_PATTERN: Lazy<Regex> = Lazy::new(|| {
        Regex::new(r"\s*(INFO|DEBUG|WARN|ERROR)\s+dfs\..*?:\s*").unwrap()
    });
    static MODULE_PATTERN: Lazy<Regex> = Lazy::new(|| {
        Regex::new(r"(?i)^\s*[\d\.]+\s+(MB|KB|bytes|B)\s+[\w\-\.\/]+.*$").unwrap()
    });

    let mut sifted = Vec::new();
    
    for line in text.lines() {
        let clean_line = TIMESTAMP_PATTERN.replace_all(line, "").trim().to_string();
        let clean_line = METADATA_PATTERN.replace_all(&clean_line, "").trim().to_string();
        
        if clean_line.is_empty() 
            || PROGRESS_PATTERN.is_match(&clean_line) 
            || MODULE_PATTERN.is_match(&clean_line) 
        {
            continue;
        }
        
        sifted.push(clean_line);
    }
    
    sifted.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_heuristic_sieve_removes_timestamps() {
        let input = "2026-05-01T12:00:00Z INFO some message";
        let expected = "INFO some message";
        assert_eq!(apply_heuristic_sieve(input), expected);
    }

    #[test]
    fn test_heuristic_sieve_removes_progress() {
        let input = "Compiling... [1/42] 25%";
        let expected = "";
        assert_eq!(apply_heuristic_sieve(input), expected);
    }

    #[test]
    fn test_heuristic_sieve_preserves_errors() {
        let input = "ERROR: connection refused at line 42";
        let expected = "ERROR: connection refused at line 42";
        assert_eq!(apply_heuristic_sieve(input), expected);
    }

    #[test]
    fn test_heuristic_sieve_strips_hdfs_metadata() {
        let input = "2026-05-01T12:00:00Z INFO dfs.DataNode: Receiving block";
        let expected = "Receiving block";
        assert_eq!(apply_heuristic_sieve(input), expected);
    }
}
