#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_AUDIT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_standalone_independence_broad_audit_en_ja_latest.json"
)
DEFAULT_JMDICT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "jmdict-ja-en"
    / "JMdict_e"
)
DEFAULT_KANJIDIC2 = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "kanjidic2-ja"
    / "kanjidic2.xml"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_compound_leak_sweep_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_compound_leak_sweep_en_ja_latest.md"
)
PAIRWISE_MIN_EXPECTED_GAP = 0.03
PAIRWISE_TIE_TOLERANCE = 0.01
BEGINNER_CORE_MAX = 0.20
BEGINNER_CORE_OBSERVED_CEILING = 0.25
BEGINNER_BROAD_MAX = 0.40
BEGINNER_BROAD_OBSERVED_CEILING = 0.50
UPPER_TAIL_MIN = 0.88
UPPER_TAIL_OBSERVED_FLOOR = 0.80
HIGH_TAIL_MIN = 0.94
HIGH_TAIL_OBSERVED_FLOOR = 0.88
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})


class ScoreOverlay(Mapping[tuple[str, str], float]):
    def __init__(
        self,
        base: Mapping[tuple[str, str], float],
        overrides: Mapping[tuple[str, str], float],
    ) -> None:
        self.base = base
        self.overrides = overrides

    def __getitem__(self, key: tuple[str, str]) -> float:
        if key in self.overrides:
            return self.overrides[key]
        return self.base[key]

    def __iter__(self) -> Iterator[tuple[str, str]]:
        return iter(self.base)

    def __len__(self) -> int:
        return len(self.base)

    def get(self, key: tuple[str, str], default: object = None) -> object:
        if key in self.overrides:
            return self.overrides[key]
        return self.base.get(key, default)  # type: ignore[arg-type]


@dataclass(frozen=True)
class SweepVariant:
    variant_id: str
    leak_source: str
    leak_threshold: float
    leak_power: float
    mass_scale: float
    surface_len_cap: int
    destination: float
    strength: float
    max_shift: float
    jlpt_protection: float
    exact_priority_protection: float
    direct_support_protection: float
    scope_mode: str
    core_guard_strength: float
    standalone_guard_mode: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Targeted sidecar sweep for en-ja compound-leak difficulty corrections.")
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--kanjidic2", type=Path, default=DEFAULT_KANJIDIC2)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--retain-limit", type=int, default=40)
    parser.add_argument("--preview-limit", type=int, default=40)
    parser.add_argument(
        "--variant-preset",
        choices=("full", "guard-probe"),
        default="full",
        help="Use guard-probe for a narrow comparison of standalone guard modes.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        ranking_csv=_resolve_path(args.ranking_csv),
        audit_json=_resolve_path(args.audit_json),
        jmdict_path=_resolve_path(args.jmdict),
        kanjidic2_path=_resolve_path(args.kanjidic2),
        calibration_json=_resolve_path(args.calibration_json),
        holdout_json=_resolve_path(args.holdout_json),
        retain_limit=max(1, int(args.retain_limit)),
        preview_limit=max(1, int(args.preview_limit)),
        variant_preset=str(args.variant_preset),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    ranking_csv: Path,
    audit_json: Path,
    jmdict_path: Path,
    kanjidic2_path: Path,
    calibration_json: Path,
    holdout_json: Path,
    retain_limit: int,
    preview_limit: int,
    variant_preset: str,
) -> dict[str, Any]:
    ranking_rows = load_ranking_rows(ranking_csv)
    rows_by_key = {(row["lemma"], row["reading"]): row for row in ranking_rows}
    audit = json.loads(audit_json.read_text(encoding="utf-8"))
    audit_by_key = {(row["lemma"], row["reading"]): row for row in audit["rows"]}
    row_contexts = build_row_contexts(
        rows_by_key=rows_by_key,
        audit_by_key=audit_by_key,
        jmdict_path=jmdict_path,
        kanjidic2_path=kanjidic2_path,
    )
    calibration_labels = load_numeric_labels(calibration_json)
    holdout_labels = load_numeric_labels(holdout_json)
    base_model_scores = {
        key: optional_float(row.get("model_score")) or optional_float(row.get("score")) or 1.0
        for key, row in rows_by_key.items()
    }
    corrected_scores = {
        key: optional_float(row.get("score")) or base_model_scores[key]
        for key, row in rows_by_key.items()
    }
    baselines = {
        "model_score": evaluate_score_map(
            base_model_scores,
            rows_by_key=rows_by_key,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            audit_by_key=audit_by_key,
            changed_keys=set(),
        ),
        "current_corrected_score": evaluate_score_map(
            corrected_scores,
            rows_by_key=rows_by_key,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            audit_by_key=audit_by_key,
            changed_keys=corrected_changed_keys(rows_by_key),
        ),
    }
    approximate: list[dict[str, Any]] = []
    variants = iter_variants(variant_preset)
    for variant in variants:
        score_overrides, pressure_by_key = apply_variant(
            variant,
            base_scores=base_model_scores,
            rows_by_key=rows_by_key,
            audit_by_key=audit_by_key,
            row_contexts=row_contexts,
        )
        candidate_scores = ScoreOverlay(base_model_scores, score_overrides)
        changed_keys = set(score_overrides)
        metrics = evaluate_score_map(
            candidate_scores,
            rows_by_key=rows_by_key,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            audit_by_key=audit_by_key,
            changed_keys=changed_keys,
            include_expensive=False,
        )
        approximate.append(
            {
                "variant": variant_to_dict(variant),
                "_variant_obj": variant,
                "selection_score": selection_score(metrics, baselines["model_score"]),
                "metrics": metrics,
            }
        )
    approximate.sort(
        key=lambda row: (
            -float(row["selection_score"]),
            -metric_value(row, "holdout", "balanced_score"),
            -metric_value(row, "manual_compoundish", "changed_f1"),
            metric_value(row, "change", "changed_count"),
        )
    )
    exact: list[dict[str, Any]] = []
    exact_retain_count = max(retain_limit * 8, retain_limit)
    for approx_row in approximate[:exact_retain_count]:
        variant = approx_row["_variant_obj"]
        score_overrides, pressure_by_key = apply_variant(
            variant,
            base_scores=base_model_scores,
            rows_by_key=rows_by_key,
            audit_by_key=audit_by_key,
            row_contexts=row_contexts,
        )
        candidate_scores = ScoreOverlay(base_model_scores, score_overrides)
        changed_keys = set(score_overrides)
        metrics = evaluate_score_map(
            candidate_scores,
            rows_by_key=rows_by_key,
            calibration_labels=calibration_labels,
            holdout_labels=holdout_labels,
            audit_by_key=audit_by_key,
            changed_keys=changed_keys,
            include_expensive=True,
        )
        exact.append(
            {
                "variant": variant_to_dict(variant),
                "selection_score": selection_score(metrics, baselines["model_score"]),
                "approximate_selection_score": approx_row["selection_score"],
                "metrics": metrics,
                "changed_preview": changed_preview(
                    changed_keys=changed_keys,
                    base_scores=base_model_scores,
                    candidate_scores=candidate_scores,
                    rows_by_key=rows_by_key,
                    audit_by_key=audit_by_key,
                    row_contexts=row_contexts,
                    variant=variant,
                    pressure_by_key=pressure_by_key,
                    limit=preview_limit,
                ),
            }
        )
    exact.sort(
        key=lambda row: (
            -float(row["selection_score"]),
            -metric_value(row, "holdout", "balanced_score"),
            -metric_value(row, "manual_compoundish", "changed_f1"),
            metric_value(row, "change", "changed_count"),
        )
    )
    best = exact[:retain_limit]
    return {
        "schema_version": 1,
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "scores_changed": False,
        "purpose": (
            "Targeted sweep over compound frequency leakage transforms. "
            "This tests automatic correction shapes without changing the ranking."
        ),
        "inputs": {
            "ranking_csv": repo_path(ranking_csv),
            "audit_json": repo_path(audit_json),
            "jmdict": str(jmdict_path),
            "kanjidic2": str(kanjidic2_path),
            "calibration_json": repo_path(calibration_json),
            "holdout_json": repo_path(holdout_json),
            "ranking_row_count": len(ranking_rows),
            "audit_row_count": len(audit_by_key),
            "calibration_numeric_label_count": len(calibration_labels),
            "holdout_numeric_label_count": len(holdout_labels),
            "variant_count": len(variants),
            "variant_preset": variant_preset,
            "exact_retained_candidate_count": len(exact),
        },
        "method": {
            "base_score": "model_score from corrected ranking CSV; falls back to score",
            "feature": "compound frequency mass Cx compared with direct mass Fx",
            "core_formula": (
                "pressure = leak_excess^power * mass_confidence * morpheme_scope "
                "* protection_terms; score = base + min(max_shift, strength * "
                "pressure * max(0, destination - base))"
            ),
            "context_formula": (
                "context-aware variants multiply morpheme_scope by a source-backed "
                "component likelihood from KANJIDIC2 on/kun readings plus JMDict "
                "exact POS/misc tags, then optionally subtract a core-standalone "
                "guard for strong exact priority, exact JLPT/commonness, and kun "
                "standalone evidence."
            ),
            "changed_key_threshold": "candidate_score > base_score + 0.01",
        },
        "baselines": baselines,
        "leaderboard": best,
    }


