#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    default_reverse_translation_dictionary_path,
    resolve_pair_capability,
)
from lexishift_core.helper.frequency_packs import build_frequency_pack_ref
from lexishift_core.helper.pair_resources import resolve_pair_resources
from lexishift_core.helper.translation_packs import (
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    build_translation_pack_ref,
)
from lexishift_core.lexicon.word_package import build_word_package, normalize_word_package
from lexishift_core.resources.path_cache import load_or_compute_path_json_value
from lexishift_core.rulegen.benchmarking import RulegenBenchmarkCase
from lexishift_core.srs import SrsStore, load_srs_store

from rulegen_benchmark_dataset import load_benchmark_dataset
from rulegen_benchmark_compiled import _build_compiled_case_refs, _build_compiled_case_table
from rulegen_benchmark_gloss_resources import (
    build_en_es_reverse_headword_norm_index as _helper_build_en_es_reverse_headword_norm_index,
    build_pair_compiled_rulegen_context as _helper_build_pair_compiled_rulegen_context,
    build_reverse_preload_headwords as _helper_build_reverse_preload_headwords,
    expand_reverse_preload_headwords as _helper_expand_reverse_preload_headwords,
    load_gloss_base_forms_for_pair as _helper_load_gloss_base_forms_for_pair,
    load_translation_gloss_records as _helper_load_translation_gloss_records,
    preload_pair_gloss_records as _helper_preload_pair_gloss_records,
    reverse_translation_target_lang_for_pair as _helper_reverse_translation_target_lang_for_pair,
    translation_target_lang_for_pair as _helper_translation_target_lang_for_pair,
)
from rulegen_benchmark_models import BenchmarkTimingCollector, PairBenchmarkContext


def _load_dataset_cases(
    path: Path,
    *,
    pair_filter: Optional[set[str]],
) -> tuple[dict[str, object], dict[str, list[RulegenBenchmarkCase]]]:
    return load_benchmark_dataset(path, pair_filter=pair_filter)


def _load_store(paths, *, profile_id: str) -> SrsStore:
    store_path = paths.srs_store_path_for(profile_id)
    if not store_path.exists():
        return SrsStore()
    return load_srs_store(store_path)


def _build_store_word_packages(
    *,
    store: SrsStore,
    pair: str,
    targets: set[str],
) -> dict[str, Mapping[str, object]]:
    package_map: dict[str, Mapping[str, object]] = {}
    for item in store.items:
        if item.language_pair != pair:
            continue
        lemma = str(item.lemma or "").strip()
        if lemma not in targets:
            continue
        if not isinstance(item.word_package, Mapping):
            continue
        package_map[lemma] = item.word_package
    return package_map


