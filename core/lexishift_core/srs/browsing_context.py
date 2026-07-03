from __future__ import annotations

import hashlib
import math
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.browsing_models import (
    BrowsingSignalAggregate,
    BrowsingSignalContextEvidence,
    BrowsingSignalIngestPolicy,
)
from lexishift_core.srs.browsing_identity import aggregate_reading_confidence


def context_evidence_from_dicts(
    value: object,
    *,
    safe_float_fn,
    optional_str_fn,
) -> tuple[BrowsingSignalContextEvidence, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    contexts: list[BrowsingSignalContextEvidence] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        context_key = normalize_context_key(
            item.get("context_key") or item.get("contextKey") or item.get("key")
        )
        if not context_key:
            continue
        contexts.append(
            BrowsingSignalContextEvidence(
                context_key=context_key,
                source_hit_count=max(0.0, safe_float_fn(item.get("source_hit_count")) or 0.0),
                target_hit_count=max(0.0, safe_float_fn(item.get("target_hit_count")) or 0.0),
                replacement_exposure_count=max(
                    0.0,
                    safe_float_fn(item.get("replacement_exposure_count")) or 0.0,
                ),
                last_seen_at=optional_str_fn(item.get("last_seen_at")),
            )
        )
    return tuple(contexts)


def merge_context_evidence(
    contexts: Sequence[BrowsingSignalContextEvidence],
    *,
    context_key: str,
    side: str,
    count: float,
    policy: BrowsingSignalIngestPolicy,
    now_text: str,
) -> tuple[BrowsingSignalContextEvidence, ...]:
    context_key = normalize_context_key(context_key)
    if not context_key or count <= 0.0:
        return tuple(contexts or ())
    by_key = {context.context_key: context for context in contexts if context.context_key}
    current = by_key.get(context_key) or BrowsingSignalContextEvidence(context_key=context_key)
    source_count = max(0.0, current.source_hit_count)
    target_count = max(0.0, current.target_hit_count)
    replacement_count = max(0.0, current.replacement_exposure_count)
    if side == "source":
        source_count += count
    elif side == "target":
        target_count += count
    elif side == "replacement_exposure":
        replacement_count += count
    by_key[context_key] = BrowsingSignalContextEvidence(
        context_key=context_key,
        source_hit_count=source_count,
        target_hit_count=target_count,
        replacement_exposure_count=replacement_count,
        last_seen_at=now_text,
    )
    retained = sorted(
        by_key.values(),
        key=lambda context: (
            str(context.last_seen_at or ""),
            context_observation_mass(context),
            context.context_key,
        ),
        reverse=True,
    )[: max(0, int(policy.max_contexts_per_item))]
    return tuple(sorted(retained, key=lambda context: context.context_key))


def normalize_context_key(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if _looks_private_context_value(text):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
        return f"ctx:v1:{digest}"
    allowed = []
    for char in text[:96]:
        if char.isalnum() or char in {":", ".", "_", "-"}:
            allowed.append(char)
    normalized = "".join(allowed).strip(".:_-")
    if not normalized:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
        return f"ctx:v1:{digest}"
    return normalized[:96]


def context_count(contexts: Sequence[BrowsingSignalContextEvidence]) -> int:
    return sum(1 for context in contexts if context_observation_mass(context) > 0.0)


def aggregate_evidence_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    _ = policy
    if aggregate is None:
        return 0.0
    if aggregate.context_evidence:
        return discounted_context_evidence_value(
            aggregate.context_evidence,
            reading_confidence=aggregate_reading_confidence(aggregate),
        )
    raw = (
        max(0.0, aggregate.source_hit_count)
        + max(0.0, aggregate.target_hit_count)
        + max(0.0, aggregate.replacement_exposure_count)
    )
    return raw * aggregate_reading_confidence(aggregate)


def aggregate_weighted_evidence_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    policy = policy or BrowsingSignalIngestPolicy()
    if aggregate is None:
        return 0.0
    if aggregate.context_evidence:
        return discounted_context_evidence_value(
            aggregate.context_evidence,
            reading_confidence=aggregate_reading_confidence(aggregate),
            replacement_exposure_weight=policy.replacement_exposure_weight,
        )
    raw = (
        max(0.0, aggregate.source_hit_count)
        + max(0.0, aggregate.target_hit_count)
        + max(0.0, aggregate.replacement_exposure_count)
        * max(0.0, policy.replacement_exposure_weight)
    )
    return raw * aggregate_reading_confidence(aggregate)


def aggregate_context_count(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> int:
    _ = policy
    if aggregate is None or not aggregate.context_evidence:
        return 0
    return context_count(aggregate.context_evidence)


def decay_context_evidence(
    contexts: Sequence[BrowsingSignalContextEvidence],
    *,
    multiplier: float,
) -> tuple[BrowsingSignalContextEvidence, ...]:
    return tuple(
        BrowsingSignalContextEvidence(
            context_key=context.context_key,
            source_hit_count=max(0.0, context.source_hit_count) * multiplier,
            target_hit_count=max(0.0, context.target_hit_count) * multiplier,
            replacement_exposure_count=max(0.0, context.replacement_exposure_count) * multiplier,
            last_seen_at=context.last_seen_at,
        )
        for context in contexts
        if context.context_key
    )


def discounted_context_evidence_value(
    contexts: Sequence[BrowsingSignalContextEvidence],
    *,
    reading_confidence: float,
    replacement_exposure_weight: Optional[float] = None,
) -> float:
    total = 0.0
    for context in contexts:
        raw = context_observation_mass(
            context,
            replacement_exposure_weight=replacement_exposure_weight,
        )
        if raw > 0.0:
            total += math.log2(1.0 + raw)
    return total * max(0.0, min(1.0, float(reading_confidence)))


def context_observation_mass(
    context: BrowsingSignalContextEvidence,
    *,
    replacement_exposure_weight: Optional[float] = None,
) -> float:
    replacement_weight = 1.0
    if replacement_exposure_weight is not None:
        replacement_weight = max(0.0, float(replacement_exposure_weight))
    return (
        max(0.0, context.source_hit_count)
        + max(0.0, context.target_hit_count)
        + max(0.0, context.replacement_exposure_count) * replacement_weight
    )


def _looks_private_context_value(value: str) -> bool:
    lowered = value.lower()
    return (
        "://" in lowered
        or lowered.startswith("www.")
        or "/" in value
        or "?" in value
        or "#" in value
        or "@" in value
        or any(char.isspace() for char in value)
    )
