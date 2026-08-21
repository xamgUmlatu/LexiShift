#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
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
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_SAMPLE_LIMIT = 20
DEFAULT_SOURCE_LABEL = "freq-es-spalex-v1"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_es_latest.md"
)
USER_AGENT = "LexiShift learner-source audit/0.1 (local development; contact via repo)"

WIKTIONARY_SPANISH1000_RAW_URL = (
    "https://en.wiktionary.org/w/index.php?title=Wiktionary:Frequency_lists/Spanish1000&action=raw"
)
ESPANJAPELI_WORDS_RAW_URL = (
    "https://raw.githubusercontent.com/lsspkk/espanjapeli/main/svelte/src/lib/data/words.ts"
)
OPENLINGO_A1_SPANISH_RAW_URL = (
    "https://raw.githubusercontent.com/pretzelai/openlingo/main/content/steve-jobs-a1-spanish.md"
)
OPENLINGO_SPANISH_DICTIONARY_RAW_URL = (
    "https://raw.githubusercontent.com/pretzelai/openlingo/main/words/spanish.json"
)

LEVEL_SCORES: Mapping[str, float] = {
    "A1": 0.08,
    "A2": 0.18,
    "B1": 0.32,
    "B2": 0.48,
    "C1": 0.64,
    "C2": 0.78,
}
LEVEL_ORDER = {level: index for index, level in enumerate(LEVEL_SCORES)}
ARTICLE_RE = re.compile(r"^(?:el|la|los|las|un|una|unos|unas|lo|al|del)\s+", re.IGNORECASE)
WIKI_LINK_RE = re.compile(r"\[\[([^]|#]+)(?:#[^]|]+)?(?:\|([^]]+))?\]\]")
SPANISH_WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[-'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*")


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit safe en-es learner/core source candidates and build a lemma-keyed "
            "sidecar overlay. This does not change production ranking or runtime scoring."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
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
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    source_texts: Mapping[str, str] | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    source_texts = dict(source_texts or {})
    source_results: list[dict[str, object]] = []
    hits: dict[str, list[SourceHit]] = defaultdict(list)

    _collect_source(
        source_results,
        hits,
        source_id="wiktionary_spanish1000",
        fetch_url=WIKTIONARY_SPANISH1000_RAW_URL,
        parser=parse_wiktionary_spanish1000,
        provided_text=source_texts.get("wiktionary_spanish1000"),
    )
    _collect_source(
        source_results,
        hits,
        source_id="espanjapeli_mit_words",
        fetch_url=ESPANJAPELI_WORDS_RAW_URL,
        parser=parse_espanjapeli_words,
        provided_text=source_texts.get("espanjapeli_mit_words"),
    )
    _collect_source(
        source_results,
        hits,
        source_id="openlingo_mit_a1_spanish",
        fetch_url=OPENLINGO_A1_SPANISH_RAW_URL,
        parser=parse_openlingo_a1_spanish,
        provided_text=source_texts.get("openlingo_mit_a1_spanish"),
    )
    _collect_source(
        source_results,
        hits,
        source_id="openlingo_mit_spanish_dictionary",
        fetch_url=OPENLINGO_SPANISH_DICTIONARY_RAW_URL,
        parser=parse_openlingo_spanish_dictionary,
        provided_text=source_texts.get("openlingo_mit_spanish_dictionary"),
    )

    overlay = _overlay_from_hits(hits)
    paths = build_helper_paths()
    resolved_frequency_db = _resolve_frequency_db(frequency_db, paths.frequency_packs_dir)
    candidate_rows, candidate_status = _candidate_rows(
        frequency_db=resolved_frequency_db,
        overlay=overlay,
        top_n=top_n,
    )
    findings = _build_findings(source_results, candidate_status)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"

    source_summary = _source_summary(source_results, hits)
    matched_rows = [row for row in candidate_rows if row.get("learner_source")]
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_es_learner_sources_ready" if status == "ok" else "en_es_learner_sources_need_review"
        ),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "inputs": {
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
            "sources": source_summary["sources"],
        },
        "methodology": {
            "purpose": (
                "Collect product-usable or product-plausible learner/core Spanish sources "
                "as a diagnostic overlay before formula tuning."
            ),
            "source_policy": (
                "Only sources with permissive/product-plausible licenses are included in "
                "the overlay. NonCommercial/proprietary/AGPL candidate sources remain "
                "documented as rejected or research-only, not ingested."
            ),
            "score_semantics": (
                "learner_core_score is a weak target score for bounded formula experiments. "
                "It is not a CEFR claim unless a source explicitly supplies a CEFR label."
            ),
            "absence_semantics": (
                "Absence from a tiny lesson/list source is not evidence. Absence from the "
                "broad OpenLingo dictionary is recorded for shape experiments, but the "
                "audit does not convert absence into a penalty by itself."
            ),
        },
        "source_summary": source_summary,
        "candidate_coverage": {
            "candidate_count": len(candidate_rows),
            "matched_candidate_count": len(matched_rows),
            "matched_candidate_ratio": _ratio(len(matched_rows), len(candidate_rows)),
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
        "rejected_or_research_only_sources": [
            {
                "source_id": "codingfriends_basic_vocabulary_word_lists",
                "url": "https://github.com/CodingFriends/basic-vocabulary-word-lists",
                "license": "CC BY-NC 4.0",
                "decision": "not_ingested",
                "reason": (
                    "Useful beginner vocabulary shape, but NonCommercial terms are not "
                    "product-safe for this app without a separate license decision."
                ),
            },
            {
                "source_id": "artcc_freelingo_es_vocabulary",
                "url": "https://github.com/ArtCC/freelingo",
                "license": "AGPL-3.0",
                "decision": "not_ingested",
                "reason": (
                    "Rich CEFR-labeled Spanish sets, but AGPL is not suitable for direct "
                    "product data ingestion without a deliberate licensing decision."
                ),
            },
            {
                "source_id": "gamescomputersplay_vocabulary_test",
                "url": "https://github.com/gamescomputersplay/vocabulary-test",
                "license": "not_confirmed",
                "decision": "not_ingested",
                "reason": (
                    "Spanish levels are described by the project as frequency-ranked chunks, "
                    "so they are not independent learner-level evidence."
                ),
            },
        ],
        "findings": findings,
        "limitations": [
            "No authoritative open DELE/CEFR Spanish vocabulary source was found in this pass.",
            "The MIT lesson/list sources are useful beginner/core presence evidence, but small and not authoritative.",
            "The OpenLingo dictionary is broad CEFR-like learner evidence under MIT, but it is still not an official DELE/CEFR specification.",
            "Wiktionary Spanish1000 is a subtitle frequency source, not a curriculum source; it is kept separate from CEFR-style evidence.",
            "This sidecar intentionally does not alter production ranking, runtime behavior, or manual correction tables.",
        ],
    }
    return report


