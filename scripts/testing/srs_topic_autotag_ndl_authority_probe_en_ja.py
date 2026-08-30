#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    DEFAULT_CANDIDATES_CSV,
    DEFAULT_POLICY_JSON,
    NDL_SPARQL_ENDPOINT,
    _as_mapping,
    _binding_value,
    _candidates_by_lemma,
    _coalesce_float,
    _evidence_row,
    _format_counter,
    _http_json,
    _is_kana_like,
    _japanese_keyword_rules,
    _load_candidates,
    _load_json,
    _mapping_rows,
    _matched_japanese_rule,
    _safe_float,
    _select_sample_rows,
    _source_posture,
    _source_summary,
    _sparql_escape,
    _string_list,
    _verified_external_candidates,
)
from srs_topic_autotag_wikidata_claim_probe_en_ja import (  # noqa: E402
    DEFAULT_EXISTING_OVERLAY_JSON,
    _covered_overlay_lemmas,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_CACHE_JSON = TEST_OUTPUTS_ROOT / "srs_topic_autotag_ndl_authority_probe_cache_en_ja.json"
DEFAULT_CHUNK_DIR = TEST_OUTPUTS_ROOT / "srs_topic_autotag_ndl_authority_probe_chunks_en_ja"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_ndl_authority_probe_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_ndl_authority_probe_en_ja_latest.md"
LANGUAGE_PAIR = "en-ja"
SOURCE_ID = "ndl_authority_probe"
DEFAULT_TOP_N = 73752
DEFAULT_CHUNK_SIZE = 250
TOPIC_SCHEME_SUFFIXES = {"topicalTerms"}
SAFE_AUTHORITY_KINDS = {"ndlsh"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe Web NDL Authorities exact-label rows as en-ja SRS topic evidence. "
            "This is evidence-only and does not promote runtime overlay rows."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument("--existing-overlay-json", type=Path, default=DEFAULT_EXISTING_OVERLAY_JSON)
    parser.add_argument("--cache-json", type=Path, default=DEFAULT_CACHE_JSON)
    parser.add_argument("--chunk-dir", type=Path, default=DEFAULT_CHUNK_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--start-chunk", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=0)
    parser.add_argument("--lemma", action="append", default=[])
    parser.add_argument(
        "--exclude-covered",
        action="store_true",
        help="Skip lemmas already covered by the existing product-safe topic overlay.",
    )
    parser.add_argument(
        "--include-non-topical-authorities",
        action="store_true",
        help="Also emit topic evidence from non-topical authority schemes. Default keeps those cached/countable only.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--offline-only", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=240)
    parser.add_argument("--fail-on-incomplete", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    candidates_csv = _resolve_path(args.candidates_csv)
    policy_json = _resolve_path(args.policy_json)
    existing_overlay_json = _resolve_path(args.existing_overlay_json)
    cache_json = _resolve_path(args.cache_json)
    chunk_dir = _resolve_path(args.chunk_dir)
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    top_n = max(0, int(args.top_n))
    chunk_size = max(1, int(args.chunk_size))
    include_covered = not bool(args.exclude_covered)
    include_non_topical_authorities = bool(args.include_non_topical_authorities)

    policy = _load_json(policy_json) if policy_json.exists() else {}
    candidates = _load_candidates(candidates_csv, top_n=top_n)
    covered_lemmas = _covered_overlay_lemmas(existing_overlay_json)
    selected_candidates = _select_candidates(
        candidates,
        explicit_lemmas=tuple(str(lemma) for lemma in args.lemma),
        covered_lemmas=covered_lemmas,
        include_covered=include_covered,
    )
    chunks = _chunks(selected_candidates, chunk_size)
    run_id = _run_id(
        selected_candidates,
        chunk_size=chunk_size,
        include_covered=include_covered,
        include_non_topical_authorities=include_non_topical_authorities,
    )
    chunk_dir.mkdir(parents=True, exist_ok=True)
    cache = NdlAuthorityCache.load(cache_json)

    start_chunk = max(0, int(args.start_chunk))
    selected_indexes = list(range(start_chunk, len(chunks)))
    if int(args.max_chunks) > 0:
        selected_indexes = selected_indexes[: int(args.max_chunks)]

    if not args.merge_only:
        for chunk_index in selected_indexes:
            chunk_path = _chunk_json_path(chunk_dir, chunk_index)
            if not args.force and _completed_chunk_exists(chunk_path, run_id=run_id):
                print(f"[skip] chunk {chunk_index:04d} already complete: {chunk_path}")
                continue
            chunk_report = build_chunk_report(
                candidates=chunks[chunk_index],
                policy=policy,
                cache=cache,
                cache_json=cache_json,
                chunk_index=chunk_index,
                chunk_size=chunk_size,
                run_id=run_id,
                include_non_topical_authorities=include_non_topical_authorities,
                offline_only=bool(args.offline_only),
                sleep_seconds=max(0.0, float(args.sleep_seconds)),
                timeout_seconds=max(1, int(args.timeout_seconds)),
                sample_per_cell=max(0, int(args.sample_per_cell)),
                max_sample_rows=max(0, int(args.max_sample_rows)),
                generated_at=_utc_now(),
            )
            _write_json(chunk_path, chunk_report)
            _chunk_markdown_path(chunk_dir, chunk_index).write_text(
                render_chunk_markdown(chunk_report), encoding="utf-8"
            )
            cache.write(cache_json)
            print(
                f"[write] chunk {chunk_index:04d}: "
                f"{len(_mapping_rows(chunk_report.get('evidence_rows')))} evidence rows"
            )

    merged = build_merged_report(
        chunk_dir=chunk_dir,
        run_id=run_id,
        expected_chunk_count=len(chunks),
        eligible_label_count=len(selected_candidates),
        chunk_size=chunk_size,
        include_covered=include_covered,
        include_non_topical_authorities=include_non_topical_authorities,
        candidates_csv=candidates_csv,
        policy_json=policy_json,
        existing_overlay_json=existing_overlay_json,
        cache_json=cache_json,
        top_n=top_n,
        generated_at=_utc_now(),
    )
    _write_json(json_out, merged)
    markdown_out.write_text(render_markdown(merged), encoding="utf-8")
    print(f"[write] merged JSON: {json_out}")
    print(f"[write] merged Markdown: {markdown_out}")
    if args.fail_on_incomplete and merged["status"] != "ok":
        return 1
    return 0


def build_chunk_report(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    cache: "NdlAuthorityCache",
    cache_json: Path,
    chunk_index: int,
    chunk_size: int,
    run_id: str,
    include_non_topical_authorities: bool,
    offline_only: bool,
    sleep_seconds: float,
    timeout_seconds: int,
    sample_per_cell: int,
    max_sample_rows: int,
    generated_at: str,
) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    client = NdlAuthorityClient(
        cache=cache,
        offline_only=offline_only,
        sleep_seconds=sleep_seconds,
        timeout_seconds=timeout_seconds,
    )
    evidence_rows: list[dict[str, object]] = []
    reading_identity_stats: Counter[str] = Counter()
    authority_scheme_counts: Counter[str] = Counter()
    authority_kind_counts: Counter[str] = Counter()
    candidates_by_lemma = _candidates_by_lemma(candidates)
    posture = _source_posture(policy, "ndl_online")
    rules = _japanese_keyword_rules(policy)
    for lemma, candidate_rows in sorted(candidates_by_lemma.items()):
        authority_rows = client.query_label(lemma)
        for authority_row in authority_rows:
            authority_scheme_counts.update(_string_list(authority_row.get("scheme_kinds")))
            authority_kind_counts.update([str(authority_row.get("authority_kind") or "unknown")])
        evidence_rows.extend(
            _evidence_rows_from_authorities(
                lemma=lemma,
                candidate_rows=candidate_rows,
                authority_rows=authority_rows,
                rules=rules,
                posture=posture,
                include_non_topical_authorities=include_non_topical_authorities,
                reading_identity_stats=reading_identity_stats,
            )
        )
    client_summary = client.summary()
    if int(client_summary.get("query_error_count") or 0):
        findings.append(
            _finding(
                "WARN",
                "ndl_query_errors",
                f"NDL query errors occurred for {client_summary.get('query_error_count')} label(s).",
            )
        )
    findings.append(
        _finding(
            "PASS",
            "ndl_chunk_completed",
            (
                f"Checked {len(candidates_by_lemma)} exact labels. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}."
            ),
        )
    )
    evidence_rows = _dedupe_evidence_rows(evidence_rows)
    review_sample = _select_sample_rows(
        evidence_rows,
        sample_per_cell=sample_per_cell,
        max_rows=max_sample_rows,
        max_rows_per_source=0,
    )
    return {
        "schema_version": 1,
        "status": "ok" if not any(row["level"] == "WARN" for row in findings) else "review",
        "decision": "ndl_authority_probe_chunk_complete",
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "chunk": {
            "run_id": run_id,
            "chunk_index": chunk_index,
            "chunk_size": chunk_size,
            "label_count": len(candidates_by_lemma),
            "first_label": next(iter(sorted(candidates_by_lemma)), ""),
            "last_label": next(reversed(sorted(candidates_by_lemma)), ""),
            "complete": not any(row["level"] == "WARN" for row in findings),
        },
        "inputs": {
            "cache_json": _repo_path(cache_json),
            "include_non_topical_authorities": include_non_topical_authorities,
        },
        "method": _method(include_non_topical_authorities=include_non_topical_authorities),
        "ndl_summary": client_summary,
        "authority_scheme_counts": dict(sorted(authority_scheme_counts.items())),
        "authority_kind_counts": dict(sorted(authority_kind_counts.items())),
        "source_summary": _source_summary(evidence_rows),
        "topic_summary": _topic_summary(evidence_rows),
        "evidence_rows": evidence_rows,
        "review_sample": review_sample,
        "findings": findings,
    }


def _evidence_rows_from_authorities(
    *,
    lemma: str,
    candidate_rows: Sequence[Mapping[str, object]],
    authority_rows: Sequence[Mapping[str, object]],
    rules: Sequence[Mapping[str, object]],
    posture: Mapping[str, object],
    include_non_topical_authorities: bool,
    reading_identity_stats: Counter[str],
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for authority_row in authority_rows:
        source_readings = [
            value for value in _string_list(authority_row.get("alt_labels")) if _is_kana_like(value)
        ]
        verified_candidates = _verified_external_candidates(
            lemma,
            candidate_rows,
            source_readings=source_readings,
            stats=reading_identity_stats,
        )
        if not verified_candidates:
            continue
        if not include_non_topical_authorities and not _is_topical_authority(authority_row):
            continue
        haystack_values = [
            str(authority_row.get("label") or ""),
            *_string_list(authority_row.get("alt_labels")),
            *_string_list(authority_row.get("broader_labels")),
        ]
        haystack = " ".join(haystack_values)
        for rule in rules:
            matched = _matched_japanese_rule(rule, haystack)
            if not matched:
                continue
            for candidate, reading_identity in verified_candidates:
                evidence.append(
                    _evidence_row(
                        candidate=candidate,
                        source=SOURCE_ID,
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
                            "ndl_uri": str(authority_row.get("uri") or ""),
                            "ndl_authority_kind": str(authority_row.get("authority_kind") or ""),
                            "ndl_label": str(authority_row.get("label") or ""),
                            "ndl_alt_labels": _string_list(authority_row.get("alt_labels")),
                            "ndl_scheme_uris": _string_list(authority_row.get("scheme_uris")),
                            "ndl_scheme_kinds": _string_list(authority_row.get("scheme_kinds")),
                            "ndl_broader_labels": _string_list(authority_row.get("broader_labels")),
                            "ndl_related_labels": _string_list(authority_row.get("related_labels")),
                            "ndl_topical_authority": _is_topical_authority(authority_row),
                        },
                    )
                )
    return evidence


def _select_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    explicit_lemmas: Sequence[str],
    covered_lemmas: set[str],
    include_covered: bool,
) -> list[Mapping[str, object]]:
    by_lemma = _candidates_by_lemma(candidates)
    if explicit_lemmas:
        selected: list[Mapping[str, object]] = []
        for lemma in dict.fromkeys(
            str(value).strip() for value in explicit_lemmas if str(value).strip()
        ):
            normal_rows = _normal_single_reading_rows(by_lemma.get(lemma, ()))
            if normal_rows:
                selected.append(normal_rows[0])
        return selected
    selected = []
    for lemma, rows in by_lemma.items():
        if not include_covered and lemma in covered_lemmas:
            continue
        normal_rows = _normal_single_reading_rows(rows)
        if normal_rows:
            selected.append(normal_rows[0])
    return sorted(
        selected, key=lambda row: (int(row.get("rank") or 0), str(row.get("lemma") or ""))
    )


def _normal_single_reading_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    normal_rows = [
        row
        for row in rows
        if str(row.get("candidate_state") or "") == "normal_vocab"
        and str(row.get("topic_stretch_allowed") or "").lower() != "false"
    ]
    if len({str(row.get("reading") or "") for row in normal_rows}) != 1:
        return []
    return normal_rows


def build_merged_report(
    *,
    chunk_dir: Path,
    run_id: str,
    expected_chunk_count: int,
    eligible_label_count: int,
    chunk_size: int,
    include_covered: bool,
    include_non_topical_authorities: bool,
    candidates_csv: Path,
    policy_json: Path,
    existing_overlay_json: Path,
    cache_json: Path,
    top_n: int,
    generated_at: str,
) -> dict[str, object]:
    chunk_reports = _load_chunk_reports(chunk_dir, run_id=run_id)
    complete_reports = [report for report in chunk_reports if not _report_is_incomplete(report)]
    present_indexes = {_chunk_index(report) for report in chunk_reports}
    missing_indexes = [
        index for index in range(expected_chunk_count) if index not in present_indexes
    ]
    evidence_rows = _dedupe_evidence_rows(
        [row for report in chunk_reports for row in _mapping_rows(report.get("evidence_rows"))]
    )
    authority_scheme_counts: Counter[str] = Counter()
    authority_kind_counts: Counter[str] = Counter()
    for report in chunk_reports:
        authority_scheme_counts.update(
            {
                str(key): int(value)
                for key, value in _as_mapping(report.get("authority_scheme_counts")).items()
            }
        )
        authority_kind_counts.update(
            {
                str(key): int(value)
                for key, value in _as_mapping(report.get("authority_kind_counts")).items()
            }
        )
    findings = [
        _finding(
            "PASS" if chunk_reports else "WARN",
            "ndl_chunk_reports_loaded" if chunk_reports else "ndl_chunk_reports_missing",
            f"Loaded {len(chunk_reports)} chunk report(s) from {chunk_dir}.",
        )
    ]
    if missing_indexes:
        findings.append(
            _finding(
                "WARN",
                "ndl_chunks_missing",
                f"{len(missing_indexes)} expected chunk(s) have not been generated yet.",
            )
        )
    if any(_report_is_incomplete(report) for report in chunk_reports):
        findings.append(
            _finding("WARN", "ndl_chunks_incomplete", "One or more NDL chunks had query warnings.")
        )
    if evidence_rows:
        findings.append(
            _finding(
                "PASS", "ndl_merged_evidence_present", f"Merged {len(evidence_rows)} evidence rows."
            )
        )
    else:
        findings.append(
            _finding(
                "WARN", "ndl_merged_evidence_empty", "No merged NDL evidence rows are present yet."
            )
        )
    review_sample = _select_sample_rows(
        evidence_rows,
        sample_per_cell=4,
        max_rows=240,
        max_rows_per_source=0,
    )
    complete = (
        bool(chunk_reports)
        and not missing_indexes
        and not any(_report_is_incomplete(report) for report in chunk_reports)
    )
    return {
        "schema_version": 1,
        "status": "ok" if complete else "review",
        "decision": "ndl_authority_probe_complete"
        if complete
        else "ndl_authority_probe_incomplete",
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "policy_json": _repo_path(policy_json),
            "existing_overlay_json": _repo_path(existing_overlay_json),
            "cache_json": _repo_path(cache_json),
            "chunk_dir": _repo_path(chunk_dir),
            "run_id": run_id,
            "top_n": top_n,
            "chunk_size": chunk_size,
            "include_covered": include_covered,
            "include_non_topical_authorities": include_non_topical_authorities,
        },
        "method": _method(include_non_topical_authorities=include_non_topical_authorities),
        "chunk_summary": {
            "expected_chunk_count": expected_chunk_count,
            "loaded_chunk_count": len(chunk_reports),
            "complete_chunk_count": len(complete_reports),
            "missing_chunk_count": len(missing_indexes),
            "missing_chunk_sample": missing_indexes[:40],
            "eligible_label_count": eligible_label_count,
            "completed_label_count": sum(
                int(_as_mapping(report.get("chunk")).get("label_count") or 0)
                for report in complete_reports
            ),
        },
        "authority_scheme_counts": dict(sorted(authority_scheme_counts.items())),
        "authority_kind_counts": dict(sorted(authority_kind_counts.items())),
        "source_summary": _source_summary(evidence_rows),
        "topic_summary": _topic_summary(evidence_rows),
        "evidence_rows": evidence_rows,
        "review_sample": review_sample,
        "findings": findings,
        "limitations": [
            "This is build-time NDL authority evidence, not a runtime dependency.",
            "Default topic evidence is limited to NDLSH/topicalTerms authority rows to avoid name-authority contamination.",
            "Keyword matches over broader/related terms are review evidence; they are not promotion-ready without sampling.",
        ],
    }


class NdlAuthorityClient:
    def __init__(
        self,
        *,
        cache: "NdlAuthorityCache",
        offline_only: bool,
        sleep_seconds: float,
        timeout_seconds: int,
    ) -> None:
        self.cache = cache
        self.offline_only = offline_only
        self.sleep_seconds = sleep_seconds
        self.timeout_seconds = timeout_seconds
        self.counters: Counter[str] = Counter()

    def query_label(self, label: str) -> list[Mapping[str, object]]:
        cached = self.cache.labels.get(label)
        if cached is not None:
            self.counters["cache_hit"] += 1
            return _mapping_rows(cached)
        if self.offline_only:
            self.counters["offline_miss"] += 1
            return []
        try:
            rows = _query_ndl_label(label, timeout_seconds=self.timeout_seconds)
        except Exception as exc:  # pragma: no cover - endpoint failure path
            self.counters["query_error_count"] += 1
            self.cache.labels[label] = []
            self.cache.errors[label] = str(exc)
            return []
        self.cache.labels[label] = rows
        self.counters["query_request_count"] += 1
        if self.sleep_seconds:
            time.sleep(self.sleep_seconds)
        return rows

    def summary(self) -> dict[str, object]:
        return {
            **dict(sorted(self.counters.items())),
            "label_cache_size": len(self.cache.labels),
            "error_cache_size": len(self.cache.errors),
        }


class NdlAuthorityCache:
    def __init__(
        self,
        *,
        labels: dict[str, object] | None = None,
        errors: dict[str, str] | None = None,
    ) -> None:
        self.labels = labels or {}
        self.errors = errors or {}

    @classmethod
    def load(cls, path: Path) -> "NdlAuthorityCache":
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(
            labels=dict(_as_mapping(payload).get("labels") or {}),
            errors={
                str(key): str(value)
                for key, value in _as_mapping(_as_mapping(payload).get("errors")).items()
            },
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "labels": self.labels,
                    "errors": self.errors,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def _query_ndl_label(label: str, *, timeout_seconds: int) -> list[dict[str, object]]:
    query = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?s ?label ?altLabel ?scheme ?broaderLabel ?relatedLabel WHERE {{
  ?s rdfs:label ?label .
  FILTER(STR(?label) = "{_sparql_escape(label)}")
  OPTIONAL {{ ?s skos:altLabel ?altLabel }}
  OPTIONAL {{ ?s skos:inScheme ?scheme }}
  OPTIONAL {{ ?s skos:broader ?broader . ?broader rdfs:label ?broaderLabel }}
  OPTIONAL {{ ?s skos:related ?related . ?related rdfs:label ?relatedLabel }}
}}
LIMIT 200
"""
    payload = _http_json(
        NDL_SPARQL_ENDPOINT,
        params={"query": query, "output": "json"},
        timeout_seconds=timeout_seconds,
    )
    grouped: dict[str, dict[str, object]] = {}
    for binding in _mapping_rows(_as_mapping(_as_mapping(payload).get("results")).get("bindings")):
        uri = _binding_value(binding, "s")
        if not uri:
            continue
        row = grouped.setdefault(
            uri,
            {
                "uri": uri,
                "authority_kind": _authority_kind(uri),
                "label": _binding_value(binding, "label") or label,
                "alt_labels": [],
                "scheme_uris": [],
                "scheme_kinds": [],
                "broader_labels": [],
                "related_labels": [],
            },
        )
        _append_unique(row, "alt_labels", _binding_value(binding, "altLabel"))
        scheme_uri = _binding_value(binding, "scheme")
        _append_unique(row, "scheme_uris", scheme_uri)
        _append_unique(row, "scheme_kinds", _scheme_kind(scheme_uri))
        _append_unique(row, "broader_labels", _binding_value(binding, "broaderLabel"))
        _append_unique(row, "related_labels", _binding_value(binding, "relatedLabel"))
    return sorted(
        grouped.values(),
        key=lambda row: (str(row.get("authority_kind") or ""), str(row.get("uri") or "")),
    )


def _is_topical_authority(row: Mapping[str, object]) -> bool:
    return str(row.get("authority_kind") or "") in SAFE_AUTHORITY_KINDS and bool(
        set(_string_list(row.get("scheme_kinds"))) & TOPIC_SCHEME_SUFFIXES
    )


def _authority_kind(uri: str) -> str:
    parts = uri.rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else ""


def _scheme_kind(uri: str) -> str:
    if "#" in uri:
        return uri.rsplit("#", 1)[-1]
    return uri.rstrip("/").rsplit("/", 1)[-1] if uri else ""


def _append_unique(row: dict[str, object], key: str, value: str) -> None:
    if not value:
        return
    values = _string_list(row.get(key))
    if value not in values:
        values.append(value)
        row[key] = values


def _dedupe_evidence_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("topic") or ""),
            str(extra.get("ndl_uri") or ""),
            str(row.get("source_label") or ""),
        )
        if not key[0] or not key[2] or not key[3]:
            continue
        by_key.setdefault(key, dict(row))
    return sorted(
        by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("score")),
            str(row.get("lemma") or ""),
        ),
    )


def _topic_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("topic") or "")].append(row)
    return {
        topic: {
            "row_count": len(topic_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in topic_rows}),
        }
        for topic, topic_rows in sorted(grouped.items())
    }


def _method(*, include_non_topical_authorities: bool) -> dict[str, object]:
    return {
        "source": SOURCE_ID,
        "query_shape": "Web NDL Authorities exact rdfs:label query with SKOS scheme/broader/related labels",
        "promotion_state": "evidence_only_not_product_overlay",
        "default_authority_filter": "ndlsh/topicalTerms only",
        "include_non_topical_authorities": include_non_topical_authorities,
        "topic_assignment": "Japanese keyword rules over exact label, alternate labels, and broader labels; related labels are retained only as review context",
    }


def render_chunk_markdown(report: Mapping[str, object]) -> str:
    return _render_report(
        title="en-ja SRS Topic Autotag NDL Authority Probe Chunk",
        report=report,
        include_chunk=True,
    )


def render_markdown(report: Mapping[str, object]) -> str:
    return _render_report(
        title="en-ja SRS Topic Autotag NDL Authority Probe",
        report=report,
        include_chunk=False,
    )


def _render_report(*, title: str, report: Mapping[str, object], include_chunk: bool) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Evidence rows: `{len(_mapping_rows(report.get('evidence_rows')))}`",
    ]
    if include_chunk:
        chunk = _as_mapping(report.get("chunk"))
        lines.extend(
            [
                f"- Chunk: `{chunk.get('chunk_index', '')}`",
                f"- Labels: `{chunk.get('label_count', 0)}`",
            ]
        )
    else:
        chunk_summary = _as_mapping(report.get("chunk_summary"))
        lines.extend(
            [
                f"- Expected chunks: `{chunk_summary.get('expected_chunk_count', 0)}`",
                f"- Complete chunks: `{chunk_summary.get('complete_chunk_count', 0)}`",
                f"- Missing chunks: `{chunk_summary.get('missing_chunk_count', 0)}`",
                f"- Eligible labels: `{chunk_summary.get('eligible_label_count', 0)}`",
            ]
        )
    lines.extend(["", "## Authority Schemes", "", "| Scheme | Rows |", "| --- | ---: |"])
    for scheme, count in _as_mapping(report.get("authority_scheme_counts")).items():
        lines.append(f"| `{scheme}` | {count} |")
    lines.extend(["", "## Topics", "", "| Topic | Rows | Lemmas |", "| --- | ---: | ---: |"])
    for topic, row in _as_mapping(report.get("topic_summary")).items():
        topic_row = _as_mapping(row)
        lines.append(
            f"| `{topic}` | {topic_row.get('row_count', 0)} | {topic_row.get('lemma_count', 0)} |"
        )
    lines.extend(["", "## Review Sample", ""])
    lines.extend(_sample_table(_mapping_rows(report.get("review_sample"))))
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: {finding.get('message', '')}"
        )
    return "\n".join(lines) + "\n"


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Score | Source label | NDL label | Broader | Related context |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{_safe_float(row.get('score'), default=0.0):.3f} | `{row.get('source_label', '')}` | "
            f"`{extra.get('ndl_label', '')}` | "
            f"`{', '.join(_string_list(extra.get('ndl_broader_labels'))[:4])}` | "
            f"`{', '.join(_string_list(extra.get('ndl_related_labels'))[:4])}` |"
        )
    return lines


def _load_chunk_reports(chunk_dir: Path, *, run_id: str) -> list[Mapping[str, object]]:
    reports: list[Mapping[str, object]] = []
    for path in sorted(chunk_dir.glob("chunk_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            isinstance(payload, Mapping)
            and str(_as_mapping(payload.get("chunk")).get("run_id") or "") == run_id
        ):
            reports.append(payload)
    return reports


def _completed_chunk_exists(path: Path, *, run_id: str) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, Mapping)
        and str(_as_mapping(payload.get("chunk")).get("run_id") or "") == run_id
        and not _report_is_incomplete(payload)
    )


def _report_is_incomplete(report: Mapping[str, object]) -> bool:
    return any(
        str(row.get("level") or "") == "WARN" for row in _mapping_rows(report.get("findings"))
    )


def _chunk_index(report: Mapping[str, object]) -> int:
    raw_index = _as_mapping(report.get("chunk")).get("chunk_index")
    try:
        return int(raw_index)
    except (TypeError, ValueError):
        return -1


def _chunks(values: Sequence[Mapping[str, object]], size: int) -> list[list[Mapping[str, object]]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _run_id(
    candidates: Sequence[Mapping[str, object]],
    *,
    chunk_size: int,
    include_covered: bool,
    include_non_topical_authorities: bool,
) -> str:
    parts = [
        "srs-topic-autotag-ndl-authority-v1",
        f"chunk_size={chunk_size}",
        f"include_covered={include_covered}",
        f"include_non_topical_authorities={include_non_topical_authorities}",
        *(f"{row.get('rank')}:{row.get('lemma')}:{row.get('reading')}" for row in candidates),
    ]
    return hashlib.sha1("\n".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


def _chunk_json_path(chunk_dir: Path, chunk_index: int) -> Path:
    return chunk_dir / f"chunk_{chunk_index:04d}.json"


def _chunk_markdown_path(chunk_dir: Path, chunk_index: int) -> Path:
    return chunk_dir / f"chunk_{chunk_index:04d}.md"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _repo_path(path: Path) -> str:
    resolved = Path(path).expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
