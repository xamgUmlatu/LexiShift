#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.translation_packs import TranslationPackRef  # noqa: E402
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    TranslationGlossRecord,
    load_translation_gloss_records_by_translation_ordered,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.semantic_shadow_embedding_bridge import (  # noqa: E402
    DEFAULT_EMBEDDING_BRIDGE_MODEL,
    DEFAULT_EMBEDDING_BRIDGE_TOP_K,
    build_embedding_bridge_neighbor_index,
    build_target_embedding_bridge_profiles,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    BenchmarkShadowTarget,
    augment_shadow_targets_with_forward_gloss_triggers,
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    build_rulegen_shadow_targets,
    normalize_shadow_text,
    subtract_shadow_target_triggers,
)
from lexishift_core.rulegen.semantic_shadow_seed_borrowing import (  # noqa: E402
    DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS,
    DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT,
    DEFAULT_NEIGHBOR_BORROW_MIN_SIMILARITY,
    augment_shadow_targets_with_neighbor_borrowed_triggers,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_es.json"
)
DEFAULT_BENCHMARK_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json"
)


@dataclass(frozen=True)
class EnEsShadowExperimentResources:
    dataset_path: Path
    benchmark_json: Path
    data_root: Path
    cases: tuple[Mapping[str, object], ...]
    benchmark_targets: tuple[BenchmarkShadowTarget, ...]
    best_run_case_results: tuple[Mapping[str, object], ...]
    forward_pack: TranslationPackRef
    reverse_pack: TranslationPackRef
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]]
    target_reverse_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]]
    forward_provider: str
    reverse_provider: str


@dataclass(frozen=True)
class EnEsShadowSeedModePayload:
    mode_id: str
    seed_targets: tuple[BenchmarkShadowTarget, ...]
    source_targets_by_label: Mapping[str, tuple[BenchmarkShadowTarget, ...]]


