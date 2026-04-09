from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
import re
from typing import Mapping, Sequence

from lexishift_core.replacement.core import RuleMetadata, VocabRule


_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


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
    return annotated


def build_semantic_inventory_from_results(
    *,
    results: Sequence[object],
    pair: str,
    profile_id: str,
    generated_at: str,
) -> dict[str, object]:
    triggers: dict[str, object] = {}
    senses: dict[str, object] = {}
    competition_sets: dict[str, object] = {}
    for raw_result in results:
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
        competition_set = _build_competition_set_record(semantic_admission)
        if competition_set is not None:
            competition_sets.setdefault(str(competition_set["competition_set_id"]), competition_set)
    return {
        "schema_version": 1,
        "pair": str(pair or "").strip(),
        "profile_id": str(profile_id or "").strip() or "default",
        "generated_at": str(generated_at or "").strip(),
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
    locator = _build_locator(
        metadata if isinstance(metadata, Mapping) else {},
        target=target,
        provider=source_dict,
    )
    if locator is None:
        return {
            "schema_version": 1,
            "status": "unavailable",
            "reason_code": "missing_sense_locator",
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
    metadata = getattr(candidate, "metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    locator = _build_locator(metadata, target=target, provider=source_dict)
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
) -> dict[str, object] | None:
    competition_set_id = str(semantic_admission.get("competition_set_id") or "").strip()
    trigger_id = str(semantic_admission.get("trigger_id") or "").strip()
    if not competition_set_id or not trigger_id:
        return None
    record: dict[str, object] = {
        "competition_set_id": competition_set_id,
        "trigger_id": trigger_id,
        "status": "unavailable",
        "reason_code": str(semantic_admission.get("reason_code") or "missing_shadow_selection"),
    }
    sense_id = str(semantic_admission.get("sense_id") or "").strip()
    if sense_id:
        record["active_sense_id"] = sense_id
    return record


def _build_locator(
    metadata: Mapping[str, object],
    *,
    target: str,
    provider: str,
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
    joined = "|".join(part for part in parts if part)
    return _stable_text_key(joined)


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