def parse_wiktionary_spanish1000(text: str) -> Sequence[SourceHit]:
    hits: list[SourceHit] = []
    for cells in _wiki_table_rows(text):
        if len(cells) < 4:
            continue
        rank_text, word_cell, _ppm_cell, lemma_cell = cells[:4]
        rank_match = re.search(r"\d+", rank_text)
        if not rank_match:
            continue
        rank = int(rank_match.group(0))
        if rank <= 0 or rank > 1000:
            continue
        score = 0.08 + 0.22 * (math.log1p(rank) / math.log1p(1000))
        surface_terms = _wiki_link_terms(word_cell) or _candidate_terms(word_cell)
        lemma_terms = _wiki_link_terms(lemma_cell) or _candidate_terms(lemma_cell)
        for term in surface_terms:
            hits.append(
                SourceHit(
                    source_id="wiktionary_spanish1000",
                    source_label="Wiktionary Spanish1000 subtitles",
                    source_kind="subtitle_frequency_core",
                    evidence="surface_top1000",
                    score=score,
                    confidence=0.62,
                    rank=rank,
                    source_term=term,
                )
            )
        for term in lemma_terms:
            hits.append(
                SourceHit(
                    source_id="wiktionary_spanish1000",
                    source_label="Wiktionary Spanish1000 subtitles",
                    source_kind="subtitle_frequency_core",
                    evidence="lemma_top1000",
                    score=score,
                    confidence=0.70,
                    rank=rank,
                    source_term=term,
                )
            )
    return hits


