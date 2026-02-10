#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from lexishift_core.frequency.sqlite import ParseConfig, convert_frequency_to_sqlite


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert BCCWJ SUW frequency list to SQLite.")
    parser.add_argument("input", type=Path, help="Path to BCCWJ SUW TSV file")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument("--table", default="frequency", help="Table name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if exists")
    parser.add_argument("--index-column", default="lemma", help="Column name to index")
    args = parser.parse_args()

    config = ParseConfig(
        delimiter="\t",
        header_starts_with="rank",
        skip_prefixes=(),
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
