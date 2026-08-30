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
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    DEFAULT_CANDIDATES_CSV,
    DEFAULT_POLICY_JSON,
    USER_AGENT,
    WIKIDATA_SPARQL_ENDPOINT,
    _as_mapping,
    _candidates_by_lemma,
    _evidence_row,
    _format_counter,
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
DEFAULT_CACHE_JSON = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_list_cache_en_ja.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_list_extractor_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_list_extractor_en_ja_latest.md"
)

LANGUAGE_PAIR = "en-ja"
SOURCE_ID = "wikidata_exact_label_list"
NOISY_DESCRIPTION_FRAGMENTS = (
    "album",
    "anime television series",
    "family name",
    "fictional character",
    "film",
    "given name",
    "japanese manga series",
    "light novel",
    "manga series",
    "novel",
    "racehorse",
    "single",
    "song",
    "surname",
    "television drama",
    "television series",
    "thoroughbred",
    "wikimedia disambiguation page",
)
ANIMAL_FALSE_FRIEND_FRAGMENTS = (
    "child",
    "human",
    "person",
    "school student",
    "student",
    "woman",
)
PLANT_TITLE_OR_CULTIVAR_FRAGMENTS = (
    "cultivar",
    "rose cultivar",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract candidate topic evidence by querying narrow Wikidata roots "
            "against exact Japanese SRS candidate labels. This is evidence-only "
            "and does not mutate runtime topic overlays."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument("--existing-overlay-json", type=Path, default=DEFAULT_EXISTING_OVERLAY_JSON)
    parser.add_argument("--cache-json", type=Path, default=DEFAULT_CACHE_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=73752)
    parser.add_argument("--collection", action="append", default=[])
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument(
        "--query-mode",
        choices=("root_enumeration", "candidate_values"),
        default="root_enumeration",
    )
    parser.add_argument("--max-root-rows", type=int, default=20000)
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--retry-after-seconds", type=float, default=15.0)
    parser.add_argument("--include-aliases", action="store_true")
    parser.add_argument("--offline-only", action="store_true")
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=240)
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
        collection_ids=tuple(str(item) for item in args.collection),
        batch_size=max(1, int(args.batch_size)),
        query_mode=str(args.query_mode),
        max_root_rows=max(1, int(args.max_root_rows)),
        sleep_seconds=max(0.0, float(args.sleep_seconds)),
        timeout_seconds=max(1, int(args.timeout_seconds)),
        retry_after_seconds=max(0.0, float(args.retry_after_seconds)),
        include_aliases=bool(args.include_aliases),
        offline_only=bool(args.offline_only),
        sample_per_cell=max(0, int(args.sample_per_cell)),
        max_sample_rows=max(0, int(args.max_sample_rows)),
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
    collection_ids: Sequence[str] = (),
    batch_size: int = 250,
    query_mode: str = "root_enumeration",
    max_root_rows: int = 20000,
    sleep_seconds: float = 0.6,
    timeout_seconds: int = 45,
    retry_after_seconds: float = 15.0,
    include_aliases: bool = False,
    offline_only: bool = False,
    sample_per_cell: int = 4,
    max_sample_rows: int = 240,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    policy = _load_json(policy_json) if policy_json.exists() else {}
    candidates = _load_candidates(candidates_csv, top_n=top_n)
    collections = _wikidata_list_collections(policy, collection_ids=collection_ids)
    overlay_keys = _overlay_keys(existing_overlay_json)
    cache = WikidataListCache.load(cache_json)
    client = WikidataListClient(
        cache=cache,
        sleep_seconds=sleep_seconds,
        timeout_seconds=timeout_seconds,
        retry_after_seconds=retry_after_seconds,
        offline_only=offline_only,
    )
    findings: list[dict[str, object]] = []
    if not collections:
        findings.append(
            _finding(
                "FAIL",
                "wikidata_list_collections_missing",
                "No Wikidata exact-label list collections are configured.",
            )
        )
    eligible_candidates = _eligible_label_candidates(candidates)
    evidence_rows: list[dict[str, object]] = []
    reading_identity_stats: Counter[str] = Counter()
    filter_stats: Counter[str] = Counter()
    if collections and eligible_candidates:
        bindings = client.query_all(
            candidates=eligible_candidates,
            collections=collections,
            batch_size=batch_size,
            include_aliases=include_aliases,
            query_mode=query_mode,
            max_root_rows=max_root_rows,
        )
        evidence_rows = _evidence_rows_from_sparql_bindings(
            bindings,
            candidates=eligible_candidates,
            collections=collections,
            policy=policy,
            overlay_keys=overlay_keys,
            reading_identity_stats=reading_identity_stats,
            filter_stats=filter_stats,
        )
    if not offline_only:
        cache.write(cache_json)
    source_summary = _source_summary(evidence_rows)
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
                "wikidata_list_evidence_generated",
                (
                    f"Generated {len(evidence_rows)} exact-label list rows. "
                    f"Reading identity gate: {_format_counter(reading_identity_stats)}."
                ),
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "wikidata_list_evidence_empty",
                "No exact-label Wikidata list rows matched the selected candidate universe.",
            )
        )
    client_summary = client.summary()
    if int(client_summary.get("http_429_count") or 0):
        findings.append(
            _finding(
                "WARN",
                "wikidata_list_rate_limited",
                f"Wikidata returned HTTP 429 {client_summary.get('http_429_count')} time(s).",
            )
        )
    if int(client_summary.get("sparql_failed_query_count") or 0):
        findings.append(
            _finding(
                "WARN",
                "wikidata_list_partial_due_to_endpoint_errors",
                f"{client_summary.get('sparql_failed_query_count')} SPARQL batch query/queries failed after retries.",
            )
        )
    status = (
        "ok"
        if evidence_rows and not any(row["level"] in {"FAIL", "WARN"} for row in findings)
        else "review"
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "wikidata_exact_label_list_has_topic_evidence"
            if evidence_rows
            else "wikidata_exact_label_list_needs_more_roots_or_sampling"
        ),
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "policy_json": _repo_path(policy_json),
            "existing_overlay_json": _repo_path(existing_overlay_json),
            "cache_json": _repo_path(cache_json),
            "top_n": top_n,
            "collection_ids": list(collection_ids),
            "batch_size": batch_size,
            "query_mode": query_mode,
            "max_root_rows": max_root_rows,
            "include_aliases": include_aliases,
            "offline_only": offline_only,
        },
        "method": {
            "source": SOURCE_ID,
            "query_shape": _query_shape_description(query_mode),
            "promotion_state": "evidence_only_not_product_overlay",
            "identity_gate": (
                "exact Japanese label plus existing single-reading verification; "
                "ambiguous multi-reading surfaces are rejected unless the surface itself "
                "is kana-exact"
            ),
        },
        "candidate_summary": {
            "loaded_count": len(candidates),
            "eligible_label_count": len(eligible_candidates),
            "collection_count": len(collections),
            "covered_overlay_key_count": len(overlay_keys),
        },
        "wikidata_summary": client_summary,
        "filter_summary": dict(sorted(filter_stats.items())),
        "source_summary": source_summary,
        "topic_summary": _topic_summary(evidence_rows),
        "collection_summary": _collection_summary(evidence_rows),
        "evidence_rows": evidence_rows,
        "review_sample": review_sample,
        "findings": findings,
        "limitations": [
            "This is exact-label list evidence only; it is not a complete Wikidata topic inventory.",
            "Japanese aliases are disabled by default because aliases tend to reintroduce broad-sense noise.",
            "Rows generated here are mining evidence only; promotion should follow sample review and source-specific guards.",
        ],
    }


