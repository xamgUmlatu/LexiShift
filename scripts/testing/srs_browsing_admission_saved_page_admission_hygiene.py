from __future__ import annotations

import re
from typing import Mapping, Sequence


HIRAGANA_ONLY_RE = re.compile(r"^[\u3040-\u309fー]+$")
KATAKANA_RE = re.compile(r"[\u30a0-\u30ff]")
POLITE_INFLECTED_TAILS = ("ませんでした", "ません", "ました", "でした")
PARTICLE_PHRASE_SURFACES = frozenset({"というのは", "じゃないか"})
COLLOQUIAL_FRAGMENT_SURFACES = frozenset({"たいもん"})


def build_signal_hygiene(signals: Sequence[Mapping[str, object]]) -> dict[str, object]:
    decisions = [classify_signal_hygiene(signal) for signal in signals]
    rejected = [
        dict(decision) for decision in decisions if str(decision.get("status") or "") == "rejected"
    ]
    retained_suspect = [
        dict(decision) for decision in decisions if str(decision.get("status") or "") == "suspect"
    ]
    return {
        "policy": {
            "version": "saved_page_admission_hygiene_v1",
            "scope": "cheap_pre_aggregate_hygiene_only",
            "full_admission_quality_gate_reused": False,
            "notes": [
                "The full candidate admission_suitability gate still runs during admission.",
                "This layer only removes obvious non-standalone page-surface strings before aggregate ingest.",
            ],
        },
        "decisions": decisions,
        "rejected": rejected,
        "retained_suspect": retained_suspect,
        "rejected_target_keys": sorted(str(row.get("target_key") or "") for row in rejected),
        "retained_suspect_target_keys": sorted(
            str(row.get("target_key") or "") for row in retained_suspect
        ),
        "summary": {
            "input_signal_count": len(signals),
            "accepted_signal_count": sum(
                1 for decision in decisions if decision["status"] == "accepted"
            ),
            "rejected_signal_count": len(rejected),
            "retained_suspect_signal_count": len(retained_suspect),
        },
    }


def classify_signal_hygiene(signal: Mapping[str, object]) -> dict[str, object]:
    lemma = str(signal.get("target_lemma") or signal.get("lemma") or "").strip()
    reading = str(signal.get("target_reading") or signal.get("reading") or "").strip()
    target_key = normalize_signal_target_key(
        target_key=str(signal.get("target_key") or "").strip(),
        lemma=lemma,
        reading=reading,
    )
    surface = lemma or target_key.split("|", 1)[0]
    reasons: list[str] = []
    if not surface:
        reasons.append("missing_surface")
    if surface in PARTICLE_PHRASE_SURFACES:
        reasons.append("particle_phrase_fragment")
    if surface in COLLOQUIAL_FRAGMENT_SURFACES:
        reasons.append("colloquial_fragment")
    if any(surface.endswith(tail) for tail in POLITE_INFLECTED_TAILS):
        reasons.append("polite_inflected_tail")
    if surface.endswith("の多い") and len(surface) >= 4:
        reasons.append("title_like_modifier_phrase")
    if len(surface) > 12 and not KATAKANA_RE.search(surface):
        reasons.append("overlong_non_katakana_surface")
    status = "rejected" if reasons else "accepted"
    if status == "accepted" and HIRAGANA_ONLY_RE.fullmatch(surface) and len(surface) >= 8:
        status = "suspect"
        reasons.append("long_hiragana_only_surface")
    return {
        "status": status,
        "target_key": target_key,
        "target_lemma": lemma,
        "target_reading": reading,
        "reasons": reasons,
        "side": str(signal.get("side") or "").strip(),
        "count": safe_float(signal.get("count")) or 0.0,
        "observation_source": str(signal.get("observation_source") or "").strip(),
    }


def normalize_signal_target_key(*, target_key: str, lemma: str, reading: str) -> str:
    if target_key:
        return target_key
    if lemma and reading and lemma != reading:
        return f"{lemma}|{reading}"
    return lemma


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed
