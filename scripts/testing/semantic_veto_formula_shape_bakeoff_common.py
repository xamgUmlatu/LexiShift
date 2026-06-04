from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from math import exp, sqrt
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping, _mapping_rows, _safe_float


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ERROR_OUTCOMES = frozenset({"positive_abstain", "negative_allow"})
PRIMARY_SELECTION_MODE = "pre_outcome"
RANK_AGGREGATION_FORMULA = "rank_aggregation"
NEGATIVE_CONTROL_IDS = frozenset({"random_seeded", "target_lemma_length", "source_rank_only"})


def _formula_score(
    *,
    formula_id: str,
    features: Mapping[str, object],
    cell: Mapping[str, object],
) -> float | None:
    f = {key: _safe_float(value) for key, value in features.items()}
    rank = f.get("rank_risk", 0.0)
    missing = f.get("rank_missing_rate", 0.0)
    sense = f.get("sense_risk", 0.0)
    pos = f.get("pos_risk", 0.0)
    case = f.get("case_type_prior", 0.0)
    contract = f.get("shadow_contract_risk", 0.0)
    tie = f.get("near_tie_rate", 0.0)
    low_active = f.get("active_low_rate", 0.0)
    coverage = f.get("coverage_gap", 0.0)
    phrase_surface = f.get("phrase_surface_pattern_rate", 0.0)
    phrase = f.get("is_phrase_case", 0.0)
    shadow = f.get("is_shadow_case", 0.0)
    positive = f.get("is_positive_case", 0.0)
    if formula_id == "linear_baseline":
        return _clamp(
            0.12
            + 0.20 * rank
            + 0.16 * missing
            + 0.18 * sense
            + 0.08 * pos
            + 0.22 * case
            + 0.04 * tie
        )
    if formula_id == "normalized_dot_signal":
        values = [rank, missing, sense, pos, case, contract, tie, coverage]
        weights = [0.22, 0.12, 0.18, 0.08, 0.18, 0.08, 0.08, 0.06]
        return _clamp(_normalized_dot(values, weights))
    if formula_id == "multiplicative_interaction":
        base = _safe_float(
            _formula_score(formula_id="linear_baseline", features=features, cell=cell)
        )
        interaction = (
            0.22 * rank * sense
            + 0.20 * phrase * max(tie, phrase_surface)
            + 0.18 * shadow * contract * sense
            + 0.15 * positive * max(tie, low_active)
            + 0.10 * missing * coverage
        )
        return _clamp(0.70 * base + interaction)
    if formula_id == "probabilistic_product":
        risks = [
            0.25 * rank,
            0.20 * missing,
            0.22 * sense,
            0.14 * pos,
            0.34 * case,
            0.22 * max(tie, low_active),
            0.20 * coverage,
        ]
        product = 1.0
        for risk in risks:
            product *= 1.0 - _clamp(risk)
        return _clamp(1.0 - product)
    if formula_id == "max_risk":
        return _clamp(
            max(
                rank,
                0.65 * missing,
                0.85 * sense,
                0.75 * case,
                0.80 * max(tie, low_active),
                0.70 * coverage,
                0.70 * phrase_surface,
            )
        )
    if formula_id == "gated_by_failure_class":
        if phrase:
            return _clamp(
                0.25
                + 0.24 * phrase_surface
                + 0.22 * max(tie, low_active)
                + 0.18 * coverage
                + 0.08 * rank
                + 0.03 * missing
            )
        if shadow:
            return _clamp(
                0.18
                + 0.24 * contract
                + 0.22 * sense
                + 0.18 * max(tie, low_active)
                + 0.12 * rank
                + 0.06 * coverage
            )
        return _clamp(
            0.10
            + 0.32 * max(tie, low_active)
            + 0.20 * coverage
            + 0.16 * sense
            + 0.14 * rank
            + 0.08 * missing
        )
    if formula_id == "logistic_signal":
        z = (
            -1.65
            + 0.95 * rank
            + 0.70 * missing
            + 0.75 * sense
            + 0.30 * pos
            + 1.15 * case
            + 0.85 * max(tie, low_active)
            + 0.70 * coverage
            + 0.40 * phrase_surface
        )
        return _sigmoid(z)
    if formula_id == "monotone_rule_table":
        score = 0.10
        if phrase:
            score += 0.30
        if shadow and contract >= 0.60:
            score += 0.16
        if positive and (tie >= 0.35 or low_active >= 0.35):
            score += 0.18
        if rank >= 0.85:
            score += 0.16
        elif rank >= 0.45:
            score += 0.08
        if sense >= 0.70:
            score += 0.14
        elif sense >= 0.35:
            score += 0.07
        if coverage >= 0.50:
            score += 0.14
        elif coverage >= 0.25:
            score += 0.07
        if tie >= 0.50:
            score += 0.12
        elif tie >= 0.25:
            score += 0.06
        return _clamp(score)
    if formula_id == "random_seeded":
        return _stable_unit_float(str(cell.get("cell_id") or ""))
    if formula_id == "target_lemma_length":
        triggers = _sequence(cell.get("triggers"))
        longest = max((len(str(item)) for item in triggers), default=0)
        return _clamp(longest / 14.0)
    if formula_id == "source_rank_only":
        return _clamp(0.85 * rank + 0.15 * missing)
    return None


