#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Mapping, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import default_frequency_db_path  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


PAIR = "en-de"
DEFAULT_TOP_N = 75000
DEFAULT_SAMPLE_LIMIT = 20
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_external_source_audit_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_external_source_audit_en_de_latest.md"
)
USER_AGENT = "LexiShift en-de external source audit/0.1 (local development; contact via repo)"

OLASTOR_OPENSUBTITLES_CSV_URL = (
    "https://raw.githubusercontent.com/olastor/german-word-frequencies/main/"
    "opensubtitles/opensubtitles_cistem_freq.csv"
)
KLEXIKON_ARTICLES_JSON_URL = (
    "https://raw.githubusercontent.com/dennlinger/klexikon/master/data/articles.json"
)
GERMAN_COMMONS_DATASET_API_URL = "https://huggingface.co/api/datasets/coral-nlp/german-commons"

MODERN_SOURCE_IDS = frozenset(
    {
        "wordfreq_de_multi_source",
        "olastor_opensubtitles_cistem",
        "german_commons_sample",
    }
)
CHILD_SOURCE_IDS = frozenset({"klexikon_child_encyclopedia_titles"})
ARCHIVE_SOURCE_IDS = frozenset({"german_literary_archive_sample"})


@dataclass(frozen=True)
class ExternalHit:
    source_id: str
    source_label: str
    source_kind: str
    evidence: str
    confidence: float
    source_term: str | None = None
    match_type: str = "exact"
    score: float | None = None
    frequency: float | None = None
    rank: int | None = None
    document_count: int | None = None
    token_count: int | None = None
    zipf: float | None = None
    subset: str | None = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit external en-de difficulty-ranking sources: modern frequency, "
            "subtitle-like spoken/dialogue evidence, child/simple concept attestation, "
            "and optional corpus samples. This is sidecar-only and does not run ranking "
            "formula sweeps."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--skip-wordfreq", action="store_true")
    parser.add_argument("--opensubtitles-csv", type=Path)
    parser.add_argument("--klexikon-articles-json", type=Path)
    parser.add_argument(
        "--german-commons-jsonl-sample",
        type=Path,
        help=(
            "Optional JSONL sample with text/source/subset fields. This intentionally "
            "does not download the full German Commons corpus."
        ),
    )
    parser.add_argument(
        "--literary-archive-jsonl-sample",
        type=Path,
        help="Optional JSONL/TXT-like sample for Gutenberg/DTA/Wikisource-style tail diagnostics.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        fetch_network=not bool(args.skip_network),
        include_wordfreq=not bool(args.skip_wordfreq),
        opensubtitles_csv=args.opensubtitles_csv,
        klexikon_articles_json=args.klexikon_articles_json,
        german_commons_jsonl_sample=args.german_commons_jsonl_sample,
        literary_archive_jsonl_sample=args.literary_archive_jsonl_sample,
    )
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
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    fetch_network: bool = True,
    include_wordfreq: bool = True,
    opensubtitles_csv: Path | None = None,
    klexikon_articles_json: Path | None = None,
    german_commons_jsonl_sample: Path | None = None,
    literary_archive_jsonl_sample: Path | None = None,
    source_texts: Mapping[str, str] | None = None,
) -> dict[str, object]:
    source_texts = dict(source_texts or {})
    generated_at = generated_at or _utc_now()
    paths = build_helper_paths()
    resolved_frequency_db = frequency_db or default_frequency_db_path(
        PAIR,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    candidate_rows = _load_frequency_rows(resolved_frequency_db, top_n=top_n)
    candidate_index = _candidate_index(candidate_rows)
    ascii_candidate_index = _ascii_candidate_index(candidate_rows)
    source_results: list[dict[str, object]] = []
    hits_by_lemma: dict[str, list[ExternalHit]] = defaultdict(list)

    _collect_wordfreq(
        source_results,
        hits_by_lemma=hits_by_lemma,
        candidate_rows=candidate_rows,
        include_wordfreq=include_wordfreq,
    )
    _collect_opensubtitles(
        source_results,
        hits_by_lemma=hits_by_lemma,
        ascii_candidate_index=ascii_candidate_index,
        path=opensubtitles_csv,
        provided_text=source_texts.get("olastor_opensubtitles_cistem"),
        fetch_network=fetch_network,
    )
    _collect_klexikon_titles(
        source_results,
        hits_by_lemma=hits_by_lemma,
        candidate_index=candidate_index,
        path=klexikon_articles_json,
        provided_text=source_texts.get("klexikon_child_encyclopedia_titles"),
        fetch_network=fetch_network,
    )
    _collect_text_corpus_sample(
        source_results,
        hits_by_lemma=hits_by_lemma,
        candidate_index=candidate_index,
        source_id="german_commons_sample",
        source_label="German Commons sample",
        source_kind="open_licensed_multi_domain_sample",
        evidence="german_commons_sample_document_attestation",
        path=german_commons_jsonl_sample,
        provided_text=source_texts.get("german_commons_sample"),
        confidence=0.58,
    )
    _collect_text_corpus_sample(
        source_results,
        hits_by_lemma=hits_by_lemma,
        candidate_index=candidate_index,
        source_id="german_literary_archive_sample",
        source_label="German literary/archive sample",
        source_kind="literary_archive_sample",
        evidence="literary_archive_sample_document_attestation",
        path=literary_archive_jsonl_sample,
        provided_text=source_texts.get("german_literary_archive_sample"),
        confidence=0.42,
    )
    _collect_german_commons_manifest(
        source_results,
        provided_text=source_texts.get("german_commons_manifest"),
        fetch_network=fetch_network,
    )

    overlay = _overlay_from_hits(hits_by_lemma)
    coverage_rows = _candidate_coverage_rows(candidate_rows, overlay)
    matched_rows = [row for row in coverage_rows if row.get("external_source")]
    findings = _build_findings(
        candidate_rows=candidate_rows,
        source_results=source_results,
        overlay=overlay,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    source_summary = _source_summary(source_results, overlay)
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_de_external_difficulty_sources_ready"
            if status == "ok"
            else "en_de_external_difficulty_sources_need_review"
        ),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "inputs": {
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
            "fetch_network": bool(fetch_network),
            "include_wordfreq": bool(include_wordfreq),
            "opensubtitles_csv": str(opensubtitles_csv) if opensubtitles_csv else None,
            "klexikon_articles_json": str(klexikon_articles_json)
            if klexikon_articles_json
            else None,
            "german_commons_jsonl_sample": str(german_commons_jsonl_sample)
            if german_commons_jsonl_sample
            else None,
            "literary_archive_jsonl_sample": str(literary_archive_jsonl_sample)
            if literary_archive_jsonl_sample
            else None,
        },
        "methodology": {
            "purpose": (
                "Expose extra source signals before en-de formula sweeps: modern "
                "frequency corroboration, dialogue/subtitle-like attestation, "
                "child-directed concept evidence, and optional advanced/archive samples."
            ),
            "source_policy": (
                "wordfreq and OpenSubtitles/COW-derived data are modern frequency "
                "perspectives; Klexikon title matches are child-concept attestation; "
                "German Commons is prepared as a manifest/local-sample hook because the "
                "full corpus is too large for this setup pass."
            ),
            "score_semantics": (
                "Scores are normalized source strengths for future bounded sweeps. They "
                "are not final learner difficulty values."
            ),
        },
        "source_summary": source_summary,
        "candidate_coverage": {
            "candidate_count": len(coverage_rows),
            "matched_candidate_count": len(matched_rows),
            "matched_candidate_ratio": _ratio(len(matched_rows), len(coverage_rows)),
            "matched_by_source": dict(
                Counter(
                    source
                    for row in matched_rows
                    for source in _as_sequence(
                        _as_mapping(row.get("external_source")).get("source_ids")
                    )
                ).most_common()
            ),
            "top_matched_samples": matched_rows[:sample_limit],
            "highest_difficulty_matched_samples": sorted(
                matched_rows,
                key=lambda row: (
                    -(_safe_float(row.get("frequency_difficulty")) or 0.0),
                    str(row.get("lemma") or ""),
                ),
            )[:sample_limit],
        },
        "external_source_by_lemma": overlay,
        "findings": findings,
        "limitations": [
            "OpenSubtitles rows are CISTEM-stemmed; matching is conservative ASCII-key matching, not true German lemmatization.",
            "Klexikon is currently title-level child-concept evidence, not full prose frequency.",
            "German Commons full-corpus processing is intentionally not automatic in this script.",
            "Archive samples are optional local inputs until a license-safe German archive source is selected.",
        ],
    }
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("source_summary"))
    coverage = _as_mapping(report.get("candidate_coverage"))
    lines = [
        "# en-de External Difficulty Source Audit",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Source Summary",
        "",
        f"- Overlay candidate lemmas: `{summary.get('overlay_term_count', 0)}`",
        f"- Source hits: `{summary.get('source_hit_count', 0)}`",
        "",
        "| Source | Status | License | Hits | Matched lemmas | Decision |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for raw in _as_sequence(summary.get("sources")):
        source = _as_mapping(raw)
        lines.append(
            f"| `{source.get('source_id')}` | `{source.get('status')}` | "
            f"{source.get('license')} | {source.get('hit_count', 0)} | "
            f"{source.get('matched_lemma_count', 0)} | {source.get('decision')} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Coverage",
            "",
            f"- Candidate rows checked: `{coverage.get('candidate_count', 0)}`",
            f"- Matched rows: `{coverage.get('matched_candidate_count', 0)}`",
            f"- Matched ratio: `{_pct(coverage.get('matched_candidate_ratio'))}`",
            "",
        ]
    )
    matched_by_source = _as_mapping(coverage.get("matched_by_source"))
    if matched_by_source:
        lines.extend(["| Source | Matched candidates |", "| --- | ---: |"])
        for source_id, count in matched_by_source.items():
            lines.append(f"| `{source_id}` | {count} |")
        lines.append("")
    for title, key in (
        ("Top Matched Samples", "top_matched_samples"),
        ("Highest Difficulty Matched Samples", "highest_difficulty_matched_samples"),
    ):
        rows = _as_sequence(coverage.get(key))
        if not rows:
            continue
        lines.extend(
            [
                f"## {title}",
                "",
                "| Lemma | Difficulty | Modern | Child | Archive | Sources | Signals |",
                "| --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for raw in rows:
            row = _as_mapping(raw)
            source = _as_mapping(row.get("external_source"))
            signals = (
                f"zipf={_fmt_float(source.get('wordfreq_zipf'))}; "
                f"sub={_fmt_float(source.get('opensubtitles_frequency_score'))}; "
                f"child={_fmt_float(source.get('child_source_known'))}"
            )
            lines.append(
                f"| `{row.get('lemma')}` | {_fmt_float(row.get('frequency_difficulty'))} | "
                f"{_fmt_float(source.get('modern_source_known'))} | "
                f"{_fmt_float(source.get('child_source_known'))} | "
                f"{_fmt_float(source.get('archive_source_known'))} | "
                f"{', '.join(str(item) for item in _as_sequence(source.get('source_ids')))} | "
                f"{signals} |"
            )
        lines.append("")
    lines.extend(["## Findings", "", "| Level | Code | Message |", "| --- | --- | --- |"])
    for raw in _as_sequence(report.get("findings")):
        row = _as_mapping(raw)
        lines.append(f"| {row.get('level')} | `{row.get('code')}` | {row.get('message')} |")
    lines.append("")
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _collect_wordfreq(
    source_results: list[dict[str, object]],
    *,
    hits_by_lemma: dict[str, list[ExternalHit]],
    candidate_rows: Sequence[Mapping[str, object]],
    include_wordfreq: bool,
) -> None:
    source_id = "wordfreq_de_multi_source"
    if not include_wordfreq:
        source_results.append(_source_result(source_id, "skipped", "not requested", 0))
        return
    try:
        from wordfreq import zipf_frequency  # type: ignore
    except Exception as exc:
        source_results.append(_source_result(source_id, "failed", str(exc), 0))
        return
    hit_count = 0
    for row in candidate_rows:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            continue
        zipf = float(zipf_frequency(lemma, "de", wordlist="best"))
        if zipf <= 0.0:
            continue
        score = min(1.0, max(0.0, zipf / 7.5))
        confidence = 0.78 if zipf >= 3.0 else 0.58
        hits_by_lemma[lemma].append(
            ExternalHit(
                source_id=source_id,
                source_label="wordfreq German multi-source frequency",
                source_kind="modern_multi_source_frequency",
                evidence="wordfreq_zipf_frequency",
                score=score,
                confidence=confidence,
                source_term=lemma,
                zipf=zipf,
                match_type="exact",
            )
        )
        hit_count += 1
    source_results.append(_source_result(source_id, "imported", "", hit_count))


def _collect_opensubtitles(
    source_results: list[dict[str, object]],
    *,
    hits_by_lemma: dict[str, list[ExternalHit]],
    ascii_candidate_index: Mapping[str, str],
    path: Path | None,
    provided_text: str | None,
    fetch_network: bool,
) -> None:
    source_id = "olastor_opensubtitles_cistem"
    text, status, issue = _source_text(
        path=path,
        provided_text=provided_text,
        url=OLASTOR_OPENSUBTITLES_CSV_URL if fetch_network else None,
    )
    if not text:
        source_results.append(_source_result(source_id, status, issue, 0))
        return
    rows: list[tuple[str, float]] = []
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        key = _ascii_key(row.get("word"))
        freq = _safe_float(row.get("freq")) or 0.0
        if key and freq > 0.0:
            rows.append((key, freq))
    rows.sort(key=lambda item: (-item[1], item[0]))
    max_freq = max((freq for _, freq in rows), default=1.0)
    hit_count = 0
    seen: set[str] = set()
    for rank, (key, freq) in enumerate(rows, start=1):
        lemma = ascii_candidate_index.get(key)
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        score = _log_score(freq, ceiling=max_freq)
        hits_by_lemma[lemma].append(
            ExternalHit(
                source_id=source_id,
                source_label="olastor OpenSubtitles CISTEM frequency",
                source_kind="subtitle_dialogue_stem_frequency",
                evidence="opensubtitles_cistem_frequency",
                score=score,
                confidence=0.50,
                source_term=key,
                match_type="ascii_key_to_cistem_stem",
                frequency=freq,
                rank=rank,
            )
        )
        hit_count += 1
    source_results.append(_source_result(source_id, status, issue, hit_count))


def _collect_klexikon_titles(
    source_results: list[dict[str, object]],
    *,
    hits_by_lemma: dict[str, list[ExternalHit]],
    candidate_index: Mapping[str, str],
    path: Path | None,
    provided_text: str | None,
    fetch_network: bool,
) -> None:
    source_id = "klexikon_child_encyclopedia_titles"
    text, status, issue = _source_text(
        path=path,
        provided_text=provided_text,
        url=KLEXIKON_ARTICLES_JSON_URL if fetch_network else None,
    )
    if not text:
        source_results.append(_source_result(source_id, status, issue, 0))
        return
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        source_results.append(_source_result(source_id, "failed", str(exc), 0))
        return
    hit_count = 0
    seen: set[str] = set()
    for row in _as_sequence(payload):
        item = _as_mapping(row)
        title = _clean_title(item.get("title"))
        key = _normalize_key(title)
        lemma = candidate_index.get(key)
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        hits_by_lemma[lemma].append(
            ExternalHit(
                source_id=source_id,
                source_label="Klexikon child encyclopedia title",
                source_kind="child_directed_concept_title",
                evidence="klexikon_article_title_exact",
                score=1.0,
                confidence=0.72,
                source_term=title,
                match_type="title_exact",
                document_count=1,
            )
        )
        hit_count += 1
    source_results.append(_source_result(source_id, status, issue, hit_count))


def _collect_text_corpus_sample(
    source_results: list[dict[str, object]],
    *,
    hits_by_lemma: dict[str, list[ExternalHit]],
    candidate_index: Mapping[str, str],
    source_id: str,
    source_label: str,
    source_kind: str,
    evidence: str,
    path: Path | None,
    provided_text: str | None,
    confidence: float,
) -> None:
    text, status, issue = _source_text(path=path, provided_text=provided_text, url=None)
    if not text:
        source_results.append(_source_result(source_id, "not_provided", issue, 0))
        return
    documents = list(_iter_text_documents(text))
    counts: Counter[str] = Counter()
    doc_counts: Counter[str] = Counter()
    for document in documents:
        doc_seen: set[str] = set()
        for token in _german_tokens(document):
            lemma = candidate_index.get(_normalize_key(token))
            if not lemma:
                continue
            counts[lemma] += 1
            doc_seen.add(lemma)
        doc_counts.update(doc_seen)
    max_count = max(counts.values(), default=1)
    for lemma, count in counts.items():
        hits_by_lemma[lemma].append(
            ExternalHit(
                source_id=source_id,
                source_label=source_label,
                source_kind=source_kind,
                evidence=evidence,
                score=_log_score(count, ceiling=max_count),
                confidence=confidence,
                source_term=lemma,
                match_type="sample_token_exact",
                frequency=float(count),
                document_count=int(doc_counts[lemma]),
                token_count=int(count),
            )
        )
    source_results.append(_source_result(source_id, status, issue, len(counts)))


def _collect_german_commons_manifest(
    source_results: list[dict[str, object]],
    *,
    provided_text: str | None,
    fetch_network: bool,
) -> None:
    source_id = "german_commons_manifest"
    text = provided_text
    status = "provided"
    issue = ""
    if text is None:
        if not fetch_network:
            source_results.append(_source_result(source_id, "skipped", "network disabled", 0))
            return
        try:
            text = _fetch_text(GERMAN_COMMONS_DATASET_API_URL)
            status = "fetched_manifest"
        except (OSError, URLError, TimeoutError) as exc:
            source_results.append(_source_result(source_id, "failed", str(exc), 0))
            return
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        source_results.append(_source_result(source_id, "failed", str(exc), 0))
        return
    card = _as_mapping(payload.get("cardData"))
    configs = _as_sequence(card.get("configs"))
    source_results.append(
        {
            **_source_result(source_id, status, issue, 0),
            "config_count": len(configs),
            "dataset_license": ", ".join(str(item) for item in _as_sequence(card.get("license"))),
            "decision": "configured_manifest_only",
            "reason": (
                "Manifest is available, but full corpus ingestion requires a sampled parquet/JSONL "
                "artifact to avoid accidentally downloading a very large corpus."
            ),
        }
    )


def _overlay_from_hits(hits_by_lemma: Mapping[str, Sequence[ExternalHit]]) -> dict[str, object]:
    overlay: dict[str, object] = {}
    for lemma, raw_hits in hits_by_lemma.items():
        hits = _dedupe_hits(raw_hits)
        source_ids = sorted({hit.source_id for hit in hits})
        modern_hits = [hit for hit in hits if hit.source_id in MODERN_SOURCE_IDS]
        child_hits = [hit for hit in hits if hit.source_id in CHILD_SOURCE_IDS]
        archive_hits = [hit for hit in hits if hit.source_id in ARCHIVE_SOURCE_IDS]
        wordfreq_hit = _first_hit(hits, "wordfreq_de_multi_source")
        opensubtitles_hit = _first_hit(hits, "olastor_opensubtitles_cistem")
        klexikon_hit = _first_hit(hits, "klexikon_child_encyclopedia_titles")
        modern_score = max((hit.score or 0.0 for hit in modern_hits), default=0.0)
        archive_score = max((hit.score or 0.0 for hit in archive_hits), default=0.0)
        confidence_miss = 1.0
        for hit in hits:
            confidence_miss *= 1.0 - max(0.0, min(1.0, hit.confidence))
        overlay[lemma] = {
            "term": lemma,
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "evidence_count": len(hits),
            "confidence": _round_float(1.0 - confidence_miss),
            "modern_source_known": bool(modern_hits),
            "modern_frequency_score": _round_float(modern_score),
            "child_source_known": bool(child_hits),
            "archive_source_known": bool(archive_hits),
            "archive_attestation_score": _round_float(archive_score),
            "wordfreq_known": bool(wordfreq_hit),
            "wordfreq_zipf": _round_float(wordfreq_hit.zipf if wordfreq_hit else None),
            "wordfreq_commonness_score": _round_float(wordfreq_hit.score if wordfreq_hit else None),
            "opensubtitles_known": bool(opensubtitles_hit),
            "opensubtitles_frequency": _round_float(
                opensubtitles_hit.frequency if opensubtitles_hit else None
            ),
            "opensubtitles_rank": opensubtitles_hit.rank if opensubtitles_hit else None,
            "opensubtitles_frequency_score": _round_float(
                opensubtitles_hit.score if opensubtitles_hit else None
            ),
            "klexikon_title_known": bool(klexikon_hit),
            "hit_evidence": [
                {
                    "source_id": hit.source_id,
                    "source_kind": hit.source_kind,
                    "evidence": hit.evidence,
                    "score": _round_float(hit.score),
                    "confidence": _round_float(hit.confidence),
                    "frequency": _round_float(hit.frequency),
                    "rank": hit.rank,
                    "document_count": hit.document_count,
                    "token_count": hit.token_count,
                    "zipf": _round_float(hit.zipf),
                    "source_term": hit.source_term,
                    "match_type": hit.match_type,
                    "subset": hit.subset,
                }
                for hit in hits[:16]
            ],
        }
    return overlay


def _candidate_coverage_rows(
    candidate_rows: Sequence[Mapping[str, object]],
    overlay: Mapping[str, object],
) -> list[dict[str, object]]:
    max_rank = max(
        (_safe_float(row.get("core_rank")) or 0.0 for row in candidate_rows), default=1.0
    )
    rows: list[dict[str, object]] = []
    for row in candidate_rows:
        lemma = str(row.get("lemma") or "").strip()
        rank = _safe_float(row.get("core_rank")) or 0.0
        rows.append(
            {
                "lemma": lemma,
                "core_rank": rank,
                "frequency_difficulty": _round_float(_log_ratio(rank, max_rank)),
                "pos": row.get("pos"),
                "external_source": _as_mapping(overlay.get(lemma)),
            }
        )
    return rows


def _source_summary(
    source_results: Sequence[Mapping[str, object]],
    overlay: Mapping[str, object],
) -> dict[str, object]:
    matched_by_source: Counter[str] = Counter()
    for raw in overlay.values():
        matched_by_source.update(
            str(source_id) for source_id in _as_sequence(_as_mapping(raw).get("source_ids"))
        )
    sources = []
    for result in source_results:
        source_id = str(result.get("source_id") or "")
        row = dict(result)
        row["matched_lemma_count"] = matched_by_source.get(source_id, 0)
        sources.append(row)
    return {
        "sources": sources,
        "source_hit_count": sum(int(row.get("hit_count") or 0) for row in source_results),
        "overlay_term_count": len(overlay),
    }


def _build_findings(
    *,
    candidate_rows: Sequence[Mapping[str, object]],
    source_results: Sequence[Mapping[str, object]],
    overlay: Mapping[str, object],
) -> list[dict[str, object]]:
    findings = [
        _finding(
            "PASS" if candidate_rows else "FAIL",
            "frequency_rows_available",
            f"Loaded {len(candidate_rows)} en-de frequency rows.",
        ),
        _finding(
            "PASS" if overlay else "WARN",
            "external_overlay_available",
            f"Matched external evidence to {len(overlay)} German candidate lemmas.",
        ),
    ]
    for source in source_results:
        status = str(source.get("status") or "")
        hit_count = int(source.get("hit_count") or 0)
        if status in {"failed"}:
            level = "WARN"
        elif status in {"not_provided", "skipped"}:
            level = "INFO"
        else:
            level = "PASS" if hit_count or status == "fetched_manifest" else "WARN"
        findings.append(
            _finding(
                level,
                f"source_{source.get('source_id')}",
                f"{status}; parsed {hit_count} hit(s).",
            )
        )
    return findings


def _source_result(source_id: str, status: str, issue: str, hit_count: int) -> dict[str, object]:
    license_name, decision = _source_policy(source_id)
    return {
        "source_id": source_id,
        "status": status,
        "issue": issue,
        "license": license_name,
        "decision": decision,
        "hit_count": int(hit_count),
    }


def _source_policy(source_id: str) -> tuple[str, str]:
    if source_id == "wordfreq_de_multi_source":
        return "Apache-2.0 code; bundled data from documented upstream sources", "included_sidecar"
    if source_id == "olastor_opensubtitles_cistem":
        return (
            "repository data; OpenSubtitles/COW-derived attribution required",
            "included_cautious_sidecar",
        )
    if source_id == "klexikon_child_encyclopedia_titles":
        return "CC BY-SA text data; MIT code wrapper", "included_sidecar"
    if source_id == "german_commons_sample":
        return "ODC-BY dataset with document-level licenses", "optional_local_sample"
    if source_id == "german_commons_manifest":
        return "ODC-BY dataset manifest", "configured_manifest_only"
    if source_id == "german_literary_archive_sample":
        return "depends on supplied archive sample", "optional_local_sample"
    return "unknown", "not_ingested"


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


def _candidate_index(candidate_rows: Sequence[Mapping[str, object]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in candidate_rows:
        lemma = str(row.get("lemma") or "").strip()
        key = _normalize_key(lemma)
        if lemma and key and key not in result:
            result[key] = lemma
    return result


def _ascii_candidate_index(candidate_rows: Sequence[Mapping[str, object]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in candidate_rows:
        lemma = str(row.get("lemma") or "").strip()
        key = _ascii_key(lemma)
        if lemma and key and key not in result:
            result[key] = lemma
    return result


def _source_text(
    *,
    path: Path | None,
    provided_text: str | None,
    url: str | None,
) -> tuple[str, str, str]:
    if provided_text is not None:
        return provided_text, "provided", ""
    if path is not None:
        try:
            return (
                Path(path).expanduser().read_text(encoding="utf-8", errors="replace"),
                "read_file",
                "",
            )
        except OSError as exc:
            return "", "failed", str(exc)
    if url is not None:
        try:
            return _fetch_text(url), "fetched", ""
        except (OSError, URLError, TimeoutError) as exc:
            return "", "failed", str(exc)
    return "", "not_provided", "no source text/path/url configured"


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:  # noqa: S310 - fixed audit URLs.
        return response.read().decode("utf-8", errors="replace")


def _iter_text_documents(text: str) -> Sequence[str]:
    docs: list[str] = []
    stripped = text.strip()
    if not stripped:
        return ()
    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            docs.append(line)
            continue
        if isinstance(row, Mapping):
            doc_text = str(row.get("text") or row.get("content") or "").strip()
            if doc_text:
                docs.append(doc_text)
    return tuple(docs)


def _german_tokens(text: str) -> Sequence[str]:
    return re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß-]{1,}", text)


def _clean_title(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or "")).strip()
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_key(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _ascii_key(value: object) -> str:
    text = _normalize_key(value)
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if char.isascii() and char.isalnum()
    )


def _dedupe_hits(raw_hits: Sequence[ExternalHit]) -> list[ExternalHit]:
    best: dict[tuple[str, str, str, str | None], ExternalHit] = {}
    for hit in raw_hits:
        key = (hit.source_id, hit.evidence, hit.match_type, hit.source_term)
        current = best.get(key)
        if current is None or (hit.score or 0.0) > (current.score or 0.0):
            best[key] = hit
    return sorted(
        best.values(),
        key=lambda hit: (
            hit.source_id,
            -(hit.score or 0.0),
            hit.source_term or "",
        ),
    )


def _first_hit(hits: Sequence[ExternalHit], source_id: str) -> ExternalHit | None:
    for hit in hits:
        if hit.source_id == source_id:
            return hit
    return None


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _log_ratio(value: object, max_value: object) -> float:
    numerator = math.log1p(max(0.0, _safe_float(value) or 0.0))
    denominator = math.log1p(max(1.0, _safe_float(max_value) or 1.0))
    return min(1.0, max(0.0, numerator / denominator))


def _log_score(value: object, *, ceiling: float) -> float:
    return min(1.0, math.log1p(max(0.0, _safe_float(value) or 0.0)) / math.log1p(ceiling))


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _round_float(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None and math.isfinite(numeric) else None


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _pct(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric * 100:.1f}%"


def _fmt_float(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
