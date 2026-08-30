#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from srs_learner_difficulty_compound_leak_sweep_en_ja import (
    DEFAULT_AUDIT_JSON,
    DEFAULT_JMDICT,
    DEFAULT_KANJIDIC2,
    DEFAULT_RANKING_CSV,
    PROJECT_ROOT,
    ScoreOverlay,
    SweepVariant,
    apply_variant,
    build_row_contexts,
    evaluate_score_map,
    load_numeric_labels,
    optional_float,
    repo_path,
    rounded,
)


DEFAULT_GUARD_PROBE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_compound_leak_guard_probe_en_ja_latest.json"
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
    / "srs_learner_difficulty_compound_leak_candidate_review_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_compound_leak_candidate_review_en_ja_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a review pack for the best guarded en-ja compound-leak "
            "candidate. This does not change the canonical ranking."
        )
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--guard-probe-json", type=Path, default=DEFAULT_GUARD_PROBE_JSON)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--kanjidic2", type=Path, default=DEFAULT_KANJIDIC2)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        ranking_csv=_resolve_path(args.ranking_csv),
        audit_json=_resolve_path(args.audit_json),
        guard_probe_json=_resolve_path(args.guard_probe_json),
        jmdict_path=_resolve_path(args.jmdict),
        kanjidic2_path=_resolve_path(args.kanjidic2),
        calibration_json=_resolve_path(args.calibration_json),
        holdout_json=_resolve_path(args.holdout_json),
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
    guard_probe_json: Path,
    jmdict_path: Path,
    kanjidic2_path: Path,
    calibration_json: Path,
    holdout_json: Path,
) -> dict[str, Any]:
    ranking_rows = load_ranking_rows(ranking_csv)
    rows_by_key = {(row["lemma"], row["reading"]): row for row in ranking_rows}
    audit = json.loads(audit_json.read_text(encoding="utf-8"))
    audit_by_key = {(row["lemma"], row["reading"]): row for row in audit["rows"]}
    guard_probe = json.loads(guard_probe_json.read_text(encoding="utf-8"))
    selected_variant = SweepVariant(**guard_probe["leaderboard"][0]["variant"])
    legacy_variant = SweepVariant(
        **{
            **guard_probe["leaderboard"][0]["variant"],
            "variant_id": "legacy_comparison_for_guarded_candidate",
            "standalone_guard_mode": "legacy",
        }
    )
    row_contexts = build_row_contexts(
        rows_by_key=rows_by_key,
        audit_by_key=audit_by_key,
        jmdict_path=jmdict_path,
        kanjidic2_path=kanjidic2_path,
    )
    base_scores = {
        key: optional_float(row.get("model_score")) or optional_float(row.get("score")) or 1.0
        for key, row in rows_by_key.items()
    }
    selected_overrides, selected_pressure = apply_variant(
        selected_variant,
        base_scores=base_scores,
        rows_by_key=rows_by_key,
        audit_by_key=audit_by_key,
        row_contexts=row_contexts,
    )
    legacy_overrides, legacy_pressure = apply_variant(
        legacy_variant,
        base_scores=base_scores,
        rows_by_key=rows_by_key,
        audit_by_key=audit_by_key,
        row_contexts=row_contexts,
    )
    selected_scores = ScoreOverlay(base_scores, selected_overrides)
    calibration_labels = load_numeric_labels(calibration_json)
    holdout_labels = load_numeric_labels(holdout_json)
    metrics = evaluate_score_map(
        selected_scores,
        rows_by_key=rows_by_key,
        calibration_labels=calibration_labels,
        holdout_labels=holdout_labels,
        audit_by_key=audit_by_key,
        changed_keys=set(selected_overrides),
        include_expensive=True,
    )
    rows = [
        classify_changed_row(
            key=key,
            base_scores=base_scores,
            selected_overrides=selected_overrides,
            selected_pressure=selected_pressure,
            rows_by_key=rows_by_key,
            audit_by_key=audit_by_key,
            row_contexts=row_contexts,
            variant=selected_variant,
        )
        for key in sorted(
            selected_overrides,
            key=lambda item: selected_overrides[item] - base_scores[item],
            reverse=True,
        )
    ]
    protected_rows = [
        protected_row(
            key=key,
            base_scores=base_scores,
            legacy_overrides=legacy_overrides,
            legacy_pressure=legacy_pressure,
            rows_by_key=rows_by_key,
            audit_by_key=audit_by_key,
            row_contexts=row_contexts,
            variant=selected_variant,
        )
        for key in sorted(set(legacy_overrides) - set(selected_overrides))
    ]
    manual_positive_keys = {
        key for key, row in audit_by_key.items() if row["manual"]["compoundish_manual_correction"]
    }
    manual_misses = [
        manual_miss_row(key, rows_by_key=rows_by_key, audit_by_key=audit_by_key)
        for key in sorted(manual_positive_keys - set(selected_overrides))
    ]
    groups = group_rows(rows)
    return {
        "schema_version": 1,
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "scores_changed": False,
        "purpose": (
            "Review pack for guarded compound-leak candidates. Proposed actions "
            "are not applied to canonical ranking or manual corrections."
        ),
        "inputs": {
            "ranking_csv": repo_path(ranking_csv),
            "audit_json": repo_path(audit_json),
            "guard_probe_json": repo_path(guard_probe_json),
            "jmdict": str(jmdict_path),
            "kanjidic2": str(kanjidic2_path),
            "calibration_json": repo_path(calibration_json),
            "holdout_json": repo_path(holdout_json),
        },
        "selected_variant": guard_probe["leaderboard"][0]["variant"],
        "metrics": metrics,
        "summary": {
            "changed_count": len(rows),
            "already_manual_count": len(groups["already_manual_confirmed"]),
            "safe_auto_restrict_count": len(groups["safe_auto_restrict"]),
            "score_lift_candidate_count": len(groups["score_lift_candidate"]),
            "review_only_count": len(groups["review_only"]),
            "protected_by_guard_count": len(protected_rows),
            "manual_miss_count": len(manual_misses),
        },
        "groups": groups,
        "protected_by_guard": protected_rows,
        "manual_misses": manual_misses,
    }


