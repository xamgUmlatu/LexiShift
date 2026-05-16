#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_TAXONOMY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_topic_preference_taxonomy_en_es_current_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_preference_taxonomy_en_es_current_latest.md"
)
RANK_COLUMNS = ("core_rank", "rank", "id", "index")
FREQUENCY_VALUE_COLUMNS = (
    "pmw",
    "core_pmw",
    "frequency",
    "core_frequency",
    "freq",
    "freq_per_million",
    "count",
    "ipm",
)
TRUSTED_SOURCE_CHANNELS = ("sense_topics",)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the en-es product-owned SRS topic preference taxonomy and measure "
            "its current installed-source coverage. Read-only; does not write overlays."
        )
    )
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=10000)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        taxonomy_path=args.taxonomy_json,
        frequency_db=args.frequency_db,
        kaikki_forward_db=args.kaikki_forward_db,
        top_n=max(1, int(args.top_n)),
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
    taxonomy_path: Path = DEFAULT_TAXONOMY,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = 10000,
    generated_at: str | None = None,
) -> dict[str, object]:
    taxonomy = _load_json(taxonomy_path)
    findings = validate_taxonomy(taxonomy)
    coverage = measure_current_coverage(
        taxonomy=taxonomy,
        frequency_db=frequency_db,
        kaikki_forward_db=kaikki_forward_db,
        top_n=top_n,
    )
    findings.extend(_coverage_findings(coverage))
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_preference_taxonomy_validated"
            if status == "ok"
            else "srs_topic_preference_taxonomy_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "taxonomy_json": str(Path(taxonomy_path).expanduser().resolve(strict=False)),
            "frequency_db": str(Path(frequency_db).expanduser().resolve(strict=False)),
            "kaikki_forward_db": str(Path(kaikki_forward_db).expanduser().resolve(strict=False)),
            "top_n": int(top_n),
        },
        "taxonomy": _public_taxonomy_summary(taxonomy),
        "coverage": coverage,
        "findings": findings,
        "summary": {
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
        "limitations": [
            "This report validates taxonomy shape and measures current source coverage only.",
            "It does not mutate frequency packs or write profile_topics overlays.",
            "Current coverage comes from installed Kaikki/Wiktionary sense_topics only.",
            "Curated overlays and embedding inference still need separate source/provenance decisions.",
        ],
    }


