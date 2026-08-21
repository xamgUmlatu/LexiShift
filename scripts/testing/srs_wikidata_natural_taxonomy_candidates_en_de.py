#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-de-default.sqlite"
DEFAULT_EXISTING_OVERLAYS = (
    TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_de_latest.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_candidates_en_de_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_candidates_en_de_latest.md"
)
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "LexiShiftTopicProbe/0.2 (local development; bounded natural-taxonomy audit)"
LANGUAGE_PAIR = "en-de"
SKOS_ALT_LABEL = "http://www.w3.org/2004/02/skos/core#altLabel"
ACCEPTED_EXISTING_CONFIDENCE = {"strong", "strong_direct_taxonomy", "strong_direct_plant"}

ROOTS_BY_TOPIC: Mapping[str, Mapping[str, str]] = {
    "animals": {
        "animal": "Q729",
        "mammal": "Q7377",
        "bird": "Q5113",
        "fish": "Q152",
        "reptile": "Q10811",
        "amphibian": "Q10908",
        "insect": "Q1390",
        "arachnid": "Q1358",
        "mollusk": "Q25326",
        "crustacean": "Q25364",
    },
    "plants_nature": {
        "plant": "Q756",
        "tree": "Q10884",
        "flower": "Q506",
        "fruit": "Q3314483",
        "vegetable": "Q11004",
        "herb": "Q207123",
        "grass": "Q643352",
        "shrub": "Q106010",
        "fungus": "Q764",
        "alga": "Q37868",
    },
}
LIGHT_ROOTS_BY_TOPIC: Mapping[str, set[str]] = {
    "animals": set(),
    "plants_nature": {"fruit", "vegetable"},
}
NOISY_ALIAS_ROOTS_BY_TOPIC: Mapping[str, set[str]] = {
    "animals": {"animal", "mammal"},
    "plants_nature": {"plant"},
}
EXCLUDED_LEMMAS_BY_TOPIC: Mapping[str, set[str]] = {
    "animals": {
        "bulle",
        "bär",
        "dame",
        "fink",
        "hahn",
        "jaguar",
        "klasse",
        "marder",
        "mutter",
        "star",
        "stier",
        "wagen",
        "wolf",
    },
    "plants_nature": {
        "art",
        "bank",
        "blatt",
        "boden",
        "dorn",
        "erde",
        "frucht",
        "krone",
        "rose",
        "weide",
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Query Wikidata for German natural-taxonomy labels/aliases that intersect the "
            "local en-de frequency corpus. This is a bounded source candidate audit, "
            "not a runtime dependency."
        )
    )
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--top-n", type=int, default=20000)
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
    parser.add_argument("--chunk-size", type=int, default=250)
    parser.add_argument("--max-labels", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    existing_paths = args.existing_overlay_json or list(DEFAULT_EXISTING_OVERLAYS)
    local_lemmas = _local_frequency_lemmas(args.frequency_db, top_n=max(1, int(args.top_n)))
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
        frequency_db=args.frequency_db,
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
    chunk_size: int = 250,
    sleep_seconds: float = 0.15,
    timeout_seconds: int = 30,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    queryable_labels = [label for label in labels if _queryable_label(label)]
    for chunk_index, chunk in enumerate(_chunks(queryable_labels, chunk_size), start=1):
        try:
            rows.extend(_query_wikidata_chunk(chunk, timeout_seconds=timeout_seconds))
        except (OSError, TimeoutError) as exc:
            rows.append(
                {
                    "_fetch_error": True,
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk),
                    "first_label": chunk[0] if chunk else "",
                    "last_label": chunk[-1] if chunk else "",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return rows


def build_report(
    *,
    local_lemmas: Sequence[str],
    wikidata_rows: Sequence[Mapping[str, object]],
    existing_overlay_payloads: Sequence[Mapping[str, object]],
    frequency_db: Path | None = None,
    existing_overlay_paths: Sequence[Path] = (),
    generated_at: str | None = None,
) -> dict[str, object]:
    local_set = set(local_lemmas)
    existing_strong = _existing_topic_lemmas(existing_overlay_payloads, strong_only=True)
    existing_any = _existing_topic_lemmas(existing_overlay_payloads, strong_only=False)
    by_topic_lemma: dict[tuple[str, str], dict[str, object]] = {}
    skipped_nonlocal: set[str] = set()
    skipped_unknown_root = 0
    fetch_errors = [dict(row) for row in wikidata_rows if bool(row.get("_fetch_error"))]
    for raw_row in wikidata_rows:
        if bool(raw_row.get("_fetch_error")):
            continue
        lemma = str(raw_row.get("lemma") or "").strip().lower()
        root = str(raw_row.get("root") or "").strip()
        qid = str(raw_row.get("qid") or "").strip()
        match_kind = str(raw_row.get("match_kind") or "label").strip() or "label"
        topic = _topic_for_root(root)
        if not lemma or lemma not in local_set:
            if lemma:
                skipped_nonlocal.add(lemma)
            continue
        if not topic:
            skipped_unknown_root += 1
            continue
        if _is_excluded_lemma(topic=topic, lemma=lemma):
            continue
        if _is_noisy_alias_root(topic=topic, root=root, match_kind=match_kind):
            continue
        candidate = by_topic_lemma.setdefault(
            (topic, lemma),
            {
                "language_pair": LANGUAGE_PAIR,
                "lemma": lemma,
                "topic": topic,
                "membership": 1.0,
                "confidence_label": "strong_direct_taxonomy",
                "source_channel": "wikidata_structured_data",
                "source_label": "wikidata_cc0_label_alias_intersection",
                "review_state": "source_candidate_pending_review",
                "wikidata_qids": [],
                "wikidata_roots": [],
                "wikidata_match_kinds": [],
                "provenance": {
                    "license": "Wikidata structured data CC0",
                    "source_policy": (
                        "bounded local-lemma intersection; labels/aliases only; "
                        "no article text scraped; build-time only"
                    ),
                },
            },
        )
        _append_unique(candidate["wikidata_roots"], root)
        if qid:
            _append_unique(candidate["wikidata_qids"], qid)
        _append_unique(candidate["wikidata_match_kinds"], match_kind)
        _refresh_candidate_confidence(candidate, topic=topic)

    candidates = sorted(
        by_topic_lemma.values(),
        key=lambda row: (str(row["topic"]), str(row["lemma"])),
    )
    new_candidates = [
        row for row in candidates if (str(row["topic"]), str(row["lemma"])) not in existing_strong
    ]
    new_strong = [
        row
        for row in new_candidates
        if str(row.get("confidence_label")) == "strong_direct_taxonomy"
    ]
    topics = sorted(ROOTS_BY_TOPIC)
    summary_by_topic = {
        topic: _topic_summary(
            topic=topic,
            candidates=candidates,
            new_candidates=new_candidates,
            existing_any=existing_any,
        )
        for topic in topics
    }
    status = "ok" if candidates and not fetch_errors else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_wikidata_natural_taxonomy_candidates_ready"
            if status == "ok"
            else "srs_wikidata_natural_taxonomy_candidates_need_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "topics": topics,
        "inputs": {
            "frequency_db": str(frequency_db) if frequency_db else "",
            "existing_overlay_json": [_repo_path(path) for path in existing_overlay_paths],
            "source": "Wikidata SPARQL German label/alias intersection",
        },
        "source_policy": {
            "license": "Wikidata structured data is CC0",
            "download_scope": "bounded SPARQL queries over local German frequency lemmas only",
            "text_scraping": "none",
            "runtime_dependency": "none",
            "promotion_policy": "candidate packet only; runtime overlay promotion requires review",
        },
        "summary": {
            "local_lemma_count": len(local_lemmas),
            "wikidata_match_count": len(candidates),
            "new_candidate_count": len(new_candidates),
            "new_strong_candidate_count": len(new_strong),
            "already_covered_strong_count": len(candidates) - len(new_candidates),
            "already_covered_any_count": sum(
                1 for row in candidates if (str(row["topic"]), str(row["lemma"])) in existing_any
            ),
            "skipped_nonlocal_label_count": len(skipped_nonlocal),
            "skipped_unknown_root_count": skipped_unknown_root,
            "fetch_error_count": len(fetch_errors),
            "by_topic": summary_by_topic,
        },
        "fetch_errors": fetch_errors[:40],
        "new_candidates": new_candidates,
        "all_candidates": candidates,
        "limitations": [
            "This proves source availability and local-lemma intersection, not final topic precision.",
            "Polysemic labels are retained as candidates unless they are known bad homographs.",
            "Fruit/vegetable roots may overlap Food & Cooking; they are still useful natural-taxonomy candidates.",
            "Promote reviewed candidates into packaged LexiShift data; do not require Wikidata at runtime.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Wikidata Natural Taxonomy Candidate Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Local lemmas checked: `{summary.get('local_lemma_count', 0)}`",
        f"- Wikidata matches: `{summary.get('wikidata_match_count', 0)}`",
        f"- New candidates: `{summary.get('new_candidate_count', 0)}`",
        f"- New strong candidates: `{summary.get('new_strong_candidate_count', 0)}`",
        f"- Fetch errors: `{summary.get('fetch_error_count', 0)}`",
        "",
        "## Topic Summary",
        "",
        "| Topic | Matches | New | New strong | Already covered | Confidence counts |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for topic, topic_summary in _as_mapping(summary.get("by_topic")).items():
        data = _as_mapping(topic_summary)
        counts = ", ".join(
            f"{key}: {value}"
            for key, value in _as_mapping(data.get("new_counts_by_confidence")).items()
        )
        lines.append(
            f"| `{topic}` | {data.get('wikidata_match_count', 0)} | "
            f"{data.get('new_candidate_count', 0)} | "
            f"{data.get('new_strong_candidate_count', 0)} | "
            f"{data.get('already_covered_strong_count', 0)} | {counts or '-'} |"
        )
    for topic in report.get("topics", []):
        topic_text = str(topic)
        lines.extend(
            [
                "",
                f"## {topic_text}",
                "",
                "| Lemma | Confidence | Roots | Match | QIDs |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        rows = [
            row
            for row in _mapping_rows(report.get("new_candidates"))
            if str(row.get("topic") or "") == topic_text
        ]
        if not rows:
            lines.append("| - | - | - | - | - |")
            continue
        for row in rows[:100]:
            roots = ", ".join(str(item) for item in row.get("wikidata_roots", []))
            kinds = ", ".join(str(item) for item in row.get("wikidata_match_kinds", []))
            qids = ", ".join(str(item) for item in row.get("wikidata_qids", [])[:4])
            lines.append(
                f"| `{row.get('lemma', '')}` | `{row.get('confidence_label', '')}` | "
                f"{roots} | {kinds} | {qids} |"
            )
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    fetch_errors = _mapping_rows(report.get("fetch_errors"))
    if fetch_errors:
        lines.extend(["", "## Fetch Errors", ""])
        for row in fetch_errors[:10]:
            lines.append(
                f"- chunk `{row.get('chunk_index', '')}` "
                f"({row.get('first_label', '')}..{row.get('last_label', '')}): "
                f"{row.get('error_type', '')}: {row.get('error', '')}"
            )
    return "\n".join(lines) + "\n"


def _query_wikidata_chunk(
    labels: Sequence[str], *, timeout_seconds: int
) -> list[dict[str, object]]:
    values = " ".join(json.dumps(label, ensure_ascii=False) for label in labels)
    root_values = " ".join(f"wd:{qid}" for qid in _all_root_qids())
    query = f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?wanted ?item ?root ?matchKind WHERE {{
  VALUES ?root {{ {root_values} }}
  VALUES ?wanted {{ {values} }}
  {{
    ?item rdfs:label ?labelNode .
    FILTER(LANG(?labelNode) = "de")
    BIND(LCASE(STR(?labelNode)) AS ?lemma)
    BIND("label" AS ?matchKind)
  }}
  UNION
  {{
    ?item <{SKOS_ALT_LABEL}> ?aliasNode .
    FILTER(LANG(?aliasNode) = "de")
    BIND(LCASE(STR(?aliasNode)) AS ?lemma)
    BIND("alias" AS ?matchKind)
  }}
  FILTER(?lemma = ?wanted)
  ?item (wdt:P31|wdt:P279)/(wdt:P279*) ?root .
}}
"""
    data = urlencode({"query": query, "format": "json"}).encode("utf-8")
    request = Request(
        SPARQL_ENDPOINT,
        data=data,
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.load(response)
    rows: list[dict[str, object]] = []
    qid_to_root = _qid_to_root()
    for binding in _mapping_rows(_as_mapping(payload.get("results")).get("bindings")):
        root_qid = str(_as_mapping(binding.get("root")).get("value") or "").rsplit("/", 1)[-1]
        item_qid = str(_as_mapping(binding.get("item")).get("value") or "").rsplit("/", 1)[-1]
        rows.append(
            {
                "lemma": str(_as_mapping(binding.get("wanted")).get("value") or ""),
                "qid": item_qid,
                "root": qid_to_root.get(root_qid, root_qid),
                "match_kind": str(_as_mapping(binding.get("matchKind")).get("value") or "label"),
            }
        )
    return rows


def _topic_summary(
    *,
    topic: str,
    candidates: Sequence[Mapping[str, object]],
    new_candidates: Sequence[Mapping[str, object]],
    existing_any: set[tuple[str, str]],
) -> dict[str, object]:
    topic_candidates = [row for row in candidates if str(row.get("topic") or "") == topic]
    topic_new = [row for row in new_candidates if str(row.get("topic") or "") == topic]
    topic_new_strong = [
        row for row in topic_new if str(row.get("confidence_label")) == "strong_direct_taxonomy"
    ]
    return {
        "wikidata_match_count": len(topic_candidates),
        "new_candidate_count": len(topic_new),
        "new_strong_candidate_count": len(topic_new_strong),
        "already_covered_strong_count": len(topic_candidates) - len(topic_new),
        "already_covered_any_count": sum(
            1 for row in topic_candidates if (topic, str(row.get("lemma") or "")) in existing_any
        ),
        "new_counts_by_confidence": dict(
            sorted(Counter(str(row["confidence_label"]) for row in topic_new).items())
        ),
    }


def _topic_for_root(root: str) -> str:
    for topic, roots in ROOTS_BY_TOPIC.items():
        if root in roots:
            return topic
    return ""


def _is_light_root(topic: str, root: str) -> bool:
    return root in LIGHT_ROOTS_BY_TOPIC.get(topic, set())


def _is_noisy_alias_root(*, topic: str, root: str, match_kind: str) -> bool:
    return match_kind == "alias" and root in NOISY_ALIAS_ROOTS_BY_TOPIC.get(topic, set())


def _is_excluded_lemma(*, topic: str, lemma: str) -> bool:
    return lemma in EXCLUDED_LEMMAS_BY_TOPIC.get(topic, set())


def _refresh_candidate_confidence(candidate: Mapping[str, object], *, topic: str) -> None:
    roots = [str(root) for root in candidate.get("wikidata_roots", []) if str(root).strip()]
    has_strong_root = any(not _is_light_root(topic, root) for root in roots)
    if isinstance(candidate, dict):
        if has_strong_root:
            candidate["membership"] = 1.0
            candidate["confidence_label"] = "strong_direct_taxonomy"
        else:
            candidate["membership"] = 0.65
            candidate["confidence_label"] = "light"


def _all_root_qids() -> tuple[str, ...]:
    qids = {qid for roots in ROOTS_BY_TOPIC.values() for qid in roots.values() if str(qid).strip()}
    return tuple(sorted(qids))


def _qid_to_root() -> dict[str, str]:
    return {
        qid: root
        for roots in ROOTS_BY_TOPIC.values()
        for root, qid in roots.items()
        if str(qid).strip()
    }


def _local_frequency_lemmas(path: Path, *, top_n: int) -> list[str]:
    db_path = Path(path).expanduser()
    if not db_path.exists():
        raise FileNotFoundError(f"Missing frequency DB: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        columns = {
            str(row["name"]) for row in conn.execute("PRAGMA table_info(frequency)").fetchall()
        }
        rank_column = "source_rank" if "source_rank" in columns else "core_rank"
        rows = conn.execute(
            f"""
            SELECT lemma, {rank_column} AS source_rank
            FROM frequency
            WHERE lemma IS NOT NULL
              AND TRIM(lemma) != ''
              AND {rank_column} <= ?
            ORDER BY {rank_column} ASC
            """,
            (float(top_n),),
        ).fetchall()
    finally:
        conn.close()
    lemmas = []
    seen = set()
    for row in rows:
        lemma = str(row["lemma"]).strip().lower()
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
    return lemmas


def _existing_topic_lemmas(
    payloads: Sequence[Mapping[str, object]], *, strong_only: bool
) -> set[tuple[str, str]]:
    lemmas: set[tuple[str, str]] = set()
    for payload in payloads:
        if str(payload.get("status") or "") != "ok":
            continue
        for row in _mapping_rows(payload.get("rows")):
            topic = str(row.get("topic") or "").strip()
            if topic not in ROOTS_BY_TOPIC:
                continue
            if (
                strong_only
                and str(row.get("confidence_label") or "") not in ACCEPTED_EXISTING_CONFIDENCE
            ):
                continue
            lemma = str(row.get("lemma") or "").strip().lower()
            if lemma:
                lemmas.add((topic, lemma))
    return lemmas


def _fixture_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    return [dict(row) for row in _mapping_rows(payload.get("rows"))]


def _queryable_label(label: str) -> bool:
    stripped = label.strip()
    return bool(stripped) and len(stripped) <= 40 and "\n" not in stripped and "\t" not in stripped


def _chunks(values: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _append_unique(value: object, item: str) -> None:
    if isinstance(value, list) and item not in value:
        value.append(item)


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