def classify_changed_row(
    *,
    key: tuple[str, str],
    base_scores: Mapping[tuple[str, str], float],
    selected_overrides: Mapping[tuple[str, str], float],
    selected_pressure: Mapping[tuple[str, str], float],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    row_contexts: Mapping[tuple[str, str], Mapping[str, Any]],
    variant: SweepVariant,
) -> dict[str, Any]:
    row = rows_by_key.get(key, {})
    audit = audit_by_key.get(key, {})
    context = row_contexts.get(key, {})
    base = float(base_scores[key])
    candidate = float(selected_overrides[key])
    manual_active = str(row.get("manual_correction_active") or "") == "yes"
    current_types = split_types(str(row.get("correction_types") or ""))
    current_admission = str(row.get("admission_override") or "")
    guard_reasons = context_reasons(context, variant)
    component_reasons = list(
        context.get("strict_component_reasons") or context.get("component_reasons") or []
    )
    proposed_group = proposed_action_group(
        row=row,
        audit=audit,
        context=context,
        manual_active=manual_active,
        current_types=current_types,
        component_reasons=component_reasons,
        guard_reasons=guard_reasons,
        delta=candidate - base,
    )
    return {
        "lemma": key[0],
        "reading": key[1],
        "group": proposed_group,
        "proposed_action": proposed_action_for_group(proposed_group, row, current_types),
        "base_score": rounded(base),
        "candidate_score": rounded(candidate),
        "delta": rounded(candidate - base),
        "pressure": rounded(selected_pressure.get(key)),
        "rank": optional_int(row.get("rank")),
        "manual_correction_active": manual_active,
        "current_correction_types": current_types,
        "current_admission_override": current_admission,
        "compound_leak": rounded(audit.get("frequency_mass", {}).get("combined_log_leak_share")),
        "direct_raw": rounded(audit.get("frequency_mass", {}).get("direct_raw_combined_total")),
        "compound_raw": rounded(audit.get("frequency_mass", {}).get("compound_raw_combined_total")),
        "component_likelihood": rounded(context.get("strict_component_likelihood")),
        "core_guard": rounded(
            context.get(f"core_standalone_guard_{variant.standalone_guard_mode}")
        ),
        "component_reasons": component_reasons,
        "guard_reasons": guard_reasons,
        "jmdict_first_sense_pos": list(context.get("jmdict_exact_first_sense_pos") or []),
        "jmdict_first_sense_misc": list(context.get("jmdict_exact_first_sense_misc") or []),
        "kanjidic_on_match": bool(context.get("kanjidic_on_match")),
        "kanjidic_kun_match": bool(context.get("kanjidic_kun_match")),
        "examples": compound_examples(audit),
    }


