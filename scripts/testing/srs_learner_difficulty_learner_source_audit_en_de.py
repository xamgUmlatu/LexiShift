#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import io
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
    / "srs_learner_difficulty_learner_source_audit_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_de_latest.md"
)
USER_AGENT = "LexiShift learner-source audit/0.1 (local development; contact via repo)"

OPENLINGO_GERMAN_DICTIONARY_RAW_URL = (
    "https://raw.githubusercontent.com/pretzelai/openlingo/HEAD/words/german.json"
)
SPRACHOMAT_GOETHE_STEMS_RAW_URL = (
    "https://raw.githubusercontent.com/technologiestiftung/sprach-o-mat/HEAD/"
    "dictionary_a1a2b1_onlystems.csv"
)
GOETHE_A1_WORDLIST_PDF_URL = "https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf"
ODENET_FILENAME = "odenet_oneline.xml"

LEVEL_SCORES: Mapping[str, float] = {
    "A1": 0.08,
    "A2": 0.18,
    "B1": 0.32,
    "B2": 0.48,
    "C1": 0.64,
    "C2": 0.78,
}
LEVEL_ORDER = {level: index for index, level in enumerate(LEVEL_SCORES)}
GERMAN_ARTICLE_RE = re.compile(
    r"^(?:der|die|das|den|dem|des|ein|eine|einen|einem|einer|eines)\s+",
    re.IGNORECASE,
)
GERMAN_SPLIT_RE = re.compile(r"[;/|()]")
ODENET_ENTRY_RE = re.compile(
    r"<LexicalEntry\b(?P<attrs>[^>]*)>(?P<body>.*?)</LexicalEntry>",
    re.DOTALL,
)
ODENET_LEMMA_RE = re.compile(r"<Lemma\b(?P<attrs>[^>]*)/?>", re.DOTALL)


