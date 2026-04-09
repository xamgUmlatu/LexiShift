from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha1
import re
from typing import Mapping, Sequence

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.replacement.core import RuleMetadata, VocabRule


_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class _CompetitionPublicationContext:
    selection_mode: str
    selection_policy_version: str
    sense_ids: tuple[str, ...]


def normalize_semantic_admission_metadata(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key in (
        "schema_version",
        "status",
        "reason_code",
        "trigger_id",
        "sense_id",
        "competition_set_id",
        "phrase_set_id",
    ):
        raw = value.get(key)
        if raw is None:
            continue
        if key == "schema_version":
            if isinstance(raw, bool):
                continue
            if isinstance(raw, int):
                normalized[key] = int(raw)
                continue
            if isinstance(raw, str):
                text = raw.strip()
                if not text:
                    continue
                try:
                    normalized[key] = int(text)
                except ValueError:
                    continue
            continue
        text = str(raw or "").strip()
        if not text:
            continue
        normalized[key] = text
    return normalized or None


def annotate_results_with_semantic_admission(
    results: Sequence[object],
) -> list[object]:
    annotated: list[object] = []
    for raw_result in results:
        rule = getattr(raw_result, "rule", None)
        candidate = getattr(raw_result, "candidate", None)
        if not isinstance(rule, VocabRule) or candidate is None:
            annotated.append(raw_result)
            continue
        metadata = rule.metadata or RuleMetadata()
        if isinstance(metadata.semantic_admission, Mapping):
            annotated.append(raw_result)
            continue
        pointer = _build_semantic_admission_pointer(candidate)
        updated_rule = _replace_rule_semantic_admission(rule, pointer)
        try:
            annotated.append(replace(raw_result, rule=updated_rule))
        except TypeError:
            setattr(raw_result, "rule", updated_rule)
            annotated.append(raw_result)
    return _promote_ready_competition_results(annotated)


def build_semantic_inventory_from_results(
    *,
    results: Sequence[object],
    pair: str,
    profile_id: str,
    generated_at: str,
) -> dict[str, object]:
    annotated_results = annotate_results_with_semantic_admission(results)
    triggers: dict[str, object] = {}
    senses: dict[str, object] = {}
    competition_sets: dict[str, object] = {}
    competition_contexts = _build_ready_competition_contexts(annotated_results)
    for raw_result in annotated_results:
        rule = getattr(raw_result, "rule", None)
        candidate = getattr(raw_result, "candidate", None)
        if not isinstance(rule, VocabRule) or candidate is None:
            continue
        metadata = rule.metadata or RuleMetadata()
        semantic_admission = (
            dict(metadata.semantic_admission)
            if isinstance(metadata.semantic_admission, Mapping)
            else _build_semantic_admission_pointer(candidate)
        )
        trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
        if trigger_id:
            triggers.setdefault(
                trigger_id,
                {
                    "trigger_id": trigger_id,
                    "source_phrase": str(rule.source_phrase or "").strip(),
                    "normalized_source_phrase": _normalize_phrase(str(rule.source_phrase or "")),
                    "token_count": _token_count(str(rule.source_phrase or "")),
                },
            )
        sense_record = _build_sense_record(candidate, semantic_admission)
        if sense_record is not None:
            senses.setdefault(str(sense_record["sense_id"]), sense_record)
        pair_key = str(getattr(candidate, "language_pair", "") or "").strip()
        competition_set = _build_competition_set_record(
            semantic_admission,
            context=competition_contexts.get(
                (
                    pair_key,
                    str(semantic_admission.get("trigger_id") or "").strip(),
                )
            ),
        )
        if competition_set is not None:
            competition_sets.setdefault(str(competition_set["competition_set_id"]), competition_set)
    return {
        "schema_version": 1,
        "pair": str(pair or "").strip(),
        "profile_id": str(profile_id or "").strip() or "default",
        "generated_at": str(generated_at or "").strip(),
        "capability": _build_publication_capability_record(str(pair or "").strip()),
        "triggers": triggers,
        "senses": senses,
        "competition_sets": competition_sets,
        "phrase_sets": {},
    }


def _replace_rule_semantic_admission(
    rule: VocabRule, semantic_admission: Mapping[str, object]
) -> VocabRule:
    metadata = rule.metadata or RuleMetadata()
    updated_metadata = replace(
        metadata,
        semantic_admission={
            str(key): value for key, value in dict(semantic_admission).items() if str(key).strip()
        },
    )
    return replace(rule, metadata=updated_metadata)


def _build_semantic_admission_pointer(candidate: object) -> dict[str, object]:
    pair = str(getattr(candidate, "language_pair", "") or "").strip()
    source_phrase = str(getattr(candidate, "source_phrase", "") or "").strip()
    target = str(getattr(candidate, "replacement", "") or "").strip()
    source_dict = str(getattr(candidate, "source_dict", "") or "").strip()
    metadata = getattr(candidate, "metadata", {})
    trigger_id = _build_trigger_id(pair, source_phrase)
    capability = resolve_pair_capability(pair).semantic_publication
    locator = _build_locator(
        metadata if isinstance(metadata, Mapping) else {},
        target=target,
        provider=source_dict,
        locator_modes=capability.locator_modes,
    )
    if locator is None:
        return {
            "schema_version": 1,
            "status": "unavailable",
            "reason_code": capability.missing_locator_reason_code,
            "trigger_id": trigger_id,
        }
    sense_id = _build_sense_id(pair=pair, provider=source_dict, target=target, locator=locator)
    competition_set_id = _build_competition_set_id(
        pair=pair,
        trigger_id=trigger_id,
        target=target,
        sense_id=sense_id,
    )
    return {
        "schema_version": 1,
        "status": "unavailable",
        "reason_code": "missing_shadow_selection",
        "trigger_id": trigger_id,
        "sense_id": sense_id,
        "competition_set_id": competition_set_id,
    }


def _build_sense_record(
    candidate: object,
    semantic_admission: Mapping[str, object],
) -> dict[str, object] | None:
    sense_id = str(semantic_admission.get("sense_id") or "").strip()
    trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
    if not sense_id or not trigger_id:
        return None
    target = str(getattr(candidate, "replacement", "") or "").strip()
    source_dict = str(getattr(candidate, "source_dict", "") or "").strip()
    pair = str(getattr(candidate, "language_pair", "") or "").strip()
    metadata = getattr(candidate, "metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    locator = _build_locator(
        metadata,
        target=target,
        provider=source_dict,
        locator_modes=resolve_pair_capability(pair).semantic_publication.locator_modes,
    )
    if locator is None:
        return None
    qualifiers = _build_qualifiers(metadata)
    evidence_views = _build_evidence_views(metadata)
    record: dict[str, object] = {
        "sense_id": sense_id,
        "trigger_id": trigger_id,
        "status": "ready",
        "target_lemma": target,
        "sense_label": _build_sense_label(metadata, fallback=target),
        "provider": source_dict or "unknown",
        "locator": locator,
    }
    canonical_pos = _extract_canonical_pos(metadata)
    if canonical_pos:
        record["canonical_pos"] = canonical_pos
    if qualifiers:
        record["qualifiers"] = qualifiers
    if evidence_views:
        record["evidence_views"] = evidence_views
    return record


def _build_competition_set_record(
    semantic_admission: Mapping[str, object],
    *,
    context: _CompetitionPublicationContext | None = None,
) -> dict[str, object] | None:
    competition_set_id = str(semantic_admission.get("competition_set_id") or "").strip()
    trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
    if not competition_set_id or not trigger_id:
        return None
    active_sense_id = str(semantic_admission.get("sense_id") or "").strip()
    if context is not None and active_sense_id:
        shadow_sense_ids = [
            sense_id for sense_id in context.sense_ids if sense_id and sense_id != active_sense_id
        ]
        if shadow_sense_ids:
            return {
                "competition_set_id": competition_set_id,
                "trigger_id": trigger_id,
                "status": "ready",
                "active_sense_id": active_sense_id,
                "shadow_sense_ids": shadow_sense_ids,
                "selection_mode": context.selection_mode,
                "selection_policy_version": context.selection_policy_version,
            }
    record: dict[str, object] = {
        "competition_set_id": competition_set_id,
        "trigger_id": trigger_id,
        "status": "unavailable",
        "reason_code": str(semantic_admission.get("reason_code") or "missing_shadow_selection"),
    }
    if active_sense_id:
        record["active_sense_id"] = active_sense_id
    return record


def _build_locator(
    metadata: Mapping[str, object],
    *,
    target: str,
    provider: str,
    locator_modes: Sequence[str],
) -> dict[str, object] | None:
    for mode in locator_modes:
        if mode == "sense_provenance":
            locator = _build_sense_provenance_locator(metadata, provider=provider, target=target)
        elif mode == "freedict_gloss":
            locator = _build_freedict_gloss_locator(metadata, provider=provider, target=target)
        elif mode == "jmdict_entry":
            locator = _build_jmdict_entry_locator(metadata, provider=provider)
        else:
            locator = None
        if locator is not None:
            return locator
    return None


def _build_sense_provenance_locator(
    metadata: Mapping[str, object],
    *,
    provider: str,
    target: str,
) -> dict[str, object] | None:
    sense_provenance = metadata.get("sense_provenance")
    if not isinstance(sense_provenance, Mapping):
        return None
    provider_text = str(provider or "").strip() or "unknown"
    entry_ord = _as_int(sense_provenance.get("entry_ord"))
    sense_ord = _as_int(sense_provenance.get("sense_ord"))
    gloss_ord = _as_int(sense_provenance.get("gloss_ord"))
    if "wiktionary" in provider_text and entry_ord is not None and sense_ord is not None:
        locator: dict[str, object] = {
            "provider": provider_text,
            "locator_kind": "wiktionary_ordinal",
            "entry_ord": entry_ord,
            "sense_ord": sense_ord,
        }
        if gloss_ord is not None:
            locator["gloss_ord"] = gloss_ord
        return locator
    if "freedict" in provider_text and gloss_ord is not None:
        locator = {
            "provider": provider_text,
            "locator_kind": "freedict_gloss",
            "target_key": str(target or "").strip(),
            "gloss_ord": gloss_ord,
        }
        if entry_ord is not None:
            locator["entry_ord"] = entry_ord
        if sense_ord is not None:
            locator["sense_ord"] = sense_ord
        return locator
    return None


def _build_freedict_gloss_locator(
    metadata: Mapping[str, object],
    *,
    provider: str,
    target: str,
) -> dict[str, object] | None:
    provider_text = str(provider or "").strip() or "unknown"
    if "freedict" not in provider_text:
        return None
    gloss_index = _as_int(metadata.get("gloss_index"))
    target_key = str(target or "").strip()
    if gloss_index is None or not target_key:
        return None
    return {
        "provider": provider_text,
        "locator_kind": "freedict_gloss",
        "target_key": target_key,
        "gloss_ord": gloss_index,
    }


def _build_jmdict_entry_locator(
    metadata: Mapping[str, object],
    *,
    provider: str,
) -> dict[str, object] | None:
    provider_text = str(provider or "").strip() or "unknown"
    if "jmdict" not in provider_text:
        return None
    word_package = metadata.get("word_package")
    script_forms: Mapping[str, object] = {}
    reading = ""
    if isinstance(word_package, Mapping):
        raw_script_forms = word_package.get("script_forms")
        if isinstance(raw_script_forms, Mapping):
            script_forms = raw_script_forms
        reading = str(word_package.get("reading") or "").strip()
    kanji_forms = _unique_string_list(script_forms.get("kanji"))
    kana_forms = _unique_string_list(script_forms.get("kana"))
    if not kana_forms and reading:
        kana_forms = [reading]
    if not kanji_forms and not kana_forms:
        return None
    locator: dict[str, object] = {
        "provider": provider_text,
        "locator_kind": "jmdict_entry",
    }
    if kanji_forms:
        locator["kanji_forms"] = kanji_forms
    if kana_forms:
        locator["kana_forms"] = kana_forms
    return locator


def _build_sense_id(
    *,
    pair: str,
    provider: str,
    target: str,
    locator: Mapping[str, object],
) -> str:
    provider_key = _stable_text_key(provider)
    target_key = _stable_text_key(target)
    locator_key = _stable_locator_key(locator)
    return f"{pair}:sense:{provider_key}:{target_key}:{locator_key}"


def _build_trigger_id(pair: str, source_phrase: str) -> str:
    return f"{pair}:trigger:{_stable_text_key(source_phrase)}"


def _build_competition_set_id(
    *,
    pair: str,
    trigger_id: str,
    target: str,
    sense_id: str,
) -> str:
    trigger_key = trigger_id.split(":")[-1]
    return (
        f"{pair}:competition:{trigger_key}:{_stable_text_key(target)}:"
        f"{_stable_text_key(sense_id)}:v1"
    )


def _stable_locator_key(locator: Mapping[str, object]) -> str:
    parts: list[str] = [str(locator.get("locator_kind") or "").strip()]
    for key in ("entry_ord", "sense_ord", "gloss_ord", "target_key", "opaque_id"):
        raw = locator.get(key)
        if raw is None:
            continue
        parts.append(f"{key}={raw}")
    for key in ("kanji_forms", "kana_forms"):
        raw = locator.get(key)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            continue
        values = [str(item).strip() for item in raw if str(item).strip()]
        if values:
            parts.append(f"{key}={','.join(values)}")
    joined = "|".join(part for part in parts if part)
    return _stable_text_key(joined)


def _build_publication_capability_record(pair: str) -> dict[str, object]:
    capability = resolve_pair_capability(pair).semantic_publication
    return {
        "pointer_modes": list(capability.locator_modes) or ["trigger_only"],
        "default_unavailable_reason_code": capability.missing_locator_reason_code,
        "competition_mode": capability.competition_publication_mode,
        "competition_reason_code": capability.missing_competition_reason_code,
        "phrase_mode": "not_published",
        "phrase_reason_code": "missing_phrase_inventory",
    }


def _promote_ready_competition_results(results: Sequence[object]) -> list[object]:
    contexts = _build_ready_competition_contexts(results)
    if not contexts:
        return list(results)
    promoted: list[object] = []
    for raw_result in results:
        rule = getattr(raw_result, "rule", None)
        candidate = getattr(raw_result, "candidate", None)
        if not isinstance(rule, VocabRule) or candidate is None:
            promoted.append(raw_result)
            continue
        metadata = rule.metadata or RuleMetadata()
        semantic_admission = normalize_semantic_admission_metadata(metadata.semantic_admission)
        if semantic_admission is None:
            promoted.append(raw_result)
            continue
        pair = str(getattr(candidate, "language_pair", "") or "").strip()
        trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
        sense_id = str(semantic_admission.get("sense_id") or "").strip()
        context = contexts.get((pair, trigger_id))
        if context is None or not sense_id or sense_id not in context.sense_ids:
            promoted.append(raw_result)
            continue
        updated_admission = dict(semantic_admission)
        updated_admission["status"] = "ready"
        updated_admission.pop("reason_code", None)
        updated_rule = _replace_rule_semantic_admission(rule, updated_admission)
        try:
            promoted.append(replace(raw_result, rule=updated_rule))
        except TypeError:
            setattr(raw_result, "rule", updated_rule)
            promoted.append(raw_result)
    return promoted


def _build_ready_competition_contexts(
    results: Sequence[object],
) -> dict[tuple[str, str], _CompetitionPublicationContext]:
    grouped_sense_ids: dict[tuple[str, str], list[str]] = {}
    grouped_capabilities: dict[tuple[str, str], object] = {}
    for raw_result in results:
        rule = getattr(raw_result, "rule", None)
        candidate = getattr(raw_result, "candidate", None)
        if not isinstance(rule, VocabRule) or candidate is None:
            continue
        pair = str(getattr(candidate, "language_pair", "") or "").strip()
        capability = resolve_pair_capability(pair).semantic_publication
        if capability.competition_publication_mode != "emitted_rule_siblings":
            continue
        metadata = rule.metadata or RuleMetadata()
        semantic_admission = (
            normalize_semantic_admission_metadata(metadata.semantic_admission)
            if isinstance(metadata.semantic_admission, Mapping)
            else _build_semantic_admission_pointer(candidate)
        )
        if semantic_admission is None:
            continue
        trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
        sense_id = str(semantic_admission.get("sense_id") or "").strip()
        if not trigger_id or not sense_id:
            continue
        key = (pair, trigger_id)
        grouped_capabilities[key] = capability
        grouped_sense_ids.setdefault(key, [])
        if sense_id not in grouped_sense_ids[key]:
            grouped_sense_ids[key].append(sense_id)
    contexts: dict[tuple[str, str], _CompetitionPublicationContext] = {}
    for key, sense_ids in grouped_sense_ids.items():
        if len(sense_ids) <= 1:
            continue
        capability = grouped_capabilities[key]
        policy_version = str(
            capability.competition_selection_policy_version or "emitted_rule_siblings_v1"
        ).strip()
        contexts[key] = _CompetitionPublicationContext(
            selection_mode="automatic",
            selection_policy_version=policy_version,
            sense_ids=tuple(sense_ids),
        )
    return contexts


def _build_sense_label(metadata: Mapping[str, object], *, fallback: str) -> str:
    sense_provenance = metadata.get("sense_provenance")
    if isinstance(sense_provenance, Mapping):
        raw_glosses = sense_provenance.get("sense_raw_glosses")
        if isinstance(raw_glosses, Sequence) and not isinstance(raw_glosses, (str, bytes)):
            first = next((str(item).strip() for item in raw_glosses if str(item).strip()), "")
            if first:
                return first
    gloss_provenance = metadata.get("gloss_provenance")
    if isinstance(gloss_provenance, Mapping):
        for key in ("raw_gloss_text", "fragment_source_text", "fragment_emitted_text"):
            text = str(gloss_provenance.get(key) or "").strip()
            if text:
                return text
    return str(fallback or "").strip()


def _build_qualifiers(metadata: Mapping[str, object]) -> dict[str, object] | None:
    sense_provenance = metadata.get("sense_provenance")
    if not isinstance(sense_provenance, Mapping):
        return None
    qualifiers: dict[str, object] = {}
    for key in ("entry_tags", "sense_tags", "translation_tags"):
        values = _string_tuple(sense_provenance.get(key))
        if values:
            qualifiers.setdefault("tags", [])
            qualifiers["tags"].extend(values)
    topics = _string_tuple(sense_provenance.get("sense_topics"))
    if topics:
        qualifiers["topics"] = list(dict.fromkeys(topics))
    categories = _string_tuple(sense_provenance.get("entry_categories")) + _string_tuple(
        sense_provenance.get("sense_categories")
    )
    if categories:
        qualifiers["categories"] = list(dict.fromkeys(categories))
    if "tags" in qualifiers:
        qualifiers["tags"] = list(dict.fromkeys(qualifiers["tags"]))
    return qualifiers or None


def _build_evidence_views(metadata: Mapping[str, object]) -> dict[str, str] | None:
    views: dict[str, str] = {}
    sense_label = _build_sense_label(metadata, fallback="")
    if sense_label:
        views["sense_label"] = sense_label
    sense_provenance = metadata.get("sense_provenance")
    if isinstance(sense_provenance, Mapping):
        raw_glosses = _string_tuple(sense_provenance.get("sense_raw_glosses"))
        if raw_glosses:
            views["sense_gloss_bundle"] = " | ".join(raw_glosses)
    gloss_provenance = metadata.get("gloss_provenance")
    if isinstance(gloss_provenance, Mapping):
        raw_gloss_text = str(gloss_provenance.get("raw_gloss_text") or "").strip()
        if raw_gloss_text:
            views["gloss_text"] = raw_gloss_text
    qualifier_text = _build_qualifier_text(metadata)
    if qualifier_text:
        views["qualifier_text"] = qualifier_text
    all_evidence_parts = [
        views.get("sense_gloss_bundle") or views.get("sense_label"),
        views.get("gloss_text"),
        qualifier_text,
    ]
    all_evidence_text = " | ".join(part for part in all_evidence_parts if part)
    if all_evidence_text:
        views["all_evidence_text"] = all_evidence_text
    return views or None


def _build_qualifier_text(metadata: Mapping[str, object]) -> str:
    qualifiers = _build_qualifiers(metadata)
    if not qualifiers:
        return ""
    parts: list[str] = []
    tags = qualifiers.get("tags")
    if isinstance(tags, Sequence) and not isinstance(tags, (str, bytes)) and tags:
        parts.append("tags: " + ", ".join(str(item).strip() for item in tags if str(item).strip()))
    topics = qualifiers.get("topics")
    if isinstance(topics, Sequence) and not isinstance(topics, (str, bytes)) and topics:
        parts.append(
            "topics: " + ", ".join(str(item).strip() for item in topics if str(item).strip())
        )
    categories = qualifiers.get("categories")
    if isinstance(categories, Sequence) and not isinstance(categories, (str, bytes)) and categories:
        parts.append(
            "categories: "
            + ", ".join(str(item).strip() for item in categories if str(item).strip())
        )
    return " ; ".join(part for part in parts if part)


def _extract_canonical_pos(metadata: Mapping[str, object]) -> str:
    pos = metadata.get("pos")
    if not isinstance(pos, Mapping):
        return ""
    for key in ("target", "dictionary", "source"):
        component = pos.get(key)
        if not isinstance(component, Mapping):
            continue
        canonical = str(component.get("canonical") or "").strip().lower()
        if canonical:
            return canonical
    sense_provenance = metadata.get("sense_provenance")
    if isinstance(sense_provenance, Mapping):
        canonical = str(sense_provenance.get("dictionary_pos_canonical") or "").strip().lower()
        if canonical:
            return canonical
    return ""


def _normalize_phrase(text: str) -> str:
    return " ".join(str(text or "").strip().lower().split())


def _token_count(text: str) -> int:
    matches = _WORD_RE.findall(str(text or ""))
    return max(1, len(matches)) if str(text or "").strip() else 1


def _stable_text_key(text: str) -> str:
    normalized = _normalize_phrase(text)
    slug = _SLUG_RE.sub("_", normalized).strip("_")
    digest = sha1(normalized.encode("utf-8")).hexdigest()[:8]
    if slug:
        return f"{slug}-{digest}"
    return digest


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _unique_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        text = str(value or "").strip()
        items = [text] if text else []
    return list(dict.fromkeys(items))
