from __future__ import annotations

import json
from typing import Mapping, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.rulegen.semantic_routing_runtime_policy import (
    DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY,
    build_semantic_admit_batch_response,
)


def semantic_admit_batch(
    paths: HelperPaths,
    *,
    payload: Mapping[str, object],
) -> dict[str, object]:
    pair = str(payload.get("pair") or "").strip().lower()
    if not pair:
        raise ValueError("semantic_admit_batch requires `pair`.")
    profile_id = str(payload.get("profile_id") or "").strip() or "default"
    raw_matches = payload.get("matches")
    if (
        not isinstance(raw_matches, Sequence)
        or isinstance(raw_matches, (str, bytes))
        or not raw_matches
    ):
        raise ValueError("semantic_admit_batch requires non-empty `matches`.")
    if any(not isinstance(match, Mapping) for match in raw_matches):
        raise ValueError("semantic_admit_batch requires object-valued `matches` items.")
    matches = [dict(match) for match in raw_matches]
    inventory_path = paths.semantic_inventory_path(pair, profile_id=profile_id)
    inventory = None
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    return build_semantic_admit_batch_response(
        pair=pair,
        profile_id=profile_id,
        matches=matches,
        inventory=inventory,
        fallback_policy=str(
            payload.get("fallback_policy") or DEFAULT_RUNTIME_SEMANTIC_FALLBACK_POLICY
        ),
        decision_policy_id=str(payload.get("decision_policy_id") or "").strip() or None,
    )
