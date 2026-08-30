#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-de-default.sqlite"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_wikidata_science_topic_overlay_en_de_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_wikidata_science_topic_overlay_en_de_latest.md"
LANGUAGE_PAIR = "en-de"
OVERLAY_ID = "srs_wikidata_science_topic_overlay_en_de_v1"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "LexiShiftWikidataScienceTopicOverlay/0.1 (local build-time enrichment)"
TOPIC = "science_technology"
CHEMICAL_ELEMENT_QID = "Q11344"
UNIT_OF_MEASUREMENT_QID = "Q47574"

ELEMENT_EXCLUDED_LEMMAS = {
    # Dominant German learner sense is not the element.
    "essen",
}
UNIT_EXACT_LABELS = {
    "ampere",
    "bar",
    "becquerel",
    "byte",
    "candela",
    "coulomb",
    "dezimeter",
    "farad",
    "gramm",
    "hektar",
    "hertz",
    "joule",
    "kelvin",
    "kilogramm",
    "kilohertz",
    "kilometer",
    "kilowatt",
    "liter",
    "lumen",
    "lux",
    "meter",
    "mikrometer",
    "milligramm",
    "milliliter",
    "millimeter",
    "nanometer",
    "newton",
    "ohm",
    "pascal",
    "tesla",
    "volt",
    "watt",
}
UNIT_EXCLUDED_LEMMAS = {
    # Too broad or product-ambiguous for a first safe science pass.
    "bar",
    "grad",
    "sekunde",
    "minute",
    "stunde",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a conservative en-de science topic overlay from bounded Wikidata "
            "structured-data classes. This is build-time only; no runtime Wikidata "
            "dependency is introduced."
        )
    )
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--top-n", type=int, default=20000)
    parser.add_argument(
        "--fixture-json",
        type=Path,
        help="Offline fixture with element_rows/unit_rows for deterministic tests.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        top_n=max(1, int(args.top_n)),
        fixture_json=args.fixture_json,
        timeout_seconds=max(1, int(args.timeout_seconds)),
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
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    top_n: int = 20000,
    fixture_json: Path | None = None,
    timeout_seconds: int = 30,
    generated_at: str | None = None,
) -> dict[str, object]:
    frequency_rows = _load_frequency_rows(frequency_db, top_n=top_n)
    local_lemmas = set(frequency_rows)
    if fixture_json is not None:
        fixture = _load_json(fixture_json)
        element_rows = _mapping_rows(fixture.get("element_rows"))
        unit_rows = _mapping_rows(fixture.get("unit_rows"))
        source_mode = "fixture"
    else:
        element_rows = fetch_chemical_element_rows(timeout_seconds=timeout_seconds)
        unit_rows = fetch_unit_rows(
            sorted((local_lemmas & UNIT_EXACT_LABELS) - UNIT_EXCLUDED_LEMMAS),
            timeout_seconds=timeout_seconds,
        )
        source_mode = "wikidata_sparql"

    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    skipped_rows: list[dict[str, object]] = []
    duplicate_row_count = 0
    for source_id, rows, excluded in (
        ("wikidata_chemical_elements", element_rows, ELEMENT_EXCLUDED_LEMMAS),
        ("wikidata_units_of_measure", unit_rows, UNIT_EXCLUDED_LEMMAS),
    ):
        for raw_row in rows:
            lemma = _normalize_lemma(raw_row.get("label"))
            qid = str(raw_row.get("qid") or "").strip()
            if not lemma:
                skipped_rows.append(_skipped_row(raw_row, source_id, "missing_label"))
                continue
            if lemma in excluded:
                skipped_rows.append(_skipped_row(raw_row, source_id, "excluded_homograph"))
                continue
            frequency = frequency_rows.get(lemma)
            if frequency is None:
                skipped_rows.append(_skipped_row(raw_row, source_id, "outside_frequency_frontier"))
                continue
            row = _overlay_row(
                source_id=source_id,
                raw_row=raw_row,
                lemma=str(frequency.get("lemma") or lemma),
                qid=qid,
                frequency=frequency,
            )
            key = (str(row["lemma"]), str(row["topic"]))
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = row
                continue
            duplicate_row_count += 1
            rows_by_key[key] = _merge_duplicate_rows(existing, row)

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
        skipped_rows=skipped_rows,
        duplicate_row_count=duplicate_row_count,
        element_rows=element_rows,
        unit_rows=unit_rows,
    )
    status = "ok" if rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_wikidata_science_topic_overlay_ready"
            if status == "ok"
            else "srs_wikidata_science_topic_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": OVERLAY_ID,
        "overlay_policy": {
            "promotion_state": "reviewed_wikidata_structured_overlay_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": source_mode,
            "source_license": "Wikidata structured data CC0",
            "runtime_dependency": "none",
            "topic_policy": (
                "chemical elements and conservative unit-shaped measurement labels are "
                "routed to science_technology; noisy homographs are excluded."
            ),
            "match_policy": "lowercase_exact_wikidata_german_label_in_frequency_top_n",
        },
        "inputs": {
            "frequency_db": str(frequency_db),
            "top_n": int(top_n),
            "fixture_json": _repo_path(fixture_json),
            "wikidata_roots": {
                "chemical_element": CHEMICAL_ELEMENT_QID,
                "unit_of_measurement": UNIT_OF_MEASUREMENT_QID,
            },
        },
        "source_license": {
            "provider": "Wikidata",
            "declared_license": "CC0",
            "homepage": "https://www.wikidata.org/",
            "query_service": SPARQL_ENDPOINT,
        },
        "summary": summary,
        "skipped_rows": skipped_rows[:300],
        "rows": rows,
        "limitations": [
            "This overlay intentionally covers only conservative science subdomains.",
            "Chemical elements are queried as direct Wikidata chemical-element items.",
            "Units are limited to local unit-shaped labels before Wikidata verification.",
            "Rows are exact German label matches; aliases are not promoted for this safe pass.",
        ],
    }