def parse_espanjapeli_words(text: str) -> Sequence[SourceHit]:
    hits: list[SourceHit] = []
    for block in _typescript_object_blocks(text):
        spanish_match = re.search(r"spanish:\s*'([^']+)'", block)
        if not spanish_match:
            continue
        raw_term = spanish_match.group(1)
        level_match = re.search(r"cefrLevel:\s*'([ABC][12])'", block)
        rank_match = re.search(r"rank:\s*(\d+)", block)
        level = level_match.group(1) if level_match else None
        rank = int(rank_match.group(1)) if rank_match else None
        score = LEVEL_SCORES.get(level or "", 0.16)
        confidence = 0.58 if level else 0.45
        evidence = "explicit_cefr_field" if level else "beginner_topic_list_presence"
        for term in _candidate_terms(raw_term):
            hits.append(
                SourceHit(
                    source_id="espanjapeli_mit_words",
                    source_label="espanjapeli MIT Spanish words",
                    source_kind="mit_beginner_word_list",
                    evidence=evidence,
                    score=score,
                    confidence=confidence,
                    level=level,
                    rank=rank,
                    source_term=raw_term,
                )
            )
    return hits


def parse_openlingo_a1_spanish(text: str) -> Sequence[SourceHit]:
    terms: list[str] = []
    for line in text.splitlines():
        pair_match = re.match(r'\s*-\s*"([^"]+)"\s*=', line)
        if pair_match:
            terms.append(pair_match.group(1))
        for words_match in re.finditer(r'srsWords:\s*"([^"]+)"', line):
            terms.extend(words_match.group(1).split())
    hits: list[SourceHit] = []
    for raw_term in terms:
        for term in _candidate_terms(raw_term):
            hits.append(
                SourceHit(
                    source_id="openlingo_mit_a1_spanish",
                    source_label="OpenLingo MIT A1 Spanish lesson",
                    source_kind="mit_a1_lesson_vocab",
                    evidence="a1_lesson_presence",
                    score=0.10,
                    confidence=0.38,
                    level="A1",
                    source_term=raw_term,
                )
            )
    return hits


def parse_openlingo_spanish_dictionary(text: str) -> Sequence[SourceHit]:
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
        # Treat this as broad learner-dictionary evidence, not official CEFR truth.
        confidence = 0.74 if level in {"A1", "A2", "B1", "B2"} else 0.62
        for term in _candidate_terms(raw_term):
            normalized = _normalize_term(term)
            if not normalized:
                continue
            hit = SourceHit(
                source_id="openlingo_mit_spanish_dictionary",
                source_label="OpenLingo MIT Spanish dictionary",
                source_kind="mit_cefr_like_dictionary",
                evidence="cefr_like_dictionary_entry",
                score=LEVEL_SCORES[level],
                confidence=confidence,
                level=level,
                rank=rank,
                source_term=raw_term,
            )
            current = by_term.get(normalized)
            if current is None or hit.score < current.score:
                by_term[normalized] = hit
    return tuple(by_term.values())


