#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.lexicon.word_package import normalize_reading  # noqa: E402


DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_CANDIDATES_CSV = (
    PROJECT_ROOT
    / "core"
    / "lexishift_core"
    / "resources"
    / "srs"
    / "en_ja"
    / "learner_difficulty_corrected.csv"
)
DEFAULT_JMDICT = DATA_ROOT / "language_packs" / "jmdict-ja-en" / "JMdict_e"
LEGACY_JMDICT = DATA_ROOT / "language_packs" / "JMdict_e"
DEFAULT_TAXONOMY_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_ja.json"
)
DEFAULT_POLICY_JSON = PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_autotag_policy_en_ja.json"
DEFAULT_WORDNET_ROOT = DATA_ROOT / "language_packs" / "english-wordnet-2025-json"
DEFAULT_JAWIKI_DUMP_ROOT = DATA_ROOT / "language_packs" / "jawiki-topic-dumps"
DEFAULT_JAWIKI_PAGE_SQL_GZ = DEFAULT_JAWIKI_DUMP_ROOT / "jawiki-latest-page.sql.gz"
DEFAULT_JAWIKI_REDIRECT_SQL_GZ = DEFAULT_JAWIKI_DUMP_ROOT / "jawiki-latest-redirect.sql.gz"
DEFAULT_JAWIKI_CATEGORYLINKS_SQL_GZ = (
    DEFAULT_JAWIKI_DUMP_ROOT / "jawiki-latest-categorylinks.sql.gz"
)
DEFAULT_JAWIKI_CATEGORY_SQL_GZ = DEFAULT_JAWIKI_DUMP_ROOT / "jawiki-latest-category.sql.gz"
DEFAULT_JAWIKI_LINKTARGET_SQL_GZ = DEFAULT_JAWIKI_DUMP_ROOT / "jawiki-latest-linktarget.sql.gz"
DEFAULT_KAIKKI_JA_JSONL_GZ = (
    DATA_ROOT / "language_packs" / "wiktionary-ja" / "kaikki.org-dictionary-Japanese.jsonl.gz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_autotag_evidence_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_autotag_evidence_en_ja_latest.md"
)
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
NDL_SPARQL_ENDPOINT = "https://id.ndl.go.jp/auth/ndla/"
JAWIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
USER_AGENT = "LexiShiftTopicAutotagProbe/0.1 (local research sidecar)"
DEFAULT_LOCAL_SOURCES = (
    "jmdict_field_direct",
    "jmdict_misc_review",
    "jmdict_gloss_keyword",
    "english_wordnet_gloss_bridge",
)
OFFLINE_DUMP_SOURCES = frozenset({"jawikipedia_dump_category", "kaikki_wiktionary_topic"})
ONLINE_SOURCES = frozenset({"wikidata_online", "ndl_online", "jawikipedia_category_online"})
ALL_SOURCES = (*DEFAULT_LOCAL_SOURCES, *sorted(OFFLINE_DUMP_SOURCES), *sorted(ONLINE_SOURCES))
WEAK_SOURCE_PREFIXES = ("jmdict_gloss_keyword", "english_wordnet_gloss_bridge")
ENGLISH_STOP_GLOSSES = {
    "a",
    "an",
    "be",
    "do",
    "go",
    "have",
    "he",
    "i",
    "it",
    "make",
    "not",
    "one",
    "she",
    "something",
    "that",
    "thing",
    "to be",
    "to do",
    "to go",
    "use",
    "we",
    "you",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build sidecar en-ja SRS topic autotag evidence and deterministic "
            "review samples. This is research-only and does not mutate admission "
            "overlays or runtime resources."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--jmdict", type=Path, default=None)
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY_JSON)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument("--wordnet-root", type=Path, default=DEFAULT_WORDNET_ROOT)
    parser.add_argument("--jawiki-page-sql-gz", type=Path, default=DEFAULT_JAWIKI_PAGE_SQL_GZ)
    parser.add_argument(
        "--jawiki-redirect-sql-gz", type=Path, default=DEFAULT_JAWIKI_REDIRECT_SQL_GZ
    )
    parser.add_argument(
        "--jawiki-categorylinks-sql-gz", type=Path, default=DEFAULT_JAWIKI_CATEGORYLINKS_SQL_GZ
    )
    parser.add_argument(
        "--jawiki-category-sql-gz", type=Path, default=DEFAULT_JAWIKI_CATEGORY_SQL_GZ
    )
    parser.add_argument(
        "--jawiki-linktarget-sql-gz", type=Path, default=DEFAULT_JAWIKI_LINKTARGET_SQL_GZ
    )
    parser.add_argument("--kaikki-ja-jsonl-gz", type=Path, default=DEFAULT_KAIKKI_JA_JSONL_GZ)
    parser.add_argument("--top-n", type=int, default=10000)
    parser.add_argument(
        "--source",
        action="append",
        choices=ALL_SOURCES,
        help="Evidence source to run. Defaults to local sources only.",
    )
    parser.add_argument("--enable-network", action="store_true")
    parser.add_argument("--online-limit", type=int, default=250)
    parser.add_argument("--online-chunk-size", type=int, default=40)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=240)
    parser.add_argument(
        "--max-sample-rows-per-source",
        type=int,
        default=80,
        help="Cap review-sample rows from any one evidence source; use 0 for no cap.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    requested_sources = tuple(args.source or DEFAULT_LOCAL_SOURCES)
    report = build_report(
        candidates_csv=_resolve_path(args.candidates_csv),
        jmdict_path=_resolve_jmdict_path(args.jmdict),
        taxonomy_json=_resolve_path(args.taxonomy_json),
        policy_json=_resolve_path(args.policy_json),
        wordnet_root=_resolve_path(args.wordnet_root),
        jawiki_page_sql_gz=_resolve_path(args.jawiki_page_sql_gz),
        jawiki_redirect_sql_gz=_resolve_path(args.jawiki_redirect_sql_gz),
        jawiki_categorylinks_sql_gz=_resolve_path(args.jawiki_categorylinks_sql_gz),
        jawiki_category_sql_gz=_resolve_path(args.jawiki_category_sql_gz),
        jawiki_linktarget_sql_gz=_resolve_path(args.jawiki_linktarget_sql_gz),
        kaikki_ja_jsonl_gz=_resolve_path(args.kaikki_ja_jsonl_gz),
        top_n=max(1, int(args.top_n)),
        sources=requested_sources,
        enable_network=bool(args.enable_network),
        online_limit=max(0, int(args.online_limit)),
        online_chunk_size=max(1, int(args.online_chunk_size)),
        sleep_seconds=max(0.0, float(args.sleep_seconds)),
        timeout_seconds=max(1, int(args.timeout_seconds)),
        sample_per_cell=max(1, int(args.sample_per_cell)),
        max_sample_rows=max(1, int(args.max_sample_rows)),
        max_sample_rows_per_source=max(0, int(args.max_sample_rows_per_source)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    candidates_csv: Path = DEFAULT_CANDIDATES_CSV,
    jmdict_path: Path | None = None,
    taxonomy_json: Path = DEFAULT_TAXONOMY_JSON,
    policy_json: Path = DEFAULT_POLICY_JSON,
    wordnet_root: Path = DEFAULT_WORDNET_ROOT,
    jawiki_page_sql_gz: Path = DEFAULT_JAWIKI_PAGE_SQL_GZ,
    jawiki_redirect_sql_gz: Path = DEFAULT_JAWIKI_REDIRECT_SQL_GZ,
    jawiki_categorylinks_sql_gz: Path = DEFAULT_JAWIKI_CATEGORYLINKS_SQL_GZ,
    jawiki_category_sql_gz: Path = DEFAULT_JAWIKI_CATEGORY_SQL_GZ,
    jawiki_linktarget_sql_gz: Path = DEFAULT_JAWIKI_LINKTARGET_SQL_GZ,
    kaikki_ja_jsonl_gz: Path = DEFAULT_KAIKKI_JA_JSONL_GZ,
    top_n: int = 10000,
    sources: Sequence[str] = DEFAULT_LOCAL_SOURCES,
    enable_network: bool = False,
    online_limit: int = 250,
    online_chunk_size: int = 40,
    sleep_seconds: float = 0.15,
    timeout_seconds: int = 30,
    sample_per_cell: int = 4,
    max_sample_rows: int = 240,
    max_sample_rows_per_source: int = 80,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    policy = _load_json(policy_json) if policy_json.exists() else {}
    taxonomy = _load_json(taxonomy_json) if taxonomy_json.exists() else {}
    requested_sources = tuple(dict.fromkeys(str(source) for source in sources))
    candidates = _load_candidates(candidates_csv, top_n=top_n) if candidates_csv.exists() else []
    evidence_rows: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []

    if not candidates:
        findings.append(
            _finding(
                "FAIL",
                "candidate_universe_missing",
                "No candidate rows were loaded; topic evidence cannot be generated.",
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "candidate_universe_loaded",
                f"Loaded {len(candidates)} en-ja corrected difficulty candidates.",
            )
        )

    jmdict_matches: dict[int, list[dict[str, object]]] = {}
    if any(
        source.startswith("jmdict_") or source == "english_wordnet_gloss_bridge"
        for source in requested_sources
    ):
        if jmdict_path and jmdict_path.exists() and candidates:
            jmdict_matches = _load_jmdict_matches(jmdict_path=jmdict_path, candidates=candidates)
            findings.append(
                _finding(
                    "PASS",
                    "jmdict_loaded",
                    f"Matched JMDict entries for {len(jmdict_matches)} candidate rows.",
                )
            )
        else:
            findings.append(
                _finding(
                    "FAIL",
                    "jmdict_missing",
                    f"JMDict path is unavailable: {_path_for_report(jmdict_path)}",
                )
            )

    if "jmdict_field_direct" in requested_sources and jmdict_matches:
        evidence_rows.extend(
            _jmdict_field_direct_evidence(
                candidates=candidates,
                jmdict_matches=jmdict_matches,
                taxonomy=taxonomy,
                policy=policy,
            )
        )
    if "jmdict_misc_review" in requested_sources and jmdict_matches:
        evidence_rows.extend(
            _jmdict_misc_evidence(
                candidates=candidates,
                jmdict_matches=jmdict_matches,
                policy=policy,
            )
        )
    if "jmdict_gloss_keyword" in requested_sources and jmdict_matches:
        evidence_rows.extend(
            _jmdict_gloss_keyword_evidence(
                candidates=candidates,
                jmdict_matches=jmdict_matches,
                policy=policy,
            )
        )
    if "english_wordnet_gloss_bridge" in requested_sources and jmdict_matches:
        if wordnet_root.exists():
            wordnet_index = _load_wordnet_topic_index(wordnet_root=wordnet_root, policy=policy)
            evidence_rows.extend(
                _wordnet_gloss_bridge_evidence(
                    candidates=candidates,
                    jmdict_matches=jmdict_matches,
                    wordnet_index=wordnet_index,
                    policy=policy,
                )
            )
            findings.append(
                _finding(
                    "PASS",
                    "wordnet_loaded",
                    f"Loaded {len(wordnet_index)} English WordNet gloss-topic entries.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    "wordnet_missing",
                    f"English WordNet root is unavailable: {_path_for_report(wordnet_root)}",
                )
            )

    if "jawikipedia_dump_category" in requested_sources and candidates:
        evidence_rows.extend(
            _jawikipedia_dump_category_evidence(
                candidates=candidates,
                policy=policy,
                page_sql_gz=jawiki_page_sql_gz,
                redirect_sql_gz=jawiki_redirect_sql_gz,
                categorylinks_sql_gz=jawiki_categorylinks_sql_gz,
                category_sql_gz=jawiki_category_sql_gz,
                linktarget_sql_gz=jawiki_linktarget_sql_gz,
                findings=findings,
            )
        )
    if "kaikki_wiktionary_topic" in requested_sources and candidates:
        evidence_rows.extend(
            _kaikki_wiktionary_topic_evidence(
                candidates=candidates,
                policy=policy,
                kaikki_jsonl_gz=kaikki_ja_jsonl_gz,
                findings=findings,
            )
        )

    online_sources_requested = [source for source in requested_sources if source in ONLINE_SOURCES]
    if online_sources_requested and not enable_network:
        findings.append(
            _finding(
                "WARN",
                "online_sources_disabled",
                (
                    "Online sources were requested but skipped because --enable-network "
                    f"was not set: {', '.join(sorted(online_sources_requested))}"
                ),
            )
        )
    elif online_sources_requested and candidates:
        online_candidates = _online_candidate_slice(candidates, limit=online_limit)
        if "wikidata_online" in online_sources_requested:
            evidence_rows.extend(
                _wikidata_online_evidence(
                    candidates=online_candidates,
                    policy=policy,
                    chunk_size=online_chunk_size,
                    sleep_seconds=sleep_seconds,
                    timeout_seconds=timeout_seconds,
                    findings=findings,
                )
            )
        if "ndl_online" in online_sources_requested:
            evidence_rows.extend(
                _ndl_online_evidence(
                    candidates=online_candidates,
                    policy=policy,
                    chunk_size=online_chunk_size,
                    sleep_seconds=sleep_seconds,
                    timeout_seconds=timeout_seconds,
                    findings=findings,
                )
            )
        if "jawikipedia_category_online" in online_sources_requested:
            evidence_rows.extend(
                _jawikipedia_category_evidence(
                    candidates=online_candidates,
                    policy=policy,
                    chunk_size=online_chunk_size,
                    sleep_seconds=sleep_seconds,
                    timeout_seconds=timeout_seconds,
                    findings=findings,
                )
            )

    evidence_rows = _dedupe_evidence(evidence_rows)
    evidence_rows, quality_guard_findings = _apply_evidence_quality_guards(evidence_rows)
    findings.extend(quality_guard_findings)
    sample_rows = _select_sample_rows(
        evidence_rows,
        sample_per_cell=sample_per_cell,
        max_rows=max_sample_rows,
        max_rows_per_source=max_sample_rows_per_source,
    )
    source_summary = _source_summary(evidence_rows)
    topic_summary = _topic_summary(evidence_rows)
    sample_summary = _sample_summary(sample_rows)
    if evidence_rows:
        findings.append(
            _finding(
                "PASS",
                "topic_evidence_generated",
                f"Generated {len(evidence_rows)} deduplicated topic evidence rows.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "topic_evidence_empty",
                "No topic evidence rows were generated for the selected sources.",
            )
        )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_autotag_evidence_ready"
            if status == "ok"
            else "srs_topic_autotag_evidence_needs_review"
        ),
        "generated_at": generated_at,
        "language_pair": "en-ja",
        "inputs": {
            "candidates_csv": _path_for_report(candidates_csv),
            "jmdict": _path_for_report(jmdict_path),
            "taxonomy_json": _path_for_report(taxonomy_json),
            "policy_json": _path_for_report(policy_json),
            "wordnet_root": _path_for_report(wordnet_root),
            "jawiki_page_sql_gz": _path_for_report(jawiki_page_sql_gz),
            "jawiki_redirect_sql_gz": _path_for_report(jawiki_redirect_sql_gz),
            "jawiki_categorylinks_sql_gz": _path_for_report(jawiki_categorylinks_sql_gz),
            "jawiki_category_sql_gz": _path_for_report(jawiki_category_sql_gz),
            "jawiki_linktarget_sql_gz": _path_for_report(jawiki_linktarget_sql_gz),
            "kaikki_ja_jsonl_gz": _path_for_report(kaikki_ja_jsonl_gz),
            "top_n": int(top_n),
            "sources": list(requested_sources),
            "enable_network": bool(enable_network),
            "online_limit": int(online_limit),
            "online_chunk_size": int(online_chunk_size),
            "sample_per_cell": int(sample_per_cell),
            "max_sample_rows": int(max_sample_rows),
            "max_sample_rows_per_source": int(max_sample_rows_per_source),
        },
        "method": {
            "candidate_universe": (
                "packaged corrected en-ja learner difficulty rows, preserving score, "
                "band, candidate_state, and correction metadata"
            ),
            "item_identity": (
                "JMDict local evidence requires exact written or kana surface plus "
                "normalized reading; kana-only dictionary entries preserve raw "
                "hiragana/katakana surface script and only normalize the reading slot"
            ),
            "promotion_posture": (
                "research evidence only; rows are not runtime topic overlays until "
                "reviewed and exported by a separate promotion step"
            ),
            "online_posture": (
                "online adapters are bounded build-time probes and never runtime dependencies"
            ),
            "offline_dump_posture": (
                "dump adapters use downloaded metadata files for full-corpus repeatability; "
                "exact page/title matches are still source evidence, not promoted product truth"
            ),
            "external_item_identity": (
                "external topic adapters must verify the candidate reading before row creation; "
                "surface-only evidence is kept only for kana-exact surfaces or surfaces with one "
                "normalized reading in the corrected candidate universe"
            ),
            "source_quality_guards": (
                "after row generation, source-specific precision guards reject mechanically "
                "suspicious rows such as generic/common words inheriting late or short-for "
                "Kaikki topic senses"
            ),
        },
        "candidate_summary": {
            "loaded_count": len(candidates),
            "top_n": int(top_n),
            "score_min": _round_float(
                min((float(row["score"]) for row in candidates), default=0.0)
            ),
            "score_max": _round_float(
                max((float(row["score"]) for row in candidates), default=0.0)
            ),
            "candidate_states": dict(
                sorted(Counter(str(row.get("candidate_state") or "") for row in candidates).items())
            ),
        },
        "source_summary": source_summary,
        "topic_summary": topic_summary,
        "sample_summary": sample_summary,
        "evidence_rows": evidence_rows,
        "review_sample": sample_rows,
        "findings": findings,
        "limitations": [
            "This artifact compares source strategies; it does not decide product topic membership.",
            "JMDict field evidence is high precision but sparse and still sense-polysemy-sensitive.",
            "Gloss, WordNet, Wikipedia category, and NDL keyword evidence are candidate-generation signals until reviewed.",
            "Wikidata/NDL/Wikipedia online adapters are intentionally bounded; full coverage should use cached/dump-based ingestion if promoted.",
            "Wikipedia dump matching is title/surface based; ambiguous multi-reading surfaces are rejected unless another adapter proves the reading.",
            "Kaikki/Wiktionary evidence is sense/category based; rows require entry reading proof or an unambiguous candidate surface before review.",
            "Kaikki sense-scope guards favor precision over coverage; rejected topic rows may still be linguistically defensible for a rare sense.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    source_summary = _as_mapping(report.get("source_summary"))
    topic_summary = _as_mapping(report.get("topic_summary"))
    sample_rows = _mapping_rows(report.get("review_sample"))
    lines = [
        "# en-ja SRS Topic Autotag Evidence",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Evidence rows: `{len(_mapping_rows(report.get('evidence_rows'))):,}`",
        f"- Review sample rows: `{len(sample_rows):,}`",
        "",
        "## Source Summary",
        "",
        "| Source | Rows | Lemmas | Topics | Avg confidence |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for source, summary in source_summary.items():
        row = _as_mapping(summary)
        lines.append(
            f"| `{source}` | {row.get('row_count', 0)} | {row.get('lemma_count', 0)} | "
            f"{row.get('topic_count', 0)} | {row.get('avg_confidence', '')} |"
        )
    lines.extend(
        [
            "",
            "## Topic Summary",
            "",
            "| Topic | Rows | Lemmas | Sources |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for topic, summary in topic_summary.items():
        row = _as_mapping(summary)
        lines.append(
            f"| `{topic}` | {row.get('row_count', 0)} | {row.get('lemma_count', 0)} | "
            f"{row.get('source_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Review Sample",
            "",
            "| # | Source | Topic | Lemma | Reading | Score | Band | Membership | Confidence | Evidence | Glosses |",
            "| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for index, row in enumerate(sample_rows, start=1):
        glosses = "<br>".join(
            _escape_md(str(item)) for item in _string_list(row.get("glosses"))[:3]
        )
        evidence = _escape_md(str(row.get("evidence_label") or row.get("source_label") or ""))
        lines.append(
            f"| {index} | `{row.get('source', '')}` | `{row.get('topic', '')}` | "
            f"`{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{row.get('score', '')} | `{row.get('band', '')}` | "
            f"{row.get('membership', '')} | {row.get('confidence', '')} | "
            f"{evidence} | {glosses} |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def _load_candidates(path: Path, *, top_n: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            if len(rows) >= top_n:
                break
            lemma = str(row.get("lemma") or "").strip()
            reading = str(row.get("reading") or "").strip()
            if not lemma:
                continue
            score = _safe_float(row.get("score"))
            rows.append(
                {
                    "row_index": index,
                    "rank": _safe_int(row.get("rank"), default=index),
                    "lemma": lemma,
                    "reading": reading,
                    "normalized_reading": _normalize_ja_reading(reading or lemma),
                    "score": score,
                    "band": str(row.get("band") or _score_band(score)),
                    "core_rank": _safe_float(row.get("core_rank")),
                    "candidate_state": str(row.get("candidate_state") or ""),
                    "admission_override": str(row.get("admission_override") or ""),
                    "topic_stretch_allowed": str(row.get("topic_stretch_allowed") or ""),
                    "correction_types": str(row.get("correction_types") or ""),
                }
            )
    return rows


def _load_jmdict_matches(
    *,
    jmdict_path: Path,
    candidates: Sequence[Mapping[str, object]],
) -> dict[int, list[dict[str, object]]]:
    index: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for candidate in candidates:
        lemma = str(candidate.get("lemma") or "").strip()
        reading = str(candidate.get("normalized_reading") or "").strip()
        if lemma and reading:
            index[(lemma, reading)].append(candidate)
    matches: dict[int, list[dict[str, object]]] = defaultdict(list)
    for _event, elem in ET.iterparse(jmdict_path, events=("end",)):
        if elem.tag != "entry":
            continue
        entry_terms = _jmdict_entry_keys(elem)
        candidate_hits: dict[int, str] = {}
        for key, match_mode in entry_terms:
            for candidate in index.get(key, ()):
                row_index = int(candidate.get("row_index") or 0)
                if row_index:
                    candidate_hits[row_index] = _stronger_match_mode(
                        candidate_hits.get(row_index, ""),
                        match_mode,
                    )
        if candidate_hits:
            ent_seq = _clean_text(elem.findtext("ent_seq"))
            for sense_index, sense in enumerate(elem.findall("sense"), start=1):
                sense_record = {
                    "ent_seq": ent_seq,
                    "sense_index": sense_index,
                    "fields": _child_texts(sense, "field"),
                    "misc": _child_texts(sense, "misc"),
                    "dialects": _child_texts(sense, "dial"),
                    "pos": _child_texts(sense, "pos"),
                    "glosses": _child_texts(sense, "gloss"),
                    "entry_surfaces": _child_texts(elem, "k_ele/keb"),
                    "entry_readings": _child_texts(elem, "r_ele/reb"),
                }
                for row_index, match_mode in candidate_hits.items():
                    matches[row_index].append({**sense_record, "match_mode": match_mode})
        elem.clear()
    return dict(matches)


def _jmdict_entry_keys(elem: ET.Element) -> list[tuple[tuple[str, str], str]]:
    surfaces = [_clean_text(surface) for surface in _child_texts(elem, "k_ele/keb")]
    readings = [
        (_clean_text(reading), _normalize_ja_reading(reading))
        for reading in _child_texts(elem, "r_ele/reb")
    ]
    keys: list[tuple[tuple[str, str], str]] = []
    for raw_reading, reading in readings:
        if not reading:
            continue
        if surfaces:
            keys.extend(
                [((surface, reading), "surface_reading") for surface in surfaces if surface]
            )
        elif raw_reading:
            keys.append(((raw_reading, reading), "kana_reading"))
    return keys


def _jmdict_field_direct_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    jmdict_matches: Mapping[int, Sequence[Mapping[str, object]]],
    taxonomy: Mapping[str, object],
    policy: Mapping[str, object],
) -> list[dict[str, object]]:
    mappings = _taxonomy_source_mappings(taxonomy, channel="jmdict_field")
    posture = _source_posture(policy, "jmdict_field_direct")
    evidence: list[dict[str, object]] = []
    candidates_by_index = {int(row["row_index"]): row for row in candidates}
    for row_index, senses in jmdict_matches.items():
        candidate = candidates_by_index.get(int(row_index))
        if not candidate:
            continue
        for sense in senses:
            for field in _string_list(sense.get("fields")):
                for mapped in mappings.get(_normalize_label(field), ()):
                    topic = str(mapped.get("target_family") or "").strip()
                    if not topic:
                        continue
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source="jmdict_field_direct",
                            topic=topic,
                            membership=_coalesce_float(
                                mapped.get("weight"),
                                posture.get("default_membership"),
                                1.0,
                            ),
                            confidence=_coalesce_float(
                                mapped.get("confidence"),
                                posture.get("default_confidence"),
                                0.9,
                            ),
                            source_label=field,
                            evidence_label=f"JMDict field: {field}",
                            sense=sense,
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                        )
                    )
    return evidence


def _jmdict_misc_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    jmdict_matches: Mapping[int, Sequence[Mapping[str, object]]],
    policy: Mapping[str, object],
) -> list[dict[str, object]]:
    mappings: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(policy.get("jmdict_misc_mappings")):
        mappings[_normalize_label(row.get("source_label"))].append(row)
    posture = _source_posture(policy, "jmdict_misc_review")
    evidence: list[dict[str, object]] = []
    candidates_by_index = {int(row["row_index"]): row for row in candidates}
    for row_index, senses in jmdict_matches.items():
        candidate = candidates_by_index.get(int(row_index))
        if not candidate:
            continue
        for sense in senses:
            for misc in _string_list(sense.get("misc")):
                for mapped in mappings.get(_normalize_label(misc), ()):
                    topic = str(mapped.get("target_family") or "").strip()
                    if not topic:
                        continue
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source="jmdict_misc_review",
                            topic=topic,
                            membership=_coalesce_float(
                                mapped.get("membership"),
                                posture.get("default_membership"),
                                0.65,
                            ),
                            confidence=_coalesce_float(
                                mapped.get("confidence"),
                                posture.get("default_confidence"),
                                0.65,
                            ),
                            source_label=misc,
                            evidence_label=f"JMDict misc: {misc}",
                            sense=sense,
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                        )
                    )
    return evidence


def _jmdict_gloss_keyword_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    jmdict_matches: Mapping[int, Sequence[Mapping[str, object]]],
    policy: Mapping[str, object],
) -> list[dict[str, object]]:
    rules = [
        _compile_gloss_rule(row) for row in _mapping_rows(policy.get("jmdict_gloss_keyword_rules"))
    ]
    posture = _source_posture(policy, "jmdict_gloss_keyword")
    evidence: list[dict[str, object]] = []
    candidates_by_index = {int(row["row_index"]): row for row in candidates}
    for row_index, senses in jmdict_matches.items():
        candidate = candidates_by_index.get(int(row_index))
        if not candidate:
            continue
        for sense in senses:
            gloss_blob = " ; ".join(_string_list(sense.get("glosses"))).lower()
            if not gloss_blob:
                continue
            for rule in rules:
                matched = _matched_gloss_rule(rule, gloss_blob)
                if not matched:
                    continue
                evidence.append(
                    _evidence_row(
                        candidate=candidate,
                        source="jmdict_gloss_keyword",
                        topic=str(rule["target_family"]),
                        membership=_coalesce_float(
                            rule.get("membership"),
                            posture.get("default_membership"),
                            0.55,
                        ),
                        confidence=_coalesce_float(
                            rule.get("confidence"),
                            posture.get("default_confidence"),
                            0.55,
                        ),
                        source_label=str(rule["id"]),
                        evidence_label=f"Gloss keyword: {matched}",
                        sense=sense,
                        review_posture=str(posture.get("review_posture") or ""),
                        license_note=str(posture.get("license_note") or ""),
                    )
                )
    return evidence


def _wordnet_gloss_bridge_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    jmdict_matches: Mapping[int, Sequence[Mapping[str, object]]],
    wordnet_index: Mapping[str, Sequence[Mapping[str, object]]],
    policy: Mapping[str, object],
) -> list[dict[str, object]]:
    posture = _source_posture(policy, "english_wordnet_gloss_bridge")
    evidence: list[dict[str, object]] = []
    candidates_by_index = {int(row["row_index"]): row for row in candidates}
    for row_index, senses in jmdict_matches.items():
        candidate = candidates_by_index.get(int(row_index))
        if not candidate:
            continue
        for sense in senses:
            for gloss in _string_list(sense.get("glosses")):
                normalized = _normalize_english_gloss(gloss)
                if not normalized or normalized in ENGLISH_STOP_GLOSSES:
                    continue
                for mapped in wordnet_index.get(normalized, ()):
                    topic = str(mapped.get("target_family") or "").strip()
                    if not topic:
                        continue
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source="english_wordnet_gloss_bridge",
                            topic=topic,
                            membership=_coalesce_float(
                                mapped.get("membership"),
                                posture.get("default_membership"),
                                0.6,
                            ),
                            confidence=_coalesce_float(
                                mapped.get("confidence"),
                                posture.get("default_confidence"),
                                0.6,
                            ),
                            source_label=str(mapped.get("lexname_file") or ""),
                            evidence_label=f"WordNet gloss bridge: {normalized}",
                            sense=sense,
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                            extra={
                                "wordnet_gloss_key": normalized,
                                "wordnet_synsets": _string_list(mapped.get("synsets"))[:6],
                            },
                        )
                    )
    return evidence


