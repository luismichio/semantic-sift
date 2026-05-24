# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

import sys
import argparse
import subprocess
import logging
import time
import os
import uuid
from datetime import datetime

from semantic_sift import kernel
from semantic_sift import telemetry as telemetry_core

# Force UTF-8 for standard streams on Windows and handle surrogates gracefully
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# We use stderr for logging so it doesn't corrupt the stdout data stream!
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[Sift-CLI] %(message)s")
logger = logging.getLogger("semantic_sift_cli")

SESSION_ID = f"cli-{uuid.uuid4().hex[:8]}"
START_TIME = datetime.now().astimezone().isoformat()


def main():
    parser = argparse.ArgumentParser(description="Semantic-Sift Universal CLI (Hybrid Engine)")
    parser.add_argument(
        "type",
        choices=["logs", "semantic", "doc", "extraction", "rank", "auto"],
        default="auto",
        nargs="?",
        help="Type of distillation",
    )
    parser.add_argument("--rate", type=float, default=0.5, help="Compression rate for semantic tasks")
    parser.add_argument("--query", type=str, help="Search query for reranking (rank mode only)")
    parser.add_argument("--top-n", type=int, default=3, help="Number of results to return (rank mode only)")
    parser.add_argument("--no-header", action="store_true", help="Do not prepend the audit header")
    args = parser.parse_args()

    # 1. Read from standard input
    input_data = sys.stdin.read()
    if not input_data:
        return

    # Self-Aware Bypass: Do not process data that already carries a Sift Audit header.
    # This prevents double-sifting in multi-layered or recursive orchestration.
    if "--- [Semantic-Sift Audit] ---" in input_data:
        logger.info("Header detected, bypassing sifting.")
        sys.stdout.write(input_data)
        return

    start_t = time.time()
    char_count = len(input_data)

    # 2. Hybrid Engine Routing Decision
    sift_engine = "heuristic"

    if args.type == "rank":
        # RERANKING PATH
        query = args.query or os.environ.get("SIFT_TOOL_NAME") or "context"
        logger.info(f"Performing Top-{args.top_n} Reranking for query: '{query}'")

        # Split input into documents (attempt standard search result delimiters)
        # 1. Try '---' separator
        docs = [d.strip() for d in input_data.split("\n---\n") if d.strip()]
        if len(docs) < 2:
            # 2. Try newline separator
            docs = [d.strip() for d in input_data.split("\n") if d.strip()]

        scored_docs = kernel.perform_ranking(query, docs, args.top_n)
        result = "\n\n---\n\n".join([doc for _, doc in scored_docs]) if scored_docs else input_data
        sift_engine = "ranker"

    elif args.type == "logs" or (args.type == "auto" and char_count < 1000):
        # FAST PATH: Heuristics or small files
        logger.info(f"Routing {char_count} chars to Heuristic Engine.")
        result = kernel.apply_heuristic_sieve(input_data)
        sift_engine = "heuristic"

    else:
        # NEURAL PATH: Semantic compression
        if char_count > 30000:
            logger.info(f"Massive payload ({char_count} chars). Routing to PyTorch Engine (Flash Attention).")
            result = kernel.perform_semantic_sift(input_data, rate=args.rate)
            sift_engine = "neural-torch"
        else:
            logger.info(f"Standard payload ({char_count} chars). Routing to Rust/ONNX Engine.")
            try:
                process = subprocess.Popen(
                    ["sift-core", "semantic", "--rate", str(args.rate)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="backslashreplace",
                )
                stdout, stderr = process.communicate(input=input_data)
                if process.returncode == 0:
                    result = stdout
                    sift_engine = "neural-rust"
                else:
                    logger.warning(f"Rust engine failed: {stderr}. Falling back to PyTorch.")
                    result = kernel.perform_semantic_sift(input_data, rate=args.rate)
                    sift_engine = "neural-torch-fallback"
            except FileNotFoundError:
                logger.info("Rust engine not found. Falling back to PyTorch.")
                result = kernel.perform_semantic_sift(input_data, rate=args.rate)
                sift_engine = "neural-torch-nofile"

    # 3. Telemetry Reporting
    latency = (time.time() - start_t) * 1000

    # Extract tool name from environment if provided by hook, or fallback
    tool_name = (
        os.environ.get("SIFT_TOOL_NAME")
        or os.environ.get("CLAUDE_TOOL_NAME")
        or os.environ.get("GEMINI_TOOL_NAME")
        or f"cli_{args.type}"
    )

    platform = telemetry_core.detect_client_id()

    # Send pulse
    telemetry_core.log_telemetry(
        SESSION_ID,
        START_TIME,
        f"sift_cli_{sift_engine}:{tool_name}",
        char_count,
        len(result),
        latency,
        client_id_override=platform,
    )

    # 4. Output to standard output
    if not args.no_header:
        header = telemetry_core.generate_audit_header(char_count, len(result), latency)
        sys.stdout.write(header)

    sys.stdout.write(result)

    # 5. Flush telemetry (Ensure pulse completes before process exit)
    telemetry_core.flush_telemetry_pulses()


if __name__ == "__main__":
    main()

# --- [Semantic-Sift Audit] ---