def _data_help_priority(
    *,
    cell: Mapping[str, object],
    predicted_failure_risk: float,
) -> float:
    features = _as_mapping(cell.get("features"))
    exposure = max(0.05, _safe_float(features.get("exposure_weight")))
    product_impact = min(1.0, _safe_float(cell.get("product_impact_weight")) / 1.4)
    uncertainty = max(
        0.08,
        _safe_float(_as_mapping(cell.get("uncertainty_interval")).get("width")),
    )
    fixability = 0.40 + 0.60 * _safe_float(features.get("fixability"))
    coverage_gap = 0.50 + _safe_float(features.get("coverage_gap"))
    return (
        exposure
        * max(0.1, product_impact)
        * uncertainty
        * max(0.0, min(1.0, predicted_failure_risk))
        * fixability
        * coverage_gap
    )


def _normalize_priorities(rows: Sequence[dict[str, object]]) -> None:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("formula_id") or "")].append(row)
    for group in grouped.values():
        max_priority = max((_safe_float(row.get("data_help_priority")) for row in group), default=0)
        if max_priority <= 0:
            continue
        for row in group:
            row["normalized_data_help_priority"] = _round4(
                _safe_float(row.get("data_help_priority")) / max_priority
            )


def _best_formula_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    primary_rows = [row for row in rows if str(row.get("scope_id") or "") == "primary_all_scorers"]
    by_scope: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        by_scope[str(row.get("scope_id") or "")].append(row)
    result = []
    for scope_id, scope_rows in sorted(by_scope.items()):
        best = sorted(scope_rows, key=_formula_rank_key)[0]
        result.append(_public_comparison_row(best))
    if primary_rows:
        best_primary = sorted(primary_rows, key=_formula_rank_key)[0]
        if not any(row.get("scope_id") == "primary_all_scorers" for row in result):
            result.insert(0, _public_comparison_row(best_primary))
    return result


def _formula_rank_key(row: Mapping[str, object]) -> tuple[float, float, float, str]:
    return (
        -_safe_float(row.get("priority_top_k_lift")),
        -_safe_float(row.get("spearman_rank_correlation")),
        _safe_float(row.get("brier_score")),
        str(row.get("formula_id") or ""),
    )


def _public_comparison_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "formula_id": row.get("formula_id"),
        "scope_id": row.get("scope_id"),
        "cell_count": row.get("cell_count"),
        "spearman_rank_correlation": row.get("spearman_rank_correlation"),
        "kendall_tau": row.get("kendall_tau"),
        "brier_score": row.get("brier_score"),
        "top_k_lift": row.get("top_k_lift"),
        "priority_top_k_lift": row.get("priority_top_k_lift"),
        "discovery_spearman": row.get("discovery_spearman"),
        "internal_locked_eval_spearman": row.get("internal_locked_eval_spearman"),
    }


