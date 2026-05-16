from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIGNAL_POLICY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_animals_plants_signal_policy_en_es.json"
)


@dataclass(frozen=True)
class SignalPolicy:
    path: Path
    policy_id: str
    broad_excluded_labels: frozenset[str]
    ambiguous_context_labels: frozenset[str]
    topic_confidence: Mapping[str, Mapping[str, float]]
    category_confidence: Mapping[str, Mapping[str, float]]
    primary_translations: Mapping[str, frozenset[str]]
    animal_translation_pattern: re.Pattern[str]
    animal_gloss_pattern: re.Pattern[str]
    plant_translation_pattern: re.Pattern[str]
    plant_gloss_pattern: re.Pattern[str]


def load_signal_policy(path: Path = DEFAULT_SIGNAL_POLICY) -> SignalPolicy:
    resolved_path = Path(path).expanduser().resolve(strict=False)
    payload = _load_json(resolved_path)
    return SignalPolicy(
        path=resolved_path,
        policy_id=str(payload.get("policy_id") or resolved_path.stem),
        broad_excluded_labels=frozenset(
            normalize_source_label(item)
            for item in _string_list(payload.get("broad_excluded_labels"))
        ),
        ambiguous_context_labels=frozenset(
            normalize_source_label(item)
            for item in _string_list(payload.get("ambiguous_context_labels"))
        ),
        topic_confidence=_confidence_map(payload.get("topic_confidence")),
        category_confidence=_confidence_map(payload.get("category_confidence")),
        primary_translations=_translation_map(payload.get("primary_translations")),
        animal_translation_pattern=_compile_policy_pattern(payload, "animal_translation"),
        animal_gloss_pattern=_compile_policy_pattern(payload, "animal_gloss"),
        plant_translation_pattern=_compile_policy_pattern(payload, "plant_translation"),
        plant_gloss_pattern=_compile_policy_pattern(payload, "plant_gloss"),
    )


def normalize_source_label(value: object) -> str:
    text = str(value or "").strip()
    if ":" in text:
        prefix, suffix = text.split(":", 1)
        if prefix.lower() in {"es", "spanish"} and suffix.strip():
            text = suffix
    return _normalize_token(text)


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _confidence_map(value: object) -> dict[str, dict[str, float]]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, dict[str, float]] = {}
    for family, rows in value.items():
        if not isinstance(rows, Mapping):
            continue
        result[normalize_source_label(family)] = {
            normalize_source_label(label): _safe_float(confidence)
            for label, confidence in rows.items()
            if normalize_source_label(label)
        }
    return result


def _translation_map(value: object) -> dict[str, frozenset[str]]:
    if not isinstance(value, Mapping):
        return {}
    return {
        normalize_source_label(family): frozenset(
            str(item or "").strip().casefold()
            for item in _string_list(rows)
            if str(item or "").strip()
        )
        for family, rows in value.items()
    }


def _compile_policy_pattern(payload: Mapping[str, object], key: str) -> re.Pattern[str]:
    patterns = payload.get("patterns")
    pattern = patterns.get(key) if isinstance(patterns, Mapping) else ""
    return re.compile(str(pattern or r"(?!x)x"))


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_token(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    normalized = raw.replace("\\", "_").replace("/", "_").replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")
