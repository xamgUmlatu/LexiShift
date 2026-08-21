from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import quote

from lexishift_core.helper.lp_capabilities import (
    default_jmdict_path,
    normalize_pair_key,
    resolve_pair_capability,
)
from lexishift_core.helper.lookup_dictionary_settings import (
    load_lookup_dictionary_settings,
    lookup_dictionary_pack_ids_for_pair,
)
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.use_cases.word_info_dictionary import (
    dictionary_metadata_for_path,
    jmdict_gloss_records_for_candidates,
    matched_headword,
    records_for_candidates,
    translation_dictionary_match,
    translation_dictionary_metadata,
)
from lexishift_core.helper.use_cases.word_info_identity import (
    find_srs_item,
    lookup_japanese_reading,
)
from lexishift_core.helper.use_cases.word_info_senses import (
    build_jmdict_sense_payloads,
    build_translation_sense_payloads,
)
from lexishift_core.helper.use_cases.word_info_jmdict import (
    jmdict_entries_for_candidates,
    jmdict_gloss_records,
    select_jmdict_definition_entries,
)
from lexishift_core.lexicon.word_package import normalize_word_package
from lexishift_core.persistence.storage import load_vocab_dataset
from lexishift_core.resources.dict_loaders import (
    JmdictEntryRecord,
    TranslationGlossRecord,
    load_translation_gloss_records_ordered,
)
from lexishift_core.resources.jmdict_definition_lookup import (
    load_jmdict_definition_records_for_terms,
)
from lexishift_core.resources.installed_packs import resolve_installed_pack_artifact
from lexishift_core.srs import normalize_srs_lifecycle_state
from lexishift_core.helper.yomitan_lookup_dictionaries import lookup_yomitan_dictionary


GLOSS_LIMIT = 5
SENSE_LIMIT = 5
DETAIL_LIMIT = 2
EXAMPLE_LIMIT = 1
LABEL_LIMIT = 4
SOURCE_PHRASE_LIMIT = 5
RESTRICTED_USAGE_TAGS = {
    "derogatory",
    "offensive",
    "obsolete",
    "slang",
    "vulgar",
}