def _public_top_cells(
    rows: Sequence[Mapping[str, object]],
    *,
    by_cell: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    result = []
    for row in rows:
        cell = _as_mapping(by_cell.get(str(row.get("cell_id") or "")))
        result.append(
            {
                "cell_id": row.get("cell_id"),
                "manual_case_type": row.get("manual_case_type"),
                "heuristic_group": row.get("heuristic_group"),
                "predicted_failure_risk": row.get("predicted_failure_risk"),
                "posterior_failure_rate": row.get("posterior_failure_rate"),
                "normalized_data_help_priority": row.get("normalized_data_help_priority"),
                "case_rows": row.get("case_rows"),
                "triggers": cell.get("triggers") or row.get("triggers") or [],
            }
        )
    return result


def _priority_public_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "formula_id": row.get("formula_id"),
        "cell_id": row.get("cell_id"),
        "scorer_id": row.get("scorer_id"),
        "manual_case_type": row.get("manual_case_type"),
        "heuristic_group": row.get("heuristic_group"),
        "shadow_contract": row.get("shadow_contract"),
        "source_rank_bin": row.get("source_rank_bin"),
        "polysemy_band": row.get("polysemy_band"),
        "predicted_failure_risk": row.get("predicted_failure_risk"),
        "posterior_failure_rate": row.get("posterior_failure_rate"),
        "uncertainty_width": row.get("uncertainty_width"),
        "normalized_data_help_priority": row.get("normalized_data_help_priority"),
        "case_rows": row.get("case_rows"),
        "failure_count": row.get("failure_count"),
        "triggers": row.get("triggers") or [],
    }


def _primary_score_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    return [row for row in rows if row.get("selection_mode") == PRIMARY_SELECTION_MODE]


def _pairs_for(rows: Sequence[Mapping[str, object]]) -> list[tuple[float, float]]:
    return [
        (
            _safe_float(row.get("predicted_failure_risk")),
            _safe_float(row.get("posterior_failure_rate")),
        )
        for row in rows
    ]


def _top_k_lift(
    ranked_rows: Sequence[Mapping[str, object]],
    all_rows: Sequence[Mapping[str, object]],
    *,
    top_k: int,
) -> float | None:
    if not ranked_rows or not all_rows:
        return None
    top = ranked_rows[: max(1, min(top_k, len(ranked_rows)))]
    all_rate = _weighted_observed_rate(all_rows)
    top_rate = _weighted_observed_rate(top)
    if all_rate is None or all_rate <= 0 or top_rate is None:
        return None
    return top_rate / all_rate


def _weighted_observed_rate(rows: Sequence[Mapping[str, object]]) -> float | None:
    trials = sum(int(row.get("case_rows") or 0) for row in rows)
    if trials <= 0:
        return None
    failures = sum(int(row.get("failure_count") or 0) for row in rows)
    return failures / trials


def _brier(*, predicted: Sequence[float], observed: Sequence[float]) -> float | None:
    if len(predicted) != len(observed) or not predicted:
        return None
    return sum((p - y) ** 2 for p, y in zip(predicted, observed)) / len(predicted)


def _spearman(pairs: Sequence[tuple[float, float]]) -> float | None:
    clean = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(clean) < 2:
        return None
    left_ranks = _rank_values([pair[0] for pair in clean])
    right_ranks = _rank_values([pair[1] for pair in clean])
    return _pearson(left_ranks, right_ranks)


def _kendall_tau(pairs: Sequence[tuple[float, float]]) -> float | None:
    clean = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(clean) < 2:
        return None
    concordant = 0
    discordant = 0
    for left_index in range(len(clean)):
        for right_index in range(left_index + 1, len(clean)):
            dx = clean[left_index][0] - clean[right_index][0]
            dy = clean[left_index][1] - clean[right_index][1]
            product = dx * dy
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    denominator = concordant + discordant
    if denominator == 0:
        return None
    return (concordant - discordant) / denominator