def iter_variants(preset: str = "full") -> list[SweepVariant]:
    variants: list[SweepVariant] = []
    if preset == "guard-probe":
        return guard_probe_variants()
    if preset != "full":
        raise ValueError(f"unknown variant preset: {preset}")
    protection_presets = (
        (0.0, 0.0, 0.0),
        (0.10, 0.15, 0.15),
    )
    scope_presets = (
        ("broad", 0.0),
        ("component", 0.0),
        ("component_core_guard", 0.60),
        ("component_core_guard", 0.85),
        ("strict_component_core_guard", 1.00),
    )
    standalone_guard_modes = (
        "legacy",
        "plain_noun_direct",
        "ordinary_noun_direct",
    )
    for leak_source in ("combined_log", "raw_combined"):
        for leak_threshold in (0.90, 0.94, 0.97):
            for leak_power in (0.5, 1.0):
                for mass_scale in (20.0, 60.0):
                    for surface_len_cap in (1, 2, 3):
                        for destination in (0.30, 0.40, 0.55):
                            for strength in (0.50, 0.75, 1.00):
                                for max_shift in (0.08, 0.15):
                                    for (
                                        jlpt_protection,
                                        exact_priority_protection,
                                        direct_support_protection,
                                    ) in protection_presets:
                                        for scope_mode, core_guard_strength in scope_presets:
                                            for standalone_guard_mode in standalone_guard_modes:
                                                variant_id = (
                                                    f"{leak_source}_t{leak_threshold:.2f}"
                                                    f"_p{leak_power:g}_m{mass_scale:g}"
                                                    f"_l{surface_len_cap}_d{destination:.2f}"
                                                    f"_s{strength:g}_x{max_shift:g}"
                                                    f"_j{jlpt_protection:g}"
                                                    f"_pri{exact_priority_protection:g}"
                                                    f"_dir{direct_support_protection:g}"
                                                    f"_scope{scope_mode}"
                                                    f"_core{core_guard_strength:g}"
                                                    f"_stand{standalone_guard_mode}"
                                                )
                                                variants.append(
                                                    SweepVariant(
                                                        variant_id=variant_id,
                                                        leak_source=leak_source,
                                                        leak_threshold=leak_threshold,
                                                        leak_power=leak_power,
                                                        mass_scale=mass_scale,
                                                        surface_len_cap=surface_len_cap,
                                                        destination=destination,
                                                        strength=strength,
                                                        max_shift=max_shift,
                                                        jlpt_protection=jlpt_protection,
                                                        exact_priority_protection=exact_priority_protection,
                                                        direct_support_protection=direct_support_protection,
                                                        scope_mode=scope_mode,
                                                        core_guard_strength=core_guard_strength,
                                                        standalone_guard_mode=standalone_guard_mode,
                                                    )
                                                )
    return variants


def guard_probe_variants() -> list[SweepVariant]:
    variants: list[SweepVariant] = []
    protection_presets = ((0.10, 0.15, 0.15),)
    scope_presets = (
        ("strict_component_core_guard", 1.00),
        ("component_core_guard", 0.85),
    )
    standalone_guard_modes = (
        "legacy",
        "plain_noun_direct",
        "ordinary_noun_direct",
    )
    for leak_threshold in (0.90, 0.94, 0.97):
        for leak_power in (0.5, 1.0):
            for surface_len_cap in (2, 3):
                for scope_mode, core_guard_strength in scope_presets:
                    for standalone_guard_mode in standalone_guard_modes:
                        for (
                            jlpt_protection,
                            exact_priority_protection,
                            direct_support_protection,
                        ) in protection_presets:
                            variant_id = (
                                f"guard_probe_combined_log_t{leak_threshold:.2f}"
                                f"_p{leak_power:g}_l{surface_len_cap}"
                                f"_scope{scope_mode}_core{core_guard_strength:g}"
                                f"_stand{standalone_guard_mode}"
                            )
                            variants.append(
                                SweepVariant(
                                    variant_id=variant_id,
                                    leak_source="combined_log",
                                    leak_threshold=leak_threshold,
                                    leak_power=leak_power,
                                    mass_scale=20.0,
                                    surface_len_cap=surface_len_cap,
                                    destination=0.30,
                                    strength=0.50,
                                    max_shift=0.08,
                                    jlpt_protection=jlpt_protection,
                                    exact_priority_protection=exact_priority_protection,
                                    direct_support_protection=direct_support_protection,
                                    scope_mode=scope_mode,
                                    core_guard_strength=core_guard_strength,
                                    standalone_guard_mode=standalone_guard_mode,
                                )
                            )
    return variants


def apply_variant(
    variant: SweepVariant,
    *,
    base_scores: Mapping[tuple[str, str], float],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    row_contexts: Mapping[tuple[str, str], Mapping[str, Any]],
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float]]:
    score_overrides: dict[tuple[str, str], float] = {}
    pressure_by_key: dict[tuple[str, str], float] = {}
    for key, audit_row in audit_by_key.items():
        if key not in base_scores:
            continue
        lemma, reading = key
        if len(lemma) > variant.surface_len_cap:
            continue
        pressure = compound_pressure(
            variant,
            audit_row,
            rows_by_key.get(key, {}),
            row_contexts.get(key, {}),
        )
        if pressure <= 0.0:
            continue
        base = float(base_scores[key])
        destination_gap = max(0.0, variant.destination - base)
        shift = min(variant.max_shift, variant.strength * pressure * destination_gap)
        if shift <= 0.009999:
            continue
        score_overrides[key] = min(1.0, base + shift)
        pressure_by_key[key] = pressure
    return score_overrides, pressure_by_key