def render_markdown(report: Mapping[str, object]) -> str:
    lines: list[str] = []
    lines.append("# en-es Learner Source Audit")
    lines.append("")
    lines.append(f"Status: `{report.get('status')}`")
    lines.append(f"Decision: `{report.get('decision')}`")
    lines.append(f"Generated: `{report.get('generated_at')}`")
    lines.append("")
    lines.append(
        "Purpose: audit Spanish learner/core sources before en-es formula tuning. "
        "This artifact is a sidecar only; production ranking is unchanged."
    )
    lines.append("")
    summary = _as_mapping(report.get("source_summary"))
    lines.append("## Source Summary")
    lines.append("")
    lines.append(f"- Overlay terms: `{summary.get('overlay_term_count', 0)}`")
    lines.append(f"- Source hits: `{summary.get('source_hit_count', 0)}`")
    lines.append("")
    lines.append("| Source | Status | License | Hits | Unique terms | Decision |")
    lines.append("| --- | --- | --- | ---: | ---: | --- |")
    for raw in _as_sequence(summary.get("sources")):
        source = _as_mapping(raw)
        lines.append(
            f"| `{source.get('source_id')}` | `{source.get('status')}` | "
            f"{source.get('license')} | {source.get('hit_count', 0)} | "
            f"{source.get('unique_term_count', 0)} | {source.get('decision')} |"
        )
    lines.append("")

    coverage = _as_mapping(report.get("candidate_coverage"))
    lines.append("## Candidate Coverage")
    lines.append("")
    lines.append(f"- Candidate rows checked: `{coverage.get('candidate_count', 0)}`")
    lines.append(f"- Matched rows: `{coverage.get('matched_candidate_count', 0)}`")
    lines.append(f"- Matched ratio: `{_pct(coverage.get('matched_candidate_ratio'))}`")
    lines.append("")
    matched_by_source = _as_mapping(coverage.get("matched_by_source"))
    if matched_by_source:
        lines.append("| Source | Matched candidates |")
        lines.append("| --- | ---: |")
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
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Lemma | Difficulty | Core score | Confidence | Sources |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for raw in rows:
            row = _as_mapping(raw)
            learner = _as_mapping(row.get("learner_source"))
            lines.append(
                f"| `{row.get('lemma')}` | {_fmt_float(row.get('frequency_difficulty'))} | "
                f"{_fmt_float(learner.get('learner_core_score'))} | "
                f"{_fmt_float(learner.get('confidence'))} | "
                f"{', '.join(str(item) for item in _as_sequence(learner.get('source_ids')))} |"
            )
        lines.append("")

    rejected = _as_sequence(report.get("rejected_or_research_only_sources"))
    if rejected:
        lines.append("## Rejected Or Research-Only Sources")
        lines.append("")
        lines.append("| Source | License | Decision | Reason |")
        lines.append("| --- | --- | --- | --- |")
        for raw in rejected:
            row = _as_mapping(raw)
            lines.append(
                f"| `{row.get('source_id')}` | {row.get('license')} | "
                f"`{row.get('decision')}` | {row.get('reason')} |"
            )
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| Level | Code | Message |")
    lines.append("| --- | --- | --- |")
    for raw in _as_sequence(report.get("findings")):
        row = _as_mapping(raw)
        lines.append(f"| {row.get('level')} | `{row.get('code')}` | {row.get('message')} |")
    lines.append("")

    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _collect_source(
    source_results: list[dict[str, object]],
    hits_by_term: dict[str, list[SourceHit]],
    *,
    source_id: str,
    fetch_url: str,
    parser,
    provided_text: str | None,
) -> None:
    text = provided_text
    status = "provided"
    issue = ""
    if text is None:
        try:
            text = _fetch_text(fetch_url)
            status = "fetched"
        except (OSError, URLError, TimeoutError) as exc:
            text = ""
            status = "failed"
            issue = str(exc)
    parsed_hits: Sequence[SourceHit] = ()
    if text:
        try:
            parsed_hits = tuple(parser(text))
        except Exception as exc:  # pragma: no cover - defensive source drift path.
            status = "failed"
            issue = f"parse failed: {exc}"
            parsed_hits = ()
    unique_terms = set()
    for hit in parsed_hits:
        for term in _candidate_terms(hit.source_term or "") or [hit.source_term or ""]:
            normalized = _normalize_term(term)
            if not normalized:
                continue
            unique_terms.add(normalized)
            hits_by_term[normalized].append(hit)
    license_name, decision = _source_policy(source_id)
    source_results.append(
        {
            "source_id": source_id,
            "url": fetch_url,
            "status": status,
            "issue": issue,
            "license": license_name,
            "decision": decision,
            "hit_count": len(parsed_hits),
            "unique_term_count": len(unique_terms),
        }
    )


