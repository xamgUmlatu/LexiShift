#!/usr/bin/env python3
"""Build a focused review pack for cross-corpus rescue regressions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_BEFORE_AFTER_JSON = Path(
    "docs/test_outputs/"
    "srs_learner_difficulty_cross_corpus_typed_rescue_before_after_en_ja_latest.json"
)
DEFAULT_JSON_OUT = Path(
    "docs/test_outputs/"
    "srs_learner_difficulty_cross_corpus_typed_rescue_failure_diagnostics_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = Path(
    "docs/test_outputs/"
    "srs_learner_difficulty_cross_corpus_typed_rescue_failure_diagnostics_en_ja_latest.md"
)
DEFAULT_LABEL_JSONS = (
    (
        "calibration",
        Path("docs/test_inputs/srs_learner_difficulty_calibration_en_ja.json"),
    ),
    (
        "holdout",
        Path("docs/test_inputs/srs_learner_difficulty_holdout_en_ja.json"),
    ),
    (
        "stitch_validation",
        Path("docs/test_inputs/srs_learner_difficulty_stitch_validation_labels_en_ja.json"),
    ),
)


def _float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, int | float):
        return f"{float(value):.{digits}f}"
    return str(value)


def _err(row: dict[str, Any], key: str) -> float:
    return abs(_float(row.get(key)) - _float(row.get("expected")))


def _raw_changed(row: dict[str, Any]) -> bool:
    return abs(_float(row.get("raw_typed")) - _float(row.get("raw_baseline"))) > 0.0005


def _row_key(dataset: str, lemma: object, reading: object) -> str:
    return f"{dataset}\t{str(lemma or '').strip()}/{str(reading or '').strip()}"


def _lemma_key(dataset: str, lemma: object) -> str:
    return f"{dataset}\t{str(lemma or '').strip()}/*"


def _label_from_row(row: dict[str, Any]) -> tuple[str, str]:
    label = str(row.get("label") or "")
    if "/" not in label:
        return label, ""
    lemma, reading = label.rsplit("/", 1)
    return lemma, reading


def _load_expected_overrides(
    label_jsons: list[tuple[str, Path]],
) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for dataset, path in label_jsons:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for label in payload.get("labels") or []:
            if not isinstance(label, dict):
                continue
            expected = label.get("expected_learner_difficulty")
            if expected is None:
                continue
            reading = label.get("expected_reading")
            if reading:
                key = _row_key(dataset, label.get("lemma"), reading)
            else:
                key = _lemma_key(dataset, label.get("lemma"))
            overrides[key] = _float(expected)
    return overrides


def _refresh_expected(row: dict[str, Any], overrides: dict[str, float]) -> dict[str, Any]:
    refreshed = dict(row)
    dataset = str(row.get("dataset") or "")
    lemma, reading = _label_from_row(row)
    key = _row_key(dataset, lemma, reading)
    expected = overrides.get(key, overrides.get(_lemma_key(dataset, lemma)))
    if expected is None:
        return refreshed

    baseline = _float(refreshed.get("baseline"))
    broad = _float(refreshed.get("broad"))
    typed = _float(refreshed.get("typed"))
    refreshed["expected"] = expected
    refreshed["broad_error_delta"] = abs(broad - expected) - abs(baseline - expected)
    refreshed["typed_error_delta"] = abs(typed - expected) - abs(baseline - expected)
    refreshed["typed_vs_broad_error_delta"] = abs(typed - expected) - abs(broad - expected)
    return refreshed


def _suspected_cause(row: dict[str, Any], group: str) -> str:
    typed_gate = _float(row.get("typed_gate"))
    broad_gate = _float(row.get("broad_gate"))
    typed_delta = _float(row.get("typed_delta"))
    kango = _float(row.get("kango"))
    marked = _float(row.get("marked_usage"))
    burden = _float(row.get("kanji_burden"))
    bccwj = row.get("bccwj_difficulty")
    tubelex = row.get("tubelex_count_difficulty")

    if group == "context_success_examples":
        if typed_gate > 0.2 and typed_delta < 0:
            return (
                "desired rescue: typed cross-corpus evidence corrected a late ordinary-looking row"
            )
        return "desired collateral shift: normalization moved row closer to current label"
    if group.startswith("normalization"):
        return "raw score unchanged; final score moved through global normalization/curve pressure"
    if marked >= 0.5:
        return "rescue still fired despite marked/form-risk signal"
    if kango >= 0.5 and typed_gate <= 0.05 and broad_gate > 0.2:
        return "typed gate blocked the broad kango pull; remaining movement is indirect"
    if typed_gate > 0.2 and typed_delta < 0 and burden >= 0.75:
        return "non-kango rescue is treating a burdened written form as ordinary"
    if typed_gate > 0.2 and typed_delta < 0:
        if bccwj is not None and tubelex is not None:
            return "cross-corpus commonness overwhelmed domain/lexical specificity"
        return "typed rescue pulled down without enough counter-signal in compact diagnostics"
    if typed_gate <= 0.05 and typed_delta > 0:
        return "gate did not fire; likely collateral upward shift from normalization"
    return "needs source-feature inspection"


def _counterbalance(row: dict[str, Any], group: str) -> str:
    typed_gate = _float(row.get("typed_gate"))
    typed_delta = _float(row.get("typed_delta"))
    kango = _float(row.get("kango"))
    marked = _float(row.get("marked_usage"))
    burden = _float(row.get("kanji_burden"))

    if group == "context_success_examples":
        return "preserve while testing any counterweight"
    if group.startswith("normalization"):
        return "add drift penalty/anchor metric for rows whose typed gate is zero"
    if marked >= 0.5:
        return "strengthen marked-form guard before cross-corpus rescue"
    if kango >= 0.5 and typed_gate <= 0.05:
        return "probably no direct rescue fix; inspect normalization and broad gate contrast"
    if typed_gate > 0.2 and typed_delta < 0 and burden >= 0.75:
        return "sweep written-form burden or rare-wago guard as a gate multiplier"
    if typed_gate > 0.2 and typed_delta < 0:
        return "try an ordinary-wago specificity counterweight; review label before hardcoding"
    return "no immediate rule; keep in review queue"


def _compact_row(row: dict[str, Any], group: str) -> dict[str, Any]:
    return {
        "group": group,
        "dataset": row.get("dataset"),
        "label": row.get("label"),
        "expected": row.get("expected"),
        "baseline": row.get("baseline"),
        "broad": row.get("broad"),
        "typed": row.get("typed"),
        "baseline_error": round(_err(row, "baseline"), 6),
        "broad_error": round(_err(row, "broad"), 6),
        "typed_error": round(_err(row, "typed"), 6),
        "typed_error_delta": row.get("typed_error_delta"),
        "typed_vs_broad_error_delta": row.get("typed_vs_broad_error_delta"),
        "typed_delta": row.get("typed_delta"),
        "broad_delta": row.get("broad_delta"),
        "typed_gate": row.get("typed_gate"),
        "broad_gate": row.get("broad_gate"),
        "raw_changed": _raw_changed(row),
        "kango": row.get("kango"),
        "kanji_burden": row.get("kanji_burden"),
        "marked_usage": row.get("marked_usage"),
        "bccwj_difficulty": row.get("bccwj_difficulty"),
        "tubelex_count_difficulty": row.get("tubelex_count_difficulty"),
        "suspected_cause": _suspected_cause(row, group),
        "counterbalance_direction": _counterbalance(row, group),
    }


def _classify_rows(
    rows: list[dict[str, Any]],
    *,
    regression_threshold: float,
    drift_threshold: float,
    gate_threshold: float,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "direct_overpull_review": [],
        "typed_worse_than_broad_review": [],
        "normalization_drift_review": [],
        "context_success_examples": [],
    }

    for row in rows:
        typed_error_delta = _float(row.get("typed_error_delta"))
        typed_vs_broad = _float(row.get("typed_vs_broad_error_delta"))
        typed_gate = _float(row.get("typed_gate"))
        typed_delta = _float(row.get("typed_delta"))
        raw_changed = _raw_changed(row)

        if (
            typed_error_delta >= regression_threshold
            and typed_gate > gate_threshold
            and typed_delta < -0.01
        ):
            groups["direct_overpull_review"].append(_compact_row(row, "direct_overpull_review"))

        if typed_vs_broad >= regression_threshold:
            groups["typed_worse_than_broad_review"].append(
                _compact_row(row, "typed_worse_than_broad_review")
            )

        if (
            typed_error_delta >= drift_threshold
            and typed_gate <= gate_threshold
            and not raw_changed
            and abs(typed_delta) >= 0.01
        ):
            groups["normalization_drift_review"].append(
                _compact_row(row, "normalization_drift_review")
            )

        if _float(row.get("typed_error_delta")) <= -0.05:
            groups["context_success_examples"].append(_compact_row(row, "context_success_examples"))

    groups["direct_overpull_review"].sort(
        key=lambda r: (_float(r.get("typed_error_delta")), _float(r.get("typed_gate"))),
        reverse=True,
    )
    groups["typed_worse_than_broad_review"].sort(
        key=lambda r: _float(r.get("typed_vs_broad_error_delta")),
        reverse=True,
    )
    groups["normalization_drift_review"].sort(
        key=lambda r: _float(r.get("typed_error_delta")),
        reverse=True,
    )
    groups["context_success_examples"].sort(
        key=lambda r: _float(r.get("typed_error_delta")),
    )

    return groups


def _limit_groups(
    groups: dict[str, list[dict[str, Any]]], limit: int
) -> dict[str, list[dict[str, Any]]]:
    return {name: rows[:limit] for name, rows in groups.items()}


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows matched._\n"
    lines = [
        "| Dataset | Label | Exp | Base | Broad | Typed | dErr typed | dErr vs broad | Gate typed | Gate broad | kango | burden | marked | Cause | Counterbalance |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("dataset") or ""),
                    f"`{row.get('label') or ''}`",
                    _fmt(row.get("expected")),
                    _fmt(row.get("baseline")),
                    _fmt(row.get("broad")),
                    _fmt(row.get("typed")),
                    _fmt(row.get("typed_error_delta")),
                    _fmt(row.get("typed_vs_broad_error_delta")),
                    _fmt(row.get("typed_gate")),
                    _fmt(row.get("broad_gate")),
                    _fmt(row.get("kango")),
                    _fmt(row.get("kanji_burden")),
                    _fmt(row.get("marked_usage")),
                    str(row.get("suspected_cause") or ""),
                    str(row.get("counterbalance_direction") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    groups = payload["review_groups"]
    lines = [
        "# Cross-Corpus Typed Rescue Failure Diagnostics",
        "",
        "This pack separates new failures by route so we can review the right counterbalance.",
        "",
        "## Summary",
        "",
        f"- Labeled rows compared: `{summary['labeled_count']}`",
        f"- Direct overpull review rows: `{summary['group_counts']['direct_overpull_review']}`",
        f"- Typed worse than broad rows: `{summary['group_counts']['typed_worse_than_broad_review']}`",
        f"- Normalization drift review rows: `{summary['group_counts']['normalization_drift_review']}`",
        f"- Context success examples included: `{summary['group_counts']['context_success_examples']}`",
        f"- Regression threshold: `{summary['regression_threshold']:.3f}`",
        f"- Drift threshold: `{summary['drift_threshold']:.3f}`",
        "",
        "## Direct Overpull Review",
        "",
        "Typed rescue fired and moved the row in the wrong direction relative to the label.",
        "",
        _markdown_table(groups["direct_overpull_review"]),
        "## Typed Worse Than Broad Review",
        "",
        "These are rows where the typed candidate is farther from the label than the broad rescue candidate.",
        "",
        _markdown_table(groups["typed_worse_than_broad_review"]),
        "## Normalization Drift Review",
        "",
        "The typed gate did not fire and raw scores did not change, but final normalized score moved.",
        "",
        _markdown_table(groups["normalization_drift_review"]),
        "## Context Success Examples",
        "",
        "These are nearby wins we should avoid breaking while adding a counterbalance.",
        "",
        _markdown_table(groups["context_success_examples"]),
    ]
    return "\n".join(lines)


def build_payload(
    before_after: dict[str, Any],
    *,
    expected_overrides: dict[str, float],
    regression_threshold: float,
    drift_threshold: float,
    gate_threshold: float,
    limit: int,
) -> dict[str, Any]:
    rows = [
        _refresh_expected(row, expected_overrides)
        for row in before_after.get("all_labeled_rows") or []
        if isinstance(row, dict)
    ]
    groups_all = _classify_rows(
        rows,
        regression_threshold=regression_threshold,
        drift_threshold=drift_threshold,
        gate_threshold=gate_threshold,
    )
    groups = _limit_groups(groups_all, limit)
    return {
        "summary": {
            "source_summary": before_after.get("summary"),
            "labeled_count": len(rows),
            "regression_threshold": regression_threshold,
            "drift_threshold": drift_threshold,
            "gate_threshold": gate_threshold,
            "limit_per_group": limit,
            "group_counts": {name: len(rows) for name, rows in groups_all.items()},
        },
        "review_groups": groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-after-json", type=Path, default=DEFAULT_BEFORE_AFTER_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--label-json",
        action="append",
        default=[],
        metavar="DATASET:PATH",
        help=(
            "Optional expected-label source override. May be repeated. "
            "Defaults to the current calibration, holdout, and stitch labels."
        ),
    )
    parser.add_argument("--regression-threshold", type=float, default=0.02)
    parser.add_argument("--drift-threshold", type=float, default=0.02)
    parser.add_argument("--gate-threshold", type=float, default=0.05)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    with args.before_after_json.open("r", encoding="utf-8") as handle:
        before_after = json.load(handle)

    label_jsons = list(DEFAULT_LABEL_JSONS)
    for value in args.label_json:
        dataset, sep, path_text = value.partition(":")
        if not sep:
            raise ValueError(f"Expected DATASET:PATH for --label-json, got: {value}")
        label_jsons.append((dataset, Path(path_text)))
    expected_overrides = _load_expected_overrides(label_jsons)

    payload = build_payload(
        before_after,
        expected_overrides=expected_overrides,
        regression_threshold=args.regression_threshold,
        drift_threshold=args.drift_threshold,
        gate_threshold=args.gate_threshold,
        limit=args.limit,
    )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(_render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