def compound_pressure(
    variant: SweepVariant,
    audit_row: Mapping[str, Any],
    ranking_row: Mapping[str, str],
    row_context: Mapping[str, Any],
) -> float:
    mass = audit_row["frequency_mass"]
    graph = audit_row["jmdict_graph"]
    leak = leak_value(variant.leak_source, mass)
    leak_excess = normalized_excess(leak, variant.leak_threshold)
    if leak_excess <= 0.0:
        return 0.0
    compound_log = float(mass.get("compound_log_combined_total") or 0.0)
    mass_confidence = min(1.0, compound_log / variant.mass_scale)
    if mass_confidence <= 0.0:
        return 0.0
    lemma = str(audit_row["lemma"])
    reading = str(audit_row["reading"])
    morpheme = morpheme_multiplier(lemma, reading) * scope_multiplier(
        variant,
        row_context,
    )
    if morpheme <= 0.0:
        return 0.0
    protection = 1.0
    if truthy(ranking_row.get("jlpt_exact_known")):
        protection *= 1.0 - variant.jlpt_protection
    if int(graph.get("exact_priority_entry_count") or 0) > 0:
        protection *= 1.0 - variant.exact_priority_protection
    direct_log = float(mass.get("direct_log_combined_total") or 0.0)
    if direct_log >= 12.0:
        protection *= 1.0 - variant.direct_support_protection
    return clamp01((leak_excess**variant.leak_power) * mass_confidence * morpheme * protection)


def scope_multiplier(variant: SweepVariant, row_context: Mapping[str, Any]) -> float:
    if variant.scope_mode == "broad":
        return 1.0
    component = float(row_context.get("component_likelihood") or 0.0)
    core_guard = float(row_context.get("core_standalone_guard") or 0.0)
    if variant.scope_mode == "component":
        return component
    if variant.scope_mode == "component_core_guard":
        core_guard = selected_core_guard(variant, row_context)
        return component * (1.0 - (variant.core_guard_strength * core_guard))
    if variant.scope_mode == "strict_component_core_guard":
        strict_component = float(row_context.get("strict_component_likelihood") or 0.0)
        core_guard = selected_core_guard(variant, row_context)
        return strict_component * (1.0 - (variant.core_guard_strength * core_guard))
    raise ValueError(f"unknown scope mode: {variant.scope_mode}")


def selected_core_guard(variant: SweepVariant, row_context: Mapping[str, Any]) -> float:
    key = f"core_standalone_guard_{variant.standalone_guard_mode}"
    if key in row_context:
        return float(row_context.get(key) or 0.0)
    return float(row_context.get("core_standalone_guard") or 0.0)


def leak_value(source: str, mass: Mapping[str, Any]) -> float:
    if source == "combined_log":
        return float(mass.get("combined_log_leak_share") or 0.0)
    if source == "raw_combined":
        return float(mass.get("raw_combined_leak_share") or 0.0)
    if source == "max_source":
        return max(
            float(mass.get("bccwj_leak_share") or 0.0),
            float(mass.get("aozora_leak_share") or 0.0),
        )
    raise ValueError(f"unknown leak source: {source}")


def build_row_contexts(
    *,
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    jmdict_path: Path,
    kanjidic2_path: Path,
) -> dict[tuple[str, str], dict[str, Any]]:
    keys = set(audit_by_key) & set(rows_by_key)
    kanjidic_readings = load_kanjidic2_readings(kanjidic2_path)
    jmdict_meta = load_jmdict_exact_metadata(jmdict_path, keys)
    contexts: dict[tuple[str, str], dict[str, Any]] = {}
    for key in keys:
        row = rows_by_key[key]
        audit = audit_by_key[key]
        meta = jmdict_meta.get(key, empty_jmdict_meta())
        reading_profile = kanjidic_reading_profile(key, kanjidic_readings)
        component_likelihood, component_reasons = component_likelihood_for_row(
            row=row,
            audit=audit,
            meta=meta,
            reading_profile=reading_profile,
        )
        strict_likelihood, strict_reasons = strict_component_likelihood_for_row(
            row=row,
            audit=audit,
            meta=meta,
            reading_profile=reading_profile,
        )
        legacy_guard, legacy_reasons = core_standalone_guard_for_row(
            row=row,
            audit=audit,
            meta=meta,
            reading_profile=reading_profile,
        )
        plain_guard, plain_reasons = direct_standalone_guard_for_row(
            row=row,
            audit=audit,
            meta=meta,
            mode="plain_noun_direct",
        )
        ordinary_guard, ordinary_reasons = direct_standalone_guard_for_row(
            row=row,
            audit=audit,
            meta=meta,
            mode="ordinary_noun_direct",
        )
        contexts[key] = {
            **reading_profile,
            "jmdict_exact_pos": sorted(meta["pos"]),
            "jmdict_exact_misc": sorted(meta["misc"]),
            "jmdict_exact_field": sorted(meta["field"]),
            "jmdict_exact_priority_tags": sorted(meta["priority_tags"]),
            "jmdict_exact_first_sense_pos": first_sense_values(meta, "pos"),
            "jmdict_exact_first_sense_misc": first_sense_values(meta, "misc"),
            "component_likelihood": rounded(component_likelihood),
            "component_reasons": component_reasons,
            "strict_component_likelihood": rounded(strict_likelihood),
            "strict_component_reasons": strict_reasons,
            "core_standalone_guard": rounded(legacy_guard),
            "core_standalone_guard_legacy": rounded(legacy_guard),
            "core_standalone_guard_plain_noun_direct": rounded(max(legacy_guard, plain_guard)),
            "core_standalone_guard_ordinary_noun_direct": rounded(
                max(legacy_guard, ordinary_guard)
            ),
            "core_guard_reasons": legacy_reasons,
            "core_guard_reasons_legacy": legacy_reasons,
            "core_guard_reasons_plain_noun_direct": merge_reasons(
                legacy_reasons,
                plain_reasons,
            ),
            "core_guard_reasons_ordinary_noun_direct": merge_reasons(
                legacy_reasons,
                ordinary_reasons,
            ),
        }
    return contexts


def load_kanjidic2_readings(path: Path) -> dict[str, dict[str, set[str]]]:
    readings: dict[str, dict[str, set[str]]] = {}
    if not path.exists():
        return readings
    for _event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "character":
            continue
        literal = (elem.findtext("literal") or "").strip()
        if not literal:
            elem.clear()
            continue
        entry = {"on": set(), "kun": set(), "nanori": set()}
        for node in elem.findall("./reading_meaning/rmgroup/reading"):
            value = normalize_reading_option(node.text or "")
            if not value:
                continue
            reading_type = str(node.attrib.get("r_type") or "")
            if reading_type == "ja_on":
                entry["on"].add(value)
            elif reading_type == "ja_kun":
                entry["kun"].add(value)
        for node in elem.findall("./reading_meaning/nanori"):
            value = normalize_reading_option(node.text or "")
            if value:
                entry["nanori"].add(value)
        readings[literal] = entry
        elem.clear()
    return readings


