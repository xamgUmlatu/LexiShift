#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve().with_name("convert_kaikki_glosses_to_sqlite.py")


def main(argv: list[str]) -> int:
    command = [
        sys.executable,
        str(SCRIPT),
        *argv,
        "--source-lang-code",
        "ja",
        "--gloss-language",
        "en",
        "--source-provider",
        "wiktionary-ja-en",
        "--source-dump",
        "enwiktionary",
    ]
    result = subprocess.run(command, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