def _load_wordnet_topic_index(
    *,
    wordnet_root: Path,
    policy: Mapping[str, object],
) -> dict[str, list[dict[str, object]]]:
    synset_to_mappings: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for mapping in _mapping_rows(policy.get("wordnet_lexname_mappings")):
        lexname_file = str(mapping.get("lexname_file") or "").strip()
        if not lexname_file:
            continue
        path = wordnet_root / lexname_file
        if not path.exists():
            continue
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        for synset in payload.keys():
            synset_to_mappings[str(synset)].append(mapping)
    lemma_index: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for path in sorted(wordnet_root.glob("entries-*.json")):
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        for lemma, pos_payload in payload.items():
            normalized = _normalize_english_gloss(str(lemma))
            if not normalized or normalized in ENGLISH_STOP_GLOSSES:
                continue
            for pos_data in _as_mapping(pos_payload).values():
                for sense in _mapping_rows(_as_mapping(pos_data).get("sense")):
                    synset = str(sense.get("synset") or "")
                    for mapping in synset_to_mappings.get(synset, ()):
                        topic = str(mapping.get("target_family") or "")
                        lexname_file = str(mapping.get("lexname_file") or "")
                        key = f"{topic}|{lexname_file}"
                        existing = lemma_index[normalized].setdefault(
                            key,
                            {
                                "target_family": topic,
                                "lexname_file": lexname_file,
                                "membership": _safe_float(mapping.get("membership"), default=0.6),
                                "confidence": _safe_float(mapping.get("confidence"), default=0.6),
                                "synsets": [],
                            },
                        )
                        existing["synsets"] = [*list(existing.get("synsets") or []), synset]
    return {
        lemma: [row for row in rows_by_key.values()] for lemma, rows_by_key in lemma_index.items()
    }


