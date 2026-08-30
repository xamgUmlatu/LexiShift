#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_LANGUAGE_PACKS_ROOT = DEFAULT_DATA_ROOT / "language_packs"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-de-default.sqlite"
DEFAULT_EN_ES_OVERLAY = TEST_OUTPUTS_ROOT / "srs_topic_reviewed_overlay_merged_en_es_latest.json"
DEFAULT_EN_JA_OVERLAY = TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_en_ja_latest.json"
DEFAULT_ES_DE_FREEDICT_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "freedict-es-de" / "main.sqlite"
DEFAULT_JA_DE_FREEDICT_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "freedict-ja-de" / "main.sqlite"
DEFAULT_ES_EN_WIKTIONARY_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "wiktionary-es-en" / "main.sqlite"
DEFAULT_ES_EN_FREEDICT_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "freedict-es-en" / "main.sqlite"
DEFAULT_EN_DE_FREEDICT_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "freedict-en-de" / "main.sqlite"
DEFAULT_DE_WIKTIONARY_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "wiktionary-de-en" / "main.sqlite"
DEFAULT_EN_WIKTIONARY_DB = DEFAULT_LANGUAGE_PACKS_ROOT / "wiktionary-en-es.sqlite"
DEFAULT_JMDICT_PATH = DEFAULT_LANGUAGE_PACKS_ROOT / "jmdict-ja-en" / "JMdict_e"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_overlay_en_de_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_overlay_en_de_latest.md"

LANGUAGE_PAIR = "en-de"
OVERLAY_ID = "srs_topic_direct_translation_overlay_en_de_v1"
SOURCE_CHANNEL = "cross_lp_direct_translation_topic_candidates"
DEFAULT_TOPICS = (
    "animals",
    "food_cooking",
    "sports_fitness",
    "medicine_health",
    "travel_places_transport",
    "music_media_entertainment",
    "finance_business",
    "law_politics_civics",
    "arts_literature_humanities",
)

REJECT_REVIEW_STATES = {
    "rejected",
    "reject_wrong_topic",
    "reject_wrong_sense",
    "reject_secondary_or_obscure_sense",
    "review_candidate_not_runtime_effective",
}

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "animals": (
        "animal",
        "mammal",
        "bird",
        "fish",
        "insect",
        "reptile",
        "amphibian",
        "arachnid",
        "crustacean",
        "mollusk",
        "mollusc",
        "zoology",
        "zoological",
        "livestock",
        "bovine",
        "canine",
        "feline",
        "equine",
        "rodent",
        "primate",
        "pinniped",
        "species",
        "organism",
        "beast",
        "pig",
        "cow",
        "cattle",
        "dog",
        "canid",
        "cat",
        "horse",
        "sheep",
        "goat",
        "suidae",
        "equus",
        "felis",
        "tier",
        "säugetier",
        "vogel",
        "fisch",
        "insekt",
    ),
    "food_cooking": (
        "food",
        "dish",
        "meal",
        "cuisine",
        "culinary",
        "cooking",
        "cookery",
        "edible",
        "ingredient",
        "fruit",
        "vegetable",
        "meat",
        "bread",
        "cheese",
        "soup",
        "sauce",
        "drink",
        "beverage",
        "beer",
        "wine",
        "pastry",
        "lebensmittel",
        "speise",
        "gericht",
        "getränk",
        "obst",
        "gemüse",
    ),
    "sports_fitness": (
        "sport",
        "sports",
        "athletic",
        "athletics",
        "exercise",
        "fitness",
        "soccer",
        "football",
        "tennis",
        "basketball",
        "baseball",
        "volleyball",
        "cycling",
        "running",
        "swimming",
        "gymnastics",
        "game",
        "sportart",
    ),
    "medicine_health": (
        "medicine",
        "medical",
        "health",
        "disease",
        "illness",
        "symptom",
        "anatomy",
        "body",
        "organ",
        "hospital",
        "doctor",
        "physician",
        "drug",
        "pharmacy",
        "pathology",
        "surgery",
        "medizin",
        "krankheit",
        "gesundheit",
    ),
    "travel_places_transport": (
        "travel",
        "tourism",
        "transport",
        "transportation",
        "vehicle",
        "traffic",
        "road",
        "railway",
        "train",
        "airport",
        "aircraft",
        "ship",
        "bus",
        "car",
        "city",
        "country",
        "geography",
        "navigation",
        "reise",
        "verkehr",
    ),
    "music_media_entertainment": (
        "music",
        "musical",
        "song",
        "instrument",
        "film",
        "movie",
        "television",
        "theater",
        "theatre",
        "media",
        "entertainment",
        "radio",
        "journalism",
        "newspaper",
        "musik",
        "film",
    ),
    "finance_business": (
        "finance",
        "financial",
        "money",
        "banking",
        "business",
        "commerce",
        "company",
        "corporation",
        "stock",
        "market",
        "accounting",
        "tax",
        "investment",
        "wirtschaft",
        "finanzen",
    ),
    "law_politics_civics": (
        "law",
        "legal",
        "court",
        "judge",
        "crime",
        "criminal",
        "politics",
        "political",
        "government",
        "parliament",
        "election",
        "civic",
        "civil",
        "recht",
        "politik",
    ),
    "arts_literature_humanities": (
        "art",
        "arts",
        "literature",
        "literary",
        "poetry",
        "poem",
        "novel",
        "painting",
        "sculpture",
        "history",
        "historical",
        "philosophy",
        "religion",
        "mythology",
        "kunst",
        "literatur",
    ),
}

