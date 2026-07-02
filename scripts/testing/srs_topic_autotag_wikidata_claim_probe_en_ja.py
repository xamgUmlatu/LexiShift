#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import sys
import time
from typing import Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    DEFAULT_CANDIDATES_CSV,
    DEFAULT_POLICY_JSON,
    JAWIKIPEDIA_API,
    USER_AGENT,
    WIKIDATA_API_ENDPOINT,
    _as_mapping,
    _candidates_by_lemma,
    _coalesce_float,
    _evidence_row,
    _format_counter,
    _is_kana_like,
    _load_candidates,
    _load_json,
    _mapping_rows,
    _resolve_path,
    _safe_float,
    _select_sample_rows,
    _source_posture,
    _source_summary,
    _string_list,
    _verified_external_candidates,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_EXISTING_OVERLAY_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_en_ja_latest.json"
)
DEFAULT_CACHE_JSON = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_cache_en_ja.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_en_ja_latest.md"

LANGUAGE_PAIR = "en-ja"
SOURCE_ID = "wikidata_claim_probe"
CLAIM_PROPS = ("P31", "P279", "P171")
MAX_ENTITY_IDS_PER_REQUEST = 50
WIKIDATA_ENTITYDATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe Wikidata exact-label entity claims as en-ja SRS topic evidence. "
            "This is evidence-only and never promotes runtime overlay rows."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument("--existing-overlay-json", type=Path, default=DEFAULT_EXISTING_OVERLAY_JSON)
    parser.add_argument("--cache-json", type=Path, default=DEFAULT_CACHE_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=73752)
    parser.add_argument("--max-labels", type=int, default=80)
    parser.add_argument(
        "--lemma",
        action="append",
        default=[],
        help="Explicit candidate lemma to probe; repeatable. Overrides stratified sample when set.",
    )
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-entity-requests", type=int, default=20)
    parser.add_argument("--max-branch-targets", type=int, default=24)
    parser.add_argument(
        "--label-lookup",
        choices=("jawikipedia_pageprops", "wikidata_search"),
        default="jawikipedia_pageprops",
    )
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--retry-after-seconds", type=float, default=0.0)
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=160)
    parser.add_argument("--include-covered", action="store_true")
    parser.add_argument("--offline-only", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        candidates_csv=_resolve_path(args.candidates_csv),
        policy_json=_resolve_path(args.policy_json),
        existing_overlay_json=_resolve_path(args.existing_overlay_json),
        cache_json=_resolve_path(args.cache_json),
        top_n=max(0, int(args.top_n)),
        max_labels=max(0, int(args.max_labels)),
        explicit_lemmas=tuple(str(lemma) for lemma in args.lemma),
        max_depth=max(0, int(args.max_depth)),
        max_entity_requests=max(0, int(args.max_entity_requests)),
        max_branch_targets=max(0, int(args.max_branch_targets)),
        sleep_seconds=max(0.0, float(args.sleep_seconds)),
        timeout_seconds=max(1, int(args.timeout_seconds)),
        retry_after_seconds=max(0.0, float(args.retry_after_seconds)),
        label_lookup=str(args.label_lookup),
        sample_per_cell=max(0, int(args.sample_per_cell)),
        max_sample_rows=max(0, int(args.max_sample_rows)),
        include_covered=bool(args.include_covered),
        offline_only=bool(args.offline_only),
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
    policy_json: Path = DEFAULT_POLICY_JSON,
    existing_overlay_json: Path = DEFAULT_EXISTING_OVERLAY_JSON,
    cache_json: Path = DEFAULT_CACHE_JSON,
    top_n: int = 73752,
    max_labels: int = 80,
    explicit_lemmas: Sequence[str] = (),
    max_depth: int = 4,
    max_entity_requests: int = 20,
    max_branch_targets: int = 24,
    sleep_seconds: float = 1.0,
    timeout_seconds: int = 30,
    retry_after_seconds: float = 30.0,
    label_lookup: str = "jawikipedia_pageprops",
    sample_per_cell: int = 4,
    max_sample_rows: int = 160,
    include_covered: bool = False,
    offline_only: bool = False,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    policy = _load_json(policy_json) if policy_json.exists() else {}
    candidates = _load_candidates(candidates_csv, top_n=top_n)
    covered_lemmas = _covered_overlay_lemmas(existing_overlay_json)
    selected_candidates = _select_probe_candidates(
        candidates,
        covered_lemmas=covered_lemmas,
        max_labels=max_labels,
        include_covered=include_covered,
        explicit_lemmas=explicit_lemmas,
    )
    roots = _wikidata_roots(policy)
    findings: list[dict[str, object]] = []
    if not roots:
        findings.append(
            _finding("FAIL", "wikidata_roots_missing", "No Wikidata roots are configured.")
        )
    cache = WikidataProbeCache.load(cache_json)
    client = WikidataClient(
        cache=cache,
        sleep_seconds=sleep_seconds,
        timeout_seconds=timeout_seconds,
        retry_after_seconds=retry_after_seconds,
        offline_only=offline_only,
        max_entity_requests=max_entity_requests,
        max_branch_targets=max_branch_targets,
        label_lookup=label_lookup,
    )
    evidence_rows: list[dict[str, object]] = []
    if roots and selected_candidates:
        evidence_rows = _wikidata_claim_evidence(
            candidates=selected_candidates,
            policy=policy,
            roots=roots,
            client=client,
            max_depth=max_depth,
            findings=findings,
        )
    if not offline_only:
        cache.write(cache_json)
    source_summary = _source_summary(evidence_rows)
    client_summary = client.summary()
    if int(client_summary.get("http_429_count") or 0):
        findings.append(
            _finding(
                "WARN",
                "wikidata_rate_limited",
                f"Wikidata returned HTTP 429 {client_summary.get('http_429_count')} time(s); probe stopped affected branches.",
            )
        )
    if int(client_summary.get("entity_request_budget_exhausted") or 0):
        findings.append(
            _finding(
                "WARN",
                "wikidata_entity_budget_exhausted",
                "The configured entity-request budget was exhausted before all ancestry paths were explored.",
            )
        )
    review_sample = _select_sample_rows(
        evidence_rows,
        sample_per_cell=sample_per_cell,
        max_rows=max_sample_rows,
        max_rows_per_source=0,
    )
    if evidence_rows:
        findings.append(
            _finding(
                "PASS",
                "wikidata_claim_evidence_generated",
                f"Generated {len(evidence_rows)} Wikidata claim evidence rows.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "wikidata_claim_evidence_empty",
                "No Wikidata claim evidence rows were generated for the selected sample.",
            )
        )
    status = "ok" if evidence_rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "wikidata_claim_probe_has_topic_evidence"
            if evidence_rows
            else "wikidata_claim_probe_needs_more_sampling_or_roots"
        ),
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "policy_json": _repo_path(policy_json),
            "existing_overlay_json": _repo_path(existing_overlay_json),
            "cache_json": _repo_path(cache_json),
            "top_n": top_n,
            "max_labels": max_labels,
            "explicit_lemmas": list(explicit_lemmas),
            "max_depth": max_depth,
            "max_entity_requests": max_entity_requests,
            "max_branch_targets": max_branch_targets,
            "include_covered": include_covered,
            "offline_only": offline_only,
            "label_lookup": label_lookup,
        },
        "method": {
            "source": SOURCE_ID,
            "query_shape": (
                "Japanese Wikipedia pageprops title-to-QID lookup, then Wikidata "
                "Special:EntityData cached claim ancestry"
            )
            if label_lookup == "jawikipedia_pageprops"
            else "Wikidata API exact-label search, then cached entity claim ancestry",
            "claim_properties": list(CLAIM_PROPS),
            "promotion_state": "evidence_only_not_product_overlay",
            "identity_gate": (
                "exact Japanese label/alias search plus existing single-reading or source-reading "
                "verification; ambiguous multi-reading surfaces are rejected"
            ),
        },
        "candidate_summary": {
            "loaded_count": len(candidates),
            "selected_label_count": len(selected_candidates),
            "covered_lemma_count": len(covered_lemmas),
            "selected_by_band": dict(
                sorted(Counter(str(row.get("band") or "") for row in selected_candidates).items())
            ),
            "selected_candidate_sample": [
                {
                    "rank": row.get("rank"),
                    "lemma": row.get("lemma"),
                    "reading": row.get("reading"),
                    "score": row.get("score"),
                    "band": row.get("band"),
                }
                for row in selected_candidates[:100]
            ],
        },
        "wikidata_summary": client_summary,
        "source_summary": source_summary,
        "topic_summary": _topic_summary(evidence_rows),
        "evidence_rows": evidence_rows,
        "review_sample": review_sample,
        "findings": findings,
        "limitations": [
            "This probe samples exact labels only; it does not measure full Wikidata coverage.",
            "Wikidata labels identify entities/concepts, not SRS sense suitability by themselves.",
            "Claim ancestry can miss useful rows when Wikidata models a term through properties outside P31/P279/P171.",
            "Rows generated here are mining evidence only; promotion requires source-specific guards and review.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("wikidata_summary"))
    candidate_summary = _as_mapping(report.get("candidate_summary"))
    lines = [
        "# en-ja SRS Topic Autotag Wikidata Claim Probe",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Selected labels: `{candidate_summary.get('selected_label_count', 0)}`",
        f"- Evidence rows: `{len(_mapping_rows(report.get('evidence_rows')))} `",
        f"- Search requests: `{summary.get('search_request_count', 0)}`",
        f"- Entity requests: `{summary.get('entity_request_count', 0)}`",
        "",
        "## Candidate Sample",
        "",
        "| Band | Labels |",
        "| --- | ---: |",
    ]
    for band, count in _as_mapping(candidate_summary.get("selected_by_band")).items():
        lines.append(f"| `{band}` | {count} |")
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
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _wikidata_claim_evidence(
    *,
    candidates: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    roots: Mapping[str, Mapping[str, object]],
    client: "WikidataClient",
    max_depth: int,
    findings: list[dict[str, object]],
) -> list[dict[str, object]]:
    posture = _source_posture(policy, "wikidata_online")
    candidates_by_lemma = _candidates_by_lemma(candidates)
    client.prefetch_pageprops(sorted(candidates_by_lemma))
    reading_identity_stats: Counter[str] = Counter()
    evidence: list[dict[str, object]] = []
    exact_entity_count = 0
    mapped_entity_count = 0
    no_root_path_count = 0
    disambiguation_page_count = 0
    for lemma, candidate_rows in sorted(candidates_by_lemma.items()):
        search_rows = client.search_exact_label(lemma)
        exact_results = [row for row in search_rows if _is_exact_label_result(row, lemma=lemma)]
        if not exact_results:
            continue
        source_readings = _source_readings_from_search_results(exact_results)
        verified_candidates = _verified_external_candidates(
            lemma,
            candidate_rows,
            source_readings=source_readings,
            stats=reading_identity_stats,
        )
        if not verified_candidates:
            continue
        for result in exact_results[:3]:
            qid = str(result.get("id") or "")
            if not qid:
                continue
            exact_entity_count += 1
            entity = client.entity(qid)
            if _is_wikidata_disambiguation_entity(entity):
                disambiguation_page_count += 1
                continue
            matches = client.root_matches(qid, roots=roots, max_depth=max_depth)
            if not matches:
                no_root_path_count += 1
                continue
            matches = _nearest_root_matches(matches)
            mapped_entity_count += 1
            for match in matches:
                root = roots.get(str(match.get("root_qid") or ""), {})
                for candidate, reading_identity in verified_candidates:
                    evidence.append(
                        _evidence_row(
                            candidate=candidate,
                            source=SOURCE_ID,
                            topic=str(root.get("target_family") or ""),
                            membership=_coalesce_float(
                                root.get("membership"),
                                posture.get("default_membership"),
                                0.72,
                            ),
                            confidence=_coalesce_float(
                                root.get("confidence"),
                                posture.get("default_confidence"),
                                0.7,
                            ),
                            source_label=str(root.get("label") or match.get("root_qid") or ""),
                            evidence_label=(
                                "Wikidata claim path: "
                                f"{_entity_label(entity)} -> {root.get('label') or match.get('root_qid')}"
                            ),
                            sense={"match_mode": reading_identity},
                            review_posture=str(posture.get("review_posture") or ""),
                            license_note=str(posture.get("license_note") or ""),
                            extra={
                                "reading_identity": reading_identity,
                                "source_readings": source_readings,
                                "wikidata_qid": qid,
                                "wikidata_label": _entity_label(entity),
                                "wikidata_description": _entity_description(entity),
                                "wikidata_root_qid": str(match.get("root_qid") or ""),
                                "wikidata_root_label": str(root.get("label") or ""),
                                "wikidata_path": match.get("path") or [],
                                "wikidata_depth": match.get("depth"),
                                "wikidata_search_match": result.get("match") or {},
                            },
                        )
                    )
    findings.append(
        _finding(
            "PASS",
            "wikidata_claim_probe_completed",
            (
                f"Checked {len(candidates_by_lemma)} exact labels, found {exact_entity_count} "
                f"exact entities, skipped {disambiguation_page_count} disambiguation pages, "
                f"mapped {mapped_entity_count}, missed roots for {no_root_path_count}. "
                f"Reading identity gate: {_format_counter(reading_identity_stats)}."
            ),
        )
    )
    return _dedupe_evidence_rows(evidence)


def _select_probe_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    covered_lemmas: set[str],
    max_labels: int,
    include_covered: bool,
    explicit_lemmas: Sequence[str],
) -> list[Mapping[str, object]]:
    if max_labels <= 0:
        return []
    by_lemma = _candidates_by_lemma(candidates)
    if explicit_lemmas:
        selected: list[Mapping[str, object]] = []
        for lemma in dict.fromkeys(
            str(value).strip() for value in explicit_lemmas if str(value).strip()
        ):
            rows = [
                row
                for row in by_lemma.get(lemma, ())
                if str(row.get("candidate_state") or "") == "normal_vocab"
            ]
            if rows:
                selected.append(rows[0])
        return selected[:max_labels]
    unique_rows: list[Mapping[str, object]] = []
    for lemma, rows in by_lemma.items():
        if not include_covered and lemma in covered_lemmas:
            continue
        normal_rows = [
            row
            for row in rows
            if str(row.get("candidate_state") or "") == "normal_vocab"
            and str(row.get("topic_stretch_allowed") or "").lower() != "false"
        ]
        if len({str(row.get("reading") or "") for row in normal_rows}) != 1:
            continue
        unique_rows.append(normal_rows[0])
    buckets = (
        ("0.05-0.25", lambda score: 0.05 <= score < 0.25),
        ("0.25-0.50", lambda score: 0.25 <= score < 0.50),
        ("0.50-0.75", lambda score: 0.50 <= score < 0.75),
        ("0.75-1.01", lambda score: 0.75 <= score <= 1.01),
    )
    by_bucket: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in unique_rows:
        score = _safe_float(row.get("score"), default=0.0)
        for bucket, predicate in buckets:
            if predicate(score):
                by_bucket[bucket].append(row)
                break
    selected: list[Mapping[str, object]] = []
    per_bucket = max(1, max_labels // len(buckets))
    for bucket, _predicate in buckets:
        rows = sorted(
            by_bucket.get(bucket, ()),
            key=lambda row: (_safe_float(row.get("score")), str(row.get("lemma"))),
        )
        selected.extend(_spread_sample(rows, per_bucket))
    if len(selected) < max_labels:
        used = {str(row.get("lemma") or "") for row in selected}
        rest = [
            row
            for row in sorted(
                unique_rows, key=lambda row: (_safe_float(row.get("score")), str(row.get("lemma")))
            )
            if str(row.get("lemma") or "") not in used
        ]
        selected.extend(rest[: max_labels - len(selected)])
    return selected[:max_labels]


def _spread_sample(rows: Sequence[Mapping[str, object]], count: int) -> list[Mapping[str, object]]:
    if count <= 0 or not rows:
        return []
    if len(rows) <= count:
        return list(rows)
    if count == 1:
        return [rows[len(rows) // 2]]
    result: list[Mapping[str, object]] = []
    for index in range(count):
        row_index = round(index * (len(rows) - 1) / (count - 1))
        result.append(rows[row_index])
    return result


class WikidataClient:
    def __init__(
        self,
        *,
        cache: "WikidataProbeCache",
        sleep_seconds: float,
        timeout_seconds: int,
        retry_after_seconds: float,
        offline_only: bool,
        max_entity_requests: int,
        max_branch_targets: int,
        label_lookup: str,
    ) -> None:
        self.cache = cache
        self.sleep_seconds = sleep_seconds
        self.timeout_seconds = timeout_seconds
        self.retry_after_seconds = retry_after_seconds
        self.offline_only = offline_only
        self.max_entity_requests = max_entity_requests
        self.max_branch_targets = max_branch_targets
        self.label_lookup = label_lookup
        self.counters: Counter[str] = Counter()

    def search_exact_label(self, label: str) -> list[Mapping[str, object]]:
        if self.label_lookup == "jawikipedia_pageprops":
            return self._search_by_jawikipedia_pageprops(label)
        cached = self.cache.search.get(label)
        if cached is not None:
            self.counters["search_cache_hit"] += 1
            return _mapping_rows(cached)
        if self.offline_only:
            self.counters["search_offline_miss"] += 1
            return []
        try:
            payload = self._api(
                {
                    "action": "wbsearchentities",
                    "format": "json",
                    "language": "ja",
                    "uselang": "en",
                    "type": "item",
                    "limit": "5",
                    "search": label,
                }
            )
        except WikidataProbeRateLimited:
            self.counters["search_rate_limited"] += 1
            return []
        rows = [dict(row) for row in _mapping_rows(payload.get("search"))]
        self.cache.search[label] = rows
        self.counters["search_request_count"] += 1
        self._sleep()
        return rows

    def _search_by_jawikipedia_pageprops(self, label: str) -> list[Mapping[str, object]]:
        cached = self.cache.pageprops.get(label)
        if cached is not None:
            self.counters["pageprops_cache_hit"] += 1
            return _pageprops_search_rows(label, _as_mapping(cached))
        if self.offline_only:
            self.counters["pageprops_offline_miss"] += 1
            return []
        try:
            payload = self._jawikipedia_api(
                {
                    "action": "query",
                    "format": "json",
                    "prop": "pageprops",
                    "redirects": "1",
                    "titles": label,
                }
            )
        except WikidataProbeRateLimited:
            self.counters["pageprops_rate_limited"] += 1
            return []
        page_payload = _extract_pageprops_result(label, payload)
        self.cache.pageprops[label] = page_payload
        self.counters["pageprops_request_count"] += 1
        self._sleep()
        return _pageprops_search_rows(label, page_payload)

    def prefetch_pageprops(self, labels: Sequence[str]) -> None:
        if self.label_lookup != "jawikipedia_pageprops":
            return
        missing = [
            label for label in dict.fromkeys(labels) if label and label not in self.cache.pageprops
        ]
        if not missing:
            self.counters["pageprops_cache_hit"] += len([label for label in labels if label])
            return
        if self.offline_only:
            self.counters["pageprops_offline_miss"] += len(missing)
            return
        for chunk in _chunks(missing, 50):
            try:
                payload = self._jawikipedia_api(
                    {
                        "action": "query",
                        "format": "json",
                        "prop": "pageprops",
                        "redirects": "1",
                        "titles": "|".join(chunk),
                    }
                )
            except WikidataProbeRateLimited:
                self.counters["pageprops_rate_limited"] += len(chunk)
                return
            for label, page_payload in _extract_pageprops_results(chunk, payload).items():
                self.cache.pageprops[label] = page_payload
            self.counters["pageprops_request_count"] += 1
            self._sleep()

    def entity(self, qid: str) -> Mapping[str, object]:
        self.ensure_entities([qid])
        return _as_mapping(self.cache.entities.get(qid))

    def ensure_entities(self, qids: Sequence[str]) -> None:
        missing = [qid for qid in dict.fromkeys(qids) if qid and qid not in self.cache.entities]
        if not missing:
            self.counters["entity_cache_hit"] += len([qid for qid in qids if qid])
            return
        if self.offline_only:
            self.counters["entity_offline_miss"] += len(missing)
            return
        for chunk in _chunks(missing, MAX_ENTITY_IDS_PER_REQUEST):
            if (
                self.max_entity_requests
                and self.counters["entity_request_count"] >= self.max_entity_requests
            ):
                self.counters["entity_request_budget_exhausted"] += 1
                return
            for qid in chunk:
                if (
                    self.max_entity_requests
                    and self.counters["entity_request_count"] >= self.max_entity_requests
                ):
                    self.counters["entity_request_budget_exhausted"] += 1
                    return
                try:
                    payload = self._entitydata(qid)
                except WikidataProbeRateLimited:
                    self.counters["entity_rate_limited"] += 1
                    return
                entity = _as_mapping(_as_mapping(payload.get("entities")).get(qid))
                if entity:
                    self.cache.entities[qid] = _simplify_entity(qid, entity)
                self.counters["entity_request_count"] += 1
                self._sleep()

    def root_matches(
        self,
        qid: str,
        *,
        roots: Mapping[str, Mapping[str, object]],
        max_depth: int,
    ) -> list[dict[str, object]]:
        root_qids = set(roots)
        matches: list[dict[str, object]] = []
        seen: set[str] = set()
        queue: deque[tuple[str, int, list[str]]] = deque([(qid, 0, [qid])])
        while queue:
            current, depth, path = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            if current in root_qids:
                matches.append({"root_qid": current, "depth": depth, "path": path})
                continue
            if depth >= max_depth:
                continue
            self.ensure_entities([current])
            entity = _as_mapping(self.cache.entities.get(current))
            targets = _claim_targets(entity, CLAIM_PROPS)
            direct_roots = [target for target in targets if target in root_qids]
            non_root_targets = [target for target in targets if target not in root_qids]
            if self.max_branch_targets and len(non_root_targets) > self.max_branch_targets:
                self.counters["branch_target_cap_applied"] += 1
                non_root_targets = non_root_targets[: self.max_branch_targets]
            targets = [*direct_roots, *non_root_targets]
            self.ensure_entities(targets)
            for target in targets:
                if target and target not in seen:
                    queue.append((target, depth + 1, [*path, target]))
        return matches

    def summary(self) -> dict[str, object]:
        return {
            **dict(sorted(self.counters.items())),
            "search_cache_size": len(self.cache.search),
            "pageprops_cache_size": len(self.cache.pageprops),
            "entity_cache_size": len(self.cache.entities),
        }

    def _api(self, params: Mapping[str, object]) -> Mapping[str, object]:
        request_url = f"{WIKIDATA_API_ENDPOINT}?{urlencode({key: str(value) for key, value in params.items()})}"
        for attempt in range(3):
            request = Request(
                request_url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - bounded public endpoint
                    return _as_mapping(json.loads(response.read().decode("utf-8")))
            except HTTPError as exc:
                if exc.code != 429 or attempt == 2:
                    raise
                self.counters["http_429_count"] += 1
                if self.retry_after_seconds <= 0:
                    raise WikidataProbeRateLimited(str(exc)) from exc
                retry_after = _safe_float(
                    exc.headers.get("Retry-After"), default=self.retry_after_seconds
                )
                time.sleep(max(self.retry_after_seconds, retry_after))
        return {}

    def _jawikipedia_api(self, params: Mapping[str, object]) -> Mapping[str, object]:
        request_url = (
            f"{JAWIKIPEDIA_API}?{urlencode({key: str(value) for key, value in params.items()})}"
        )
        request = Request(
            request_url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - bounded public endpoint
                return _as_mapping(json.loads(response.read().decode("utf-8")))
        except HTTPError as exc:
            if exc.code == 429:
                self.counters["http_429_count"] += 1
                raise WikidataProbeRateLimited(str(exc)) from exc
            raise

    def _entitydata(self, qid: str) -> Mapping[str, object]:
        request_url = WIKIDATA_ENTITYDATA_URL.format(qid=qid)
        request = Request(
            request_url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - bounded public endpoint
                return _as_mapping(json.loads(response.read().decode("utf-8")))
        except HTTPError as exc:
            if exc.code == 429:
                self.counters["http_429_count"] += 1
                raise WikidataProbeRateLimited(str(exc)) from exc
            self.counters["entity_fetch_error"] += 1
            return {}

    def _sleep(self) -> None:
        if self.sleep_seconds:
            time.sleep(self.sleep_seconds)


class WikidataProbeRateLimited(RuntimeError):
    pass


class WikidataProbeCache:
    def __init__(
        self,
        *,
        search: dict[str, object] | None = None,
        pageprops: dict[str, object] | None = None,
        entities: dict[str, object] | None = None,
    ) -> None:
        self.search = search or {}
        self.pageprops = pageprops or {}
        self.entities = entities or {}

    @classmethod
    def load(cls, path: Path) -> "WikidataProbeCache":
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(
            search=dict(_as_mapping(payload).get("search") or {}),
            pageprops=dict(_as_mapping(payload).get("pageprops") or {}),
            entities=dict(_as_mapping(payload).get("entities") or {}),
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "search": self.search,
                    "pageprops": self.pageprops,
                    "entities": self.entities,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def _simplify_entity(qid: str, entity: Mapping[str, object]) -> dict[str, object]:
    labels = {
        lang: str(_as_mapping(row).get("value") or "")
        for lang, row in _as_mapping(entity.get("labels")).items()
        if lang in {"ja", "en"}
    }
    descriptions = {
        lang: str(_as_mapping(row).get("value") or "")
        for lang, row in _as_mapping(entity.get("descriptions")).items()
        if lang in {"ja", "en"}
    }
    aliases = {
        lang: [
            str(_as_mapping(alias).get("value") or "")
            for alias in _mapping_rows(rows)
            if str(_as_mapping(alias).get("value") or "")
        ]
        for lang, rows in _as_mapping(entity.get("aliases")).items()
        if lang in {"ja", "en"}
    }
    claims = {
        prop: _claim_targets_raw(_mapping_rows(_as_mapping(entity.get("claims")).get(prop)))
        for prop in CLAIM_PROPS
    }
    return {
        "id": qid,
        "labels": labels,
        "descriptions": descriptions,
        "aliases": aliases,
        "claims": claims,
    }


def _claim_targets(entity: Mapping[str, object], props: Sequence[str]) -> list[str]:
    claims = _as_mapping(entity.get("claims"))
    targets: list[str] = []
    for prop in props:
        targets.extend(_string_list(claims.get(prop)))
    return list(dict.fromkeys(target for target in targets if target.startswith("Q")))


def _is_wikidata_disambiguation_entity(entity: Mapping[str, object]) -> bool:
    if "Q4167410" in _claim_targets(entity, ("P31",)):
        return True
    descriptions = _as_mapping(entity.get("descriptions"))
    labels = _as_mapping(entity.get("labels"))
    haystack = " ".join(
        str(value or "")
        for value in [
            labels.get("ja"),
            labels.get("en"),
            descriptions.get("ja"),
            descriptions.get("en"),
        ]
    ).lower()
    return "曖昧さ回避" in haystack or "disambiguation page" in haystack


def _claim_targets_raw(rows: Sequence[Mapping[str, object]]) -> list[str]:
    targets: list[str] = []
    for row in rows:
        value = _as_mapping(
            _as_mapping(_as_mapping(row.get("mainsnak")).get("datavalue")).get("value")
        )
        qid = str(value.get("id") or "")
        if qid.startswith("Q"):
            targets.append(qid)
    return list(dict.fromkeys(targets))


def _is_exact_label_result(row: Mapping[str, object], *, lemma: str) -> bool:
    match = _as_mapping(row.get("match"))
    if str(match.get("language") or "") == "ja" and str(match.get("text") or "") == lemma:
        return True
    if lemma in _string_list(row.get("aliases")):
        return True
    return str(row.get("label") or "") == lemma


def _source_readings_from_search_results(rows: Sequence[Mapping[str, object]]) -> list[str]:
    readings: list[str] = []
    for row in rows:
        for value in [
            str(_as_mapping(row.get("match")).get("text") or ""),
            *_string_list(row.get("aliases")),
        ]:
            if _is_kana_like(value):
                readings.append(value)
    return list(dict.fromkeys(readings))


def _extract_pageprops_result(label: str, payload: Mapping[str, object]) -> dict[str, object]:
    return _extract_pageprops_results([label], payload).get(
        label, {"requested": label, "qid": "", "title": ""}
    )


def _extract_pageprops_results(
    labels: Sequence[str], payload: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    label_set = set(labels)
    results = {label: {"requested": label, "qid": "", "title": ""} for label in labels}
    normalized_to: dict[str, str] = {}
    for row in _mapping_rows(_as_mapping(_as_mapping(payload.get("query")).get("normalized"))):
        normalized_to[str(row.get("to") or "")] = str(row.get("from") or "")
    redirects_to: dict[str, str] = {}
    for row in _mapping_rows(_as_mapping(_as_mapping(payload.get("query")).get("redirects"))):
        redirects_to[str(row.get("to") or "")] = str(row.get("from") or "")
    for page in _as_mapping(_as_mapping(payload.get("query")).get("pages")).values():
        if not isinstance(page, Mapping) or "missing" in page:
            continue
        title = str(page.get("title") or "")
        requested = redirects_to.get(title) or normalized_to.get(title) or title
        if requested not in label_set and title in label_set:
            requested = title
        if requested not in label_set:
            continue
        qid = str(_as_mapping(page.get("pageprops")).get("wikibase_item") or "")
        if not qid:
            continue
        results[requested] = {
            "qid": qid,
            "requested": requested,
            "title": title,
            "pageid": page.get("pageid"),
            "redirect_from": redirects_to.get(title, ""),
        }
    return results


def _pageprops_search_rows(
    label: str, page_payload: Mapping[str, object]
) -> list[Mapping[str, object]]:
    qid = str(page_payload.get("qid") or "")
    if not qid:
        return []
    title = str(page_payload.get("title") or label)
    aliases = [label]
    if title and title != label:
        aliases.append(title)
    return [
        {
            "id": qid,
            "label": title,
            "description": "",
            "match": {
                "type": "jawikipedia_pageprops",
                "language": "ja",
                "text": label,
            },
            "aliases": aliases,
        }
    ]


def _wikidata_roots(policy: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("qid") or ""): row
        for row in _mapping_rows(policy.get("wikidata_roots"))
        if str(row.get("qid") or "").startswith("Q") and str(row.get("target_family") or "")
    }


def _nearest_root_matches(matches: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    if not matches:
        return []
    min_depth = min(int(match.get("depth") or 0) for match in matches)
    return [match for match in matches if int(match.get("depth") or 0) == min_depth]


def _covered_overlay_lemmas(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        str(row.get("lemma") or "")
        for row in _mapping_rows(payload.get("rows"))
        if _safe_float(row.get("membership"), default=0.0) >= 1.0 and str(row.get("lemma") or "")
    }


def _dedupe_evidence_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    result: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("topic") or ""),
            str(_as_mapping(row.get("extra")).get("wikidata_qid") or ""),
        )
        result.setdefault(key, dict(row))
    return sorted(
        result.values(),
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


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Score | Source label | Wikidata item | Description | Path |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('reading', '')}` | {row.get('score', '')} | "
            f"`{row.get('source_label', '')}` | `{extra.get('wikidata_qid', '')}` "
            f"{_escape_md(str(extra.get('wikidata_label') or ''))} | "
            f"{_escape_md(str(extra.get('wikidata_description') or ''))} | "
            f"`{' -> '.join(_string_list(extra.get('wikidata_path'))[:8])}` |"
        )
    return lines


def _entity_label(entity: Mapping[str, object]) -> str:
    labels = _as_mapping(entity.get("labels"))
    return str(labels.get("ja") or labels.get("en") or entity.get("id") or "")


def _entity_description(entity: Mapping[str, object]) -> str:
    descriptions = _as_mapping(entity.get("descriptions"))
    return str(descriptions.get("ja") or descriptions.get("en") or "")


def _chunks(values: Sequence[str], size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _repo_path(path: Path) -> str:
    resolved = path.expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
