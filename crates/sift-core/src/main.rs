// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Luis Kobayashi. All rights reserved.

use clap::{Parser, Subcommand};
use std::io::{self, Read};
use std::path::PathBuf;
use semantic_sift_core::{apply_heuristic_sieve, SemanticEngine};

#[derive(Parser)]
#[command(name = "sift-core")]
#[command(about = "High-performance context distillation core", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Sift logs via heuristic sieve
    Logs {
        /// Input text to sift (reads from stdin if omitted)
        #[arg(short, long)]
        input: Option<String>,
    },
    /// Sift prose via semantic engine (ONNX)
    Semantic {
        /// Input text to sift (reads from stdin if omitted)
        #[arg(short, long)]
        input: Option<String>,
        /// Compression rate (0.1 to 0.9)
        #[arg(short, long, default_value_t = 0.5)]
        rate: f32,
        /// Path to the ONNX model directory
        #[arg(short, long)]
        model: Option<PathBuf>,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Logs { input } => {
            let text = match input {
                Some(t) => t,
                None => {
                    let mut buffer = String::new();
                    io::stdin().read_to_string(&mut buffer)?;
                    buffer
                }
            };
            let result = apply_heuristic_sieve(&text);
            println!("{}", result);
        }
        Commands::Semantic { input, rate, model } => {
            let text = match input {
                Some(t) => t,
                None => {
                    let mut buffer = String::new();
                    io::stdin().read_to_string(&mut buffer)?;
                    buffer
                }
            };
            
            if let Some(model_path) = model {
                let mut engine = SemanticEngine::new(model_path)?;
                let result = engine.compress(&text, rate)?;
                println!("{}", result);
            } else {
                // Heuristic fallback if no model is provided
                let result = apply_heuristic_sieve(&text);
                println!("[Semantic-Sift: Heuristic Fallback (no model provided)]");
                println!("{}", result);
            }
        }
    }

    Ok(())
}

