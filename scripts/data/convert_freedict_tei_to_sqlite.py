#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if CORE_ROOT.exists():
    core_path = str(CORE_ROOT)
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

from lexishift_core.resources.freedict_sqlite import convert_freedict_tei_to_sqlite  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert FreeDict TEI (or source archive/dir containing TEI) to SQLite."
    )
    parser.add_argument("input", type=Path, help="Path to .tei, directory, or .tar.* archive")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument(
        "--target-lang",
        default="",
        help="Filter translation quote xml:lang (e.g., en, es). Empty means no filter.",
    )
    parser.add_argument(
        "--tei-filename",
        default="",
        help="Expected TEI filename inside directory/archive (e.g., spa-eng.tei).",
    )
    parser.add_argument("--batch", type=int, default=5000, help="Insert batch size")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")
    return parser.parse_args()


def _is_sqlite(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(16).startswith(b"SQLite format 3")
    except OSError:
        return False


def main() -> int:
    args = _parse_args()
    metadata = convert_freedict_tei_to_sqlite(
        args.input,
        args.output,
        target_lang=args.target_lang,
        tei_filename=args.tei_filename,
        overwrite=args.overwrite,
        batch_size=max(100, int(args.batch)),
    )
    if not _is_sqlite(args.output):
        raise RuntimeError(f"Output is not a valid SQLite file: {args.output}")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