def _jawikipedia_dump_category_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    page_sql_gz: Path,
    redirect_sql_gz: Path,
    categorylinks_sql_gz: Path,
    category_sql_gz: Path,
    linktarget_sql_gz: Path,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    required = (page_sql_gz, redirect_sql_gz, categorylinks_sql_gz, linktarget_sql_gz)
    missing = [path for path in required if not path.exists()]
    if missing:
        findings.append(
            _finding(
                "WARN",
                "jawikipedia_dump_missing",
                "Missing Japanese Wikipedia dump files: "
                + ", ".join(_path_for_report(path) for path in missing),
            )
        )
        return []
    posture = _source_posture(policy, "jawikipedia_dump_category")
    rules = _japanese_keyword_rules(policy)
    candidates_by_lemma = _candidates_by_lemma(candidates)
    wanted_titles = set(candidates_by_lemma)
    candidate_pages: dict[int, dict[str, object]] = {}
    direct_title_to_page_id: dict[str, int] = {}
    redirect_page_ids: set[int] = set()

    for row in _iter_mysql_insert_rows(page_sql_gz):
        if len(row) < 4 or row[1] != "0":
            continue
        title = _wiki_title_display(row[2])
        if title not in wanted_titles:
            continue
        page_id = _safe_int(row[0])
        if not page_id:
            continue
        is_redirect = row[3] == "1"
        candidate_pages[page_id] = {
            "candidate_title": title,
            "page_title": title,
            "is_redirect": is_redirect,
        }
        if is_redirect:
            redirect_page_ids.add(page_id)
        else:
            direct_title_to_page_id[title] = page_id

    redirect_targets_by_page_id: dict[int, str] = {}
    target_titles: set[str] = set()
    if redirect_page_ids:
        for row in _iter_mysql_insert_rows(redirect_sql_gz):
            if len(row) < 3 or row[1] != "0":
                continue
            page_id = _safe_int(row[0])
            if page_id not in redirect_page_ids:
                continue
            target_title = _wiki_title_display(row[2])
            if target_title:
                redirect_targets_by_page_id[page_id] = target_title
                target_titles.add(target_title)

    target_title_to_page_id: dict[str, int] = {}
    if target_titles:
        for row in _iter_mysql_insert_rows(page_sql_gz):
            if len(row) < 4 or row[1] != "0":
                continue
            title = _wiki_title_display(row[2])
            if title in target_titles:
                page_id = _safe_int(row[0])
                if page_id:
                    target_title_to_page_id[title] = page_id

    source_page_to_candidate_titles: dict[int, list[str]] = defaultdict(list)
    title_to_resolved_title: dict[str, str] = {}
    for page_id, page in candidate_pages.items():
        title = str(page.get("candidate_title") or "")
        if page.get("is_redirect"):
            target_title = redirect_targets_by_page_id.get(page_id, "")
            target_page_id = target_title_to_page_id.get(target_title, 0)
            if target_page_id:
                source_page_to_candidate_titles[target_page_id].append(title)
                title_to_resolved_title[title] = target_title
        else:
            source_page_to_candidate_titles[page_id].append(title)
            title_to_resolved_title[title] = title

    if not source_page_to_candidate_titles:
        findings.append(
            _finding(
                "WARN",
                "jawikipedia_dump_no_title_matches",
                "No corrected candidates matched Japanese Wikipedia page titles.",
            )
        )
        return []

    wanted_linktarget_ids: set[int] = set()
    page_to_linktarget_ids: dict[int, set[int]] = defaultdict(set)
    for row in _iter_mysql_insert_rows(categorylinks_sql_gz):
        if len(row) < 7:
            continue
        page_id = _safe_int(row[0])
        if page_id not in source_page_to_candidate_titles:
            continue
        linktarget_id = _safe_int(row[6])
        if not linktarget_id:
            continue
        page_to_linktarget_ids[page_id].add(linktarget_id)
        wanted_linktarget_ids.add(linktarget_id)

    linktarget_id_to_title: dict[int, str] = {}
    if wanted_linktarget_ids:
        for row in _iter_mysql_insert_rows(linktarget_sql_gz):
            if len(row) < 3:
                continue
            linktarget_id = _safe_int(row[0])
            namespace = row[1]
            if linktarget_id in wanted_linktarget_ids and namespace == "14":
                title = _wiki_title_display(row[2])
                if title and not _is_ignored_wiki_category(title):
                    linktarget_id_to_title[linktarget_id] = title

    evidence: list[dict[str, object]] = []
    matched_titles = 0
    reading_identity_stats: Counter[str] = Counter()
    for page_id, titles in source_page_to_candidate_titles.items():
        categories = sorted(
            {
                linktarget_id_to_title[linktarget_id]
                for linktarget_id in page_to_linktarget_ids.get(page_id, set())
                if linktarget_id in linktarget_id_to_title
            }
        )
        if not categories:
            continue
        for title in titles:
            verified_candidates = _verified_external_candidates(
                title,
                candidates_by_lemma.get(title, []),
                source_readings=(),
                stats=reading_identity_stats,
            )
            if not verified_candidates:
                continue
            matched_titles += 1
            resolved_title = title_to_resolved_title.get(title, title)
            haystack = " ".join([title, resolved_title, *categories])
            for rule in rules:
                matched = _matched_japanese_rule(rule, haystack)
                if not matched:
                    continue
                for candidate, reading_identity in verified_candidates:
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source="jawikipedia_dump_category",
                            topic=str(rule.get("target_family") or ""),
                            membership=_coalesce_float(
                                rule.get("membership"),
                                posture.get("default_membership"),
                                0.7,
                            ),
                            confidence=_coalesce_float(
                                rule.get("confidence"),
                                posture.get("default_confidence"),
                                0.66,
                            ),
                            source_label=matched,
                            evidence_label=f"ja.wikipedia dump category/title keyword: {matched}",
                            sense={"match_mode": reading_identity},
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                            extra={
                                "reading_identity": reading_identity,
                                "wikipedia_title": title,
                                "wikipedia_resolved_title": resolved_title,
                                "wikipedia_pageid": str(page_id),
                                "wikipedia_categories": categories[:18],
                            },
                        )
                    )
    findings.append(
        _finding(
            "PASS",
            "jawikipedia_dump_completed",
            (
                f"Matched {len(candidate_pages)} candidate titles, resolved "
                f"{len(source_page_to_candidate_titles)} pages, and generated "
                f"{len(evidence)} Wikipedia dump category evidence rows from "
                f"{matched_titles} title-category records. Reading identity gate: "
                f"{_format_counter(reading_identity_stats)}."
            ),
        )
    )
    return evidence


