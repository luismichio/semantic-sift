# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
#
# Rust extension is OPTIONAL:
#   - PyPI wheel: sift-core binary is pre-built and bundled — no Rust toolchain needed.
#   - Editable/dev clone: run `python scripts/fetch_sift_core.py` to download the binary.
#   - Source build (CI release): setuptools_rust is installed by the release workflow.
# If setuptools_rust is not available, setup() proceeds without the extension.

from setuptools import setup

try:
    from setuptools_rust import RustBin
    rust_extensions = [RustBin("sift-core", path="crates/sift-core/Cargo.toml", optional=True)]
except ImportError:
    rust_extensions = []

setup(rust_extensions=rust_extensions)
