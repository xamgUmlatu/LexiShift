#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403
from semantic_decision_rule_matrix_context import *  # noqa: F403
from semantic_decision_rule_matrix_metrics import *  # noqa: F403


def _validate_config(config: Mapping[str, object]) -> None:
    required = {
        "config_id",
        "scorer_id",
        "context_view",
        "sense_representation",
        "aggregation_rule",
        "decision_rule",
        "phrase_handling",
    }
    missing = [key for key in required if not str(config.get(key) or "").strip()]
    if missing:
        raise ValueError(f"Decision-rule matrix config is missing required keys: {missing!r}")
    if str(config.get("aggregation_rule")) not in SUPPORTED_AGGREGATION_RULES:
        raise ValueError(f"Unsupported aggregation rule: {config.get('aggregation_rule')!r}")
    if str(config.get("decision_rule")) not in SUPPORTED_DECISION_RULES:
        raise ValueError(f"Unsupported decision rule: {config.get('decision_rule')!r}")
    if str(config.get("phrase_handling")) not in SUPPORTED_PHRASE_HANDLING:
        raise ValueError(f"Unsupported phrase handling: {config.get('phrase_handling')!r}")
    if str(config.get("evidence_control") or "normal") not in SUPPORTED_EVIDENCE_CONTROLS:
        raise ValueError(f"Unsupported evidence control: {config.get('evidence_control')!r}")


def _load_matrix_dataset(
    manifest: Mapping[str, object],
    *,
    default_dataset_path: Path,
    apply_source_evidence: bool = True,
) -> dict[str, object]:
    suites = manifest.get("evaluation_suites")
    if not isinstance(suites, Sequence) or isinstance(suites, (str, bytes)) or not suites:
        dataset = load_sentence_veto_dataset(default_dataset_path)
        dataset["evaluation_suites"] = (
            {
                "suite_id": "default",
                "suite_role": "default_dataset",
                "dataset_path": str(default_dataset_path),
                "family_count": len(dataset.get("families", ())),
                "case_count": _dataset_case_count(dataset),
            },
        )
        if apply_source_evidence:
            return _apply_matrix_source_evidence(dataset, manifest=manifest)
        return dataset

    combined_families: list[dict[str, object]] = []
    suite_rows: list[dict[str, object]] = []
    pair = ""
    base_cache: dict[Path, dict[str, object]] = {}
    for index, raw_suite in enumerate(suites, start=1):
        if not isinstance(raw_suite, Mapping):
            raise ValueError("Every evaluation_suites entry must be an object.")
        suite_id = str(raw_suite.get("suite_id") or f"suite_{index}").strip()
        suite_role = str(raw_suite.get("suite_role") or raw_suite.get("role") or "").strip()
        base_dataset_path = _resolve_project_path(
            raw_suite.get("base_dataset_path"),
            default=default_dataset_path,
        )
        if raw_suite.get("dataset_path"):
            suite_path = _resolve_project_path(
                raw_suite.get("dataset_path"), default=base_dataset_path
            )
            suite_dataset = load_sentence_veto_dataset(suite_path)
            source_paths = {"dataset_path": str(suite_path)}
        else:
            case_path_value = (
                raw_suite.get("case_dataset_path")
                or raw_suite.get("case_path")
                or raw_suite.get("cases_path")
            )
            if not str(case_path_value or "").strip():
                raise ValueError(
                    f"Evaluation suite {suite_id!r} needs `dataset_path` or `case_dataset_path`."
                )
            case_path = _resolve_project_path(
                case_path_value,
                default=default_dataset_path,
            )
            base_dataset = base_cache.get(base_dataset_path)
            if base_dataset is None:
                base_dataset = load_sentence_veto_dataset(base_dataset_path)
                base_cache[base_dataset_path] = base_dataset
            case_payload = _load_json(case_path)
            suite_dataset = _build_case_suite_dataset(
                base_dataset=base_dataset,
                case_payload=case_payload,
            )
            source_paths = {
                "base_dataset_path": str(base_dataset_path),
                "case_dataset_path": str(case_path),
            }
        pair = pair or str(suite_dataset.get("pair") or "").strip()
        annotated_families = _annotate_suite_families(
            suite_dataset.get("families", ()),
            suite_id=suite_id,
            suite_role=suite_role,
        )
        combined_families.extend(annotated_families)
        suite_rows.append(
            {
                "suite_id": suite_id,
                "suite_role": suite_role,
                **source_paths,
                "dataset_id": str(suite_dataset.get("dataset_id") or "").strip(),
                "family_count": len(annotated_families),
                "case_count": _dataset_case_count({"families": annotated_families}),
            }
        )
    if not combined_families:
        raise ValueError("Evaluation suites resolved no families.")
    combined_dataset = {
        "schema_version": 1,
        "pair": pair or "en-es",
        "dataset_id": str(manifest.get("matrix_id") or "semantic_decision_matrix")
        + "_evaluation_suites",
        "families": combined_families,
        "evaluation_suites": suite_rows,
        "default_fit_scope": "per_evaluation_suite",
    }
    if apply_source_evidence:
        return _apply_matrix_source_evidence(combined_dataset, manifest=manifest)
    return combined_dataset