@dataclass(frozen=True)
class SourceHit:
    source_id: str
    source_label: str
    source_kind: str
    evidence: str
    score: float
    confidence: float
    level: str | None = None
    rank: int | None = None
    source_term: str | None = None
    match_type: str = "exact"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-de learner/core source candidates and build a German-lemma overlay. "
            "This does not change production ranking or runtime scoring."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--odenet-path", type=Path)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        odenet_path=args.odenet_path,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
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
    odenet_path: Path | None = None,
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    source_texts: Mapping[str, str] | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    source_texts = dict(source_texts or {})
    source_results: list[dict[str, object]] = []
    exact_hits: dict[str, list[SourceHit]] = defaultdict(list)
    stem_hits: dict[str, list[SourceHit]] = defaultdict(list)
    paths = build_helper_paths()
    resolved_odenet_path = odenet_path or paths.language_packs_dir / ODENET_FILENAME

    _collect_source(
        source_results,
        exact_hits=exact_hits,
        stem_hits=stem_hits,
        source_id="openlingo_mit_german_dictionary",
        fetch_url=OPENLINGO_GERMAN_DICTIONARY_RAW_URL,
        parser=parse_openlingo_german_dictionary,
        provided_text=source_texts.get("openlingo_mit_german_dictionary"),
    )
    _collect_source(
        source_results,
        exact_hits=exact_hits,
        stem_hits=stem_hits,
        source_id="sprachomat_goethe_a1a2b1_stems",
        fetch_url=SPRACHOMAT_GOETHE_STEMS_RAW_URL,
        parser=parse_sprachomat_goethe_stems,
        provided_text=source_texts.get("sprachomat_goethe_a1a2b1_stems"),
    )
    _collect_goethe_a1_pdf_source(
        source_results,
        exact_hits=exact_hits,
        stem_hits=stem_hits,
        provided_text=source_texts.get("goethe_official_a1_wordlist"),
    )
    _collect_source(
        source_results,
        exact_hits=exact_hits,
        stem_hits=stem_hits,
        source_id="odenet_basiswortschatz",
        fetch_path=resolved_odenet_path,
        parser=parse_odenet_basiswortschatz,
        provided_text=source_texts.get("odenet_basiswortschatz"),
    )

    resolved_frequency_db = frequency_db or default_frequency_db_path(
        PAIR,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    candidate_rows = _load_frequency_rows(resolved_frequency_db, top_n=top_n)
    overlay = _overlay_for_candidates(
        candidate_rows,
        exact_hits=exact_hits,
        stem_hits=stem_hits,
    )
    coverage_rows = _candidate_coverage_rows(candidate_rows, overlay)
    matched_rows = [row for row in coverage_rows if row.get("learner_source")]
    findings = _build_findings(
        source_results=source_results,
        candidate_rows=candidate_rows,
        overlay=overlay,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    source_summary = _source_summary(source_results, exact_hits, stem_hits, overlay)
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_de_learner_sources_ready" if status == "ok" else "en_de_learner_sources_need_review"
        ),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "inputs": {
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "odenet_path": str(resolved_odenet_path) if resolved_odenet_path else None,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
            "sources": source_summary["sources"],
        },
        "methodology": {
            "purpose": (
                "Collect German learner/core source evidence as a diagnostic overlay before "
                "formula tuning."
            ),
            "source_policy": (
                "OpenLingo is ingested as MIT CEFR-like learner dictionary evidence. "
                "Sprach-O-Mat stems are ingested as cautious Goethe-derived stem evidence "
                "because the repo is MIT but the underlying vocabulary origin is more "
                "provenance-sensitive. OdeNet Basiswortschatz entries are ingested as "
                "exact basic-vocabulary evidence only; synonym expansion is intentionally "
                "not used for difficulty."
            ),
            "score_semantics": (
                "learner_core_score is a weak target score for bounded formula experiments. "
                "It is not treated as official CEFR truth."
            ),
            "stem_semantics": (
                "Stem evidence is matched only by conservative normalized-prefix matching "
                "with lower confidence; short stems are discarded to reduce false positives."
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
                        _as_mapping(row.get("learner_source")).get("source_ids")
                    )
                ).most_common()
            ),
            "top_matched_samples": matched_rows[:sample_limit],
            "highest_score_matched_samples": sorted(
                matched_rows,
                key=lambda row: (
                    -(_safe_float(row.get("frequency_difficulty")) or 0.0),
                    str(row.get("lemma") or ""),
                ),
            )[:sample_limit],
        },
        "source_overlay": overlay,
        "next_source_candidates": [
            {
                "source_id": "zix_understandability_cefr_vocab",
                "url": "https://github.com/machinelearningZH/zix_understandability-index",
                "license": "MIT",
                "decision": "not_ingested_this_slice",
                "reason": (
                    "Promising CEFR-ish German vocabulary artifact, but its useful files are "
                    "Parquet and need a schema/provenance audit before adding another source."
                ),
            },
            {
                "source_id": "kaikki_german_wiktionary",
                "url": "https://kaikki.org/dictionary/German/index.html",
                "license": "Wiktionary-derived CC BY-SA/GFDL style obligations",
                "decision": "not_ingested_this_slice",
                "reason": (
                    "Promising lexical metadata parity source, but not a pedagogical source. "
                    "Add separately with attribution handling and source-specific tests."
                ),
            },
            {
                "source_id": "openthesaurus_de",
                "url": "https://www.openthesaurus.de/about/download",
                "license": "LGPL 2.1+",
                "decision": "not_ingested_this_slice",
                "reason": (
                    "Available locally and useful for semantic grouping, but synonym links are "
                    "not direct difficulty evidence. Keep out of learner difficulty until a "
                    "specific semantic-usefulness hypothesis needs it."
                ),
            },
        ],
        "findings": findings,
        "limitations": [
            "OpenLingo CEFR labels are useful learner evidence, not official CEFR certification.",
            "Sprach-O-Mat rows are stems rather than lemmas; the matched evidence is intentionally weak.",
            "OdeNet Basiswortschatz is basic-vocabulary evidence, not a graded A1/A2/B1 list.",
            "This sidecar intentionally does not alter production ranking, runtime behavior, or manual correction tables.",
        ],
    }
    return report


