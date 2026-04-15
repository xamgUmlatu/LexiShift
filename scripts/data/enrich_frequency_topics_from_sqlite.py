#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SQLITE_MODULE_PATH = CORE_ROOT / "lexishift_core" / "frequency" / "sqlite.py"
SQLITE_SPEC = importlib.util.spec_from_file_location(
    "lexishift_frequency_sqlite_cli", SQLITE_MODULE_PATH
)
if SQLITE_SPEC is None or SQLITE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load frequency sqlite module: {SQLITE_MODULE_PATH}")
SQLITE_MODULE = importlib.util.module_from_spec(SQLITE_SPEC)
sys.modules[SQLITE_SPEC.name] = SQLITE_MODULE
SQLITE_SPEC.loader.exec_module(SQLITE_MODULE)

TopicEnrichmentConfig = SQLITE_MODULE.TopicEnrichmentConfig  # type: ignore[attr-defined]
enrich_frequency_sqlite_topics = SQLITE_MODULE.enrich_frequency_sqlite_topics  # type: ignore[attr-defined]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich an existing frequency SQLite with topic metadata from a companion SQLite."
    )
    parser.add_argument("frequency_db", type=Path, help="Path to the target frequency SQLite")
    parser.add_argument("topic_source_sqlite", type=Path, help="Path to the source topic SQLite")
    parser.add_argument("--table", default="frequency", help="Target frequency table name")
    parser.add_argument(
        "--source-provider",
        default="",
        help="Optional source provider label for metadata/logging",
    )
    parser.add_argument(
        "--target-topic-column",
        default="sense_topics",
        help="Target topic column to create/update (default: sense_topics)",
    )
    parser.add_argument(
        "--max-topics-per-lemma",
        type=int,
        default=24,
        help="Maximum number of topics to persist per lemma",
    )
    args = parser.parse_args()

    metadata = enrich_frequency_sqlite_topics(
        args.frequency_db,
        table=args.table,
        enrichment=TopicEnrichmentConfig(
            source_sqlite_path=args.topic_source_sqlite,
            source_provider=str(args.source_provider or args.topic_source_sqlite.stem),
            target_topic_column=args.target_topic_column,
            max_topics_per_lemma=max(1, int(args.max_topics_per_lemma)),
        ),
    )
    print(json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
