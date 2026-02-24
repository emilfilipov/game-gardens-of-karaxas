#!/usr/bin/env python3
"""Install a pinned Blender build for headless asset automation.

Usage:
  python3 tools/blender/install_blender.py
  python3 tools/blender/install_blender.py --version 4.2.3 --install-root .tools/blender
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_VERSION = "4.2.3"
DEFAULT_ROOT = Path(".tools/blender")


def _platform_descriptor(version: str) -> tuple[str, str]:
    system = platform.system().lower()
    if system == "linux":
        file_name = f"blender-{version}-linux-x64.tar.xz"
        return (
            f"https://download.blender.org/release/Blender4.2/{file_name}",
            file_name,
        )
    if system == "windows":
        file_name = f"blender-{version}-windows-x64.zip"
        return (
            f"https://download.blender.org/release/Blender4.2/{file_name}",
            file_name,
        )
    raise SystemExit(f"unsupported platform: {system}")


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out)


def _extract(archive_path: Path, install_root: Path) -> Path:
    install_root.mkdir(parents=True, exist_ok=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(install_root)
    else:
        with tarfile.open(archive_path, "r:xz") as archive:
            archive.extractall(install_root)
    candidates = sorted(path for path in install_root.iterdir() if path.is_dir() and path.name.startswith("blender-"))
    if not candidates:
        raise SystemExit(f"no extracted blender directory found in {install_root}")
    return candidates[-1]


def _write_manifest(install_root: Path, version: str, binary_path: Path) -> Path:
    manifest = install_root / "manifest.env"
    content = "\n".join(
        [
            f"BLENDER_VERSION={version}",
            f"BLENDER_BIN={binary_path}",
        ]
    )
    manifest.write_text(content + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--install-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    install_root = Path(args.install_root).resolve()
    url, file_name = _platform_descriptor(args.version)
    archive_path = install_root / file_name

    if args.force and install_root.exists():
        shutil.rmtree(install_root)

    if not archive_path.exists():
        print(f"[blender-install] downloading {url}")
        _download(url, archive_path)
    else:
        print(f"[blender-install] using cached archive {archive_path}")

    extracted_dir = _extract(archive_path, install_root)
    if platform.system().lower() == "windows":
        binary_path = extracted_dir / "blender.exe"
    else:
        binary_path = extracted_dir / "blender"

    if not binary_path.exists():
        raise SystemExit(f"blender binary not found at {binary_path}")

    manifest = _write_manifest(install_root, args.version, binary_path)
    print(f"[blender-install] OK version={args.version}")
    print(f"[blender-install] binary={binary_path}")
    print(f"[blender-install] manifest={manifest}")


if __name__ == "__main__":
    main()