def parse_openlingo_german_dictionary(text: str) -> Sequence[SourceHit]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, list):
        return ()
    by_term: dict[str, SourceHit] = {}
    for raw_row in payload:
        row = _as_mapping(raw_row)
        if row.get("useful_for_flashcard") is False:
            continue
        raw_term = str(row.get("word") or "").strip()
        if not raw_term:
            continue
        level = str(row.get("cefr_level") or "").strip().upper()
        if level not in LEVEL_SCORES:
            continue
        rank = _safe_int(row.get("word_frequency")) or None
        confidence = 0.82 if level in {"A1", "A2", "B1", "B2"} else 0.68
        for term in _candidate_terms(raw_term):
            normalized = _normalize_key(term)
            if not normalized:
                continue
            hit = SourceHit(
                source_id="openlingo_mit_german_dictionary",
                source_label="OpenLingo MIT German dictionary",
                source_kind="mit_cefr_like_dictionary",
                evidence="cefr_like_dictionary_entry",
                score=LEVEL_SCORES[level],
                confidence=confidence,
                level=level,
                rank=rank,
                source_term=raw_term,
                match_type="exact",
            )
            current = by_term.get(normalized)
            if current is None or (hit.score, hit.rank or 999999) < (
                current.score,
                current.rank or 999999,
            ):
                by_term[normalized] = hit
    return tuple(by_term.values())


def parse_sprachomat_goethe_stems(text: str) -> Sequence[SourceHit]:
    hits: list[SourceHit] = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        level = str(row.get("level") or "").strip().upper()
        stem = _normalize_key(row.get("stem"))
        if level not in LEVEL_SCORES or not _usable_stem(stem):
            continue
        confidence = 0.40 if len(stem) >= 5 else 0.30
        hits.append(
            SourceHit(
                source_id="sprachomat_goethe_a1a2b1_stems",
                source_label="Sprach-O-Mat Goethe A1/A2/B1 stems",
                source_kind="mit_goethe_derived_stem_list",
                evidence="goethe_level_stem_prefix",
                score=LEVEL_SCORES[level],
                confidence=confidence,
                level=level,
                source_term=stem,
                match_type="stem_prefix",
            )
        )
    return tuple(hits)


def parse_goethe_a1_wordlist_text(text: str) -> Sequence[SourceHit]:
    by_term: dict[str, SourceHit] = {}
    for raw_line in text.splitlines():
        term = _goethe_headword_from_line(raw_line)
        if not term:
            continue
        for candidate in _candidate_terms(term):
            normalized = _normalize_key(candidate)
            if not normalized:
                continue
            by_term[normalized] = SourceHit(
                source_id="goethe_official_a1_wordlist",
                source_label="Goethe-Institut A1 Start Deutsch 1 wordlist",
                source_kind="official_a1_exam_wordlist",
                evidence="official_a1_wordlist_entry",
                score=LEVEL_SCORES["A1"],
                confidence=0.76,
                level="A1",
                source_term=candidate,
                match_type="exact",
            )
    return tuple(by_term.values())


def parse_odenet_basiswortschatz(text: str) -> Sequence[SourceHit]:
    by_term: dict[str, SourceHit] = {}
    for entry_match in ODENET_ENTRY_RE.finditer(text):
        entry_attrs = entry_match.group("attrs")
        if _attr_value(entry_attrs, "dc:type") != "Basiswortschatz":
            continue
        confidence_score = _safe_float(_attr_value(entry_attrs, "confidenceScore"))
        confidence = 0.35 + (0.20 * max(0.0, min(1.0, confidence_score or 1.0)))
        lemma_match = ODENET_LEMMA_RE.search(entry_match.group("body"))
        if not lemma_match:
            continue
        raw_term = html.unescape(_attr_value(lemma_match.group("attrs"), "writtenForm"))
        if not raw_term:
            continue
        pos = html.unescape(_attr_value(lemma_match.group("attrs"), "partOfSpeech"))
        evidence = "basiswortschatz_entry" if not pos else f"basiswortschatz_entry:{pos}"
        for term in _candidate_terms(raw_term):
            normalized = _normalize_key(term)
            if not normalized:
                continue
            hit = SourceHit(
                source_id="odenet_basiswortschatz",
                source_label="OdeNet Basiswortschatz",
                source_kind="cc_by_sa_basic_vocabulary",
                evidence=evidence,
                score=0.18,
                confidence=confidence,
                source_term=raw_term,
                match_type="exact",
            )
            current = by_term.get(normalized)
            if current is None or hit.confidence > current.confidence:
                by_term[normalized] = hit
    return tuple(by_term.values())


