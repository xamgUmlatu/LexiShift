#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from lexishift_core.frequency.sqlite import ParseConfig, convert_frequency_to_sqlite


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
    args = parser.parse_args()

    config = ParseConfig(
        delimiter=args.delimiter,
        header_starts_with=args.header_starts_with,
        skip_prefixes=tuple(args.skip_prefix),
    )
    convert_frequency_to_sqlite(
        args.input,
        args.output,
        table=args.table,
        overwrite=args.overwrite,
        config=config,
        index_column=args.index_column,
    )


if __name__ == "__main__":
    main()
