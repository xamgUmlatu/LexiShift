#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from convert_freedict_tei_to_sqlite import convert_freedict_tei_to_sqlite


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert FreeDict English->Spanish resource to SQLite."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to eng-spa.tei, directory, or freedict-eng-spa-*.src.tar.xz",
    )
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument("--batch", type=int, default=5000, help="Insert batch size")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if exists")
    args = parser.parse_args()

    convert_freedict_tei_to_sqlite(
        args.input,
        args.output,
        target_lang="es",
        tei_filename="eng-spa.tei",
        overwrite=args.overwrite,
        batch_size=max(100, int(args.batch)),
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
