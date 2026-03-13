#!/usr/bin/env python3
"""Build a deterministic Windows designer-client release bundle + manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_zip_from_dir(source_dir: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, "w") as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(source_dir).as_posix()
            info = ZipInfo(filename=arcname, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, file_path.read_bytes())


def build_manifest(staging_dir: Path, version: str, artifact_name: str) -> dict:
    files: list[dict] = []
    for file_path in sorted(staging_dir.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(staging_dir).as_posix()
        files.append(
            {
                "path": relative,
                "size_bytes": file_path.stat().st_size,
                "sha256": file_sha256(file_path),
            }
        )
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "version": version,
        "platform": "windows-x64",
        "entrypoint": "start_designer_client.bat",
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Windows designer-client runtime for release.")
    parser.add_argument("--version", required=True, help="Release version (e.g. 1.0.123)")
    parser.add_argument("--output-dir", default="releases/designer", help="Artifact output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = args.version.strip()
    if not version:
        raise ValueError("--version is required")

    repo_root = Path(__file__).resolve().parents[1]
    designer_dir = repo_root / "designer-client"
    if not designer_dir.exists():
        raise FileNotFoundError(f"Missing designer-client directory: {designer_dir}")

    output_dir = (repo_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_dir = output_dir / "_designer_stage"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    (stage_dir / "release_version.txt").write_text(f"{version}\n", encoding="ascii")

    target_designer = stage_dir / "designer-client"
    shutil.copytree(designer_dir, target_designer)
    pycache = target_designer / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)

    launcher_bat = stage_dir / "start_designer_client.bat"
    launcher_bat.write_text(
        "@echo off\r\n"
        "setlocal\r\n"
        "cd /d %~dp0\r\n"
        "python designer-client\\designer_tool.py\r\n",
        encoding="ascii",
    )

    artifact_base = f"AmbitionsOfPeace-designer-client-win-x64-{version}"
    zip_name = f"{artifact_base}.zip"
    zip_path = output_dir / zip_name
    manifest_path = output_dir / f"{artifact_base}.manifest.json"
    checksum_path = output_dir / f"{artifact_base}.sha256"

    deterministic_zip_from_dir(stage_dir, zip_path)
    manifest = build_manifest(stage_dir, version, zip_name)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_path.write_text(f"{file_sha256(zip_path)}  {zip_name}\n", encoding="utf-8")

    shutil.rmtree(stage_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
