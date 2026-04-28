#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    RuntimeSimilarityBackend,
    build_runtime_context_views,
    extract_runtime_phrase_control_signals,
)
from semantic_routing_sentence_veto_helpers import (  # noqa: E402
    _accumulate_sentence_veto_summary,
    _append_sample,
    _finalize_sentence_veto_breakdown_rows,
    _finalize_sentence_veto_summary,
    _new_sentence_veto_summary,
    _normalize_slice_dimensions,
    _normalize_string_list,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    _resolve_sentence_veto_phrase_guard_pos_tags,
    load_sentence_veto_dataset,
)

DEFAULT_MANIFEST = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_decision_rule_matrix_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_decision_rule_matrix_en_es_latest.md"
)
DEFAULT_DATASET = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_sentence_veto_v10.json"
)

SUPPORTED_AGGREGATION_RULES = {
    "single_concatenated_text",
    "max_row_score",
    "mean_row_score",
    "top_k_mean",
    "source_weighted_top_k",
    "definition_example_agreement",
    "context_selected_max_row_score",
    "context_selected_top_k_mean",
    "context_selected_source_weighted_top_k",
}
SUPPORTED_DECISION_RULES = {
    "active_minus_strongest_shadow",
    "active_ratio_strongest_shadow",
    "softmax_probability",
    "pairwise_active_beats_all_shadows",
    "pairwise_active_beats_most_shadows",
    "shadow_veto_only",
}
SUPPORTED_EVIDENCE_CONTROLS = {
    "normal",
    "active_only_source",
    "shadow_only_source",
    "no_shadow_competition",
    "shuffled_labels",
    "target_lemma_only",
}
SUPPORTED_PHRASE_HANDLING = {
    "semantic_only",
    "phrase_first",
    "phrase_override",
    "phrase_as_shadow",
}

DEFAULT_SOURCE_WEIGHTS = {
    "all_evidence": 1.0,
    "sense_label": 0.8,
    "definition": 1.0,
    "qualifier": 0.6,
    "auxiliary": 0.5,
    "target_lemma": 0.25,
    "installed_translation_pack": 0.8,
    "wordnet_example_frames": 1.0,
    "wiktextract_example_frames": 1.0,
    "source_row": 1.0,
    "empty": 0.0,
}
_EXPERIMENT_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+|___")
_DETERMINERS = frozenset(
    {
        "a",
        "an",
        "her",
        "his",
        "its",
        "my",
        "our",
        "that",
        "the",
        "their",
        "these",
        "this",
        "those",
        "your",
    }
)
_PREPOSITIONS = frozenset(
    {
        "about",
        "after",
        "at",
        "before",
        "beside",
        "by",
        "during",
        "for",
        "from",
        "in",
        "into",
        "near",
        "of",
        "off",
        "on",
        "out",
        "over",
        "past",
        "through",
        "to",
        "toward",
        "under",
        "up",
        "with",
        "within",
        "without",
    }
)
_MODALS = frozenset(
    {
        "can",
        "cannot",
        "can't",
        "could",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "will",
        "would",
    }
)
_NEGATIONS = frozenset({"no", "not", "never", "n't", "without"})
_BE_VERBS = frozenset({"am", "are", "be", "been", "being", "is", "was", "were"})
_AUXILIARY_VERBS = frozenset(
    {
        "am",
        "are",
        "be",
        "been",
        "being",
        "did",
        "do",
        "does",
        "had",
        "has",
        "have",
        "is",
        "was",
        "were",
    }
)
_PRONOUNS = frozenset(
    {
        "he",
        "her",
        "him",
        "i",
        "it",
        "me",
        "she",
        "them",
        "they",
        "us",
        "we",
        "you",
    }
)
_PARTICLES = frozenset(
    {
        "away",
        "back",
        "down",
        "in",
        "off",
        "on",
        "out",
        "over",
        "through",
        "up",
    }
)


@dataclass(frozen=True)
class EvidenceRow:
    row_id: str
    source_family: str
    text: str
    weight: float
    selector_text: str = ""


@dataclass(frozen=True)
class SenseScore:
    sense_id: str
    target_lemma: str
    winner_type: str
    aggregate_score: float
    row_scores: tuple[dict[str, object], ...]


def build_decision_rule_matrix_report(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, object]:
    manifest = _load_json(manifest_path)
    dataset_path = _resolve_project_path(manifest.get("dataset_path"), default=DEFAULT_DATASET)
    base_dataset = _load_matrix_dataset(
        manifest,
        default_dataset_path=dataset_path,
        apply_source_evidence=False,
    )
    dataset_cache: dict[tuple[tuple[str, ...], str, int], dict[str, object]] = {}
    dataset = _matrix_dataset_for_config(
        base_dataset=base_dataset,
        manifest=manifest,
        config={},
        cache=dataset_cache,
    )
    defaults = manifest.get("defaults") if isinstance(manifest.get("defaults"), Mapping) else {}
    rows = _manifest_rows(manifest)
    include_case_results = bool(manifest.get("include_case_results", True))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    config_rows: list[dict[str, object]] = []
    case_results: list[dict[str, object]] = []
    threshold_sensitivity: list[dict[str, object]] = []
    source_dropout: list[dict[str, object]] = []

    for manifest_index, raw_config in enumerate(rows):
        config = _merge_defaults(defaults, raw_config)
        config["manifest_index"] = manifest_index
        config_dataset = _matrix_dataset_for_config(
            base_dataset=base_dataset,
            manifest=manifest,
            config=config,
            cache=dataset_cache,
        )
        config["source_evidence_scope_id"] = _source_evidence_scope_id(
            manifest=manifest,
            config=config,
        )
        config["source_evidence_batches"] = list(
            config_dataset.get("source_evidence_batches") or ()
        )
        config_row, config_cases = _evaluate_config(dataset=config_dataset, config=config)
        config_rows.append(config_row)
        case_results.extend(config_cases)

        if bool(config.get("threshold_sensitivity")):
            threshold_sensitivity.extend(
                _build_threshold_sensitivity_rows(dataset=config_dataset, config=config)
            )
        if bool(config.get("source_dropout")):
            source_dropout.extend(_build_source_dropout_rows(dataset=config_dataset, config=config))

    config_rows.sort(key=_rank_key)
    incumbent = _select_incumbent(config_rows)
    report = {
        "schema_version": 1,
        "status": "ok",
        "matrix_id": str(manifest.get("matrix_id") or "semantic_decision_rule_matrix_en_es"),
        "generated_at": generated_at,
        "manifest_path": str(manifest_path),
        "dataset_path": str(dataset_path),
        "evaluation_suites": list(dataset.get("evaluation_suites") or ()),
        "source_evidence_batches": list(dataset.get("source_evidence_batches") or ()),
        "source_evidence_scopes": _source_evidence_scope_rows(dataset_cache),
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "input_fingerprint": _build_input_fingerprint(
            manifest_path=manifest_path,
            dataset_path=dataset_path,
            dataset=dataset,
            source_evidence_scopes=_source_evidence_scope_rows(dataset_cache),
        ),
        "row_count": len(config_rows),
        "case_result_count": len(case_results),
        "case_results_omitted": not include_case_results,
        "config_rows": config_rows,
        "case_results": case_results if include_case_results else [],
        "best_by_constraint": _build_best_by_constraint(config_rows, incumbent=incumbent),
        "family_bakeoff_summary": _build_family_bakeoff_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "decision_signature_summary": _build_decision_signature_summary(config_rows),
        "metric_tie_summary": _build_metric_tie_summary(config_rows),
        "selection_validation_summary": _build_selection_validation_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "incumbent_delta_summary": _build_incumbent_delta_summary(
            config_rows,
            case_results,
            incumbent=incumbent,
        ),
        "negative_control_summary": _build_negative_control_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "overfitting_checks": _build_overfitting_checks(
            config_rows,
            case_results,
            defaults=defaults,
        ),
        "threshold_sensitivity": threshold_sensitivity,
        "source_dropout": source_dropout,
    }
    report["recommendation"] = _build_recommendation(report)
    return report