STOP_ENGLISH_TERMS = {
    "",
    "a",
    "an",
    "the",
    "one",
    "someone",
    "something",
    "somebody",
    "person",
    "thing",
    "act",
    "action",
    "quality",
    "state",
    "process",
}
GERMAN_LEADING_ARTICLES = (
    "der ",
    "die ",
    "das ",
    "den ",
    "dem ",
    "des ",
    "ein ",
    "eine ",
    "einen ",
    "einem ",
    "einer ",
    "eines ",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate review-only en-de topic candidates by translating trusted en-es/en-ja "
            "topic rows directly into German, then confirming German candidates with local "
            "German Wiktionary/Wiktextract evidence."
        )
    )
    parser.add_argument("--source-overlay", action="append", type=Path, default=[])
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--es-de-freedict-db", type=Path, default=DEFAULT_ES_DE_FREEDICT_DB)
    parser.add_argument("--ja-de-freedict-db", type=Path, default=DEFAULT_JA_DE_FREEDICT_DB)
    parser.add_argument("--es-en-wiktionary-db", type=Path, default=DEFAULT_ES_EN_WIKTIONARY_DB)
    parser.add_argument("--es-en-freedict-db", type=Path, default=DEFAULT_ES_EN_FREEDICT_DB)
    parser.add_argument("--en-de-freedict-db", type=Path, default=DEFAULT_EN_DE_FREEDICT_DB)
    parser.add_argument("--de-wiktionary-db", type=Path, default=DEFAULT_DE_WIKTIONARY_DB)
    parser.add_argument("--en-wiktionary-db", type=Path, default=DEFAULT_EN_WIKTIONARY_DB)
    parser.add_argument("--jmdict-path", type=Path, default=DEFAULT_JMDICT_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--topics", nargs="*", default=list(DEFAULT_TOPICS))
    parser.add_argument("--top-n", type=int, default=50000)
    parser.add_argument("--source-row-limit", type=int, default=0)
    parser.add_argument("--max-direct-per-source", type=int, default=80)
    parser.add_argument("--max-english-per-source", type=int, default=12)
    parser.add_argument("--max-german-per-english", type=int, default=24)
    parser.add_argument("--max-translation-rank", type=int, default=80)
    parser.add_argument(
        "--allow-english-pivot-fallback",
        action="store_true",
        help="Allow the old English-pivot route when no direct German dictionary candidate exists.",
    )
    parser.add_argument(
        "--include-en-ja-review-candidates",
        action="store_true",
        help="Also use en-ja auto-review rows. Default keeps only runtime-effective/trusted source rows.",
    )
    parser.add_argument(
        "--require-strong-german-evidence",
        action="store_true",
        help="Emit only candidates with direct German-side topic keyword evidence.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_overlays = args.source_overlay or [DEFAULT_EN_ES_OVERLAY, DEFAULT_EN_JA_OVERLAY]
    report = build_report(
        source_overlays=source_overlays,
        frequency_db=args.frequency_db,
        es_de_freedict_db=args.es_de_freedict_db,
        ja_de_freedict_db=args.ja_de_freedict_db,
        es_en_wiktionary_db=args.es_en_wiktionary_db,
        es_en_freedict_db=args.es_en_freedict_db,
        en_de_freedict_db=args.en_de_freedict_db,
        de_wiktionary_db=args.de_wiktionary_db,
        en_wiktionary_db=args.en_wiktionary_db,
        jmdict_path=args.jmdict_path,
        topics=tuple(args.topics or DEFAULT_TOPICS),
        top_n=max(1, int(args.top_n)),
        source_row_limit=max(0, int(args.source_row_limit)),
        max_direct_per_source=max(1, int(args.max_direct_per_source)),
        max_english_per_source=max(1, int(args.max_english_per_source)),
        max_german_per_english=max(1, int(args.max_german_per_english)),
        max_translation_rank=max(1, int(args.max_translation_rank)),
        allow_english_pivot_fallback=bool(args.allow_english_pivot_fallback),
        include_en_ja_review_candidates=bool(args.include_en_ja_review_candidates),
        require_strong_german_evidence=bool(args.require_strong_german_evidence),
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
    source_overlays: Sequence[Path],
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    es_de_freedict_db: Path = DEFAULT_ES_DE_FREEDICT_DB,
    ja_de_freedict_db: Path = DEFAULT_JA_DE_FREEDICT_DB,
    es_en_wiktionary_db: Path = DEFAULT_ES_EN_WIKTIONARY_DB,
    es_en_freedict_db: Path = DEFAULT_ES_EN_FREEDICT_DB,
    en_de_freedict_db: Path = DEFAULT_EN_DE_FREEDICT_DB,
    de_wiktionary_db: Path = DEFAULT_DE_WIKTIONARY_DB,
    en_wiktionary_db: Path = DEFAULT_EN_WIKTIONARY_DB,
    jmdict_path: Path = DEFAULT_JMDICT_PATH,
    topics: Sequence[str] = DEFAULT_TOPICS,
    top_n: int = 50000,
    source_row_limit: int = 0,
    max_direct_per_source: int = 80,
    max_english_per_source: int = 12,
    max_german_per_english: int = 24,
    max_translation_rank: int = 80,
    allow_english_pivot_fallback: bool = False,
    include_en_ja_review_candidates: bool = False,
    require_strong_german_evidence: bool = False,
    generated_at: str | None = None,
) -> dict[str, object]:
    topic_set = {str(topic).strip() for topic in topics if str(topic).strip()}
    frequency_rows = _load_frequency_rows(frequency_db, top_n=top_n)
    source_rows, source_diagnostics = _load_source_topic_rows(
        source_overlays,
        topics=topic_set,
        row_limit=source_row_limit,
        include_en_ja_review_candidates=include_en_ja_review_candidates,
    )
    required_pairs = {str(row.get("language_pair") or "") for row in source_rows}
    jmdict_glosses: dict[str, tuple[str, ...]] = {}
    if allow_english_pivot_fallback and "en-ja" in required_pairs:
        jmdict_glosses = _load_jmdict_glosses(jmdict_path, source_rows)

    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    candidate_audit: list[dict[str, object]] = []
    source_usage: Counter[str] = Counter()
    direct_source_usage: Counter[str] = Counter()
    direct_translation_count = 0
    direct_existing_candidate_count = 0
    fallback_source_usage: Counter[str] = Counter()
    english_term_count = 0
    pivot_german_candidate_count = 0
    pivot_existing_candidate_count = 0
    strong_evidence_count = 0
    direct_review_evidence_count = 0
    pivot_review_evidence_count = 0
    duplicate_row_count = 0
    missing_translation_count = 0
    rejected_evidence_count = 0

    es_de = _sqlite_connection(es_de_freedict_db)
    ja_de = _sqlite_connection(ja_de_freedict_db)
    es_wikt = _sqlite_connection(es_en_wiktionary_db) if allow_english_pivot_fallback else None
    es_fd = _sqlite_connection(es_en_freedict_db) if allow_english_pivot_fallback else None
    en_de = _sqlite_connection(en_de_freedict_db) if allow_english_pivot_fallback else None
    de_wikt = _sqlite_connection(de_wiktionary_db)
    en_wikt = _sqlite_connection(en_wiktionary_db) if allow_english_pivot_fallback else None
    english_topic_cache: dict[tuple[str, str], bool] = {}
    try:
        for source_row in source_rows:
            pair = str(source_row.get("language_pair") or "")
            topic = str(source_row.get("topic") or "")
            source_lemma = str(source_row.get("lemma") or "")
            direct_rows = _direct_german_rows_for_source_row(
                source_row,
                es_de_freedict=es_de,
                ja_de_freedict=ja_de,
                max_rows=max_direct_per_source,
                max_rank=max_translation_rank,
            )
            direct_translation_count += len(direct_rows)

            source_german_candidates: list[Mapping[str, object]] = list(direct_rows)
            if not source_german_candidates and allow_english_pivot_fallback:
                english_terms = _english_terms_for_source_row(
                    source_row,
                    es_wiktionary=es_wikt,
                    es_freedict=es_fd,
                    en_wiktionary=en_wikt,
                    jmdict_glosses=jmdict_glosses,
                    topic=topic,
                    english_topic_cache=english_topic_cache,
                    max_terms=max_english_per_source,
                )
                if english_terms:
                    fallback_source_usage[pair] += 1
                    english_term_count += len(english_terms)
                    for english_term in english_terms:
                        german_rows = _english_to_german_candidates(
                            en_de,
                            english_term=english_term,
                            max_rows=max_german_per_english,
                            max_rank=max_translation_rank,
                        )
                        pivot_german_candidate_count += len(german_rows)
                        for german_row in german_rows:
                            if str(german_row.get("pos") or "").strip() == "v":
                                continue
                            for candidate in _german_candidate_terms(german_row.get("translation")):
                                source_german_candidates.append(
                                    {
                                        **german_row,
                                        "term": candidate,
                                        "translation_route": "english_pivot_fallback",
                                        "source_query": english_term,
                                        "english_pivot": english_term,
                                    }
                                )

            if not source_german_candidates:
                missing_translation_count += 1
                candidate_audit.append(
                    _candidate_audit_row(
                        source_row,
                        reason="no_direct_german_translation_candidate",
                    )
                )
                continue

            source_usage[pair] += 1
            if direct_rows:
                direct_source_usage[pair] += 1
            seen_source_candidates: set[tuple[str, str, str]] = set()
            for german_row in source_german_candidates:
                candidate = str(german_row.get("term") or "").strip()
                if not candidate:
                    continue
                route = str(german_row.get("translation_route") or "direct_unknown")
                source_query = str(german_row.get("source_query") or "")
                english_term = str(german_row.get("english_pivot") or "")
                candidate_key = (route, source_query.casefold(), candidate.casefold())
                if candidate_key in seen_source_candidates:
                    continue
                seen_source_candidates.add(candidate_key)
                frequency = _resolve_frequency_row(frequency_rows, candidate)
                if frequency is None:
                    continue
                if route == "english_pivot_fallback":
                    pivot_existing_candidate_count += 1
                else:
                    direct_existing_candidate_count += 1
                evidence = _german_topic_evidence(
                    de_wikt,
                    lemma=str(frequency.get("lemma") or candidate),
                    topic=topic,
                    english_pivot=english_term,
                    direct_translation=route != "english_pivot_fallback",
                )
                if evidence["decision"] == "strong_topic_keyword":
                    strong_evidence_count += 1
                elif evidence["decision"] == "direct_translation_match_needs_review":
                    direct_review_evidence_count += 1
                elif evidence["decision"] == "pivot_gloss_match_needs_review":
                    pivot_review_evidence_count += 1
                else:
                    rejected_evidence_count += 1
                    candidate_audit.append(
                        _candidate_audit_row(
                            source_row,
                            reason=str(evidence["decision"]),
                            english_terms=[english_term] if english_term else [],
                            german_candidate=str(frequency.get("lemma") or candidate),
                            evidence=evidence,
                            translation_route=route,
                            source_query=source_query,
                        )
                    )
                    continue
                if (
                    require_strong_german_evidence
                    and evidence["decision"] != "strong_topic_keyword"
                ):
                    continue
                row = _overlay_row(
                    source_row=source_row,
                    source_pair=pair,
                    source_lemma=source_lemma,
                    german_translation_row=german_row,
                    frequency=frequency,
                    evidence=evidence,
                )
                key = (str(row["lemma"]), str(row["topic"]))
                existing = rows_by_key.get(key)
                if existing is None:
                    rows_by_key[key] = row
                    continue
                duplicate_row_count += 1
                rows_by_key[key] = _merge_duplicate_rows(existing, row)
    finally:
        for connection in (es_de, ja_de, es_wikt, es_fd, en_de, de_wikt, en_wikt):
            if connection is not None:
                connection.close()

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("corpus_rank"), default=999999.0),
            str(row.get("lemma") or ""),
        ),
    )
    summary = _summary(
        rows,
        source_rows=source_rows,
        source_usage=source_usage,
        direct_source_usage=direct_source_usage,
        fallback_source_usage=fallback_source_usage,
        direct_translation_count=direct_translation_count,
        direct_existing_candidate_count=direct_existing_candidate_count,
        english_term_count=english_term_count,
        pivot_german_candidate_count=pivot_german_candidate_count,
        pivot_existing_candidate_count=pivot_existing_candidate_count,
        strong_evidence_count=strong_evidence_count,
        direct_review_evidence_count=direct_review_evidence_count,
        pivot_review_evidence_count=pivot_review_evidence_count,
        rejected_evidence_count=rejected_evidence_count,
        duplicate_row_count=duplicate_row_count,
        missing_translation_count=missing_translation_count,
    )
    status = "ok" if rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_direct_translation_overlay_review_ready"
            if status == "ok"
            else "srs_topic_direct_translation_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": OVERLAY_ID,
        "overlay_policy": {
            "promotion_state": "review_only_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": "FreeDict spa-deu and jpn-deu source dictionaries converted locally",
            "runtime_dependency": "none",
            "candidate_generation": (
                "trusted cross-LP topic rows -> direct source-to-German FreeDict translations "
                "-> German frequency exact match -> local German Wiktionary evidence"
            ),
            "promotion_policy": (
                "Rows are intentionally review-only. Direct German-side topic keyword "
                "evidence is marked separately from weaker direct-translation-only review matches."
            ),
            "match_policy": "frequency_exact_or_casefolded_german_candidate",
            "english_pivot_fallback_enabled": bool(allow_english_pivot_fallback),
        },
        "inputs": {
            "source_overlays": [_repo_path(path) for path in source_overlays],
            "frequency_db": str(frequency_db),
            "top_n": int(top_n),
            "es_de_freedict_db": str(es_de_freedict_db),
            "ja_de_freedict_db": str(ja_de_freedict_db),
            "es_en_wiktionary_db": str(es_en_wiktionary_db),
            "es_en_freedict_db": str(es_en_freedict_db),
            "en_de_freedict_db": str(en_de_freedict_db),
            "de_wiktionary_db": str(de_wiktionary_db),
            "en_wiktionary_db": str(en_wiktionary_db),
            "jmdict_path": str(jmdict_path),
            "topics": sorted(topic_set),
            "source_row_limit": int(source_row_limit),
            "max_direct_per_source": int(max_direct_per_source),
            "max_english_per_source": int(max_english_per_source),
            "max_german_per_english": int(max_german_per_english),
            "max_translation_rank": int(max_translation_rank),
            "allow_english_pivot_fallback": bool(allow_english_pivot_fallback),
            "include_en_ja_review_candidates": bool(include_en_ja_review_candidates),
            "require_strong_german_evidence": bool(require_strong_german_evidence),
        },
        "source_diagnostics": source_diagnostics,
        "summary": summary,
        "rows": rows,
        "candidate_audit": candidate_audit[:500],
        "limitations": [
            "Direct translation rows are candidate evidence, not product-reviewed topic truth.",
            "Every direct German translation candidate is tried; fanout is recorded in provenance.",
            "Strong German evidence comes from local Wiktionary/Wiktextract topics, categories, and gloss text.",
            "Direct-translation-only matches are useful for review but still preserve source dictionary polysemy.",
            "English pivot fallback is disabled by default because it can introduce unrelated cross-sense drift.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Direct Translation Topic Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Row count: `{summary.get('row_count', 0)}`",
        f"- Runtime-effective row count: `{summary.get('runtime_effective_row_count', 0)}`",
        f"- Unique lemmas: `{summary.get('unique_lemma_count', 0)}`",
        f"- Source rows considered: `{summary.get('source_row_count', 0)}`",
        f"- Direct German translation rows: `{summary.get('direct_translation_count', 0)}`",
        f"- Existing direct German candidates: `{summary.get('direct_existing_candidate_count', 0)}`",
        f"- English pivot terms: `{summary.get('english_term_count', 0)}`",
        f"- Pivot German candidates: `{summary.get('pivot_german_candidate_count', 0)}`",
        f"- Existing pivot German candidates: `{summary.get('pivot_existing_candidate_count', 0)}`",
        f"- Strong German evidence: `{summary.get('strong_evidence_count', 0)}`",
        f"- Direct-review evidence: `{summary.get('direct_review_evidence_count', 0)}`",
        f"- Pivot-review evidence: `{summary.get('pivot_review_evidence_count', 0)}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows | Strong | Direct-review | Pivot-review |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    counts = _as_mapping(summary.get("counts_by_topic"))
    strong_counts = _as_mapping(summary.get("strong_counts_by_topic"))
    direct_counts = _as_mapping(summary.get("direct_review_counts_by_topic"))
    pivot_counts = _as_mapping(summary.get("pivot_review_counts_by_topic"))
    for topic in sorted(counts):
        lines.append(
            f"| `{topic}` | {int(counts.get(topic) or 0)} | "
            f"{int(strong_counts.get(topic) or 0)} | {int(direct_counts.get(topic) or 0)} | "
            f"{int(pivot_counts.get(topic) or 0)} |"
        )

    lines.extend(["", "## Source Use", "", "| Source Pair | Rows Used |", "| --- | ---: |"])
    for pair, count in sorted(_as_mapping(summary.get("source_usage")).items()):
        lines.append(f"| `{pair}` | {int(count)} |")
    direct_usage = _as_mapping(summary.get("direct_source_usage"))
    if direct_usage:
        lines.extend(
            ["", "## Direct Source Use", "", "| Source Pair | Rows Used |", "| --- | ---: |"]
        )
        for pair, count in sorted(direct_usage.items()):
            lines.append(f"| `{pair}` | {int(count)} |")

    rows = _mapping_rows(report.get("rows"))
    if rows:
        lines.extend(["", "## Candidate Sample", ""])
        lines.append(
            "| Topic | Lemma | Rank | Evidence | Source | Route | Source Query | German Translation |"
        )
        lines.append("| --- | --- | ---: | --- | --- | --- | --- | --- |")
        for row in rows[:80]:
            provenance = _as_mapping(row.get("provenance"))
            lines.append(
                f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
                f"{_fmt_num(row.get('corpus_rank'))} | "
                f"`{row.get('confidence_label', '')}` | "
                f"`{provenance.get('source_pair', '')}:{provenance.get('source_lemma', '')}` | "
                f"`{provenance.get('translation_route', '')}` | "
                f"`{provenance.get('source_query', '')}` | "
                f"`{provenance.get('raw_german_translation', '')}` |"
            )

    audit = _mapping_rows(report.get("candidate_audit"))
    if audit:
        lines.extend(["", "## Rejection / Missing Audit Sample", ""])
        for row in audit[:50]:
            lines.append(
                f"- `{row.get('source_pair', '')}:{row.get('source_lemma', '')}` "
                f"`{row.get('topic', '')}` -> {row.get('reason', '')}"
            )
    return "\n".join(lines) + "\n"


def _load_source_topic_rows(
    source_overlays: Sequence[Path],
    *,
    topics: set[str],
    row_limit: int,
    include_en_ja_review_candidates: bool,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    missing_paths: list[str] = []
    invalid_paths: list[str] = []
    skipped_counts: Counter[str] = Counter()
    for path in source_overlays:
        payload = _load_json_if_ready(path)
        if payload is None:
            if Path(path).expanduser().exists():
                invalid_paths.append(_repo_path(path))
            else:
                missing_paths.append(_repo_path(path))
            continue
        for row in _mapping_rows(payload.get("rows")):
            topic = str(row.get("topic") or "").strip()
            if topic not in topics:
                skipped_counts["topic_not_requested"] += 1
                continue
            pair = str(row.get("language_pair") or "").strip()
            if pair == LANGUAGE_PAIR:
                skipped_counts["target_pair_source_ignored"] += 1
                continue
            if not _source_row_is_trusted(
                row,
                include_en_ja_review_candidates=include_en_ja_review_candidates,
            ):
                skipped_counts[f"{pair}:not_trusted_source_row"] += 1
                continue
            rows.append(dict(row))
            if row_limit and len(rows) >= row_limit:
                break
        if row_limit and len(rows) >= row_limit:
            break
    return rows, {
        "loaded_source_rows": len(rows),
        "missing_source_overlays": missing_paths,
        "invalid_source_overlays": invalid_paths,
        "skipped_counts": dict(sorted(skipped_counts.items())),
    }


def _source_row_is_trusted(
    row: Mapping[str, object],
    *,
    include_en_ja_review_candidates: bool,
) -> bool:
    pair = str(row.get("language_pair") or "").strip()
    if pair == "en-ja" and include_en_ja_review_candidates:
        return str(row.get("review_state") or "").strip() not in REJECT_REVIEW_STATES - {
            "review_candidate_not_runtime_effective"
        }
    membership = _safe_float(row.get("membership"))
    review_state = str(row.get("review_state") or "").strip()
    runtime_blockers = _string_list(row.get("runtime_blockers"))
    if membership < 1.0:
        return False
    if review_state in REJECT_REVIEW_STATES:
        return False
    return not runtime_blockers


def _english_terms_for_source_row(
    row: Mapping[str, object],
    *,
    es_wiktionary: sqlite3.Connection | None,
    es_freedict: sqlite3.Connection | None,
    en_wiktionary: sqlite3.Connection | None,
    jmdict_glosses: Mapping[str, Sequence[str]],
    topic: str,
    english_topic_cache: dict[tuple[str, str], bool],
    max_terms: int,
) -> tuple[str, ...]:
    pair = str(row.get("language_pair") or "").strip()
    lemma = str(row.get("lemma") or "").strip()
    raw_terms: list[str] = []
    if pair == "en-es":
        if es_wiktionary is not None:
            raw_terms.extend(
                _lookup_es_wiktionary_topic_terms(
                    es_wiktionary,
                    lemma=lemma,
                    topic=topic,
                    en_wiktionary=en_wiktionary,
                    english_topic_cache=english_topic_cache,
                )
            )
        if es_freedict is not None:
            raw_terms.extend(_lookup_translation_column(es_freedict, "entries", lemma))
    elif pair == "en-ja":
        raw_terms.extend(jmdict_glosses.get(lemma, ()))
        reading = str(row.get("reading") or "").strip()
        if reading:
            raw_terms.extend(jmdict_glosses.get(reading, ()))
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_term in raw_terms:
        for term in _english_candidate_terms(raw_term):
            if term in STOP_ENGLISH_TERMS or term in seen:
                continue
            if not _english_pivot_has_topic_evidence(
                en_wiktionary,
                english_term=term,
                topic=topic,
                cache=english_topic_cache,
            ):
                continue
            seen.add(term)
            normalized.append(term)
            if len(normalized) >= max_terms:
                return tuple(normalized)
    return tuple(normalized)


def _lookup_es_wiktionary_topic_terms(
    connection: sqlite3.Connection,
    *,
    lemma: str,
    topic: str,
    en_wiktionary: sqlite3.Connection | None,
    english_topic_cache: dict[tuple[str, str], bool],
) -> list[str]:
    if connection is None:
        return []
    try:
        rows = connection.execute(
            """
            SELECT translation, raw_glosses_json, tags_json, topics_json, categories_json
            FROM sense_glosses
            WHERE headword_lc = ?
            ORDER BY entry_ord, sense_ord, gloss_ord
            LIMIT 120
            """,
            (lemma.casefold(),),
        ).fetchall()
    except sqlite3.Error:
        return []
    accepted: list[str] = []
    for translation, raw_glosses, tags_json, topics_json, categories_json in rows:
        sense_text = "\n".join(
            str(value or "")
            for value in (translation, raw_glosses, tags_json, topics_json, categories_json)
        ).casefold()
        if _sense_has_non_primary_usage(sense_text) and not _topic_keyword_hit(sense_text, topic):
            continue
        terms = _english_candidate_terms(translation)
        if _topic_keyword_hit(sense_text, topic):
            accepted.extend(terms)
            continue
        accepted.extend(
            term
            for term in terms
            if _english_pivot_has_topic_evidence(
                en_wiktionary,
                english_term=term,
                topic=topic,
                cache=english_topic_cache,
            )
        )
    return accepted


def _sense_has_non_primary_usage(text: str) -> bool:
    lowered = str(text or "").casefold()
    markers = (
        "slang",
        "colloquial",
        "informal",
        "figurative",
        "figuratively",
        "derogatory",
        "vulgar",
        "dated",
        "obsolete",
        "regional",
        "puerto-rico",
        "mexico",
        "colombia",
        "ecuador",
        "spain",
    )
    return any(marker in lowered for marker in markers)


def _english_pivot_has_topic_evidence(
    connection: sqlite3.Connection | None,
    *,
    english_term: str,
    topic: str,
    cache: dict[tuple[str, str], bool],
) -> bool:
    key = (topic, english_term.casefold())
    cached = cache.get(key)
    if cached is not None:
        return cached
    if connection is None:
        cache[key] = True
        return True
    fields: list[str] = []
    try:
        for row in connection.execute(
            """
            SELECT pos, categories_json, etymology_text
            FROM entry_meta
            WHERE headword_lc = ?
            LIMIT 20
            """,
            (english_term.casefold(),),
        ):
            fields.extend(str(value or "") for value in row)
        for row in connection.execute(
            """
            SELECT translation, pos, raw_glosses_json, tags_json, topics_json, categories_json
            FROM sense_glosses
            WHERE headword_lc = ?
            LIMIT 120
            """,
            (english_term.casefold(),),
        ):
            fields.extend(str(value or "") for value in row)
    except sqlite3.Error:
        cache[key] = False
        return False
    result = _topic_keyword_hit("\n".join(fields).casefold(), topic)
    cache[key] = result
    return result


def _lookup_translation_column(
    connection: sqlite3.Connection,
    table_name: str,
    lemma: str,
) -> list[str]:
    if connection is None:
        return []
    order_by = (
        "entry_ord, sense_ord, gloss_ord"
        if table_name == "sense_glosses"
        else "COALESCE(rank, 999999), entry_ord, gloss_ord"
    )
    try:
        cursor = connection.execute(
            f"""
            SELECT translation
            FROM {table_name}
            WHERE headword_lc = ?
            ORDER BY {order_by}
            LIMIT 80
            """,
            (lemma.casefold(),),
        )
    except sqlite3.Error:
        return []
    return [str(row[0] or "") for row in cursor.fetchall()]


def _direct_german_rows_for_source_row(
    row: Mapping[str, object],
    *,
    es_de_freedict: sqlite3.Connection | None,
    ja_de_freedict: sqlite3.Connection | None,
    max_rows: int,
    max_rank: int,
) -> list[dict[str, object]]:
    pair = str(row.get("language_pair") or "").strip()
    if pair == "en-es":
        connection = es_de_freedict
        route = "direct_freedict_es_de"
        source_queries = [str(row.get("lemma") or "").strip()]
    elif pair == "en-ja":
        connection = ja_de_freedict
        route = "direct_freedict_ja_de"
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("reading") or "").strip()
        source_queries = [lemma or reading]
    else:
        return []
    if connection is None:
        return []
    out: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for source_query in dict.fromkeys(query for query in source_queries if query):
        for direct_row in _source_to_german_candidates(
            connection,
            source_query=source_query,
            max_rows=max_rows,
            max_rank=max_rank,
        ):
            if str(direct_row.get("pos") or "").strip() == "v":
                continue
            for candidate in _german_candidate_terms(direct_row.get("translation")):
                key = (source_query.casefold(), str(direct_row.get("translation") or ""), candidate)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    {
                        **direct_row,
                        "term": candidate,
                        "translation_route": route,
                        "source_query": source_query,
                        "english_pivot": "",
                    }
                )
    return out