def _kaikki_wiktionary_topic_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    kaikki_jsonl_gz: Path,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not kaikki_jsonl_gz.exists():
        findings.append(
            _finding(
                "WARN",
                "kaikki_wiktionary_missing",
                f"Kaikki Japanese JSONL is unavailable: {_path_for_report(kaikki_jsonl_gz)}",
            )
        )
        return []
    posture = _source_posture(policy, "kaikki_wiktionary_topic")
    candidates_by_lemma = _candidates_by_lemma(candidates)
    topic_mappings = _kaikki_topic_mappings(policy)
    evidence: list[dict[str, object]] = []
    entries_seen = 0
    exact_entries = 0
    reading_identity_stats: Counter[str] = Counter()
    with gzip.open(kaikki_jsonl_gz, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            entries_seen += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(entry.get("lang_code") or "") != "ja":
                continue
            word = str(entry.get("word") or "").strip()
            if word not in candidates_by_lemma:
                continue
            exact_entries += 1
            pos = str(entry.get("pos") or "")
            if pos == "romanization":
                continue
            entry_readings = _kaikki_entry_readings(entry)
            verified_candidates = _verified_external_candidates(
                word,
                candidates_by_lemma.get(word, []),
                source_readings=entry_readings,
                stats=reading_identity_stats,
            )
            if not verified_candidates:
                continue
            for sense_index, sense in enumerate(_mapping_rows(entry.get("senses")), start=1):
                labels = _kaikki_sense_topic_labels(sense)
                for source_label in labels:
                    for mapped in topic_mappings.get(_normalize_label(source_label), ()):
                        for candidate, reading_identity in verified_candidates:
                            evidence.append(
                                _evidence_row(
                                    candidate=candidate,
                                    source="kaikki_wiktionary_topic",
                                    topic=str(mapped.get("target_family") or ""),
                                    membership=_coalesce_float(
                                        mapped.get("membership"),
                                        posture.get("default_membership"),
                                        0.68,
                                    ),
                                    confidence=_coalesce_float(
                                        mapped.get("confidence"),
                                        posture.get("default_confidence"),
                                        0.66,
                                    ),
                                    source_label=source_label,
                                    evidence_label=f"Kaikki/Wiktionary sense topic: {source_label}",
                                    sense={"match_mode": reading_identity},
                                    review_posture=str(posture.get("review_posture") or ""),
                                    license_note=str(posture.get("license_note") or ""),
                                    extra={
                                        "reading_identity": reading_identity,
                                        "kaikki_entry_readings": entry_readings[:12],
                                        "kaikki_word": word,
                                        "kaikki_pos": pos,
                                        "kaikki_sense_index": sense_index,
                                        "kaikki_topics": _string_list(sense.get("topics")),
                                        "kaikki_categories": [
                                            str(row.get("name") or "")
                                            for row in _mapping_rows(sense.get("categories"))[:10]
                                        ],
                                        "kaikki_glosses": _string_list(sense.get("glosses"))[:4],
                                    },
                                )
                            )
    findings.append(
        _finding(
            "PASS",
            "kaikki_wiktionary_completed",
            (
                f"Scanned {entries_seen} Kaikki Japanese entries, found {exact_entries} "
                f"exact candidate headwords, and generated {len(evidence)} topic rows. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}."
            ),
        )
    )
    return evidence


def _wikidata_online_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    chunk_size: int,
    sleep_seconds: float,
    timeout_seconds: int,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    roots = _mapping_rows(policy.get("wikidata_roots"))
    if not roots:
        findings.append(_finding("WARN", "wikidata_roots_missing", "No Wikidata roots configured."))
        return []
    root_by_qid = {str(row.get("qid") or ""): row for row in roots}
    evidence: list[dict[str, object]] = []
    candidates_by_lemma = _candidates_by_lemma(candidates)
    reading_identity_stats: Counter[str] = Counter()
    try:
        for chunk in _chunks(sorted(candidates_by_lemma), chunk_size):
            rows = _query_wikidata_chunk(chunk, roots=roots, timeout_seconds=timeout_seconds)
            for raw in rows:
                lemma = str(raw.get("lemma") or "")
                verified_candidates = _verified_external_candidates(
                    lemma,
                    candidates_by_lemma.get(lemma, []),
                    source_readings=(),
                    stats=reading_identity_stats,
                )
                root_qid = str(raw.get("root_qid") or "")
                mapped = root_by_qid.get(root_qid)
                if not verified_candidates or not mapped:
                    continue
                posture = _source_posture(policy, "wikidata_online")
                for candidate, reading_identity in verified_candidates:
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source="wikidata_online",
                            topic=str(mapped.get("target_family") or ""),
                            membership=_coalesce_float(
                                mapped.get("membership"),
                                posture.get("default_membership"),
                                0.75,
                            ),
                            confidence=_coalesce_float(
                                mapped.get("confidence"),
                                posture.get("default_confidence"),
                                0.72,
                            ),
                            source_label=str(mapped.get("label") or root_qid),
                            evidence_label=f"Wikidata root {mapped.get('label') or root_qid}",
                            sense={"match_mode": reading_identity},
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                            extra={
                                "reading_identity": reading_identity,
                                "wikidata_qid": str(raw.get("item_qid") or ""),
                                "wikidata_root_qid": root_qid,
                                "wikidata_item_label": str(raw.get("item_label") or ""),
                            },
                        )
                    )
            if sleep_seconds:
                time.sleep(sleep_seconds)
        findings.append(
            _finding(
                "PASS",
                "wikidata_online_completed",
                f"Queried Wikidata for {len(candidates_by_lemma)} bounded labels. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}.",
            )
        )
    except Exception as exc:  # pragma: no cover - network failure path
        findings.append(
            _finding(
                "WARN",
                "wikidata_sparql_failed",
                f"Wikidata SPARQL probe failed; trying API search fallback: {exc}",
            )
        )
        evidence.extend(
            _wikidata_api_search_evidence(
                candidates=candidates,
                policy=policy,
                sleep_seconds=sleep_seconds,
                timeout_seconds=timeout_seconds,
                findings=findings,
            )
        )
    return evidence