def render_markdown(report: Mapping[str, object]) -> str:
    lines: list[str] = [
        "# en-de Learner Source Audit",
        "",
        f"Status: `{report.get('status')}`",
        f"Decision: `{report.get('decision')}`",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Purpose: audit German learner/core sources before en-de formula tuning. "
        "This artifact is a sidecar only; production ranking is unchanged.",
        "",
    ]
    summary = _as_mapping(report.get("source_summary"))
    lines.extend(
        [
            "## Source Summary",
            "",
            f"- Overlay candidate lemmas: `{summary.get('overlay_term_count', 0)}`",
            f"- Source hits: `{summary.get('source_hit_count', 0)}`",
            f"- Short/unsafe stems skipped: `{summary.get('skipped_short_stem_count', 0)}`",
            "",
            "| Source | Status | License | Hits | Unique terms | Matched lemmas | Decision |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for raw in _as_sequence(summary.get("sources")):
        source = _as_mapping(raw)
        lines.append(
            f"| `{source.get('source_id')}` | `{source.get('status')}` | "
            f"{source.get('license')} | {source.get('hit_count', 0)} | "
            f"{source.get('unique_term_count', 0)} | {source.get('matched_lemma_count', 0)} | "
            f"{source.get('decision')} |"
        )
    lines.append("")

    coverage = _as_mapping(report.get("candidate_coverage"))
    lines.extend(
        [
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
        ("Highest Difficulty Matched Samples", "highest_score_matched_samples"),
    ):
        rows = _as_sequence(coverage.get(key))
        if not rows:
            continue
        lines.extend(
            [
                f"## {title}",
                "",
                "| Lemma | Difficulty | Core score | Confidence | Sources | Levels | Evidence |",
                "| --- | ---: | ---: | ---: | --- | --- | --- |",
            ]
        )
        for raw in rows:
            row = _as_mapping(raw)
            learner = _as_mapping(row.get("learner_source"))
            evidence = "; ".join(
                str(_as_mapping(item).get("evidence") or "")
                for item in _as_sequence(learner.get("hit_evidence"))[:2]
            )
            lines.append(
                f"| `{row.get('lemma')}` | {_fmt_float(row.get('frequency_difficulty'))} | "
                f"{_fmt_float(learner.get('learner_core_score'))} | "
                f"{_fmt_float(learner.get('confidence'))} | "
                f"{', '.join(str(item) for item in _as_sequence(learner.get('source_ids')))} | "
                f"{', '.join(str(item) for item in _as_sequence(learner.get('levels')))} | "
                f"{evidence} |"
            )
        lines.append("")

    next_sources = _as_sequence(report.get("next_source_candidates"))
    if next_sources:
        lines.extend(["## Next Source Candidates", "", "| Source | License | Decision | Reason |"])
        lines.append("| --- | --- | --- | --- |")
        for raw in next_sources:
            row = _as_mapping(raw)
            lines.append(
                f"| `{row.get('source_id')}` | {row.get('license')} | "
                f"`{row.get('decision')}` | {row.get('reason')} |"
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


def _collect_source(
    source_results: list[dict[str, object]],
    *,
    exact_hits: dict[str, list[SourceHit]],
    stem_hits: dict[str, list[SourceHit]],
    source_id: str,
    parser,
    provided_text: str | None,
    fetch_url: str | None = None,
    fetch_path: Path | None = None,
) -> None:
    text = provided_text
    status = "provided"
    issue = ""
    if text is None:
        if fetch_path is not None:
            try:
                text = Path(fetch_path).expanduser().read_text(encoding="utf-8", errors="replace")
                status = "read_file"
            except OSError as exc:
                text = ""
                status = "failed"
                issue = str(exc)
        elif fetch_url is not None:
            try:
                text = _fetch_text(fetch_url)
                status = "fetched"
            except (OSError, URLError, TimeoutError) as exc:
                text = ""
                status = "failed"
                issue = str(exc)
        else:
            text = ""
            status = "failed"
            issue = "no source location configured"
    parsed_hits: Sequence[SourceHit] = ()
    if text:
        try:
            parsed_hits = tuple(parser(text))
        except Exception as exc:  # pragma: no cover - defensive source drift path.
            status = "failed"
            issue = f"parse failed: {exc}"
            parsed_hits = ()
    unique_terms = set()
    skipped_short_stems = 0
    for hit in parsed_hits:
        normalized = _normalize_key(hit.source_term)
        if not normalized:
            continue
        unique_terms.add(normalized)
        if hit.match_type == "stem_prefix":
            if _usable_stem(normalized):
                stem_hits[normalized].append(hit)
            else:
                skipped_short_stems += 1
        else:
            exact_hits[normalized].append(hit)
    license_name, decision = _source_policy(source_id)
    source_results.append(
        {
            "source_id": source_id,
            "url": fetch_url or "",
            "path": str(fetch_path) if fetch_path else "",
            "status": status,
            "issue": issue,
            "license": license_name,
            "decision": decision,
            "hit_count": len(parsed_hits),
            "unique_term_count": len(unique_terms),
            "skipped_short_stem_count": skipped_short_stems,
        }
    )


def _collect_goethe_a1_pdf_source(
    source_results: list[dict[str, object]],
    *,
    exact_hits: dict[str, list[SourceHit]],
    stem_hits: dict[str, list[SourceHit]],
    provided_text: str | None,
) -> None:
    source_id = "goethe_official_a1_wordlist"
    text = provided_text
    status = "provided"
    issue = ""
    if text is None:
        try:
            text = _extract_pdf_text(_fetch_bytes(GOETHE_A1_WORDLIST_PDF_URL))
            status = "fetched_pdf"
        except Exception as exc:  # pragma: no cover - defensive source/network drift.
            text = ""
            status = "failed"
            issue = str(exc)
    parsed_hits: Sequence[SourceHit] = ()
    if text:
        try:
            parsed_hits = tuple(parse_goethe_a1_wordlist_text(text))
        except Exception as exc:  # pragma: no cover - defensive source drift path.
            status = "failed"
            issue = f"parse failed: {exc}"
            parsed_hits = ()
    unique_terms = set()
    for hit in parsed_hits:
        normalized = _normalize_key(hit.source_term)
        if not normalized:
            continue
        unique_terms.add(normalized)
        if hit.match_type == "stem_prefix":
            if _usable_stem(normalized):
                stem_hits[normalized].append(hit)
        else:
            exact_hits[normalized].append(hit)
    license_name, decision = _source_policy(source_id)
    source_results.append(
        {
            "source_id": source_id,
            "url": GOETHE_A1_WORDLIST_PDF_URL,
            "path": "",
            "status": status,
            "issue": issue,
            "license": license_name,
            "decision": decision,
            "hit_count": len(parsed_hits),
            "unique_term_count": len(unique_terms),
            "skipped_short_stem_count": 0,
        }
    )


def _overlay_for_candidates(
    candidate_rows: Sequence[Mapping[str, object]],
    *,
    exact_hits: Mapping[str, Sequence[SourceHit]],
    stem_hits: Mapping[str, Sequence[SourceHit]],
) -> dict[str, object]:
    stem_index: dict[str, list[tuple[str, Sequence[SourceHit]]]] = defaultdict(list)
    for stem, hits in stem_hits.items():
        stem_index[stem[:3]].append((stem, hits))

    overlay: dict[str, object] = {}
    for row in candidate_rows:
        lemma = str(row.get("lemma") or "").strip()
        key = _normalize_key(lemma)
        if not key:
            continue
        hits: list[SourceHit] = list(exact_hits.get(key, ()))
        for stem, raw_hits in stem_index.get(key[:3], ()):
            if _stem_matches(key, stem):
                hits.extend(raw_hits)
        term_overlay = _overlay_entry(lemma, hits)
        if term_overlay:
            overlay[lemma] = term_overlay
    return overlay


def _overlay_entry(lemma: str, raw_hits: Sequence[SourceHit]) -> dict[str, object]:
    hits = _dedupe_hits(raw_hits)
    if not hits:
        return {}
    source_ids = sorted({hit.source_id for hit in hits})
    scores = [hit.score for hit in hits if hit.score is not None]
    confidence = 1.0
    for hit in hits:
        confidence *= 1.0 - max(0.0, min(1.0, hit.confidence))
    confidence = 1.0 - confidence
    levels = sorted(
        {hit.level for hit in hits if hit.level},
        key=lambda level: LEVEL_ORDER.get(level or "", 999),
    )
    ranks_by_source: dict[str, int] = {}
    for hit in hits:
        if hit.rank is None:
            continue
        current = ranks_by_source.get(hit.source_id)
        ranks_by_source[hit.source_id] = (
            int(hit.rank) if current is None else min(current, int(hit.rank))
        )
    return {
        "term": lemma,
        "source_ids": source_ids,
        "source_count": len(source_ids),
        "evidence_count": len(hits),
        "learner_core_score": _round_float(min(scores) if scores else 0.5),
        "confidence": _round_float(confidence),
        "levels": levels,
        "min_level": levels[0] if levels else None,
        "ranks_by_source": ranks_by_source,
        "hit_evidence": [
            {
                "source_id": hit.source_id,
                "source_kind": hit.source_kind,
                "evidence": hit.evidence,
                "score": _round_float(hit.score),
                "confidence": _round_float(hit.confidence),
                "level": hit.level,
                "rank": hit.rank,
                "source_term": hit.source_term,
                "match_type": hit.match_type,
            }
            for hit in hits[:12]
        ],
    }


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
                "learner_source": _as_mapping(overlay.get(lemma)),
            }
        )
    return rows


def _source_summary(
    source_results: Sequence[Mapping[str, object]],
    exact_hits: Mapping[str, Sequence[SourceHit]],
    stem_hits: Mapping[str, Sequence[SourceHit]],
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
        "exact_source_term_count": len(exact_hits),
        "stem_source_term_count": len(stem_hits),
        "skipped_short_stem_count": sum(
            int(row.get("skipped_short_stem_count") or 0) for row in source_results
        ),
    }


def _build_findings(
    *,
    source_results: Sequence[Mapping[str, object]],
    candidate_rows: Sequence[Mapping[str, object]],
    overlay: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    findings.append(
        _finding(
            "PASS" if candidate_rows else "FAIL",
            "frequency_rows_available",
            f"Loaded {len(candidate_rows)} en-de frequency rows.",
        )
    )
    for source in source_results:
        hit_count = int(source.get("hit_count") or 0)
        status = str(source.get("status") or "")
        findings.append(
            _finding(
                "PASS" if hit_count and status != "failed" else "WARN",
                f"source_{source.get('source_id')}",
                f"{status}; parsed {hit_count} hit(s).",
            )
        )
    findings.append(
        _finding(
            "PASS" if overlay else "WARN",
            "candidate_overlay_available",
            f"Matched learner-source evidence to {len(overlay)} German candidate lemmas.",
        )
    )
    return findings


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


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=40) as response:  # noqa: S310 - fixed audit URLs.
        return response.read().decode("utf-8", errors="replace")


def _fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=40) as response:  # noqa: S310 - fixed audit URL.
        return response.read()


def _extract_pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _candidate_terms(value: object) -> tuple[str, ...]:
    raw = unicodedata.normalize("NFC", str(value or "")).strip()
    if not raw:
        return ()
    cleaned = GERMAN_ARTICLE_RE.sub("", raw).strip()
    pieces = [cleaned]
    pieces.extend(part.strip() for part in GERMAN_SPLIT_RE.split(cleaned))
    result: list[str] = []
    for piece in pieces:
        piece = piece.strip().strip(",.;:!?\"'“”„")
        if not piece or len(piece) < 2:
            continue
        if piece not in result:
            result.append(piece)
    return tuple(result)


def _goethe_headword_from_line(value: object) -> str:
    line = unicodedata.normalize("NFC", str(value or "")).replace("\t", " ")
    line = re.sub(r"\s+", " ", line).strip()
    if not line:
        return ""
    if line.startswith("VS_") or line in {"INVeNTAre", "INVENTARE"}:
        return ""
    if len(line) == 1 and line.isalpha():
        return ""
    if line[0].isupper() and not line.lower().startswith(("der ", "die ", "das ")):
        return ""
    line = re.sub(r"^\(sich\)\s+", "", line, flags=re.IGNORECASE)
    article_match = re.match(
        r"^(?:(?:der/die|der|die|das)\s+)(?P<body>.+)$",
        line,
        flags=re.IGNORECASE,
    )
    if article_match:
        return _goethe_trim_headword(article_match.group("body"))
    if line[0].islower() or line.startswith(("öff", "ä", "ö", "ü")):
        return _goethe_trim_headword(line)
    return ""


def _goethe_trim_headword(value: str) -> str:
    text = str(value or "").strip()
    text = re.split(r"\s{2,}", text, maxsplit=1)[0].strip()
    text = re.split(r"\s+[A-ZÄÖÜ„0-9]", text, maxsplit=1)[0].strip()
    text = text.split(",", 1)[0].strip()
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text).strip()
    tokens = text.split()
    if not tokens:
        return ""
    if tokens[0].endswith("-"):
        return tokens[0].rstrip("-")
    if len(tokens) >= 2 and tokens[1] in {"sein", "fahren", "frites", "viel"}:
        return " ".join(tokens[:2])
    return tokens[0]


