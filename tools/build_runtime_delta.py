#!/usr/bin/env python3
"""Build a deterministic file-level runtime delta package between two client zips."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
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


def extract_zip(zip_path: Path, destination: Path) -> None:
    with ZipFile(zip_path, "r") as archive:
        archive.extractall(destination)


def collect_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(root).as_posix()
        hashes[relative] = file_sha256(file_path)
    return hashes


def deterministic_zip_from_dir(source_dir: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, "w") as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(source_dir).as_posix()
            info = ZipInfo(filename=arcname, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, file_path.read_bytes())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build file-level runtime delta package.")
    parser.add_argument("--from-version", required=True)
    parser.add_argument("--to-version", required=True)
    parser.add_argument("--from-zip", required=True)
    parser.add_argument("--to-zip", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    from_version = args.from_version.strip()
    to_version = args.to_version.strip()
    if not from_version or not to_version:
        raise ValueError("from/to version are required")

    from_zip = Path(args.from_zip).resolve()
    to_zip = Path(args.to_zip).resolve()
    if not from_zip.exists():
        raise FileNotFoundError(f"Missing from zip: {from_zip}")
    if not to_zip.exists():
        raise FileNotFoundError(f"Missing to zip: {to_zip}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_base = f"AmbitionsOfPeace-client-delta-{to_version}-from-{from_version}"
    delta_zip = output_dir / f"{artifact_base}.zip"
    delta_sha = output_dir / f"{artifact_base}.sha256"

    with tempfile.TemporaryDirectory(prefix="aop-delta-build-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        from_dir = temp_dir / "from"
        to_dir = temp_dir / "to"
        stage_dir = temp_dir / "stage"
        from_dir.mkdir(parents=True)
        to_dir.mkdir(parents=True)
        stage_dir.mkdir(parents=True)

        extract_zip(from_zip, from_dir)
        extract_zip(to_zip, to_dir)

        from_hashes = collect_hashes(from_dir)
        to_hashes = collect_hashes(to_dir)

        changed_paths = [path for path, digest in to_hashes.items() if from_hashes.get(path) != digest]
        removed_paths = sorted(path for path in from_hashes.keys() if path not in to_hashes)

        for relative in changed_paths:
            source = to_dir / relative
            destination = stage_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        delta_manifest = {
            "schema_version": 1,
            "from_version": from_version,
            "to_version": to_version,
            "changed_files": sorted(changed_paths),
            "removed_files": removed_paths,
        }
        (stage_dir / "delta_manifest.json").write_text(
            json.dumps(delta_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        deterministic_zip_from_dir(stage_dir, delta_zip)

    delta_sha.write_text(f"{file_sha256(delta_zip)}  {delta_zip.name}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
