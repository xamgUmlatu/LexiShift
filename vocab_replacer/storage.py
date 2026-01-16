from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .core import MeaningRule, RuleMetadata, VocabPool, VocabRule
from .inflect import InflectionOverrides, InflectionSpec


@dataclass(frozen=True)
class InflectionSettings:
    enabled: bool = True
    spec: InflectionSpec = field(default_factory=InflectionSpec)
    per_rule_spec: Mapping[str, InflectionSpec] = field(default_factory=dict)
    strict: bool = True
    overrides: InflectionOverrides = field(default_factory=InflectionOverrides)
    include_generated_tag: bool = True
    generated_tag: str = "generated"


@dataclass(frozen=True)
class LearningSettings:
    enabled: bool = False
    show_original: bool = True
    show_original_mode: str = "tooltip"  # tooltip, inline, side-by-side
    highlight_replacements: bool = True


@dataclass(frozen=True)
class VocabSettings:
    inflections: Optional[InflectionSettings] = None
    learning: Optional[LearningSettings] = None


@dataclass(frozen=True)
class VocabDataset:
    rules: Sequence[VocabRule] = field(default_factory=tuple)
    meaning_rules: Sequence[MeaningRule] = field(default_factory=tuple)
    synonyms: Mapping[str, str] = field(default_factory=dict)
    version: int = 1
    settings: Optional[VocabSettings] = None


def load_vocab_dataset(path: str | Path) -> VocabDataset:
    payload = Path(path).read_text(encoding="utf-8")
    data = json.loads(payload)
    return dataset_from_dict(data)


def save_vocab_dataset(dataset: VocabDataset, path: str | Path) -> None:
    data = dataset_to_dict(dataset)
    payload = json.dumps(data, indent=2, sort_keys=True)
    Path(path).write_text(payload, encoding="utf-8")


def load_vocab_pool(path: str | Path) -> VocabPool:
    dataset = load_vocab_dataset(path)
    return VocabPool(dataset.rules)


def save_vocab_pool(pool: VocabPool, path: str | Path) -> None:
    dataset = VocabDataset(rules=pool.rules)
    save_vocab_dataset(dataset, path)


def dataset_from_dict(data: Mapping[str, Any]) -> VocabDataset:
    version = int(data.get("version", 1))
    rules = [_rule_from_dict(item) for item in data.get("rules", [])]
    meaning_rules = [_meaning_rule_from_dict(item) for item in data.get("meaning_rules", [])]
    synonyms = dict(data.get("synonyms", {}))
    settings = _settings_from_dict(data.get("settings"))
    return VocabDataset(
        rules=tuple(rules),
        meaning_rules=tuple(meaning_rules),
        synonyms=synonyms,
        version=version,
        settings=settings,
    )


def dataset_to_dict(dataset: VocabDataset) -> dict[str, Any]:
    data = {
        "version": dataset.version,
        "rules": [_rule_to_dict(rule) for rule in dataset.rules],
        "meaning_rules": [_meaning_rule_to_dict(rule) for rule in dataset.meaning_rules],
        "synonyms": dict(dataset.synonyms),
    }
    settings = _settings_to_dict(dataset.settings)
    if settings:
        data["settings"] = settings
    return data


def _metadata_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[RuleMetadata]:
    if not data:
        return None
    examples = tuple(str(item) for item in data.get("examples", []))
    return RuleMetadata(
        label=data.get("label"),
        description=data.get("description"),
        examples=examples,
        notes=data.get("notes"),
        source=data.get("source"),
    )


def _metadata_to_dict(metadata: Optional[RuleMetadata]) -> Optional[dict[str, Any]]:
    if metadata is None:
        return None
    data: dict[str, Any] = {
        "label": metadata.label,
        "description": metadata.description,
        "examples": list(metadata.examples),
        "notes": metadata.notes,
        "source": metadata.source,
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, [])}
    return trimmed or None


def _rule_from_dict(data: Mapping[str, Any]) -> VocabRule:
    return VocabRule(
        source_phrase=str(data.get("source_phrase", "")),
        replacement=str(data.get("replacement", "")),
        priority=int(data.get("priority", 0)),
        case_policy=str(data.get("case_policy", "match")),
        enabled=bool(data.get("enabled", True)),
        tags=tuple(data.get("tags", [])),
        metadata=_metadata_from_dict(data.get("metadata")),
    )


def _rule_to_dict(rule: VocabRule) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source_phrase": rule.source_phrase,
        "replacement": rule.replacement,
        "priority": rule.priority,
        "case_policy": rule.case_policy,
        "enabled": rule.enabled,
        "tags": list(rule.tags),
    }
    metadata = _metadata_to_dict(rule.metadata)
    if metadata:
        data["metadata"] = metadata
    return data


def _meaning_rule_from_dict(data: Mapping[str, Any]) -> MeaningRule:
    source_phrases = tuple(str(item) for item in data.get("source_phrases", []))
    return MeaningRule(
        source_phrases=source_phrases,
        replacement=str(data.get("replacement", "")),
        priority=int(data.get("priority", 0)),
        case_policy=str(data.get("case_policy", "match")),
        enabled=bool(data.get("enabled", True)),
        tags=tuple(data.get("tags", [])),
        metadata=_metadata_from_dict(data.get("metadata")),
    )


def _meaning_rule_to_dict(rule: MeaningRule) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source_phrases": list(rule.source_phrases),
        "replacement": rule.replacement,
        "priority": rule.priority,
        "case_policy": rule.case_policy,
        "enabled": rule.enabled,
        "tags": list(rule.tags),
    }
    metadata = _metadata_to_dict(rule.metadata)
    if metadata:
        data["metadata"] = metadata
    return data