def lookup_word_info(
    paths: HelperPaths,
    *,
    pair: str,
    lemma: str,
    profile_id: str = "default",
    display: str = "",
    origin: str = "",
    source_phrase: str = "",
    word_package: Mapping[str, object] | None = None,
    translation_dict_path: Path | None = None,
    jmdict_path: Path | None = None,
    resolve_profile_id_fn: Callable[..., str],
) -> dict[str, object]:
    normalized_pair = normalize_pair_key(pair, default="")
    if not normalized_pair:
        raise ValueError("Missing pair.")
    source_language, target_language = _split_pair(normalized_pair)
    normalized_lemma = _normalize_lemma(lemma)
    if not normalized_lemma:
        raise ValueError("Missing lemma.")

    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    request_word_package = _normalize_package(
        word_package,
        fallback_surface=display or lemma,
        fallback_language_tag=target_language,
        fallback_provider="request",
    )
    srs_item = find_srs_item(
        paths,
        profile_id=normalized_profile_id,
        pair=normalized_pair,
        normalized_lemma=normalized_lemma,
        request_word_package=request_word_package,
    )
    srs_word_package = _normalize_package(
        getattr(srs_item, "word_package", None),
        fallback_surface=getattr(srs_item, "lemma", "") if srs_item is not None else "",
        fallback_language_tag=target_language,
        fallback_provider=getattr(srs_item, "source_type", "") if srs_item is not None else "",
    )
    primary_word_package = request_word_package or srs_word_package or {}
    resolved_display = _first_text(
        display,
        primary_word_package.get("surface") if isinstance(primary_word_package, Mapping) else "",
        lemma,
    )
    lookup_candidates = _lookup_candidates(
        lemma=lemma,
        display=resolved_display,
        request_word_package=request_word_package,
        srs_word_package=srs_word_package,
    )
    lookup_surface = _first_text(primary_word_package.get("surface"), lemma, resolved_display)
    lookup_reading = lookup_japanese_reading(
        primary_word_package,
        target_language=target_language,
        surface=lookup_surface,
    )
    rule_summary = _rule_summary(
        paths,
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        normalized_lemma=normalized_lemma,
        source_phrase=source_phrase,
    )
    gloss_payload, sense_payload, gloss_diagnostics = _resolve_glosses(
        paths,
        pair=normalized_pair,
        source_language=source_language,
        target_language=target_language,
        lookup_candidates=lookup_candidates,
        lookup_surface=lookup_surface,
        lookup_reading=lookup_reading,
        translation_dict_path=translation_dict_path,
        jmdict_path=jmdict_path,
    )

    safe_word_package = _safe_word_package(primary_word_package)
    diagnostics = {
        "resolution_sources": _resolution_sources(
            srs_item=srs_item,
            rule_summary=rule_summary,
            glosses=gloss_payload,
        ),
        "missing_resources": gloss_diagnostics["missing_resources"],
        "provider_status": gloss_diagnostics["provider_status"],
    }
    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "source_language": source_language,
        "target_language": target_language,
        "lemma": str(lemma or "").strip(),
        "display": resolved_display,
        "normalized_lemma": normalized_lemma,
        "origin": str(origin or "").strip().lower(),
        "pos": _pos_payload(primary_word_package, gloss_payload),
        "glosses": gloss_payload,
        "senses": sense_payload,
        "dictionary": gloss_diagnostics.get("dictionary"),
        "dictionary_match": gloss_diagnostics.get("dictionary_match"),
        "source_phrases": rule_summary["source_phrases"],
        "rule_summary": {
            "rule_count": rule_summary["rule_count"],
            "enabled_rule_count": rule_summary["enabled_rule_count"],
            "source_phrase_count": rule_summary["source_phrase_count"],
            "source_preview_truncated": rule_summary["source_preview_truncated"],
        },
        "srs": _srs_payload(srs_item),
        "word_package": safe_word_package or None,
        "external_links": _external_links(
            lemma=normalized_lemma,
            display=resolved_display,
            target_language=target_language,
        ),
        "diagnostics": diagnostics,
    }


def _split_pair(pair: str) -> tuple[str, str]:
    left, sep, right = normalize_pair_key(pair, default="").partition("-")
    if not sep or not left or not right:
        return "", ""
    return left, right


def _normalize_lemma(value: object) -> str:
    return str(value or "").strip().casefold()


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _normalize_package(
    value: object,
    *,
    fallback_surface: str,
    fallback_language_tag: str,
    fallback_provider: str,
) -> dict[str, object]:
    package = normalize_word_package(
        value,
        fallback_surface=fallback_surface,
        fallback_language_tag=fallback_language_tag,
        fallback_provider=fallback_provider,
    )
    return dict(package or {})


def _safe_word_package(value: Mapping[str, object]) -> dict[str, object]:
    safe = _safe_payload_value(value)
    return safe if isinstance(safe, dict) else {}


def _safe_payload_value(value: object) -> object:
    if isinstance(value, Mapping):
        payload: dict[str, object] = {}
        for key, raw in value.items():
            safe_key = str(key or "").strip()
            if not safe_key or _is_local_resource_key(safe_key):
                continue
            payload[safe_key] = _safe_payload_value(raw)
        return payload
    if isinstance(value, (list, tuple)):
        return [_safe_payload_value(item) for item in value]
    return value


def _is_local_resource_key(key: str) -> bool:
    normalized = str(key or "").strip().lower()
    return "path" in normalized or normalized.endswith("_dir") or normalized == "dir"


def _lookup_candidates(
    *,
    lemma: str,
    display: str,
    request_word_package: Mapping[str, object],
    srs_word_package: Mapping[str, object],
) -> tuple[str, ...]:
    ordered: list[str] = []

    def add(value: object) -> None:
        text = str(value or "").strip()
        if not text:
            return
        normalized = text.casefold()
        if normalized in {_normalize_lemma(item) for item in ordered}:
            return
        ordered.append(text)

    add(lemma)
    add(display)
    for package in (srs_word_package, request_word_package):
        if not isinstance(package, Mapping):
            continue
        add(package.get("surface"))
        add(package.get("reading"))
        script_forms = package.get("script_forms")
        if isinstance(script_forms, Mapping):
            for value in script_forms.values():
                add(value)
    return tuple(ordered)