def _overlay_from_hits(hits: Mapping[str, Sequence[SourceHit]]) -> dict[str, object]:
    overlay: dict[str, object] = {}
    for term, raw_term_hits in sorted(hits.items()):
        term_hits = _dedupe_source_hits(raw_term_hits)
        if not term_hits:
            continue
        source_ids = sorted({hit.source_id for hit in term_hits})
        scores = [hit.score for hit in term_hits if hit.score is not None]
        confidences = [max(0.0, min(1.0, hit.confidence)) for hit in term_hits]
        confidence = 1.0
        for value in confidences:
            confidence *= 1.0 - value
        confidence = 1.0 - confidence
        levels = sorted(
            {hit.level for hit in term_hits if hit.level},
            key=lambda level: LEVEL_ORDER.get(level or "", 999),
        )
        ranks_by_source: dict[str, int] = {}
        for hit in term_hits:
            if hit.rank is None:
                continue
            current = ranks_by_source.get(hit.source_id)
            ranks_by_source[hit.source_id] = (
                int(hit.rank) if current is None else min(current, int(hit.rank))
            )
        overlay[term] = {
            "term": term,
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "evidence_count": len(term_hits),
            "learner_core_score": _round_float(min(scores) if scores else 0.5),
            "confidence": _round_float(confidence),
            "levels": levels,
            "min_level": levels[0] if levels else None,
            "ranks_by_source": ranks_by_source,
            "hit_evidence": [
                {
                    "source_id": hit.source_id,
                    "evidence": hit.evidence,
                    "score": _round_float(hit.score),
                    "confidence": _round_float(hit.confidence),
                    "level": hit.level,
                    "rank": hit.rank,
                    "source_term": hit.source_term,
                }
                for hit in sorted(
                    term_hits,
                    key=lambda item: (
                        item.score,
                        item.source_id,
                        item.rank if item.rank is not None else 999999,
                    ),
                )[:8]
            ],
        }
    return overlay


def _dedupe_source_hits(hits: Sequence[SourceHit]) -> list[SourceHit]:
    by_key: dict[tuple[object, ...], SourceHit] = {}
    for hit in hits:
        key = (
            hit.source_id,
            hit.evidence,
            hit.level,
            hit.rank,
            _normalize_term(hit.source_term or ""),
        )
        current = by_key.get(key)
        if current is None or hit.score < current.score:
            by_key[key] = hit
    return list(by_key.values())


def _candidate_rows(
    *,
    frequency_db: Path | None,
    overlay: Mapping[str, object],
    top_n: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not frequency_db or not frequency_db.exists():
        return [], {"status": "missing_frequency_db"}
    try:
        seeds = build_seed_candidates(
            frequency_db=frequency_db,
            config=SeedSelectionConfig(
                language_pair=PAIR,
                top_n=top_n,
                require_jmdict=False,
                source_label=DEFAULT_SOURCE_LABEL,
                sort_by_admission_weight=False,
            ),
        )
    except Exception as exc:  # pragma: no cover - defensive corrupt DB path.
        return [], {"status": "seed_build_failed", "error": str(exc)}
    rows = []
    for seed in seeds:
        learner_source = _lookup_overlay(seed.lemma, overlay)
        base_weight = _safe_float(seed.base_weight)
        row = {
            "lemma": seed.lemma,
            "core_rank": _safe_float(seed.core_rank),
            "frequency_difficulty": _round_float(1.0 - base_weight)
            if base_weight is not None
            else None,
            "pos": seed.pos_canonical or seed.pos_raw or seed.pos_bucket,
        }
        if learner_source:
            row["learner_source"] = learner_source
        rows.append(row)
    return rows, {"status": "ok"}


def _lookup_overlay(lemma: str, overlay: Mapping[str, object]) -> Mapping[str, object]:
    normalized = _normalize_term(lemma)
    if normalized in overlay:
        return _as_mapping(overlay.get(normalized))
    return {}


def _source_summary(
    source_results: Sequence[Mapping[str, object]],
    hits: Mapping[str, Sequence[SourceHit]],
) -> dict[str, object]:
    return {
        "overlay_term_count": len(hits),
        "source_hit_count": sum(len(value) for value in hits.values()),
        "sources": list(source_results),
    }


def _build_findings(
    source_results: Sequence[Mapping[str, object]],
    candidate_status: Mapping[str, object],
) -> list[dict[str, object]]:
    findings = []
    if candidate_status.get("status") != "ok":
        findings.append(
            {
                "level": "WARN",
                "code": str(candidate_status.get("status") or "candidate_status_unknown"),
                "message": "Candidate coverage could not be computed; source overlay was still built.",
            }
        )
    failed = [row for row in source_results if row.get("status") == "failed"]
    for row in failed:
        findings.append(
            {
                "level": "WARN",
                "code": f"source_fetch_or_parse_failed:{row.get('source_id')}",
                "message": str(row.get("issue") or "Source fetch or parse failed."),
            }
        )
    if not any(_safe_int(row.get("hit_count")) > 0 for row in source_results):
        findings.append(
            {
                "level": "FAIL",
                "code": "no_learner_source_hits",
                "message": "No included learner-source rows were parsed.",
            }
        )
    if not findings:
        findings.append(
            {
                "level": "OK",
                "code": "learner_sources_parsed",
                "message": "Included learner/core source overlays parsed successfully.",
            }
        )
    return findings


def _wiki_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    cells: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "|-":
            if cells:
                rows.append(cells)
            cells = []
            continue
        if line.startswith("|") and not line.startswith("|}") and not line.startswith("!"):
            cells.append(line.lstrip("|").strip())
    if cells:
        rows.append(cells)
    return rows


def _wiki_link_terms(text: str) -> list[str]:
    terms = []
    for match in WIKI_LINK_RE.finditer(text):
        raw = match.group(2) or match.group(1)
        terms.extend(_candidate_terms(raw))
    return sorted(dict.fromkeys(terms))


def _typescript_object_blocks(text: str) -> list[str]:
    blocks = []
    for match in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, flags=re.DOTALL):
        block = match.group(0)
        if "spanish:" in block:
            blocks.append(block)
    return blocks


