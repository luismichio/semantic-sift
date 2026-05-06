# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.

from setuptools import setup
from setuptools_rust import RustBin

setup(
    rust_extensions=[
        RustBin("sift-core", path="crates/sift-core/Cargo.toml")
    ],
)
