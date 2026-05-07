#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Luis Kobayashi. All rights reserved.
"""
Download the pre-built sift-core binary for the current platform from the
matching GitHub release and install it into the active Python environment's
Scripts / bin directory.

Usage (editable / dev install):
    python scripts/fetch_sift_core.py

The script reads the package version from pyproject.toml so it always pulls
the binary that matches the checked-out source tree.
"""

from __future__ import annotations

import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_version() -> str:
    """Parse version from pyproject.toml without importing the package."""
    repo_root = Path(__file__).resolve().parent.parent
    pyproject = repo_root / "pyproject.toml"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Could not find version in pyproject.toml")


def _asset_name() -> tuple[str, bool]:
    """Return (asset_filename, is_windows) for the running platform."""
    machine = platform.machine().lower()
    plat = sys.platform

    if plat == "win32":
        if machine in ("amd64", "x86_64"):
            return "sift-core-x86_64-pc-windows-msvc.zip", True
        raise RuntimeError(f"No pre-built Windows binary for arch: {machine}")

    if plat == "darwin":
        if machine in ("arm64", "aarch64"):
            return "sift-core-aarch64-apple-darwin.tar.gz", False
        if machine in ("x86_64", "amd64"):
            return "sift-core-x86_64-apple-darwin.tar.gz", False
        raise RuntimeError(f"No pre-built macOS binary for arch: {machine}")

    # Linux (and anything else — treat as Linux/glibc)
    if machine in ("x86_64", "amd64"):
        return "sift-core-x86_64-unknown-linux-gnu.tar.gz", False
    if machine in ("aarch64", "arm64"):
        return "sift-core-aarch64-unknown-linux-gnu.tar.gz", False
    raise RuntimeError(f"No pre-built Linux binary for arch: {machine}")


def _scripts_dir() -> Path:
    """Return the Scripts (Windows) or bin (POSIX) directory of the active env."""
    if sys.platform == "win32":
        return Path(sys.prefix) / "Scripts"
    return Path(sys.prefix) / "bin"


def _download(url: str, dest: Path) -> None:
    print(f"  Downloading {url} …")
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as fh:  # noqa: S310
        shutil.copyfileobj(resp, fh)


def _extract_binary(archive: Path, is_windows: bool, target_dir: Path) -> Path:
    """Extract the sift-core binary from the archive into target_dir.

    Release archives contain a single file named after the target triple
    (e.g. sift-core-x86_64-pc-windows-msvc.exe). We extract it and rename it
    to the canonical sift-core[.exe] name.
    """
    exe_name = "sift-core.exe" if is_windows else "sift-core"
    dest = target_dir / exe_name

    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            members = zf.namelist()
            if not members:
                raise RuntimeError(f"Empty archive: {archive.name}")
            zf.extract(members[0], target_dir)
            (target_dir / members[0]).rename(dest)
    else:
        with tarfile.open(archive, "r:gz") as tf:
            members = tf.getmembers()
            if not members:
                raise RuntimeError(f"Empty archive: {archive.name}")
            tf.extract(members[0], target_dir, filter="data")
            (target_dir / members[0].name).rename(dest)

    return dest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    version = _read_version()
    asset, is_windows = _asset_name()
    scripts_dir = _scripts_dir()

    exe_name = "sift-core.exe" if is_windows else "sift-core"
    dest = scripts_dir / exe_name

    print(f"semantic-sift v{version}  |  platform: {sys.platform}/{platform.machine()}")
    print(f"Asset  : {asset}")
    print(f"Target : {dest}")

    base_url = (
        f"https://github.com/luismichio/semantic-sift/releases/download/v{version}"
    )
    url = f"{base_url}/{asset}"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / asset
        _download(url, archive)
        binary = _extract_binary(archive, is_windows, tmp_path)

        scripts_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(binary, dest)

    # Ensure executable bit on POSIX
    if not is_windows:
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"  Installed -> {dest}")
    print("Done. Run `sift-core --help` to verify.")


if __name__ == "__main__":
    main()