def validate_taxonomy(taxonomy: Mapping[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if int(taxonomy.get("schema_version") or 0) >= 1:
        findings.append(_finding("PASS", "schema_version_present", "Taxonomy schema is present."))
    else:
        findings.append(_finding("FAIL", "schema_version_missing", "Taxonomy schema is missing."))
    families = _mapping_rows(taxonomy.get("families"))
    family_ids = [_normalize_token(row.get("id")) for row in families]
    duplicate_families = _duplicates(family_ids)
    if families and not duplicate_families:
        findings.append(
            _finding("PASS", "family_ids_unique", "Product topic family ids are unique.")
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "family_ids_invalid",
                f"Product topic family ids are missing or duplicated: {duplicate_families}",
            )
        )
    family_set = {family for family in family_ids if family}
    mappings = _mapping_rows(taxonomy.get("source_label_mappings"))
    mapping_failures: list[str] = []
    positive_animals_labels: set[str] = set()
    for index, row in enumerate(mappings):
        source_label = _normalize_token(row.get("source_label"))
        target_family = _normalize_token(row.get("target_family"))
        weight = _optional_float(row.get("weight"))
        confidence = _optional_float(row.get("confidence"))
        if not source_label:
            mapping_failures.append(f"mapping[{index}].source_label")
        if target_family not in family_set:
            mapping_failures.append(f"mapping[{index}].target_family:{target_family}")
        if weight is None or not 0.0 < weight <= 1.0:
            mapping_failures.append(f"mapping[{index}].weight")
        if confidence is None or not 0.0 < confidence <= 1.0:
            mapping_failures.append(f"mapping[{index}].confidence")
        if target_family == "animals_nature" and source_label:
            positive_animals_labels.add(source_label)
    if mapping_failures:
        findings.append(
            _finding(
                "FAIL",
                "source_label_mappings_invalid",
                "Some source-label mappings are invalid.",
                details=", ".join(mapping_failures),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "source_label_mappings_valid",
                "Source-label mappings reference known families and valid weights.",
            )
        )
    excluded_labels = {
        _normalize_token(row.get("source_label"))
        for row in _mapping_rows(taxonomy.get("excluded_source_labels"))
        if _normalize_token(row.get("source_label"))
    }
    blocked_positive_overlap = sorted(positive_animals_labels & excluded_labels)
    if blocked_positive_overlap:
        findings.append(
            _finding(
                "FAIL",
                "excluded_labels_mapped_positive",
                "Excluded source labels are also positively mapped.",
                details=", ".join(blocked_positive_overlap),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "excluded_labels_not_mapped_positive",
                "Excluded broad labels are not positively mapped.",
            )
        )
    required_animals_labels = {"animals", "zoology", "botany"}
    missing_animals_labels = sorted(required_animals_labels - positive_animals_labels)
    if missing_animals_labels:
        findings.append(
            _finding(
                "FAIL",
                "animals_nature_seed_labels_missing",
                "Animals/nature seed labels are missing from the mapping.",
                details=", ".join(missing_animals_labels),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "animals_nature_seed_labels_present",
                "Animals/nature includes the current trusted CDE seed labels.",
            )
        )
    exam_family = next(
        (row for row in families if _normalize_token(row.get("id")) == "sat_toefl_exam_prep"), {}
    )
    if _normalize_token(_as_mapping(exam_family).get("readiness_state")) == "legal_source_gated":
        findings.append(
            _finding("PASS", "exam_prep_legal_gated", "SAT/TOEFL remains legal/source gated.")
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "exam_prep_not_legal_gated",
                "SAT/TOEFL must stay legal/source gated until allowed data exists.",
            )
        )
    return findings