def _rank_values(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for original_index, _value in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    denom_left = sqrt(sum((x - mean_left) ** 2 for x in left))
    denom_right = sqrt(sum((y - mean_right) ** 2 for y in right))
    denominator = denom_left * denom_right
    if denominator == 0:
        return None
    return numerator / denominator


def _formula_definitions(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    definitions = []
    for row in _mapping_rows(manifest.get("formula_rows")):
        definitions.append(
            {
                "formula_id": row.get("formula_id"),
                "formula_class": row.get("formula_class"),
                "description": row.get("description"),
            }
        )
    for row in _mapping_rows(manifest.get("negative_controls")):
        definitions.append(
            {
                "formula_id": row.get("control_id"),
                "formula_class": "negative_control",
                "description": row.get("description"),
            }
        )
    return definitions


def _failure_count(*, case_type: str, outcomes: Mapping[str, int]) -> int:
    if case_type == "positive_active":
        return int(outcomes.get("positive_abstain") or 0)
    if case_type in {"shadow_negative", "phrase_no_winner"}:
        return int(outcomes.get("negative_allow") or 0)
    return sum(int(outcomes.get(outcome) or 0) for outcome in ERROR_OUTCOMES)


def _product_impact_weight(*, case_type: str, weights: Mapping[str, float]) -> float:
    if case_type == "positive_active":
        return weights.get("positive_allow", 1.0) - weights.get("positive_abstain", -0.4)
    return weights.get("negative_abstain", 0.8) - weights.get("negative_allow", -0.6)


def _rank_risk_score(rank: float) -> float:
    if rank <= 500:
        return 1.0
    if rank <= 1000:
        return 0.85
    if rank <= 2000:
        return 0.65
    if rank <= 5000:
        return 0.45
    return 0.25


def _wilson_interval(*, failures: int, trials: int) -> tuple[float, float]:
    if trials <= 0:
        return (0.0, 1.0)
    z = 1.96
    p = failures / trials
    denominator = 1.0 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denominator
    radius = z * sqrt((p * (1.0 - p) + z**2 / (4 * trials)) / trials) / denominator
    return (max(0.0, centre - radius), min(1.0, centre + radius))


def _has_phrase_surface_pattern(row: Mapping[str, object]) -> bool:
    sentence = str(row.get("sentence") or "").strip().lower()
    trigger = str(row.get("trigger") or "").strip().lower()
    if not sentence or not trigger:
        return False
    if sentence.startswith(f"{trigger},") or sentence.startswith(f"{trigger}!"):
        return True
    if f"{trigger}," in sentence or f"{trigger}!" in sentence or f'"{trigger}"' in sentence:
        return True
    return bool(row.get("phrase_preemption_hit"))


def _internal_split(*, cell_id: str, manifest: Mapping[str, object]) -> str:
    split = _as_mapping(manifest.get("internal_split"))
    modulo = int(split.get("modulo") or 4)
    locked = {int(value) for value in _sequence(split.get("locked_eval_remainders"))}
    digest = hashlib.sha256(cell_id.encode("utf-8")).hexdigest()
    remainder = int(digest[:8], 16) % max(1, modulo)
    return "internal_locked_eval" if remainder in locked else "discovery"


def _resolve_repo_path(value: object) -> Path:
    path = Path(str(value or ""))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _dimension_value(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if value is None or value == "":
        return "missing"
    return str(value)


def _top_k(manifest: Mapping[str, object]) -> int:
    return max(1, int(_as_mapping(manifest.get("data_help_priority")).get("top_k") or 8))


def _rows_for_priority(*, manifest: Mapping[str, object], key: str, priority: str) -> int:
    mapping = _as_mapping(_as_mapping(manifest.get("data_help_priority")).get(key))
    return int(mapping.get(priority) or 0)


def _rotate(values: Sequence[float]) -> list[float]:
    if len(values) < 2:
        return list(values)
    return list(values[1:]) + [values[0]]


def _normalized_dot(values: Sequence[float], weights: Sequence[float]) -> float:
    numerator = sum(value * weight for value, weight in zip(values, weights))
    denom_values = sqrt(sum(value * value for value in values))
    denom_weights = sqrt(sum(weight * weight for weight in weights))
    denominator = denom_values * denom_weights
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))


def _stable_unit_float(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _round4(value: object) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _round6(value: object) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _metric(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _string_list(value: object) -> list[str]:
    return [str(item) for item in _sequence(value) if str(item)]


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