def _normalize_key(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().lower()
    text = GERMAN_ARTICLE_RE.sub("", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _usable_stem(stem: str) -> bool:
    if len(stem) < 4:
        return False
    if not any(char.isalpha() for char in stem):
        return False
    return True


def _stem_matches(key: str, stem: str) -> bool:
    if not _usable_stem(stem):
        return False
    if key == stem:
        return True
    max_extra = 4 if len(stem) <= 4 else 6
    return key.startswith(stem) and len(key) <= len(stem) + max_extra


def _dedupe_hits(raw_hits: Sequence[SourceHit]) -> list[SourceHit]:
    best: dict[tuple[str, str, str, str | None], SourceHit] = {}
    for hit in raw_hits:
        key = (hit.source_id, hit.evidence, hit.match_type, hit.level)
        current = best.get(key)
        if current is None or hit.score < current.score:
            best[key] = hit
    return sorted(
        best.values(),
        key=lambda hit: (
            LEVEL_ORDER.get(hit.level or "", 999),
            hit.score,
            -hit.confidence,
            hit.source_id,
            hit.source_term or "",
        ),
    )


def _source_policy(source_id: str) -> tuple[str, str]:
    if source_id == "openlingo_mit_german_dictionary":
        return "MIT", "included_sidecar"
    if source_id == "sprachomat_goethe_a1a2b1_stems":
        return "MIT repo; Goethe-derived stem data", "included_cautious_sidecar"
    if source_id == "goethe_official_a1_wordlist":
        return (
            "Goethe-Institut public exam-prep PDF; attribution/source notice required",
            "included_cautious_sidecar",
        )
    if source_id == "odenet_basiswortschatz":
        return "CC BY-SA 4.0", "included_sidecar"
    return "unknown", "not_ingested"


def _attr_value(attrs: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*([\"'])(?P<value>.*?)\1", attrs, re.DOTALL)
    return str(match.group("value") or "").strip() if match else ""


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _log_ratio(value: object, max_value: object) -> float:
    numerator = math.log1p(max(0.0, _safe_float(value) or 0.0))
    denominator = math.log1p(max(1.0, _safe_float(max_value) or 1.0))
    return min(1.0, max(0.0, numerator / denominator))


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


def _safe_int(value: object) -> int:
    try:
        if value is None or value == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


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