def measure_current_coverage(
    *,
    taxonomy: Mapping[str, object],
    frequency_db: Path,
    kaikki_forward_db: Path,
    top_n: int,
) -> dict[str, object]:
    frequency_path = Path(frequency_db).expanduser().resolve(strict=False)
    kaikki_path = Path(kaikki_forward_db).expanduser().resolve(strict=False)
    if not frequency_path.exists() or not kaikki_path.exists():
        return {
            "frequency_db_exists": frequency_path.exists(),
            "kaikki_forward_db_exists": kaikki_path.exists(),
            "row_count": 0,
            "unique_lemma_count": 0,
            "families": [],
        }
    lemmas = list(dict.fromkeys(_candidate_lemmas(frequency_path, top_n=top_n)))
    topics_by_lemma = _kaikki_sense_topics_by_lemma(kaikki_path)
    mappings_by_label = _mappings_by_source_label(taxonomy)
    family_rows: dict[str, set[str]] = defaultdict(set)
    family_label_counter: dict[str, Counter[str]] = defaultdict(Counter)
    family_examples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for lemma in lemmas:
        source_labels = sorted(
            {_normalize_token(value) for value in topics_by_lemma.get(lemma, [])}
        )
        family_scores: dict[str, float] = {}
        evidence_by_family: dict[str, list[str]] = defaultdict(list)
        for source_label in source_labels:
            for mapping in mappings_by_label.get(source_label, []):
                family = _normalize_token(mapping.get("target_family"))
                score = (_optional_float(mapping.get("weight")) or 0.0) * (
                    _optional_float(mapping.get("confidence")) or 0.0
                )
                if family and score > family_scores.get(family, 0.0):
                    family_scores[family] = score
                if family:
                    evidence_by_family[family].append(source_label)
                    family_label_counter[family][source_label] += 1
        for family, score in family_scores.items():
            family_rows[family].add(lemma)
            if len(family_examples[family]) < 12:
                family_examples[family].append(
                    {
                        "lemma": lemma,
                        "score": round(score, 6),
                        "source_labels": sorted(set(evidence_by_family[family])),
                    }
                )
    families = []
    for family in sorted({*family_rows.keys(), *_family_ids(taxonomy)}):
        rows = family_rows.get(family, set())
        families.append(
            {
                "family": family,
                "row_count": len(rows),
                "row_share": _ratio(len(rows), len(lemmas)),
                "top_source_labels": _counter_rows(family_label_counter.get(family, Counter())),
                "sample_rows": family_examples.get(family, []),
            }
        )
    families.sort(key=lambda row: (-int(row["row_count"]), str(row["family"])))
    return {
        "frequency_db_exists": True,
        "kaikki_forward_db_exists": True,
        "row_count": len(lemmas),
        "unique_lemma_count": len(lemmas),
        "source_channels_used": list(TRUSTED_SOURCE_CHANNELS),
        "families": families,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    coverage = _as_mapping(report.get("coverage"))
    lines = [
        "# en-es SRS Topic Preference Taxonomy Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows measured: `{coverage.get('row_count', 0)}`",
        f"- Unique lemmas measured: `{coverage.get('unique_lemma_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        details = str(finding.get("details") or "").strip()
        suffix = f" Details: {details}" if details else ""
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}{suffix}"
        )
    lines.extend(["", "## Current Installed-Source Coverage", ""])
    lines.append("| Family | Rows | Share | Top Source Labels |")
    lines.append("| --- | ---: | ---: | --- |")
    for family in _mapping_rows(coverage.get("families")):
        top_labels = ", ".join(
            f"{row.get('label')}={row.get('count')}"
            for row in _mapping_rows(family.get("top_source_labels"))[:5]
        )
        lines.append(
            f"| `{family.get('family', '')}` | {family.get('row_count', 0)} | "
            f"{_pct(family.get('row_share'))} | {top_labels or 'none'} |"
        )
    lines.extend(["", "## Animals/Nature Samples", ""])
    animals = next(
        (
            family
            for family in _mapping_rows(coverage.get("families"))
            if family.get("family") == "animals_nature"
        ),
        {},
    )
    sample_rows = _mapping_rows(_as_mapping(animals).get("sample_rows"))
    if not sample_rows:
        lines.append("No current installed-source samples matched `animals_nature`.")
    else:
        lines.append("| Lemma | Score | Source Labels |")
        lines.append("| --- | ---: | --- |")
        for sample in sample_rows:
            lines.append(
                f"| `{sample.get('lemma', '')}` | {sample.get('score', 0)} | "
                f"`{', '.join(sample.get('source_labels', []))}` |"
            )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _coverage_findings(coverage: Mapping[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if not coverage.get("frequency_db_exists"):
        findings.append(
            _finding("FAIL", "frequency_db_missing", "Frequency DB is missing for coverage audit.")
        )
    if not coverage.get("kaikki_forward_db_exists"):
        findings.append(
            _finding("FAIL", "kaikki_db_missing", "Kaikki DB is missing for coverage audit.")
        )
    family_by_id = {
        str(row.get("family") or ""): row for row in _mapping_rows(coverage.get("families"))
    }
    animals = _as_mapping(family_by_id.get("animals_nature"))
    if int(animals.get("row_count") or 0) > 0:
        findings.append(
            _finding(
                "PASS",
                "animals_nature_current_signal_available",
                "Current installed sources provide some animals/nature seed coverage.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "animals_nature_current_signal_absent",
                "No current installed-source animals/nature rows were found.",
            )
        )
    return findings


def _load_json(path: Path) -> Mapping[str, object]:
    resolved = Path(path).expanduser().resolve(strict=False)
    return _as_mapping(json.loads(resolved.read_text(encoding="utf-8")))


def _public_taxonomy_summary(taxonomy: Mapping[str, object]) -> dict[str, object]:
    families = _mapping_rows(taxonomy.get("families"))
    mappings = _mapping_rows(taxonomy.get("source_label_mappings"))
    return {
        "taxonomy_id": str(taxonomy.get("taxonomy_id") or ""),
        "language_pair": str(taxonomy.get("language_pair") or ""),
        "family_count": len(families),
        "mapping_count": len(mappings),
        "families": [
            {
                "id": _normalize_token(row.get("id")),
                "product_priority": str(row.get("product_priority") or ""),
                "readiness_state": str(row.get("readiness_state") or ""),
            }
            for row in families
        ],
    }


def _family_ids(taxonomy: Mapping[str, object]) -> set[str]:
    return {
        _normalize_token(row.get("id"))
        for row in _mapping_rows(taxonomy.get("families"))
        if _normalize_token(row.get("id"))
    }


def _mappings_by_source_label(
    taxonomy: Mapping[str, object],
) -> dict[str, list[Mapping[str, object]]]:
    by_label: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in _mapping_rows(taxonomy.get("source_label_mappings")):
        if str(row.get("source_channel") or "") not in TRUSTED_SOURCE_CHANNELS:
            continue
        source_label = _normalize_token(row.get("source_label"))
        if source_label:
            by_label[source_label].append(row)
    return by_label


def _kaikki_sense_topics_by_lemma(path: Path) -> dict[str, set[str]]:
    topics_by_lemma: dict[str, set[str]] = defaultdict(set)
    with sqlite3.connect(path) as conn:
        for lemma, topics_json in conn.execute(
            "SELECT headword_lc, topics_json FROM sense_glosses"
        ):
            normalized_lemma = _normalize_lemma(lemma)
            if not normalized_lemma:
                continue
            topics_by_lemma[normalized_lemma].update(_json_string_list(topics_json))
    return topics_by_lemma


def _candidate_lemmas(path: Path, *, top_n: int) -> list[str]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        columns = _column_names(conn, "frequency")
        lemma_column = _resolve_column("lemma", columns)
        if not lemma_column:
            return []
        rank_column = _resolve_first_column(RANK_COLUMNS, columns)
        frequency_column = _resolve_first_column(FREQUENCY_VALUE_COLUMNS, columns)
        order_terms: list[str] = []
        if rank_column:
            order_terms.append(f"{_quote_identifier(rank_column)} IS NULL ASC")
            order_terms.append(f"{_quote_identifier(rank_column)} ASC")
        if frequency_column:
            order_terms.append(f"{_quote_identifier(frequency_column)} DESC")
        order_sql = f" ORDER BY {', '.join(order_terms)}" if order_terms else ""
        sql = f"SELECT {_quote_identifier(lemma_column)} FROM frequency{order_sql} LIMIT ?"
        return [
            _normalize_lemma(row[lemma_column])
            for row in conn.execute(sql, (max(1, int(top_n)),))
            if _normalize_lemma(row[lemma_column])
        ]
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _resolve_column(requested: str, columns: Sequence[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    return lowered.get(str(requested).strip().lower())


def _resolve_first_column(candidates: Sequence[str], columns: Sequence[str]) -> str | None:
    for candidate in candidates:
        resolved = _resolve_column(candidate, columns)
        if resolved:
            return resolved
    return None


def _json_string_list(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value or "").strip()
    if not text or text == "[]":
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [_normalize_token(text)] if _normalize_token(text) else []
    if not isinstance(payload, list):
        return []
    return [_normalize_token(item) for item in payload if _normalize_token(item)]


def _quote_identifier(value: object) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _counter_rows(counter: Counter[str]) -> list[dict[str, object]]:
    return [{"label": label, "count": count} for label, count in counter.most_common(12)]


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _duplicates(values: Sequence[str]) -> list[str]:
    counter = Counter(value for value in values if value)
    return sorted(value for value, count in counter.items() if count > 1)


def _optional_float(value: object) -> float | None:
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _finding(
    level: str,
    code: str,
    message: str,
    *,
    details: str | None = None,
) -> dict[str, object]:
    row = {"level": level, "code": code, "message": message}
    if details:
        row["details"] = details
    return row


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _normalize_token(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    normalized = raw.replace("\\", "_").replace("/", "_").replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().casefold()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