def _ndl_online_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    chunk_size: int,
    sleep_seconds: float,
    timeout_seconds: int,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    rules = _japanese_keyword_rules(policy)
    evidence: list[dict[str, object]] = []
    candidates_by_lemma = _candidates_by_lemma(candidates)
    posture = _source_posture(policy, "ndl_online")
    reading_identity_stats: Counter[str] = Counter()
    try:
        for chunk in _chunks(sorted(candidates_by_lemma), chunk_size):
            rows = _query_ndl_chunk(chunk, timeout_seconds=timeout_seconds)
            for raw in rows:
                lemma = str(raw.get("lemma") or "")
                source_readings = [
                    label
                    for label in (
                        str(raw.get("alt_label") or ""),
                        str(raw.get("label") or ""),
                    )
                    if _is_kana_like(label)
                ]
                verified_candidates = _verified_external_candidates(
                    lemma,
                    candidates_by_lemma.get(lemma, []),
                    source_readings=source_readings,
                    stats=reading_identity_stats,
                )
                if not verified_candidates:
                    continue
                haystack = " ".join(
                    str(raw.get(key) or "")
                    for key in ("label", "alt_label", "broader_label", "related_label")
                )
                for rule in rules:
                    matched = _matched_japanese_rule(rule, haystack)
                    if not matched:
                        continue
                    for candidate, reading_identity in verified_candidates:
                        evidence.append(
                            _evidence_row(
                                candidate=candidate,
                                source="ndl_online",
                                topic=str(rule.get("target_family") or ""),
                                membership=_coalesce_float(
                                    rule.get("membership"),
                                    posture.get("default_membership"),
                                    0.72,
                                ),
                                confidence=_coalesce_float(
                                    rule.get("confidence"),
                                    posture.get("default_confidence"),
                                    0.7,
                                ),
                                source_label=matched,
                                evidence_label=f"NDL authority keyword: {matched}",
                                sense={"match_mode": reading_identity},
                                review_posture=str(posture.get("review_posture") or ""),
                                license_note=str(posture.get("license_note") or ""),
                                extra={
                                    "reading_identity": reading_identity,
                                    "source_readings": source_readings,
                                    "ndl_uri": str(raw.get("uri") or ""),
                                    "ndl_label": str(raw.get("label") or ""),
                                    "ndl_broader_label": str(raw.get("broader_label") or ""),
                                },
                            )
                        )
            if sleep_seconds:
                time.sleep(sleep_seconds)
        findings.append(
            _finding(
                "PASS",
                "ndl_online_completed",
                f"Queried Web NDL Authorities for {len(candidates_by_lemma)} bounded labels. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}.",
            )
        )
    except Exception as exc:  # pragma: no cover - network failure path
        findings.append(_finding("WARN", "ndl_online_failed", f"NDL probe failed: {exc}"))
    return evidence


def _jawikipedia_category_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    chunk_size: int,
    sleep_seconds: float,
    timeout_seconds: int,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    rules = _japanese_keyword_rules(policy)
    evidence: list[dict[str, object]] = []
    candidates_by_lemma = _candidates_by_lemma(candidates)
    posture = _source_posture(policy, "jawikipedia_category_online")
    reading_identity_stats: Counter[str] = Counter()
    try:
        for chunk in _chunks(sorted(candidates_by_lemma), min(chunk_size, 50)):
            pages = _query_jawikipedia_categories(chunk, timeout_seconds=timeout_seconds)
            for lemma, page in pages.items():
                verified_candidates = _verified_external_candidates(
                    lemma,
                    candidates_by_lemma.get(lemma, []),
                    source_readings=(),
                    stats=reading_identity_stats,
                )
                if not verified_candidates:
                    continue
                categories = _string_list(page.get("categories"))
                haystack = " ".join([lemma, str(page.get("title") or ""), *categories])
                for rule in rules:
                    matched = _matched_japanese_rule(rule, haystack)
                    if not matched:
                        continue
                    for candidate, reading_identity in verified_candidates:
                        evidence.append(
                            _evidence_row(
                                candidate=candidate,
                                source="jawikipedia_category_online",
                                topic=str(rule.get("target_family") or ""),
                                membership=_coalesce_float(
                                    rule.get("membership"),
                                    posture.get("default_membership"),
                                    0.62,
                                ),
                                confidence=_coalesce_float(
                                    rule.get("confidence"),
                                    posture.get("default_confidence"),
                                    0.58,
                                ),
                                source_label=matched,
                                evidence_label=f"ja.wikipedia category/title keyword: {matched}",
                                sense={"match_mode": reading_identity},
                                review_posture=str(posture.get("review_posture") or ""),
                                license_note=str(posture.get("license_note") or ""),
                                extra={
                                    "reading_identity": reading_identity,
                                    "wikipedia_title": str(page.get("title") or ""),
                                    "wikipedia_pageid": str(page.get("pageid") or ""),
                                    "wikipedia_categories": categories[:12],
                                },
                            )
                        )
            if sleep_seconds:
                time.sleep(sleep_seconds)
        findings.append(
            _finding(
                "PASS",
                "jawikipedia_online_completed",
                f"Queried ja.wikipedia categories for {len(candidates_by_lemma)} bounded titles. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}.",
            )
        )
    except Exception as exc:  # pragma: no cover - network failure path
        findings.append(
            _finding("WARN", "jawikipedia_online_failed", f"ja.wikipedia probe failed: {exc}")
        )
    return evidence


def _query_wikidata_chunk(
    labels: Sequence[str],
    *,
    roots: Sequence[Mapping[str, object]],
    timeout_seconds: int,
) -> list[dict[str, object]]:
    label_values = " ".join(f'"{_sparql_escape(label)}"' for label in labels)
    root_values = " ".join(f"wd:{_sparql_escape(str(row.get('qid') or ''))}" for row in roots)
    query = f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?lemma ?item ?itemLabel ?root WHERE {{
  VALUES ?lemma {{ {label_values} }}
  VALUES ?root {{ {root_values} }}
  ?item rdfs:label ?label .
  FILTER(LANG(?label) = "ja" && STR(?label) = ?lemma)
  {{
    ?item wdt:P31/wdt:P279* ?root .
  }} UNION {{
    ?item wdt:P279* ?root .
  }}
  OPTIONAL {{ ?item rdfs:label ?itemLabel FILTER(LANG(?itemLabel) = "ja") }}
}}
LIMIT 1000
"""
    payload = _http_json(
        WIKIDATA_SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        timeout_seconds=timeout_seconds,
    )
    rows: list[dict[str, object]] = []
    for binding in _mapping_rows(_as_mapping(_as_mapping(payload).get("results")).get("bindings")):
        item_uri = _binding_value(binding, "item")
        root_uri = _binding_value(binding, "root")
        rows.append(
            {
                "lemma": _binding_value(binding, "lemma"),
                "item_qid": item_uri.rsplit("/", 1)[-1],
                "root_qid": root_uri.rsplit("/", 1)[-1],
                "item_label": _binding_value(binding, "itemLabel"),
            }
        )
    return rows


def _query_ndl_chunk(labels: Sequence[str], *, timeout_seconds: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for label in labels:
        rows.extend(_query_ndl_label(label, timeout_seconds=timeout_seconds))
    return rows


def _query_ndl_label(label: str, *, timeout_seconds: int) -> list[dict[str, object]]:
    query = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?s ?label ?altLabel ?broaderLabel ?relatedLabel WHERE {{
  ?s rdfs:label ?label .
  FILTER(STR(?label) = "{_sparql_escape(label)}")
  OPTIONAL {{ ?s skos:altLabel ?altLabel }}
  OPTIONAL {{ ?s skos:broader ?broader . ?broader rdfs:label ?broaderLabel }}
  OPTIONAL {{ ?s skos:related ?related . ?related rdfs:label ?relatedLabel }}
}}
LIMIT 100
"""
    payload = _http_json(
        NDL_SPARQL_ENDPOINT,
        params={"query": query, "output": "json"},
        timeout_seconds=timeout_seconds,
    )
    rows: list[dict[str, object]] = []
    for binding in _mapping_rows(_as_mapping(_as_mapping(payload).get("results")).get("bindings")):
        rows.append(
            {
                "lemma": label,
                "uri": _binding_value(binding, "s"),
                "label": _binding_value(binding, "label"),
                "alt_label": _binding_value(binding, "altLabel"),
                "broader_label": _binding_value(binding, "broaderLabel"),
                "related_label": _binding_value(binding, "relatedLabel"),
            }
        )
    return rows