def _matrix_dataset_for_config(
    *,
    base_dataset: Mapping[str, object],
    manifest: Mapping[str, object],
    config: Mapping[str, object],
    cache: dict[tuple[tuple[str, ...], str, int], dict[str, object]],
) -> dict[str, object]:
    scope_manifest = _source_evidence_scope_manifest(manifest=manifest, config=config)
    paths = _matrix_source_evidence_paths(scope_manifest)
    defaults = (
        scope_manifest.get("defaults")
        if isinstance(scope_manifest.get("defaults"), Mapping)
        else {}
    )
    mask_token = str(defaults.get("mask_token") or DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    window_tokens = int(
        defaults.get("window_tokens") or DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
    )
    cache_key = (tuple(str(path) for path in paths), mask_token, window_tokens)
    cached = cache.get(cache_key)
    if cached is None:
        cached = _apply_matrix_source_evidence(base_dataset, manifest=scope_manifest)
        cache[cache_key] = cached
    return cached


def _source_evidence_scope_manifest(
    *,
    manifest: Mapping[str, object],
    config: Mapping[str, object],
) -> dict[str, object]:
    for key in ("source_evidence_batch_paths", "evidence_batch_paths", "source_evidence_batches"):
        if key in config:
            return {
                "source_evidence_batch_paths": config.get(key) or (),
                "defaults": dict(config),
            }
    return dict(manifest)


def _source_evidence_scope_id(
    *,
    manifest: Mapping[str, object],
    config: Mapping[str, object],
) -> str:
    explicit = str(config.get("source_evidence_scope_id") or "").strip()
    if explicit:
        return explicit
    if any(
        key in config
        for key in (
            "source_evidence_batch_paths",
            "evidence_batch_paths",
            "source_evidence_batches",
        )
    ):
        return str(config.get("config_id") or "row_source_scope").strip()
    return str(manifest.get("source_evidence_scope_id") or "manifest_default").strip()


def _source_evidence_scope_rows(
    cache: Mapping[tuple[tuple[str, ...], str, int], Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (cache_key, dataset) in enumerate(cache.items(), start=1):
        paths, mask_token, window_tokens = cache_key
        batches = list(dataset.get("source_evidence_batches") or ())
        rows.append(
            {
                "scope_index": index,
                "path_count": len(paths),
                "paths": list(paths),
                "mask_token": mask_token,
                "window_tokens": window_tokens,
                "batch_count": len(batches),
                "attached_row_count": sum(
                    int(batch.get("attached_row_count") or 0)
                    for batch in batches
                    if isinstance(batch, Mapping)
                ),
                "source_evidence_batches": batches,
            }
        )
    return sorted(rows, key=lambda row: (row["paths"], row["mask_token"], row["window_tokens"]))


def _apply_matrix_source_evidence(
    dataset: Mapping[str, object],
    *,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    paths = _matrix_source_evidence_paths(manifest)
    if not paths:
        return dict(dataset)
    defaults = manifest.get("defaults") if isinstance(manifest.get("defaults"), Mapping) else {}
    mask_token = str(defaults.get("mask_token") or DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    window_tokens = int(
        defaults.get("window_tokens") or DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
    )
    rows_by_sense: dict[str, list[dict[str, object]]] = defaultdict(list)
    batch_rows: list[dict[str, object]] = []
    for path in paths:
        payload = _load_json(path)
        attached_count = 0
        payload_rows = payload.get("rows")
        if not isinstance(payload_rows, Sequence) or isinstance(payload_rows, (str, bytes)):
            payload_rows = ()
        for raw_row in payload_rows:
            if not isinstance(raw_row, Mapping):
                continue
            sense_id = _source_evidence_row_sense_id(raw_row)
            evidence_text = str(raw_row.get("evidence_text") or "").strip()
            if not sense_id or not evidence_text:
                continue
            trigger = str(raw_row.get("normalized_trigger") or raw_row.get("trigger") or "").strip()
            selector_views = _build_matrix_context_views(
                evidence_text,
                source_phrase=trigger,
                mask_token=mask_token,
                window_tokens=window_tokens,
            )
            rows_by_sense[sense_id].append(
                {
                    "row_id": str(
                        raw_row.get("row_id") or raw_row.get("evidence_id") or ""
                    ).strip(),
                    "evidence_id": str(raw_row.get("evidence_id") or "").strip(),
                    "evidence_text": evidence_text,
                    "source_family": str(raw_row.get("source_family") or "source_row").strip(),
                    "source_id": str(raw_row.get("source_id") or "").strip(),
                    "source_type": str(raw_row.get("source_type") or "").strip(),
                    "relation_type": str(raw_row.get("relation_type") or "").strip(),
                    "trigger": trigger,
                    "selector_views": selector_views,
                }
            )
            attached_count += 1
        batch_rows.append(
            {
                "path": str(path),
                "sha256": _file_sha256(path),
                "row_count": int(payload.get("row_count") or len(payload.get("rows", ()) or ())),
                "attached_row_count": attached_count,
            }
        )

    copied_dataset = deepcopy(dict(dataset))
    for family in copied_dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        for sense in (
            [family.get("active")] if isinstance(family.get("active"), Mapping) else []
        ) + [shadow for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)]:
            sense_id = str(sense.get("sense_id") or "").strip()
            source_rows = rows_by_sense.get(sense_id, [])
            if not source_rows:
                continue
            existing = sense.get("matrix_source_rows")
            merged_rows = (
                [dict(row) for row in existing if isinstance(row, Mapping)]
                if isinstance(existing, Sequence) and not isinstance(existing, (str, bytes))
                else []
            )
            merged_rows.extend(deepcopy(source_rows))
            sense["matrix_source_rows"] = merged_rows
    copied_dataset["source_evidence_batches"] = batch_rows
    return copied_dataset


def _matrix_source_evidence_paths(manifest: Mapping[str, object]) -> list[Path]:
    raw_paths = (
        manifest.get("source_evidence_batch_paths")
        or manifest.get("evidence_batch_paths")
        or manifest.get("source_evidence_batches")
        or ()
    )
    if isinstance(raw_paths, (str, bytes)) or not isinstance(raw_paths, Sequence):
        raw_paths = (raw_paths,)
    paths: list[Path] = []
    for raw_path in raw_paths:
        path_value = raw_path
        if isinstance(raw_path, Mapping):
            path_value = raw_path.get("path") or raw_path.get("batch_path")
        if not str(path_value or "").strip():
            continue
        paths.append(_resolve_project_path(path_value, default=DEFAULT_DATASET))
    return paths


def _source_evidence_row_sense_id(row: Mapping[str, object]) -> str:
    metadata = row.get("metadata")
    if isinstance(metadata, Mapping):
        candidate_sense_id = str(metadata.get("candidate_sense_id") or "").strip()
        if candidate_sense_id:
            return candidate_sense_id
    hint = row.get("candidate_sense_hint")
    if isinstance(hint, Mapping):
        target_key = str(hint.get("target_key") or "").strip()
        if target_key:
            return target_key
    return ""


def _build_case_suite_dataset(
    *,
    base_dataset: Mapping[str, object],
    case_payload: Mapping[str, object],
) -> dict[str, object]:
    base_by_family = {
        str(family.get("family_id") or "").strip(): family
        for family in base_dataset.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }
    families: list[dict[str, object]] = []
    for case_family in case_payload.get("families", ()):
        if not isinstance(case_family, Mapping):
            continue
        family_id = str(case_family.get("family_id") or "").strip()
        base_family = base_by_family.get(family_id)
        if not isinstance(base_family, Mapping):
            raise ValueError(f"Case-suite family {family_id!r} is missing from the base dataset.")
        family = _copy_family_without_cases(base_family)
        cases = [dict(case) for case in case_family.get("cases", ()) if isinstance(case, Mapping)]
        _validate_cases_against_family(family, cases)
        family["cases"] = cases
        families.append(family)
    if not families:
        raise ValueError("Case-suite payload resolved no families.")
    return {
        "schema_version": 1,
        "pair": str(case_payload.get("pair") or base_dataset.get("pair") or "en-es").strip(),
        "dataset_id": str(case_payload.get("dataset_id") or "case_suite").strip(),
        "families": families,
    }


def _annotate_suite_families(
    families: object,
    *,
    suite_id: str,
    suite_role: str,
) -> list[dict[str, object]]:
    annotated: list[dict[str, object]] = []
    for family in families if isinstance(families, Sequence) else ():
        if not isinstance(family, Mapping):
            continue
        original_family_id = str(family.get("family_id") or "").strip()
        copied_family = deepcopy(dict(family))
        copied_family["original_family_id"] = original_family_id
        copied_family["family_id"] = f"{suite_id}::{original_family_id}"
        copied_family["evaluation_suite_id"] = suite_id
        copied_family["evaluation_suite_role"] = suite_role
        copied_cases: list[dict[str, object]] = []
        for case in copied_family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            copied_case = deepcopy(dict(case))
            original_case_id = str(copied_case.get("case_id") or "").strip()
            copied_case["original_case_id"] = original_case_id
            copied_case["case_id"] = f"{suite_id}::{original_case_id}"
            copied_case["evaluation_suite_id"] = suite_id
            copied_case["evaluation_suite_role"] = suite_role
            copied_case["slice_tags"] = [
                *_normalize_string_list(copied_case.get("slice_tags")),
                f"suite:{suite_id}",
            ]
            dimensions = copied_case.get("slice_dimensions")
            copied_dimensions = (
                deepcopy(dict(dimensions)) if isinstance(dimensions, Mapping) else {}
            )
            copied_dimensions.setdefault("evaluation_suite", [suite_id])
            if suite_role:
                copied_dimensions.setdefault("evaluation_suite_role", [suite_role])
            copied_case["slice_dimensions"] = copied_dimensions
            copied_cases.append(copied_case)
        copied_family["cases"] = copied_cases
        annotated.append(copied_family)
    return annotated


def _copy_family_without_cases(family: Mapping[str, object]) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active": deepcopy(dict(family.get("active") or {})),
        "shadows": [
            deepcopy(dict(shadow))
            for shadow in family.get("shadows", ())
            if isinstance(shadow, Mapping)
        ],
        "cases": [],
    }


def _validate_cases_against_family(
    family: Mapping[str, object],
    cases: Sequence[Mapping[str, object]],
) -> None:
    family_id = str(family.get("family_id") or "").strip()
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    active_sense_id = str(active.get("sense_id") or "").strip()
    shadow_ids = {
        str(shadow.get("sense_id") or "").strip()
        for shadow in family.get("shadows", ())
        if isinstance(shadow, Mapping) and str(shadow.get("sense_id") or "").strip()
    }
    if not cases:
        raise ValueError(f"Case-suite family {family_id!r} has no cases.")
    for case in cases:
        case_id = str(case.get("case_id") or "").strip()
        sentence = str(case.get("sentence") or "").strip()
        source_phrase = str(case.get("source_phrase") or "").strip()
        gold_winner = str(case.get("gold_winner") or "").strip()
        gold_decision = str(case.get("gold_decision") or "").strip().lower()
        if not case_id or not sentence or not source_phrase or not gold_winner:
            raise ValueError(f"Case-suite family {family_id!r} has a case missing fields.")
        if gold_decision and gold_decision not in {"replace", "abstain"}:
            raise ValueError(
                f"Case-suite case {case_id!r} has unsupported gold_decision {gold_decision!r}."
            )
        if gold_winner not in {"none", active_sense_id} and gold_winner not in shadow_ids:
            raise ValueError(
                f"Case-suite case {case_id!r} gold_winner {gold_winner!r} does not match "
                f"family {family_id!r}."
            )


def _dataset_case_count(dataset: Mapping[str, object]) -> int:
    return sum(
        len([case for case in family.get("cases", ()) if isinstance(case, Mapping)])
        for family in dataset.get("families", ())
        if isinstance(family, Mapping)
    )


def _build_input_fingerprint(
    *,
    manifest_path: Path,
    dataset_path: Path,
    dataset: Mapping[str, object],
    source_evidence_scopes: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    families = dataset.get("families") if isinstance(dataset.get("families"), Sequence) else []
    case_ids = [
        str(case.get("case_id") or "").strip()
        for family in families
        if isinstance(family, Mapping)
        for case in family.get("cases", ())
        if isinstance(case, Mapping)
    ]
    sense_ids = []
    for family in families:
        if not isinstance(family, Mapping):
            continue
        active = family.get("active")
        if isinstance(active, Mapping):
            sense_ids.append(str(active.get("sense_id") or "").strip())
        for shadow in family.get("shadows", ()):
            if isinstance(shadow, Mapping):
                sense_ids.append(str(shadow.get("sense_id") or "").strip())
    return {
        "manifest_sha256": _file_sha256(manifest_path),
        "dataset_sha256": _file_sha256(dataset_path),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "pair": str(dataset.get("pair") or "").strip(),
        "family_count": len(families),
        "case_count": len(case_ids),
        "case_ids_sha256": _text_sha256("\n".join(sorted(case_ids))),
        "sense_ids_sha256": _text_sha256("\n".join(sorted(sense_ids))),
        "evaluation_suite_count": len(_as_mapping_rows(dataset.get("evaluation_suites"))),
        "evaluation_suites": _fingerprint_evaluation_suites(dataset.get("evaluation_suites")),
        "source_evidence_batches": list(dataset.get("source_evidence_batches") or ()),
        "source_evidence_scopes": [dict(row) for row in source_evidence_scopes],
    }


def _fingerprint_evaluation_suites(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for suite in _as_mapping_rows(value):
        row = dict(suite)
        for key in ("dataset_path", "base_dataset_path", "case_dataset_path"):
            path_text = str(suite.get(key) or "").strip()
            if path_text:
                row[f"{key}_sha256"] = _file_sha256(Path(path_text))
        rows.append(row)
    return rows


def _manifest_rows(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    rows = manifest.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("Decision-rule matrix manifest must include a non-empty `rows` list.")
    normalized = [dict(row) for row in rows if isinstance(row, Mapping)]
    if len(normalized) != len(rows):
        raise ValueError("Every decision-rule matrix manifest row must be an object.")
    expanded: list[dict[str, object]] = []
    for raw_row in normalized:
        expanded.extend(_expand_manifest_row(raw_row))
    return expanded


def _expand_manifest_row(raw_row: Mapping[str, object]) -> list[dict[str, object]]:
    parameter_grid = raw_row.get("parameter_grid")
    base_row = {key: value for key, value in raw_row.items() if key != "parameter_grid"}
    base_row.setdefault(
        "algorithm_family",
        str(base_row.get("decision_rule") or base_row.get("config_id") or "").strip(),
    )
    if not parameter_grid:
        row = dict(base_row)
        row.setdefault("parameter_set_id", "single")
        return [row]
    parameter_rows = _parameter_grid_rows(parameter_grid)
    expanded: list[dict[str, object]] = []
    base_config_id = str(base_row.get("config_id") or "").strip()
    for index, parameter_row in enumerate(parameter_rows, start=1):
        parameter_set_id = str(parameter_row.pop("parameter_set_id", "") or "").strip()
        if not parameter_set_id:
            parameter_set_id = _parameter_set_id(parameter_row, fallback=f"p{index:03d}")
        row = dict(base_row)
        row.update(parameter_row)
        row["parameter_set_id"] = parameter_set_id
        if base_config_id and not str(parameter_row.get("config_id") or "").strip():
            row["config_id"] = f"{base_config_id}:{parameter_set_id}"
        expanded.append(row)
    return expanded


def _parameter_grid_rows(parameter_grid: object) -> list[dict[str, object]]:
    if isinstance(parameter_grid, Mapping):
        keys = [str(key) for key in parameter_grid.keys()]
        values: list[list[object]] = []
        for key in keys:
            raw_values = parameter_grid.get(key)
            if not isinstance(raw_values, Sequence) or isinstance(raw_values, (str, bytes)):
                raise ValueError(f"Parameter grid field {key!r} must be a list.")
            values.append(list(raw_values))
        return [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    if isinstance(parameter_grid, Sequence) and not isinstance(parameter_grid, (str, bytes)):
        rows = [dict(row) for row in parameter_grid if isinstance(row, Mapping)]
        if len(rows) != len(parameter_grid):
            raise ValueError("Every parameter_grid row must be an object.")
        return rows
    raise ValueError("parameter_grid must be either an object of lists or a list of objects.")


def _parameter_set_id(parameter_row: Mapping[str, object], *, fallback: str) -> str:
    if not parameter_row:
        return fallback
    prefixes = {
        "min_active_score": "a",
        "min_margin": "m",
        "ratio_threshold": "r",
        "softmax_threshold": "p",
        "softmax_temperature": "t",
        "pairwise_min_win_rate": "w",
    }
    parts = []
    for key, value in parameter_row.items():
        if key == "config_id":
            continue
        parts.append(f"{prefixes.get(str(key), str(key))}{_format_parameter_value(value)}")
    return "__".join(parts) or fallback


def _format_parameter_value(value: object) -> str:
    if isinstance(value, float):
        text = f"{value:.6g}"
    else:
        text = str(value)
    return (
        text.replace("-", "neg")
        .replace(".", "_")
        .replace("+", "")
        .replace(" ", "")
        .replace("/", "_")
    )


def _merge_defaults(defaults: Mapping[str, object], row: Mapping[str, object]) -> dict[str, object]:
    merged = dict(defaults)
    merged.update(dict(row))
    merged.setdefault("evidence_control", "normal")
    merged.setdefault("min_active_score", 0.0)
    merged.setdefault("min_margin", 0.0)
    merged.setdefault("ratio_threshold", 1.0)
    merged.setdefault("softmax_threshold", 0.5)
    merged.setdefault("pairwise_min_win_rate", 0.75)
    merged.setdefault("top_k", 2)
    merged.setdefault("phrase_guard_pos_scope", "family_all")
    merged.setdefault("window_tokens", DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS)
    merged.setdefault("mask_token", DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    return merged


def _normalize_ints(value: object, *, default: Sequence[int]) -> list[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return list(default)
    normalized: list[int] = []
    for item in value:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized or list(default)


def _threshold_label(value: Mapping[str, object]) -> str:
    parts = []
    for key in ("min_active_score", "min_margin", "ratio_threshold", "softmax_threshold"):
        if key in value:
            parts.append(f"{key}={value[key]}")
    return ",".join(parts) or "default"