def proposed_action_group(
    *,
    row: Mapping[str, str],
    audit: Mapping[str, Any],
    context: Mapping[str, Any],
    manual_active: bool,
    current_types: Sequence[str],
    component_reasons: Sequence[str],
    guard_reasons: Sequence[str],
    delta: float,
) -> str:
    if manual_active or current_types:
        return "already_manual_confirmed"
    if float(context.get("core_standalone_guard_ordinary_noun_direct") or 0.0) >= 0.75:
        return "review_only"
    direct_raw = float(audit.get("frequency_mass", {}).get("direct_raw_combined_total") or 0.0)
    leak = float(audit.get("frequency_mass", {}).get("combined_log_leak_share") or 0.0)
    risk = float(audit.get("risk", {}).get("compound_component_risk") or 0.0)
    exact_commonness = optional_float(row.get("exact_commonness")) or 0.0
    high_component = any(
        reason in component_reasons
        for reason in (
            "tiny_direct_mass",
            "weak_exact_same_surface",
            "weak_exact_suspicious",
            "jmdict_component_misc",
            "audit_high_confidence",
            "kanjidic_on",
        )
    )
    weak_standalone = (
        direct_raw < 5000.0
        or exact_commonness < 0.15
        or "tiny_direct_mass" in component_reasons
        or "weak_exact_same_surface" in component_reasons
    )
    if high_component and weak_standalone and leak >= 0.94:
        return "safe_auto_restrict"
    if risk >= 0.60 and leak >= 0.97 and not guard_reasons:
        return "safe_auto_restrict"
    if delta >= 0.03 and high_component:
        return "score_lift_candidate"
    return "review_only"


def proposed_action_for_group(
    group: str,
    row: Mapping[str, str],
    current_types: Sequence[str],
) -> str:
    if group == "already_manual_confirmed":
        current = ",".join(current_types) or str(row.get("admission_override") or "manual")
        return f"keep_existing_manual:{current}"
    if group == "safe_auto_restrict":
        return "propose_restricted_admission_no_canonical_score_change_yet"
    if group == "score_lift_candidate":
        return "review_for_restricted_admission_and_optional_score_floor"
    return "review_only_no_auto_action"


def protected_row(
    *,
    key: tuple[str, str],
    base_scores: Mapping[tuple[str, str], float],
    legacy_overrides: Mapping[tuple[str, str], float],
    legacy_pressure: Mapping[tuple[str, str], float],
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    row_contexts: Mapping[tuple[str, str], Mapping[str, Any]],
    variant: SweepVariant,
) -> dict[str, Any]:
    row = rows_by_key.get(key, {})
    audit = audit_by_key.get(key, {})
    context = row_contexts.get(key, {})
    base = float(base_scores[key])
    legacy_candidate = float(legacy_overrides[key])
    return {
        "lemma": key[0],
        "reading": key[1],
        "base_score": rounded(base),
        "legacy_candidate_score": rounded(legacy_candidate),
        "legacy_delta": rounded(legacy_candidate - base),
        "legacy_pressure": rounded(legacy_pressure.get(key)),
        "rank": optional_int(row.get("rank")),
        "recommended_action": "keep_due_to_standalone_evidence",
        "direct_raw": rounded(audit.get("frequency_mass", {}).get("direct_raw_combined_total")),
        "compound_raw": rounded(audit.get("frequency_mass", {}).get("compound_raw_combined_total")),
        "compound_leak": rounded(audit.get("frequency_mass", {}).get("combined_log_leak_share")),
        "core_guard": rounded(
            context.get(f"core_standalone_guard_{variant.standalone_guard_mode}")
        ),
        "guard_reasons": context_reasons(context, variant),
        "component_reasons": list(
            context.get("strict_component_reasons") or context.get("component_reasons") or []
        ),
        "jmdict_first_sense_pos": list(context.get("jmdict_exact_first_sense_pos") or []),
        "jmdict_first_sense_misc": list(context.get("jmdict_exact_first_sense_misc") or []),
        "examples": compound_examples(audit),
    }


