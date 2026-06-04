#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: F405

from semantic_decision_rule_matrix_common import *  # noqa: F403
from semantic_decision_rule_matrix_context import *  # noqa: F403
from semantic_decision_rule_matrix_data import _normalize_ints, _threshold_label, _validate_config
from semantic_decision_rule_matrix_evidence import *  # noqa: F403
from semantic_decision_rule_matrix_metrics import *  # noqa: F403
from semantic_decision_rule_matrix_summary import _config_summary_row

_RUNTIME_BACKEND_FIT_CACHE: dict[str, RuntimeSimilarityBackend] = {}


def _runtime_backend_for_fit(
    *,
    scorer_id: str,
    model_name: str,
    fit_texts: Sequence[str],
) -> RuntimeSimilarityBackend:
    normalized_scorer_id = str(scorer_id or "").strip()
    normalized_model_name = str(model_name or "").strip()
    normalized_texts = [str(text or "").strip() for text in fit_texts if str(text or "").strip()]
    cache_payload = json.dumps(
        {
            "scorer_id": normalized_scorer_id,
            "model_name": normalized_model_name,
            "texts": normalized_texts,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    cache_key = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()
    cached = _RUNTIME_BACKEND_FIT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    backend = RuntimeSimilarityBackend(
        scorer_id=normalized_scorer_id,
        model_name=normalized_model_name,
    )
    backend.fit(normalized_texts)
    _RUNTIME_BACKEND_FIT_CACHE[cache_key] = backend
    return backend


def _evaluate_config(
    *,
    dataset: Mapping[str, object],
    config: Mapping[str, object],
    drop_source_families: Sequence[str] = (),
    threshold_override: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    resolved_config = dict(config)
    if threshold_override:
        resolved_config.update(dict(threshold_override))
    _validate_config(resolved_config)
    fit_scope = str(
        resolved_config.get("fit_scope") or dataset.get("default_fit_scope") or "whole_dataset"
    ).strip()
    resolved_config["fit_scope"] = fit_scope

    summary = _new_sentence_veto_summary()
    family_breakdown: dict[str, dict[str, object]] = {}
    suite_breakdown: dict[str, dict[str, object]] = {}
    slice_tag_breakdown: dict[str, dict[str, object]] = {}
    gold_winner_type_breakdown: dict[str, dict[str, object]] = {}
    case_rows: list[dict[str, object]] = []
    harmful_replace_rows: list[dict[str, object]] = []
    false_abstain_rows: list[dict[str, object]] = []
    winner_error_rows: list[dict[str, object]] = []
    backend_by_family_id: dict[str, RuntimeSimilarityBackend] = {}
    for _fit_group_id, fit_families in _fit_family_groups(dataset, fit_scope=fit_scope):
        fit_dataset = dict(dataset)
        fit_dataset["families"] = fit_families
        fit_texts = _collect_fit_texts(
            dataset=fit_dataset,
            config=resolved_config,
            drop_source_families=drop_source_families,
        )
        backend = _runtime_backend_for_fit(
            scorer_id=str(resolved_config.get("scorer_id") or "").strip(),
            model_name=str(resolved_config.get("model_name") or "").strip(),
            fit_texts=fit_texts,
        )
        for family in fit_families:
            if isinstance(family, Mapping):
                backend_by_family_id[str(family.get("family_id") or "").strip()] = backend

    for family in dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        backend = backend_by_family_id.get(family_id)
        if backend is None:
            raise ValueError(f"No similarity backend was fitted for family {family_id!r}.")
        active = dict(family.get("active") or {})
        shadows = [
            dict(shadow) for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)
        ]
        family_pos_tags = list(
            _resolve_sentence_veto_phrase_guard_pos_tags(
                active_sense=active,
                shadow_senses=shadows,
                phrase_guard_pos_scope=str(
                    resolved_config.get("phrase_guard_pos_scope") or "family_all"
                ),
            )
        )
        family_entry = family_breakdown.setdefault(
            family_id,
            {
                "family_id": family_id,
                "trigger": str(family.get("trigger") or "").strip(),
                "active_target": str(active.get("target_lemma") or "").strip(),
                "shadow_targets": [
                    str(shadow.get("target_lemma") or "").strip()
                    for shadow in shadows
                    if str(shadow.get("target_lemma") or "").strip()
                ],
                "summary": _new_sentence_veto_summary(),
            },
        )
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            row = _evaluate_case(
                family=family,
                case=case,
                backend=backend,
                config=resolved_config,
                family_pos_tags=family_pos_tags,
                drop_source_families=drop_source_families,
            )
            case_rows.append(row)
            summary_result = SimpleNamespace(**row)
            _accumulate_sentence_veto_summary(summary, result=summary_result)
            _accumulate_sentence_veto_summary(family_entry["summary"], result=summary_result)
            suite_id = str(row.get("evaluation_suite_id") or "default").strip() or "default"
            suite_entry = suite_breakdown.setdefault(
                suite_id,
                {"suite_id": suite_id, "summary": _new_sentence_veto_summary()},
            )
            _accumulate_sentence_veto_summary(suite_entry["summary"], result=summary_result)
            winner_entry = gold_winner_type_breakdown.setdefault(
                row["gold_winner_type"],
                {
                    "gold_winner_type": row["gold_winner_type"],
                    "summary": _new_sentence_veto_summary(),
                },
            )
            _accumulate_sentence_veto_summary(winner_entry["summary"], result=summary_result)
            for slice_tag in row["slice_tags"]:
                slice_entry = slice_tag_breakdown.setdefault(
                    slice_tag,
                    {"slice_tag": slice_tag, "summary": _new_sentence_veto_summary()},
                )
                _accumulate_sentence_veto_summary(slice_entry["summary"], result=summary_result)
            if row["predicted_decision"] == "replace" and row["gold_decision"] != "replace":
                _append_sample(harmful_replace_rows, row)
            if row["predicted_decision"] != "replace" and row["gold_decision"] == "replace":
                _append_sample(false_abstain_rows, row)
            if (
                row["gold_winner_type"] in {"active", "shadow"}
                and row["predicted_winner"] != row["gold_winner"]
            ):
                _append_sample(winner_error_rows, row)

    _finalize_sentence_veto_summary(summary)
    row_payload = _config_summary_row(
        config=resolved_config,
        summary=summary,
        case_rows=case_rows,
        family_breakdown=_finalize_sentence_veto_breakdown_rows(
            tuple(family_breakdown.values()),
            primary_sort_key="family_id",
        ),
        suite_breakdown=_finalize_sentence_veto_breakdown_rows(
            tuple(suite_breakdown.values()),
            primary_sort_key="suite_id",
        ),
        slice_tag_breakdown=_finalize_sentence_veto_breakdown_rows(
            tuple(slice_tag_breakdown.values()),
            primary_sort_key="slice_tag",
            sort_by_cases_desc=True,
        ),
        gold_winner_type_breakdown=_finalize_sentence_veto_breakdown_rows(
            tuple(gold_winner_type_breakdown.values()),
            primary_sort_key="gold_winner_type",
            preferred_order=("active", "shadow", "none", "phrase"),
        ),
        harmful_replace_rows=harmful_replace_rows,
        false_abstain_rows=false_abstain_rows,
        winner_error_rows=winner_error_rows,
        drop_source_families=drop_source_families,
        threshold_override=threshold_override,
    )
    return row_payload, case_rows


def _evaluate_case(
    *,
    family: Mapping[str, object],
    case: Mapping[str, object],
    backend: RuntimeSimilarityBackend,
    config: Mapping[str, object],
    family_pos_tags: Sequence[str],
    drop_source_families: Sequence[str],
) -> dict[str, object]:
    original_active = dict(family.get("active") or {})
    original_shadows = [
        dict(shadow) for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)
    ]
    active_sense, shadow_senses = _apply_evidence_control(
        active_sense=original_active,
        shadow_senses=original_shadows,
        evidence_control=str(config.get("evidence_control") or "normal"),
    )
    source_phrase = str(case.get("source_phrase") or family.get("trigger") or "").strip()
    context_views = _build_matrix_context_views(
        str(case.get("sentence") or "").strip(),
        source_phrase=source_phrase,
        mask_token=str(config.get("mask_token") or DEFAULT_SENTENCE_VETO_MASK_TOKEN),
        window_tokens=int(
            config.get("window_tokens") or DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
        ),
    )
    context_view = str(config.get("context_view") or "masked_sentence").strip()
    context_text = str(context_views.get(context_view) or "").strip()

    active_score = _score_sense(
        context_text=context_text,
        selector_context_text=_selector_context_text(context_views, config=config),
        sense=active_sense,
        winner_type="active",
        backend=backend,
        config=config,
        drop_source_families=drop_source_families,
    )
    shadow_scores = [
        _score_sense(
            context_text=context_text,
            selector_context_text=_selector_context_text(context_views, config=config),
            sense=shadow,
            winner_type="shadow",
            backend=backend,
            config=config,
            drop_source_families=drop_source_families,
        )
        for shadow in shadow_senses
    ]

    phrase_signals = extract_runtime_phrase_control_signals(
        str(case.get("sentence") or "").strip(),
        source_phrase=source_phrase,
        family_pos_tags=family_pos_tags,
    )
    decision = _apply_decision_rule(
        active_score=active_score,
        shadow_scores=shadow_scores,
        config=config,
        phrase_hit=bool(phrase_signals.phrase_preemption_hit),
        phrase_reason_code=str(phrase_signals.phrase_reason_code or ""),
    )

    original_active_id = str(original_active.get("sense_id") or "").strip()
    gold_winner = str(case.get("gold_winner") or "").strip()
    gold_winner_type = _classify_gold_winner_type(gold_winner, active_sense_id=original_active_id)
    gold_decision = str(case.get("gold_decision") or "").strip().lower()
    if gold_decision not in {"replace", "abstain"}:
        gold_decision = "replace" if gold_winner_type == "active" else "abstain"

    active_row_scores = list(active_score.row_scores)
    shadow_row_scores = [
        {
            "sense_id": score.sense_id,
            "target_lemma": score.target_lemma,
            "aggregate_score": _round_float(score.aggregate_score),
            "row_scores": list(score.row_scores),
        }
        for score in shadow_scores
    ]
    return {
        "config_id": str(config.get("config_id") or "").strip(),
        "case_id": str(case.get("case_id") or "").strip(),
        "original_case_id": str(case.get("original_case_id") or case.get("case_id") or "").strip(),
        "family_id": str(family.get("family_id") or "").strip(),
        "original_family_id": str(
            family.get("original_family_id") or family.get("family_id") or ""
        ).strip(),
        "evaluation_suite_id": str(
            case.get("evaluation_suite_id") or family.get("evaluation_suite_id") or "default"
        ).strip(),
        "evaluation_suite_role": str(
            case.get("evaluation_suite_role") or family.get("evaluation_suite_role") or ""
        ).strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "sentence": str(case.get("sentence") or "").strip(),
        "source_phrase": source_phrase,
        "gold_decision": gold_decision,
        "gold_winner": gold_winner,
        "gold_winner_type": gold_winner_type,
        "predicted_decision": decision["predicted_decision"],
        "predicted_winner": decision["predicted_winner"],
        "predicted_winner_type": decision["predicted_winner_type"],
        "active_score": _round_float(active_score.aggregate_score),
        "strongest_shadow_score": _round_float(decision["strongest_shadow_score"]),
        "margin": _round_float(decision["margin"]),
        "active_ratio": _round_float(decision["active_ratio"]),
        "active_softmax_probability": _round_float(decision["active_softmax_probability"]),
        "pairwise_win_rate": _round_float(decision["pairwise_win_rate"]),
        "strongest_shadow_id": decision["strongest_shadow_id"],
        "replacement_confidence": _round_float(decision["replacement_confidence"]),
        "context_text": context_text,
        "active_evidence_trace": active_row_scores,
        "shadow_evidence_traces": shadow_row_scores,
        "phrase_preemption_hit": bool(phrase_signals.phrase_preemption_hit),
        "matched_phrase_pattern": str(phrase_signals.matched_phrase_pattern or ""),
        "phrase_reason_code": str(phrase_signals.phrase_reason_code or ""),
        "reason_codes": decision["reason_codes"],
        "active_rescue_applied": False,
        "slice_tags": _normalize_string_list(case.get("slice_tags")),
        "slice_dimensions": _normalize_slice_dimensions(case.get("slice_dimensions")),
        "split": _case_split(
            str(case.get("case_id") or "").strip(),
            split_modulo=int(config.get("split_modulo") or 4),
            locked_eval_remainders=_normalize_ints(
                config.get("locked_eval_remainders"), default=(0,)
            ),
        ),
        "notes": str(case.get("notes") or "").strip(),
    }


def _build_threshold_sensitivity_rows(
    *,
    dataset: Mapping[str, object],
    config: Mapping[str, object],
) -> list[dict[str, object]]:
    grid = config.get("threshold_grid")
    if not isinstance(grid, Sequence) or isinstance(grid, (str, bytes)) or not grid:
        grid = (
            {"threshold_label": "a0_m0", "min_active_score": 0.0, "min_margin": 0.0},
            {"threshold_label": "a0_m005", "min_active_score": 0.0, "min_margin": 0.005},
            {"threshold_label": "a005_m0", "min_active_score": 0.05, "min_margin": 0.0},
            {"threshold_label": "a035_m005", "min_active_score": 0.35, "min_margin": 0.05},
        )
    rows: list[dict[str, object]] = []
    for raw_threshold in grid:
        if not isinstance(raw_threshold, Mapping):
            continue
        label = str(raw_threshold.get("threshold_label") or "").strip()
        override = {key: value for key, value in raw_threshold.items() if key != "threshold_label"}
        row, _cases = _evaluate_config(
            dataset=dataset,
            config=config,
            threshold_override=override,
        )
        rows.append(
            {
                "config_id": row.get("config_id"),
                "threshold_label": label or _threshold_label(override),
                "min_active_score": row.get("min_active_score"),
                "min_margin": row.get("min_margin"),
                "ratio_threshold": row.get("ratio_threshold"),
                "softmax_threshold": row.get("softmax_threshold"),
                "pairwise_min_win_rate": row.get("pairwise_min_win_rate"),
                "harmful_replace_count": row.get("harmful_replace_count"),
                "false_abstain_count": row.get("false_abstain_count"),
                "decision_accuracy": row.get("decision_accuracy"),
                "winner_accuracy": row.get("winner_accuracy"),
                "objective_score": row.get("objective_score"),
            }
        )
    return rows


def _build_source_dropout_rows(
    *,
    dataset: Mapping[str, object],
    config: Mapping[str, object],
) -> list[dict[str, object]]:
    source_families = _normalize_string_list(config.get("source_dropout_families"))
    if not source_families:
        source_families = ["sense_label", "definition", "auxiliary", "qualifier", "target_lemma"]
    rows: list[dict[str, object]] = []
    for source_family in source_families:
        row, _cases = _evaluate_config(
            dataset=dataset,
            config=config,
            drop_source_families=(source_family,),
        )
        rows.append(
            {
                "config_id": row.get("config_id"),
                "dropped_source_family": source_family,
                "harmful_replace_count": row.get("harmful_replace_count"),
                "false_abstain_count": row.get("false_abstain_count"),
                "decision_accuracy": row.get("decision_accuracy"),
                "winner_accuracy": row.get("winner_accuracy"),
                "objective_score": row.get("objective_score"),
            }
        )
    return rows


def _fit_family_groups(
    dataset: Mapping[str, object],
    *,
    fit_scope: str,
) -> list[tuple[str, list[Mapping[str, object]]]]:
    families = [family for family in dataset.get("families", ()) if isinstance(family, Mapping)]
    if str(fit_scope or "").strip() != "per_evaluation_suite":
        return [("whole_dataset", families)]
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for family in families:
        suite_id = str(family.get("evaluation_suite_id") or "default").strip() or "default"
        grouped[suite_id].append(family)
    return [(suite_id, grouped[suite_id]) for suite_id in sorted(grouped)]


def _collect_fit_texts(
    *,
    dataset: Mapping[str, object],
    config: Mapping[str, object],
    drop_source_families: Sequence[str],
) -> list[str]:
    texts: list[str] = []
    context_view = str(config.get("context_view") or "masked_sentence").strip()
    for family in dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        active = dict(family.get("active") or {})
        shadows = [
            dict(shadow) for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)
        ]
        active, shadows = _apply_evidence_control(
            active_sense=active,
            shadow_senses=shadows,
            evidence_control=str(config.get("evidence_control") or "normal"),
        )
        for sense in (active, *shadows):
            for row in _evidence_rows_for_sense(sense, config=config):
                if row.source_family not in drop_source_families:
                    texts.append(row.text)
                    if str(row.selector_text or "").strip():
                        texts.append(row.selector_text)
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            context_views = _build_matrix_context_views(
                str(case.get("sentence") or "").strip(),
                source_phrase=str(case.get("source_phrase") or family.get("trigger") or "").strip(),
                mask_token=str(config.get("mask_token") or DEFAULT_SENTENCE_VETO_MASK_TOKEN),
                window_tokens=int(
                    config.get("window_tokens") or DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS
                ),
            )
            texts.append(str(context_views.get(context_view) or "").strip())
            selector_context_view = str(
                config.get("evidence_selector_context_view") or context_view
            ).strip()
            texts.append(str(context_views.get(selector_context_view) or "").strip())
    return [text for text in texts if str(text or "").strip()]
