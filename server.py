# SPDX-License-Identifier: BUSL-1.1
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
import sys

from mcp.server.fastmcp import FastMCP

import sift_kernel
from semantic_sift.hook_injector import build_runtime_hook_command, get_windsurf_gateway_command
from semantic_sift.tools import register_tools


def _build_runtime_hook_command() -> tuple[str, str, str]:
    return build_runtime_hook_command()


RUNTIME_PYTHON_EXE, RUNTIME_HOOK_SCRIPT, RUNTIME_HOOK_COMMAND = _build_runtime_hook_command()


def _get_windsurf_gateway_command() -> str:
    return get_windsurf_gateway_command()


mcp = FastMCP("Semantic-Sift")

try:
    sift_kernel.start_model_warmup()
except Exception as e:
    print(f"[Semantic-Sift] Model warm-up skipped: {e}", file=sys.stderr)


register_tools(mcp, RUNTIME_PYTHON_EXE, RUNTIME_HOOK_SCRIPT, RUNTIME_HOOK_COMMAND)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
