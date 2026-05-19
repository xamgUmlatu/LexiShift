from __future__ import annotations

from typing import Mapping, Sequence

from lexishift_core.srs.admission_features import (
    clamp01,
    normalize_topic_string_list,
    normalize_topic_token,
)


def trusted_source_mappings(
    taxonomy: Mapping[str, object],
) -> dict[str, list[Mapping[str, object]]]:
    by_label: dict[str, list[Mapping[str, object]]] = {}
    family_ids = {str(row.get("id") or "") for row in _mapping_rows(taxonomy.get("families"))}
    for row in _mapping_rows(taxonomy.get("source_label_mappings")):
        if str(row.get("source_channel") or "") != "sense_topics":
            continue
        source_label = normalize_topic_token(row.get("source_label"))
        target_family = normalize_topic_token(row.get("target_family"))
        if not source_label or target_family not in family_ids:
            continue
        by_label.setdefault(source_label, []).append(
            {
                "source_label": source_label,
                "target_family": target_family,
                "weight": _float(row.get("weight")),
                "confidence": _float(row.get("confidence")),
            }
        )
    return by_label


def trusted_source_exclusions(taxonomy: Mapping[str, object]) -> list[Mapping[str, object]]:
    rules: list[Mapping[str, object]] = []
    for row in _mapping_rows(taxonomy.get("excluded_source_labels")):
        source_label = normalize_topic_token(row.get("source_label"))
        target_family = normalize_topic_token(row.get("target_family"))
        if not source_label or not target_family:
            continue
        rules.append(
            {
                "source_labels": [source_label],
                "target_family": target_family,
                "reason": str(row.get("reason") or ""),
                "policy": "excluded_source_label",
            }
        )
    for row in _mapping_rows(taxonomy.get("source_topic_candidate_exclusions")):
        target_family = normalize_topic_token(row.get("target_family"))
        if not target_family:
            continue
        rules.append(
            {
                "source_labels": [
                    normalize_topic_token(label)
                    for label in raw_topic_tokens(row.get("source_labels"))
                    if normalize_topic_token(label)
                ],
                "lemmas": [
                    _normalize_lemma_for_rule(lemma)
                    for lemma in raw_topic_tokens(row.get("lemmas"))
                    if _normalize_lemma_for_rule(lemma)
                ],
                "pos_buckets": [
                    normalize_topic_token(pos)
                    for pos in raw_topic_tokens(row.get("pos_buckets"))
                    if normalize_topic_token(pos)
                ],
                "target_family": target_family,
                "reason": str(row.get("reason") or ""),
                "policy": str(row.get("policy") or "source_topic_candidate_exclusion"),
            }
        )
    return rules


def trusted_source_exclusion(
    rules: Sequence[Mapping[str, object]],
    *,
    lemma: str,
    seed_info: Mapping[str, object],
    source_label: str,
    target_family: str,
) -> Mapping[str, object]:
    normalized_lemma = _normalize_lemma_for_rule(lemma)
    normalized_source_label = normalize_topic_token(source_label)
    normalized_target = normalize_topic_token(target_family)
    pos_bucket = normalize_topic_token(seed_info.get("pos_bucket"))
    for rule in rules:
        if normalize_topic_token(rule.get("target_family")) != normalized_target:
            continue
        rule_labels = _string_set(rule.get("source_labels"))
        if rule_labels and normalized_source_label not in rule_labels:
            continue
        rule_lemmas = _string_set(rule.get("lemmas"))
        if rule_lemmas and normalized_lemma not in rule_lemmas:
            continue
        rule_pos = _string_set(rule.get("pos_buckets"))
        if rule_pos and pos_bucket not in rule_pos:
            continue
        if not (rule_labels or rule_lemmas or rule_pos):
            continue
        return rule
    return {}


def trusted_labels_for_seed(
    seed: object,
    *,
    lemma: str,
    by_channel: Mapping[str, object],
) -> list[str]:
    labels: list[str] = []
    metadata = _as_mapping(getattr(seed, "metadata", {}))
    for key in ("sense_topics", "topics", "topic", "profile_topics"):
        labels.extend(raw_topic_tokens(metadata.get(key)))
    sense_topics = _as_mapping(by_channel.get("sense_topics"))
    labels.extend(raw_topic_tokens(sense_topics.get(lemma)))
    return sorted(dict.fromkeys(label for label in labels if label))


def seed_info(seed: object, seed_rank: int) -> dict[str, object]:
    admission_weight = _float(getattr(seed, "admission_weight", None))
    base_weight = _float(getattr(seed, "base_weight", None))
    commonness = admission_weight if admission_weight > 0.0 else base_weight
    difficulty = clamp01(1.0 - commonness) or 0.0
    return {
        "seed_rank": int(seed_rank),
        "lemma": str(getattr(seed, "lemma", "") or "").strip(),
        "pos_bucket": str(getattr(seed, "pos_bucket", "") or ""),
        "admission_weight": round(admission_weight, 6),
        "difficulty": round(float(difficulty), 6),
    }


def raw_topic_tokens(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return normalize_topic_string_list(value)
    if isinstance(value, (list, tuple, set)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(raw_topic_tokens(item))
        return sorted(dict.fromkeys(tokens))
    return []


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _float(value: object) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return 0.0
    return 0.0


def _normalize_lemma_for_rule(value: object) -> str:
    return str(value or "").strip().lower()


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        return {value} if value.strip() else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value if str(item).strip()}
    return set()
