#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_reverse_translation_dictionary_path,
    default_translation_dictionary_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.admission_policy import classify_pos_bucket  # noqa: E402
from lexishift_core.srs.topic_overlay import PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP  # noqa: E402


PAIR = "en-de"
DEFAULT_TOP_N = 10000
DEFAULT_SAMPLE_LIMIT = 20
DEFAULT_SOURCE_LABEL = "freq-de-default"
DEFAULT_TOPIC_OVERLAY_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_manual_semantic_lexicon_en_de_latest.json"
)
DEFAULT_LEARNER_SOURCE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_de_latest.json"
)
DEFAULT_WIKTIONARY_METADATA_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_wiktionary_metadata_en_de_latest.json"
)
DEFAULT_EXTERNAL_SOURCE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_external_source_audit_en_de_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_signal_palette_en_de_latest.md"
)

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*", re.UNICODE)
ENGLISH_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "one",
        "or",
        "someone",
        "something",
        "that",
        "the",
        "thing",
        "to",
        "with",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a read-only signal palette for en-de learner-difficulty model design. "
            "This inventories currently available signals; it does not add manual labels "
            "or change production scoring."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--translation-db", type=Path)
    parser.add_argument("--reverse-translation-db", type=Path)
    parser.add_argument("--english-frequency-db", type=Path)
    parser.add_argument("--topic-overlay-json", type=Path, default=DEFAULT_TOPIC_OVERLAY_JSON)
    parser.add_argument("--learner-source-json", type=Path, default=DEFAULT_LEARNER_SOURCE_JSON)
    parser.add_argument(
        "--wiktionary-metadata-json",
        type=Path,
        default=DEFAULT_WIKTIONARY_METADATA_JSON,
    )
    parser.add_argument(
        "--external-source-json",
        type=Path,
        default=DEFAULT_EXTERNAL_SOURCE_JSON,
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--rows-jsonl-out", type=Path)
    parser.add_argument("--include-rows-in-json", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        translation_db=args.translation_db,
        reverse_translation_db=args.reverse_translation_db,
        english_frequency_db=args.english_frequency_db,
        topic_overlay_json=args.topic_overlay_json,
        learner_source_json=args.learner_source_json,
        wiktionary_metadata_json=args.wiktionary_metadata_json,
        external_source_json=args.external_source_json,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        include_rows=bool(args.include_rows_in_json or args.rows_jsonl_out),
    )
    signal_rows = _as_sequence(report.get("signal_rows"))
    if args.rows_jsonl_out:
        args.rows_jsonl_out.parent.mkdir(parents=True, exist_ok=True)
        with args.rows_jsonl_out.open("w", encoding="utf-8") as handle:
            for row in signal_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Wrote row-level signal artifact to {args.rows_jsonl_out}")
    if not args.include_rows_in_json:
        report.pop("signal_rows", None)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    frequency_db: Path | None = None,
    translation_db: Path | None = None,
    reverse_translation_db: Path | None = None,
    english_frequency_db: Path | None = None,
    topic_overlay_json: Path | None = DEFAULT_TOPIC_OVERLAY_JSON,
    learner_source_json: Path | None = DEFAULT_LEARNER_SOURCE_JSON,
    wiktionary_metadata_json: Path | None = DEFAULT_WIKTIONARY_METADATA_JSON,
    external_source_json: Path | None = DEFAULT_EXTERNAL_SOURCE_JSON,
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    include_rows: bool = False,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    paths = build_helper_paths()
    resolved_frequency_db = frequency_db or default_frequency_db_path(
        PAIR,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    resolved_translation_db = translation_db or default_translation_dictionary_path(
        PAIR,
        language_packs_dir=paths.language_packs_dir,
    )
    resolved_reverse_translation_db = (
        reverse_translation_db
        or default_reverse_translation_dictionary_path(
            PAIR,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    resolved_english_frequency_db = (
        english_frequency_db
        or paths.frequency_packs_dir / "freq-en-leipzig-default" / "main.sqlite"
    )

    frequency_rows = _load_frequency_rows(resolved_frequency_db, top_n=top_n)
    topic_by_lemma = _load_topic_overlay(topic_overlay_json)
    learner_source_index = _load_learner_source_index(learner_source_json)
    wiktionary_metadata_index = _load_wiktionary_metadata_index(wiktionary_metadata_json)
    external_source_index = _load_external_source_index(external_source_json)
    translation_entries = _load_translation_entries(
        resolved_translation_db,
        keys=[str(row.get("lemma") or "") for row in frequency_rows],
    )
    english_tokens = sorted(
        {
            token
            for entries in translation_entries.values()
            for entry in entries
            for token in _translation_tokens(str(entry.get("translation") or ""))
        }
    )
    english_frequency = _load_english_frequency(
        resolved_english_frequency_db,
        tokens=english_tokens,
    )
    reverse_support = _load_reverse_support(
        resolved_reverse_translation_db,
        translation_entries=translation_entries,
    )
    max_rank = max((_safe_float(row.get("core_rank")) for row in frequency_rows), default=1.0)
    max_pmw = max((_safe_float(row.get("pmw")) for row in frequency_rows), default=1.0)
    rows = [
        _signal_row(
            row=row,
            max_rank=max_rank,
            max_pmw=max_pmw,
            topics=topic_by_lemma.get(str(row.get("lemma") or ""), ()),
            translations=translation_entries.get(str(row.get("lemma") or ""), ()),
            english_frequency=english_frequency,
            reverse_support=reverse_support.get(str(row.get("lemma") or ""), ()),
            learner_source=_learner_source_for(
                str(row.get("lemma") or ""),
                learner_source_index,
            ),
            learner_source_context=_learner_source_context(
                str(row.get("lemma") or ""),
                learner_source_index,
            ),
            wiktionary_metadata=_wiktionary_metadata_for(
                str(row.get("lemma") or ""),
                wiktionary_metadata_index,
            ),
            external_source=_external_source_for(
                str(row.get("lemma") or ""),
                external_source_index,
            ),
        )
        for row in frequency_rows
    ]
    findings = _build_findings(
        frequency_rows=frequency_rows,
        translation_entries=translation_entries,
        english_frequency=english_frequency,
        topic_by_lemma=topic_by_lemma,
        learner_source_index=learner_source_index,
        wiktionary_metadata_index=wiktionary_metadata_index,
        external_source_index=external_source_index,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    report: dict[str, object] = {
        "schema_version": 1,
        "language_pair": PAIR,
        "status": status,
        "decision": (
            "en_de_learner_difficulty_signal_palette_ready"
            if status == "ok"
            else "en_de_learner_difficulty_signal_palette_needs_review"
        ),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Inventory en-de learner-difficulty signals before calibration labels "
                "and formula sweeps. Rows are sidecar evidence, not production scores."
            ),
            "ranking_layer_policy": (
                "Global difficulty should remain distinct from admission-time topic "
                "preference. topic_documented is exposed only as a weak optional "
                "tail/tiebreak signal for future sweeps."
            ),
            "candidate_scope": "German target lemmas from freq-de-default ordered by core_rank.",
        },
        "inputs": {
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "translation_db": str(resolved_translation_db) if resolved_translation_db else None,
            "reverse_translation_db": str(resolved_reverse_translation_db)
            if resolved_reverse_translation_db
            else None,
            "english_frequency_db": str(resolved_english_frequency_db)
            if resolved_english_frequency_db
            else None,
            "topic_overlay_json": str(topic_overlay_json) if topic_overlay_json else None,
            "learner_source_json": str(learner_source_json) if learner_source_json else None,
            "wiktionary_metadata_json": str(wiktionary_metadata_json)
            if wiktionary_metadata_json
            else None,
            "external_source_json": str(external_source_json) if external_source_json else None,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
        },
        "learner_source_pack": {
            key: value for key, value in learner_source_index.items() if key != "by_lemma"
        },
        "wiktionary_metadata_pack": {
            key: value for key, value in wiktionary_metadata_index.items() if key != "by_lemma"
        },
        "external_source_pack": {
            key: value for key, value in external_source_index.items() if key != "by_lemma"
        },
        "summary": _summary(rows),
        "findings": findings,
        "samples": _samples(rows, sample_limit=sample_limit),
    }
    if include_rows:
        report["signal_rows"] = rows
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Learner Difficulty Signal Palette",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Coverage",
        "",
        f"- Candidate rows: `{summary.get('row_count', 0)}`",
        f"- Rows with translations: `{summary.get('rows_with_translations', 0)}`",
        f"- Rows with English frequency on a translation token: `{summary.get('rows_with_english_frequency', 0)}`",
        f"- Rows with reverse-dictionary support: `{summary.get('rows_with_reverse_support', 0)}`",
        f"- Rows with reviewed topic overlay: `{summary.get('rows_with_topic_overlay', 0)}`",
        f"- Rows with learner-source evidence: `{summary.get('rows_with_learner_source', 0)}`",
        f"- Rows with Wiktionary metadata: `{summary.get('rows_with_wiktionary_metadata', 0)}`",
        f"- Rows with Wiktionary marked usage: `{summary.get('rows_with_wiktionary_marked_usage', 0)}`",
        f"- Rows with Wiktionary form/alt-of evidence: `{summary.get('rows_with_wiktionary_form_variant', 0)}`",
        f"- Rows with external source evidence: `{summary.get('rows_with_external_source', 0)}`",
        f"- Rows with modern external evidence: `{summary.get('rows_with_external_modern_source', 0)}`",
        f"- Rows with child/simple source evidence: `{summary.get('rows_with_external_child_source', 0)}`",
        "",
        "POS buckets:",
        "",
    ]
    for bucket, count in sorted(_as_mapping(summary.get("pos_bucket_counts")).items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(["", "Topic counts:", ""])
    topic_counts = _as_mapping(summary.get("topic_counts"))
    if topic_counts:
        for topic, count in sorted(topic_counts.items()):
            lines.append(f"- `{topic}`: `{count}`")
    else:
        lines.append("- none")
    learner_source_counts = _as_mapping(summary.get("learner_source_counts"))
    lines.extend(["", "Learner-source counts:", ""])
    if learner_source_counts:
        for source_id, count in sorted(learner_source_counts.items()):
            lines.append(f"- `{source_id}`: `{count}`")
    else:
        lines.append("- none")
    external_source_counts = _as_mapping(summary.get("external_source_counts"))
    lines.extend(["", "External-source counts:", ""])
    if external_source_counts:
        for source_id, count in sorted(external_source_counts.items()):
            lines.append(f"- `{source_id}`: `{count}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Findings", ""])
    for finding in _as_sequence(report.get("findings")):
        row = _as_mapping(finding)
        lines.append(
            f"- `{row.get('level', '')}` `{row.get('code', '')}`: {row.get('message', '')}"
        )
    samples = _as_mapping(report.get("samples"))
    for title, rows in (
        ("Top Frequency Sample", _as_sequence(samples.get("top_frequency"))),
        ("Topic Overlay Sample", _as_sequence(samples.get("topic_overlay"))),
        ("Learner Source Sample", _as_sequence(samples.get("learner_source"))),
        ("Cognate/Transparency Sample", _as_sequence(samples.get("cognate_transparency"))),
        ("Long/Compound-Like Sample", _as_sequence(samples.get("long_or_compound_like"))),
    ):
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Lemma | Rank | POS | Topics | Translations | Signals |",
                "| --- | ---: | --- | --- | --- | --- |",
            ]
        )
        for row in rows:
            item = _as_mapping(row)
            signals = (
                f"base={_fmt(item.get('frequency_blend'))}; "
                f"cog={_fmt(item.get('english_translation_similarity_ease'))}; "
                f"learn={_fmt(item.get('learner_core_score'))}; "
                f"poly={_fmt(item.get('translation_count_score'))}; "
                f"len={_fmt(item.get('length_risk'))}"
            )
            lines.append(
                "| "
                + " | ".join(
                    (
                        f"`{_escape(item.get('lemma'))}`",
                        _fmt(item.get("core_rank")),
                        f"`{_escape(item.get('pos_bucket'))}`",
                        _escape(", ".join(str(t) for t in _as_sequence(item.get("topics")))) or "-",
                        _escape(
                            ", ".join(str(t) for t in _as_sequence(item.get("translations"))[:3])
                        )
                        or "-",
                        signals,
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _load_frequency_rows(path: Path | None, *, top_n: int) -> list[dict[str, object]]:
    if path is None or not Path(path).expanduser().exists():
        return []
    conn = sqlite3.connect(Path(path).expanduser())
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT lemma, core_rank, pmw, pos
            FROM frequency
            WHERE lemma IS NOT NULL AND TRIM(lemma) != ''
            ORDER BY COALESCE(core_rank, 999999999), lemma
            LIMIT ?
            """,
            (int(top_n),),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "lemma": str(row["lemma"]).strip(),
            "core_rank": _safe_float(row["core_rank"]),
            "pmw": _safe_float(row["pmw"]),
            "pos": str(row["pos"] or ""),
        }
        for row in rows
        if str(row["lemma"]).strip()
    ]


def _load_topic_overlay(path: Path | None) -> dict[str, tuple[str, ...]]:
    if path is None or not Path(path).expanduser().exists():
        return {}
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    topics_by_lemma: dict[str, list[str]] = defaultdict(list)
    for row in _mapping_rows(_as_mapping(payload).get("rows")):
        if str(row.get("language_pair") or "").strip() != PAIR:
            continue
        membership = _safe_float(row.get("membership"))
        if membership < PROFILE_TOPIC_OVERLAY_MIN_MEMBERSHIP:
            continue
        lemma = str(row.get("lemma") or "").strip()
        topic = str(row.get("topic") or "").strip()
        if lemma and topic and topic not in topics_by_lemma[lemma]:
            topics_by_lemma[lemma].append(topic)
    return {lemma: tuple(topics) for lemma, topics in topics_by_lemma.items()}


def _load_learner_source_index(path: Path | None) -> dict[str, object]:
    base: dict[str, object] = {
        "path": str(path) if path else None,
        "exists": False,
        "status": "missing",
        "overlay_term_count": 0,
        "included_source_ids": [],
        "broad_source_ids": [],
        "broad_source_available": False,
        "by_lemma": {},
    }
    if path is None or not Path(path).expanduser().is_file():
        return base
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["status"] = "unreadable"
        base["error"] = str(exc)
        return base
    overlay = _as_mapping(payload.get("source_overlay"))
    sources = [
        _as_mapping(source)
        for source in _as_sequence(_as_mapping(payload.get("source_summary")).get("sources"))
    ]
    included_source_ids = sorted(
        {
            str(source.get("source_id") or "")
            for source in sources
            if str(source.get("decision") or "").startswith("included")
            and str(source.get("source_id") or "")
        }
    )
    broad_source_ids = sorted(
        source_id
        for source_id in included_source_ids
        if source_id == "openlingo_mit_german_dictionary"
    )
    by_lemma = {
        _normalize_learner_source_key(key): dict(_as_mapping(value))
        for key, value in overlay.items()
        if _normalize_learner_source_key(key)
    }
    base.update(
        {
            "exists": True,
            "status": str(payload.get("status") or "unknown"),
            "decision": payload.get("decision"),
            "overlay_term_count": len(by_lemma),
            "included_source_ids": included_source_ids,
            "broad_source_ids": broad_source_ids,
            "broad_source_available": bool(broad_source_ids),
            "by_lemma": by_lemma,
        }
    )
    return base


def _load_wiktionary_metadata_index(path: Path | None) -> dict[str, object]:
    base: dict[str, object] = {
        "path": str(path) if path else None,
        "exists": False,
        "status": "missing",
        "metadata_coverage_count": 0,
        "by_lemma": {},
    }
    if path is None or not Path(path).expanduser().is_file():
        return base
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["status"] = "unreadable"
        base["error"] = str(exc)
        return base
    by_lemma = {
        _normalize_learner_source_key(key): dict(_as_mapping(value))
        for key, value in _as_mapping(payload.get("wiktionary_metadata_by_lemma")).items()
        if _normalize_learner_source_key(key)
    }
    summary = _as_mapping(payload.get("summary"))
    base.update(
        {
            "exists": True,
            "status": str(payload.get("status") or "unknown"),
            "decision": payload.get("decision"),
            "metadata_coverage_count": len(by_lemma),
            "summary": {
                "metadata_coverage_count": summary.get("metadata_coverage_count", len(by_lemma)),
                "marked_usage_count": summary.get("marked_usage_count", 0),
                "rare_dated_count": summary.get("rare_dated_count", 0),
                "form_or_alt_of_count": summary.get("form_or_alt_of_count", 0),
                "multi_sense_count": summary.get("multi_sense_count", 0),
            },
            "by_lemma": by_lemma,
        }
    )
    return base


def _load_external_source_index(path: Path | None) -> dict[str, object]:
    base: dict[str, object] = {
        "path": str(path) if path else None,
        "exists": False,
        "status": "missing",
        "overlay_term_count": 0,
        "by_lemma": {},
    }
    if path is None or not Path(path).expanduser().is_file():
        return base
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["status"] = "unreadable"
        base["error"] = str(exc)
        return base
    by_lemma = {
        _normalize_learner_source_key(key): dict(_as_mapping(value))
        for key, value in _as_mapping(payload.get("external_source_by_lemma")).items()
        if _normalize_learner_source_key(key)
    }
    summary = _as_mapping(payload.get("source_summary"))
    base.update(
        {
            "exists": True,
            "status": str(payload.get("status") or "unknown"),
            "decision": payload.get("decision"),
            "overlay_term_count": len(by_lemma),
            "summary": {
                "overlay_term_count": summary.get("overlay_term_count", len(by_lemma)),
                "source_hit_count": summary.get("source_hit_count", 0),
            },
            "by_lemma": by_lemma,
        }
    )
    return base


def _learner_source_for(
    lemma: str,
    learner_source_index: Mapping[str, object],
) -> Mapping[str, object]:
    by_lemma = _as_mapping(learner_source_index.get("by_lemma"))
    key = _normalize_learner_source_key(lemma)
    if key in by_lemma:
        return _as_mapping(by_lemma.get(key))
    return {}


def _learner_source_context(
    lemma: str,
    learner_source_index: Mapping[str, object],
) -> Mapping[str, object]:
    learner = _learner_source_for(lemma, learner_source_index)
    source_ids = {str(item) for item in _as_sequence(learner.get("source_ids"))}
    broad_source_ids = {
        str(item) for item in _as_sequence(learner_source_index.get("broad_source_ids"))
    }
    broad_available = bool(learner_source_index.get("broad_source_available"))
    broad_known_ids = sorted(source_ids & broad_source_ids)
    return {
        "broad_source_available": broad_available,
        "broad_source_ids": sorted(broad_source_ids),
        "broad_source_known": bool(broad_known_ids),
        "broad_source_known_ids": broad_known_ids,
        "broad_source_absent": bool(broad_available and not broad_known_ids),
    }


def _wiktionary_metadata_for(
    lemma: str,
    wiktionary_metadata_index: Mapping[str, object],
) -> Mapping[str, object]:
    by_lemma = _as_mapping(wiktionary_metadata_index.get("by_lemma"))
    key = _normalize_learner_source_key(lemma)
    if key in by_lemma:
        return _as_mapping(by_lemma.get(key))
    return {}


def _external_source_for(
    lemma: str,
    external_source_index: Mapping[str, object],
) -> Mapping[str, object]:
    by_lemma = _as_mapping(external_source_index.get("by_lemma"))
    key = _normalize_learner_source_key(lemma)
    if key in by_lemma:
        return _as_mapping(by_lemma.get(key))
    return {}


def _load_translation_entries(
    path: Path | None,
    *,
    keys: Sequence[str],
) -> dict[str, tuple[dict[str, object], ...]]:
    result: dict[str, list[dict[str, object]]] = {key: [] for key in keys}
    if path is None or not Path(path).expanduser().exists() or not keys:
        return {key: tuple(values) for key, values in result.items()}
    conn = sqlite3.connect(Path(path).expanduser())
    conn.row_factory = sqlite3.Row
    try:
        for chunk in _chunks([key.lower() for key in keys], size=750):
            placeholders = ",".join("?" for _ in chunk)
            rows = conn.execute(
                f"""
                SELECT headword_lc, translation_lc, pos, rank
                FROM entries
                WHERE headword_lc IN ({placeholders})
                ORDER BY headword_lc, rank, translation_lc
                """,
                tuple(chunk),
            ).fetchall()
            for row in rows:
                headword = str(row["headword_lc"] or "").strip()
                translation = str(row["translation_lc"] or "").strip()
                if not headword or not translation:
                    continue
                result.setdefault(headword, []).append(
                    {
                        "translation": translation,
                        "pos": str(row["pos"] or ""),
                        "rank": int(row["rank"] or 0),
                    }
                )
    finally:
        conn.close()
    return {key: tuple(values[:20]) for key, values in result.items()}


def _load_english_frequency(
    path: Path | None,
    *,
    tokens: Sequence[str],
) -> dict[str, dict[str, object]]:
    if path is None or not Path(path).expanduser().exists() or not tokens:
        return {}
    conn = sqlite3.connect(Path(path).expanduser())
    conn.row_factory = sqlite3.Row
    found: dict[str, dict[str, object]] = {}
    try:
        for chunk in _chunks(sorted(set(tokens)), size=750):
            placeholders = ",".join("?" for _ in chunk)
            rows = conn.execute(
                f"""
                SELECT lemma, core_rank, pmw
                FROM frequency
                WHERE lemma IN ({placeholders})
                """,
                tuple(chunk),
            ).fetchall()
            for row in rows:
                lemma = str(row["lemma"] or "").strip()
                if lemma:
                    found[lemma] = {
                        "core_rank": _safe_float(row["core_rank"]),
                        "pmw": _safe_float(row["pmw"]),
                    }
    finally:
        conn.close()
    return found


def _load_reverse_support(
    path: Path | None,
    *,
    translation_entries: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, tuple[str, ...]]:
    if path is None or not Path(path).expanduser().exists():
        return {}
    english_terms_by_lemma: dict[str, set[str]] = defaultdict(set)
    for lemma, entries in translation_entries.items():
        for entry in entries[:8]:
            translation = str(entry.get("translation") or "").strip()
            if translation:
                english_terms_by_lemma[lemma].add(translation)
            english_terms_by_lemma[lemma].update(_translation_tokens(translation))
    all_terms = sorted(
        {term for terms in english_terms_by_lemma.values() for term in terms if term}
    )
    if not all_terms:
        return {}
    reverse_rows_by_headword: dict[str, tuple[str, ...]] = {}
    conn = sqlite3.connect(Path(path).expanduser())
    conn.row_factory = sqlite3.Row
    try:
        for chunk in _chunks(all_terms, size=750):
            placeholders = ",".join("?" for _ in chunk)
            rows = conn.execute(
                f"""
                SELECT headword_lc, translation_lc
                FROM entries
                WHERE headword_lc IN ({placeholders})
                """,
                tuple(chunk),
            ).fetchall()
            grouped: dict[str, list[str]] = defaultdict(list)
            for row in rows:
                headword = str(row["headword_lc"] or "").strip()
                translation = str(row["translation_lc"] or "").strip()
                if headword and translation and translation not in grouped[headword]:
                    grouped[headword].append(translation)
            for headword, values in grouped.items():
                existing = list(reverse_rows_by_headword.get(headword, ()))
                for value in values:
                    if value not in existing:
                        existing.append(value)
                reverse_rows_by_headword[headword] = tuple(existing)
    finally:
        conn.close()
    support: dict[str, list[str]] = defaultdict(list)
    for lemma, terms in english_terms_by_lemma.items():
        for term in sorted(terms):
            translations = reverse_rows_by_headword.get(term, ())
            if lemma in translations and term not in support[lemma]:
                support[lemma].append(term)
    return {lemma: tuple(values) for lemma, values in support.items()}


def _signal_row(
    *,
    row: Mapping[str, object],
    max_rank: float,
    max_pmw: float,
    topics: Sequence[str],
    translations: Sequence[Mapping[str, object]],
    english_frequency: Mapping[str, Mapping[str, object]],
    reverse_support: Sequence[str],
    learner_source: Mapping[str, object],
    learner_source_context: Mapping[str, object],
    wiktionary_metadata: Mapping[str, object],
    external_source: Mapping[str, object],
) -> dict[str, object]:
    lemma = str(row.get("lemma") or "").strip()
    rank = _safe_float(row.get("core_rank"))
    pmw = _safe_float(row.get("pmw"))
    raw_pos = str(row.get("pos") or "")
    pos_bucket = classify_pos_bucket(language_pair=PAIR, raw_pos=raw_pos)
    rank_base = _log_ratio(rank, max_rank)
    pmw_base = 1.0 - _log_ratio(pmw, max_pmw)
    translations_text = _unique(
        str(entry.get("translation") or "").strip()
        for entry in translations
        if str(entry.get("translation") or "").strip()
    )
    translation_tokens = _unique(
        token for text in translations_text for token in _translation_tokens(text)
    )
    english_commonness = _english_commonness(translation_tokens, english_frequency)
    similarity = _best_similarity(lemma, translation_tokens)
    translation_count_score = _log_score(len(translations_text), ceiling=12.0)
    length_risk = min(1.0, max(0.0, (len(lemma) - 8) / 12.0))
    compound_like = 1.0 if len(lemma) >= 12 else 0.0
    other_pos_risk = 1.0 if pos_bucket == "other" else 0.0
    content_pos_gate = 1.0 if pos_bucket in {"noun", "verb", "adjective", "adverb"} else 0.0
    topic_documented = 1.0 if topics else 0.0
    reverse_support_score = min(1.0, len(reverse_support) / 3.0)
    learner = dict(learner_source)
    learner_context = dict(learner_source_context)
    learner_core_score = _safe_float(learner.get("learner_core_score"))
    learner_confidence = _safe_float(learner.get("confidence"))
    learner_source_known = 1.0 if learner else 0.0
    source_ids = {str(item) for item in _as_sequence(learner.get("source_ids"))}
    learner_source_count = len(source_ids)
    broad_learner_source_known = 1.0 if learner_context.get("broad_source_known") else 0.0
    broad_learner_source_absent = 1.0 if learner_context.get("broad_source_absent") else 0.0
    openlingo_source = _source_specific_learner_summary(
        learner,
        "openlingo_mit_german_dictionary",
    )
    goethe_stem_source = _source_specific_learner_summary(
        learner,
        "sprachomat_goethe_a1a2b1_stems",
    )
    goethe_official_a1_source = _source_specific_learner_summary(
        learner,
        "goethe_official_a1_wordlist",
    )
    odenet_basis_source = _source_specific_learner_summary(
        learner,
        "odenet_basiswortschatz",
    )
    wiktionary = dict(wiktionary_metadata)
    wiktionary_known = 1.0 if wiktionary else 0.0
    wiktionary_entry_count = int(_safe_float(wiktionary.get("entry_count")))
    wiktionary_sense_count = int(_safe_float(wiktionary.get("sense_count")))
    wiktionary_gloss_count = int(_safe_float(wiktionary.get("gloss_count")))
    wiktionary_pos_count = int(_safe_float(wiktionary.get("pos_count")))
    wiktionary_topic_count = int(_safe_float(wiktionary.get("topic_count")))
    wiktionary_region_tag_count = int(_safe_float(wiktionary.get("region_tag_count")))
    wiktionary_form_of_count = int(_safe_float(wiktionary.get("form_of_count")))
    wiktionary_alt_of_count = int(_safe_float(wiktionary.get("alt_of_count")))
    wiktionary_form_variant_count = wiktionary_form_of_count + wiktionary_alt_of_count
    wiktionary_marked_usage_flag = 1.0 if wiktionary.get("marked_usage_flag") else 0.0
    wiktionary_rare_dated_flag = 1.0 if wiktionary.get("rare_dated_flag") else 0.0
    wiktionary_colloquial_flag = 1.0 if wiktionary.get("colloquial_flag") else 0.0
    wiktionary_sensitive_flag = 1.0 if wiktionary.get("sensitive_flag") else 0.0
    wiktionary_sense_count_score = _log_score(wiktionary_sense_count, ceiling=18.0)
    wiktionary_form_variant_score = _log_score(wiktionary_form_variant_count, ceiling=6.0)
    external = dict(external_source)
    external_known = 1.0 if external else 0.0
    external_source_ids = {str(item) for item in _as_sequence(external.get("source_ids"))}
    external_modern_known = 1.0 if external.get("modern_source_known") else 0.0
    external_child_known = 1.0 if external.get("child_source_known") else 0.0
    external_archive_known = 1.0 if external.get("archive_source_known") else 0.0
    external_modern_score = _safe_float(external.get("modern_frequency_score"))
    external_archive_score = _safe_float(external.get("archive_attestation_score"))
    wordfreq_zipf = _safe_float(external.get("wordfreq_zipf"))
    wordfreq_commonness = _safe_float(external.get("wordfreq_commonness_score"))
    opensubtitles_score = _safe_float(external.get("opensubtitles_frequency_score"))
    opensubtitles_rank = int(_safe_float(external.get("opensubtitles_rank")))
    klexikon_title_known = 1.0 if external.get("klexikon_title_known") else 0.0
    return {
        "language_pair": PAIR,
        "lemma": lemma,
        "core_rank": rank,
        "pmw": pmw,
        "pos": raw_pos,
        "pos_bucket": pos_bucket,
        "rank_base": round(rank_base, 6),
        "pmw_base": round(pmw_base, 6),
        "frequency_blend": round((rank_base * 0.55) + (pmw_base * 0.45), 6),
        "content_pos_gate": round(content_pos_gate, 6),
        "other_pos_risk": round(other_pos_risk, 6),
        "length_risk": round(length_risk, 6),
        "compound_like": round(compound_like, 6),
        "topic_documented": round(topic_documented, 6),
        "topics": list(topics),
        "translation_count": len(translations_text),
        "translation_count_score": round(translation_count_score, 6),
        "translations": list(translations_text[:8]),
        "english_translation_tokens": list(translation_tokens[:12]),
        "english_translation_frequency_ease": round(english_commonness, 6),
        "english_translation_similarity_ease": round(similarity, 6),
        "reverse_support_count": len(reverse_support),
        "reverse_support_score": round(reverse_support_score, 6),
        "reverse_support_terms": list(reverse_support[:8]),
        "learner_source": learner,
        "learner_source_context": learner_context,
        "learner_source_known": round(learner_source_known, 6),
        "learner_core_score": round(learner_core_score, 6),
        "learner_source_confidence": round(learner_confidence, 6),
        "learner_source_count": learner_source_count,
        "broad_learner_source_known": round(broad_learner_source_known, 6),
        "broad_learner_source_absent": round(broad_learner_source_absent, 6),
        "openlingo_learner_source_known": round(openlingo_source["known"], 6),
        "openlingo_learner_core_score": round(openlingo_source["score"], 6),
        "openlingo_learner_source_confidence": round(openlingo_source["confidence"], 6),
        "goethe_stem_learner_source_known": round(goethe_stem_source["known"], 6),
        "goethe_stem_learner_core_score": round(goethe_stem_source["score"], 6),
        "goethe_stem_learner_source_confidence": round(goethe_stem_source["confidence"], 6),
        "goethe_official_a1_learner_source_known": round(
            goethe_official_a1_source["known"],
            6,
        ),
        "goethe_official_a1_learner_core_score": round(
            goethe_official_a1_source["score"],
            6,
        ),
        "goethe_official_a1_learner_source_confidence": round(
            goethe_official_a1_source["confidence"],
            6,
        ),
        "odenet_basis_learner_source_known": round(odenet_basis_source["known"], 6),
        "odenet_basis_learner_core_score": round(odenet_basis_source["score"], 6),
        "odenet_basis_learner_source_confidence": round(odenet_basis_source["confidence"], 6),
        "wiktionary_metadata_known": round(wiktionary_known, 6),
        "wiktionary_entry_count": wiktionary_entry_count,
        "wiktionary_sense_count": wiktionary_sense_count,
        "wiktionary_sense_count_score": round(wiktionary_sense_count_score, 6),
        "wiktionary_gloss_count": wiktionary_gloss_count,
        "wiktionary_pos_count": wiktionary_pos_count,
        "wiktionary_topic_count": wiktionary_topic_count,
        "wiktionary_region_tag_count": wiktionary_region_tag_count,
        "wiktionary_form_of_count": wiktionary_form_of_count,
        "wiktionary_alt_of_count": wiktionary_alt_of_count,
        "wiktionary_form_variant_count": wiktionary_form_variant_count,
        "wiktionary_form_variant_score": round(wiktionary_form_variant_score, 6),
        "wiktionary_marked_usage_flag": round(wiktionary_marked_usage_flag, 6),
        "wiktionary_rare_dated_flag": round(wiktionary_rare_dated_flag, 6),
        "wiktionary_colloquial_flag": round(wiktionary_colloquial_flag, 6),
        "wiktionary_sensitive_flag": round(wiktionary_sensitive_flag, 6),
        "external_source": external,
        "external_source_known": round(external_known, 6),
        "external_source_count": len(external_source_ids),
        "external_modern_source_known": round(external_modern_known, 6),
        "external_modern_frequency_score": round(external_modern_score, 6),
        "external_child_source_known": round(external_child_known, 6),
        "external_archive_source_known": round(external_archive_known, 6),
        "external_archive_attestation_score": round(external_archive_score, 6),
        "wordfreq_de_known": 1.0 if external.get("wordfreq_known") else 0.0,
        "wordfreq_de_zipf": round(wordfreq_zipf, 6),
        "wordfreq_de_commonness_score": round(wordfreq_commonness, 6),
        "opensubtitles_cistem_known": 1.0 if external.get("opensubtitles_known") else 0.0,
        "opensubtitles_cistem_frequency_score": round(opensubtitles_score, 6),
        "opensubtitles_cistem_rank": opensubtitles_rank,
        "klexikon_title_known": round(klexikon_title_known, 6),
    }


def _source_specific_learner_summary(
    learner: Mapping[str, object],
    source_id: str,
) -> dict[str, float]:
    hits = [
        _as_mapping(hit)
        for hit in _as_sequence(learner.get("hit_evidence"))
        if str(_as_mapping(hit).get("source_id") or "") == source_id
    ]
    if not hits:
        return {"known": 0.0, "score": 0.0, "confidence": 0.0}
    scores = [_safe_float(hit.get("score")) for hit in hits]
    confidences = [_safe_float(hit.get("confidence")) for hit in hits]
    confidence_miss = 1.0
    for confidence in confidences:
        confidence_miss *= 1.0 - max(0.0, min(1.0, confidence))
    return {
        "known": 1.0,
        "score": min(scores) if scores else 0.0,
        "confidence": 1.0 - confidence_miss,
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    topic_counts: Counter[str] = Counter(
        topic for row in rows for topic in _as_sequence(row.get("topics")) if str(topic).strip()
    )
    learner_source_counts: Counter[str] = Counter(
        source_id
        for row in rows
        for source_id in _as_sequence(_as_mapping(row.get("learner_source")).get("source_ids"))
        if str(source_id).strip()
    )
    external_source_counts: Counter[str] = Counter(
        source_id
        for row in rows
        for source_id in _as_sequence(_as_mapping(row.get("external_source")).get("source_ids"))
        if str(source_id).strip()
    )
    return {
        "row_count": len(rows),
        "pos_bucket_counts": dict(
            sorted(Counter(str(row.get("pos_bucket") or "other") for row in rows).items())
        ),
        "rows_with_translations": sum(
            1 for row in rows if int(row.get("translation_count") or 0) > 0
        ),
        "rows_with_english_frequency": sum(
            1 for row in rows if _safe_float(row.get("english_translation_frequency_ease")) > 0.0
        ),
        "rows_with_reverse_support": sum(
            1 for row in rows if int(row.get("reverse_support_count") or 0) > 0
        ),
        "rows_with_topic_overlay": sum(
            1 for row in rows if _safe_float(row.get("topic_documented")) > 0.0
        ),
        "rows_with_learner_source": sum(
            1 for row in rows if _safe_float(row.get("learner_source_known")) > 0.0
        ),
        "rows_with_wiktionary_metadata": sum(
            1 for row in rows if _safe_float(row.get("wiktionary_metadata_known")) > 0.0
        ),
        "rows_with_wiktionary_marked_usage": sum(
            1 for row in rows if _safe_float(row.get("wiktionary_marked_usage_flag")) > 0.0
        ),
        "rows_with_wiktionary_rare_dated": sum(
            1 for row in rows if _safe_float(row.get("wiktionary_rare_dated_flag")) > 0.0
        ),
        "rows_with_wiktionary_form_variant": sum(
            1 for row in rows if _safe_float(row.get("wiktionary_form_variant_count")) > 0.0
        ),
        "rows_with_external_source": sum(
            1 for row in rows if _safe_float(row.get("external_source_known")) > 0.0
        ),
        "rows_with_external_modern_source": sum(
            1 for row in rows if _safe_float(row.get("external_modern_source_known")) > 0.0
        ),
        "rows_with_external_child_source": sum(
            1 for row in rows if _safe_float(row.get("external_child_source_known")) > 0.0
        ),
        "rows_with_external_archive_source": sum(
            1 for row in rows if _safe_float(row.get("external_archive_source_known")) > 0.0
        ),
        "topic_counts": dict(sorted(topic_counts.items())),
        "learner_source_counts": dict(sorted(learner_source_counts.items())),
        "external_source_counts": dict(sorted(external_source_counts.items())),
    }


def _samples(rows: Sequence[Mapping[str, object]], *, sample_limit: int) -> dict[str, object]:
    return {
        "top_frequency": list(rows[:sample_limit]),
        "topic_overlay": [row for row in rows if _safe_float(row.get("topic_documented")) > 0.0][
            :sample_limit
        ],
        "learner_source": [
            row for row in rows if _safe_float(row.get("learner_source_known")) > 0.0
        ][:sample_limit],
        "cognate_transparency": sorted(
            rows,
            key=lambda row: (
                -_safe_float(row.get("english_translation_similarity_ease")),
                _safe_float(row.get("core_rank")),
            ),
        )[:sample_limit],
        "long_or_compound_like": sorted(
            rows,
            key=lambda row: (
                -_safe_float(row.get("length_risk")),
                _safe_float(row.get("core_rank")),
            ),
        )[:sample_limit],
        "external_source": [
            row for row in rows if _safe_float(row.get("external_source_known")) > 0.0
        ][:sample_limit],
    }


def _build_findings(
    *,
    frequency_rows: Sequence[Mapping[str, object]],
    translation_entries: Mapping[str, Sequence[Mapping[str, object]]],
    english_frequency: Mapping[str, Mapping[str, object]],
    topic_by_lemma: Mapping[str, Sequence[str]],
    learner_source_index: Mapping[str, object],
    wiktionary_metadata_index: Mapping[str, object],
    external_source_index: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    findings.append(
        _finding(
            "PASS" if frequency_rows else "FAIL",
            "frequency_rows_available",
            f"Loaded {len(frequency_rows)} en-de frequency rows.",
        )
    )
    translated_count = sum(1 for values in translation_entries.values() if values)
    findings.append(
        _finding(
            "PASS" if translated_count else "WARN",
            "translation_glosses_available",
            f"Loaded translation glosses for {translated_count} frequency rows.",
        )
    )
    findings.append(
        _finding(
            "PASS" if english_frequency else "WARN",
            "english_frequency_available",
            f"Loaded English frequency for {len(english_frequency)} translation tokens.",
        )
    )
    findings.append(
        _finding(
            "PASS" if topic_by_lemma else "WARN",
            "topic_overlay_available",
            f"Loaded reviewed topic overlay rows for {len(topic_by_lemma)} German lemmas.",
        )
    )
    findings.append(
        _finding(
            "PASS" if learner_source_index.get("exists") else "WARN",
            "learner_source_overlay_available",
            "Loaded learner-source evidence for "
            f"{learner_source_index.get('overlay_term_count', 0)} German lemmas.",
        )
    )
    findings.append(
        _finding(
            "PASS" if wiktionary_metadata_index.get("exists") else "WARN",
            "wiktionary_metadata_available",
            "Loaded Wiktionary metadata for "
            f"{wiktionary_metadata_index.get('metadata_coverage_count', 0)} German lemmas.",
        )
    )
    findings.append(
        _finding(
            "PASS" if external_source_index.get("exists") else "WARN",
            "external_source_overlay_available",
            "Loaded external source evidence for "
            f"{external_source_index.get('overlay_term_count', 0)} German lemmas.",
        )
    )
    return findings


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _translation_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(str(value or "").lower()):
        token = match.group(0).strip("-'")
        if len(token) < 2 or token in ENGLISH_STOPWORDS:
            continue
        tokens.append(token)
    return tuple(_unique(tokens))


def _english_commonness(
    tokens: Sequence[str],
    english_frequency: Mapping[str, Mapping[str, object]],
) -> float:
    best = 0.0
    for token in tokens:
        row = english_frequency.get(token)
        if not row:
            continue
        pmw = _safe_float(row.get("pmw"))
        best = max(best, min(1.0, math.log1p(max(0.0, pmw)) / math.log1p(4000.0)))
    return best


def _best_similarity(lemma: str, tokens: Sequence[str]) -> float:
    normalized_lemma = _latin_key(lemma)
    if len(normalized_lemma) < 4:
        return 0.0
    best = 0.0
    for token in tokens:
        normalized_token = _latin_key(token)
        if len(normalized_token) < 4:
            continue
        best = max(best, SequenceMatcher(None, normalized_lemma, normalized_token).ratio())
    return best if best >= 0.55 else 0.0


def _latin_key(value: str) -> str:
    text = str(value or "").lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if char.isascii() and char.isalpha()
    )


def _normalize_learner_source_key(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _log_ratio(value: object, max_value: object) -> float:
    numerator = math.log1p(max(0.0, _safe_float(value)))
    denominator = math.log1p(max(1.0, _safe_float(max_value)))
    return min(1.0, max(0.0, numerator / denominator))


def _log_score(value: object, *, ceiling: float) -> float:
    return min(1.0, math.log1p(max(0.0, _safe_float(value))) / math.log1p(ceiling))


def _chunks(values: Sequence[str], *, size: int) -> Sequence[Sequence[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _unique(values: Iterable[object]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: object) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return (
        value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        else ()
    )


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in _as_sequence(value) if isinstance(row, Mapping)]


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return ""


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
