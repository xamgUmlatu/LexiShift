from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import quote

from lexishift_core.helper.lp_capabilities import (
    default_jmdict_path,
    normalize_pair_key,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.lexicon.word_package import normalize_word_package
from lexishift_core.persistence.storage import load_vocab_dataset
from lexishift_core.resources.dict_loaders import (
    TranslationGlossRecord,
    load_jmdict_glosses_ordered,
    load_translation_gloss_records_ordered,
)
from lexishift_core.srs import load_srs_store, normalize_srs_lifecycle_state


GLOSS_LIMIT = 5
SOURCE_PHRASE_LIMIT = 5


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
    srs_item = _find_srs_item(
        paths,
        profile_id=normalized_profile_id,
        pair=normalized_pair,
        normalized_lemma=normalized_lemma,
    )
    srs_word_package = _normalize_package(
        getattr(srs_item, "word_package", None),
        fallback_surface=getattr(srs_item, "lemma", "") if srs_item is not None else "",
        fallback_language_tag=target_language,
        fallback_provider=getattr(srs_item, "source_type", "") if srs_item is not None else "",
    )
    primary_word_package = srs_word_package or request_word_package or {}
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
    rule_summary = _rule_summary(
        paths,
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        normalized_lemma=normalized_lemma,
        source_phrase=source_phrase,
    )
    gloss_payload, gloss_diagnostics = _resolve_glosses(
        paths,
        pair=normalized_pair,
        source_language=source_language,
        target_language=target_language,
        lookup_candidates=lookup_candidates,
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


def _find_srs_item(
    paths: HelperPaths,
    *,
    profile_id: str,
    pair: str,
    normalized_lemma: str,
) -> object | None:
    store_path = paths.srs_store_path_for(profile_id)
    if not store_path.exists():
        return None
    store = load_srs_store(store_path)
    for item in store.items:
        if item.language_pair != pair:
            continue
        if _normalize_lemma(item.lemma) == normalized_lemma:
            return item
    return None


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
    translation_dict_path: Path | None,
    jmdict_path: Path | None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen or capability.requires_jmdict_for_seed:
        return _resolve_jmdict_glosses(
            paths,
            pair=pair,
            source_language=source_language,
            lookup_candidates=lookup_candidates,
            jmdict_path=jmdict_path,
        )
    if capability.requires_translation_dictionary_for_rulegen:
        return _resolve_translation_glosses(
            paths,
            pair=pair,
            source_language=source_language,
            lookup_candidates=lookup_candidates,
            translation_dict_path=translation_dict_path,
        )
    return [], {
        "provider_status": "unsupported_pair",
        "missing_resources": [{"type": "word_info_provider", "reason": "pair_lacks_provider"}],
    }


def _resolve_translation_glosses(
    paths: HelperPaths,
    *,
    pair: str,
    source_language: str,
    lookup_candidates: Sequence[str],
    translation_dict_path: Path | None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    resolved_pack, _reverse_pack = resolve_pair_translation_packs(
        paths,
        pair=pair,
        translation_dict_path=translation_dict_path,
    )
    if resolved_pack is None or not resolved_pack.path.exists():
        return [], {
            "provider_status": "missing_translation_pack",
            "missing_resources": [
                {
                    "type": "translation_pack",
                    "reason": "missing",
                    "pack_id": resolved_pack.pack_id if resolved_pack is not None else "",
                }
            ],
        }
    records_by_headword = load_translation_gloss_records_ordered(
        resolved_pack.path,
        target_lang=source_language,
        headwords=lookup_candidates,
    )
    records = _records_for_candidates(records_by_headword, lookup_candidates)
    return (
        _gloss_payloads(
            records,
            language=source_language,
            source=resolved_pack.pack_id,
            source_kind="installed_translation_pack",
        ),
        {"provider_status": "ok", "missing_resources": []},
    )


def _resolve_jmdict_glosses(
    paths: HelperPaths,
    *,
    pair: str,
    source_language: str,
    lookup_candidates: Sequence[str],
    jmdict_path: Path | None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    resolved_path = jmdict_path or default_jmdict_path(
        pair, language_packs_dir=paths.language_packs_dir
    )
    if resolved_path is None or not resolved_path.exists():
        return [], {
            "provider_status": "missing_jmdict",
            "missing_resources": [{"type": "jmdict", "reason": "missing", "pack_id": "jmdict"}],
        }
    glosses_by_headword = load_jmdict_glosses_ordered(resolved_path)
    records: list[TranslationGlossRecord] = []
    lookup_set = {_normalize_lemma(candidate) for candidate in lookup_candidates}
    for headword, glosses in glosses_by_headword.items():
        if _normalize_lemma(headword) not in lookup_set:
            continue
        records.extend(TranslationGlossRecord(translation=gloss, pos_raw="") for gloss in glosses)
    return (
        _gloss_payloads(
            records,
            language=source_language or "en",
            source="jmdict",
            source_kind="installed_jmdict",
        ),
        {"provider_status": "ok", "missing_resources": []},
    )


def _records_for_candidates(
    records_by_headword: Mapping[str, Sequence[TranslationGlossRecord]],
    lookup_candidates: Sequence[str],
) -> list[TranslationGlossRecord]:
    lookup_set = {_normalize_lemma(candidate) for candidate in lookup_candidates}
    records: list[TranslationGlossRecord] = []
    for headword, entries in records_by_headword.items():
        if _normalize_lemma(headword) not in lookup_set:
            continue
        records.extend(entries)
    return records


def _gloss_payloads(
    records: Sequence[TranslationGlossRecord],
    *,
    language: str,
    source: str,
    source_kind: str,
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        text = str(record.translation or "").strip()
        if not text:
            continue
        dedupe_key = text.casefold()
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
        payloads.append(payload)
        if len(payloads) >= GLOSS_LIMIT:
            break
    return payloads


def _record_sense_id(record: TranslationGlossRecord) -> str:
    metadata = getattr(record, "metadata", None)
    if not isinstance(metadata, Mapping):
        return ""
    parts: list[str] = []
    for key in ("entry_ord", "sense_ord", "gloss_ord"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            parts.append(f"{key}:{value}")
    return "|".join(parts)


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
    if int(rule_summary.get("rule_count") or 0) > 0:
        sources.append("published_ruleset")
    if glosses:
        sources.append("installed_lexical_pack")
    return sources