def fetch_chemical_element_rows(*, timeout_seconds: int = 30) -> list[dict[str, object]]:
    query = f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?item ?label ?desc WHERE {{
  ?item wdt:P31 wd:{CHEMICAL_ELEMENT_QID} .
  ?item rdfs:label ?labelNode .
  FILTER(LANG(?labelNode) = "de")
  BIND(LCASE(STR(?labelNode)) AS ?label)
  OPTIONAL {{ ?item schema:description ?desc . FILTER(LANG(?desc) = "de") }}
}}
ORDER BY ?label
"""
    return _sparql_rows(query, timeout_seconds=timeout_seconds)


def fetch_unit_rows(labels: Sequence[str], *, timeout_seconds: int = 30) -> list[dict[str, object]]:
    if not labels:
        return []
    values = " ".join(json.dumps(label, ensure_ascii=False) for label in labels)
    query = f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?item ?label ?desc WHERE {{
  VALUES ?wanted {{ {values} }}
  ?item wdt:P31/wdt:P279* wd:{UNIT_OF_MEASUREMENT_QID} .
  ?item rdfs:label ?labelNode .
  FILTER(LANG(?labelNode) = "de")
  BIND(LCASE(STR(?labelNode)) AS ?label)
  FILTER(?label = ?wanted)
  OPTIONAL {{ ?item schema:description ?desc . FILTER(LANG(?desc) = "de") }}
}}
ORDER BY ?label
"""
    return _sparql_rows(query, timeout_seconds=timeout_seconds)


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Wikidata Science Topic Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime rows: `{summary.get('row_count', 0)}`",
        f"- Unique lemmas: `{summary.get('unique_lemma_count', 0)}`",
        f"- Duplicate rows resolved: `{summary.get('duplicate_row_count', 0)}`",
        f"- Skipped rows: `{summary.get('skipped_row_count', 0)}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in sorted(_as_mapping(summary.get("counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")
    lines.extend(["", "## Source Counts", "", "| Source | Rows |", "| --- | ---: |"])
    for source, count in sorted(_as_mapping(summary.get("counts_by_source")).items()):
        lines.append(f"| `{source}` | {int(count)} |")
    lines.extend(
        ["", "## Rows", "", "| Lemma | Source | Rank | QID |", "| --- | --- | ---: | --- |"]
    )
    for row in _mapping_rows(report.get("rows"))[:160]:
        provenance = _as_mapping(row.get("provenance"))
        qids = ", ".join(str(qid) for qid in _string_list(provenance.get("wikidata_qids")))
        lines.append(
            f"| `{row.get('lemma', '')}` | `{row.get('source_label', '')}` | "
            f"{row.get('corpus_rank', '')} | {qids} |"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def _sparql_rows(query: str, *, timeout_seconds: int) -> list[dict[str, object]]:
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
    for binding in _mapping_rows(_as_mapping(payload.get("results")).get("bindings")):
        rows.append(
            {
                "label": str(_as_mapping(binding.get("label")).get("value") or ""),
                "qid": str(_as_mapping(binding.get("item")).get("value") or "").rsplit("/", 1)[-1],
                "description": str(_as_mapping(binding.get("desc")).get("value") or ""),
            }
        )
    return rows


def _overlay_row(
    *,
    source_id: str,
    raw_row: Mapping[str, object],
    lemma: str,
    qid: str,
    frequency: Mapping[str, object],
) -> dict[str, object]:
    evidence_score = 0.98 if source_id == "wikidata_chemical_elements" else 0.94
    return {
        "language_pair": LANGUAGE_PAIR,
        "lemma": lemma,
        "topic": TOPIC,
        "membership": 1.0,
        "confidence_label": "strong",
        "review_state": "structured_source_safe_pass",
        "review_id": _review_id(source_id, lemma, TOPIC),
        "source_channel": "wikidata_structured_data",
        "source_label": source_id,
        "facet_id": (
            "chemical_elements" if source_id == "wikidata_chemical_elements" else "units_of_measure"
        ),
        "evidence_score": evidence_score,
        "corpus_rank": frequency.get("source_rank"),
        "pmw": frequency.get("pmw"),
        "pos": str(frequency.get("pos") or ""),
        "pos_canonical": str(frequency.get("pos_canonical") or ""),
        "provenance": {
            "source_overlay_ids": [OVERLAY_ID],
            "wikidata_qids": [qid] if qid else [],
            "wikidata_label": str(raw_row.get("label") or ""),
            "wikidata_description": str(raw_row.get("description") or ""),
            "wikidata_root_qid": (
                CHEMICAL_ELEMENT_QID
                if source_id == "wikidata_chemical_elements"
                else UNIT_OF_MEASUREMENT_QID
            ),
            "source_license": "Wikidata structured data CC0",
            "runtime_dependency": "none",
            "match_policy": "exact_german_label_in_frequency_top_n",
        },
    }


def _merge_duplicate_rows(
    left: Mapping[str, object], right: Mapping[str, object]
) -> dict[str, object]:
    winner = dict(left if _row_priority(left) >= _row_priority(right) else right)
    provenance = dict(_as_mapping(winner.get("provenance")))
    qids: list[str] = []
    source_labels: list[str] = []
    for row in (left, right):
        for qid in _string_list(_as_mapping(row.get("provenance")).get("wikidata_qids")):
            if qid and qid not in qids:
                qids.append(qid)
        source_label = str(row.get("source_label") or "").strip()
        if source_label and source_label not in source_labels:
            source_labels.append(source_label)
    provenance["wikidata_qids"] = qids
    provenance["source_labels"] = source_labels
    winner["provenance"] = provenance
    return winner


def _row_priority(row: Mapping[str, object]) -> tuple[float, float, float]:
    return (
        _safe_float(row.get("membership")),
        _safe_float(row.get("evidence_score")),
        -_safe_float(row.get("corpus_rank"), default=999999.0),
    )


def _summary(
    rows: Sequence[Mapping[str, object]],
    *,
    skipped_rows: Sequence[Mapping[str, object]],
    duplicate_row_count: int,
    element_rows: Sequence[Mapping[str, object]],
    unit_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    counts_by_source = Counter(str(row.get("source_label") or "") for row in rows)
    counts_by_confidence = Counter(str(row.get("confidence_label") or "unknown") for row in rows)
    skip_counts = Counter(str(row.get("reason") or "unknown") for row in skipped_rows)
    unique_lemmas = {str(row.get("lemma") or "").strip() for row in rows if row.get("lemma")}
    return {
        "row_count": len(rows),
        "runtime_effective_row_count": len(rows),
        "unique_lemma_count": len(unique_lemmas),
        "topic_count": len(counts_by_topic),
        "runtime_effective_topic_count": len(counts_by_topic),
        "counts_by_topic": dict(sorted(counts_by_topic.items())),
        "runtime_effective_counts_by_topic": dict(sorted(counts_by_topic.items())),
        "counts_by_source": dict(sorted(counts_by_source.items())),
        "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
        "runtime_effective_counts_by_confidence": dict(sorted(counts_by_confidence.items())),
        "wikidata_element_row_count": len(element_rows),
        "wikidata_unit_row_count": len(unit_rows),
        "skipped_row_count": len(skipped_rows),
        "skipped_counts_by_reason": dict(sorted(skip_counts.items())),
        "duplicate_row_count": duplicate_row_count,
    }


def _load_frequency_rows(path: Path, *, top_n: int) -> dict[str, dict[str, object]]:
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
        pos_canonical_expr = "pos_canonical" if "pos_canonical" in columns else "''"
        rows = conn.execute(
            f"""
            SELECT lemma, {rank_column} AS source_rank, pmw, pos, {pos_canonical_expr} AS pos_canonical
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
    by_lemma: dict[str, dict[str, object]] = {}
    for row in rows:
        lemma = str(row["lemma"]).strip()
        lookup = lemma.lower()
        if not lookup or lookup in by_lemma:
            continue
        by_lemma[lookup] = {
            "lemma": lemma,
            "source_rank": _safe_float(row["source_rank"], default=0.0),
            "pmw": _safe_float(row["pmw"], default=0.0),
            "pos": str(row["pos"] or ""),
            "pos_canonical": str(row["pos_canonical"] or ""),
        }
    return by_lemma


def _skipped_row(row: Mapping[str, object], source_id: str, reason: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "label": str(row.get("label") or ""),
        "qid": str(row.get("qid") or ""),
        "reason": reason,
    }


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().lower()


def _review_id(source_id: str, lemma: str, topic: str) -> str:
    digest = hashlib.sha1(f"{source_id}\0{lemma}\0{topic}".encode("utf-8")).hexdigest()[:12]
    return f"srs-ende-wikidata-science-{digest}"


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


if __name__ == "__main__":
    raise SystemExit(main())