def load_jmdict_exact_metadata(
    path: Path,
    keys: set[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    metadata = {key: empty_jmdict_meta() for key in keys}
    if not path.exists() or not keys:
        return metadata
    surface_to_keys: dict[str, set[tuple[str, str]]] = {}
    for surface, reading in keys:
        surface_to_keys.setdefault(surface, set()).add((surface, normalize_kana(reading)))
    for _event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "entry":
            continue
        forms = [
            {
                "text": child.findtext("keb") or "",
                "priorities": {node.text or "" for node in child.findall("ke_pri") if node.text},
            }
            for child in elem.findall("k_ele")
            if child.findtext("keb")
        ]
        if not any(str(form["text"]) in surface_to_keys for form in forms):
            elem.clear()
            continue
        readings = []
        for child in elem.findall("r_ele"):
            text = child.findtext("reb") or ""
            if not text:
                continue
            readings.append(
                {
                    "text": text,
                    "normalized": normalize_kana(text),
                    "priorities": {
                        node.text or "" for node in child.findall("re_pri") if node.text
                    },
                    "restrictions": {
                        node.text or "" for node in child.findall("re_restr") if node.text
                    },
                }
            )
        senses = []
        for sense in elem.findall("sense"):
            sense_payload = {
                "pos": [node.text or "" for node in sense.findall("pos") if node.text],
                "misc": [node.text or "" for node in sense.findall("misc") if node.text],
                "field": [node.text or "" for node in sense.findall("field") if node.text],
            }
            senses.append(sense_payload)
        pos_tags = {value for sense in senses for value in sense["pos"]}
        misc_tags = {value for sense in senses for value in sense["misc"]}
        field_tags = {value for sense in senses for value in sense["field"]}
        for form in forms:
            surface = str(form["text"])
            for key in surface_to_keys.get(surface, ()):
                for reading in readings:
                    if str(reading["normalized"]) != key[1]:
                        continue
                    if not reading_allowed_for_form(reading, surface):
                        continue
                    target = metadata[key]
                    target["pos"].update(pos_tags)
                    target["misc"].update(misc_tags)
                    target["field"].update(field_tags)
                    target["senses"].extend(senses)
                    target["priority_tags"].update(form["priorities"])
                    target["priority_tags"].update(reading["priorities"])
        elem.clear()
    return metadata


def empty_jmdict_meta() -> dict[str, Any]:
    return {
        "pos": set(),
        "misc": set(),
        "field": set(),
        "priority_tags": set(),
        "senses": [],
    }


def kanjidic_reading_profile(
    key: tuple[str, str],
    kanjidic_readings: Mapping[str, Mapping[str, set[str]]],
) -> dict[str, Any]:
    lemma, reading = key
    normalized_reading = normalize_reading_option(reading)
    if len(lemma) != 1 or not contains_kanji(lemma):
        return {
            "single_kanji": False,
            "kanjidic_on_match": False,
            "kanjidic_kun_match": False,
            "kanjidic_nanori_match": False,
            "kanjidic_known": False,
        }
    readings = kanjidic_readings.get(lemma)
    if not readings:
        return {
            "single_kanji": True,
            "kanjidic_on_match": False,
            "kanjidic_kun_match": False,
            "kanjidic_nanori_match": False,
            "kanjidic_known": False,
        }
    return {
        "single_kanji": True,
        "kanjidic_on_match": normalized_reading in readings.get("on", set()),
        "kanjidic_kun_match": normalized_reading in readings.get("kun", set()),
        "kanjidic_nanori_match": normalized_reading in readings.get("nanori", set()),
        "kanjidic_known": True,
    }


def component_likelihood_for_row(
    *,
    row: Mapping[str, str],
    audit: Mapping[str, Any],
    meta: Mapping[str, set[str]],
    reading_profile: Mapping[str, Any],
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    candidates: list[float] = []
    if truthy(reading_profile.get("kanjidic_on_match")):
        candidates.append(0.95)
        reasons.append("kanjidic_on")
    if has_component_pos(meta):
        candidates.append(0.90)
        reasons.append("jmdict_component_pos")
    if has_component_misc(meta):
        candidates.append(0.85)
        reasons.append("jmdict_component_misc")
    if is_nominalized_stem_surface(str(row.get("lemma") or "")):
        candidates.append(0.70)
        reasons.append("nominalized_stem_surface")

    exact_commonness = optional_float(row.get("exact_commonness")) or 0.0
    same_surface = optional_float(row.get("same_surface_risk")) or 0.0
    suspicion = optional_float(row.get("suspicion_full")) or 0.0
    mass = audit.get("frequency_mass", {})
    direct_log = float(mass.get("direct_log_combined_total") or 0.0)
    leak = float(mass.get("combined_log_leak_share") or 0.0)
    risk = float(audit.get("risk", {}).get("compound_component_risk") or 0.0)
    classification = str(audit.get("risk", {}).get("classification") or "")
    if exact_commonness < 0.15 and max(same_surface, suspicion) >= 0.70:
        candidates.append(0.95)
        reasons.append("weak_exact_same_surface")
    elif exact_commonness < 0.30 and max(same_surface, suspicion) >= 0.30:
        candidates.append(0.80)
        reasons.append("weak_exact_suspicious")
    if direct_log < 6.0 and leak >= 0.94:
        candidates.append(0.80)
        reasons.append("tiny_direct_mass")
    if classification == "high_confidence_compound_component":
        candidates.append(0.75)
        reasons.append("audit_high_confidence")
    elif classification == "medium_confidence_compound_component":
        candidates.append(0.60)
        reasons.append("audit_medium_confidence")
    if risk >= 0.60:
        candidates.append(0.55)
        reasons.append("high_audit_risk")
    return max(candidates or [0.20]), reasons or ["broad_residual"]


def strict_component_likelihood_for_row(
    *,
    row: Mapping[str, str],
    audit: Mapping[str, Any],
    meta: Mapping[str, set[str]],
    reading_profile: Mapping[str, Any],
) -> tuple[float, list[str]]:
    component, reasons = component_likelihood_for_row(
        row=row,
        audit=audit,
        meta=meta,
        reading_profile=reading_profile,
    )
    strict_reasons = [
        reason
        for reason in reasons
        if reason
        in {
            "kanjidic_on",
            "jmdict_component_pos",
            "jmdict_component_misc",
            "nominalized_stem_surface",
            "weak_exact_same_surface",
            "tiny_direct_mass",
            "audit_high_confidence",
        }
    ]
    if not strict_reasons:
        return 0.0, []
    return component, strict_reasons


def core_standalone_guard_for_row(
    *,
    row: Mapping[str, str],
    audit: Mapping[str, Any],
    meta: Mapping[str, set[str]],
    reading_profile: Mapping[str, Any],
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    guards: list[float] = []
    exact_commonness = optional_float(row.get("exact_commonness")) or 0.0
    mass = audit.get("frequency_mass", {})
    direct_log = float(mass.get("direct_log_combined_total") or 0.0)
    if truthy(reading_profile.get("kanjidic_kun_match")) and not truthy(
        reading_profile.get("kanjidic_on_match")
    ):
        guards.append(0.75)
        reasons.append("kanjidic_kun")
    if has_strong_exact_priority(meta):
        guards.append(0.70)
        reasons.append("strong_exact_priority")
    if truthy(row.get("jlpt_exact_known")) and exact_commonness >= 0.75:
        guards.append(0.80)
        reasons.append("exact_jlpt_common")
    if exact_commonness >= 0.90 and direct_log >= 16.0:
        guards.append(0.75)
        reasons.append("strong_exact_commonness")
    if direct_log >= 20.0 and has_strong_exact_priority(meta):
        guards.append(0.95)
        reasons.append("very_strong_direct_priority")
    guard = max(guards or [0.0])
    if truthy(reading_profile.get("kanjidic_on_match")) and (
        has_component_pos(meta) or has_component_misc(meta)
    ):
        guard *= 0.35
        reasons.append("on_component_discount")
    return clamp01(guard), reasons


def direct_standalone_guard_for_row(
    *,
    row: Mapping[str, str],
    audit: Mapping[str, Any],
    meta: Mapping[str, Any],
    mode: str,
) -> tuple[float, list[str]]:
    mass = audit.get("frequency_mass", {})
    direct_raw = float(mass.get("direct_raw_combined_total") or 0.0)
    direct_log = float(mass.get("direct_log_combined_total") or 0.0)
    exact_commonness = optional_float(row.get("exact_commonness")) or 0.0
    same_surface = optional_float(row.get("same_surface_risk")) or 0.0
    suspicion = optional_float(row.get("suspicion_full")) or 0.0
    if direct_raw < 30000.0 or direct_log < 17.5:
        return 0.0, []
    if exact_commonness < 0.85:
        return 0.0, []
    if not has_strong_exact_priority(meta):
        return 0.0, []
    if max(same_surface, suspicion) >= 0.70:
        return 0.0, []
    if has_exact_bad_misc(meta):
        return 0.0, []

    first_plain = first_sense_is_plain_common_noun(meta)
    has_plain = has_plain_common_noun_sense(meta)
    first_ordinary = first_sense_is_ordinary_common_noun(meta)
    has_ordinary = has_ordinary_common_noun_sense(meta)
    if mode == "plain_noun_direct":
        if first_plain:
            return 0.95, ["direct_high_first_plain_noun"]
        if has_plain and exact_commonness >= 0.95 and direct_raw >= 60000.0:
            return 0.90, ["direct_high_plain_noun"]
        return 0.0, []
    if mode == "ordinary_noun_direct":
        if first_plain:
            return 0.97, ["direct_high_first_plain_noun"]
        if first_ordinary and exact_commonness >= 0.95:
            return 0.92, ["direct_high_first_ordinary_noun"]
        if has_plain and exact_commonness >= 0.95:
            return 0.90, ["direct_high_plain_noun"]
        if has_ordinary and truthy(row.get("jlpt_exact_known")) and direct_raw >= 30000.0:
            return 0.82, ["direct_high_ordinary_jlpt_noun"]
        return 0.0, []
    raise ValueError(f"unknown direct standalone guard mode: {mode}")


def first_sense_values(meta: Mapping[str, Any], key: str) -> list[str]:
    senses = list(meta.get("senses") or [])
    if not senses:
        return []
    first = senses[0]
    if not isinstance(first, Mapping):
        return []
    return [str(value) for value in first.get(key, []) if str(value)]


def merge_reasons(*groups: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for reason in group:
            if reason not in merged:
                merged.append(reason)
    return merged


def has_plain_common_noun_sense(meta: Mapping[str, Any]) -> bool:
    return any(sense_is_plain_common_noun(sense) for sense in meta.get("senses", []))


def has_ordinary_common_noun_sense(meta: Mapping[str, Any]) -> bool:
    return any(sense_is_ordinary_common_noun(sense) for sense in meta.get("senses", []))


def first_sense_is_plain_common_noun(meta: Mapping[str, Any]) -> bool:
    senses = list(meta.get("senses") or [])
    return bool(senses and sense_is_plain_common_noun(senses[0]))


def first_sense_is_ordinary_common_noun(meta: Mapping[str, Any]) -> bool:
    senses = list(meta.get("senses") or [])
    return bool(senses and sense_is_ordinary_common_noun(senses[0]))


def sense_is_plain_common_noun(sense: object) -> bool:
    if not isinstance(sense, Mapping):
        return False
    pos = {str(value) for value in sense.get("pos", [])}
    misc = {str(value) for value in sense.get("misc", [])}
    return (
        has_common_noun_pos(pos)
        and not has_component_pos_values(pos)
        and not has_bad_misc_values(misc)
    )


def sense_is_ordinary_common_noun(sense: object) -> bool:
    if not isinstance(sense, Mapping):
        return False
    pos = {str(value) for value in sense.get("pos", [])}
    misc = {str(value) for value in sense.get("misc", [])}
    return has_common_noun_pos(pos) and not has_bad_misc_values(misc)


def has_common_noun_pos(pos_values: set[str]) -> bool:
    return any("noun (common)" in value.lower() for value in pos_values)


def has_component_pos_values(pos_values: set[str]) -> bool:
    pos_text = " ".join(sorted(pos_values)).lower()
    return any(
        needle in pos_text
        for needle in (
            "suffix",
            "prefix",
            "auxiliary",
            "counter",
        )
    )


def has_bad_misc_values(misc_values: set[str]) -> bool:
    misc_text = " ".join(sorted(misc_values)).lower()
    return any(
        needle in misc_text
        for needle in (
            "abbreviation",
            "dated",
            "historical",
            "archaic",
            "obsolete",
            "rare",
        )
    )


def has_exact_bad_misc(meta: Mapping[str, Any]) -> bool:
    return has_bad_misc_values({str(value) for value in meta.get("misc", set())})


def has_component_pos(meta: Mapping[str, set[str]]) -> bool:
    pos_text = " ".join(sorted(meta.get("pos", set()))).lower()
    return any(
        needle in pos_text
        for needle in (
            "suffix",
            "prefix",
            "auxiliary",
            "counter",
        )
    )


def has_component_misc(meta: Mapping[str, set[str]]) -> bool:
    misc_text = " ".join(sorted(meta.get("misc", set()))).lower()
    return any(
        needle in misc_text
        for needle in (
            "abbreviation",
            "dated",
            "historical",
            "archaic",
            "obsolete",
        )
    )


def has_strong_exact_priority(meta: Mapping[str, set[str]]) -> bool:
    for tag in sorted(meta.get("priority_tags", set())):
        if tag in {"ichi1", "news1"}:
            return True
        if tag.startswith("nf"):
            try:
                if int(tag[2:]) <= 10:
                    return True
            except ValueError:
                continue
    return False


def is_nominalized_stem_surface(lemma: str) -> bool:
    return contains_kanji(lemma) and len(lemma) <= 3 and lemma.endswith(("き", "ぎ", "ち", "り"))


def normalize_reading_option(value: object) -> str:
    normalized = normalize_kana(str(value or "").strip())
    return normalized.replace(".", "").replace("-", "")


def normalize_kana(value: str) -> str:
    chars = []
    for char in value:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def contains_kanji(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def reading_allowed_for_form(reading: Mapping[str, Any], form: str) -> bool:
    restrictions = {str(value) for value in reading.get("restrictions") or ()}
    return not restrictions or form in restrictions


def normalized_excess(value: float, threshold: float) -> float:
    if value <= threshold:
        return 0.0
    if threshold >= 1.0:
        return 0.0
    return clamp01((value - threshold) / (1.0 - threshold))


def morpheme_multiplier(lemma: str, reading: str) -> float:
    if len(lemma) == 1 and len(reading) <= 3:
        return 1.0
    if len(lemma) <= 2 and len(reading) <= 4:
        return 0.80
    return 0.55


def evaluate_score_map(
    scores: Mapping[tuple[str, str], float],
    *,
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    calibration_labels: Sequence[Mapping[str, Any]],
    holdout_labels: Sequence[Mapping[str, Any]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    changed_keys: set[tuple[str, str]],
    include_expensive: bool = True,
) -> dict[str, Any]:
    return {
        "calibration": evaluate_labels(
            calibration_labels,
            scores,
            rows_by_key,
            include_expensive=include_expensive,
        ),
        "holdout": evaluate_labels(
            holdout_labels,
            scores,
            rows_by_key,
            include_expensive=include_expensive,
        ),
        "manual_compoundish": manual_compoundish_metrics(audit_by_key, changed_keys),
        "change": change_metrics(changed_keys, rows_by_key, audit_by_key),
    }


def evaluate_labels(
    labels: Sequence[Mapping[str, Any]],
    scores: Mapping[tuple[str, str], float],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    *,
    include_expensive: bool = True,
) -> dict[str, Any]:
    rows = []
    for label in labels:
        key = label_key(label)
        if key not in scores:
            continue
        expected = optional_float(label.get("expected_learner_difficulty"))
        if expected is None:
            continue
        observed = scores[key]
        rows.append(
            {
                "label": f"{key[0]}/{key[1]}",
                "expected": expected,
                "observed": observed,
                "expected_band": str(label.get("expected_difficulty_band") or ""),
                "expected_candidate_state": str(label.get("expected_candidate_state") or ""),
                "observed_candidate_state": str(
                    rows_by_key.get(key, {}).get("candidate_state") or ""
                ),
            }
        )
    return metrics_for_rows(rows, include_expensive=include_expensive)


def metrics_for_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    include_expensive: bool = True,
) -> dict[str, Any]:
    errors = [abs(float(row["observed"]) - float(row["expected"])) for row in rows]
    bucket_rows = []
    for row in rows:
        expected_band = str(row.get("expected_band") or "") or coarse_band(float(row["expected"]))
        observed_band = coarse_band(float(row["observed"]))
        bucket_rows.append((expected_band, observed_band, row))
    bucket_matches = sum(1 for expected, observed, _row in bucket_rows if expected == observed)
    pairwise = pairwise_metrics(rows) if include_expensive else empty_pairwise_metrics()
    rank = rank_metrics(rows) if include_expensive else empty_rank_metrics(rows)
    segments = {
        "beginner_core": segment_metrics(
            rows,
            expected_max=BEGINNER_CORE_MAX,
            observed_ceiling=BEGINNER_CORE_OBSERVED_CEILING,
        ),
        "beginner_broad": segment_metrics(
            rows,
            expected_max=BEGINNER_BROAD_MAX,
            observed_ceiling=BEGINNER_BROAD_OBSERVED_CEILING,
        ),
        "upper_tail": segment_metrics(
            rows,
            expected_min=UPPER_TAIL_MIN,
            observed_floor=UPPER_TAIL_OBSERVED_FLOOR,
        ),
        "high_tail": segment_metrics(
            rows,
            expected_min=HIGH_TAIL_MIN,
            observed_floor=HIGH_TAIL_OBSERVED_FLOOR,
        ),
    }
    separation = tail_separation(rows)
    scores = score_summary(
        mae=mean(errors),
        bucket_accuracy=ratio(bucket_matches, len(bucket_rows)),
        pairwise_accuracy=pairwise["accuracy"],
        rank_spearman=rank["spearman"],
        beginner_core=segments["beginner_core"]["pass_rate"],
        beginner_broad=segments["beginner_broad"]["pass_rate"],
        upper_tail=segments["upper_tail"]["pass_rate"],
        high_tail=segments["high_tail"]["pass_rate"],
        tail_gap=separation["mean_gap"],
    )
    return {
        "evaluated_count": len(rows),
        "difficulty_value": {
            "mae": rounded(mean(errors)),
            "max_abs_error": rounded(max(errors) if errors else None),
        },
        "difficulty_bucket": {
            "evaluated_count": len(bucket_rows),
            "match_count": bucket_matches,
            "accuracy": rounded(ratio(bucket_matches, len(bucket_rows))),
        },
        "pairwise_order": pairwise,
        "rank_correlation": rank,
        "segments": segments,
        "separation": separation,
        "scores": scores,
    }


def pairwise_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    comparable = 0
    correct = 0
    ties = 0
    wrong = 0
    examples = []
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            expected_gap = float(right["expected"]) - float(left["expected"])
            if abs(expected_gap) < PAIRWISE_MIN_EXPECTED_GAP:
                continue
            comparable += 1
            observed_gap = float(right["observed"]) - float(left["observed"])
            if abs(observed_gap) <= PAIRWISE_TIE_TOLERANCE:
                ties += 1
            elif (expected_gap > 0 and observed_gap > 0) or (expected_gap < 0 and observed_gap < 0):
                correct += 1
            else:
                wrong += 1
                if len(examples) < 20:
                    easier = left if expected_gap > 0 else right
                    harder = right if expected_gap > 0 else left
                    examples.append(
                        {
                            "expected_easier": easier["label"],
                            "expected_harder": harder["label"],
                            "expected_gap": rounded(abs(expected_gap)),
                            "observed_gap": rounded(
                                float(harder["observed"]) - float(easier["observed"])
                            ),
                        }
                    )
    return {
        "comparable_count": comparable,
        "correct_count": correct,
        "tie_count": ties,
        "wrong_count": wrong,
        "accuracy": rounded(ratio(correct + (0.5 * ties), comparable)),
        "strict_accuracy": rounded(ratio(correct, comparable)),
        "wrong_examples": examples,
    }


def empty_pairwise_metrics() -> dict[str, Any]:
    return {
        "comparable_count": 0,
        "correct_count": 0,
        "tie_count": 0,
        "wrong_count": 0,
        "accuracy": None,
        "strict_accuracy": None,
        "wrong_examples": [],
    }


def rank_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = [float(row["expected"]) for row in rows]
    observed = [float(row["observed"]) for row in rows]
    return {
        "evaluated_count": len(rows),
        "spearman": rounded(pearson(ranks(expected), ranks(observed))),
        "pearson": rounded(pearson(expected, observed)),
    }


def empty_rank_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "evaluated_count": len(rows),
        "spearman": None,
        "pearson": None,
    }


def segment_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_min: float | None = None,
    expected_max: float | None = None,
    observed_floor: float | None = None,
    observed_ceiling: float | None = None,
) -> dict[str, Any]:
    selected = []
    for row in rows:
        expected = float(row["expected"])
        if expected_min is not None and expected < expected_min:
            continue
        if expected_max is not None and expected > expected_max:
            continue
        selected.append(row)
    passed = 0
    errors = []
    values = []
    for row in selected:
        observed = float(row["observed"])
        expected = float(row["expected"])
        values.append(observed)
        errors.append(abs(observed - expected))
        if observed_floor is not None and observed < observed_floor:
            continue
        if observed_ceiling is not None and observed > observed_ceiling:
            continue
        passed += 1
    return {
        "count": len(selected),
        "pass_count": passed,
        "pass_rate": rounded(ratio(passed, len(selected))),
        "mae": rounded(mean(errors)),
        "observed_min": rounded(min(values) if values else None),
        "observed_max": rounded(max(values) if values else None),
        "observed_avg": rounded(mean(values)),
    }


def tail_separation(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    beginner = [
        float(row["observed"]) for row in rows if float(row["expected"]) <= BEGINNER_CORE_MAX
    ]
    high_tail = [float(row["observed"]) for row in rows if float(row["expected"]) >= HIGH_TAIL_MIN]
    beginner_avg = mean(beginner)
    high_tail_avg = mean(high_tail)
    mean_gap = (
        high_tail_avg - beginner_avg
        if high_tail_avg is not None and beginner_avg is not None
        else None
    )
    return {
        "beginner_count": len(beginner),
        "high_tail_count": len(high_tail),
        "beginner_observed_avg": rounded(beginner_avg),
        "high_tail_observed_avg": rounded(high_tail_avg),
        "mean_gap": rounded(mean_gap),
    }


def score_summary(
    *,
    mae: float | None,
    bucket_accuracy: float | None,
    pairwise_accuracy: float | None,
    rank_spearman: float | None,
    beginner_core: float | None,
    beginner_broad: float | None,
    upper_tail: float | None,
    high_tail: float | None,
    tail_gap: float | None,
) -> dict[str, Any]:
    rank_score = (rank_spearman + 1.0) / 2.0 if rank_spearman is not None else None
    tail_score = min(1.0, max(0.0, tail_gap / 0.70)) if tail_gap is not None else None
    scores = {
        "numeric_mae_score": rounded(1.0 - mae if mae is not None else None),
        "bucket_accuracy_score": rounded(bucket_accuracy),
        "pairwise_order_score": rounded(pairwise_accuracy),
        "rank_correlation_score": rounded(rank_score),
        "beginner_core_score": rounded(beginner_core),
        "beginner_broad_score": rounded(beginner_broad),
        "upper_tail_score": rounded(upper_tail),
        "high_tail_score": rounded(high_tail),
        "tail_separation_score": rounded(tail_score),
    }
    scores["balanced_score"] = rounded(
        weighted_average(
            (
                (scores["numeric_mae_score"], 0.16),
                (scores["bucket_accuracy_score"], 0.12),
                (scores["pairwise_order_score"], 0.20),
                (scores["rank_correlation_score"], 0.10),
                (scores["beginner_core_score"], 0.12),
                (scores["beginner_broad_score"], 0.08),
                (scores["upper_tail_score"], 0.10),
                (scores["high_tail_score"], 0.06),
                (scores["tail_separation_score"], 0.03),
            )
        )
    )
    return scores


def manual_compoundish_metrics(
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    changed_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    positives = {
        key for key, row in audit_by_key.items() if row["manual"]["compoundish_manual_correction"]
    }
    hits = positives & changed_keys
    return {
        "positive_count": len(positives),
        "changed_count": len(changed_keys),
        "hit_count": len(hits),
        "recall": rounded(ratio(len(hits), len(positives))),
        "precision": rounded(ratio(len(hits), len(changed_keys))),
        "changed_f1": rounded(
            f1(ratio(len(hits), len(changed_keys)), ratio(len(hits), len(positives)))
        ),
    }


def change_metrics(
    changed_keys: set[tuple[str, str]],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    manual = sum(
        1
        for key in changed_keys
        if str(rows_by_key.get(key, {}).get("manual_correction_active") or "") == "yes"
    )
    strong_pressure = sum(
        1
        for key in changed_keys
        if float(audit_by_key.get(key, {}).get("risk", {}).get("compound_component_risk") or 0.0)
        >= 0.40
    )
    return {
        "changed_count": len(changed_keys),
        "manual_correction_changed_count": manual,
        "strong_pressure_changed_count": strong_pressure,
    }


def selection_score(metrics: Mapping[str, Any], baseline: Mapping[str, Any]) -> float:
    holdout = float(metrics["holdout"]["scores"].get("balanced_score") or 0.0)
    calibration = float(metrics["calibration"]["scores"].get("balanced_score") or 0.0)
    manual_f1 = float(metrics["manual_compoundish"].get("changed_f1") or 0.0)
    manual_recall = float(metrics["manual_compoundish"].get("recall") or 0.0)
    changed = float(metrics["change"].get("changed_count") or 0.0)
    baseline_holdout = float(baseline["holdout"]["scores"].get("balanced_score") or 0.0)
    holdout_delta = holdout - baseline_holdout
    return (
        rounded(
            holdout
            + (0.20 * max(-0.05, holdout_delta))
            + (0.10 * manual_f1)
            + (0.03 * manual_recall)
            + (0.03 * calibration)
            - (0.02 * min(1.0, changed / 500.0))
        )
        or 0.0
    )


def changed_preview(
    *,
    variant: SweepVariant,
    changed_keys: set[tuple[str, str]],
    base_scores: Mapping[tuple[str, str], float],
    candidate_scores: Mapping[tuple[str, str], float],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    row_contexts: Mapping[tuple[str, str], Mapping[str, Any]],
    pressure_by_key: Mapping[tuple[str, str], float],
    limit: int,
) -> list[dict[str, Any]]:
    rows = []
    for key in changed_keys:
        audit = audit_by_key.get(key, {})
        mass = audit.get("frequency_mass", {})
        row = rows_by_key.get(key, {})
        context = row_contexts.get(key, {})
        guard_key = f"core_standalone_guard_{variant.standalone_guard_mode}"
        guard_reasons_key = f"core_guard_reasons_{variant.standalone_guard_mode}"
        rows.append(
            {
                "lemma": key[0],
                "reading": key[1],
                "base_score": rounded(base_scores[key]),
                "candidate_score": rounded(candidate_scores[key]),
                "delta": rounded(candidate_scores[key] - base_scores[key]),
                "pressure": rounded(pressure_by_key.get(key)),
                "compound_leak": rounded(mass.get("combined_log_leak_share")),
                "direct_mass": rounded(mass.get("direct_log_combined_total")),
                "compound_mass": rounded(mass.get("compound_log_combined_total")),
                "manual_correction_active": str(row.get("manual_correction_active") or "") == "yes",
                "manual_correction_types": str(row.get("correction_types") or ""),
                "manual_admission_override": str(row.get("admission_override") or ""),
                "component_likelihood": rounded(context.get("component_likelihood")),
                "strict_component_likelihood": rounded(context.get("strict_component_likelihood")),
                "core_standalone_guard": rounded(context.get(guard_key)),
                "component_reasons": list(context.get("component_reasons") or []),
                "core_guard_reasons": list(context.get(guard_reasons_key) or []),
                "standalone_guard_mode": variant.standalone_guard_mode,
                "kanjidic_on_match": bool(context.get("kanjidic_on_match")),
                "kanjidic_kun_match": bool(context.get("kanjidic_kun_match")),
                "jmdict_exact_pos": list(context.get("jmdict_exact_pos") or []),
                "jmdict_exact_misc": list(context.get("jmdict_exact_misc") or []),
                "examples": [
                    f"{item.get('surface')}/{item.get('reading')}"
                    for item in (mass.get("compound_mass_examples") or [])[:5]
                ],
            }
        )
    rows.sort(key=lambda row: (-float(row["delta"] or 0.0), -float(row["pressure"] or 0.0)))
    return rows[:limit]


def corrected_changed_keys(
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
) -> set[tuple[str, str]]:
    return {
        key
        for key, row in rows_by_key.items()
        if abs(
            (optional_float(row.get("score")) or 0.0)
            - (optional_float(row.get("model_score")) or 0.0)
        )
        >= 0.01
    }


def load_ranking_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_numeric_labels(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    labels = []
    for row in data.get("labels", []):
        if optional_float(row.get("expected_learner_difficulty")) is None:
            continue
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        if not reading:
            continue
        labels.append({**row, "reading": reading})
    return labels


def label_key(label: Mapping[str, Any]) -> tuple[str, str]:
    return str(label.get("lemma") or ""), str(label.get("reading") or "")


def coarse_band(value: float) -> str:
    if value < 0.55:
        return "beginner"
    if value < 0.80:
        return "intermediate"
    return "advanced"


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# en-ja Compound Leak Sweep",
        "",
        "This is a sidecar sweep only. It does not change runtime scores or admission.",
        "",
        "## Inputs",
        "",
        f"- Ranking rows: `{report['inputs']['ranking_row_count']}`",
        f"- Audit rows: `{report['inputs']['audit_row_count']}`",
        f"- Calibration numeric labels: `{report['inputs']['calibration_numeric_label_count']}`",
        f"- Holdout numeric labels: `{report['inputs']['holdout_numeric_label_count']}`",
        f"- Variants: `{report['inputs']['variant_count']}`",
        "",
        "## Baselines",
        "",
        baseline_table(report["baselines"]),
        "",
        "## Leaderboard",
        "",
        leaderboard_table(report["leaderboard"][:20]),
        "",
        "## Best Preview",
        "",
        preview_table(report["leaderboard"][0]["changed_preview"] if report["leaderboard"] else []),
        "",
        "## Notes",
        "",
        "- `model_score` is the pre-manual-correction baseline.",
        "- `current_corrected_score` is the existing corrected ranking reference.",
        "- The sweep ranks variants by holdout balanced score, manual compoundish F1, recall, and changed-row compactness.",
        "- `scopebroad` variants reproduce the earlier broad score-lift shape. `scopecomponent*` variants use KANJIDIC2/JMDict context to focus on component-like readings.",
        "- This tests score-lift behavior only; admission restriction can be derived later from the same pressure signal.",
        "",
    ]
    return "\n".join(lines)


def baseline_table(baselines: Mapping[str, Any]) -> str:
    lines = [
        "| Baseline | Cal bal | Cal MAE | Hold bal | Hold MAE | Manual recall | Changed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, metrics in baselines.items():
        lines.append(
            "| "
            f"`{escape(name)}` | "
            f"{fmt(metrics['calibration']['scores'].get('balanced_score'))} | "
            f"{fmt(metrics['calibration']['difficulty_value'].get('mae'))} | "
            f"{fmt(metrics['holdout']['scores'].get('balanced_score'))} | "
            f"{fmt(metrics['holdout']['difficulty_value'].get('mae'))} | "
            f"{fmt(metrics['manual_compoundish'].get('recall'))} | "
            f"{fmt(metrics['change'].get('changed_count'))} |"
        )
    return "\n".join(lines)


def leaderboard_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| # | Variant | Scope | Select | Cal bal | Hold bal | Hold MAE | Manual R/P/F1 | Changed |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(rows, start=1):
        metrics = row["metrics"]
        manual = metrics["manual_compoundish"]
        variant = row["variant"]
        lines.append(
            "| "
            f"{index} | "
            f"`{escape(variant['variant_id'])}` | "
            f"`{escape(variant.get('scope_mode'))}` | "
            f"{fmt(row.get('selection_score'))} | "
            f"{fmt(metrics['calibration']['scores'].get('balanced_score'))} | "
            f"{fmt(metrics['holdout']['scores'].get('balanced_score'))} | "
            f"{fmt(metrics['holdout']['difficulty_value'].get('mae'))} | "
            f"{fmt(manual.get('recall'))}/{fmt(manual.get('precision'))}/{fmt(manual.get('changed_f1'))} | "
            f"{fmt(metrics['change'].get('changed_count'))} |"
        )
    return "\n".join(lines)


def preview_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| Row | Base | New | Delta | Pressure | Leak | Component/Core | Manual | Examples |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        manual = ",".join(
            item
            for item in [
                str(row.get("manual_correction_types") or ""),
                str(row.get("manual_admission_override") or ""),
            ]
            if item
        )
        examples = ", ".join(str(item) for item in row.get("examples") or [])
        context = (
            f"c={fmt(row.get('component_likelihood'))}; "
            f"strict={fmt(row.get('strict_component_likelihood'))}; "
            f"core={fmt(row.get('core_standalone_guard'))}; "
            f"guard_mode={row.get('standalone_guard_mode')}; "
            f"on={row.get('kanjidic_on_match')}; kun={row.get('kanjidic_kun_match')}; "
            f"{','.join(str(item) for item in row.get('component_reasons') or [])}; "
            f"guard={','.join(str(item) for item in row.get('core_guard_reasons') or [])}"
        )
        lines.append(
            "| "
            f"`{escape(row['lemma'])}/{escape(row['reading'])}` | "
            f"{fmt(row.get('base_score'))} | "
            f"{fmt(row.get('candidate_score'))} | "
            f"{fmt(row.get('delta'))} | "
            f"{fmt(row.get('pressure'))} | "
            f"{fmt(row.get('compound_leak'))} | "
            f"{escape(context)} | "
            f"{escape(manual)} | "
            f"{escape(examples)} |"
        )
    return "\n".join(lines)


def variant_to_dict(variant: SweepVariant) -> dict[str, Any]:
    return {
        "variant_id": variant.variant_id,
        "leak_source": variant.leak_source,
        "leak_threshold": variant.leak_threshold,
        "leak_power": variant.leak_power,
        "mass_scale": variant.mass_scale,
        "surface_len_cap": variant.surface_len_cap,
        "destination": variant.destination,
        "strength": variant.strength,
        "max_shift": variant.max_shift,
        "jlpt_protection": variant.jlpt_protection,
        "exact_priority_protection": variant.exact_priority_protection,
        "direct_support_protection": variant.direct_support_protection,
        "scope_mode": variant.scope_mode,
        "core_guard_strength": variant.core_guard_strength,
        "standalone_guard_mode": variant.standalone_guard_mode,
    }


def metric_value(row: Mapping[str, Any], section: str, key: str) -> float:
    value = row["metrics"][section].get(key)
    if value is None and section in {"calibration", "holdout"}:
        value = row["metrics"][section]["scores"].get(key)
    return float(value or 0.0)


def optional_float(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip()
        return float(text) if text else None
    except ValueError:
        return None


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2 * precision * recall / (precision + recall)


def weighted_average(items: Sequence[tuple[object, float]]) -> float | None:
    total = 0.0
    weight_total = 0.0
    for value, weight in items:
        number = optional_float(value)
        if number is None:
            continue
        total += number * weight
        weight_total += weight
    if weight_total <= 0:
        return None
    return total / weight_total


def ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average = (index + end - 1) / 2.0
        for position in range(index, end):
            result[indexed[position][0]] = average
        index = end
    return result


def pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    left_den = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    right_den = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    if left_den <= 0 or right_den <= 0:
        return None
    return numerator / (left_den * right_den)


def rounded(value: object) -> float | None:
    number = optional_float(value)
    return round(number, 6) if number is not None else None


def fmt(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return ""
    if abs(number) >= 10:
        return str(int(number)) if float(number).is_integer() else f"{number:.2f}"
    return f"{number:.6f}".rstrip("0").rstrip(".")


def escape(value: object) -> str:
    return str(value).replace("|", "\\|")


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