def manual_miss_row(
    key: tuple[str, str],
    *,
    rows_by_key: Mapping[tuple[str, str], Mapping[str, str]],
    audit_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    row = rows_by_key.get(key, {})
    audit = audit_by_key.get(key, {})
    return {
        "lemma": key[0],
        "reading": key[1],
        "score": rounded(row.get("score")),
        "model_score": rounded(row.get("model_score")),
        "correction_types": split_types(str(row.get("correction_types") or "")),
        "admission_override": str(row.get("admission_override") or ""),
        "compound_leak": rounded(audit.get("frequency_mass", {}).get("combined_log_leak_share")),
        "direct_raw": rounded(audit.get("frequency_mass", {}).get("direct_raw_combined_total")),
        "reason_not_caught": "not enough guarded compound-leak pressure; likely needs separate lexical/admission rule",
        "examples": compound_examples(audit),
    }


def group_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "already_manual_confirmed": [],
        "safe_auto_restrict": [],
        "score_lift_candidate": [],
        "review_only": [],
    }
    for row in rows:
        groups[str(row["group"])].append(dict(row))
    return groups


def render_markdown(report: Mapping[str, Any]) -> str:
    variant = report["selected_variant"]
    metrics = report["metrics"]
    summary = report["summary"]
    lines = [
        "# en-ja Compound Leak Candidate Review",
        "",
        "This is a sidecar review pack only. It does not change canonical ranking, manual corrections, admission, or runtime behavior.",
        "",
        "## Selected Variant",
        "",
        f"- Variant: `{variant['variant_id']}`",
        f"- Scope: `{variant['scope_mode']}`",
        f"- Standalone guard: `{variant['standalone_guard_mode']}`",
        f"- Leak threshold/power: `{variant['leak_threshold']}` / `{variant['leak_power']}`",
        "",
        "## Summary",
        "",
        f"- Changed rows under candidate: `{summary['changed_count']}`",
        f"- Already-manual confirmations: `{summary['already_manual_count']}`",
        f"- Safe auto-restrict candidates: `{summary['safe_auto_restrict_count']}`",
        f"- Score-lift/restriction review candidates: `{summary['score_lift_candidate_count']}`",
        f"- Review-only candidates: `{summary['review_only_count']}`",
        f"- Rows protected by standalone guard vs legacy behavior: `{summary['protected_by_guard_count']}`",
        f"- Existing manual compoundish misses: `{summary['manual_miss_count']}`",
        "",
        "## Metrics",
        "",
        "| Split | Balanced | MAE |",
        "| --- | ---: | ---: |",
        f"| Calibration | {fmt(metrics['calibration']['scores'].get('balanced_score'))} | {fmt(metrics['calibration']['difficulty_value'].get('mae'))} |",
        f"| Holdout | {fmt(metrics['holdout']['scores'].get('balanced_score'))} | {fmt(metrics['holdout']['difficulty_value'].get('mae'))} |",
        "",
        "## Safe Auto-Restrict Candidates",
        "",
        row_table(report["groups"]["safe_auto_restrict"][:80]),
        "",
        "## Score-Lift / Restriction Review Candidates",
        "",
        row_table(report["groups"]["score_lift_candidate"][:80]),
        "",
        "## Review-Only Candidates",
        "",
        row_table(report["groups"]["review_only"][:80]),
        "",
        "## Already-Manual Confirmations",
        "",
        row_table(report["groups"]["already_manual_confirmed"][:80]),
        "",
        "## Protected By Standalone Guard",
        "",
        protected_table(report["protected_by_guard"][:80]),
        "",
        "## Manual Misses",
        "",
        manual_miss_table(report["manual_misses"]),
        "",
        "## Interpretation",
        "",
        "- `safe_auto_restrict` means the signal looks strong enough to propose restricted admission, but this pack still does not apply it.",
        "- `score_lift_candidate` means the row has real component pressure but needs product review before any score floor or admission change.",
        "- `protected_by_guard` are rows the older component-leak shape would have moved, but the standalone guard now keeps.",
        "- Existing manual misses are a reminder that compound leak is not meant to solve every awkward standalone-admission case.",
        "",
    ]
    return "\n".join(lines)