def _build_word_package_snapshot(
    *,
    targets: Sequence[str],
    word_packages_by_target: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    normalized_targets = sorted(
        {str(target or "").strip() for target in targets if str(target or "").strip()}
    )
    for target in normalized_targets:
        normalized_package = normalize_word_package(word_packages_by_target.get(target))
        snapshot[target] = dict(normalized_package) if normalized_package is not None else None
    return snapshot


def _load_frozen_word_package_snapshots(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_pairs = payload
    if isinstance(payload, Mapping) and isinstance(payload.get("pairs"), Mapping):
        raw_pairs = payload.get("pairs")
        if isinstance(raw_pairs, Mapping):
            sample_value = next(iter(raw_pairs.values()), None)
            if isinstance(sample_value, Mapping) and "word_package_snapshot" in sample_value:
                raw_pairs = {
                    pair: value.get("word_package_snapshot")
                    for pair, value in raw_pairs.items()
                    if isinstance(value, Mapping)
                }
    if not isinstance(raw_pairs, Mapping):
        raise ValueError(f"Frozen word-package snapshot payload must be an object: {path}")
    frozen: dict[str, dict[str, object]] = {}
    for raw_pair, raw_snapshot in raw_pairs.items():
        pair = str(raw_pair or "").strip()
        if not pair:
            continue
        if not isinstance(raw_snapshot, Mapping):
            continue
        pair_snapshot: dict[str, object] = {}
        for raw_target, raw_package in raw_snapshot.items():
            target = str(raw_target or "").strip()
            if not target:
                continue
            if raw_package is None:
                pair_snapshot[target] = None
                continue
            if not isinstance(raw_package, Mapping):
                raise ValueError(
                    f"Frozen word-package snapshot for pair `{pair}` target `{target}` "
                    f"must be an object or null: {path}"
                )
            normalized_package = normalize_word_package(raw_package)
            pair_snapshot[target] = (
                dict(normalized_package) if normalized_package is not None else None
            )
        frozen[pair] = pair_snapshot
    return frozen


def _apply_case_word_package_overrides(
    *,
    package_map: dict[str, Mapping[str, object]],
    pair: str,
    cases: Sequence[RulegenBenchmarkCase],
) -> None:
    for case in cases:
        if case.target in package_map:
            continue
        if not case.target_reading:
            continue
        package = build_word_package(
            language_pair=pair,
            surface=case.target,
            reading=case.target_reading,
            source_provider="rulegen_benchmark",
        )
        if package is None:
            continue
        package_map[case.target] = package


def _resolve_pair_resources_for_benchmark(
    *,
    paths,
    pair: str,
    jmdict_override: Optional[Path],
    translation_dict_override: Optional[Path],
    reverse_translation_dict_override: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    jmdict_path, translation_dict_path, _ = resolve_pair_resources(
        paths,
        pair=pair,
        jmdict_path=jmdict_override,
        translation_dict_path=translation_dict_override,
        set_source_db=None,
    )
    reverse_translation_dict_path = reverse_translation_dict_override
    if reverse_translation_dict_path is None:
        reverse_translation_dict_path = default_reverse_translation_dictionary_path(
            pair,
            language_packs_dir=paths.language_packs_dir,
        )
    capability = resolve_pair_capability(pair)
    if capability.requires_jmdict_for_rulegen:
        if jmdict_path is None or not jmdict_path.exists():
            raise FileNotFoundError(f"JMDict path not found for pair {pair}: {jmdict_path}")
    if capability.requires_translation_dictionary_for_rulegen:
        if translation_dict_path is None or not translation_dict_path.exists():
            raise FileNotFoundError(
                f"Translation dictionary path not found for pair {pair}: {translation_dict_path}"
            )
    if pair in {"en-es", "es-en"} and reverse_translation_dict_path is not None:
        if not reverse_translation_dict_path.exists():
            raise FileNotFoundError(
                f"Reverse translation dictionary path not found for pair {pair}: "
                f"{reverse_translation_dict_path}"
            )
    return jmdict_path, translation_dict_path, reverse_translation_dict_path


def _resolve_source_frequency_db_for_benchmark(
    *,
    paths,
    pair: str,
    source_frequency_db_override: Optional[Path],
) -> Optional[Path]:
    if source_frequency_db_override is not None:
        return Path(source_frequency_db_override)
    source_frequency_pair = _source_frequency_pair_for_benchmark(pair)
    if not source_frequency_pair:
        return None
    return default_frequency_db_path(
        source_frequency_pair,
        frequency_packs_dir=paths.frequency_packs_dir,
    )


def _source_frequency_pair_for_benchmark(pair: str) -> Optional[str]:
    normalized = str(pair or "").strip().lower()
    source_lang = normalized.split("-", 1)[0] if "-" in normalized else ""
    if not source_lang:
        return None
    return f"{source_lang}-{source_lang}"


def _translation_target_lang_for_pair(pair: str) -> Optional[str]:
    return _helper_translation_target_lang_for_pair(pair)


def _reverse_translation_target_lang_for_pair(pair: str) -> Optional[str]:
    return _helper_reverse_translation_target_lang_for_pair(pair)


def _load_translation_gloss_records(
    path: Optional[Path],
    *,
    target_lang: Optional[str],
    headwords: Optional[Sequence[str]] = None,
) -> Optional[dict[str, list[object]]]:
    return _helper_load_translation_gloss_records(
        path,
        target_lang=target_lang,
        headwords=headwords,
    )


def _preload_pair_gloss_records(
    *,
    pair: str,
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    targets: Sequence[str] = (),
) -> tuple[Optional[dict[str, list[object]]], Optional[dict[str, list[object]]]]:
    return _helper_preload_pair_gloss_records(
        pair=pair,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        targets=targets,
        expand_reverse_headwords=_expand_reverse_preload_headwords,
    )


def _build_reverse_preload_headwords(
    *,
    pair: str,
    forward_records_by_target: Optional[Mapping[str, Sequence[object]]],
) -> Optional[tuple[str, ...]]:
    return _helper_build_reverse_preload_headwords(
        pair=pair,
        forward_records_by_target=forward_records_by_target,
    )


def _expand_reverse_preload_headwords(
    *,
    pair: str,
    reverse_translation_dict_path: Optional[Path],
    reverse_headwords: Optional[Sequence[str]],
) -> Optional[tuple[str, ...]]:
    return _helper_expand_reverse_preload_headwords(
        pair=pair,
        reverse_translation_dict_path=reverse_translation_dict_path,
        reverse_headwords=reverse_headwords,
        load_reverse_headword_norm_index=_load_en_es_reverse_headword_norm_index,
    )


def _load_en_es_reverse_headword_norm_index(
    reverse_translation_dict_path: Path,
) -> dict[str, tuple[str, ...]]:
    return load_or_compute_path_json_value(
        reverse_translation_dict_path,
        namespace="translation_pack_metadata",
        key={
            "kind": "reverse_headword_norm_index",
            "pair": "en-es",
        },
        compute=lambda: _build_en_es_reverse_headword_norm_index(reverse_translation_dict_path),
        serialize=lambda mapping: {
            str(normalized or "").strip().lower(): [
                str(raw_headword or "").strip().lower()
                for raw_headword in raw_headwords
                if str(raw_headword or "").strip()
            ]
            for normalized, raw_headwords in mapping.items()
            if str(normalized or "").strip()
        },
        deserialize=lambda payload: {
            str(normalized or "").strip().lower(): tuple(
                str(raw_headword or "").strip().lower()
                for raw_headword in raw_headwords
                if str(raw_headword or "").strip()
            )
            for normalized, raw_headwords in payload.items()
            if str(normalized or "").strip()
        },
    )


def _build_en_es_reverse_headword_norm_index(
    reverse_translation_dict_path: Path,
) -> dict[str, tuple[str, ...]]:
    return _helper_build_en_es_reverse_headword_norm_index(reverse_translation_dict_path)


def _path_looks_kaikki(path: Optional[Path]) -> bool:
    from rulegen_benchmark_gloss_resources import path_looks_kaikki as _helper_path_looks_kaikki

    return _helper_path_looks_kaikki(path)


def _build_pair_compiled_rulegen_context(
    *,
    pair: str,
    targets: Sequence[str],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    gloss_records_by_target: Optional[Mapping[str, Sequence[object]]],
    reverse_gloss_records_by_source: Optional[Mapping[str, Sequence[object]]],
    word_packages_by_target: Mapping[str, Mapping[str, object]],
    gloss_base_forms: Optional[Sequence[str]] = None,
) -> Optional[object]:
    return _helper_build_pair_compiled_rulegen_context(
        pair=pair,
        targets=targets,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        gloss_records_by_target=gloss_records_by_target,
        reverse_gloss_records_by_source=reverse_gloss_records_by_source,
        word_packages_by_target=word_packages_by_target,
        gloss_base_forms=gloss_base_forms,
    )


def _compute_file_sha256_uncached(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _compute_file_sha256(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists() or not path.is_file():
        return None
    return load_or_compute_path_json_value(
        path,
        namespace="benchmark_resource_checksums",
        key={"kind": "sha256"},
        compute=lambda: _compute_file_sha256_uncached(path),
        serialize=lambda value: str(value or ""),
        deserialize=lambda payload: str(payload or ""),
    )


def _build_pair_resources_payload(
    *,
    pair: str,
    jmdict_path: Optional[Path],
    translation_dict_path: Optional[Path],
    reverse_translation_dict_path: Optional[Path],
    source_frequency_db_path: Optional[Path] = None,
) -> dict[str, object]:
    translation_pack = build_translation_pack_ref(
        pair,
        translation_dict_path,
        direction=FORWARD_PACK_DIRECTION,
    )
    reverse_translation_pack = build_translation_pack_ref(
        pair,
        reverse_translation_dict_path,
        direction=REVERSE_PACK_DIRECTION,
    )
    source_frequency_pair = _source_frequency_pair_for_benchmark(pair)
    source_frequency_pack = build_frequency_pack_ref(
        source_frequency_pair or pair,
        source_frequency_db_path,
    )
    return {
        "jmdict_path": str(jmdict_path) if jmdict_path else None,
        "translation_dict_path": str(translation_dict_path) if translation_dict_path else None,
        "translation_pack_id": (translation_pack.pack_id if translation_pack is not None else None),
        "translation_pack_provider": (
            translation_pack.provider if translation_pack is not None else None
        ),
        "translation_pack_pos_source_profile": (
            translation_pack.pos_source_profile if translation_pack is not None else None
        ),
        "reverse_translation_dict_path": (
            str(reverse_translation_dict_path) if reverse_translation_dict_path else None
        ),
        "reverse_translation_pack_id": (
            reverse_translation_pack.pack_id if reverse_translation_pack is not None else None
        ),
        "reverse_translation_pack_provider": (
            reverse_translation_pack.provider if reverse_translation_pack is not None else None
        ),
        "reverse_translation_pack_pos_source_profile": (
            reverse_translation_pack.pos_source_profile
            if reverse_translation_pack is not None
            else None
        ),
        "source_frequency_db_path": str(source_frequency_db_path)
        if source_frequency_db_path
        else None,
        "source_frequency_pack_id": (
            source_frequency_pack.pack_id if source_frequency_pack is not None else None
        ),
        "source_frequency_pack_provider": (
            source_frequency_pack.provider if source_frequency_pack is not None else None
        ),
        "source_frequency_pack_pos_source_profile": (
            source_frequency_pack.pos_source_profile if source_frequency_pack is not None else None
        ),
        "checksums": {
            "jmdict_sha256": _compute_file_sha256(jmdict_path),
            "translation_dict_sha256": _compute_file_sha256(translation_dict_path),
            "reverse_translation_dict_sha256": _compute_file_sha256(reverse_translation_dict_path),
            "source_frequency_db_sha256": _compute_file_sha256(source_frequency_db_path),
        },
    }


def _build_pair_benchmark_context(
    *,
    paths,
    store: SrsStore,
    pair: str,
    cases: Sequence[RulegenBenchmarkCase],
    jmdict_override: Optional[Path],
    translation_dict_override: Optional[Path],
    reverse_translation_dict_override: Optional[Path],
    source_frequency_db_override: Optional[Path],
    frozen_word_package_snapshots: Mapping[str, Mapping[str, object]],
    timing: Optional[BenchmarkTimingCollector] = None,
) -> PairBenchmarkContext:
    started = perf_counter()
    jmdict_path, translation_dict_path, reverse_translation_dict_path = (
        _resolve_pair_resources_for_benchmark(
            paths=paths,
            pair=pair,
            jmdict_override=jmdict_override,
            translation_dict_override=translation_dict_override,
            reverse_translation_dict_override=reverse_translation_dict_override,
        )
    )
    if timing is not None:
        timing.add("resolve_resources", perf_counter() - started, pair=pair)

    source_frequency_db_path = _resolve_source_frequency_db_for_benchmark(
        paths=paths,
        pair=pair,
        source_frequency_db_override=source_frequency_db_override,
    )

    started = perf_counter()
    resources = _build_pair_resources_payload(
        pair=pair,
        jmdict_path=jmdict_path,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        source_frequency_db_path=source_frequency_db_path,
    )
    if timing is not None:
        timing.add("build_resource_payload", perf_counter() - started, pair=pair)

    target_set = {case.target for case in cases}
    targets = tuple(sorted(target_set))
    started = perf_counter()
    frozen_snapshot = frozen_word_package_snapshots.get(pair)
    if isinstance(frozen_snapshot, Mapping):
        word_package_snapshot = {target: frozen_snapshot.get(target) for target in targets}
        word_packages = {
            target: package
            for target, package in word_package_snapshot.items()
            if isinstance(package, Mapping)
        }
    else:
        word_packages = _build_store_word_packages(store=store, pair=pair, targets=target_set)
        _apply_case_word_package_overrides(package_map=word_packages, pair=pair, cases=cases)
        word_package_snapshot = _build_word_package_snapshot(
            targets=targets,
            word_packages_by_target=word_packages,
        )
    if timing is not None:
        timing.add("build_word_packages", perf_counter() - started, pair=pair)

    started = perf_counter()
    gloss_records_by_target, reverse_gloss_records_by_source = _preload_pair_gloss_records(
        pair=pair,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        targets=targets,
    )
    gloss_base_forms = _helper_load_gloss_base_forms_for_pair(
        pair=pair,
        translation_dict_path=translation_dict_path,
    )
    if timing is not None:
        timing.add("preload_translation_gloss_records", perf_counter() - started, pair=pair)

    started = perf_counter()
    compiled_pair_context = _build_pair_compiled_rulegen_context(
        pair=pair,
        targets=targets,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        gloss_records_by_target=gloss_records_by_target,
        reverse_gloss_records_by_source=reverse_gloss_records_by_source,
        word_packages_by_target=word_packages,
        gloss_base_forms=gloss_base_forms,
    )
    if timing is not None:
        timing.add("compile_pair_context", perf_counter() - started, pair=pair)

    compiled_case_refs = _build_compiled_case_refs(
        cases=cases,
        compiled_pair_context=compiled_pair_context,
    )
    compiled_case_table = _build_compiled_case_table(
        cases=cases,
        compiled_case_refs=compiled_case_refs,
    )

    return PairBenchmarkContext(
        pair=pair,
        cases=tuple(cases),
        targets=targets,
        jmdict_path=jmdict_path,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=reverse_translation_dict_path,
        source_frequency_db_path=source_frequency_db_path,
        resources=resources,
        word_package_snapshot=word_package_snapshot,
        word_packages_by_target=word_packages,
        gloss_records_by_target=gloss_records_by_target,
        reverse_gloss_records_by_source=reverse_gloss_records_by_source,
        compiled_pair_context=compiled_pair_context,
        compiled_case_refs=compiled_case_refs,
        compiled_case_table=compiled_case_table,
    )
