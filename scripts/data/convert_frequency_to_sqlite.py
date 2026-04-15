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


DEFAULT_SKIP_PREFIXES = ("*", "-----")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a frequency list to SQLite.")
    parser.add_argument("input", type=Path, help="Path to frequency list file")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument("--table", default="frequency", help="Table name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if exists")
    parser.add_argument("--index-column", default="lemma", help="Column name to index")
    parser.add_argument("--delimiter", default="\t", help="Delimiter (default: tab)")
    parser.add_argument(
        "--header-starts-with",
        default="rank",
        help="Header row must start with this token",
    )
    parser.add_argument(
        "--skip-prefix",
        action="append",
        default=list(DEFAULT_SKIP_PREFIXES),
        help="Line prefix to skip (can be repeated)",
    )
    parser.add_argument(
        "--pos-provider",
        default="",
        help="Optional POS source provider ID for unknown-tag inventory",
    )
    parser.add_argument(
        "--pos-profile",
        default="",
        help="Optional POS source profile (for example: bccwj, freq-es-cde)",
    )
    parser.add_argument(
        "--pos-kind",
        default="frequency",
        help="Optional POS source kind (default: frequency)",
    )
    parser.add_argument(
        "--pos-column",
        action="append",
        default=[],
        help="POS column name to inventory (repeatable; default: pos,wtype when POS inventory is enabled)",
    )
    parser.add_argument(
        "--topic-source-sqlite",
        type=Path,
        default=None,
        help="Optional companion SQLite with sense_glosses.topics_json to enrich the frequency pack.",
    )
    parser.add_argument(
        "--topic-source-provider",
        default="",
        help="Optional provider label for topic enrichment metadata.",
    )
    args = parser.parse_args()

    config = ParseConfig(
        delimiter=args.delimiter,
        header_starts_with=args.header_starts_with,
        skip_prefixes=tuple(args.skip_prefix),
    )
    pos_inventory: PosInventoryConfig | None = None
    if args.pos_provider or args.pos_profile or args.pos_column:
        pos_columns = tuple(args.pos_column) if args.pos_column else ("pos", "wtype")
        pos_inventory = PosInventoryConfig(
            source_provider=str(args.pos_provider or ""),
            source_profile=str(args.pos_profile or ""),
            source_kind=str(args.pos_kind or "frequency"),
            pos_columns=pos_columns,
        )
    topic_enrichment: TopicEnrichmentConfig | None = None
    if args.topic_source_sqlite:
        topic_enrichment = TopicEnrichmentConfig(
            source_sqlite_path=args.topic_source_sqlite,
            source_provider=str(args.topic_source_provider or args.topic_source_sqlite.stem),
        )

    metadata = convert_frequency_to_sqlite(
        args.input,
        args.output,
        table=args.table,
        overwrite=args.overwrite,
        config=config,
        index_column=args.index_column,
        pos_inventory=pos_inventory,
        topic_enrichment=topic_enrichment,
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