def _settings_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[VocabSettings]:
    if not data:
        return None
    return VocabSettings(
        inflections=_inflection_settings_from_dict(data.get("inflections")),
        learning=_learning_settings_from_dict(data.get("learning")),
    )


def _settings_to_dict(settings: Optional[VocabSettings]) -> Optional[dict[str, Any]]:
    if settings is None:
        return None
    data: dict[str, Any] = {}
    inflections = _inflection_settings_to_dict(settings.inflections)
    if inflections:
        data["inflections"] = inflections
    learning = _learning_settings_to_dict(settings.learning)
    if learning:
        data["learning"] = learning
    return data or None


def _inflection_settings_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[InflectionSettings]:
    if not data:
        return None
    return InflectionSettings(
        enabled=bool(data.get("enabled", True)),
        spec=_inflection_spec_from_dict(data.get("spec")),
        per_rule_spec=_inflection_spec_map_from_dict(data.get("per_rule_spec", {})),
        strict=bool(data.get("strict", True)),
        overrides=_inflection_overrides_from_dict(data.get("overrides")),
        include_generated_tag=bool(data.get("include_generated_tag", True)),
        generated_tag=str(data.get("generated_tag", "generated")),
    )


def _inflection_settings_to_dict(settings: Optional[InflectionSettings]) -> Optional[dict[str, Any]]:
    if settings is None:
        return None
    data: dict[str, Any] = {
        "enabled": settings.enabled,
        "spec": _inflection_spec_to_dict(settings.spec),
        "per_rule_spec": _inflection_spec_map_to_dict(settings.per_rule_spec),
        "strict": settings.strict,
        "overrides": _inflection_overrides_to_dict(settings.overrides),
        "include_generated_tag": settings.include_generated_tag,
        "generated_tag": settings.generated_tag,
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, {}, [])}
    return trimmed or None


def _learning_settings_from_dict(data: Optional[Mapping[str, Any]]) -> Optional[LearningSettings]:
    if not data:
        return None
    return LearningSettings(
        enabled=bool(data.get("enabled", False)),
        show_original=bool(data.get("show_original", True)),
        show_original_mode=str(data.get("show_original_mode", "tooltip")),
        highlight_replacements=bool(data.get("highlight_replacements", True)),
    )


def _learning_settings_to_dict(settings: Optional[LearningSettings]) -> Optional[dict[str, Any]]:
    if settings is None:
        return None
    data: dict[str, Any] = {
        "enabled": settings.enabled,
        "show_original": settings.show_original,
        "show_original_mode": settings.show_original_mode,
        "highlight_replacements": settings.highlight_replacements,
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, [])}
    return trimmed or None


def _inflection_spec_from_dict(data: Optional[Mapping[str, Any]]) -> InflectionSpec:
    if not data:
        return InflectionSpec()
    forms_data = data.get("forms")
    forms = InflectionSpec().forms if forms_data is None else frozenset(str(item) for item in forms_data)
    return InflectionSpec(
        forms=forms,
        apply_to=str(data.get("apply_to", "last_word")),
        include_original=bool(data.get("include_original", True)),
    )


def _inflection_spec_to_dict(spec: InflectionSpec) -> dict[str, Any]:
    return {
        "forms": sorted(spec.forms),
        "apply_to": spec.apply_to,
        "include_original": spec.include_original,
    }


def _inflection_spec_map_from_dict(data: Mapping[str, Any]) -> dict[str, InflectionSpec]:
    return {key: _inflection_spec_from_dict(value) for key, value in data.items()}


def _inflection_spec_map_to_dict(data: Mapping[str, InflectionSpec]) -> dict[str, Any]:
    return {key: _inflection_spec_to_dict(value) for key, value in data.items()}


def _inflection_overrides_from_dict(data: Optional[Mapping[str, Any]]) -> InflectionOverrides:
    if not data:
        return InflectionOverrides()
    return InflectionOverrides(
        plurals=dict(data.get("plurals", {})),
        past=dict(data.get("past", {})),
        gerunds=dict(data.get("gerunds", {})),
        third_person=dict(data.get("third_person", {})),
        blocked=frozenset(data.get("blocked", [])),
    )


def _inflection_overrides_to_dict(overrides: InflectionOverrides) -> Optional[dict[str, Any]]:
    data: dict[str, Any] = {
        "plurals": dict(overrides.plurals),
        "past": dict(overrides.past),
        "gerunds": dict(overrides.gerunds),
        "third_person": dict(overrides.third_person),
        "blocked": sorted(overrides.blocked),
    }
    trimmed = {key: value for key, value in data.items() if value not in (None, {}, [])}
    return trimmed or None


def build_options_from_settings(settings: Optional[VocabSettings]):
    if not settings or not settings.inflections or not settings.inflections.enabled:
        return None
    from .builder import BuildOptions
    from .inflect import InflectionGenerator

    inflections = settings.inflections
    generator = InflectionGenerator(overrides=inflections.overrides, strict=inflections.strict)
    return BuildOptions(
        inflection_spec=inflections.spec,
        inflection_overrides=inflections.per_rule_spec,
        inflection_generator=generator,
        include_generated_tag=inflections.include_generated_tag,
        generated_tag=inflections.generated_tag,
    )


def build_vocab_pool_from_dataset(
    dataset: VocabDataset,
    *,
    tokenizer=None,
    normalizer=None,
) -> VocabPool:
    from .builder import build_vocab_pool

    options = build_options_from_settings(dataset.settings)
    return build_vocab_pool(dataset.rules, options=options, tokenizer=tokenizer, normalizer=normalizer)