def _candidate_terms(raw: str) -> list[str]:
    cleaned = _clean_source_term(raw)
    if not cleaned:
        return []
    candidates = {cleaned}
    candidates.add(ARTICLE_RE.sub("", cleaned).strip())
    if "/" in cleaned:
        candidates.update(_slash_variants(cleaned))
    expanded: set[str] = set()
    for candidate in candidates:
        candidate = _clean_source_term(candidate)
        if not candidate:
            continue
        expanded.add(candidate)
        no_article = ARTICLE_RE.sub("", candidate).strip()
        if no_article:
            expanded.add(no_article)
    return sorted(term for term in expanded if term)


def _slash_variants(term: str) -> set[str]:
    variants = {term.replace("/", "")}
    variants.add(term.replace("o/a", "o"))
    variants.add(term.replace("o/a", "a"))
    variants.add(term.replace("/a", ""))
    if term.endswith("/a"):
        variants.add(term[:-2] + "a")
    variants.add(term.replace("el/la ", ""))
    variants.add(term.replace("el/la ", "el "))
    variants.add(term.replace("el/la ", "la "))
    return variants


def _clean_source_term(raw: str) -> str:
    value = unicodedata.normalize("NFC", str(raw or ""))
    value = value.replace("...", " ").replace("…", " ")
    value = value.strip().strip('"').strip("'")
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.strip("!¡?¿.,;:[]{}")
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def _normalize_term(raw: str) -> str:
    value = _clean_source_term(raw)
    tokens = SPANISH_WORD_RE.findall(value)
    if not tokens:
        return ""
    return " ".join(tokens)


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def _resolve_frequency_db(path: Path | None, frequency_packs_dir: Path) -> Path | None:
    if path:
        return path
    resolved = default_frequency_db_path(PAIR, frequency_packs_dir=frequency_packs_dir)
    return resolved if resolved and resolved.exists() else resolved


def _source_policy(source_id: str) -> tuple[str, str]:
    if source_id == "wiktionary_spanish1000":
        return "Wiktionary CC BY-SA/GFDL terms", "included_sidecar"
    if source_id == "espanjapeli_mit_words":
        return "MIT", "included_sidecar"
    if source_id == "openlingo_mit_a1_spanish":
        return "MIT", "included_sidecar"
    if source_id == "openlingo_mit_spanish_dictionary":
        return "MIT", "included_sidecar"
    return "unknown", "review_required"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ratio(count: int, total: int) -> float:
    return 0.0 if total <= 0 else round(float(count) / float(total), 6)


def _pct(value: object) -> str:
    numeric = _safe_float(value) or 0.0
    return f"{numeric * 100:.2f}%"


def _fmt_float(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _round_float(value: object) -> float:
    numeric = _safe_float(value)
    return 0.0 if numeric is None else round(numeric, 6)


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric) or math.isinf(numeric):
        return None
    return numeric


def _safe_int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or value is None:
        return ()
    return value if isinstance(value, Sequence) else ()


if __name__ == "__main__":
    raise SystemExit(main())