def _source_to_german_candidates(
    connection: sqlite3.Connection | None,
    *,
    source_query: str,
    max_rows: int,
    max_rank: int,
) -> list[dict[str, object]]:
    if connection is None:
        return []
    try:
        rows = connection.execute(
            """
            SELECT headword, translation, rank, pos, entry_ord, gloss_ord
            FROM entries
            WHERE headword_lc = ? AND COALESCE(rank, 999999) <= ?
            ORDER BY COALESCE(rank, 999999), entry_ord, gloss_ord
            LIMIT ?
            """,
            (source_query.casefold(), int(max_rank), int(max_rows)),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [
        {
            "headword": row[0],
            "translation": row[1],
            "rank": row[2],
            "pos": row[3],
            "entry_ord": row[4],
            "gloss_ord": row[5],
        }
        for row in rows
    ]


def _english_to_german_candidates(
    connection: sqlite3.Connection | None,
    *,
    english_term: str,
    max_rows: int,
    max_rank: int,
) -> list[dict[str, object]]:
    if connection is None:
        return []
    try:
        rows = connection.execute(
            """
            SELECT headword, translation, rank, pos, entry_ord, gloss_ord
            FROM entries
            WHERE headword_lc = ? AND COALESCE(rank, 999999) <= ?
            ORDER BY COALESCE(rank, 999999), entry_ord, gloss_ord
            LIMIT ?
            """,
            (english_term.casefold(), int(max_rank), int(max_rows)),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [
        {
            "headword": row[0],
            "translation": row[1],
            "rank": row[2],
            "pos": row[3],
            "entry_ord": row[4],
            "gloss_ord": row[5],
        }
        for row in rows
    ]


def _german_topic_evidence(
    connection: sqlite3.Connection | None,
    *,
    lemma: str,
    topic: str,
    english_pivot: str,
    direct_translation: bool = False,
) -> dict[str, object]:
    if connection is None:
        return {
            "decision": "missing_german_wiktionary_db",
            "keyword_hits": [],
            "pivot_gloss_hits": [],
        }
    keyword_hits: list[str] = []
    pivot_hits: list[str] = []
    try:
        for row in connection.execute(
            """
            SELECT pos, categories_json
            FROM entry_meta
            WHERE headword_lc = ?
            LIMIT 20
            """,
            (lemma.casefold(),),
        ):
            category_text = _topic_category_evidence_text(topic, str(row[1] or ""))
            for keyword in _topic_keyword_hits(category_text, topic):
                keyword_hits.append(keyword)
        for row in connection.execute(
            """
            SELECT translation, pos, raw_glosses_json, tags_json, topics_json, categories_json
            FROM sense_glosses
            WHERE headword_lc = ?
            LIMIT 120
            """,
            (lemma.casefold(),),
        ):
            values = [str(value or "") for value in row]
            translation_text = values[0]
            sense_text = "\n".join(
                (
                    translation_text,
                    values[2],
                    values[3],
                    values[4],
                    _topic_category_evidence_text(topic, values[5]),
                )
            ).casefold()
            if not _sense_has_non_primary_usage(sense_text):
                for keyword in _topic_keyword_hits(sense_text, topic):
                    keyword_hits.append(keyword)
            translation_text = values[0].casefold()
            if english_pivot and _term_occurs(translation_text, english_pivot):
                pivot_hits.append(values[0])
    except sqlite3.Error:
        return {
            "decision": "german_wiktionary_query_failed",
            "keyword_hits": [],
            "pivot_gloss_hits": [],
        }

    if keyword_hits:
        return {
            "decision": "strong_topic_keyword",
            "keyword_hits": sorted(dict.fromkeys(keyword_hits)),
            "pivot_gloss_hits": pivot_hits[:8],
        }
    if direct_translation:
        return {
            "decision": "direct_translation_match_needs_review",
            "keyword_hits": [],
            "pivot_gloss_hits": [],
        }
    if pivot_hits:
        return {
            "decision": "pivot_gloss_match_needs_review",
            "keyword_hits": [],
            "pivot_gloss_hits": pivot_hits[:8],
        }
    return {"decision": "no_german_topic_evidence", "keyword_hits": [], "pivot_gloss_hits": []}


def _overlay_row(
    *,
    source_row: Mapping[str, object],
    source_pair: str,
    source_lemma: str,
    german_translation_row: Mapping[str, object],
    frequency: Mapping[str, object],
    evidence: Mapping[str, object],
) -> dict[str, object]:
    lemma = str(frequency.get("lemma") or german_translation_row.get("term") or "").strip()
    topic = str(source_row.get("topic") or "").strip()
    evidence_decision = str(evidence.get("decision") or "")
    strong = evidence_decision == "strong_topic_keyword"
    direct_review = evidence_decision == "direct_translation_match_needs_review"
    route = str(german_translation_row.get("translation_route") or "direct_unknown")
    source_query = str(german_translation_row.get("source_query") or "")
    english_pivot = str(german_translation_row.get("english_pivot") or "")
    review_id = _review_id(lemma, topic, source_pair, source_lemma, route, source_query)
    raw_german_translation = str(german_translation_row.get("translation") or "").strip()
    return {
        "language_pair": LANGUAGE_PAIR,
        "lemma": lemma,
        "topic": topic,
        "membership": 0.65 if strong else 0.55 if direct_review else 0.45,
        "confidence_label": (
            "strong_german_topic_evidence"
            if strong
            else "direct_translation_review"
            if direct_review
            else "pivot_match_review"
        ),
        "review_state": "review_candidate_not_runtime_effective",
        "review_id": review_id,
        "source_channel": SOURCE_CHANNEL,
        "source_label": f"{source_pair}_direct_topic_translation",
        "facet_id": f"direct_translation_{topic}",
        "evidence_score": 0.78 if strong else 0.64 if direct_review else 0.58,
        "corpus_rank": frequency.get("source_rank"),
        "pmw": frequency.get("pmw"),
        "pos": str(frequency.get("pos") or ""),
        "pos_canonical": str(frequency.get("pos_canonical") or ""),
        "provenance": {
            "lexicon_id": OVERLAY_ID,
            "source_overlay_ids": _source_overlay_ids(source_row),
            "source_pair": source_pair,
            "source_lemma": source_lemma,
            "source_topic": topic,
            "source_review_id": str(source_row.get("review_id") or ""),
            "translation_route": route,
            "source_query": source_query,
            "english_pivot": english_pivot,
            "raw_german_translation": raw_german_translation,
            "german_translation_rank": german_translation_row.get("rank"),
            "german_translation_pos": str(german_translation_row.get("pos") or ""),
            "german_evidence_decision": evidence_decision,
            "german_keyword_hits": _string_list(evidence.get("keyword_hits")),
            "german_pivot_gloss_hits": _string_list(evidence.get("pivot_gloss_hits"))[:6],
            "promotion_state": "review_only_candidate_not_default",
            "license_note": (
                "Derived candidate row from local FreeDict/Wiktionary/JMDict evidence. "
                "No dictionary definitions or source text are packaged in runtime data."
            ),
            "match_policy": "direct_translation_candidates_tried_then_german_frequency_and_wiktionary_evidence",
        },
    }


def _merge_duplicate_rows(
    left: Mapping[str, object], right: Mapping[str, object]
) -> dict[str, object]:
    winner = dict(right if _row_priority(right) > _row_priority(left) else left)
    provenance = dict(_as_mapping(winner.get("provenance")))
    source_pairs = []
    source_lemmas = []
    source_queries = []
    translation_routes = []
    english_pivots = []
    for row in (left, right):
        prov = _as_mapping(row.get("provenance"))
        for key, target in (
            ("source_pair", source_pairs),
            ("source_lemma", source_lemmas),
            ("source_query", source_queries),
            ("translation_route", translation_routes),
            ("english_pivot", english_pivots),
        ):
            value = str(prov.get(key) or "")
            if value and value not in target:
                target.append(value)
    provenance["merged_source_pairs"] = source_pairs
    provenance["merged_source_lemmas"] = source_lemmas[:12]
    provenance["merged_source_queries"] = source_queries[:12]
    provenance["merged_translation_routes"] = translation_routes[:12]
    provenance["merged_english_pivots"] = english_pivots[:12]
    winner["provenance"] = provenance
    return winner


def _source_overlay_ids(source_row: Mapping[str, object]) -> list[str]:
    provenance = _as_mapping(source_row.get("provenance"))
    source_ids = _string_list(provenance.get("source_overlay_ids"))
    return source_ids or [str(source_row.get("source_label") or "unknown_source_overlay")]


def _row_priority(row: Mapping[str, object]) -> tuple[int, float, float, float]:
    label = str(row.get("confidence_label") or "")
    label_rank = (
        3
        if label == "strong_german_topic_evidence"
        else 2
        if label == "direct_translation_review"
        else 1
        if label
        else 0
    )
    membership = _safe_float(row.get("membership"))
    evidence = _safe_float(row.get("evidence_score"))
    rank = _safe_float(row.get("corpus_rank"), default=999999.0)
    return (label_rank, membership, evidence, -rank)


def _summary(
    rows: Sequence[Mapping[str, object]],
    *,
    source_rows: Sequence[Mapping[str, object]],
    source_usage: Counter[str],
    direct_source_usage: Counter[str],
    fallback_source_usage: Counter[str],
    direct_translation_count: int,
    direct_existing_candidate_count: int,
    english_term_count: int,
    pivot_german_candidate_count: int,
    pivot_existing_candidate_count: int,
    strong_evidence_count: int,
    direct_review_evidence_count: int,
    pivot_review_evidence_count: int,
    rejected_evidence_count: int,
    duplicate_row_count: int,
    missing_translation_count: int,
) -> dict[str, object]:
    counts = Counter(str(row.get("topic") or "") for row in rows)
    strong_counts = Counter(
        str(row.get("topic") or "")
        for row in rows
        if str(row.get("confidence_label") or "") == "strong_german_topic_evidence"
    )
    pivot_counts = Counter(
        str(row.get("topic") or "")
        for row in rows
        if str(row.get("confidence_label") or "") == "pivot_match_review"
    )
    direct_counts = Counter(
        str(row.get("topic") or "")
        for row in rows
        if str(row.get("confidence_label") or "") == "direct_translation_review"
    )
    runtime_rows = [
        row
        for row in rows
        if _safe_float(row.get("membership")) >= 1.0
        and str(row.get("review_state") or "").strip()
        not in {"rejected", "review_candidate_not_runtime_effective"}
    ]
    return {
        "row_count": len(rows),
        "runtime_effective_row_count": len(runtime_rows),
        "unique_lemma_count": len({str(row.get("lemma") or "") for row in rows}),
        "topic_count": len(counts),
        "counts_by_topic": dict(sorted(counts.items())),
        "strong_counts_by_topic": dict(sorted(strong_counts.items())),
        "direct_review_counts_by_topic": dict(sorted(direct_counts.items())),
        "pivot_review_counts_by_topic": dict(sorted(pivot_counts.items())),
        "counts_by_confidence": dict(
            sorted(Counter(str(row.get("confidence_label") or "") for row in rows).items())
        ),
        "source_row_count": len(source_rows),
        "source_usage": dict(sorted(source_usage.items())),
        "direct_source_usage": dict(sorted(direct_source_usage.items())),
        "fallback_source_usage": dict(sorted(fallback_source_usage.items())),
        "direct_translation_count": direct_translation_count,
        "direct_existing_candidate_count": direct_existing_candidate_count,
        "english_term_count": english_term_count,
        "pivot_german_candidate_count": pivot_german_candidate_count,
        "pivot_existing_candidate_count": pivot_existing_candidate_count,
        "strong_evidence_count": strong_evidence_count,
        "direct_review_evidence_count": direct_review_evidence_count,
        "pivot_review_evidence_count": pivot_review_evidence_count,
        "rejected_evidence_count": rejected_evidence_count,
        "duplicate_row_count": duplicate_row_count,
        "missing_translation_count": missing_translation_count,
    }


def _candidate_audit_row(
    source_row: Mapping[str, object],
    *,
    reason: str,
    english_terms: Sequence[str] = (),
    german_candidate: str = "",
    evidence: Mapping[str, object] | None = None,
    translation_route: str = "",
    source_query: str = "",
) -> dict[str, object]:
    return {
        "source_pair": str(source_row.get("language_pair") or ""),
        "source_lemma": str(source_row.get("lemma") or ""),
        "topic": str(source_row.get("topic") or ""),
        "reason": reason,
        "english_terms": list(english_terms),
        "german_candidate": german_candidate,
        "translation_route": translation_route,
        "source_query": source_query,
        "evidence": dict(evidence or {}),
    }


def _load_frequency_rows(path: Path, *, top_n: int) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    resolved = Path(path).expanduser()
    if not resolved.exists():
        return rows
    with closing(sqlite3.connect(resolved)) as connection:
        try:
            cursor = connection.execute(
                """
                SELECT lemma, core_rank, pmw, pos
                FROM frequency
                WHERE core_rank <= ?
                ORDER BY core_rank
                """,
                (float(top_n),),
            )
        except sqlite3.Error:
            return rows
        for lemma, rank, pmw, pos in cursor.fetchall():
            frequency = {
                "lemma": str(lemma or ""),
                "source_rank": rank,
                "pmw": pmw,
                "pos": str(pos or ""),
                "pos_canonical": "",
            }
            rows[str(lemma or "").casefold()] = frequency
    return rows


def _resolve_frequency_row(
    frequency_rows: Mapping[str, Mapping[str, object]],
    lemma: str,
) -> Mapping[str, object] | None:
    candidates = [
        str(lemma or "").strip(),
        str(lemma or "").strip().casefold(),
        str(lemma or "").strip().lower(),
        str(lemma or "").strip().capitalize(),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        frequency = frequency_rows.get(candidate.casefold())
        if frequency is not None:
            return frequency
    return None


def _load_jmdict_glosses(
    jmdict_path: Path,
    source_rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[str, ...]]:
    wanted = {
        value
        for row in source_rows
        if str(row.get("language_pair") or "") == "en-ja"
        for value in (str(row.get("lemma") or "").strip(), str(row.get("reading") or "").strip())
        if value
    }
    if not wanted or not Path(jmdict_path).expanduser().exists():
        return {}
    glosses_by_surface: dict[str, list[str]] = defaultdict(list)
    try:
        for _event, elem in ET.iterparse(Path(jmdict_path).expanduser(), events=("end",)):
            if elem.tag != "entry":
                continue
            surfaces = [
                child.text.strip()
                for child in elem.findall("./k_ele/keb")
                if child.text and child.text.strip()
            ]
            surfaces.extend(
                child.text.strip()
                for child in elem.findall("./r_ele/reb")
                if child.text and child.text.strip()
            )
            matched = [surface for surface in surfaces if surface in wanted]
            if matched:
                glosses = [
                    gloss.text.strip()
                    for gloss in elem.findall("./sense/gloss")
                    if gloss.text
                    and (gloss.get("{http://www.w3.org/XML/1998/namespace}lang") in {None, "eng"})
                ]
                for surface in matched:
                    glosses_by_surface[surface].extend(glosses)
            elem.clear()
    except (OSError, ET.ParseError):
        return {}
    return {
        surface: tuple(dict.fromkeys(_flatten_english_terms(glosses)))
        for surface, glosses in glosses_by_surface.items()
    }


def _flatten_english_terms(values: Iterable[str]) -> list[str]:
    terms: list[str] = []
    for value in values:
        terms.extend(_english_candidate_terms(value))
    return terms


def _english_candidate_terms(raw: object) -> tuple[str, ...]:
    text = str(raw or "")
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    pieces = re.split(r";|,|/|\bor\b|\band\b", text, flags=re.IGNORECASE)
    terms: list[str] = []
    for piece in pieces:
        term = re.sub(r"[^A-Za-z0-9' -]", " ", piece).strip().casefold()
        term = re.sub(r"\s+", " ", term)
        term = re.sub(r"^(to|a|an|the)\s+", "", term).strip()
        if not term or len(term) > 48 or term.count(" ") > 3:
            continue
        terms.append(term)
    return tuple(dict.fromkeys(terms))


def _german_candidate_terms(raw: object) -> tuple[str, ...]:
    text = str(raw or "")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace(";", ",")
    pieces = re.split(r",|\bor\b|\bund\b", text, flags=re.IGNORECASE)
    terms: list[str] = []
    for piece in pieces:
        if "/" in piece:
            continue
        term = piece.strip(" \t\n\r\"'`.;:!?")
        term = re.sub(r"\s+", " ", term)
        if re.search(r"\b(etw|jdn|jd|jmdm|jmdn|sich)\.", term, flags=re.IGNORECASE):
            continue
        if re.match(r"^(ich|du|er|sie|es|wir|ihr|Sie)\b", term):
            continue
        for article in GERMAN_LEADING_ARTICLES:
            if term.casefold().startswith(article):
                term = term[len(article) :].strip()
                break
        term = term.strip(" \t\n\r\"'`.;:!?")
        if not term or len(term) > 64:
            continue
        if term.count(" ") > 1:
            continue
        if any(ch.isdigit() for ch in term):
            continue
        terms.append(term)
    return tuple(dict.fromkeys(terms))


def _topic_keyword_hit(text: str, topic: str) -> bool:
    return any(_term_occurs(text, keyword) for keyword in TOPIC_KEYWORDS.get(topic, ()))


def _topic_keyword_hits(text: str, topic: str) -> list[str]:
    return [keyword for keyword in TOPIC_KEYWORDS.get(topic, ()) if _term_occurs(text, keyword)]


def _topic_category_evidence_text(topic: str, categories_json: str) -> str:
    text = str(categories_json or "")
    lowered = text.casefold()
    if not lowered:
        return ""
    if topic == "animals" and any(
        marker in lowered
        for marker in (
            "animal body parts",
            "body parts",
            "genitalia",
            "meats",
            "people",
            "occupations",
        )
    ):
        return ""
    return text


def _term_occurs(text: str, term: str) -> bool:
    normalized_text = str(text or "").casefold()
    normalized_term = str(term or "").strip().casefold()
    if not normalized_text or not normalized_term:
        return False
    if " " in normalized_term:
        return normalized_term in normalized_text
    return (
        re.search(rf"(?<![a-zäöüß-]){re.escape(normalized_term)}(?![a-zäöüß-])", normalized_text)
        is not None
    )


def _sqlite_connection(path: Path) -> sqlite3.Connection | None:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        return None
    connection = sqlite3.connect(resolved)
    connection.row_factory = sqlite3.Row
    return connection


def _load_json_if_ready(path: Path) -> Mapping[str, object] | None:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        return None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if str(payload.get("status") or "").strip() != "ok":
        return None
    return payload


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item)]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt_num(value: object) -> str:
    number = _safe_float(value, default=-1.0)
    if number < 0:
        return ""
    if number.is_integer():
        return str(int(number))
    return f"{number:.3f}"


def _review_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return f"srs-ende-translation-topic-{digest[:12]}"


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except (OSError, ValueError):
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
