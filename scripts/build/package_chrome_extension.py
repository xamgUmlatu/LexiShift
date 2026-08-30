#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "apps" / "chrome-extension"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "dist" / "cws"
EXCLUDED_RELATIVE_PATHS = {PurePosixPath("README.md")}
PACKAGE_NOISE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
CHROME_VERSION_RE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,3}")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _read_manifest(source_root: Path) -> dict[str, object]:
    manifest_path = source_root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Chrome extension manifest is missing: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Chrome extension manifest must contain a JSON object.")
    return payload


def _validated_version(manifest: dict[str, object]) -> str:
    version = str(manifest.get("version", "")).strip()
    if not CHROME_VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid Chrome extension version: {version!r}")
    parts = [int(part) for part in version.split(".")]
    if any(part > 65535 for part in parts):
        raise ValueError(f"Chrome extension version component exceeds 65535: {version}")
    return version


def _package_files(source_root: Path) -> list[tuple[Path, PurePosixPath]]:
    files: list[tuple[Path, PurePosixPath]] = []
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in the extension package: {path}")
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(source_root).as_posix())
        if path.name in PACKAGE_NOISE_NAMES:
            raise ValueError(f"Package noise found in extension source: {relative}")
        if relative in EXCLUDED_RELATIVE_PATHS:
            continue
        files.append((path, relative))
    if not files:
        raise ValueError(f"No extension files found under {source_root}")
    return files


def _write_deterministic_zip(
    files: list[tuple[Path, PurePosixPath]], output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for source_path, relative in files:
                info = zipfile.ZipInfo(str(relative), date_time=ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source_path.read_bytes())
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _validate_archive(
    output_path: Path,
    expected_files: list[tuple[Path, PurePosixPath]],
    expected_version: str,
) -> None:
    expected_names = [str(relative) for _source, relative in expected_files]
    with zipfile.ZipFile(output_path) as archive:
        actual_names = archive.namelist()
        if actual_names != expected_names:
            raise ValueError("Packaged archive contents differ from the selected source files.")
        if "manifest.json" not in actual_names:
            raise ValueError("Packaged archive does not contain manifest.json at its root.")
        for name in actual_names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe path in packaged archive: {name}")
        manifest = json.loads(archive.read("manifest.json"))
    if str(manifest.get("version", "")).strip() != expected_version:
        raise ValueError("Packaged manifest version does not match the release version.")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_package(
    source_root: Path,
    output_path: Path,
    *,
    expected_version: str | None = None,
) -> tuple[str, int]:
    manifest = _read_manifest(source_root)
    version = _validated_version(manifest)
    if expected_version is not None and version != expected_version:
        raise ValueError(
            f"Manifest version {version} does not match requested version {expected_version}."
        )
    files = _package_files(source_root)
    _write_deterministic_zip(files, output_path)
    _validate_archive(output_path, files, version)
    digest = sha256_file(output_path)
    checksum_path = output_path.with_suffix(f"{output_path.suffix}.sha256")
    checksum_path.write_text(f"{digest}  {output_path.name}\n", encoding="utf-8")
    return digest, len(files)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic Chrome Web Store upload ZIP."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Chrome extension source directory.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output ZIP path. Defaults to dist/cws using the manifest version.",
    )
    parser.add_argument(
        "--version",
        help="Require an exact manifest version before packaging.",
    )
    args = parser.parse_args()

    source_root = args.source.expanduser().resolve()
    manifest = _read_manifest(source_root)
    version = _validated_version(manifest)
    output_path = (
        args.out.expanduser().resolve()
        if args.out
        else DEFAULT_OUTPUT_ROOT / f"lexishift-chrome-extension-{version}-beta.zip"
    )
    digest, file_count = build_package(
        source_root,
        output_path,
        expected_version=args.version,
    )
    print(f"CWS ZIP: {output_path}")
    print(f"Version: {version}")
    print(f"Files: {file_count}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