def collect_shadow_cases(dataset_payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return tuple(dict(case) for case in raw_cases if isinstance(case, Mapping))


def load_en_es_best_run_case_results(
    benchmark_report: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    pairs = benchmark_report.get("pairs")
    if not isinstance(pairs, Mapping):
        raise ValueError("Benchmark report is missing `pairs`.")
    en_es = pairs.get("en-es")
    if not isinstance(en_es, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es`.")
    best_run = en_es.get("best_run")
    if not isinstance(best_run, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es.best_run`.")
    case_results = best_run.get("case_results")
    if not isinstance(case_results, Sequence) or isinstance(case_results, (str, bytes)):
        raise ValueError("Benchmark report best_run is missing `case_results`.")
    return tuple(dict(case) for case in case_results if isinstance(case, Mapping))


def load_en_es_shadow_experiment_resources(
    *,
    benchmark_dataset: Path = DEFAULT_DATASET_PATH,
    benchmark_json: Path = DEFAULT_BENCHMARK_JSON,
    data_root: Path = Path(resolve_data_root()),
    translation_dict: Path | None = None,
    reverse_translation_dict: Path | None = None,
) -> EnEsShadowExperimentResources:
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    cases = collect_shadow_cases(dataset_payload)
    benchmark_targets = tuple(build_benchmark_shadow_targets(cases))
    best_run_case_results = load_en_es_best_run_case_results(benchmark_report)
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )
    if forward_pack is None or not forward_pack.path.exists():
        raise ValueError("Missing forward translation pack for en-es semantic-shadow experiments.")
    if reverse_pack is None or not reverse_pack.path.exists():
        raise ValueError("Missing reverse translation pack for en-es semantic-shadow experiments.")
    all_targets = sorted(
        {target.target for target in benchmark_targets if str(target.target or "").strip()}
    )
    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=all_targets,
    )
    target_reverse_records_by_target = load_translation_gloss_records_by_translation_ordered(
        reverse_pack.path,
        translations=all_targets,
    )
    return EnEsShadowExperimentResources(
        dataset_path=Path(benchmark_dataset),
        benchmark_json=Path(benchmark_json),
        data_root=Path(data_root),
        cases=cases,
        benchmark_targets=benchmark_targets,
        best_run_case_results=best_run_case_results,
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
        forward_records_by_target=forward_records_by_target,
        target_reverse_records_by_target=target_reverse_records_by_target,
        forward_provider=forward_pack.provider,
        reverse_provider=reverse_pack.provider,
    )


def build_en_es_seed_mode_payloads(
    resources: EnEsShadowExperimentResources,
    *,
    forward_seed_max_words: int = 1,
    include_neighbor_borrow_seed_modes: bool = False,
    neighbor_borrow_model: str = DEFAULT_EMBEDDING_BRIDGE_MODEL,
    neighbor_borrow_min_similarity: float = DEFAULT_NEIGHBOR_BORROW_MIN_SIMILARITY,
    neighbor_borrow_top_k: int = DEFAULT_EMBEDDING_BRIDGE_TOP_K,
    neighbor_borrow_min_reverse_target_count: int = DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT,
    neighbor_borrow_max_triggers_per_target: int = DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS,
) -> dict[str, EnEsShadowSeedModePayload]:
    target_filter = [target.target for target in resources.benchmark_targets]
    rulegen_top3_targets = tuple(
        build_rulegen_shadow_targets(
            resources.best_run_case_results,
            targets=target_filter,
            source_field="top3_sources",
        )
    )
    rulegen_all_targets = tuple(
        build_rulegen_shadow_targets(
            resources.best_run_case_results,
            targets=target_filter,
            source_field="all_sources",
        )
    )
    top3_plus_forward_gloss = tuple(
        augment_shadow_targets_with_forward_gloss_triggers(
            rulegen_top3_targets,
            forward_records_by_target=resources.forward_records_by_target,
            max_words=forward_seed_max_words,
        )
    )
    all_plus_forward_gloss = tuple(
        augment_shadow_targets_with_forward_gloss_triggers(
            rulegen_all_targets,
            forward_records_by_target=resources.forward_records_by_target,
            max_words=forward_seed_max_words,
        )
    )
    top3_forward_only = tuple(
        subtract_shadow_target_triggers(
            top3_plus_forward_gloss,
            rulegen_top3_targets,
            tier_label="forward_gloss_fragments",
        )
    )
    all_forward_only = tuple(
        subtract_shadow_target_triggers(
            all_plus_forward_gloss,
            rulegen_all_targets,
            tier_label="forward_gloss_fragments",
        )
    )
    payloads: dict[str, EnEsShadowSeedModePayload] = {
        "benchmark_reviewed": EnEsShadowSeedModePayload(
            mode_id="benchmark_reviewed",
            seed_targets=resources.benchmark_targets,
            source_targets_by_label={"benchmark_reviewed": resources.benchmark_targets},
        ),
        "rulegen_top3_sources": EnEsShadowSeedModePayload(
            mode_id="rulegen_top3_sources",
            seed_targets=rulegen_top3_targets,
            source_targets_by_label={"rulegen_top3_sources": rulegen_top3_targets},
        ),
        "rulegen_all_sources": EnEsShadowSeedModePayload(
            mode_id="rulegen_all_sources",
            seed_targets=rulegen_all_targets,
            source_targets_by_label={"rulegen_all_sources": rulegen_all_targets},
        ),
        "rulegen_top3_plus_forward_gloss": EnEsShadowSeedModePayload(
            mode_id="rulegen_top3_plus_forward_gloss",
            seed_targets=top3_plus_forward_gloss,
            source_targets_by_label={
                "rulegen_top3_sources": rulegen_top3_targets,
                "forward_gloss_fragments": top3_forward_only,
            },
        ),
        "rulegen_all_plus_forward_gloss": EnEsShadowSeedModePayload(
            mode_id="rulegen_all_plus_forward_gloss",
            seed_targets=all_plus_forward_gloss,
            source_targets_by_label={
                "rulegen_all_sources": rulegen_all_targets,
                "forward_gloss_fragments": all_forward_only,
            },
        ),
    }
    if not include_neighbor_borrow_seed_modes:
        return payloads

    reverse_records_by_source = load_reverse_records_by_source_for_seed_modes(
        resources,
        payloads.values(),
    )
    target_profiles = build_target_embedding_bridge_profiles(
        benchmark_targets=resources.benchmark_targets,
        forward_records_by_target=resources.forward_records_by_target,
        target_reverse_records_by_target=resources.target_reverse_records_by_target,
    )
    neighbor_index = build_embedding_bridge_neighbor_index(
        target_profiles=target_profiles,
        model_name=neighbor_borrow_model,
        min_similarity=float(neighbor_borrow_min_similarity),
        top_k=int(neighbor_borrow_top_k),
    )
    top3_neighbor_borrow = tuple(
        augment_shadow_targets_with_neighbor_borrowed_triggers(
            top3_plus_forward_gloss,
            neighbor_index=neighbor_index,
            reverse_records_by_source=reverse_records_by_source,
            min_reverse_target_count=int(neighbor_borrow_min_reverse_target_count),
            max_borrowed_triggers_per_target=int(neighbor_borrow_max_triggers_per_target),
            max_words=int(forward_seed_max_words),
        )
    )
    all_neighbor_borrow = tuple(
        augment_shadow_targets_with_neighbor_borrowed_triggers(
            all_plus_forward_gloss,
            neighbor_index=neighbor_index,
            reverse_records_by_source=reverse_records_by_source,
            min_reverse_target_count=int(neighbor_borrow_min_reverse_target_count),
            max_borrowed_triggers_per_target=int(neighbor_borrow_max_triggers_per_target),
            max_words=int(forward_seed_max_words),
        )
    )
    top3_neighbor_only = tuple(
        subtract_shadow_target_triggers(
            top3_neighbor_borrow,
            top3_plus_forward_gloss,
            tier_label="neighbor_borrowed_triggers",
        )
    )
    all_neighbor_only = tuple(
        subtract_shadow_target_triggers(
            all_neighbor_borrow,
            all_plus_forward_gloss,
            tier_label="neighbor_borrowed_triggers",
        )
    )
    payloads["rulegen_top3_plus_forward_gloss_plus_neighbor_borrow"] = EnEsShadowSeedModePayload(
        mode_id="rulegen_top3_plus_forward_gloss_plus_neighbor_borrow",
        seed_targets=top3_neighbor_borrow,
        source_targets_by_label={
            "rulegen_top3_sources": rulegen_top3_targets,
            "forward_gloss_fragments": top3_forward_only,
            "neighbor_borrowed_triggers": top3_neighbor_only,
        },
    )
    payloads["rulegen_all_plus_forward_gloss_plus_neighbor_borrow"] = EnEsShadowSeedModePayload(
        mode_id="rulegen_all_plus_forward_gloss_plus_neighbor_borrow",
        seed_targets=all_neighbor_borrow,
        source_targets_by_label={
            "rulegen_all_sources": rulegen_all_targets,
            "forward_gloss_fragments": all_forward_only,
            "neighbor_borrowed_triggers": all_neighbor_only,
        },
    )
    return payloads


def load_reverse_records_by_source_for_seed_modes(
    resources: EnEsShadowExperimentResources,
    seed_mode_payloads: Sequence[EnEsShadowSeedModePayload],
) -> Mapping[str, Sequence[TranslationGlossRecord]]:
    triggers = sorted(
        {
            trigger
            for payload in seed_mode_payloads
            for target in payload.seed_targets
            for trigger in target.reviewed_triggers
            if str(trigger or "").strip()
        }
    )
    return load_translation_gloss_records_ordered(
        resources.reverse_pack.path,
        target_lang="es",
        headwords=triggers,
    )


def build_inventory_for_seed_targets(
    resources: EnEsShadowExperimentResources,
    *,
    seed_targets: Sequence[BenchmarkShadowTarget],
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
    promotion_policy: str,
    support_score_weights: Mapping[str, object] | None = None,
    semantic_bridge_include_aux_text: bool = False,
    semantic_bridge_include_examples: bool = False,
) -> dict[str, object]:
    return build_en_es_shadow_inventory(
        benchmark_targets=seed_targets,
        forward_records_by_target=resources.forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        target_reverse_records_by_target=resources.target_reverse_records_by_target,
        forward_provider=resources.forward_provider,
        reverse_provider=resources.reverse_provider,
        promotion_policy=promotion_policy,
        support_score_weights=support_score_weights,
        semantic_bridge_include_aux_text=semantic_bridge_include_aux_text,
        semantic_bridge_include_examples=semantic_bridge_include_examples,
    )


def normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def collect_reviewed_triggers(case: Mapping[str, object]) -> list[str]:
    reviewed_values: list[str] = []
    for key in ("expected_top1_any", "expected_any"):
        reviewed_values.extend(normalize_string_list(case.get(key)))
    triggers: list[str] = []
    for value in reviewed_values:
        normalized = normalize_shadow_text(value)
        if normalized and normalized not in triggers:
            triggers.append(normalized)
    return triggers


def collect_top1_triggers(case: Mapping[str, object]) -> list[str]:
    triggers: list[str] = []
    for value in normalize_string_list(case.get("expected_top1_any")):
        normalized = normalize_shadow_text(value)
        if normalized and normalized not in triggers:
            triggers.append(normalized)
    return triggers


def merge_slice_dimension_values(
    dimension_map: dict[str, list[str]],
    dimension_name: str,
    values: Sequence[str],
) -> None:
    normalized_name = str(dimension_name or "").strip()
    if not normalized_name:
        return
    bucket = dimension_map.setdefault(normalized_name, [])
    for value in values:
        normalized_value = str(value or "").strip()
        if normalized_value and normalized_value not in bucket:
            bucket.append(normalized_value)


def build_trigger_row_metadata_from_cases(
    cases: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    trigger_to_targets: dict[str, set[str]] = {}
    for case in cases:
        target = str(case.get("target") or "").strip()
        if not target:
            continue
        for trigger in collect_reviewed_triggers(case):
            bucket = trigger_to_targets.setdefault(trigger, set())
            bucket.add(target)

    metadata_by_key: dict[tuple[str, str], dict[str, object]] = {}
    for case in cases:
        target = str(case.get("target") or "").strip()
        if not target:
            continue
        case_id = str(case.get("case_id") or "").strip()
        tiers = normalize_string_list((case.get("tier"),))
        top1_triggers = set(collect_top1_triggers(case))
        slice_tags = normalize_string_list(case.get("slice_tags"))
        raw_dimensions = case.get("slice_dimensions")
        slice_dimensions: dict[str, list[str]] = {}
        if isinstance(raw_dimensions, Mapping):
            for dimension, raw_values in raw_dimensions.items():
                dimension_name = str(dimension or "").strip()
                values = normalize_string_list(raw_values)
                if dimension_name and values:
                    slice_dimensions[dimension_name] = values
        if tiers:
            merge_slice_dimension_values(slice_dimensions, "tier", tiers)

        for trigger in collect_reviewed_triggers(case):
            metadata = metadata_by_key.setdefault(
                (target, trigger),
                {
                    "case_ids": [],
                    "tiers": [],
                    "slice_tags": [],
                    "slice_dimensions": {},
                },
            )
            if case_id and case_id not in metadata["case_ids"]:
                metadata["case_ids"].append(case_id)
            for tier in tiers:
                if tier not in metadata["tiers"]:
                    metadata["tiers"].append(tier)
            for tag in slice_tags:
                if tag not in metadata["slice_tags"]:
                    metadata["slice_tags"].append(tag)
            metadata_dimensions = metadata["slice_dimensions"]
            if isinstance(metadata_dimensions, dict):
                overlap_target_count = len(trigger_to_targets.get(trigger, {target}))
                merge_slice_dimension_values(
                    metadata_dimensions,
                    "overlap_topology",
                    ("shared_trigger" if overlap_target_count > 1 else "singleton_trigger",),
                )
                merge_slice_dimension_values(
                    metadata_dimensions,
                    "overlap_target_count",
                    (str(max(1, overlap_target_count)),),
                )
                merge_slice_dimension_values(
                    metadata_dimensions,
                    "trigger_shape",
                    ("multiword" if " " in trigger else "unigram",),
                )
                merge_slice_dimension_values(
                    metadata_dimensions,
                    "reviewed_expectation",
                    ("top1_expected" if trigger in top1_triggers else "expected_only",),
                )
                for dimension_name, values in slice_dimensions.items():
                    merge_slice_dimension_values(metadata_dimensions, dimension_name, values)
    return metadata_by_key


def build_shadow_signal_availability_summary(
    resources: EnEsShadowExperimentResources,
    *,
    reverse_records_by_source: Mapping[str, Sequence[TranslationGlossRecord]],
) -> dict[str, object]:
    forward_records = [
        record
        for records in resources.forward_records_by_target.values()
        for record in records
        if isinstance(record, TranslationGlossRecord)
    ]
    target_reverse_records = [
        record
        for records in resources.target_reverse_records_by_target.values()
        for record in records
        if isinstance(record, TranslationGlossRecord)
    ]
    trigger_reverse_records = [
        record
        for records in reverse_records_by_source.values()
        for record in records
        if isinstance(record, TranslationGlossRecord)
    ]
    return {
        "forward_records_total": len(forward_records),
        "forward_records_with_examples": _count_records_with_metadata_keys(
            forward_records,
            ("sense_examples",),
        ),
        "forward_targets_with_examples": _count_group_keys_with_metadata_keys(
            resources.forward_records_by_target,
            ("sense_examples",),
        ),
        "target_reverse_records_total": len(target_reverse_records),
        "target_reverse_records_with_aux_text": _count_records_with_metadata_keys(
            target_reverse_records,
            ("translation_sense_text", "translation_english_text", "translation_note_text"),
        ),
        "target_reverse_targets_with_aux_text": _count_group_keys_with_metadata_keys(
            resources.target_reverse_records_by_target,
            ("translation_sense_text", "translation_english_text", "translation_note_text"),
        ),
        "trigger_reverse_records_total": len(trigger_reverse_records),
        "trigger_reverse_records_with_aux_text": _count_records_with_metadata_keys(
            trigger_reverse_records,
            ("translation_sense_text", "translation_english_text", "translation_note_text"),
        ),
        "trigger_reverse_triggers_with_aux_text": _count_group_keys_with_metadata_keys(
            reverse_records_by_source,
            ("translation_sense_text", "translation_english_text", "translation_note_text"),
        ),
    }


def _count_records_with_metadata_keys(
    records: Sequence[TranslationGlossRecord],
    metadata_keys: Sequence[str],
) -> int:
    return sum(
        1 for record in records if _record_has_any_metadata_key(record, metadata_keys=metadata_keys)
    )


def _count_group_keys_with_metadata_keys(
    record_groups: Mapping[str, Sequence[TranslationGlossRecord]],
    metadata_keys: Sequence[str],
) -> int:
    count = 0
    for records in record_groups.values():
        if any(
            _record_has_any_metadata_key(record, metadata_keys=metadata_keys) for record in records
        ):
            count += 1
    return count


def _record_has_any_metadata_key(
    record: TranslationGlossRecord,
    *,
    metadata_keys: Sequence[str],
) -> bool:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    for key in metadata_keys:
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if any(str(item or "").strip() for item in value):
                return True
        elif str(value or "").strip():
            return True
    return False