def _query_shape_description(query_mode: str) -> str:
    if query_mode == "root_enumeration":
        return (
            "configured Wikidata roots are enumerated for Japanese labels, then exact-matched "
            "locally against corrected SRS candidate labels"
        )
    return (
        "candidate Japanese labels are sent as SPARQL VALUES, then matched only when a "
        "Wikidata item with that exact Japanese label is an instance or subclass of a "
        "configured narrow topic root"
    )


def render_markdown(report: Mapping[str, object]) -> str:
    candidate_summary = _as_mapping(report.get("candidate_summary"))
    wikidata_summary = _as_mapping(report.get("wikidata_summary"))
    lines = [
        "# en-ja SRS Topic Autotag Wikidata Exact-Label Lists",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Eligible labels: `{candidate_summary.get('eligible_label_count', 0)}`",
        f"- Collections: `{candidate_summary.get('collection_count', 0)}`",
        f"- Evidence rows: `{len(_mapping_rows(report.get('evidence_rows')))} `",
        f"- SPARQL requests: `{wikidata_summary.get('sparql_request_count', 0)}`",
        f"- SPARQL cache hits: `{wikidata_summary.get('sparql_cache_hit', 0)}`",
        "",
        "## Topics",
        "",
        "| Topic | Rows | Lemmas | New vs current overlay |",
        "| --- | ---: | ---: | ---: |",
    ]
    for topic, row in _as_mapping(report.get("topic_summary")).items():
        topic_row = _as_mapping(row)
        lines.append(
            f"| `{topic}` | {topic_row.get('row_count', 0)} | "
            f"{topic_row.get('lemma_count', 0)} | {topic_row.get('new_overlay_key_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Collections",
            "",
            "| Collection | Topic | Rows | Lemmas | New vs current overlay |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for collection_id, row in _as_mapping(report.get("collection_summary")).items():
        collection_row = _as_mapping(row)
        lines.append(
            f"| `{collection_id}` | `{collection_row.get('topic', '')}` | "
            f"{collection_row.get('row_count', 0)} | {collection_row.get('lemma_count', 0)} | "
            f"{collection_row.get('new_overlay_key_count', 0)} |"
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


def _eligible_label_candidates(
    candidates: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    by_lemma = _candidates_by_lemma(candidates)
    result: list[Mapping[str, object]] = []
    for lemma, rows in sorted(by_lemma.items()):
        normal_rows = [
            row
            for row in rows
            if str(row.get("candidate_state") or "") == "normal_vocab"
            and str(row.get("topic_stretch_allowed") or "").lower() != "false"
        ]
        if normal_rows:
            result.extend(normal_rows)
    return result


def _evidence_rows_from_sparql_bindings(
    bindings: Sequence[Mapping[str, object]],
    *,
    candidates: Sequence[Mapping[str, object]],
    collections: Mapping[str, Mapping[str, object]],
    policy: Mapping[str, object],
    overlay_keys: set[tuple[str, str]],
    reading_identity_stats: Counter[str] | None = None,
    filter_stats: Counter[str] | None = None,
) -> list[dict[str, object]]:
    posture = _source_posture(policy, "wikidata_online")
    candidates_by_lemma = _candidates_by_lemma(candidates)
    evidence: list[dict[str, object]] = []
    for binding in bindings:
        label = _binding_value(binding, "label")
        collection_id = _binding_value(binding, "collection")
        collection = collections.get(collection_id)
        if not label or not collection:
            continue
        target_family = str(collection.get("target_family") or "")
        if not target_family:
            continue
        verified_candidates = _verified_external_candidates(
            label,
            candidates_by_lemma.get(label, ()),
            source_readings=[],
            stats=reading_identity_stats,
        )
        if not verified_candidates:
            continue
        root_qid = _binding_qid(binding, "root")
        item_qid = _binding_qid(binding, "item")
        root_label = _binding_value(binding, "rootLabel")
        item_label = _binding_value(binding, "itemLabel")
        description = _binding_value(binding, "description")
        if _is_noisy_list_item(
            label=label,
            target_family=target_family,
            item_label=item_label,
            description=description,
        ):
            if filter_stats is not None:
                filter_stats["rejected_noisy_named_entity_or_title_collision"] += 1
            continue
        match_kind = _binding_value(binding, "matchKind") or "label"
        source_label = str(
            collection.get("source_label") or collection.get("display_name") or collection_id
        )
        for candidate, reading_identity in verified_candidates:
            overlay_key = (str(candidate.get("lemma") or ""), target_family)
            evidence.append(
                _evidence_row(
                    candidate=candidate,
                    source=SOURCE_ID,
                    topic=target_family,
                    membership=_safe_float(
                        collection.get("membership"),
                        default=_safe_float(posture.get("default_membership"), default=0.72),
                    ),
                    confidence=_safe_float(
                        collection.get("confidence"),
                        default=_safe_float(posture.get("default_confidence"), default=0.7),
                    ),
                    source_label=source_label,
                    evidence_label=(
                        f"Wikidata exact {match_kind}: {label} under "
                        f"{root_label or root_qid or source_label}"
                    ),
                    sense={"match_mode": reading_identity},
                    review_posture=str(
                        posture.get("review_posture") or "cc0_exact_label_candidate_generation"
                    ),
                    license_note=str(
                        posture.get("license_note")
                        or "Wikidata structured data is CC0; extracted labels are build-time evidence."
                    ),
                    extra={
                        "wikidata_collection_id": collection_id,
                        "wikidata_collection_display_name": str(
                            collection.get("display_name") or ""
                        ),
                        "wikidata_item_qid": item_qid,
                        "wikidata_item_label_en": item_label,
                        "wikidata_description_en": description,
                        "wikidata_root_qid": root_qid,
                        "wikidata_root_label_en": root_label,
                        "wikidata_match_label": label,
                        "wikidata_match_kind": match_kind,
                        "reading_identity": reading_identity,
                        "already_in_current_overlay": overlay_key in overlay_keys,
                    },
                )
            )
    return _dedupe_evidence_rows(evidence)


class WikidataListClient:
    def __init__(
        self,
        *,
        cache: "WikidataListCache",
        sleep_seconds: float,
        timeout_seconds: int,
        retry_after_seconds: float,
        offline_only: bool,
    ) -> None:
        self.cache = cache
        self.sleep_seconds = sleep_seconds
        self.timeout_seconds = timeout_seconds
        self.retry_after_seconds = retry_after_seconds
        self.offline_only = offline_only
        self.counters: Counter[str] = Counter()

    def query_all(
        self,
        *,
        candidates: Sequence[Mapping[str, object]],
        collections: Mapping[str, Mapping[str, object]],
        batch_size: int,
        include_aliases: bool,
        query_mode: str,
        max_root_rows: int,
    ) -> list[Mapping[str, object]]:
        if query_mode == "root_enumeration":
            return self.query_roots(
                collections=collections,
                include_aliases=include_aliases,
                max_root_rows=max_root_rows,
            )
        labels = sorted(
            {str(row.get("lemma") or "") for row in candidates if str(row.get("lemma") or "")}
        )
        all_rows: list[Mapping[str, object]] = []
        collection_values_by_relation = _collection_values_by_relation(collections)
        for relation, collection_values in sorted(collection_values_by_relation.items()):
            if not collection_values:
                continue
            for batch in _chunks(labels, batch_size):
                query = _sparql_query(
                    batch,
                    collection_values,
                    include_aliases=include_aliases,
                    relation=relation,
                )
                all_rows.extend(self.query(query))
        return all_rows

    def query_roots(
        self,
        *,
        collections: Mapping[str, Mapping[str, object]],
        include_aliases: bool,
        max_root_rows: int,
    ) -> list[Mapping[str, object]]:
        all_rows: list[Mapping[str, object]] = []
        for collection_id, collection in sorted(collections.items()):
            query = _sparql_root_query(
                collection_id,
                collection,
                include_aliases=include_aliases,
                max_root_rows=max_root_rows,
            )
            all_rows.extend(self.query(query))
        return all_rows

    def query(self, query: str) -> list[Mapping[str, object]]:
        key = hashlib.sha1(query.encode("utf-8")).hexdigest()
        cached = self.cache.queries.get(key)
        if cached is not None:
            self.counters["sparql_cache_hit"] += 1
            return _mapping_rows(cached)
        if self.offline_only:
            self.counters["sparql_offline_miss"] += 1
            return []
        data = urlencode({"query": query, "format": "json"}).encode("utf-8")
        request = Request(
            WIKIDATA_SPARQL_ENDPOINT,
            data=data,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - public endpoint
                    payload = _as_mapping(json.loads(response.read().decode("utf-8")))
                rows = [
                    dict(row)
                    for row in _mapping_rows(_as_mapping(payload.get("results")).get("bindings"))
                ]
                self.cache.queries[key] = rows
                self.counters["sparql_request_count"] += 1
                self._sleep()
                return rows
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504}:
                    raise
                self.counters[f"http_{exc.code}_count"] += 1
                if attempt == 2:
                    self.counters["sparql_failed_query_count"] += 1
                    return []
                retry_after = _safe_float(
                    exc.headers.get("Retry-After"), default=self.retry_after_seconds
                )
                time.sleep(max(self.retry_after_seconds, retry_after))
            except (TimeoutError, URLError):
                self.counters["sparql_transport_error_count"] += 1
                if attempt == 2:
                    self.counters["sparql_failed_query_count"] += 1
                    return []
                time.sleep(self.retry_after_seconds)
        return []

    def summary(self) -> dict[str, object]:
        return {
            **dict(sorted(self.counters.items())),
            "sparql_cache_size": len(self.cache.queries),
        }

    def _sleep(self) -> None:
        if self.sleep_seconds:
            time.sleep(self.sleep_seconds)


class WikidataListCache:
    def __init__(self, *, queries: dict[str, object] | None = None) -> None:
        self.queries = queries or {}

    @classmethod
    def load(cls, path: Path) -> "WikidataListCache":
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(queries=dict(_as_mapping(payload).get("queries") or {}))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"schema_version": 1, "queries": self.queries},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def _sparql_query(
    labels: Sequence[str],
    collection_values: Sequence[Mapping[str, str]],
    *,
    include_aliases: bool,
    relation: str = "instance_or_subclass",
) -> str:
    label_values = " ".join(_sparql_ja_literal(label) for label in labels)
    collection_rows = "\n    ".join(
        f"({_sparql_string(row['collection_id'])} wd:{row['qid']})" for row in collection_values
    )
    label_clause = '?item rdfs:label ?label . BIND("label" AS ?matchKind)'
    if include_aliases:
        label_clause = (
            '{ ?item rdfs:label ?label . BIND("label" AS ?matchKind) } '
            'UNION { ?item skos:altLabel ?label . BIND("alias" AS ?matchKind) }'
        )
    relation_clause = _relation_clause(relation)
    return f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX schema: <http://schema.org/>
SELECT DISTINCT ?label ?item ?itemLabel ?collection ?root ?rootLabel ?description ?matchKind WHERE {{
  VALUES ?label {{ {label_values} }}
  VALUES (?collection ?root) {{
    {collection_rows}
  }}
  {label_clause}
  {relation_clause}
  OPTIONAL {{ ?item rdfs:label ?itemLabel FILTER(LANG(?itemLabel) = "en") }}
  OPTIONAL {{ ?root rdfs:label ?rootLabel FILTER(LANG(?rootLabel) = "en") }}
  OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
}}
""".strip()


def _sparql_root_query(
    collection_id: str,
    collection: Mapping[str, object],
    *,
    include_aliases: bool,
    max_root_rows: int,
) -> str:
    root_values = " ".join(
        f"wd:{qid}" for qid in _string_list(collection.get("qids")) if qid.startswith("Q")
    )
    label_clause = (
        '?item rdfs:label ?label . FILTER(LANG(?label) = "ja") BIND("label" AS ?matchKind)'
    )
    if include_aliases:
        label_clause = (
            '{ ?item rdfs:label ?label . FILTER(LANG(?label) = "ja") BIND("label" AS ?matchKind) } '
            'UNION { ?item skos:altLabel ?label . FILTER(LANG(?label) = "ja") BIND("alias" AS ?matchKind) }'
        )
    relation_clause = _relation_clause(str(collection.get("relation") or "instance_or_subclass"))
    return f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX schema: <http://schema.org/>
SELECT DISTINCT ?label ?item ?itemLabel ?collection ?root ?rootLabel ?description ?matchKind WHERE {{
  VALUES ?root {{ {root_values} }}
  BIND({_sparql_string(collection_id)} AS ?collection)
  {label_clause}
  {relation_clause}
  OPTIONAL {{ ?item rdfs:label ?itemLabel FILTER(LANG(?itemLabel) = "en") }}
  OPTIONAL {{ ?root rdfs:label ?rootLabel FILTER(LANG(?rootLabel) = "en") }}
  OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
}}
LIMIT {max_root_rows}
""".strip()


def _relation_clause(relation: str) -> str:
    if relation == "subclass_only":
        return "?item wdt:P279* ?root ."
    if relation == "instance_only":
        return "?item wdt:P31/wdt:P279* ?root ."
    return """
  {
    ?item wdt:P31/wdt:P279* ?root .
  } UNION {
    ?item wdt:P279* ?root .
  }
""".rstrip()


def _collection_values_by_relation(
    collections: Mapping[str, Mapping[str, object]],
) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for collection_id, collection in sorted(collections.items()):
        relation = str(collection.get("relation") or "instance_or_subclass")
        for qid in _string_list(collection.get("qids")):
            if not qid.startswith("Q"):
                continue
            key = (collection_id, qid)
            if key in seen:
                continue
            seen.add(key)
            result[relation].append({"collection_id": collection_id, "qid": qid})
    return result


def _is_noisy_list_item(
    *,
    label: str,
    target_family: str,
    item_label: str,
    description: str,
) -> bool:
    haystack = " ".join([label, item_label, description]).lower()
    if any(fragment in haystack for fragment in NOISY_DESCRIPTION_FRAGMENTS):
        return True
    if target_family == "animals" and any(
        fragment in haystack for fragment in ANIMAL_FALSE_FRIEND_FRAGMENTS
    ):
        return True
    if target_family == "plants_nature" and any(
        fragment in haystack for fragment in PLANT_TITLE_OR_CULTIVAR_FRAGMENTS
    ):
        return True
    return False


def _wikidata_list_collections(
    policy: Mapping[str, object],
    *,
    collection_ids: Sequence[str],
) -> dict[str, Mapping[str, object]]:
    wanted = {str(collection_id) for collection_id in collection_ids if str(collection_id)}
    result: dict[str, Mapping[str, object]] = {}
    for row in _mapping_rows(policy.get("wikidata_exact_label_list_collections")):
        collection_id = str(row.get("id") or "").strip()
        if not collection_id or (wanted and collection_id not in wanted):
            continue
        if not str(row.get("target_family") or "") or not _string_list(row.get("qids")):
            continue
        result[collection_id] = row
    return result


def _topic_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("topic") or "")].append(row)
    return {
        topic: {
            "row_count": len(topic_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in topic_rows}),
            "new_overlay_key_count": sum(
                1
                for row in topic_rows
                if not bool(_as_mapping(row.get("extra")).get("already_in_current_overlay"))
            ),
        }
        for topic, topic_rows in sorted(grouped.items())
    }


