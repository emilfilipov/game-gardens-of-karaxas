#!/usr/bin/env python3
"""Build a deterministic Windows client-app release bundle + manifest."""

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


def add_tree(source_root: Path, dest_root: Path) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"Missing source directory: {source_root}")
    for source_path in sorted(source_root.rglob("*")):
        if not source_path.is_file():
            continue
        relative = source_path.relative_to(source_root)
        destination = dest_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)


def deterministic_zip_from_dir(source_dir: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, "w") as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(source_dir).as_posix()
            info = ZipInfo(filename=arcname, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            data = file_path.read_bytes()
            archive.writestr(info, data)


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
        "entrypoint": "bin/AmbitionsOfPeaceClient.exe",
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Windows client-app runtime for release.")
    parser.add_argument("--version", required=True, help="Release version (e.g. 1.0.123)")
    parser.add_argument("--exe", required=True, help="Path to compiled Windows client-app executable.")
    parser.add_argument("--output-dir", default="releases/windows", help="Artifact output directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = args.version.strip()
    if not version:
        raise ValueError("--version is required")

    executable = Path(args.exe).resolve()
    if not executable.exists():
        raise FileNotFoundError(f"Missing executable: {executable}")

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = (repo_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_dir = output_dir / "_client_app_stage"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    (stage_dir / "release_version.txt").write_text(f"{version}\n", encoding="ascii")

    bin_dir = stage_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(executable, bin_dir / "AmbitionsOfPeaceClient.exe")

    add_tree(repo_root / "client-app" / "assets", stage_dir / "client-app" / "assets")
    add_tree(repo_root / "assets" / "content" / "provinces", stage_dir / "assets" / "content" / "provinces")

    artifact_base = f"AmbitionsOfPeace-client-app-win-x64-{version}"
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
