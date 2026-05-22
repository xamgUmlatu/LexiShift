#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_ZIPF_BRIDGE = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_spalex_10k_full_rulegen_latest.json"
)
DEFAULT_EXISTING_OVERLAYS = (
    TEST_OUTPUTS_ROOT / "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_source_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_wikidata_plants_topic_candidates_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_wikidata_plants_topic_candidates_en_es_latest.md"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "LexiShiftTopicProbe/0.1 (local development; bounded candidate audit)"
LANGUAGE_PAIR = "en-es"
TOPIC = "plants_nature"

ROOTS = {
    "plant": "Q756",
    "tree": "Q10884",
    "flower": "Q506",
    "fruit": "Q3314483",
    "vegetable": "Q11004",
    "herb": "Q207123",
    "grass": "Q643352",
    "shrub": "Q106010",
}
LIGHT_ROOTS = {"fruit", "vegetable"}
ACCEPTED_EXISTING_CONFIDENCE = {"strong"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Query Wikidata for Spanish plant/nature labels that intersect the local en-es "
            "10k learner universe. This is a bounded source candidate audit, not a broad dump."
        )
    )
    parser.add_argument("--zipf-bridge-json", type=Path, default=DEFAULT_ZIPF_BRIDGE)
    parser.add_argument(
        "--existing-overlay-json",
        action="append",
        type=Path,
        default=[],
        help="Existing overlay JSON to avoid counting already-covered strong lemmas.",
    )
    parser.add_argument(
        "--fixture-json",
        type=Path,
        help="Offline Wikidata-style fixture for tests or no-network development.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--chunk-size", type=int, default=200)
    parser.add_argument("--max-labels", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    existing_paths = args.existing_overlay_json or list(DEFAULT_EXISTING_OVERLAYS)
    local_lemmas = _local_target_lemmas(_load_json(args.zipf_bridge_json))
    if args.max_labels:
        local_lemmas = local_lemmas[: max(1, int(args.max_labels))]
    wikidata_rows = (
        _fixture_rows(_load_json(args.fixture_json))
        if args.fixture_json
        else fetch_wikidata_rows(
            local_lemmas,
            chunk_size=max(1, int(args.chunk_size)),
            sleep_seconds=max(0.0, float(args.sleep_seconds)),
            timeout_seconds=max(1, int(args.timeout_seconds)),
        )
    )
    report = build_report(
        local_lemmas=local_lemmas,
        wikidata_rows=wikidata_rows,
        existing_overlay_payloads=[
            payload
            for payload in (_load_json_if_exists(path) for path in existing_paths)
            if payload
        ],
        zipf_bridge_path=args.zipf_bridge_json,
        existing_overlay_paths=existing_paths,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def fetch_wikidata_rows(
    labels: Sequence[str],
    *,
    chunk_size: int = 200,
    sleep_seconds: float = 0.15,
    timeout_seconds: int = 30,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for chunk in _chunks([label for label in labels if _queryable_label(label)], chunk_size):
        rows.extend(_query_wikidata_chunk(chunk, timeout_seconds=timeout_seconds))
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return rows


def build_report(
    *,
    local_lemmas: Sequence[str],
    wikidata_rows: Sequence[Mapping[str, object]],
    existing_overlay_payloads: Sequence[Mapping[str, object]],
    zipf_bridge_path: Path | None = None,
    existing_overlay_paths: Sequence[Path] = (),
    generated_at: str | None = None,
) -> dict[str, object]:
    local_set = set(local_lemmas)
    existing_strong = _existing_topic_lemmas(existing_overlay_payloads, strong_only=True)
    existing_any = _existing_topic_lemmas(existing_overlay_payloads, strong_only=False)
    by_lemma: dict[str, dict[str, object]] = {}
    skipped_nonlocal: set[str] = set()
    for raw_row in wikidata_rows:
        lemma = str(raw_row.get("lemma") or "").strip()
        root = str(raw_row.get("root") or "").strip()
        qid = str(raw_row.get("qid") or "").strip()
        if not lemma or lemma not in local_set:
            if lemma:
                skipped_nonlocal.add(lemma)
            continue
        if root not in ROOTS:
            continue
        candidate = by_lemma.setdefault(
            lemma,
            {
                "language_pair": LANGUAGE_PAIR,
                "lemma": lemma,
                "topic": TOPIC,
                "membership": 1.0,
                "confidence_label": "strong",
                "source_channel": "wikidata_structured_data",
                "source_label": "wikidata_cc0_label_intersection",
                "review_state": "source_candidate_pending_review",
                "wikidata_qids": [],
                "wikidata_roots": [],
                "provenance": {
                    "license": "Wikidata structured data CC0",
                    "source_policy": "bounded local-lemma intersection; no article text scraped",
                },
            },
        )
        roots = candidate["wikidata_roots"]
        qids = candidate["wikidata_qids"]
        if isinstance(roots, list) and root not in roots:
            roots.append(root)
        if isinstance(qids, list) and qid and qid not in qids:
            qids.append(qid)
        if root in LIGHT_ROOTS and candidate.get("confidence_label") != "strong_direct_plant":
            candidate["membership"] = min(float(candidate["membership"]), 0.65)
            candidate["confidence_label"] = "light"
        elif root not in LIGHT_ROOTS:
            candidate["membership"] = 1.0
            candidate["confidence_label"] = "strong_direct_plant"

    candidates = sorted(by_lemma.values(), key=lambda row: str(row["lemma"]))
    new_candidates = [row for row in candidates if str(row["lemma"]) not in existing_strong]
    new_strong = [
        row for row in new_candidates if str(row.get("confidence_label")) == "strong_direct_plant"
    ]
    counts_by_confidence = Counter(str(row["confidence_label"]) for row in candidates)
    new_counts_by_confidence = Counter(str(row["confidence_label"]) for row in new_candidates)
    status = "ok" if candidates else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_wikidata_plants_topic_candidates_ready"
            if status == "ok"
            else "srs_wikidata_plants_topic_candidates_need_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "topic": TOPIC,
        "inputs": {
            "zipf_bridge_json": _repo_path(zipf_bridge_path),
            "existing_overlay_json": [_repo_path(path) for path in existing_overlay_paths],
            "source": "Wikidata SPARQL label intersection",
        },
        "source_policy": {
            "license": "Wikidata structured data is CC0",
            "download_scope": "bounded SPARQL queries over local learner lemmas only",
            "text_scraping": "none",
            "promotion_policy": "candidate packet only; runtime overlay promotion requires review",
        },
        "summary": {
            "local_lemma_count": len(local_lemmas),
            "wikidata_match_count": len(candidates),
            "new_candidate_count": len(new_candidates),
            "new_strong_candidate_count": len(new_strong),
            "already_covered_strong_count": len(candidates) - len(new_candidates),
            "already_covered_any_count": sum(
                1 for row in candidates if str(row["lemma"]) in existing_any
            ),
            "skipped_nonlocal_label_count": len(skipped_nonlocal),
            "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
            "new_counts_by_confidence": dict(sorted(new_counts_by_confidence.items())),
        },
        "new_candidates": new_candidates,
        "all_candidates": candidates,
        "limitations": [
            "This proves source availability and local-lemma intersection, not final topic precision.",
            "Fruit/vegetable roots are marked light because they overlap Food & Cooking.",
            "Labels can be ambiguous; promote only reviewed candidates into runtime overlays.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Wikidata Plants/Nature Candidate Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Local lemmas checked: `{summary.get('local_lemma_count', 0)}`",
        f"- Wikidata matches: `{summary.get('wikidata_match_count', 0)}`",
        f"- New candidates: `{summary.get('new_candidate_count', 0)}`",
        f"- New strong candidates: `{summary.get('new_strong_candidate_count', 0)}`",
        "",
        "## New Candidate Counts",
        "",
        "| Confidence | Count |",
        "| --- | ---: |",
    ]
    for label, count in _as_mapping(summary.get("new_counts_by_confidence")).items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(["", "## New Candidate Sample", "", "| Lemma | Confidence | Roots | QIDs |"])
    lines.append("| --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("new_candidates"))[:80]:
        roots = ", ".join(str(item) for item in row.get("wikidata_roots", []))
        qids = ", ".join(str(item) for item in row.get("wikidata_qids", [])[:4])
        lines.append(
            f"| `{row.get('lemma', '')}` | `{row.get('confidence_label', '')}` | {roots} | {qids} |"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def _query_wikidata_chunk(
    labels: Sequence[str], *, timeout_seconds: int
) -> list[dict[str, object]]:
    values = " ".join(f'"{_sparql_string(label)}"@es' for label in labels)
    root_values = " ".join(f"wd:{qid}" for qid in ROOTS.values())
    query = f"""
SELECT ?lemma ?item ?root WHERE {{
  VALUES ?root {{ {root_values} }}
  VALUES ?lemma {{ {values} }}
  ?item rdfs:label ?lemma .
  ?item (wdt:P31|wdt:P279)/(wdt:P279*) ?root .
}}
"""
    url = SPARQL_ENDPOINT + "?" + urlencode({"query": query, "format": "json"})
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.load(response)
    rows: list[dict[str, object]] = []
    qid_to_root = {qid: root for root, qid in ROOTS.items()}
    for binding in _mapping_rows(_as_mapping(payload.get("results")).get("bindings")):
        root_qid = str(_as_mapping(binding.get("root")).get("value") or "").rsplit("/", 1)[-1]
        item_qid = str(_as_mapping(binding.get("item")).get("value") or "").rsplit("/", 1)[-1]
        rows.append(
            {
                "lemma": str(_as_mapping(binding.get("lemma")).get("value") or ""),
                "qid": item_qid,
                "root": qid_to_root.get(root_qid, root_qid),
            }
        )
    return rows


def _local_target_lemmas(payload: Mapping[str, object]) -> list[str]:
    lemmas = {
        str(row.get("target") or "").strip()
        for row in _mapping_rows(payload.get("full_source_target_pairs"))
        if str(row.get("target") or "").strip()
    }
    return sorted(lemmas)


def _existing_topic_lemmas(
    payloads: Sequence[Mapping[str, object]], *, strong_only: bool
) -> set[str]:
    lemmas: set[str] = set()
    for payload in payloads:
        if str(payload.get("status") or "") != "ok":
            continue
        for row in _mapping_rows(payload.get("rows")):
            if str(row.get("topic") or "") != TOPIC:
                continue
            if (
                strong_only
                and str(row.get("confidence_label") or "") not in ACCEPTED_EXISTING_CONFIDENCE
            ):
                continue
            lemma = str(row.get("lemma") or "").strip()
            if lemma:
                lemmas.add(lemma)
    return lemmas


def _fixture_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    return [dict(row) for row in _mapping_rows(payload.get("rows"))]


def _queryable_label(label: str) -> bool:
    stripped = label.strip()
    return bool(stripped) and len(stripped) <= 40 and "\n" not in stripped and "\t" not in stripped


def _chunks(values: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _sparql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    return _as_mapping(json.loads(path.expanduser().read_text(encoding="utf-8")))


def _load_json_if_exists(path: Path) -> Mapping[str, object] | None:
    return _load_json(path) if path.exists() else None


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