def _collection_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        collection_id = str(_as_mapping(row.get("extra")).get("wikidata_collection_id") or "")
        grouped[collection_id].append(row)
    return {
        collection_id: {
            "topic": str(collection_rows[0].get("topic") or "") if collection_rows else "",
            "row_count": len(collection_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in collection_rows}),
            "new_overlay_key_count": sum(
                1
                for row in collection_rows
                if not bool(_as_mapping(row.get("extra")).get("already_in_current_overlay"))
            ),
        }
        for collection_id, collection_rows in sorted(grouped.items())
    }


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Score | Collection | Wikidata item | Root | New? |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        is_new = not bool(extra.get("already_in_current_overlay"))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('reading', '')}` | {row.get('score', '')} | "
            f"`{extra.get('wikidata_collection_id', '')}` | "
            f"`{extra.get('wikidata_item_qid', '')}` {_escape_md(str(extra.get('wikidata_item_label_en') or ''))} | "
            f"`{extra.get('wikidata_root_qid', '')}` {_escape_md(str(extra.get('wikidata_root_label_en') or ''))} | "
            f"{'yes' if is_new else 'no'} |"
        )
    return lines


def _dedupe_evidence_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    result: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("topic") or ""),
            str(extra.get("wikidata_collection_id") or ""),
            str(extra.get("wikidata_item_qid") or ""),
        )
        result.setdefault(key, dict(row))
    return sorted(
        result.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            str(_as_mapping(row.get("extra")).get("wikidata_collection_id") or ""),
            _safe_float(row.get("score")),
            str(row.get("lemma") or ""),
        ),
    )


def _overlay_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        (str(row.get("lemma") or ""), str(row.get("topic") or ""))
        for row in _mapping_rows(payload.get("rows"))
        if str(row.get("lemma") or "") and str(row.get("topic") or "")
    }


def _binding_value(binding: Mapping[str, object], key: str) -> str:
    return str(_as_mapping(binding.get(key)).get("value") or "")


def _binding_qid(binding: Mapping[str, object], key: str) -> str:
    value = _binding_value(binding, key)
    if value.startswith("http://www.wikidata.org/entity/"):
        return value.rsplit("/", 1)[-1]
    return value


def _sparql_ja_literal(value: str) -> str:
    return f"{json.dumps(value, ensure_ascii=False)}@ja"


def _sparql_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _chunks(items: Sequence[str], size: int) -> list[list[str]]:
    return [list(items[index : index + size]) for index in range(0, len(items), size)]


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