def row_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| Row | Base -> Candidate | Delta | Direct/Cx | Leak | Action | Reasons | Examples |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        reasons = ",".join(str(item) for item in row.get("component_reasons") or [])
        guard = ",".join(str(item) for item in row.get("guard_reasons") or [])
        examples = ", ".join(str(item) for item in row.get("examples") or [])
        lines.append(
            "| "
            f"`{escape(row['lemma'])}/{escape(row['reading'])}` | "
            f"{fmt(row.get('base_score'))} -> {fmt(row.get('candidate_score'))} | "
            f"{fmt(row.get('delta'))} | "
            f"{fmt(row.get('direct_raw'))}/{fmt(row.get('compound_raw'))} | "
            f"{fmt(row.get('compound_leak'))} | "
            f"`{escape(row.get('proposed_action'))}` | "
            f"{escape(reasons)}; guard={escape(guard)} | "
            f"{escape(examples)} |"
        )
    return "\n".join(lines)


def protected_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| Row | Base | Legacy delta | Direct/Cx | Leak | Guard | Reasons | Examples |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        reasons = ",".join(str(item) for item in row.get("guard_reasons") or [])
        examples = ", ".join(str(item) for item in row.get("examples") or [])
        lines.append(
            "| "
            f"`{escape(row['lemma'])}/{escape(row['reading'])}` | "
            f"{fmt(row.get('base_score'))} | "
            f"{fmt(row.get('legacy_delta'))} | "
            f"{fmt(row.get('direct_raw'))}/{fmt(row.get('compound_raw'))} | "
            f"{fmt(row.get('compound_leak'))} | "
            f"{fmt(row.get('core_guard'))} | "
            f"{escape(reasons)} | "
            f"{escape(examples)} |"
        )
    return "\n".join(lines)


def manual_miss_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| Row | Score | Manual Types | Admission | Direct/Cx | Leak | Note |",
        "| --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{escape(row['lemma'])}/{escape(row['reading'])}` | "
            f"{fmt(row.get('score'))} | "
            f"{escape(','.join(row.get('correction_types') or []))} | "
            f"{escape(row.get('admission_override'))} | "
            f"{fmt(row.get('direct_raw'))}/{fmt(row.get('compound_raw'))} | "
            f"{fmt(row.get('compound_leak'))} | "
            f"{escape(row.get('reason_not_caught'))} |"
        )
    return "\n".join(lines)


def context_reasons(context: Mapping[str, Any], variant: SweepVariant) -> list[str]:
    return list(context.get(f"core_guard_reasons_{variant.standalone_guard_mode}") or [])


def compound_examples(audit: Mapping[str, Any]) -> list[str]:
    return [
        f"{item.get('surface')}/{item.get('reading')}"
        for item in (audit.get("frequency_mass", {}).get("compound_mass_examples") or [])[:5]
    ]


def load_ranking_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def split_types(value: str) -> list[str]:
    return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]


def optional_int(value: object) -> int | None:
    try:
        text = str(value if value is not None else "").strip()
        return int(float(text)) if text else None
    except ValueError:
        return None


def fmt(value: object) -> str:
    maybe = optional_float(value)
    if maybe is None:
        return ""
    return f"{maybe:.6g}"


def escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
