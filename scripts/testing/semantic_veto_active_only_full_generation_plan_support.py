from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _mapping_rows


ZIPF_BAND_ORDER = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)


def source_target_review_decisions(
    payload: Mapping[str, object] | None,
) -> dict[str, dict[str, object]]:
    if payload is None:
        return {}
    decisions: dict[str, dict[str, object]] = {}
    for row in _mapping_rows(payload.get("decisions")):
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        if not source or not target:
            continue
        key = str(row.get("coverage_key") or coverage_key(source=source, target=target))
        approved = bool(row.get("approved_for_active_only_generation"))
        decision = str(row.get("decision") or ("approve" if approved else "exclude"))
        decisions[key] = {
            **dict(row),
            "source": source,
            "target": target,
            "coverage_key": key,
            "decision": decision,
            "approved_for_active_only_generation": approved,
            "review_status": "approved" if approved else "excluded",
        }
    return decisions


def annotate_source_target_review(
    row: Mapping[str, object],
    *,
    review_decisions: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    output = dict(row)
    key = str(output.get("coverage_key") or "")
    decision = review_decisions.get(key)
    if not review_decisions:
        return output
    if not decision:
        output["source_target_review_status"] = "unreviewed"
        output["source_target_review_decision"] = "unreviewed"
        output["source_target_review_notes"] = ""
        output["source_target_review_rationale"] = ""
        return output
    output["source_target_review_status"] = str(decision.get("review_status") or "")
    output["source_target_review_decision"] = str(decision.get("decision") or "")
    output["source_target_review_notes"] = str(decision.get("notes") or "")
    output["source_target_review_rationale"] = str(decision.get("rationale") or "")
    output["source_target_review_approved_for_active_only_generation"] = bool(
        decision.get("approved_for_active_only_generation")
    )
    return output


def source_target_review_excludes(row: Mapping[str, object]) -> bool:
    return str(row.get("source_target_review_status") or "") == "excluded"


def coverage_breakdown(
    *,
    denominator_rows: Sequence[Mapping[str, object]],
    covered_denominator_keys: set[str],
    group_key: str,
    label: str,
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in denominator_rows:
        grouped[str(row.get(group_key) or "missing")].append(row)
    rows = []
    for band in ZIPF_BAND_ORDER:
        bucket = grouped.get(band, [])
        if not bucket:
            continue
        covered = [
            row for row in bucket if str(row.get("coverage_key") or "") in covered_denominator_keys
        ]
        rows.append(
            {
                label: band,
                "family_count": len(bucket),
                "covered_family_count": len(covered),
                "covered_share": _ratio(len(covered), len(bucket)),
                "uncovered_family_count": len(bucket) - len(covered),
                "sample_uncovered": [
                    {"source": row.get("source"), "target": row.get("target")}
                    for row in bucket
                    if str(row.get("coverage_key") or "") not in covered_denominator_keys
                ][:10],
            }
        )
    return rows


def coverage_matrix(
    *,
    denominator_rows: Sequence[Mapping[str, object]],
    covered_denominator_keys: set[str],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in denominator_rows:
        grouped[
            (
                str(row.get("source_zipf_band_en") or "missing"),
                str(row.get("target_zipf_band_es") or "missing"),
            )
        ].append(row)
    matrix = []
    for source_band in ZIPF_BAND_ORDER:
        for target_band in ZIPF_BAND_ORDER:
            bucket = grouped.get((source_band, target_band), [])
            if not bucket:
                continue
            covered = [
                row
                for row in bucket
                if str(row.get("coverage_key") or "") in covered_denominator_keys
            ]
            matrix.append(
                {
                    "source_zipf_band_en": source_band,
                    "target_zipf_band_es": target_band,
                    "family_count": len(bucket),
                    "covered_family_count": len(covered),
                    "covered_share": _ratio(len(covered), len(bucket)),
                    "uncovered_family_count": len(bucket) - len(covered),
                }
            )
    return matrix


def coverage_key(*, source: str, target: str) -> str:
    return f"{_normalize_key_part(source)}::{_normalize_key_part(target)}"


def _normalize_key_part(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)
