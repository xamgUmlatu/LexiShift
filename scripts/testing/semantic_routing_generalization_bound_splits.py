from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping, Sequence


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def load_generalization_split_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Generalization split manifest must be a JSON object.")
    if int(payload.get("schema_version") or 0) != 1:
        raise ValueError("Generalization split manifest must declare schema_version=1.")
    if str(payload.get("pair") or "").strip().lower() != "en-es":
        raise ValueError("Generalization split manifest must target pair 'en-es'.")
    return payload


def build_split_lookup(section: Mapping[str, object]) -> tuple[tuple[str, ...], dict[str, str]]:
    splits = section.get("splits")
    if not isinstance(splits, Mapping):
        raise ValueError("Split section is missing a `splits` mapping.")
    split_ids: list[str] = []
    lookup: dict[str, str] = {}
    for raw_split_id, raw_values in splits.items():
        split_id = str(raw_split_id or "").strip()
        if not split_id:
            continue
        split_ids.append(split_id)
        for value in _normalize_string_list(raw_values):
            existing = lookup.get(value)
            if existing and existing != split_id:
                raise ValueError(
                    f"Split value {value!r} is assigned to both {existing!r} and {split_id!r}."
                )
            lookup[value] = split_id
    if not split_ids:
        raise ValueError("Split section must define at least one non-empty split.")
    return tuple(split_ids), lookup


def resolve_sentence_veto_split_id(
    row: Mapping[str, object],
    split_lookup: Mapping[str, str],
) -> str:
    for candidate in (
        str(row.get("family_id") or "").strip(),
        *(
            _normalize_string_list(
                (row.get("slice_dimensions") or {}).get("family")
                if isinstance(row.get("slice_dimensions"), Mapping)
                else ()
            )
        ),
    ):
        split_id = str(split_lookup.get(candidate) or "").strip()
        if split_id:
            return split_id
    return ""


def resolve_overlap_family_split_id(
    row: Mapping[str, object],
    split_lookup: Mapping[str, str],
) -> str:
    candidates: list[str] = []
    slice_dimensions = row.get("slice_dimensions")
    if isinstance(slice_dimensions, Mapping):
        candidates.extend(_normalize_string_list(slice_dimensions.get("semantic_family")))
    for tag in _normalize_string_list(row.get("slice_tags")):
        if tag.startswith("family:"):
            candidates.append(tag.split(":", 1)[1].strip())
    for candidate in candidates:
        split_id = str(split_lookup.get(candidate) or "").strip()
        if split_id:
            return split_id
    return ""


def partition_rows_by_split(
    rows: Sequence[Mapping[str, object]],
    *,
    split_ids: Sequence[str],
    split_lookup: Mapping[str, str],
    resolve_split_id: Callable[[Mapping[str, object], Mapping[str, str]], str],
) -> tuple[dict[str, list[Mapping[str, object]]], list[Mapping[str, object]]]:
    subset_rows = {str(split_id): [] for split_id in split_ids if str(split_id).strip()}
    unassigned_rows: list[Mapping[str, object]] = []
    for row in rows:
        split_id = resolve_split_id(row, split_lookup)
        if split_id and split_id in subset_rows:
            subset_rows[split_id].append(row)
        else:
            unassigned_rows.append(row)
    return subset_rows, unassigned_rows


def build_metric_views(
    *,
    point_summary: Mapping[str, object],
    bootstrap_intervals: Mapping[str, Mapping[str, object]],
    leave_one_cluster_out: Mapping[str, object],
    metric_directions: Mapping[str, str],
    confidence_level: float,
) -> dict[str, dict[str, object]]:
    loo_metrics = leave_one_cluster_out.get("metrics")
    if not isinstance(loo_metrics, Mapping):
        loo_metrics = {}
    metric_views: dict[str, dict[str, object]] = {}
    for metric_name, direction in metric_directions.items():
        point_estimate = point_summary.get(metric_name)
        bootstrap = bootstrap_intervals.get(metric_name, {})
        loo = loo_metrics.get(metric_name, {})
        metric_view: dict[str, object] = {
            "direction": direction,
            "point_estimate": point_estimate if isinstance(point_estimate, (int, float)) else None,
            "bootstrap_interval": {
                "confidence_level": float(confidence_level),
                "lower": bootstrap.get("lower"),
                "upper": bootstrap.get("upper"),
                "sample_count": bootstrap.get("sample_count"),
            },
            "leave_one_cluster_out": {
                "min": loo.get("min"),
                "max": loo.get("max"),
                "worst_case": loo.get("worst_case"),
                "worst_case_omitted_cluster_id": loo.get("worst_case_omitted_cluster_id"),
            },
        }
        conservative_candidates: list[float] = []
        if direction == "lower":
            for value in (bootstrap.get("upper"), loo.get("worst_case")):
                if isinstance(value, (int, float)):
                    conservative_candidates.append(float(value))
            metric_view["conservative_ceiling"] = (
                max(conservative_candidates) if conservative_candidates else None
            )
        else:
            for value in (bootstrap.get("lower"), loo.get("worst_case")):
                if isinstance(value, (int, float)):
                    conservative_candidates.append(float(value))
            metric_view["conservative_floor"] = (
                min(conservative_candidates) if conservative_candidates else None
            )
        metric_views[metric_name] = metric_view
    return metric_views


def select_best_source_only_row(
    rows: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    candidates = []
    for row in rows:
        source_id = str(row.get("source_id") or "").strip()
        if source_id in {"auto_shadows", "borrowed_trigger_auto_shadows"}:
            candidates.append(row)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            float(row.get("overall_accuracy") or 0.0),
            float(row.get("abstain_recall") or 0.0),
            -float(row.get("harmful_allow_rate") or 0.0),
            -float(row.get("overblocking_rate") or 0.0),
        ),
    )


def find_row(rows: Sequence[Mapping[str, object]], source_id: str) -> Mapping[str, object] | None:
    for row in rows:
        if str(row.get("source_id") or "").strip() == source_id:
            return row
    return None
