# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

import sys
import argparse
import subprocess
import logging

from semantic_sift import kernel

# We use stderr for logging so it doesn't corrupt the stdout data stream!
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[Sift-CLI] %(message)s")
logger = logging.getLogger("semantic_sift_cli")

def main():
    parser = argparse.ArgumentParser(description="Semantic-Sift Universal CLI (Hybrid Engine)")
    parser.add_argument("type", choices=["logs", "semantic", "doc", "extraction", "auto"], default="auto", nargs="?", help="Type of distillation")
    parser.add_argument("--rate", type=float, default=0.5, help="Compression rate for semantic tasks")

    args = parser.parse_args()

    # 1. Read from standard input
    input_data = sys.stdin.read()
    if not input_data:
        return

    char_count = len(input_data)

    # 2. Hybrid Engine Routing Decision
    if args.type == "logs" or (args.type == "auto" and char_count < 1000):
        # FAST PATH: Heuristics or small files
        # Ideally, we shell out to `sift-core logs` here if available.
        # For now, we use the Python kernel equivalent.
        logger.info(f"Routing {char_count} chars to Heuristic Engine.")
        result = kernel.apply_heuristic_sieve(input_data)

    else:
        # NEURAL PATH: Semantic compression
        if char_count > 30000:
            logger.info(f"Massive payload ({char_count} chars). Routing to PyTorch Engine (Flash Attention).")
            # In the future, this explicitly loads PyTorch.
            # Currently, the python kernel uses PyTorch (llmlingua).
            result = kernel.perform_semantic_sift(input_data, rate=args.rate)
        else:
            logger.info(f"Standard payload ({char_count} chars). Routing to Rust/ONNX Engine.")
            # Shell out to the Rust sidecar for low-latency ONNX execution
            try:
                process = subprocess.Popen(
                    ["sift-core", "semantic", "--rate", str(args.rate)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=input_data)
                if process.returncode == 0:
                    result = stdout
                else:
                    logger.warning(f"Rust engine failed: {stderr}. Falling back to PyTorch.")
                    result = kernel.perform_semantic_sift(input_data, rate=args.rate)
            except FileNotFoundError:
                logger.info("Rust engine not found. Falling back to PyTorch.")
                result = kernel.perform_semantic_sift(input_data, rate=args.rate)

    # 3. Output to standard output
    sys.stdout.write(result)

if __name__ == "__main__":
    main()