def _wikidata_api_search_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    sleep_seconds: float,
    timeout_seconds: int,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    posture = _source_posture(policy, "wikidata_online")
    gloss_rules = [
        _compile_gloss_rule(row) for row in _mapping_rows(policy.get("jmdict_gloss_keyword_rules"))
    ]
    japanese_rules = _japanese_keyword_rules(policy)
    evidence: list[dict[str, object]] = []
    candidates_by_lemma = _candidates_by_lemma(candidates)
    reading_identity_stats: Counter[str] = Counter()
    completed = 0
    for lemma, candidate_rows in sorted(candidates_by_lemma.items()):
        if not lemma:
            continue
        try:
            payload = _http_json(
                WIKIDATA_API_ENDPOINT,
                params={
                    "action": "wbsearchentities",
                    "format": "json",
                    "language": "ja",
                    "uselang": "en",
                    "type": "item",
                    "limit": "5",
                    "search": lemma,
                },
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - network failure path
            findings.append(
                _finding("WARN", "wikidata_api_search_failed", f"Wikidata API failed: {exc}")
            )
            return evidence
        completed += 1
        for result in _mapping_rows(payload.get("search")):
            label = str(result.get("label") or "")
            aliases = _string_list(result.get("aliases"))
            if lemma != label:
                continue
            source_readings = [alias for alias in aliases if _is_kana_like(alias)]
            verified_candidates = _verified_external_candidates(
                lemma,
                candidate_rows,
                source_readings=source_readings,
                stats=reading_identity_stats,
            )
            if not verified_candidates:
                continue
            description = str(result.get("description") or "")
            ja_haystack = " ".join([label, *aliases])
            en_haystack = " ".join(
                [description, str(result.get("match", {}).get("text", ""))]
            ).lower()
            for rule in japanese_rules:
                matched = _matched_japanese_rule(rule, ja_haystack)
                if matched:
                    for candidate, reading_identity in verified_candidates:
                        evidence.append(
                            _evidence_row(
                                candidate=candidate,
                                source="wikidata_online",
                                topic=str(rule.get("target_family") or ""),
                                membership=_coalesce_float(
                                    rule.get("membership"),
                                    posture.get("default_membership"),
                                    0.75,
                                ),
                                confidence=_coalesce_float(
                                    rule.get("confidence"),
                                    posture.get("default_confidence"),
                                    0.72,
                                ),
                                source_label=matched,
                                evidence_label=f"Wikidata API exact label/alias keyword: {matched}",
                                sense={"match_mode": reading_identity},
                                review_posture=str(posture.get("review_posture") or ""),
                                license_note=str(posture.get("license_note") or ""),
                                extra={
                                    "reading_identity": reading_identity,
                                    "source_readings": source_readings,
                                    "wikidata_qid": str(result.get("id") or ""),
                                    "wikidata_label": label,
                                    "wikidata_description": description,
                                    "wikidata_adapter": "wbsearchentities_fallback",
                                },
                            )
                        )
            for rule in gloss_rules:
                matched = _matched_gloss_rule(rule, en_haystack)
                if matched:
                    for candidate, reading_identity in verified_candidates:
                        evidence.append(
                            _evidence_row(
                                candidate=candidate,
                                source="wikidata_online",
                                topic=str(rule.get("target_family") or ""),
                                membership=_coalesce_float(
                                    rule.get("membership"),
                                    posture.get("default_membership"),
                                    0.75,
                                ),
                                confidence=_coalesce_float(
                                    rule.get("confidence"),
                                    posture.get("default_confidence"),
                                    0.72,
                                ),
                                source_label=str(rule.get("id") or matched),
                                evidence_label=f"Wikidata API description keyword: {matched}",
                                sense={"match_mode": reading_identity},
                                review_posture=str(posture.get("review_posture") or ""),
                                license_note=str(posture.get("license_note") or ""),
                                extra={
                                    "reading_identity": reading_identity,
                                    "source_readings": source_readings,
                                    "wikidata_qid": str(result.get("id") or ""),
                                    "wikidata_label": label,
                                    "wikidata_description": description,
                                    "wikidata_adapter": "wbsearchentities_fallback",
                                },
                            )
                        )
        if sleep_seconds:
            time.sleep(sleep_seconds)
    findings.append(
        _finding(
            "PASS",
            "wikidata_api_search_completed",
            f"Queried Wikidata wbsearchentities fallback for {completed} exact labels. "
            f"Reading identity gate: {_format_counter(reading_identity_stats)}.",
        )
    )
    return evidence


def _query_jawikipedia_categories(
    titles: Sequence[str], *, timeout_seconds: int
) -> dict[str, dict[str, object]]:
    payload = _http_json(
        JAWIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "prop": "categories",
            "cllimit": "max",
            "redirects": "1",
            "titles": "|".join(titles),
        },
        timeout_seconds=timeout_seconds,
    )
    normalized_to: dict[str, str] = {}
    for row in _mapping_rows(_as_mapping(_as_mapping(payload).get("query")).get("normalized")):
        normalized_to[str(row.get("to") or "")] = str(row.get("from") or "")
    pages: dict[str, dict[str, object]] = {}
    for page in _as_mapping(_as_mapping(payload).get("query")).get("pages", {}).values():
        if not isinstance(page, Mapping) or "missing" in page:
            continue
        title = str(page.get("title") or "")
        requested = normalized_to.get(title, title)
        if requested not in titles:
            continue
        categories = [
            str(row.get("title") or "").replace("Category:", "").replace("カテゴリ:", "")
            for row in _mapping_rows(page.get("categories"))
        ]
        pages[requested] = {
            "title": title,
            "pageid": page.get("pageid"),
            "categories": sorted(set(categories)),
        }
    return pages