def _rule_summary(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str,
    normalized_lemma: str,
    source_phrase: str,
) -> dict[str, object]:
    ruleset_path = paths.ruleset_path(pair, profile_id=profile_id)
    source_phrases: list[str] = []
    enabled_count = 0
    total_count = 0
    if ruleset_path.exists():
        try:
            dataset = load_vocab_dataset(ruleset_path)
        except Exception:  # pragma: no cover - defensive read-only endpoint
            dataset = None
        if dataset is not None:
            for rule in dataset.rules:
                if _normalize_lemma(getattr(rule, "replacement", "")) != normalized_lemma:
                    continue
                total_count += 1
                if getattr(rule, "enabled", True) is False:
                    continue
                enabled_count += 1
                _append_unique(source_phrases, getattr(rule, "source_phrase", ""))
    _append_unique(source_phrases, source_phrase)
    truncated = len(source_phrases) > SOURCE_PHRASE_LIMIT
    return {
        "rule_count": total_count,
        "enabled_rule_count": enabled_count,
        "source_phrases": source_phrases[:SOURCE_PHRASE_LIMIT],
        "source_phrase_count": len(source_phrases),
        "source_preview_truncated": truncated,
    }


def _append_unique(values: list[str], value: object) -> None:
    text = str(value or "").strip()
    if not text:
        return
    if text.casefold() in {item.casefold() for item in values}:
        return
    values.append(text)


def _resolve_glosses(
    paths: HelperPaths,
    *,
    pair: str,
    source_language: str,
    target_language: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
    translation_dict_path: Path | None,
    jmdict_path: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    configured_lookup = _resolve_configured_lookup_dictionary(
        paths,
        pair=pair,
        lookup_candidates=lookup_candidates,
        lookup_surface=lookup_surface,
        lookup_reading=lookup_reading,
    )
    if configured_lookup is not None:
        return configured_lookup
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen or capability.requires_jmdict_for_seed:
        return _resolve_jmdict_glosses(
            paths,
            pair=pair,
            source_language=source_language,
            lookup_candidates=lookup_candidates,
            lookup_surface=lookup_surface,
            lookup_reading=lookup_reading,
            jmdict_path=jmdict_path,
        )
    if capability.requires_translation_dictionary_for_rulegen:
        return _resolve_translation_glosses(
            paths,
            pair=pair,
            source_language=source_language,
            lookup_candidates=lookup_candidates,
            lookup_surface=lookup_surface,
            translation_dict_path=translation_dict_path,
        )
    return (
        [],
        [],
        {
            "provider_status": "unsupported_pair",
            "missing_resources": [{"type": "word_info_provider", "reason": "pair_lacks_provider"}],
        },
    )


def _resolve_configured_lookup_dictionary(
    paths: HelperPaths,
    *,
    pair: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]] | None:
    settings = load_lookup_dictionary_settings(paths.lookup_dictionary_settings_path)
    pack_ids = lookup_dictionary_pack_ids_for_pair(settings, pair)
    for pack_id in pack_ids:
        artifact_path = resolve_installed_pack_artifact(
            paths.lookup_dictionary_packs_dir,
            pack_id,
        )
        if artifact_path is None:
            continue
        result = lookup_yomitan_dictionary(
            artifact_path,
            lookup_candidates=lookup_candidates,
            surface=lookup_surface,
            reading=lookup_reading,
            sense_limit=SENSE_LIMIT,
            gloss_limit=GLOSS_LIMIT,
        )
        if result is None:
            continue
        return (
            list(result.glosses),
            list(result.senses),
            {
                "provider_status": "ok",
                "missing_resources": [],
                "dictionary": result.dictionary,
                "dictionary_match": result.dictionary_match,
            },
        )
    return None


