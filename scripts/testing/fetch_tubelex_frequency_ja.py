#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import lzma
import os
from pathlib import Path
import sys
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[2]


PACK_ID = "freq-ja-tubelex"
SOURCE_REPO = "https://github.com/naist-nlp/tubelex"
RAW_ROOT = "https://raw.githubusercontent.com/naist-nlp/tubelex/main/frequencies"
DEFAULT_VARIANTS = ("lemma-pos",)
VARIANTS = {
    "surface": "tubelex-ja.tsv.xz",
    "lemma-pos": "tubelex-ja-lemma-pos.tsv.xz",
    "base-pos": "tubelex-ja-base-pos.tsv.xz",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch local TUBELEX Japanese frequency sidecar files for learner-"
            "difficulty research. This does not modify production frequency packs."
        )
    )
    parser.add_argument(
        "--variant",
        action="append",
        choices=sorted(VARIANTS),
        help=(
            "Variant to fetch. Repeat for multiple variants. Defaults to lemma-pos "
            "unless --all is used."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch surface, lemma-pos, and base-pos Japanese frequency variants.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to the local LexiShift frequency_packs/freq-ja-tubelex.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even when they already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_dir = _resolve_output_dir(args.output_dir)
    variants = _resolve_variants(args.variant, all_variants=bool(args.all))
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for variant in variants:
        filename = VARIANTS[variant]
        url = f"{RAW_ROOT}/{filename}"
        path = output_dir / filename
        status = _download(url=url, path=path, force=bool(args.force))
        _validate_tubelex_file(path)
        files.append(
            {
                "variant": variant,
                "filename": filename,
                "url": url,
                "path": str(path),
                "status": status,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )

    metadata = _metadata_payload(output_dir=output_dir, files=files)
    (output_dir / "manifest.json").write_text(
        json.dumps(metadata["manifest"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "provenance.json").write_text(
        json.dumps(metadata["provenance"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote TUBELEX Japanese frequency sidecar to {output_dir}")
    for file_record in files:
        print(
            f"- {file_record['filename']}: {file_record['status']} sha256={file_record['sha256']}"
        )
    return 0


def _resolve_output_dir(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID


def _resolve_data_root() -> Path:
    override = os.environ.get("LEXISHIFT_DATA_DIR")
    if override:
        root = Path(override)
    else:
        home = Path.home()
        if sys.platform == "darwin":
            root = home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
        elif sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
            root = Path(base) / "LexiShift" / "LexiShift"
        else:
            root = home / ".local" / "share" / "LexiShift" / "LexiShift"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_variants(
    values: list[str] | None,
    *,
    all_variants: bool,
) -> tuple[str, ...]:
    if all_variants:
        return tuple(VARIANTS)
    if values:
        return tuple(dict.fromkeys(values))
    return DEFAULT_VARIANTS


def _download(*, url: str, path: Path, force: bool) -> str:
    if path.exists() and not force:
        return "exists"
    temporary = path.with_suffix(path.suffix + ".tmp")
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    temporary.write_bytes(data)
    temporary.replace(path)
    return "downloaded"


def _validate_tubelex_file(path: Path) -> None:
    _raise_csv_field_size_limit()
    with lzma.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = set(reader.fieldnames or ())
        missing = {"word", "count", "videos", "channels"} - fields
        if missing:
            raise ValueError(f"{path} is missing TUBELEX columns: {sorted(missing)}")
        first = next(reader, None)
        if not first or not str(first.get("word") or "").strip():
            raise ValueError(f"{path} did not contain frequency rows")


def _raise_csv_field_size_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)


def _metadata_payload(
    *,
    output_dir: Path,
    files: list[dict[str, object]],
) -> dict[str, object]:
    now = _utc_now()
    default_file = VARIANTS["lemma-pos"]
    return {
        "manifest": {
            "pack_id": PACK_ID,
            "pack_kind": "frequency_sidecar",
            "provider": "naist-nlp/tubelex",
            "local_kind": "file",
            "artifact_relpath": default_file,
            "artifact_kind": "tsv.xz",
            "installed_at_utc": now,
            "raw_retained": True,
            "variants": [
                {
                    "variant": file_record["variant"],
                    "artifact_relpath": file_record["filename"],
                    "artifact_kind": "tsv.xz",
                    "sha256": file_record["sha256"],
                }
                for file_record in files
            ],
        },
        "provenance": {
            "schema_version": 1,
            "pack_id": PACK_ID,
            "pack_kind": "frequency_sidecar",
            "provider": "naist-nlp/tubelex",
            "installed_at_utc": now,
            "output_dir": str(output_dir),
            "source": {
                "source_name": "TUBELEX",
                "source_url": SOURCE_REPO,
                "source_version": "main/frequencies",
                "license": "BSD-3-Clause",
                "license_url": f"{SOURCE_REPO}/blob/main/LICENSE",
                "notes": (
                    "Frequency lists are local research sidecars; the full corpus "
                    "text is not redistributed here."
                ),
            },
            "raw_artifacts": files,
        },
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