def _http_json(
    url: str,
    *,
    params: Mapping[str, object],
    timeout_seconds: int,
) -> Mapping[str, object]:
    request_url = f"{url}?{urlencode({key: str(value) for key, value in params.items()})}"
    request = Request(request_url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - bounded public endpoints
        return _as_mapping(json.loads(response.read().decode("utf-8")))


def _evidence_row(
    *,
    candidate: Mapping[str, object],
    source: str,
    topic: str,
    membership: float,
    confidence: float,
    source_label: str,
    evidence_label: str,
    sense: Mapping[str, object] | None,
    review_posture: str,
    license_note: str,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    row = {
        "language_pair": "en-ja",
        "lemma": str(candidate.get("lemma") or ""),
        "reading": str(candidate.get("reading") or ""),
        "rank": candidate.get("rank"),
        "score": _round_float(candidate.get("score")),
        "band": str(candidate.get("band") or ""),
        "core_rank": _round_float(candidate.get("core_rank")),
        "candidate_state": str(candidate.get("candidate_state") or ""),
        "admission_override": str(candidate.get("admission_override") or ""),
        "topic_stretch_allowed": str(candidate.get("topic_stretch_allowed") or ""),
        "correction_types": str(candidate.get("correction_types") or ""),
        "source": source,
        "topic": topic,
        "membership": _round_float(membership),
        "confidence": _round_float(confidence),
        "source_label": source_label,
        "evidence_label": evidence_label,
        "review_posture": review_posture,
        "license_note": license_note,
        "match_mode": str(_as_mapping(sense).get("match_mode") or "external_exact_label"),
        "jmdict_ent_seq": str(_as_mapping(sense).get("ent_seq") or ""),
        "jmdict_sense_index": _as_mapping(sense).get("sense_index"),
        "jmdict_fields": _string_list(_as_mapping(sense).get("fields")),
        "jmdict_misc": _string_list(_as_mapping(sense).get("misc")),
        "jmdict_pos": _string_list(_as_mapping(sense).get("pos")),
        "glosses": _string_list(_as_mapping(sense).get("glosses"))[:8],
        "ambiguity_flags": _ambiguity_flags(candidate=candidate, source=source, sense=sense),
    }
    if extra:
        row["extra"] = dict(extra)
    return row


def _ambiguity_flags(
    *,
    candidate: Mapping[str, object],
    source: str,
    sense: Mapping[str, object] | None,
) -> list[str]:
    flags: list[str] = []
    match_mode = str(_as_mapping(sense).get("match_mode") or "")
    externally_verified_modes = {
        "external_exact_source_reading",
        "external_kana_exact_surface",
        "external_unique_surface_reading",
    }
    if match_mode == "external_unique_surface_reading":
        flags.append("surface_only_unique_reading")
    elif match_mode and match_mode not in {"surface_reading", *externally_verified_modes}:
        flags.append(match_mode)
    if source.startswith(WEAK_SOURCE_PREFIXES):
        flags.append("weak_inferred_source")
    if str(candidate.get("candidate_state") or "") != "normal_vocab":
        flags.append("non_normal_candidate_state")
    if str(candidate.get("topic_stretch_allowed") or "").lower() == "false":
        flags.append("topic_stretch_disallowed")
    glosses = _string_list(_as_mapping(sense).get("glosses"))
    if len(glosses) > 4:
        flags.append("many_glosses")
    return sorted(set(flags))


def _dedupe_evidence(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str, str, str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("source") or ""),
            str(row.get("topic") or ""),
            str(row.get("source_label") or ""),
            str(row.get("evidence_label") or ""),
        )
        if not key[0] or not key[2] or not key[3]:
            continue
        existing = by_key.get(key)
        if existing is None or (
            float(row.get("confidence") or 0.0),
            float(row.get("membership") or 0.0),
        ) > (
            float(existing.get("confidence") or 0.0),
            float(existing.get("membership") or 0.0),
        ):
            by_key[key] = dict(row)
    return sorted(by_key.values(), key=_evidence_sort_key)


def _apply_evidence_quality_guards(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sources_by_item_topic: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in rows:
        sources_by_item_topic[
            (
                str(row.get("lemma") or ""),
                str(row.get("reading") or ""),
                str(row.get("topic") or ""),
            )
        ].add(str(row.get("source") or ""))

    kept: list[dict[str, object]] = []
    rejected: Counter[str] = Counter()
    for row in rows:
        reason = _quality_reject_reason(row, sources_by_item_topic=sources_by_item_topic)
        if reason:
            rejected[f"{row.get('source')}:{reason}"] += 1
            continue
        kept.append(dict(row))

    if not rejected:
        return kept, []
    return kept, [
        _finding(
            "PASS",
            "topic_evidence_quality_guards_applied",
            "Rejected source-specific low-precision topic rows: " + _format_counter(rejected),
        )
    ]


def _quality_reject_reason(
    row: Mapping[str, object],
    *,
    sources_by_item_topic: Mapping[tuple[str, str, str], set[str]],
) -> str:
    source = str(row.get("source") or "")
    if source == "kaikki_wiktionary_topic":
        return _kaikki_sense_scope_reject_reason(row, sources_by_item_topic=sources_by_item_topic)
    if source == "jawikipedia_dump_category":
        return _jawikipedia_dump_category_reject_reason(row)
    return ""


def _jawikipedia_dump_category_reject_reason(row: Mapping[str, object]) -> str:
    score = _safe_float(row.get("score"), default=1.0)
    if score > 0.25:
        return ""
    if _wiki_lemma_is_topic_literal(row):
        return ""
    source_label = str(row.get("source_label") or "").strip()
    if not source_label:
        return "low_score_uncorroborated_category"
    extra = _as_mapping(row.get("extra"))
    lemma = str(row.get("lemma") or "")
    title = str(extra.get("wikipedia_title") or "")
    resolved_title = str(extra.get("wikipedia_resolved_title") or "")
    if _wiki_title_corroborates_source_label(
        source_label,
        lemma=lemma,
        title=title,
        resolved_title=resolved_title,
    ):
        return ""
    return "low_score_uncorroborated_category"


def _kaikki_sense_scope_reject_reason(
    row: Mapping[str, object],
    *,
    sources_by_item_topic: Mapping[tuple[str, str, str], set[str]],
) -> str:
    extra = _as_mapping(row.get("extra"))
    lemma = str(row.get("lemma") or "")
    reading = str(row.get("reading") or "")
    topic = str(row.get("topic") or "")
    peer_sources = sources_by_item_topic.get((lemma, reading, topic), set())
    has_cross_source_agreement = len(peer_sources - {"kaikki_wiktionary_topic"}) > 0
    sense_index = _safe_int(extra.get("kaikki_sense_index"))
    score = _safe_float(row.get("score"), default=1.0)
    pos = _normalize_label(extra.get("kaikki_pos"))
    is_literal_topic = _lemma_is_topic_literal(row)

    if pos == "name" and score <= 0.25 and not is_literal_topic:
        return "low_score_name_entry"
    if sense_index > 1 and score <= 0.18 and not is_literal_topic:
        return "low_score_nonprimary_sense"
    weak_label_reason = _kaikki_weak_broad_label_reject_reason(
        row,
        is_literal_topic=is_literal_topic,
    )
    if weak_label_reason:
        return weak_label_reason

    if not _is_generic_topic_candidate(row):
        return ""

    if _has_kaikki_short_for_or_redirect_gloss(row):
        return "generic_short_for_or_redirect_sense"
    if sense_index > 1:
        return "generic_nonprimary_sense"
    if _is_broad_kaikki_label(row) and not has_cross_source_agreement:
        return "generic_broad_single_source_sense"
    return ""


def _kaikki_weak_broad_label_reject_reason(
    row: Mapping[str, object],
    *,
    is_literal_topic: bool,
) -> str:
    score = _safe_float(row.get("score"), default=1.0)
    if score > 0.25 or is_literal_topic:
        return ""
    label = _normalize_label(row.get("source_label"))
    weak_labels = {"business", "engineering", "media", "philosophy", "religion", "sciences"}
    if label not in weak_labels:
        return ""
    if label in {"philosophy", "religion", "sciences"}:
        return "weak_broad_label_without_topic_anchor"
    if _has_kaikki_weak_label_anchor(row, source_label=label):
        return ""
    return "weak_broad_label_without_topic_anchor"


def _has_kaikki_weak_label_anchor(row: Mapping[str, object], *, source_label: str) -> bool:
    extra = _as_mapping(row.get("extra"))
    text = " ".join(
        [
            " ".join(_string_list(extra.get("kaikki_glosses"))),
            " ".join(_string_list(extra.get("kaikki_categories"))),
        ]
    ).lower()
    anchors_by_label = {
        "business": (
            "account",
            "bank",
            "business",
            "ceo",
            "commercial",
            "company",
            "econom",
            "executive",
            "finance",
            "market",
            "president",
            "sale",
            "shop",
            "sold",
            "store",
            "trade",
        ),
        "engineering": (
            "computer",
            "computing",
            "engineer",
            "engineering",
            "mechanical",
            "technology",
        ),
        "media": (
            "broadcast",
            "film",
            "media",
            "movie",
            "program",
            "television",
            "tv",
        ),
    }
    return any(anchor in text for anchor in anchors_by_label.get(source_label, ()))


def _is_generic_topic_candidate(row: Mapping[str, object]) -> bool:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return False
    score = _safe_float(row.get("score"), default=1.0)
    if score > 0.25:
        return False
    extra = _as_mapping(row.get("extra"))
    pos = _normalize_label(extra.get("kaikki_pos"))
    if _is_single_kanji(lemma):
        return True
    if pos in {"verb", "adjective", "adj", "adverb", "pronoun", "determiner", "particle"}:
        return True
    if score <= 0.08 and _kanji_count(lemma) <= 2 and not _is_katakana_like(lemma):
        return True
    return False


def _lemma_is_topic_literal(row: Mapping[str, object]) -> bool:
    lemma = str(row.get("lemma") or "")
    topic = str(row.get("topic") or "")
    return _lemma_matches_topic_keywords(
        lemma,
        topic=topic,
        allow_single_character_substrings=True,
    )


def _wiki_lemma_is_topic_literal(row: Mapping[str, object]) -> bool:
    lemma = str(row.get("lemma") or "")
    topic = str(row.get("topic") or "")
    return _lemma_matches_topic_keywords(
        lemma,
        topic=topic,
        allow_single_character_substrings=False,
    )


def _lemma_matches_topic_keywords(
    lemma: str,
    *,
    topic: str,
    allow_single_character_substrings: bool,
) -> bool:
    for keyword in _topic_literal_keywords(topic):
        if not keyword:
            continue
        if len(keyword) == 1 and not allow_single_character_substrings:
            if lemma == keyword:
                return True
            continue
        if keyword in lemma:
            return True
    return False


def _topic_literal_keywords(topic: str) -> tuple[str, ...]:
    keywords_by_topic = {
        "animals": ("動物", "犬", "猫", "鳥", "魚", "虫", "獣", "嘴"),
        "anime_manga_pop_culture": ("漫画", "アニメ", "コミック", "声優", "アイドル", "コスプレ"),
        "arts_literature_humanities": ("文学", "小説", "詩", "宗教", "寺", "仏", "神", "歴史"),
        "computing_internet": ("コンピュー", "インターネット", "通信", "電子", "ソフト", "アプリ"),
        "finance_business": ("会社", "経済", "金融", "金利", "株", "資", "社長", "経費"),
        "food_cooking": (
            "料理",
            "食",
            "食べ",
            "食べ物",
            "飲む",
            "飲み",
            "飯",
            "御飯",
            "ご飯",
            "茶",
            "酒",
            "パン",
            "牛乳",
            "肉",
            "野菜",
            "果物",
        ),
        "games": ("ゲーム", "将棋", "囲碁", "麻雀", "チェス", "カード"),
        "law_politics_civics": ("法", "政治", "裁判", "軍", "税", "国会", "国家"),
        "medicine_health": ("医", "病", "疾", "薬", "風邪", "歯", "解剖", "身体", "鼻"),
        "music_media_entertainment": ("音楽", "映画", "テレビ", "番組", "コンサート"),
        "plants_nature": ("植物", "花", "花見", "花瓶", "木", "草", "菌", "農", "園芸"),
        "science_math": ("科学", "数学", "物理", "化学", "天文", "星", "生物", "地学"),
        "science_technology": ("科学", "数学", "物理", "化学", "天文", "星", "コンピュー"),
        "shopping_money": ("買", "売", "店", "商", "金", "円", "価格", "料金", "財布", "株"),
        "sports_fitness": (
            "スポーツ",
            "野球",
            "サッカー",
            "相撲",
            "柔道",
            "テニス",
            "ゴルフ",
            "登山",
        ),
        "travel_places_transport": (
            "旅行",
            "旅",
            "交通",
            "鉄道",
            "航空",
            "駅",
            "空港",
            "ホテル",
            "バス",
        ),
        "work_office": ("仕事", "会社", "社員", "会議", "書類", "職", "勤務", "上司", "社長"),
    }
    return keywords_by_topic.get(topic, ())


def _wiki_title_corroborates_source_label(
    source_label: str,
    *,
    lemma: str,
    title: str,
    resolved_title: str,
) -> bool:
    titles = tuple(part for part in (lemma, title, resolved_title) if part)
    if len(source_label) == 1:
        return source_label in titles
    return any(source_label in title_part for title_part in titles)


def _has_kaikki_short_for_or_redirect_gloss(row: Mapping[str, object]) -> bool:
    extra = _as_mapping(row.get("extra"))
    gloss_blob = " ; ".join(_string_list(extra.get("kaikki_glosses"))).lower()
    if not gloss_blob:
        return False
    markers = (
        "short for",
        "abbreviation of",
        "abbreviated form",
        "clipping of",
        "ellipsis of",
        "synonym of",
        "alternative form of",
        "alt form of",
        "see:",
    )
    return any(marker in gloss_blob for marker in markers)


def _is_broad_kaikki_label(row: Mapping[str, object]) -> bool:
    label = _normalize_label(row.get("source_label"))
    broad_labels = {
        "art",
        "business",
        "games",
        "health",
        "history",
        "law",
        "literature",
        "media",
        "military",
        "music",
        "philosophy",
        "politics",
        "religion",
        "sciences",
        "sports",
        "technology",
        "transport",
    }
    return label in broad_labels


def _is_single_kanji(value: str) -> bool:
    return len(value) == 1 and _is_cjk_unified_ideograph(value)


def _kanji_count(value: str) -> int:
    return sum(1 for char in value if _is_cjk_unified_ideograph(char))


def _is_cjk_unified_ideograph(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def _is_katakana_like(value: str) -> bool:
    return bool(value) and all(
        "\u30a0" <= char <= "\u30ff" or char in {"ー", "・"} for char in value
    )


def _select_sample_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_per_cell: int,
    max_rows: int,
    max_rows_per_source: int,
) -> list[dict[str, object]]:
    cells: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        cell = "|".join(
            [
                str(row.get("source") or ""),
                str(row.get("topic") or ""),
                str(row.get("band") or ""),
                "ambiguous" if row.get("ambiguity_flags") else "clean",
            ]
        )
        cells[cell].append(row)
    for cell_rows in cells.values():
        cell_rows.sort(key=_sample_sort_key)
    selected: list[dict[str, object]] = []
    selected_by_source: Counter[str] = Counter()
    for round_index in range(sample_per_cell):
        for cell in sorted(cells):
            if len(selected) >= max_rows:
                return selected
            if round_index < len(cells[cell]):
                row = cells[cell][round_index]
                source = str(row.get("source") or "")
                if max_rows_per_source and selected_by_source[source] >= max_rows_per_source:
                    continue
                selected.append(dict(row))
                selected_by_source[source] += 1
    return selected


def _source_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source") or "")].append(row)
    summary: dict[str, dict[str, object]] = {}
    for source, source_rows in sorted(grouped.items()):
        summary[source] = {
            "row_count": len(source_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in source_rows}),
            "topic_count": len({str(row.get("topic") or "") for row in source_rows}),
            "avg_membership": _round_float(_mean(row.get("membership") for row in source_rows)),
            "avg_confidence": _round_float(_mean(row.get("confidence") for row in source_rows)),
            "ambiguity_flag_count": sum(1 for row in source_rows if row.get("ambiguity_flags")),
        }
    return summary


def _topic_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("topic") or "")].append(row)
    summary: dict[str, dict[str, object]] = {}
    for topic, topic_rows in sorted(grouped.items()):
        summary[topic] = {
            "row_count": len(topic_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in topic_rows}),
            "source_count": len({str(row.get("source") or "") for row in topic_rows}),
            "source_counts": dict(
                sorted(Counter(str(row.get("source") or "") for row in topic_rows).items())
            ),
        }
    return summary


def _sample_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "row_count": len(rows),
        "source_counts": dict(
            sorted(Counter(str(row.get("source") or "") for row in rows).items())
        ),
        "topic_counts": dict(sorted(Counter(str(row.get("topic") or "") for row in rows).items())),
    }


def _taxonomy_source_mappings(
    taxonomy: Mapping[str, object],
    *,
    channel: str,
) -> dict[str, list[Mapping[str, object]]]:
    mappings: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(taxonomy.get("source_label_mappings")):
        if str(row.get("source_channel") or "") != channel:
            continue
        mappings[_normalize_label(row.get("source_label"))].append(row)
    return dict(mappings)