def render_decision_rule_matrix_markdown(report: Mapping[str, object]) -> str:
    best = (
        report.get("best_by_constraint")
        if isinstance(report.get("best_by_constraint"), Mapping)
        else {}
    )
    negative = (
        report.get("negative_control_summary")
        if isinstance(report.get("negative_control_summary"), Mapping)
        else {}
    )
    config_rows = _as_mapping_rows(report.get("config_rows"))
    lines = [
        "# en-es Semantic Decision Rule Matrix",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Matrix: `{report.get('matrix_id', '')}`",
        f"- Dataset: `{report.get('dataset_path', '')}`",
        f"- Manifest: `{report.get('manifest_path', '')}`",
        f"- Evaluation suites: `{len(_as_mapping_rows(report.get('evaluation_suites')))}`",
        f"- Config rows: `{report.get('row_count', 0)}`",
        f"- Case score traces: `{report.get('case_result_count', 0)}`",
        f"- Case traces included in JSON: `{not bool(report.get('case_results_omitted'))}`",
        f"- Negative-control sanity: `{negative.get('status', 'unknown')}`",
        "",
        "## Recommendation",
        "",
        str(report.get("recommendation") or ""),
        "",
        "## Best By Constraint",
        "",
    ]
    for key in (
        "incumbent_control",
        "best_overall",
        "best_zero_harm",
        "best_promotable_candidate",
    ):
        row = best.get(key) if isinstance(best.get(key), Mapping) else None
        if row:
            lines.extend(_render_public_config_row(key, row))
            lines.append("")

    source_batches = _as_mapping_rows(report.get("source_evidence_batches"))
    if source_batches:
        lines.extend(["## Source Evidence Batches", ""])
        lines.append("| Path | Rows | Attached Rows | SHA-256 |")
        lines.append("| --- | ---: | ---: | --- |")
        for row in source_batches:
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("path") or ""),
                        str(int(row.get("row_count") or 0)),
                        str(int(row.get("attached_row_count") or 0)),
                        str(row.get("sha256") or ""),
                    )
                )
                + " |"
            )
        lines.append("")

    source_scopes = _as_mapping_rows(report.get("source_evidence_scopes"))
    if source_scopes:
        lines.extend(["## Source Evidence Scopes", ""])
        lines.append("| Scope | Paths | Attached Rows | Mask | Window |")
        lines.append("| ---: | --- | ---: | --- | ---: |")
        for row in source_scopes:
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("scope_index") or ""),
                        "<br>".join(str(path) for path in row.get("paths", ()) or ()),
                        str(int(row.get("attached_row_count") or 0)),
                        str(row.get("mask_token") or ""),
                        str(int(row.get("window_tokens") or 0)),
                    )
                )
                + " |"
            )
        lines.append("")

    candidate_rows = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    family_summary = _as_mapping_rows(report.get("family_bakeoff_summary"))
    if family_summary:
        lines.extend(["## Algorithm Family Winners", ""])
        lines.append(
            "| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |"
        )
        lines.append("| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |")
        for row in family_summary:
            best_row = row.get("best_row") if isinstance(row.get("best_row"), Mapping) else {}
            zero_harm = (
                row.get("best_zero_harm_row")
                if isinstance(row.get("best_zero_harm_row"), Mapping)
                else {}
            )
            display_row = zero_harm or best_row
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("algorithm_family") or ""),
                        str(int(row.get("config_count") or 0)),
                        str(best_row.get("config_id") or ""),
                        str(zero_harm.get("config_id") or ""),
                        str(int(display_row.get("harmful_replace_count") or 0)),
                        str(int(display_row.get("false_abstain_count") or 0)),
                        _render_rate(display_row.get("winner_accuracy")),
                        f"{float(display_row.get('objective_score') or 0.0):.4f}",
                    )
                )
                + " |"
            )
        lines.append("")

    if len(_as_mapping_rows(report.get("evaluation_suites"))) > 1:
        lines.extend(["## Evaluation Suite Breakdown", ""])
        lines.append("| Config | Suite | Cases | Harmful | False Abstain | Accuracy |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for config in candidate_rows[:8]:
            for suite_row in _as_mapping_rows(config.get("suite_breakdown")):
                summary = _breakdown_summary(suite_row)
                lines.append(
                    "| "
                    + " | ".join(
                        (
                            str(config.get("config_id") or ""),
                            str(suite_row.get("suite_id") or ""),
                            str(int(summary.get("cases_total") or 0)),
                            str(int(summary.get("harmful_replace_count") or 0)),
                            str(int(summary.get("false_abstain_count") or 0)),
                            _render_rate(summary.get("decision_accuracy")),
                        )
                    )
                    + " |"
                )
        lines.append("")

    signature_summary = (
        report.get("decision_signature_summary")
        if isinstance(report.get("decision_signature_summary"), Mapping)
        else {}
    )
    if signature_summary:
        lines.extend(["## Decision Signature Clusters", ""])
        lines.append(
            f"- Unique replace signatures: `{signature_summary.get('unique_replace_signature_count', 0)}`"
        )
        lines.append(
            f"- Largest replace-signature cluster: `{signature_summary.get('largest_replace_signature_size', 0)}` configs"
        )
        for row in _as_mapping_rows(signature_summary.get("top_replace_signature_clusters"))[:5]:
            lines.append(
                "- "
                f"`{row.get('signature', '')}`: `{int(row.get('config_count') or 0)}` configs, "
                f"sample `{', '.join(str(value) for value in row.get('sample_config_ids', ()))}`"
            )
        lines.append("")

    tie_summary = (
        report.get("metric_tie_summary")
        if isinstance(report.get("metric_tie_summary"), Mapping)
        else {}
    )
    if tie_summary:
        lines.extend(["## Headline Metric Ties", ""])
        lines.append(f"- Tied primary-metric groups: `{tie_summary.get('tied_group_count', 0)}`")
        lines.append(
            f"- Largest tied group: `{tie_summary.get('largest_tied_group_size', 0)}` configs"
        )
        for row in _as_mapping_rows(tie_summary.get("top_tied_groups"))[:8]:
            lines.append(
                "- "
                f"`{row.get('metric_signature', '')}`: `{int(row.get('config_count') or 0)}` "
                f"configs, unique replace signatures "
                f"`{int(row.get('unique_replace_signature_count') or 0)}`, "
                f"ROC AUC `{_render_range(row.get('roc_auc_min'), row.get('roc_auc_max'))}`, "
                f"Avg Prec. `{_render_range(row.get('average_precision_min'), row.get('average_precision_max'))}`"
            )
        lines.append("")

    selection_summary = (
        report.get("selection_validation_summary")
        if isinstance(report.get("selection_validation_summary"), Mapping)
        else {}
    )
    if selection_summary:
        lines.extend(["## Discovery Selection vs Locked Eval", ""])
        lines.append(f"- Policy: {selection_summary.get('selection_policy', '')}")
        lines.append(
            "| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |"
        )
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in _as_mapping_rows(selection_summary.get("rows")):
            selected = (
                row.get("selected_on_discovery")
                if isinstance(row.get("selected_on_discovery"), Mapping)
                else {}
            )
            oracle = (
                row.get("locked_oracle") if isinstance(row.get("locked_oracle"), Mapping) else {}
            )
            discovery = (
                selected.get("discovery") if isinstance(selected.get("discovery"), Mapping) else {}
            )
            locked = (
                selected.get("locked_eval")
                if isinstance(selected.get("locked_eval"), Mapping)
                else {}
            )
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row.get("algorithm_family") or ""),
                        str(selected.get("config_id") or ""),
                        str(int(discovery.get("harmful_replace_count") or 0)),
                        str(int(discovery.get("false_abstain_count") or 0)),
                        str(int(locked.get("harmful_replace_count") or 0)),
                        str(int(locked.get("false_abstain_count") or 0)),
                        _render_float(locked.get("objective_score")),
                        str(oracle.get("config_id") or ""),
                    )
                )
                + " |"
            )
        lines.append("")

    delta_summary = (
        report.get("incumbent_delta_summary")
        if isinstance(report.get("incumbent_delta_summary"), Mapping)
        else {}
    )
    if delta_summary:
        lines.extend(["## Incumbent Case Deltas", ""])
        lines.append(f"- Incumbent config: `{delta_summary.get('incumbent_config_id', '')}`")
        lines.append(
            f"- Configs identical to incumbent decisions: `{delta_summary.get('identical_decision_count', 0)}`"
        )
        for row in _as_mapping_rows(delta_summary.get("top_delta_rows"))[:8]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}`: decisions changed "
                f"`{int(row.get('decision_changed_count') or 0)}`, "
                f"false abstains fixed/introduced "
                f"`{int(row.get('false_abstain_fixed_count') or 0)}`/"
                f"`{int(row.get('false_abstain_introduced_count') or 0)}`, "
                f"harmful fixed/introduced "
                f"`{int(row.get('harmful_fixed_count') or 0)}`/"
                f"`{int(row.get('harmful_introduced_count') or 0)}`"
            )
        lines.append("")

    lines.extend(["## Top Candidate Configs", ""])
    lines.append(
        "| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |"
    )
    lines.append(
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for index, row in enumerate(candidate_rows[:20], start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    str(row.get("algorithm_family") or ""),
                    str(row.get("config_id") or ""),
                    str(row.get("scorer_id") or ""),
                    str(row.get("context_view") or ""),
                    str(row.get("sense_representation") or ""),
                    str(row.get("aggregation_rule") or ""),
                    str(row.get("decision_rule") or ""),
                    str(row.get("phrase_handling") or ""),
                    str(row.get("evidence_control") or ""),
                    str(int(row.get("harmful_replace_count") or 0)),
                    str(int(row.get("false_abstain_count") or 0)),
                    _render_rate(row.get("winner_accuracy")),
                    _render_float(row.get("ranking_roc_auc")),
                    _render_float(row.get("ranking_average_precision")),
                    f"{float(row.get('objective_score') or 0.0):.4f}",
                )
            )
            + " |"
        )

    negative_rows = _as_mapping_rows(negative.get("rows"))
    if negative_rows:
        lines.extend(["", "## Negative Controls", ""])
        for row in negative_rows:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}`: `{row.get('status', '')}` "
                f"({row.get('expected_failure_mode', '')}; "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"accuracy `{_render_rate(row.get('decision_accuracy'))}`)"
            )

    overfit = (
        report.get("overfitting_checks")
        if isinstance(report.get("overfitting_checks"), Mapping)
        else {}
    )
    lines.extend(["", "## Overfitting Checks", ""])
    lines.append(
        f"- Split policy: `{overfit.get('split_policy', '')}` "
        f"(locked remainders `{overfit.get('locked_eval_remainders', [])}`)"
    )
    for row in _as_mapping_rows(overfit.get("rows"))[:10]:
        lines.append(
            "- "
            f"`{row.get('config_id', '')}`: discovery objective "
            f"`{_render_float(row.get('discovery_objective_score'))}`, locked objective "
            f"`{_render_float(row.get('locked_eval_objective_score'))}`, "
            f"worst leave-one-family objective "
            f"`{_render_float(row.get('worst_leave_one_family_objective_score'))}`"
        )

    threshold_rows = _as_mapping_rows(report.get("threshold_sensitivity"))
    if threshold_rows:
        lines.extend(["", "## Threshold Sensitivity", ""])
        for row in threshold_rows[:20]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}` {row.get('threshold_label', '')}: "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"objective `{_render_float(row.get('objective_score'))}`"
            )

    dropout_rows = _as_mapping_rows(report.get("source_dropout"))
    if dropout_rows:
        lines.extend(["", "## Source-Family Dropout", ""])
        for row in dropout_rows[:20]:
            lines.append(
                "- "
                f"`{row.get('config_id', '')}` drop `{row.get('dropped_source_family', '')}`: "
                f"harmful `{int(row.get('harmful_replace_count') or 0)}`, "
                f"false abstain `{int(row.get('false_abstain_count') or 0)}`, "
                f"objective `{_render_float(row.get('objective_score'))}`"
            )
    return "\n".join(lines).rstrip() + "\n"


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
        backend = RuntimeSimilarityBackend(
            scorer_id=str(resolved_config.get("scorer_id") or "").strip(),
            model_name=str(resolved_config.get("model_name") or "").strip(),
        )
        backend.fit(
            _collect_fit_texts(
                dataset=fit_dataset,
                config=resolved_config,
                drop_source_families=drop_source_families,
            )
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


def _build_matrix_context_views(
    sentence: str,
    *,
    source_phrase: str,
    mask_token: str,
    window_tokens: int,
) -> dict[str, str]:
    views = dict(
        build_runtime_context_views(
            sentence,
            source_phrase=source_phrase,
            mask_token=mask_token,
            window_tokens=window_tokens,
        )
    )
    tokens = _tokenize_experiment_text(sentence)
    phrase_tokens = _tokenize_experiment_text(source_phrase)
    span = _find_token_span(tokens, phrase_tokens)
    if span is None:
        span = _find_mask_span(_tokenize_experiment_text(views.get("masked_sentence", "")))
    if span is None:
        window = _tokenize_experiment_text(views.get("masked_window") or sentence)
        masked_window = window
        before: list[str] = []
        after: list[str] = []
    else:
        start, end = span
        left = tokens[max(0, start - max(0, int(window_tokens))) : start]
        right = tokens[end : min(len(tokens), end + max(0, int(window_tokens)))]
        masked_window = [*left, mask_token, *right]
        before = left
        after = right

    views.update(
        {
            "ordered_ngram_context": _ordered_ngram_text(masked_window),
            "skipgram_context": _skipgram_text(masked_window),
            "before_after_slot_context": _before_after_slot_text(before, after),
            "surface_frame_context": _surface_frame_text(before, after, mask_token=mask_token),
            "pos_frame_context": _pos_frame_text(masked_window, mask_token=mask_token),
            "dependency_role_context": _dependency_role_text(
                before,
                after,
                mask_token=mask_token,
            ),
            "negation_modal_context": _negation_modal_text(masked_window),
            "shuffled_context_tokens": _deterministic_shuffle_text(
                masked_window, seed=source_phrase
            ),
            "reversed_context_tokens": " ".join(reversed(masked_window)),
            "lexical_only_without_frame": " ".join(sorted(set(masked_window))),
            "frame_only_without_lexical_content": _frame_only_text(
                masked_window, mask_token=mask_token
            ),
        }
    )
    return views


def _selector_context_text(
    context_views: Mapping[str, object],
    *,
    config: Mapping[str, object],
) -> str:
    selector_view = str(
        config.get("evidence_selector_context_view")
        or config.get("context_view")
        or "masked_sentence"
    ).strip()
    return str(
        context_views.get(selector_view) or context_views.get("masked_sentence") or ""
    ).strip()


def _tokenize_experiment_text(value: object) -> list[str]:
    return [match.group(0).casefold() for match in _EXPERIMENT_TOKEN_RE.finditer(str(value or ""))]


def _find_token_span(tokens: Sequence[str], phrase_tokens: Sequence[str]) -> tuple[int, int] | None:
    if not tokens or not phrase_tokens:
        return None
    phrase = [token.casefold() for token in phrase_tokens]
    width = len(phrase)
    for index in range(0, len(tokens) - width + 1):
        if [token.casefold() for token in tokens[index : index + width]] == phrase:
            return index, index + width
    return None


def _find_mask_span(tokens: Sequence[str]) -> tuple[int, int] | None:
    for index, token in enumerate(tokens):
        if token == DEFAULT_SENTENCE_VETO_MASK_TOKEN:
            return index, index + 1
    return None


def _ordered_ngram_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    parts: list[str] = []
    for size in (2, 3):
        for index in range(0, max(0, len(materialized) - size + 1)):
            parts.append(f"ng{size}=" + "_".join(materialized[index : index + size]))
    return " | ".join(parts) or " ".join(materialized)


def _skipgram_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    parts: list[str] = []
    max_gap = 2
    for index, left in enumerate(materialized):
        for right_index in range(index + 1, min(len(materialized), index + max_gap + 2)):
            parts.append(f"skip={left}>{materialized[right_index]}")
    return " | ".join(parts) or " ".join(materialized)


def _before_after_slot_text(before: Sequence[str], after: Sequence[str]) -> str:
    left = list(before)[-3:]
    right = list(after)[:3]
    parts = [f"left{len(left) - index}={token}" for index, token in enumerate(left)]
    parts.extend(f"right{index + 1}={token}" for index, token in enumerate(right))
    if left:
        parts.append("left_phrase=" + "_".join(left))
    if right:
        parts.append("right_phrase=" + "_".join(right))
    if left and right:
        parts.append(f"bridge={left[-1]}___{right[0]}")
    return " | ".join(parts)


def _surface_frame_text(before: Sequence[str], after: Sequence[str], *, mask_token: str) -> str:
    left = list(before)[-2:]
    right = list(after)[:3]
    prev_token = left[-1] if left else "BOS"
    next_token = right[0] if right else "EOS"
    parts = [
        f"frame={prev_token}_{mask_token}_{next_token}",
        f"prev={prev_token}",
        f"next={next_token}",
    ]
    if next_token in _PREPOSITIONS:
        object_token = right[1] if len(right) > 1 else "EOS"
        parts.append(f"prep_frame={mask_token}_{next_token}_{object_token}")
    if prev_token in _DETERMINERS:
        parts.append(f"det_frame={prev_token}_{mask_token}_{next_token}")
    if left and right:
        parts.append("ordered_window=" + "_".join([*left, mask_token, *right]))
    return " | ".join(parts)


def _pos_frame_text(tokens: Sequence[str], *, mask_token: str) -> str:
    tags = [_coarse_token_class(token, mask_token=mask_token) for token in tokens if token]
    return " ".join(tags)


def _frame_only_text(tokens: Sequence[str], *, mask_token: str) -> str:
    return " ".join(_coarse_token_class(token, mask_token=mask_token) for token in tokens if token)


def _dependency_role_text(
    before: Sequence[str],
    after: Sequence[str],
    *,
    mask_token: str,
) -> str:
    left = list(before)[-4:]
    right = list(after)[:4]
    prev_token = left[-1] if left else "BOS"
    prev2_token = left[-2] if len(left) > 1 else "BOS"
    next_token = right[0] if right else "EOS"
    next2_token = right[1] if len(right) > 1 else "EOS"
    prev_class = _coarse_token_class(prev_token, mask_token=mask_token)
    next_class = _coarse_token_class(next_token, mask_token=mask_token)
    parts = [
        f"dep_frame={prev_class}_TRIGGER_{next_class}",
        f"dep_prev={prev_token}",
        f"dep_next={next_token}",
    ]
    if next_token in _PREPOSITIONS:
        parts.extend(
            (
                "role=head_with_prepositional_complement",
                f"dep_prep_after={next_token}",
                f"dep_prep_object={next2_token}",
            )
        )
        if next_token in _PARTICLES:
            parts.append(f"role=phrasal_verb_particle_{next_token}")
    if prev_token in _PREPOSITIONS:
        parts.extend(
            (
                "role=prepositional_object",
                f"dep_prep_before={prev_token}",
                f"dep_prep_governor={prev2_token}",
            )
        )
    if prev_token in _DETERMINERS or prev2_token in _DETERMINERS:
        parts.append("role=noun_phrase_head")
    if next_token in _BE_VERBS or next_token in _MODALS or _looks_like_verb(next_token):
        parts.append("role=subject_or_topic")
    if prev_token in _AUXILIARY_VERBS or prev_token in _MODALS or prev_token == "to":
        parts.append("role=verb_head_after_auxiliary")
    if (
        next_token in _DETERMINERS
        or next_token in _PRONOUNS
        or _coarse_token_class(next_token, mask_token=mask_token) == "WORD"
    ) and prev_token not in _DETERMINERS:
        parts.append("role=verb_or_predicate_with_object")
    if right:
        parts.append("right_dependency_chain=" + ">".join(right[:3]))
    if left:
        parts.append("left_dependency_chain=" + ">".join(left[-3:]))
    return " | ".join(dict.fromkeys(parts))


def _coarse_token_class(token: str, *, mask_token: str) -> str:
    normalized = str(token or "").casefold()
    if normalized == str(mask_token).casefold():
        return "TRIGGER"
    if normalized in _DETERMINERS:
        return "DET"
    if normalized in _PREPOSITIONS:
        return "PREP"
    if normalized in _MODALS:
        return "MODAL"
    if normalized in _NEGATIONS:
        return "NEG"
    if normalized.isdigit():
        return "NUM"
    if normalized.endswith("ing"):
        return "ING"
    if normalized.endswith("ed"):
        return "PAST"
    if normalized.endswith("ly"):
        return "ADV"
    return "WORD"


def _looks_like_verb(token: str) -> bool:
    normalized = str(token or "").casefold()
    return normalized in _AUXILIARY_VERBS or normalized.endswith(("ed", "ing", "s"))


def _negation_modal_text(tokens: Sequence[str]) -> str:
    materialized = [token for token in tokens if token]
    signals = [f"neg={token}" for token in materialized if token in _NEGATIONS] + [
        f"modal={token}" for token in materialized if token in _MODALS
    ]
    return " | ".join(signals) or "no_negation_or_modal"


def _deterministic_shuffle_text(tokens: Sequence[str], *, seed: str) -> str:
    return " ".join(
        sorted(
            [token for token in tokens if token],
            key=lambda token: _text_sha256(f"{seed}|{token}")[:12],
        )
    )


def _score_sense(
    *,
    context_text: str,
    selector_context_text: str,
    sense: Mapping[str, object],
    winner_type: str,
    backend: RuntimeSimilarityBackend,
    config: Mapping[str, object],
    drop_source_families: Sequence[str],
) -> SenseScore:
    rows = _evidence_rows_for_sense(sense, config=config)
    dropped = {
        str(value or "").strip() for value in drop_source_families if str(value or "").strip()
    }
    if dropped:
        rows = [row for row in rows if row.source_family not in dropped]
    row_scores: list[dict[str, object]] = []
    for row in rows:
        selector_text = str(row.selector_text or row.text).strip()
        row_scores.append(
            {
                "row_id": row.row_id,
                "source_family": row.source_family,
                "text": row.text,
                "selector_text": selector_text,
                "weight": row.weight,
                "score": _round_float(backend.similarity(context_text, row.text)),
                "selection_score": _round_float(
                    backend.similarity(selector_context_text, selector_text)
                ),
            }
        )
    aggregate = _aggregate_row_scores(
        row_scores,
        aggregation_rule=str(config.get("aggregation_rule") or "single_concatenated_text"),
        top_k=int(config.get("top_k") or 2),
        selection_top_k=int(config.get("selection_top_k") or config.get("top_k") or 2),
    )
    return SenseScore(
        sense_id=str(sense.get("sense_id") or "").strip(),
        target_lemma=str(sense.get("target_lemma") or "").strip(),
        winner_type=winner_type,
        aggregate_score=aggregate,
        row_scores=tuple(row_scores),
    )


def _evidence_rows_for_sense(
    sense: Mapping[str, object],
    *,
    config: Mapping[str, object],
) -> list[EvidenceRow]:
    representation = str(config.get("sense_representation") or "all_evidence_text").strip()
    if str(config.get("evidence_control") or "") == "target_lemma_only":
        representation = "target_lemma_only"
    source_weights = _source_weights(config)
    evidence_views = sense.get("evidence_views")
    if not isinstance(evidence_views, Mapping):
        evidence_views = {}
    sense_id = str(sense.get("sense_id") or "sense").strip()

    def row(
        row_id: str,
        source_family: str,
        text: object,
        *,
        selector_text: object = "",
    ) -> EvidenceRow | None:
        normalized = str(text or "").strip()
        if not normalized:
            return None
        normalized_selector = str(selector_text or "").strip()
        return EvidenceRow(
            row_id=f"{sense_id}:{row_id}",
            source_family=source_family,
            text=normalized,
            weight=float(source_weights.get(source_family, 1.0)),
            selector_text=normalized_selector,
        )

    if representation in {"all_evidence_text", "current_concatenated"}:
        return _dedupe_rows(
            (row("all_evidence_text", "all_evidence", evidence_views.get("all_evidence_text")),)
        )
    if representation in {"sense_label", "gloss_text", "sense_gloss_bundle", "qualifier_text"}:
        source_family = {
            "sense_label": "sense_label",
            "gloss_text": "definition",
            "sense_gloss_bundle": "all_evidence",
            "qualifier_text": "qualifier",
        }[representation]
        return _dedupe_rows(
            (row(representation, source_family, evidence_views.get(representation)),)
        )
    if representation == "target_lemma_only":
        return _dedupe_rows((row("target_lemma", "target_lemma", sense.get("target_lemma")),))
    if representation == "definition_and_example_rows_separate":
        split_rows: list[EvidenceRow | None] = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
        ]
        for index, part in enumerate(
            _split_evidence_parts(evidence_views.get("all_evidence_text"))
        ):
            split_rows.append(row(f"all_evidence_part_{index + 1}", "auxiliary", part))
        return _dedupe_rows(split_rows)
    if representation in {
        "definition_example_plus_source_rows_separate",
        "contextualized_definition_example_plus_source_rows",
    }:
        split_rows = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
        ]
        for index, part in enumerate(
            _split_evidence_parts(evidence_views.get("all_evidence_text"))
        ):
            split_rows.append(row(f"all_evidence_part_{index + 1}", "auxiliary", part))
        split_rows.extend(_source_evidence_rows_for_sense(sense, config=config, row_factory=row))
        return _dedupe_rows(split_rows)
    if representation in {
        "source_rows_separate",
        "source_plus_definition_rows_separate",
        "contextualized_source_rows",
        "contextualized_source_plus_definition_rows",
    }:
        source_rows = _source_evidence_rows_for_sense(sense, config=config, row_factory=row)
        if representation in {"source_rows_separate", "contextualized_source_rows"}:
            return _dedupe_rows(source_rows)
        split_rows = [
            row("sense_label", "sense_label", evidence_views.get("sense_label")),
            row("gloss_text", "definition", evidence_views.get("gloss_text")),
            row("qualifier_text", "qualifier", evidence_views.get("qualifier_text")),
            *source_rows,
        ]
        return _dedupe_rows(split_rows)
    if representation == "ordered_evidence_phrase":
        return _dedupe_rows(
            (
                row(
                    "ordered_evidence_phrase",
                    "ordered_evidence",
                    _ordered_evidence_text(evidence_views, sense=sense),
                ),
            )
        )
    if representation == "canonical_template_evidence":
        return _dedupe_rows(
            (
                row(
                    "canonical_template_evidence",
                    "canonical_template",
                    _canonical_template_evidence_text(evidence_views, sense=sense),
                ),
            )
        )
    if representation == "paraphrase_variant_evidence":
        return _dedupe_rows(
            tuple(
                row(f"paraphrase_variant_{index + 1}", "paraphrase_variant", text)
                for index, text in enumerate(_paraphrase_variant_texts(evidence_views, sense=sense))
            )
        )
    if representation == "shuffled_evidence_tokens":
        base_text = str(evidence_views.get("all_evidence_text") or "").strip()
        return _dedupe_rows(
            (
                row(
                    "shuffled_evidence_tokens",
                    "shuffled_evidence",
                    _deterministic_shuffle_text(
                        _tokenize_experiment_text(base_text),
                        seed=sense_id,
                    ),
                ),
            )
        )
    if representation == "reversed_evidence_tokens":
        base_text = str(evidence_views.get("all_evidence_text") or "").strip()
        return _dedupe_rows(
            (
                row(
                    "reversed_evidence_tokens",
                    "reversed_evidence",
                    " ".join(reversed(_tokenize_experiment_text(base_text))),
                ),
            )
        )
    raise ValueError(f"Unsupported sense representation: {representation!r}")


def _source_evidence_rows_for_sense(
    sense: Mapping[str, object],
    *,
    config: Mapping[str, object],
    row_factory,
) -> list[EvidenceRow | None]:
    source_rows = sense.get("matrix_source_rows")
    if not isinstance(source_rows, Sequence) or isinstance(source_rows, (str, bytes)):
        return []
    source_selector_view = str(
        config.get("evidence_selector_source_view")
        or config.get("evidence_selector_context_view")
        or config.get("context_view")
        or "masked_sentence"
    ).strip()
    rows: list[EvidenceRow | None] = []
    for index, source_row in enumerate(source_rows, start=1):
        if not isinstance(source_row, Mapping):
            continue
        text = str(source_row.get("evidence_text") or source_row.get("text") or "").strip()
        if not text:
            continue
        selector_views = source_row.get("selector_views")
        selector_text = ""
        if isinstance(selector_views, Mapping):
            selector_text = str(
                selector_views.get(source_selector_view)
                or selector_views.get("masked_sentence")
                or selector_views.get("raw_sentence")
                or ""
            ).strip()
        source_family = str(source_row.get("source_family") or "source_row").strip()
        row_id = str(source_row.get("row_id") or f"source_row_{index}").strip()
        rows.append(
            row_factory(
                f"source_row_{index}:{row_id}",
                source_family,
                text,
                selector_text=selector_text,
            )
        )
    return rows


def _aggregate_row_scores(
    row_scores: Sequence[Mapping[str, object]],
    *,
    aggregation_rule: str,
    top_k: int,
    selection_top_k: int,
) -> float:
    scores = [float(row.get("score") or 0.0) for row in row_scores]
    if not scores:
        return 0.0
    if aggregation_rule == "single_concatenated_text":
        return scores[0] if len(scores) == 1 else sum(scores) / len(scores)
    if aggregation_rule == "max_row_score":
        return max(scores)
    if aggregation_rule == "mean_row_score":
        return sum(scores) / len(scores)
    if aggregation_rule == "top_k_mean":
        selected = sorted(scores, reverse=True)[: max(1, top_k)]
        return sum(selected) / len(selected)
    if aggregation_rule == "source_weighted_top_k":
        return _source_weighted_top_k_score(row_scores, top_k=top_k)
    if aggregation_rule == "context_selected_max_row_score":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        return max(float(row.get("score") or 0.0) for row in selected_rows)
    if aggregation_rule == "context_selected_top_k_mean":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        selected_scores = sorted(
            (float(row.get("score") or 0.0) for row in selected_rows),
            reverse=True,
        )[: max(1, top_k)]
        return sum(selected_scores) / len(selected_scores)
    if aggregation_rule == "context_selected_source_weighted_top_k":
        selected_rows = _select_rows_by_context(row_scores, selection_top_k=selection_top_k)
        return _source_weighted_top_k_score(selected_rows, top_k=top_k)
    if aggregation_rule == "definition_example_agreement":
        by_family: dict[str, list[float]] = defaultdict(list)
        for row in row_scores:
            by_family[str(row.get("source_family") or "")].append(float(row.get("score") or 0.0))
        definition_score = max(by_family.get("definition", [0.0]))
        support_scores = [
            score
            for family, family_scores in by_family.items()
            if family != "definition"
            for score in family_scores
        ]
        support_score = max(support_scores) if support_scores else definition_score
        return min(definition_score, support_score)
    raise ValueError(f"Unsupported aggregation rule: {aggregation_rule!r}")


def _select_rows_by_context(
    row_scores: Sequence[Mapping[str, object]],
    *,
    selection_top_k: int,
) -> list[Mapping[str, object]]:
    selected = sorted(
        row_scores,
        key=lambda row: (
            float(row.get("selection_score") or 0.0),
            float(row.get("score") or 0.0),
            str(row.get("row_id") or ""),
        ),
        reverse=True,
    )[: max(1, selection_top_k)]
    return list(selected or row_scores[:1])


def _source_weighted_top_k_score(
    row_scores: Sequence[Mapping[str, object]],
    *,
    top_k: int,
) -> float:
    selected_rows = sorted(
        row_scores,
        key=lambda row: float(row.get("score") or 0.0),
        reverse=True,
    )[: max(1, top_k)]
    denominator = sum(max(0.0, float(row.get("weight") or 0.0)) for row in selected_rows)
    if denominator <= 0:
        return 0.0
    return (
        sum(
            float(row.get("score") or 0.0) * max(0.0, float(row.get("weight") or 0.0))
            for row in selected_rows
        )
        / denominator
    )


def _apply_decision_rule(
    *,
    active_score: SenseScore,
    shadow_scores: Sequence[SenseScore],
    config: Mapping[str, object],
    phrase_hit: bool,
    phrase_reason_code: str,
) -> dict[str, object]:
    phrase_handling = str(config.get("phrase_handling") or "semantic_only").strip()
    shadow_candidates = list(shadow_scores)
    if phrase_handling == "phrase_as_shadow" and phrase_hit:
        phrase_score = float(config.get("phrase_shadow_score") or 1.0)
        shadow_candidates.append(
            SenseScore(
                sense_id="phrase_control",
                target_lemma="phrase_control",
                winner_type="phrase",
                aggregate_score=phrase_score,
                row_scores=(
                    {
                        "row_id": "phrase_control",
                        "source_family": "phrase_control",
                        "text": phrase_reason_code,
                        "weight": 1.0,
                        "score": _round_float(phrase_score),
                    },
                ),
            )
        )

    strongest_shadow = _strongest_shadow(shadow_candidates)
    strongest_shadow_score = strongest_shadow.aggregate_score if strongest_shadow else 0.0
    margin = float(active_score.aggregate_score) - float(strongest_shadow_score)
    ratio = _active_ratio(
        active_score.aggregate_score, strongest_shadow_score, bool(shadow_candidates)
    )
    probability = _active_softmax_probability(
        active_score.aggregate_score,
        [score.aggregate_score for score in shadow_candidates],
        temperature=float(config.get("softmax_temperature") or 8.0),
    )
    pairwise_win_rate = _pairwise_win_rate(
        active_score.aggregate_score,
        [score.aggregate_score for score in shadow_candidates],
        min_margin=float(config.get("min_margin") or 0.0),
    )

    predicted_winner = active_score.sense_id
    predicted_winner_type = "active"
    if strongest_shadow and strongest_shadow.aggregate_score > active_score.aggregate_score:
        predicted_winner = strongest_shadow.sense_id
        predicted_winner_type = strongest_shadow.winner_type

    reason_codes: list[str] = []
    if phrase_handling == "phrase_first" and phrase_hit:
        return {
            "predicted_decision": "abstain",
            "predicted_winner": "phrase_control",
            "predicted_winner_type": "phrase",
            "strongest_shadow_score": strongest_shadow_score,
            "strongest_shadow_id": strongest_shadow.sense_id if strongest_shadow else "",
            "margin": margin,
            "active_ratio": ratio,
            "active_softmax_probability": probability,
            "pairwise_win_rate": pairwise_win_rate,
            "replacement_confidence": _replacement_confidence(
                decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
                margin=margin,
                ratio=ratio,
                probability=probability,
                pairwise_win_rate=pairwise_win_rate,
                strongest_shadow_score=strongest_shadow_score,
            ),
            "reason_codes": ("phrase_first_preemption", phrase_reason_code),
        }

    predicted_decision = _semantic_decision(
        decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
        active_score=float(active_score.aggregate_score),
        strongest_shadow_score=float(strongest_shadow_score),
        shadow_scores=[score.aggregate_score for score in shadow_candidates],
        min_active_score=float(config.get("min_active_score") or 0.0),
        min_margin=float(config.get("min_margin") or 0.0),
        ratio_threshold=float(config.get("ratio_threshold") or 1.0),
        softmax_threshold=float(config.get("softmax_threshold") or 0.5),
        active_softmax_probability=probability,
        pairwise_win_rate=pairwise_win_rate,
        pairwise_min_win_rate=float(config.get("pairwise_min_win_rate") or 0.75),
        shadow_veto_threshold=float(config.get("shadow_veto_threshold") or 0.0),
    )
    reason_codes.append(str(config.get("decision_rule") or "active_minus_strongest_shadow"))
    if phrase_handling == "phrase_override" and phrase_hit:
        predicted_decision = "abstain"
        reason_codes.extend(("phrase_override", phrase_reason_code))
    if phrase_handling == "phrase_as_shadow" and phrase_hit:
        reason_codes.extend(("phrase_as_shadow", phrase_reason_code))
    if predicted_decision != "replace" and strongest_shadow:
        predicted_winner = strongest_shadow.sense_id
        predicted_winner_type = strongest_shadow.winner_type
    return {
        "predicted_decision": predicted_decision,
        "predicted_winner": predicted_winner,
        "predicted_winner_type": predicted_winner_type,
        "strongest_shadow_score": strongest_shadow_score,
        "strongest_shadow_id": strongest_shadow.sense_id if strongest_shadow else "",
        "margin": margin,
        "active_ratio": ratio,
        "active_softmax_probability": probability,
        "pairwise_win_rate": pairwise_win_rate,
        "replacement_confidence": _replacement_confidence(
            decision_rule=str(config.get("decision_rule") or "active_minus_strongest_shadow"),
            margin=margin,
            ratio=ratio,
            probability=probability,
            pairwise_win_rate=pairwise_win_rate,
            strongest_shadow_score=strongest_shadow_score,
        ),
        "reason_codes": tuple(code for code in reason_codes if code),
    }


def _semantic_decision(
    *,
    decision_rule: str,
    active_score: float,
    strongest_shadow_score: float,
    shadow_scores: Sequence[float],
    min_active_score: float,
    min_margin: float,
    ratio_threshold: float,
    softmax_threshold: float,
    active_softmax_probability: float,
    pairwise_win_rate: float,
    pairwise_min_win_rate: float,
    shadow_veto_threshold: float,
) -> str:
    if decision_rule == "shadow_veto_only":
        return "abstain" if strongest_shadow_score >= shadow_veto_threshold else "replace"
    if active_score < min_active_score:
        return "abstain"
    if decision_rule == "active_minus_strongest_shadow":
        return "replace" if active_score - strongest_shadow_score >= min_margin else "abstain"
    if decision_rule == "active_ratio_strongest_shadow":
        ratio = _active_ratio(active_score, strongest_shadow_score, bool(shadow_scores))
        return "replace" if ratio >= ratio_threshold else "abstain"
    if decision_rule == "softmax_probability":
        return "replace" if active_softmax_probability >= softmax_threshold else "abstain"
    if decision_rule == "pairwise_active_beats_all_shadows":
        return (
            "replace"
            if all(active_score - score >= min_margin for score in shadow_scores)
            else "abstain"
        )
    if decision_rule == "pairwise_active_beats_most_shadows":
        return "replace" if pairwise_win_rate >= pairwise_min_win_rate else "abstain"
    raise ValueError(f"Unsupported decision rule: {decision_rule!r}")


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


def _config_summary_row(
    *,
    config: Mapping[str, object],
    summary: Mapping[str, object],
    case_rows: Sequence[Mapping[str, object]],
    family_breakdown: Sequence[Mapping[str, object]],
    suite_breakdown: Sequence[Mapping[str, object]],
    slice_tag_breakdown: Sequence[Mapping[str, object]],
    gold_winner_type_breakdown: Sequence[Mapping[str, object]],
    harmful_replace_rows: Sequence[Mapping[str, object]],
    false_abstain_rows: Sequence[Mapping[str, object]],
    winner_error_rows: Sequence[Mapping[str, object]],
    drop_source_families: Sequence[str],
    threshold_override: Mapping[str, object] | None,
) -> dict[str, object]:
    row = {
        "config_id": str(config.get("config_id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "category": str(config.get("category") or "").strip(),
        "algorithm_family": str(
            config.get("algorithm_family") or config.get("decision_rule") or ""
        ).strip(),
        "parameter_set_id": str(config.get("parameter_set_id") or "").strip(),
        "manifest_index": int(config.get("manifest_index") or 0),
        "is_control": bool(config.get("is_control")),
        "expected_failure_mode": str(config.get("expected_failure_mode") or "").strip(),
        "scorer_id": str(config.get("scorer_id") or "").strip(),
        "model_name": str(config.get("model_name") or "").strip(),
        "context_view": str(config.get("context_view") or "").strip(),
        "evidence_selector_context_view": str(
            config.get("evidence_selector_context_view") or ""
        ).strip(),
        "evidence_selector_source_view": str(
            config.get("evidence_selector_source_view") or ""
        ).strip(),
        "sense_representation": str(config.get("sense_representation") or "").strip(),
        "aggregation_rule": str(config.get("aggregation_rule") or "").strip(),
        "decision_rule": str(config.get("decision_rule") or "").strip(),
        "phrase_handling": str(config.get("phrase_handling") or "").strip(),
        "evidence_control": str(config.get("evidence_control") or "normal").strip(),
        "source_evidence_scope_id": str(config.get("source_evidence_scope_id") or "").strip(),
        "source_evidence_batch_count": len(_as_mapping_rows(config.get("source_evidence_batches"))),
        "source_evidence_attached_row_count": sum(
            int(batch.get("attached_row_count") or 0)
            for batch in _as_mapping_rows(config.get("source_evidence_batches"))
        ),
        "fit_scope": str(config.get("fit_scope") or "").strip(),
        "min_active_score": float(config.get("min_active_score") or 0.0),
        "min_margin": float(config.get("min_margin") or 0.0),
        "ratio_threshold": float(config.get("ratio_threshold") or 1.0),
        "softmax_threshold": float(config.get("softmax_threshold") or 0.5),
        "pairwise_min_win_rate": float(config.get("pairwise_min_win_rate") or 0.75),
        "top_k": int(config.get("top_k") or 2),
        "selection_top_k": int(config.get("selection_top_k") or config.get("top_k") or 2),
        "drop_source_families": list(drop_source_families),
        "threshold_override": dict(threshold_override or {}),
    }
    row.update(_public_summary(summary))
    row.update(_ranking_metrics(case_rows))
    row["split_summaries"] = _build_split_summaries(case_rows)
    row["objective_score"] = _objective_score(row)
    row["family_breakdown"] = list(family_breakdown)
    row["suite_breakdown"] = list(suite_breakdown)
    row["slice_tag_breakdown"] = list(slice_tag_breakdown)
    row["gold_winner_type_breakdown"] = list(gold_winner_type_breakdown)
    row["harmful_replace_case_ids"] = [
        str(case.get("case_id") or "") for case in case_rows if _is_harmful_replace(case)
    ]
    row["false_abstain_case_ids"] = [
        str(case.get("case_id") or "") for case in case_rows if _is_false_abstain(case)
    ]
    row["predicted_replace_case_ids"] = [
        str(case.get("case_id") or "")
        for case in case_rows
        if str(case.get("predicted_decision") or "") == "replace"
    ]
    row["replace_case_signature"] = _case_id_signature(row["predicted_replace_case_ids"])
    row["winner_signature"] = _case_id_signature(
        [
            f"{case.get('case_id')}={case.get('predicted_winner')}"
            for case in case_rows
            if str(case.get("case_id") or "")
        ]
    )
    row["sample_harmful_replace_rows"] = [_public_case_row(case) for case in harmful_replace_rows]
    row["sample_false_abstain_rows"] = [_public_case_row(case) for case in false_abstain_rows]
    row["sample_winner_error_rows"] = [_public_case_row(case) for case in winner_error_rows]
    return row


def _build_best_by_constraint(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    zero_harm = [row for row in candidates if int(row.get("harmful_replace_count") or 0) == 0]
    incumbent_false = int(incumbent.get("false_abstain_count") or 0) if incumbent else None
    incumbent_winner = float(incumbent.get("winner_accuracy") or 0.0) if incumbent else 0.0
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 0.0
    promotable = [
        row
        for row in zero_harm
        if incumbent_false is None
        or (
            int(row.get("false_abstain_count") or 0) <= incumbent_false
            and float(row.get("winner_accuracy") or 0.0) >= incumbent_winner
            and float(row.get("decision_accuracy") or 0.0) >= incumbent_accuracy
        )
    ]
    return {
        "incumbent_control": _public_config_row(incumbent),
        "best_overall": _public_config_row(_select_best(candidates)),
        "best_zero_harm": _public_config_row(_select_best(zero_harm)),
        "best_promotable_candidate": _public_config_row(_select_best(promotable)),
        "best_by_decision_rule": {
            key: _public_config_row(_select_best(value))
            for key, value in _group_by(candidates, "decision_rule").items()
        },
        "best_by_scorer": {
            key: _public_config_row(_select_best(value))
            for key, value in _group_by(candidates, "scorer_id").items()
        },
    }


def _build_family_bakeoff_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "algorithm_family")
    incumbent_false = int(incumbent.get("false_abstain_count") or 0) if incumbent else None
    incumbent_winner = float(incumbent.get("winner_accuracy") or 0.0) if incumbent else 0.0
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 0.0
    rows: list[dict[str, object]] = []
    for family, family_rows in sorted(grouped.items()):
        zero_harm = [row for row in family_rows if int(row.get("harmful_replace_count") or 0) == 0]
        promotable = [
            row
            for row in zero_harm
            if incumbent_false is None
            or (
                int(row.get("false_abstain_count") or 0) <= incumbent_false
                and float(row.get("winner_accuracy") or 0.0) >= incumbent_winner
                and float(row.get("decision_accuracy") or 0.0) >= incumbent_accuracy
            )
        ]
        rows.append(
            {
                "algorithm_family": family,
                "config_count": len(family_rows),
                "zero_harm_config_count": len(zero_harm),
                "best_row": _public_config_row(_select_best(family_rows)),
                "best_zero_harm_row": _public_config_row(_select_best(zero_harm)),
                "best_promotable_row": _public_config_row(_select_best(promotable)),
            }
        )
    rows.sort(
        key=lambda row: (
            float(
                (row.get("best_zero_harm_row") or row.get("best_row") or {}).get("objective_score")
                or 0.0
            ),
            str(row.get("algorithm_family") or ""),
        )
    )
    return rows


def _build_decision_signature_summary(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "replace_case_signature")
    cluster_rows: list[dict[str, object]] = []
    for signature, rows in grouped.items():
        sorted_rows = sorted(rows, key=_rank_key)
        best = sorted_rows[0] if sorted_rows else {}
        cluster_rows.append(
            {
                "signature": signature,
                "config_count": len(sorted_rows),
                "sample_config_ids": [str(row.get("config_id") or "") for row in sorted_rows[:5]],
                "algorithm_families": sorted(
                    {
                        str(row.get("algorithm_family") or "")
                        for row in sorted_rows
                        if str(row.get("algorithm_family") or "")
                    }
                ),
                "best_row": _public_config_row(best),
            }
        )
    cluster_rows.sort(
        key=lambda row: (
            -int(row.get("config_count") or 0),
            str(row.get("signature") or ""),
        )
    )
    return {
        "unique_replace_signature_count": len(grouped),
        "largest_replace_signature_size": int(cluster_rows[0].get("config_count") or 0)
        if cluster_rows
        else 0,
        "top_replace_signature_clusters": cluster_rows[:12],
    }


def _build_metric_tie_summary(
    config_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in candidates:
        grouped[_primary_metric_signature(row)].append(row)
    tie_rows: list[dict[str, object]] = []
    for signature, rows in grouped.items():
        if len(rows) <= 1:
            continue
        roc_values = [
            float(row.get("ranking_roc_auc"))
            for row in rows
            if row.get("ranking_roc_auc") is not None
        ]
        ap_values = [
            float(row.get("ranking_average_precision"))
            for row in rows
            if row.get("ranking_average_precision") is not None
        ]
        sorted_rows = sorted(rows, key=_ranking_quality_key)
        tie_rows.append(
            {
                "metric_signature": signature,
                "config_count": len(rows),
                "unique_replace_signature_count": len(
                    {
                        str(row.get("replace_case_signature") or "")
                        for row in rows
                        if str(row.get("replace_case_signature") or "")
                    }
                ),
                "algorithm_families": sorted(
                    {
                        str(row.get("algorithm_family") or "")
                        for row in rows
                        if str(row.get("algorithm_family") or "")
                    }
                ),
                "roc_auc_min": min(roc_values) if roc_values else None,
                "roc_auc_max": max(roc_values) if roc_values else None,
                "average_precision_min": min(ap_values) if ap_values else None,
                "average_precision_max": max(ap_values) if ap_values else None,
                "best_ranking_row": _public_config_row(sorted_rows[0]),
                "worst_ranking_row": _public_config_row(sorted_rows[-1]),
                "sample_config_ids": [
                    str(row.get("config_id") or "") for row in sorted(rows, key=_rank_key)[:8]
                ],
            }
        )
    tie_rows.sort(
        key=lambda row: (
            -int(row.get("config_count") or 0),
            -int(row.get("unique_replace_signature_count") or 0),
            str(row.get("metric_signature") or ""),
        )
    )
    return {
        "tied_group_count": len(tie_rows),
        "largest_tied_group_size": int(tie_rows[0].get("config_count") or 0) if tie_rows else 0,
        "top_tied_groups": tie_rows[:20],
    }


def _build_selection_validation_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    candidates = [row for row in config_rows if not str(row.get("expected_failure_mode") or "")]
    grouped = _group_by(candidates, "algorithm_family")
    rows: list[dict[str, object]] = []
    for family, family_rows in sorted(grouped.items()):
        selected_on_discovery = _select_best_for_split(family_rows, "discovery")
        selected_on_all_cases = _select_best(family_rows)
        locked_oracle = _select_best_for_split(family_rows, "locked_eval")
        if not selected_on_discovery:
            continue
        rows.append(
            {
                "algorithm_family": family,
                "config_count": len(family_rows),
                "selected_on_discovery": _public_selection_row(selected_on_discovery),
                "selected_on_all_cases": _public_selection_row(selected_on_all_cases),
                "locked_oracle": _public_selection_row(locked_oracle),
                "matches_all_case_selection": _same_config(
                    selected_on_discovery,
                    selected_on_all_cases,
                ),
                "matches_locked_oracle": _same_config(selected_on_discovery, locked_oracle),
                "locked_objective_gap_vs_oracle": _split_objective_gap(
                    selected_on_discovery,
                    locked_oracle,
                    split="locked_eval",
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            _selection_locked_objective(row),
            str(row.get("algorithm_family") or ""),
        )
    )
    return {
        "selection_policy": (
            "select the best config inside each algorithm family using discovery-split "
            "objective only; report locked-eval metrics after selection"
        ),
        "incumbent_config_id": str(incumbent.get("config_id") or "").strip()
        if isinstance(incumbent, Mapping)
        else "",
        "rows": rows,
    }


def _build_incumbent_delta_summary(
    config_rows: Sequence[Mapping[str, object]],
    case_results: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(incumbent, Mapping):
        return {}
    incumbent_config_id = str(incumbent.get("config_id") or "").strip()
    by_config: dict[str, dict[str, Mapping[str, object]]] = defaultdict(dict)
    for row in case_results:
        config_id = str(row.get("config_id") or "").strip()
        case_id = str(row.get("case_id") or "").strip()
        if config_id and case_id:
            by_config[config_id][case_id] = row
    incumbent_rows = by_config.get(incumbent_config_id, {})
    if not incumbent_rows:
        return {"incumbent_config_id": incumbent_config_id, "top_delta_rows": []}
    delta_rows: list[dict[str, object]] = []
    identical_decision_count = 0
    for config in config_rows:
        config_id = str(config.get("config_id") or "").strip()
        if not config_id or config_id == incumbent_config_id:
            continue
        if str(config.get("expected_failure_mode") or ""):
            continue
        case_lookup = by_config.get(config_id, {})
        delta = _config_delta_against_incumbent(
            config_id=config_id,
            case_lookup=case_lookup,
            incumbent_lookup=incumbent_rows,
        )
        if int(delta.get("decision_changed_count") or 0) == 0:
            identical_decision_count += 1
        delta_rows.append(delta)
    delta_rows.sort(
        key=lambda row: (
            -int(row.get("decision_changed_count") or 0),
            -int(row.get("false_abstain_fixed_count") or 0),
            int(row.get("harmful_introduced_count") or 0),
            str(row.get("config_id") or ""),
        )
    )
    return {
        "incumbent_config_id": incumbent_config_id,
        "compared_config_count": len(delta_rows),
        "identical_decision_count": identical_decision_count,
        "top_delta_rows": delta_rows[:40],
    }


def _config_delta_against_incumbent(
    *,
    config_id: str,
    case_lookup: Mapping[str, Mapping[str, object]],
    incumbent_lookup: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    decision_changed: list[str] = []
    winner_changed: list[str] = []
    false_abstain_fixed: list[str] = []
    false_abstain_introduced: list[str] = []
    harmful_fixed: list[str] = []
    harmful_introduced: list[str] = []
    replace_gained: list[str] = []
    replace_lost: list[str] = []
    for case_id, incumbent_row in incumbent_lookup.items():
        row = case_lookup.get(case_id)
        if not row:
            continue
        incumbent_decision = str(incumbent_row.get("predicted_decision") or "")
        decision = str(row.get("predicted_decision") or "")
        gold_decision = str(row.get("gold_decision") or "")
        if decision != incumbent_decision:
            decision_changed.append(case_id)
        if str(row.get("predicted_winner") or "") != str(
            incumbent_row.get("predicted_winner") or ""
        ):
            winner_changed.append(case_id)
        if incumbent_decision != "replace" and decision == "replace":
            replace_gained.append(case_id)
        if incumbent_decision == "replace" and decision != "replace":
            replace_lost.append(case_id)
        if incumbent_decision != "replace" and gold_decision == "replace" and decision == "replace":
            false_abstain_fixed.append(case_id)
        if incumbent_decision == "replace" and gold_decision == "replace" and decision != "replace":
            false_abstain_introduced.append(case_id)
        if (
            incumbent_decision == "replace"
            and str(incumbent_row.get("gold_decision") or "") != "replace"
            and decision != "replace"
        ):
            harmful_fixed.append(case_id)
        if incumbent_decision != "replace" and decision == "replace" and gold_decision != "replace":
            harmful_introduced.append(case_id)
    return {
        "config_id": config_id,
        "decision_changed_count": len(decision_changed),
        "winner_changed_count": len(winner_changed),
        "replace_gained_count": len(replace_gained),
        "replace_lost_count": len(replace_lost),
        "false_abstain_fixed_count": len(false_abstain_fixed),
        "false_abstain_introduced_count": len(false_abstain_introduced),
        "harmful_fixed_count": len(harmful_fixed),
        "harmful_introduced_count": len(harmful_introduced),
        "sample_decision_changed_case_ids": decision_changed[:8],
        "sample_false_abstain_fixed_case_ids": false_abstain_fixed[:8],
        "sample_false_abstain_introduced_case_ids": false_abstain_introduced[:8],
        "sample_harmful_introduced_case_ids": harmful_introduced[:8],
    }


def _build_negative_control_summary(
    config_rows: Sequence[Mapping[str, object]],
    *,
    incumbent: Mapping[str, object] | None,
) -> dict[str, object]:
    incumbent_accuracy = float(incumbent.get("decision_accuracy") or 0.0) if incumbent else 1.0
    rows: list[dict[str, object]] = []
    for row in config_rows:
        mode = str(row.get("expected_failure_mode") or "").strip()
        if not mode:
            continue
        failed_as_expected = _negative_control_failed_as_expected(
            row,
            mode=mode,
            incumbent_accuracy=incumbent_accuracy,
        )
        public = _public_config_row(row) or {}
        public["expected_failure_mode"] = mode
        public["status"] = "failed_as_expected" if failed_as_expected else "unexpectedly_safe"
        rows.append(public)
    if not rows:
        return {"status": "not_applicable", "rows": []}
    status = (
        "ok"
        if rows and all(row.get("status") == "failed_as_expected" for row in rows)
        else "review"
    )
    return {"status": status, "rows": rows}


def _build_overfitting_checks(
    config_rows: Sequence[Mapping[str, object]],
    case_results: Sequence[Mapping[str, object]],
    *,
    defaults: Mapping[str, object],
) -> dict[str, object]:
    by_config: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in case_results:
        by_config[str(row.get("config_id") or "")].append(row)
    rows: list[dict[str, object]] = []
    for config in config_rows:
        config_id = str(config.get("config_id") or "").strip()
        cases = by_config.get(config_id, [])
        discovery = [case for case in cases if str(case.get("split") or "") == "discovery"]
        locked = [case for case in cases if str(case.get("split") or "") == "locked_eval"]
        discovery_summary = _summary_from_cases(discovery)
        locked_summary = _summary_from_cases(locked)
        leave_one_out = _leave_one_family_out(cases)
        rows.append(
            {
                "config_id": config_id,
                "discovery_cases": discovery_summary.get("cases_total", 0),
                "locked_eval_cases": locked_summary.get("cases_total", 0),
                "discovery_objective_score": _objective_score(discovery_summary),
                "locked_eval_objective_score": _objective_score(locked_summary),
                "worst_leave_one_family": leave_one_out.get("worst_family_id", ""),
                "worst_leave_one_family_objective_score": leave_one_out.get(
                    "worst_objective_score"
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            float(row.get("locked_eval_objective_score") or 0.0),
            float(row.get("discovery_objective_score") or 0.0),
            str(row.get("config_id") or ""),
        )
    )
    return {
        "split_policy": "deterministic_case_id_hash_modulo",
        "split_modulo": int(defaults.get("split_modulo") or 4),
        "locked_eval_remainders": _normalize_ints(
            defaults.get("locked_eval_remainders"),
            default=(0,),
        ),
        "rows": rows,
    }


def _leave_one_family_out(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    family_ids = sorted(
        {str(case.get("family_id") or "") for case in cases if case.get("family_id")}
    )
    rows: list[dict[str, object]] = []
    for family_id in family_ids:
        summary = _summary_from_cases(
            [case for case in cases if case.get("family_id") != family_id]
        )
        rows.append(
            {
                "family_id": family_id,
                "objective_score": _objective_score(summary),
                "harmful_replace_count": summary.get("harmful_replace_count"),
                "false_abstain_count": summary.get("false_abstain_count"),
            }
        )
    if not rows:
        return {}
    worst = sorted(
        rows, key=lambda row: (-float(row.get("objective_score") or 0.0), row["family_id"])
    )[0]
    return {
        "rows": rows,
        "worst_family_id": worst["family_id"],
        "worst_objective_score": worst["objective_score"],
    }


def _summary_from_cases(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    summary = _new_sentence_veto_summary()
    for case in cases:
        _accumulate_sentence_veto_summary(summary, result=SimpleNamespace(**dict(case)))
    _finalize_sentence_veto_summary(summary)
    return summary


def _build_split_summaries(cases: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for split in ("discovery", "locked_eval"):
        split_cases = [case for case in cases if str(case.get("split") or "") == split]
        summary = _summary_from_cases(split_cases)
        public = _public_summary(summary)
        public.update(_ranking_metrics(split_cases))
        public["objective_score"] = _objective_score(public)
        rows[split] = public
    return rows


def _ranking_metrics(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    scored_rows: list[tuple[float, int, str]] = []
    for row in cases:
        case_id = str(row.get("case_id") or "").strip()
        label = 1 if str(row.get("gold_decision") or "") == "replace" else 0
        score = _finite_score(row.get("replacement_confidence"))
        scored_rows.append((score, label, case_id))
    positives = sum(label for _score, label, _case_id in scored_rows)
    negatives = len(scored_rows) - positives
    positive_scores = [score for score, label, _case_id in scored_rows if label == 1]
    negative_scores = [score for score, label, _case_id in scored_rows if label == 0]
    return {
        "ranking_positive_cases": positives,
        "ranking_negative_cases": negatives,
        "ranking_roc_auc": _roc_auc(scored_rows),
        "ranking_average_precision": _average_precision(scored_rows),
        "ranking_unique_score_count": len({score for score, _label, _case_id in scored_rows}),
        "ranking_positive_score_mean": _mean(positive_scores),
        "ranking_negative_score_mean": _mean(negative_scores),
        "ranking_positive_score_min": min(positive_scores) if positive_scores else None,
        "ranking_positive_score_max": max(positive_scores) if positive_scores else None,
        "ranking_negative_score_min": min(negative_scores) if negative_scores else None,
        "ranking_negative_score_max": max(negative_scores) if negative_scores else None,
    }


def _roc_auc(scored_rows: Sequence[tuple[float, int, str]]) -> float | None:
    positives = sum(label for _score, label, _case_id in scored_rows)
    negatives = len(scored_rows) - positives
    if positives <= 0 or negatives <= 0:
        return None
    sorted_rows = sorted(scored_rows, key=lambda row: row[0])
    rank_lookup: dict[str, float] = {}
    start = 0
    while start < len(sorted_rows):
        end = start + 1
        while end < len(sorted_rows) and sorted_rows[end][0] == sorted_rows[start][0]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for _score, _label, case_id in sorted_rows[start:end]:
            rank_lookup[case_id] = average_rank
        start = end
    positive_rank_sum = sum(
        rank_lookup[case_id] for _score, label, case_id in scored_rows if label == 1
    )
    auc = (positive_rank_sum - (positives * (positives + 1) / 2.0)) / (positives * negatives)
    return _round_float(auc)


def _average_precision(scored_rows: Sequence[tuple[float, int, str]]) -> float | None:
    positives = sum(label for _score, label, _case_id in scored_rows)
    if positives <= 0:
        return None
    sorted_rows = sorted(scored_rows, key=lambda row: (-row[0], row[2]))
    true_positive_count = 0
    precision_sum = 0.0
    for index, (_score, label, _case_id) in enumerate(sorted_rows, start=1):
        if label != 1:
            continue
        true_positive_count += 1
        precision_sum += true_positive_count / index
    return _round_float(precision_sum / positives)


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return _round_float(sum(values) / len(values))


def _finite_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isinf(score):
        return 1_000_000.0 if score > 0 else -1_000_000.0
    if math.isnan(score):
        return 0.0
    return score


def _build_recommendation(report: Mapping[str, object]) -> str:
    best = (
        report.get("best_by_constraint")
        if isinstance(report.get("best_by_constraint"), Mapping)
        else {}
    )
    incumbent = (
        best.get("incumbent_control") if isinstance(best.get("incumbent_control"), Mapping) else {}
    )
    candidate = (
        best.get("best_promotable_candidate")
        if isinstance(best.get("best_promotable_candidate"), Mapping)
        else {}
    )
    negative = (
        report.get("negative_control_summary")
        if isinstance(report.get("negative_control_summary"), Mapping)
        else {}
    )
    if not candidate:
        return (
            "No candidate cleared the incumbent-aware promotability screen; treat the matrix "
            "as evidence for source coverage or representation work before policy promotion."
        )
    notes = [
        f"Best promotable candidate is `{candidate.get('config_id', '')}`",
        f"with harmful `{int(candidate.get('harmful_replace_count') or 0)}`",
        f"and false abstain `{int(candidate.get('false_abstain_count') or 0)}`",
    ]
    if incumbent:
        notes.append(f"against incumbent `{incumbent.get('config_id', '')}`")
    negative_status = str(negative.get("status") or "").strip()
    if negative_status == "ok":
        notes.append("and negative controls failed as expected")
    elif negative_status == "not_applicable":
        notes.append("with negative controls delegated to the companion broad matrix")
    else:
        notes.append("but negative-control sanity needs review before promotion")
    return "; ".join(notes) + "."


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


def _apply_evidence_control(
    *,
    active_sense: Mapping[str, object],
    shadow_senses: Sequence[Mapping[str, object]],
    evidence_control: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    active = dict(active_sense)
    shadows = [dict(shadow) for shadow in shadow_senses]
    if evidence_control in {"normal", "target_lemma_only"}:
        return active, shadows
    if evidence_control in {"active_only_source", "no_shadow_competition"}:
        return active, []
    if evidence_control == "shadow_only_source":
        empty_active = dict(active)
        empty_active["evidence_views"] = {}
        empty_active["target_lemma"] = ""
        return empty_active, shadows
    if evidence_control == "shuffled_labels" and shadows:
        shuffled_active = dict(shadows[0])
        shuffled_shadows = [active, *shadows[1:]]
        return shuffled_active, shuffled_shadows
    return active, shadows


def _source_weights(config: Mapping[str, object]) -> dict[str, float]:
    raw = config.get("source_weights")
    weights = dict(DEFAULT_SOURCE_WEIGHTS)
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            try:
                weights[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
    return weights


def _dedupe_rows(rows: Sequence[EvidenceRow | None]) -> list[EvidenceRow]:
    seen: set[str] = set()
    deduped: list[EvidenceRow] = []
    for row in rows:
        if row is None:
            continue
        key = row.text.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _split_evidence_parts(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def _ordered_evidence_text(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> str:
    parts = _split_evidence_parts(evidence_views.get("all_evidence_text"))
    if not parts:
        parts = [
            str(evidence_views.get("sense_label") or "").strip(),
            str(evidence_views.get("gloss_text") or "").strip(),
        ]
    ordered_parts: list[str] = []
    target = str(sense.get("target_lemma") or "").strip()
    if target:
        ordered_parts.append(f"target={target}")
    for index, part in enumerate(parts, start=1):
        tokens = _tokenize_experiment_text(part)
        ordered_parts.append(f"part{index}=" + " ".join(tokens))
        ngrams = _ordered_ngram_text(tokens)
        if ngrams:
            ordered_parts.append(f"part{index}_order={ngrams}")
    return " | ".join(part for part in ordered_parts if part.strip())


def _canonical_template_evidence_text(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> str:
    target = str(sense.get("target_lemma") or "").strip()
    label = str(evidence_views.get("sense_label") or "").strip()
    gloss = str(evidence_views.get("gloss_text") or "").strip()
    bundle = str(evidence_views.get("sense_gloss_bundle") or "").strip()
    parts = []
    if target and gloss:
        parts.append(f"{target} means {gloss}")
        parts.append(f"use {target} when the context means {gloss}")
    if target and label:
        parts.append(f"{target} is the {label} sense")
    if bundle:
        parts.append(f"sense evidence says {bundle}")
    return " | ".join(parts)


def _paraphrase_variant_texts(
    evidence_views: Mapping[str, object],
    *,
    sense: Mapping[str, object],
) -> list[str]:
    target = str(sense.get("target_lemma") or "").strip()
    label = str(evidence_views.get("sense_label") or "").strip()
    gloss = str(evidence_views.get("gloss_text") or "").strip()
    variants = []
    if gloss:
        variants.append(gloss)
        variants.append(f"this context is about {gloss}")
    if label:
        variants.append(label)
        variants.append(f"this is the {label} meaning")
    if target and gloss:
        variants.append(f"{target}: {gloss}")
    return [variant for variant in variants if variant.strip()]


def _strongest_shadow(shadow_scores: Sequence[SenseScore]) -> SenseScore | None:
    if not shadow_scores:
        return None
    return sorted(
        shadow_scores,
        key=lambda score: (-float(score.aggregate_score), score.sense_id),
    )[0]


def _active_ratio(active_score: float, strongest_shadow_score: float, has_shadow: bool) -> float:
    if not has_shadow:
        return math.inf if active_score > 0 else 0.0
    if strongest_shadow_score <= 0:
        return math.inf if active_score > 0 else 0.0
    return active_score / strongest_shadow_score


def _active_softmax_probability(
    active_score: float,
    shadow_scores: Sequence[float],
    *,
    temperature: float,
) -> float:
    values = [float(active_score), *(float(score) for score in shadow_scores)]
    if not values:
        return 0.0
    scaled = [value * max(0.01, temperature) for value in values]
    max_value = max(scaled)
    exp_values = [math.exp(value - max_value) for value in scaled]
    denominator = sum(exp_values)
    return exp_values[0] / denominator if denominator > 0 else 0.0


def _pairwise_win_rate(
    active_score: float,
    shadow_scores: Sequence[float],
    *,
    min_margin: float,
) -> float:
    if not shadow_scores:
        return 1.0
    wins = sum(1 for score in shadow_scores if active_score - float(score) >= min_margin)
    return wins / len(shadow_scores)


def _replacement_confidence(
    *,
    decision_rule: str,
    margin: float,
    ratio: float,
    probability: float,
    pairwise_win_rate: float,
    strongest_shadow_score: float,
) -> float:
    if decision_rule == "active_ratio_strongest_shadow":
        return ratio
    if decision_rule == "softmax_probability":
        return probability
    if decision_rule in {"pairwise_active_beats_all_shadows", "pairwise_active_beats_most_shadows"}:
        return pairwise_win_rate
    if decision_rule == "shadow_veto_only":
        return -float(strongest_shadow_score)
    return margin


def _public_summary(summary: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "cases_total",
        "gold_replace_cases",
        "gold_abstain_cases",
        "gold_active_winner_cases",
        "gold_shadow_winner_cases",
        "gold_none_cases",
        "predicted_replace_cases",
        "predicted_abstain_cases",
        "true_replace_count",
        "true_abstain_count",
        "harmful_replace_count",
        "false_abstain_count",
        "winner_labeled_cases",
        "winner_correct_count",
        "shadow_winner_labeled_cases",
        "shadow_winner_correct_count",
        "phrase_preemption_hit_count",
        "decision_accuracy",
        "replace_precision",
        "replace_recall",
        "harmful_replace_rate",
        "false_abstain_rate",
        "winner_accuracy",
        "shadow_winner_accuracy",
        "predicted_replace_rate",
        "phrase_preemption_hit_rate",
        "phrase_preemption_precision",
    )
    return {key: summary.get(key) for key in keys}


def _objective_score(row: Mapping[str, object]) -> float:
    harmful = int(row.get("harmful_replace_count") or 0)
    false_abstain = int(row.get("false_abstain_count") or 0)
    accuracy_penalty = 1.0 - float(row.get("decision_accuracy") or 0.0)
    winner_penalty = 1.0 - float(row.get("winner_accuracy") or 0.0)
    return round((harmful * 1000.0) + (false_abstain * 10.0) + accuracy_penalty + winner_penalty, 6)


def _rank_key(row: Mapping[str, object]) -> tuple[float, int, int, str]:
    return (
        float(row.get("objective_score") or 0.0),
        int(row.get("harmful_replace_count") or 0),
        int(row.get("false_abstain_count") or 0),
        str(row.get("config_id") or ""),
    )


def _split_rank_key(row: Mapping[str, object], *, split: str) -> tuple[float, int, int, str]:
    split_summary = _split_summary(row, split)
    return (
        float(split_summary.get("objective_score") or 0.0),
        int(split_summary.get("harmful_replace_count") or 0),
        int(split_summary.get("false_abstain_count") or 0),
        str(row.get("config_id") or ""),
    )


def _ranking_quality_key(row: Mapping[str, object]) -> tuple[float, float, str]:
    return (
        -float(row.get("ranking_roc_auc") or 0.0),
        -float(row.get("ranking_average_precision") or 0.0),
        str(row.get("config_id") or ""),
    )


def _select_best(rows: object) -> Mapping[str, object] | None:
    materialized = [row for row in rows or () if isinstance(row, Mapping)]
    if not materialized:
        return None
    return sorted(materialized, key=_rank_key)[0]


def _select_best_for_split(
    rows: object,
    split: str,
) -> Mapping[str, object] | None:
    materialized = [row for row in rows or () if isinstance(row, Mapping)]
    materialized = [
        row for row in materialized if int(_split_summary(row, split).get("cases_total") or 0) > 0
    ]
    if not materialized:
        return None
    return sorted(materialized, key=lambda row: _split_rank_key(row, split=split))[0]


def _select_incumbent(config_rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    controls = [row for row in config_rows if bool(row.get("is_control"))]
    return _select_best(controls) or _select_best(config_rows)


def _public_config_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    keys = (
        "config_id",
        "label",
        "category",
        "algorithm_family",
        "parameter_set_id",
        "is_control",
        "scorer_id",
        "context_view",
        "evidence_selector_context_view",
        "evidence_selector_source_view",
        "sense_representation",
        "aggregation_rule",
        "decision_rule",
        "phrase_handling",
        "evidence_control",
        "source_evidence_scope_id",
        "source_evidence_batch_count",
        "source_evidence_attached_row_count",
        "fit_scope",
        "min_active_score",
        "min_margin",
        "ratio_threshold",
        "softmax_threshold",
        "pairwise_min_win_rate",
        "selection_top_k",
        "cases_total",
        "harmful_replace_count",
        "false_abstain_count",
        "decision_accuracy",
        "winner_accuracy",
        "shadow_winner_accuracy",
        "replace_recall",
        "ranking_roc_auc",
        "ranking_average_precision",
        "ranking_unique_score_count",
        "objective_score",
        "harmful_replace_case_ids",
        "false_abstain_case_ids",
        "predicted_replace_case_ids",
        "replace_case_signature",
    )
    return {key: row.get(key) for key in keys}


def _public_selection_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(row, Mapping):
        return None
    return {
        "config_id": str(row.get("config_id") or "").strip(),
        "algorithm_family": str(row.get("algorithm_family") or "").strip(),
        "parameter_set_id": str(row.get("parameter_set_id") or "").strip(),
        "decision_rule": str(row.get("decision_rule") or "").strip(),
        "min_active_score": row.get("min_active_score"),
        "min_margin": row.get("min_margin"),
        "ratio_threshold": row.get("ratio_threshold"),
        "softmax_threshold": row.get("softmax_threshold"),
        "pairwise_min_win_rate": row.get("pairwise_min_win_rate"),
        "overall": _public_config_row(row),
        "discovery": dict(_split_summary(row, "discovery")),
        "locked_eval": dict(_split_summary(row, "locked_eval")),
    }


def _public_case_row(row: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "case_id",
        "original_case_id",
        "family_id",
        "original_family_id",
        "evaluation_suite_id",
        "evaluation_suite_role",
        "gold_decision",
        "gold_winner",
        "gold_winner_type",
        "predicted_decision",
        "predicted_winner",
        "predicted_winner_type",
        "active_score",
        "strongest_shadow_score",
        "margin",
        "replacement_confidence",
        "phrase_preemption_hit",
        "phrase_reason_code",
        "reason_codes",
    )
    return {key: row.get(key) for key in keys}


def _primary_metric_signature(row: Mapping[str, object]) -> str:
    return "|".join(
        (
            f"harm={int(row.get('harmful_replace_count') or 0)}",
            f"false={int(row.get('false_abstain_count') or 0)}",
            f"decision={float(row.get('decision_accuracy') or 0.0):.6f}",
            f"winner={float(row.get('winner_accuracy') or 0.0):.6f}",
        )
    )


def _split_summary(row: Mapping[str, object], split: str) -> Mapping[str, object]:
    summaries = row.get("split_summaries")
    if isinstance(summaries, Mapping):
        summary = summaries.get(split)
        if isinstance(summary, Mapping):
            return summary
    return {}


def _same_config(
    left: Mapping[str, object] | None,
    right: Mapping[str, object] | None,
) -> bool:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    return str(left.get("config_id") or "") == str(right.get("config_id") or "")


def _split_objective_gap(
    left: Mapping[str, object] | None,
    right: Mapping[str, object] | None,
    *,
    split: str,
) -> float | None:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return None
    return _round_float(
        float(_split_summary(left, split).get("objective_score") or 0.0)
        - float(_split_summary(right, split).get("objective_score") or 0.0)
    )


def _selection_locked_objective(row: Mapping[str, object]) -> float:
    selected = row.get("selected_on_discovery")
    if not isinstance(selected, Mapping):
        return 0.0
    locked = selected.get("locked_eval")
    if not isinstance(locked, Mapping):
        return 0.0
    return float(locked.get("objective_score") or 0.0)


def _group_by(
    rows: Sequence[Mapping[str, object]], key: str
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "")].append(row)
    return dict(grouped)


def _negative_control_failed_as_expected(
    row: Mapping[str, object],
    *,
    mode: str,
    incumbent_accuracy: float,
) -> bool:
    harmful = int(row.get("harmful_replace_count") or 0)
    false_abstain = int(row.get("false_abstain_count") or 0)
    accuracy = float(row.get("decision_accuracy") or 0.0)
    if mode == "over_replace":
        return harmful > 0
    if mode == "over_abstain":
        return false_abstain > 0
    if mode in {"collapse", "lexical_leakage"}:
        return accuracy < incumbent_accuracy
    return harmful > 0 or false_abstain > 0 or accuracy < incumbent_accuracy


def _is_harmful_replace(row: Mapping[str, object]) -> bool:
    return row.get("predicted_decision") == "replace" and row.get("gold_decision") != "replace"


def _is_false_abstain(row: Mapping[str, object]) -> bool:
    return row.get("predicted_decision") != "replace" and row.get("gold_decision") == "replace"


def _classify_gold_winner_type(gold_winner: str, *, active_sense_id: str) -> str:
    normalized = str(gold_winner or "").strip()
    if not normalized or normalized in {"none", "abstain"}:
        return "none"
    if normalized == active_sense_id:
        return "active"
    return "shadow"


def _case_split(
    case_id: str,
    *,
    split_modulo: int,
    locked_eval_remainders: Sequence[int],
) -> str:
    modulo = max(2, int(split_modulo))
    digest = hashlib.sha256(str(case_id or "").encode("utf-8")).hexdigest()
    remainder = int(digest[:8], 16) % modulo
    return "locked_eval" if remainder in set(locked_eval_remainders) else "discovery"


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


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _resolve_project_path(value: object, *, default: Path) -> Path:
    raw = str(value or "").strip()
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _case_id_signature(case_ids: Sequence[str]) -> str:
    normalized = "\n".join(
        sorted(str(case_id or "").strip() for case_id in case_ids if str(case_id or "").strip())
    )
    return _text_sha256(normalized)[:16]


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


def _round_float(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isinf(number):
        return number
    return round(number, 6)


def _render_public_config_row(label: str, row: Mapping[str, object]) -> list[str]:
    return [
        f"- {label}: `{row.get('config_id', '')}`",
        f"  - Harmful / false abstain: `{int(row.get('harmful_replace_count') or 0)}` / `{int(row.get('false_abstain_count') or 0)}`",
        f"  - Decision / winner accuracy: `{_render_rate(row.get('decision_accuracy'))}` / `{_render_rate(row.get('winner_accuracy'))}`",
        f"  - Shape: `{row.get('scorer_id', '')}:{row.get('context_view', '')}:{row.get('sense_representation', '')}:{row.get('aggregation_rule', '')}:{row.get('decision_rule', '')}:{row.get('phrase_handling', '')}`",
        f"  - Source scope: `{row.get('source_evidence_scope_id', '')}` (`{int(row.get('source_evidence_attached_row_count') or 0)}` attached rows)",
    ]


def _as_mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _breakdown_summary(row: Mapping[str, object]) -> Mapping[str, object]:
    summary = row.get("summary")
    return summary if isinstance(summary, Mapping) else row


def _render_rate(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "n/a"


def _render_float(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def _render_range(left: object, right: object) -> str:
    return f"{_render_float(left)}..{_render_float(right)}"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare decomposed en-es semantic decision-rule configurations offline.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_decision_rule_matrix_report(manifest_path=args.manifest)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_decision_rule_matrix_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
