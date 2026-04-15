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

from lexishift_core.frequency.sqlite import (  # noqa: E402
    ParseConfig,
    PosInventoryConfig,
    TopicEnrichmentConfig,
    convert_frequency_to_sqlite,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Corpus del Espanol sample frequency list to SQLite."
    )
    parser.add_argument("input", type=Path, help="Path to spanish_lemmas20k.txt")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument("--table", default="frequency", help="Table name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if exists")
    parser.add_argument("--index-column", default="lemma", help="Column name to index")
    parser.add_argument(
        "--topic-source-sqlite",
        type=Path,
        default=None,
        help="Optional companion SQLite with sense_glosses.topics_json for topic enrichment.",
    )
    args = parser.parse_args()

    config = ParseConfig(
        delimiter="\t",
        header_starts_with="ID",
        skip_prefixes=("----",),
        encoding="latin-1",
        errors="strict",
    )
    metadata = convert_frequency_to_sqlite(
        args.input,
        args.output,
        table=args.table,
        overwrite=args.overwrite,
        config=config,
        index_column=args.index_column,
        pos_inventory=PosInventoryConfig(
            source_provider="freq-es-cde",
            source_kind="frequency",
            source_profile="freq-es-cde",
            pos_columns=("pos",),
        ),
        topic_enrichment=(
            TopicEnrichmentConfig(
                source_sqlite_path=args.topic_source_sqlite,
                source_provider=args.topic_source_sqlite.stem,
            )
            if args.topic_source_sqlite
            else None
        ),
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
