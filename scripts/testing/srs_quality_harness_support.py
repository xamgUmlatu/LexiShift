from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from typing import Any, Mapping
from xml.sax.saxutils import escape

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.replacement.core import VocabRule


def _alpha_suffix(index: int) -> str:
    value = max(0, int(index))
    chars: list[str] = []
    for _ in range(3):
        chars.append(chr(ord("a") + (value % 26)))
        value //= 26
    return "".join(reversed(chars))


def _build_tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{_alpha_suffix(i)}" for i in range(max(0, int(count)))]


def _write_frequency_db(*, path: Path, lemmas: list[str], pos: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TABLE IF EXISTS frequency;")
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL, pos TEXT);")
        rows = [
            (lemma, float(index + 1), float(len(lemmas) - index), pos)
            for index, lemma in enumerate(lemmas)
        ]
        conn.executemany(
            "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def _write_jmdict(path: Path, *, targets: list[str], sources: list[str]) -> None:
    entries: list[str] = []
    for target, source in zip(targets, sources):
        entries.append(
            "<entry>"
            f"<k_ele><keb>{escape(target)}</keb></k_ele>"
            f"<r_ele><reb>{escape(target)}</reb></r_ele>"
            f"<sense><gloss>{escape(source)}</gloss></sense>"
            "</entry>"
        )
    payload = "<JMdict>" + "".join(entries) + "</JMdict>"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_freedict_de_en(path: Path, *, targets: list[str], sources: list[str]) -> None:
    entries: list[str] = []
    for target, source in zip(targets, sources):
        entries.append(
            "<entry>"
            f"<form><orth>{escape(target)}</orth></form>"
            "<sense>"
            f"<cit type='trans'><quote xml:lang='en'>{escape(source)}</quote></cit>"
            "</sense>"
            "</entry>"
        )
    payload = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<TEI xmlns='http://www.tei-c.org/ns/1.0'>"
        "<text><body>" + "".join(entries) + "</body></text>"
        "</TEI>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_placeholder_sqlite(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT, value TEXT)")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("source", "synthetic_srs_quality_harness"),
        )
        conn.commit()
    finally:
        conn.close()


def _load_ruleset_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Ruleset payload must be an object: {path}")
    return payload


def _load_snapshot_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Snapshot payload must be an object: {path}")
    return payload


def ruleset_unique_target_count(path: Path) -> int:
    payload = _load_ruleset_payload(path)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        return 0
    replacements = {
        str(rule.get("replacement") or "").strip()
        for rule in rules
        if isinstance(rule, Mapping) and str(rule.get("replacement") or "").strip()
    }
    return len(replacements)


def snapshot_target_count(path: Path) -> int:
    payload = _load_snapshot_payload(path)
    stats = payload.get("stats")
    if isinstance(stats, Mapping) and stats.get("target_count") is not None:
        return int(stats.get("target_count") or 0)
    targets = payload.get("targets", [])
    return len(targets) if isinstance(targets, list) else 0


def build_seed_candidates() -> list[SimpleNamespace]:
    specs = [
        ("alpha", 0.95, "noun", 1.00),
        ("beta", 0.90, "noun", 1.00),
        ("gamma", 0.84, "adjective", 0.85),
        ("delta", 0.78, "verb", 0.70),
        ("epsilon", 0.73, "adverb", 0.55),
        ("zeta", 0.68, "other", 0.40),
    ]
    candidates: list[SimpleNamespace] = []
    for index, (lemma, base_weight, bucket, pos_weight) in enumerate(specs):
        candidates.append(
            SimpleNamespace(
                lemma=lemma,
                language_pair="en-ja",
                core_rank=float(index + 1),
                pos=f"{bucket}-tag",
                pos_bucket=bucket,
                pos_weight=pos_weight,
                pmw=100.0 - (index * 5.0),
                base_weight=base_weight,
                admission_weight=round(base_weight * pos_weight, 6),
                metadata={},
            )
        )
    return candidates


def create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE frequency (lemma TEXT, core_rank REAL, pmw REAL)")
        conn.execute(
            "INSERT INTO frequency (lemma, core_rank, pmw) VALUES (?, ?, ?)",
            ("alpha", 1.0, 100.0),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def stub_run_rulegen_for_pair(*, store, pair, **_kwargs):
    pair_lemmas = sorted({item.lemma for item in store.items if item.language_pair == pair})
    rules = tuple(
        VocabRule(source_phrase=f"src_{lemma}", replacement=lemma) for lemma in pair_lemmas
    )
    snapshot_targets = [{"lemma": lemma, "sources": [f"src_{lemma}"]} for lemma in pair_lemmas]
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": snapshot_targets,
        "stats": {
            "target_count": len(pair_lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(rules=rules, snapshot=snapshot, target_count=len(pair_lemmas))


def build_pair_resources(paths: HelperPaths, *, pair: str) -> None:
    if pair == "en-ja":
        targets = _build_tokens("ja", 70)
        sources = _build_tokens("eng", 70)
        _write_frequency_db(
            path=paths.frequency_packs_dir / "freq-ja-bccwj.sqlite",
            lemmas=targets,
            pos="名詞-普通名詞-一般",
        )
        _write_jmdict(paths.language_packs_dir / "JMdict_e", targets=targets, sources=sources)
        _write_placeholder_sqlite(paths.language_packs_dir / "wiktionary-ja-en.sqlite")
        return
    if pair == "en-de":
        targets = _build_tokens("de", 70)
        sources = _build_tokens("eng", 70)
        _write_frequency_db(
            path=paths.frequency_packs_dir / "freq-de-default.sqlite",
            lemmas=targets,
            pos="SUB:NOM:SIN:NEU",
        )
        _write_freedict_de_en(
            paths.language_packs_dir / "deu-eng.tei",
            targets=targets,
            sources=sources,
        )
        return
    raise ValueError(f"Unsupported synthetic SRS pair: {pair}")
