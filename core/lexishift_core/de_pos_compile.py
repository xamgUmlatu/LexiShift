#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import unicodedata

TOKEN_ALLOWED = re.compile(
    r"^[A-Za-z\u00C4\u00D6\u00DC\u00E4\u00F6\u00FC\u00DF]"
    r"[A-Za-z\u00C4\u00D6\u00DC\u00E4\u00F6\u00FC\u00DF'-]*$"
)
TRIM_PUNCT = ".,;:!?\"`~^()[]{}<>|/\\"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile german-pos-dict into compact lemma->tagset TSV "
            "(lemma<TAB>TAG1|TAG2|...)."
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to german-pos-dict.txt")
    parser.add_argument("--output", type=Path, required=True, help="Output TSV path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")
    return parser.parse_args()


def normalize_token(value: str) -> str:
    token = unicodedata.normalize("NFC", str(value or "")).strip()
    token = token.replace("\u2019", "'").replace("\u2018", "'")
    token = token.replace("\u2013", "-").replace("\u2014", "-")
    token = token.strip(TRIM_PUNCT)
    token = token.strip("-'")
    if not token:
        return ""
    if any(ch.isdigit() for ch in token):
        return ""
    if not TOKEN_ALLOWED.fullmatch(token):
        return ""
    normalized = token.lower()
    if not any(ch.isalpha() for ch in normalized):
        return ""
    return normalized


def normalize_tag(value: str) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


def strip_inline_comment(line: str) -> str:
    if " -- " in line:
        return line.split(" -- ", 1)[0].rstrip()
    return line


def compile_pos(input_path: Path) -> tuple[dict[str, set[str]], int]:
    tags_by_lemma: dict[str, set[str]] = defaultdict(set)
    rows = 0
    with input_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = strip_inline_comment(raw.strip())
            if not line:
                continue
            parts = [part.strip() for part in line.split("\t")]
            if len(parts) < 3:
                continue
            lemma = normalize_token(parts[1])
            tag = normalize_tag(parts[2])
            if not lemma or not tag:
                continue
            tags_by_lemma[lemma].add(tag)
            rows += 1
    return dict(tags_by_lemma), rows


def write_compact_pos_lexicon(
    *,
    input_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> tuple[int, int]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output exists: {output_path}")
    if output_path.exists():
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mapping, row_count = compile_pos(input_path)
    with output_path.open("w", encoding="utf-8") as handle:
        for lemma in sorted(mapping.keys()):
            tags = "|".join(sorted(mapping[lemma]))
            handle.write(f"{lemma}\t{tags}\n")
    return row_count, len(mapping)


def main() -> None:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    row_count, lemma_count = write_compact_pos_lexicon(
        input_path=input_path,
        output_path=output_path,
        overwrite=bool(args.overwrite),
    )

    print(f"Compiled: {output_path}")
    print(f"Rows consumed: {row_count:,}")
    print(f"Lemmas written: {lemma_count:,}")


if __name__ == "__main__":
    main()
