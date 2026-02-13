#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


XML_LANG_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
SQLITE_MAGIC = b"SQLite format 3"


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


def _safe_extract_tar(archive: tarfile.TarFile, target_dir: Path) -> None:
    target_abs = target_dir.resolve()
    for member in archive.getmembers():
        member_path = (target_dir / member.name).resolve()
        if os.path.commonpath([str(target_abs), str(member_path)]) != str(target_abs):
            raise ValueError(f"Unsafe tar member path: {member.name}")
    archive.extractall(target_dir)


def _iter_tei_candidates(root: Path) -> Iterable[Path]:
    for candidate in root.rglob("*.tei"):
        if candidate.is_file():
            yield candidate


def _resolve_tei_path(input_path: Path, tei_filename: str = "") -> tuple[Path, Path | None]:
    if input_path.is_file() and input_path.suffix.lower() in {".tei", ".xml"}:
        return input_path, None
    if input_path.is_dir():
        return _find_tei_in_dir(input_path, tei_filename=tei_filename), None
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    name = input_path.name.lower()
    if name.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz", ".tar")):
        temp_dir = Path(tempfile.mkdtemp(prefix="freedict-convert-"))
        with tarfile.open(input_path, "r:*") as archive:
            _safe_extract_tar(archive, temp_dir)
        tei_path = _find_tei_in_dir(temp_dir, tei_filename=tei_filename)
        return tei_path, temp_dir
    raise ValueError(
        "Input must be a .tei/.xml file, a directory containing TEI, or a .tar archive."
    )


def _find_tei_in_dir(root: Path, tei_filename: str = "") -> Path:
    if tei_filename:
        for candidate in root.rglob(tei_filename):
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            f"Could not find expected TEI file '{tei_filename}' under: {root}"
        )
    candidates = list(_iter_tei_candidates(root))
    if not candidates:
        raise FileNotFoundError(f"No .tei files found under: {root}")
    if len(candidates) > 1:
        listed = "\n".join(str(path) for path in sorted(candidates)[:10])
        raise ValueError(
            "Multiple .tei files found. Pass --tei-filename to disambiguate.\n"
            f"{listed}"
        )
    return candidates[0]


def _init_db(output_path: Path, *, overwrite: bool) -> sqlite3.Connection:
    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output_path}")
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
    conn.execute(
        "CREATE TABLE entries ("
        "headword TEXT NOT NULL, "
        "headword_lc TEXT NOT NULL, "
        "translation TEXT NOT NULL, "
        "translation_lc TEXT NOT NULL, "
        "rank INTEGER NOT NULL, "
        "pos TEXT, "
        "entry_ord INTEGER NOT NULL, "
        "gloss_ord INTEGER NOT NULL, "
        "PRIMARY KEY (headword_lc, translation_lc)"
        ");"
    )
    conn.execute("CREATE INDEX idx_entries_headword ON entries(headword);")
    conn.execute("CREATE INDEX idx_entries_headword_lc_rank ON entries(headword_lc, rank);")
    conn.execute("CREATE INDEX idx_entries_translation_lc ON entries(translation_lc);")
    return conn


def _collect_unique_texts(nodes: Iterable[ElementTree.Element]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for node in nodes:
        text = (node.text or "").strip()
        if not text or text in seen:
            continue
        out.append(text)
        seen.add(text)
    return out


def _collect_translations(elem: ElementTree.Element, *, target_lang: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for quote in elem.findall(".//tei:cit[@type='trans']/tei:quote", TEI_NS):
        text = (quote.text or "").strip()
        if not text:
            continue
        lang = (quote.get(XML_LANG_KEY) or "").strip().lower()
        if target_lang and lang and lang != target_lang:
            continue
        if text in seen:
            continue
        out.append(text)
        seen.add(text)
    return out


def convert_freedict_tei_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    target_lang: str = "",
    tei_filename: str = "",
    overwrite: bool = False,
    batch_size: int = 5000,
) -> dict[str, int | str]:
    resolved_target_lang = target_lang.strip().lower()
    tei_path, temp_dir = _resolve_tei_path(input_path, tei_filename=tei_filename.strip())
    conn = _init_db(output_path, overwrite=overwrite)
    batch: list[tuple[object, ...]] = []
    next_rank_by_headword: dict[str, int] = {}
    seen_pairs: set[tuple[str, str]] = set()
    pair_count = 0
    entry_count = 0
    try:
        context = ElementTree.iterparse(tei_path, events=("end",))
        entry_tag = f"{{{TEI_NS['tei']}}}entry"
        for _event, elem in context:
            if elem.tag != entry_tag:
                continue
            entry_count += 1
            headwords = _collect_unique_texts(elem.findall("tei:form/tei:orth", TEI_NS))
            if not headwords:
                elem.clear()
                continue
            translations = _collect_translations(elem, target_lang=resolved_target_lang)
            if not translations:
                elem.clear()
                continue
            pos_values = _collect_unique_texts(elem.findall(".//tei:gramGrp/tei:pos", TEI_NS))
            pos_text = "|".join(pos_values) if pos_values else ""
            for headword in headwords:
                headword_lc = headword.lower()
                next_rank = next_rank_by_headword.get(headword_lc, 0)
                for gloss_ord, translation in enumerate(translations):
                    translation_lc = translation.lower()
                    key = (headword_lc, translation_lc)
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    next_rank += 1
                    batch.append(
                        (
                            headword,
                            headword_lc,
                            translation,
                            translation_lc,
                            next_rank,
                            pos_text,
                            entry_count,
                            gloss_ord,
                        )
                    )
                    pair_count += 1
                    if len(batch) >= batch_size:
                        conn.executemany(
                            "INSERT OR IGNORE INTO entries "
                            "(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            batch,
                        )
                        conn.commit()
                        batch.clear()
                next_rank_by_headword[headword_lc] = next_rank
            elem.clear()
        if batch:
            conn.executemany(
                "INSERT OR IGNORE INTO entries "
                "(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                batch,
            )
            conn.commit()
            batch.clear()
        metadata = {
            "schema_version": 1,
            "source_file": str(input_path),
            "resolved_tei_path": str(tei_path),
            "target_lang": resolved_target_lang,
            "entry_count_scanned": entry_count,
            "headword_count": len(next_rank_by_headword),
            "pair_count": pair_count,
            "generated_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps(metadata, sort_keys=True)),
        )
        conn.commit()
        return metadata
    finally:
        conn.close()
        if temp_dir is not None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def _is_sqlite(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            return handle.read(16).startswith(SQLITE_MAGIC)
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
