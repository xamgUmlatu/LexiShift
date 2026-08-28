from __future__ import annotations

from typing import Callable, Mapping, Sequence

from lexishift_core.helper.lookup_dictionary_settings import (
    load_lookup_dictionary_settings,
    lookup_dictionary_pack_ids_for_pair,
    lookup_dictionary_source_ids_for_pair,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.yomitan_lookup_dictionaries import lookup_yomitan_dictionary
from lexishift_core.resources.installed_packs import resolve_installed_pack_artifact


BuiltinDictionaryLookup = tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]


def resolve_configured_dictionary_results(
    paths: HelperPaths,
    *,
    pair: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
    sense_limit: int,
    gloss_limit: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], int]:
    settings = load_lookup_dictionary_settings(paths.lookup_dictionary_settings_path)
    pack_ids = lookup_dictionary_pack_ids_for_pair(settings, pair)
    results: list[dict[str, object]] = []
    missing_resources: list[dict[str, object]] = []
    for index, pack_id in enumerate(pack_ids):
        artifact_path = resolve_installed_pack_artifact(
            paths.lookup_dictionary_packs_dir,
            pack_id,
        )
        if artifact_path is None:
            missing_resources.append(
                {"type": "lookup_dictionary", "reason": "missing", "pack_id": pack_id}
            )
            continue
        result = lookup_yomitan_dictionary(
            artifact_path,
            lookup_candidates=lookup_candidates,
            surface=lookup_surface,
            reading=lookup_reading,
            sense_limit=sense_limit,
            gloss_limit=gloss_limit,
        )
        if result is None:
            continue
        glosses = list(result.glosses)
        senses = list(result.senses)
        if not has_presentable_dictionary_content(glosses, senses):
            continue
        results.append(
            {
                "source_id": pack_id,
                "priority": index + 1,
                "builtin": False,
                "glosses": glosses,
                "senses": senses,
                "dictionary": result.dictionary,
                "dictionary_match": result.dictionary_match,
            }
        )
    return results, missing_resources, len(pack_ids)


def resolve_configured_dictionary_result(
    paths: HelperPaths,
    *,
    pack_id: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
    sense_limit: int,
    gloss_limit: int,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    artifact_path = resolve_installed_pack_artifact(
        paths.lookup_dictionary_packs_dir,
        pack_id,
    )
    if artifact_path is None:
        return None, {
            "type": "lookup_dictionary",
            "reason": "missing",
            "pack_id": pack_id,
        }
    result = lookup_yomitan_dictionary(
        artifact_path,
        lookup_candidates=lookup_candidates,
        surface=lookup_surface,
        reading=lookup_reading,
        sense_limit=sense_limit,
        gloss_limit=gloss_limit,
    )
    if result is None:
        return None, None
    glosses = list(result.glosses)
    senses = list(result.senses)
    if not has_presentable_dictionary_content(glosses, senses):
        return None, None
    return (
        {
            "source_id": pack_id,
            "builtin": False,
            "glosses": glosses,
            "senses": senses,
            "dictionary": result.dictionary,
            "dictionary_match": result.dictionary_match,
        },
        None,
    )


def resolve_ordered_dictionary_results(
    paths: HelperPaths,
    *,
    pair: str,
    builtin_source_id: str,
    lookup_candidates: Sequence[str],
    lookup_surface: str,
    lookup_reading: str,
    sense_limit: int,
    gloss_limit: int,
    resolve_builtin: Callable[[str], BuiltinDictionaryLookup | None],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    BuiltinDictionaryLookup | None,
]:
    settings = load_lookup_dictionary_settings(paths.lookup_dictionary_settings_path)
    source_ids = lookup_dictionary_source_ids_for_pair(
        settings,
        pair,
        builtin_source_id=builtin_source_id,
    )
    results: list[dict[str, object]] = []
    missing_resources: list[dict[str, object]] = []
    builtin_lookup: BuiltinDictionaryLookup | None = None
    for index, source_id in enumerate(source_ids):
        if source_id.startswith("builtin:"):
            builtin_lookup = resolve_builtin(source_id)
            if builtin_lookup is None:
                continue
            builtin_glosses, builtin_senses, diagnostics = builtin_lookup
            raw_missing = diagnostics.get("missing_resources")
            if isinstance(raw_missing, list):
                missing_resources.extend(
                    dict(item) for item in raw_missing if isinstance(item, Mapping)
                )
            if has_presentable_dictionary_content(builtin_glosses, builtin_senses):
                results.append(
                    dictionary_result_payload(
                        source_id=source_id,
                        priority=index + 1,
                        builtin=True,
                        glosses=builtin_glosses,
                        senses=builtin_senses,
                        diagnostics=diagnostics,
                    )
                )
            continue
        configured_result, missing_resource = resolve_configured_dictionary_result(
            paths,
            pack_id=source_id,
            lookup_candidates=lookup_candidates,
            lookup_surface=lookup_surface,
            lookup_reading=lookup_reading,
            sense_limit=sense_limit,
            gloss_limit=gloss_limit,
        )
        if missing_resource is not None:
            missing_resources.append(missing_resource)
        if configured_result is not None:
            configured_result["priority"] = index + 1
            results.append(configured_result)
    return results, missing_resources, builtin_lookup


def has_presentable_dictionary_content(
    glosses: Sequence[Mapping[str, object]],
    senses: Sequence[Mapping[str, object]],
) -> bool:
    if any(str(gloss.get("text") or "").strip() for gloss in glosses):
        return True
    for sense in senses:
        if sense.get("structured_content"):
            return True
        raw_sense_glosses = sense.get("glosses")
        if not isinstance(raw_sense_glosses, (list, tuple)):
            continue
        if any(
            str(gloss.get("text") if isinstance(gloss, Mapping) else gloss or "").strip()
            for gloss in raw_sense_glosses
        ):
            return True
    return False


def dictionary_result_payload(
    *,
    source_id: str,
    priority: int,
    builtin: bool,
    glosses: list[dict[str, object]],
    senses: list[dict[str, object]],
    diagnostics: Mapping[str, object],
) -> dict[str, object]:
    raw_dictionary = diagnostics.get("dictionary")
    dictionary = dict(raw_dictionary) if isinstance(raw_dictionary, Mapping) else {}
    if not str(dictionary.get("title") or "").strip():
        if source_id == "builtin:jmdict":
            dictionary["title"] = "JMdict"
        else:
            dictionary["title"] = str(dictionary.get("pack_id") or "Built-in dictionary")
    return {
        "source_id": source_id,
        "priority": priority,
        "builtin": builtin,
        "glosses": glosses,
        "senses": senses,
        "dictionary": dictionary,
        "dictionary_match": diagnostics.get("dictionary_match"),
    }
