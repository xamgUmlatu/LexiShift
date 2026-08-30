from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from lexishift_core.srs.admission_policy import POS_BUCKET_OTHER
from lexishift_core.srs.candidate_identity import candidate_identity_from_seed
from lexishift_core.srs.seed_cache import (
    read_seed_frontier_cache_rows,
    write_seed_frontier_cache_rows,
)


def load_seed_frontier_cache(
    *,
    cache_path: Path,
    config: object,
    seed_factory,
) -> list[object] | None:
    rows = read_seed_frontier_cache_rows(cache_path)
    if rows is None:
        return None
    language_pair = str(getattr(config, "language_pair", "") or "")
    return [
        seed_from_cache_row(row, language_pair=language_pair, seed_factory=seed_factory)
        for row in rows
    ]


def write_seed_frontier_cache(
    *,
    cache_path: Path,
    seeds: Sequence[object],
    config: object,
) -> None:
    write_seed_frontier_cache_rows(
        cache_path=cache_path,
        rows=[seed_to_cache_row(seed) for seed in seeds],
        config=config,
    )


def seed_to_cache_row(seed: object) -> dict[str, object]:
    candidate_identity = candidate_identity_from_seed(seed)
    return {
        "lemma": getattr(seed, "lemma"),
        "language_pair": getattr(seed, "language_pair"),
        "identity_key": getattr(seed, "identity_key", "")
        or str(candidate_identity.get("key") or "").strip(),
        "candidate_identity": _json_safe(candidate_identity),
        "word_package": _json_safe(getattr(seed, "word_package", None)),
        "core_rank": getattr(seed, "core_rank", None),
        "pos": getattr(seed, "pos", None),
        "pos_bucket": getattr(seed, "pos_bucket", None),
        "pos_weight": getattr(seed, "pos_weight", None),
        "pmw": getattr(seed, "pmw", None),
        "base_weight": getattr(seed, "base_weight", None),
        "admission_weight": getattr(seed, "admission_weight", None),
        "metadata": _json_safe(getattr(seed, "metadata", {})),
        "candidate_state": getattr(seed, "candidate_state", None),
        "presentation_mode": getattr(seed, "presentation_mode", None),
        "problem_class": getattr(seed, "problem_class", None),
        "classification_confidence": getattr(seed, "classification_confidence", None),
        "classification_reasons": list(getattr(seed, "classification_reasons", ()) or ()),
        "admission_suitability": getattr(seed, "admission_suitability", None),
        "pos_raw": getattr(seed, "pos_raw", None),
        "pos_canonical": getattr(seed, "pos_canonical", None),
        "pos_source_profile": getattr(seed, "pos_source_profile", None),
        "pos_matched_rule": getattr(seed, "pos_matched_rule", None),
        "pos_mapped": getattr(seed, "pos_mapped", False),
    }


def seed_from_cache_row(row: object, *, language_pair: str, seed_factory):
    if not isinstance(row, dict):
        raise ValueError("Invalid seed frontier cache row.")
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        raise ValueError("Invalid seed frontier cache row without lemma.")
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    word_package = row.get("word_package") if isinstance(row.get("word_package"), dict) else None
    classification_reasons = row.get("classification_reasons")
    if not isinstance(classification_reasons, list):
        classification_reasons = []
    admission_suitability = _safe_float(row.get("admission_suitability"))
    if admission_suitability is None:
        admission_suitability = 1.0
    identity_key = str(row.get("identity_key") or "").strip()
    candidate_identity = row.get("candidate_identity")
    if not identity_key and isinstance(candidate_identity, dict):
        identity_key = str(candidate_identity.get("key") or "").strip()
    return seed_factory(
        lemma=lemma,
        language_pair=str(row.get("language_pair") or language_pair),
        identity_key=identity_key,
        word_package=word_package,
        core_rank=_safe_float(row.get("core_rank")),
        pos=_optional_text(row.get("pos")),
        pos_bucket=str(row.get("pos_bucket") or POS_BUCKET_OTHER),
        pos_weight=_safe_float(row.get("pos_weight")) or 0.0,
        pmw=_safe_float(row.get("pmw")),
        base_weight=_safe_float(row.get("base_weight")) or 0.0,
        admission_weight=_safe_float(row.get("admission_weight")) or 0.0,
        metadata=metadata,
        candidate_state=str(row.get("candidate_state") or "normal_vocab"),
        presentation_mode=str(row.get("presentation_mode") or "vocab"),
        problem_class=str(row.get("problem_class") or "normal_vocab"),
        classification_confidence=str(row.get("classification_confidence") or "review"),
        classification_reasons=tuple(str(item) for item in classification_reasons),
        admission_suitability=admission_suitability,
        pos_raw=_optional_text(row.get("pos_raw")),
        pos_canonical=_optional_text(row.get("pos_canonical")),
        pos_source_profile=_optional_text(row.get("pos_source_profile")),
        pos_matched_rule=_optional_text(row.get("pos_matched_rule")),
        pos_mapped=bool(row.get("pos_mapped")),
    )


def _json_safe(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _optional_text(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return float(value)
        except ValueError:
            return None
    return None