def _source_posture(policy: Mapping[str, object], source: str) -> Mapping[str, object]:
    return _as_mapping(_as_mapping(policy.get("source_posture")).get(source))


def _compile_gloss_rule(row: Mapping[str, object]) -> dict[str, object]:
    return {
        **dict(row),
        "_include_patterns": [
            re.compile(str(pattern), re.IGNORECASE) for pattern in row.get("include_any", [])
        ],
        "_exclude_patterns": [
            re.compile(str(pattern), re.IGNORECASE) for pattern in row.get("exclude_any", [])
        ],
    }


def _matched_gloss_rule(rule: Mapping[str, object], gloss_blob: str) -> str:
    for pattern in rule.get("_exclude_patterns", []):
        if pattern.search(gloss_blob):
            return ""
    for pattern in rule.get("_include_patterns", []):
        if pattern.search(gloss_blob):
            return pattern.pattern
    return ""


def _japanese_keyword_rules(policy: Mapping[str, object]) -> list[Mapping[str, object]]:
    return _mapping_rows(policy.get("japanese_text_keyword_rules"))


def _matched_japanese_rule(rule: Mapping[str, object], haystack: str) -> str:
    if not haystack:
        return ""
    for keyword in _string_list(rule.get("include_any")):
        if keyword and keyword in haystack:
            return keyword
    return ""


def _candidates_by_lemma(
    candidates: Sequence[Mapping[str, object]],
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for candidate in candidates:
        lemma = str(candidate.get("lemma") or "").strip()
        if lemma:
            grouped[lemma].append(candidate)
    return dict(grouped)


def _kaikki_topic_mappings(policy: Mapping[str, object]) -> dict[str, list[Mapping[str, object]]]:
    mappings: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(policy.get("kaikki_topic_mappings")):
        mappings[_normalize_label(row.get("source_label"))].append(row)
    return dict(mappings)


def _kaikki_sense_topic_labels(sense: Mapping[str, object]) -> list[str]:
    labels: list[str] = []
    labels.extend(_string_list(sense.get("topics")))
    for category in _mapping_rows(sense.get("categories")):
        name = str(category.get("orig") or category.get("name") or "").strip()
        if not name:
            continue
        if name.startswith("ja:"):
            labels.append(name[3:])
        labels.append(name)
    return sorted(set(labels))


def _kaikki_entry_readings(entry: Mapping[str, object]) -> list[str]:
    readings: set[str] = set()
    word = str(entry.get("word") or "").strip()
    for form in _mapping_rows(entry.get("forms")):
        form_text = str(form.get("form") or "").strip()
        if form_text and _is_kana_like(form_text):
            readings.add(form_text)
        ruby_reading = _ruby_reading(form.get("ruby"))
        if ruby_reading:
            readings.add(ruby_reading)
    for sound in _mapping_rows(entry.get("sounds")):
        other = str(sound.get("other") or "").strip()
        if other and _is_kana_like(other):
            readings.add(other)
    if word and _is_kana_like(word):
        readings.add(word)
    return sorted(reading for reading in readings if _normalize_ja_reading(reading))


def _ruby_reading(value: object) -> str:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ""
    pieces: list[str] = []
    for part in value:
        if isinstance(part, Sequence) and not isinstance(part, (str, bytes)) and len(part) >= 2:
            pieces.append(str(part[1] or ""))
    reading = "".join(pieces).strip()
    return reading if _is_kana_like(reading) else ""


def _verified_external_candidates(
    surface: str,
    candidates: Sequence[Mapping[str, object]],
    *,
    source_readings: Sequence[str],
    stats: Counter[str] | None = None,
) -> list[tuple[Mapping[str, object], str]]:
    normalized_source_readings = {
        _normalize_ja_reading(reading)
        for reading in source_readings
        if _normalize_ja_reading(reading)
    }
    candidate_readings = {_candidate_normalized_reading(candidate) for candidate in candidates} - {
        ""
    }
    has_unique_candidate_reading = len(candidate_readings) == 1
    surface_is_kana_exact = _is_kana_like(surface)
    normalized_surface = _normalize_ja_reading(surface) if surface_is_kana_exact else ""
    verified: list[tuple[Mapping[str, object], str]] = []
    for candidate in candidates:
        candidate_reading = _candidate_normalized_reading(candidate)
        if normalized_source_readings:
            if candidate_reading in normalized_source_readings:
                _increment(stats, "accepted_exact_source_reading")
                verified.append((candidate, "external_exact_source_reading"))
            else:
                _increment(stats, "rejected_conflicting_source_reading")
            continue
        if surface_is_kana_exact and normalized_surface == candidate_reading:
            _increment(stats, "accepted_kana_exact_surface")
            verified.append((candidate, "external_kana_exact_surface"))
        elif has_unique_candidate_reading:
            _increment(stats, "accepted_unique_surface_reading")
            verified.append((candidate, "external_unique_surface_reading"))
        else:
            _increment(stats, "rejected_ambiguous_surface_only")
    return verified


def _candidate_normalized_reading(candidate: Mapping[str, object]) -> str:
    return str(candidate.get("normalized_reading") or "").strip() or _normalize_ja_reading(
        candidate.get("reading") or candidate.get("lemma")
    )


def _increment(counter: Counter[str] | None, key: str) -> None:
    if counter is not None:
        counter[key] += 1


def _format_counter(counter: Mapping[str, int]) -> str:
    if not counter:
        return "no candidates checked"
    return ", ".join(f"{key}={counter[key]}" for key in sorted(counter))


def _iter_mysql_insert_rows(path: Path) -> Iterable[list[str]]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.startswith("INSERT INTO"):
                continue
            values_marker = " VALUES "
            values_start = line.find(values_marker)
            if values_start < 0:
                continue
            yield from _parse_mysql_values(line[values_start + len(values_marker) :].rstrip(";\n"))


def _parse_mysql_values(values_blob: str) -> Iterable[list[str]]:
    row: list[str] | None = None
    value_chars: list[str] = []
    in_string = False
    escaped = False
    for char in values_blob:
        if row is None:
            if char == "(":
                row = []
                value_chars = []
            continue
        if in_string:
            if escaped:
                value_chars.append(_mysql_unescape_char(char))
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_string = False
            else:
                value_chars.append(char)
            continue
        if char == "'":
            in_string = True
        elif char == ",":
            row.append(_clean_mysql_value("".join(value_chars)))
            value_chars = []
        elif char == ")":
            row.append(_clean_mysql_value("".join(value_chars)))
            yield row
            row = None
            value_chars = []
        else:
            value_chars.append(char)


def _mysql_unescape_char(char: str) -> str:
    escapes = {"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a"}
    return escapes.get(char, char)


def _clean_mysql_value(value: str) -> str:
    cleaned = value.strip()
    return "" if cleaned.upper() == "NULL" else cleaned


def _wiki_title_display(value: object) -> str:
    return str(value or "").replace("_", " ").strip()


def _is_ignored_wiki_category(title: str) -> bool:
    ignore_fragments = (
        "スタブ",
        "曖昧さ回避",
        "出典",
        "加筆依頼",
        "修正が必要",
        "独自研究",
        "中立的観点",
        "ウィキデータ",
        "ウィキペディア",
        "テンプレート",
        "プロジェクト",
        "画像提供依頼",
        "コモンズ",
        "書きかけ",
        "改名提案",
        "ISBN",
        "識別子",
        "年没",
        "年生",
        "生年不明",
        "没年不明",
    )
    return any(fragment in title for fragment in ignore_fragments)


def _child_texts(elem: ET.Element, path: str) -> list[str]:
    return [_clean_text(child.text) for child in elem.findall(path) if _clean_text(child.text)]


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _normalize_ja_reading(value: object) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return ""
    return normalize_reading(cleaned, language_tag="ja")


def _is_kana_like(value: str) -> bool:
    return bool(value) and all(
        "\u3040" <= char <= "\u30ff" or char in {"ー", "・", "ヽ", "ヾ", "ゝ", "ゞ"}
        for char in value
    )


def _stronger_match_mode(current: str, candidate: str) -> str:
    priority = {"surface_reading": 0, "kana_reading": 1}
    if not current:
        return candidate
    return current if priority.get(current, 99) <= priority.get(candidate, 99) else candidate


def _normalize_label(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_english_gloss(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9+ #.-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    if len(text) <= 1 or len(text) > 64:
        return ""
    if text.startswith("to "):
        return ""
    return text


def _candidate_by_lemma(
    candidates: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for candidate in candidates:
        lemma = str(candidate.get("lemma") or "").strip()
        if lemma and lemma not in result:
            result[lemma] = candidate
    return result


def _online_candidate_slice(
    candidates: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[Mapping[str, object]]:
    if limit <= 0:
        return []
    rows = [
        row
        for row in candidates
        if str(row.get("lemma") or "").strip()
        and len(str(row.get("lemma") or "").strip()) <= 24
        and str(row.get("candidate_state") or "") == "normal_vocab"
    ]
    return rows[:limit]


def _evidence_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("source") or ""),
        str(row.get("topic") or ""),
        float(row.get("score") or 0.0),
        str(row.get("lemma") or ""),
        str(row.get("reading") or ""),
        str(row.get("evidence_label") or ""),
    )


def _sample_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        -float(row.get("confidence") or 0.0),
        -float(row.get("membership") or 0.0),
        float(row.get("score") or 0.0),
        _stable_hash(
            str(row.get("source") or ""), str(row.get("topic") or ""), str(row.get("lemma") or "")
        ),
    )


def _score_band(score: float) -> str:
    low = max(0.0, min(0.95, int(score * 20) / 20))
    high = min(1.0, low + 0.05)
    return f"{low:.2f}-{high:.2f}"


def _safe_float(value: object, *, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: object, *, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _coalesce_float(*values: object) -> float:
    for value in values:
        if value not in (None, ""):
            return _safe_float(value)
    return 0.0


def _round_float(value: object) -> float:
    return round(_safe_float(value), 6)


def _mean(values: Iterable[object]) -> float:
    floats = [_safe_float(value) for value in values]
    return sum(floats) / len(floats) if floats else 0.0


def _stable_hash(*parts: str) -> int:
    digest = hashlib.sha256("\u241f".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _chunks(values: Sequence[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield list(values[index : index + size])


def _sparql_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _binding_value(binding: Mapping[str, object], key: str) -> str:
    return str(_as_mapping(binding.get(key)).get("value") or "")


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _as_mapping(payload)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _resolve_jmdict_path(path: Path | None) -> Path | None:
    if path:
        return _resolve_path(path)
    for candidate in (DEFAULT_JMDICT, LEGACY_JMDICT):
        resolved = _resolve_path(candidate)
        if resolved.exists():
            return resolved
    return _resolve_path(DEFAULT_JMDICT)


def _path_for_report(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
