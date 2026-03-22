#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if CORE_ROOT.exists():
    core_path = str(CORE_ROOT)
    if core_path not in sys.path:
        sys.path.insert(0, core_path)

from lexishift_core.resources.kaikki_sqlite import convert_kaikki_translations_to_sqlite  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Kaikki/Wiktextract translation boxes to a compatibility SQLite dictionary."
    )
    parser.add_argument("input", type=Path, help="Path to Kaikki JSONL or JSONL.GZ")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument(
        "--source-lang-code",
        default="en",
        help="Language code to keep from the Kaikki dump (default: en)",
    )
    parser.add_argument(
        "--target-lang-code",
        default="es",
        help="Translation target language code to keep (default: es)",
    )
    parser.add_argument(
        "--translation-language",
        default="es",
        help="Metadata label for translation language (default: es)",
    )
    parser.add_argument(
        "--source-provider",
        default="kaikki",
        help="Metadata label for source provider (default: kaikki)",
    )
    parser.add_argument(
        "--source-dump",
        default="enwiktionary",
        help="Metadata label for source dump (default: enwiktionary)",
    )
    parser.add_argument("--batch", type=int, default=1000, help="Insert batch size")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    metadata = convert_kaikki_translations_to_sqlite(
        args.input,
        args.output,
        source_lang_code=args.source_lang_code,
        target_lang_code=args.target_lang_code,
        translation_language=args.translation_language,
        source_provider=args.source_provider,
        source_dump=args.source_dump,
        overwrite=args.overwrite,
        batch_size=args.batch,
    )
    print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