def _resolve_translation_glosses(
    paths: HelperPaths,
    *,
    pair: str,
    source_language: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    translation_dict_path: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    resolved_pack, _reverse_pack = resolve_pair_translation_packs(
        paths,
        pair=pair,
        translation_dict_path=translation_dict_path,
    )
    if resolved_pack is None or not resolved_pack.path.exists():
        return (
            [],
            [],
            {
                "provider_status": "missing_translation_pack",
                "missing_resources": [
                    {
                        "type": "translation_pack",
                        "reason": "missing",
                        "pack_id": resolved_pack.pack_id if resolved_pack is not None else "",
                    }
                ],
            },
        )
    records_by_headword = load_translation_gloss_records_ordered(
        resolved_pack.path,
        target_lang=source_language,
        headwords=lookup_candidates,
    )
    records = records_for_candidates(records_by_headword, lookup_candidates)
    resolved_headword = matched_headword(records_by_headword, lookup_candidates)
    payload_options = {
        "language": source_language,
        "source": resolved_pack.pack_id,
        "source_kind": "installed_translation_pack",
    }
    return (
        _gloss_payloads(records, **payload_options),
        build_translation_sense_payloads(
            _presentation_records(records),
            **payload_options,
            sense_limit=SENSE_LIMIT,
            detail_limit=DETAIL_LIMIT,
            example_limit=EXAMPLE_LIMIT,
            label_limit=LABEL_LIMIT,
        ),
        {
            "provider_status": "ok",
            "missing_resources": [],
            "dictionary": translation_dictionary_metadata(resolved_pack),
            "dictionary_match": translation_dictionary_match(
                resolved_headword,
                lookup_surface=lookup_surface,
            ),
        },
    )


def _resolve_jmdict_glosses(
    paths: HelperPaths,
    *,
    pair: str,
    source_language: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
    jmdict_path: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    resolved_path = jmdict_path or default_jmdict_path(
        pair, language_packs_dir=paths.language_packs_dir
    )
    if resolved_path is None or not resolved_path.exists():
        return (
            [],
            [],
            {
                "provider_status": "missing_jmdict",
                "missing_resources": [{"type": "jmdict", "reason": "missing", "pack_id": "jmdict"}],
            },
        )
    entries_by_headword, glosses_by_headword = _load_cached_jmdict_definition_data(
        resolved_path,
        lookup_candidates,
    )
    entries = jmdict_entries_for_candidates(entries_by_headword, lookup_candidates)
    selection = select_jmdict_definition_entries(
        entries,
        surface=lookup_surface,
        reading=lookup_reading,
    )
    records = jmdict_gloss_records(selection.entries)
    if not records:
        records = jmdict_gloss_records_for_candidates(glosses_by_headword, lookup_candidates)
    return (
        _gloss_payloads(
            records,
            language=source_language or "en",
            source="jmdict",
            source_kind="installed_jmdict",
        ),
        build_jmdict_sense_payloads(
            selection.entries,
            language=source_language or "en",
            source="jmdict",
            source_kind="installed_jmdict",
            sense_limit=SENSE_LIMIT,
            detail_limit=DETAIL_LIMIT,
            label_limit=LABEL_LIMIT,
        ),
        {
            "provider_status": "ok",
            "missing_resources": [],
            "dictionary": dictionary_metadata_for_path(
                resolved_path,
                fallback_pack_id="jmdict-ja-en",
                fallback_provider="edrdg",
                source_kind="installed_jmdict",
            ),
            "dictionary_match": {
                "surface": selection.matched_surface,
                "reading": selection.matched_reading,
                "quality": selection.match_quality,
            },
        },
    )


@lru_cache(maxsize=128)
def _load_jmdict_definition_data_cached(
    path_value: str,
    mtime_ns: int,
    size: int,
    lookup_candidates: tuple[str, ...],
) -> tuple[
    Mapping[str, Sequence[JmdictEntryRecord]],
    Mapping[str, list[str]],
]:
    del mtime_ns, size
    return load_jmdict_definition_records_for_terms(
        Path(path_value),
        lookup_candidates,
    )


def _load_cached_jmdict_definition_data(
    path: Path,
    lookup_candidates: Sequence[str],
) -> tuple[
    Mapping[str, Sequence[JmdictEntryRecord]],
    Mapping[str, list[str]],
]:
    stat = path.stat()
    return _load_jmdict_definition_data_cached(
        str(path),
        int(stat.st_mtime_ns),
        int(stat.st_size),
        tuple(
            dict.fromkeys(
                normalized
                for candidate in lookup_candidates
                if (normalized := _normalize_lemma(candidate))
            )
        ),
    )


def _gloss_payloads(
    records: Sequence[TranslationGlossRecord],
    *,
    language: str,
    source: str,
    source_kind: str,
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in _presentation_records(records):
        raw_text = str(record.translation or "").strip()
        if not raw_text:
            continue
        text, inline_detail = _split_inline_gloss_detail(raw_text)
        dedupe_key = raw_text.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        payload: dict[str, object] = {
            "text": text,
            "language": str(language or "").strip(),
            "source": str(source or "").strip(),
            "source_kind": source_kind,
            "rank": len(payloads) + 1,
            "confidence": 0.9,
        }
        pos_raw = str(getattr(record, "pos_raw", "") or "").strip()
        if pos_raw:
            payload["pos"] = pos_raw
        sense_id = _record_sense_id(record)
        if sense_id:
            payload["sense_id"] = sense_id
        metadata = _record_metadata(record)
        details = _sense_details(metadata, fallback_text=text)
        if inline_detail:
            _prepend_unique(details, inline_detail, limit=DETAIL_LIMIT)
        if details:
            payload["details"] = details
        examples = _sense_examples(metadata)
        if examples:
            payload["examples"] = examples
        payloads.append(payload)
        if len(payloads) >= GLOSS_LIMIT:
            break
    return payloads


def _presentation_records(
    records: Sequence[TranslationGlossRecord],
) -> Sequence[TranslationGlossRecord]:
    unrestricted_records = [record for record in records if not _has_restricted_usage(record)]
    return _primary_pos_records(unrestricted_records or records)


def _record_metadata(record: TranslationGlossRecord) -> Mapping[str, object]:
    metadata = getattr(record, "metadata", None)
    return metadata if isinstance(metadata, Mapping) else {}


def _has_restricted_usage(record: TranslationGlossRecord) -> bool:
    metadata = _record_metadata(record)
    values: list[str] = []
    for key in ("sense_tags", "entry_tags", "translation_tags"):
        values.extend(_string_items(metadata.get(key)))
    return any(value.casefold() in RESTRICTED_USAGE_TAGS for value in values)


def _primary_pos_records(
    records: Sequence[TranslationGlossRecord],
) -> Sequence[TranslationGlossRecord]:
    primary_pos = ""
    for record in records:
        pos_raw = str(getattr(record, "pos_raw", "") or "").strip().casefold()
        if pos_raw:
            primary_pos = pos_raw
            break
    if not primary_pos:
        return records
    filtered = [
        record
        for record in records
        if str(getattr(record, "pos_raw", "") or "").strip().casefold() == primary_pos
    ]
    return filtered or records


def _record_sense_id(record: TranslationGlossRecord) -> str:
    metadata = _record_metadata(record)
    parts: list[str] = []
    for key in ("entry_ord", "sense_ord", "gloss_ord"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            parts.append(f"{key}:{value}")
    return "|".join(parts)


def _sense_details(metadata: Mapping[str, object], *, fallback_text: str) -> list[str]:
    details: list[str] = []
    fallback_normalized = str(fallback_text or "").strip().casefold()
    for value in _string_items(metadata.get("sense_raw_glosses")):
        normalized = value.casefold()
        if not normalized or normalized == fallback_normalized:
            continue
        if normalized in {item.casefold() for item in details}:
            continue
        details.append(value)
        if len(details) >= DETAIL_LIMIT:
            break
    return details


def _split_inline_gloss_detail(value: str) -> tuple[str, str]:
    text = " ".join(str(value or "").strip().split())
    if not text.endswith(")") or " (" not in text:
        return _truncate_text(text), ""
    head, detail = text.split(" (", 1)
    head = head.strip()
    detail = detail[:-1].strip()
    if not head or not detail:
        return _truncate_text(text), ""
    return _truncate_text(head), _truncate_text(detail)


def _sense_examples(metadata: Mapping[str, object]) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    raw_examples = metadata.get("sense_examples")
    if not isinstance(raw_examples, Sequence) or isinstance(raw_examples, (str, bytes)):
        return examples
    for raw in raw_examples:
        if not isinstance(raw, Mapping):
            continue
        text = _truncate_text(_first_text(raw.get("text")))
        translation = _truncate_text(_first_text(raw.get("translation"), raw.get("english")))
        if not text and not translation:
            continue
        example: dict[str, str] = {}
        if text:
            example["text"] = text
        if translation and translation.casefold() != text.casefold():
            example["translation"] = translation
        if example in examples:
            continue
        examples.append(example)
        if len(examples) >= EXAMPLE_LIMIT:
            break
    return examples


def _prepend_unique(values: list[str], value: str, *, limit: int) -> None:
    text = _truncate_text(value)
    if not text:
        return
    if text.casefold() in {item.casefold() for item in values}:
        return
    values.insert(0, text)
    del values[limit:]


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        raw_values: Sequence[object] = (value,)
    elif isinstance(value, Sequence):
        raw_values = value
    else:
        return []
    items: list[str] = []
    for raw in raw_values:
        text = _truncate_text(raw)
        if text:
            items.append(text)
    return items


def _truncate_text(value: object, *, limit: int = 160) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _pos_payload(
    word_package: Mapping[str, object],
    glosses: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    canonical = _first_text(word_package.get("pos_canonical"), word_package.get("pos"))
    if canonical:
        return {"canonical": canonical, "label": canonical, "source": "word_package"}
    for gloss in glosses:
        pos = _first_text(gloss.get("pos") if isinstance(gloss, Mapping) else "")
        if pos:
            return {"canonical": pos, "label": pos, "source": "installed_dictionary"}
    return {"canonical": "", "label": "", "source": ""}


def _srs_payload(item: object | None) -> dict[str, object]:
    if item is None:
        return {"present": False}
    lifecycle_state = normalize_srs_lifecycle_state(getattr(item, "lifecycle_state", "active"))
    return {
        "present": True,
        "status": lifecycle_state,
        "status_label": lifecycle_state.replace("_", " ").title(),
        "next_due": getattr(item, "next_due", None),
        "last_review": getattr(item, "last_review", None),
        "last_seen": getattr(item, "last_seen", None),
        "admitted_at": getattr(item, "admitted_at", None),
        "review_count": len(getattr(item, "history", ()) or ()),
        "exposures": max(0, int(getattr(item, "exposures", 0) or 0)),
        "lifecycle_state": lifecycle_state,
        "source_type": getattr(item, "source_type", ""),
    }


def _external_links(*, lemma: str, display: str, target_language: str) -> list[dict[str, str]]:
    term = _first_text(display, lemma)
    if not term:
        return []
    section = _wiktionary_section(target_language)
    suffix = f"#{quote(section)}" if section else ""
    return [
        {
            "label": "Wiktionary",
            "url": f"https://en.wiktionary.org/wiki/{quote(term)}{suffix}",
        }
    ]


def _wiktionary_section(language: str) -> str:
    return {
        "de": "German",
        "en": "English",
        "es": "Spanish",
        "ja": "Japanese",
        "zh": "Chinese",
    }.get(str(language or "").strip().lower(), "")


def _resolution_sources(
    *,
    srs_item: object | None,
    rule_summary: Mapping[str, object],
    glosses: Sequence[Mapping[str, object]],
) -> list[str]:
    sources: list[str] = []
    if srs_item is not None:
        sources.append("srs_store")
    if _safe_int(rule_summary.get("rule_count")) > 0:
        sources.append("published_ruleset")
    if glosses:
        sources.append("installed_lexical_pack")
    return sources


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value or "").strip() or "0")
    except (TypeError, ValueError):
        return 0
