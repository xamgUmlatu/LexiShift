#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_formula_eval_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_formula_eval_en_es_latest.md"
)
PRIMARY_STATE = "normal_vocab"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate en-es formula-probe variants against reviewed learner-difficulty "
            "calibration and holdout labels."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    report = build_report(
        formula_report=formula_report,
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in formula_rows}
    variant_ids = _variant_ids(formula_rows)

    records = []
    for variant_id in variant_ids:
        records.append(
            _variant_record(
                variant_id=variant_id,
                rows_by_lemma=rows_by_lemma,
                calibration_labels=calibration_labels,
                holdout_labels=holdout_labels,
            )
        )
    records = sorted(
        records,
        key=lambda row: (
            _score_at(row, "calibration_primary", "balanced_score"),
            _score_at(row, "holdout_primary", "balanced_score"),
            _score_at(row, "calibration_primary", "pairwise_order_score"),
        ),
        reverse=True,
    )
    best = records[0] if records else {}
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_formula_eval_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "formula_source": "srs_learner_difficulty_formula_probe_en_es",
            "metric_source": "srs_learner_difficulty_piecewise_search_en_ja shared metric helpers",
            "primary_score_policy": (
                "Primary metrics exclude labels whose expected_candidate_state is not "
                "`normal_vocab`; all-numeric metrics are reported separately."
            ),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "variant_count": len(variant_ids),
        },
        "summary": {
            "best_variant_id": best.get("variant_id"),
            "best_calibration_primary": _compact_eval(best.get("calibration_primary")),
            "best_holdout_primary": _compact_eval(best.get("holdout_primary")),
            "best_calibration_all_numeric": _compact_eval(best.get("calibration_all_numeric")),
            "best_holdout_all_numeric": _compact_eval(best.get("holdout_all_numeric")),
        },
        "variants": records,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _as_mapping(report.get("inputs"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Learner Difficulty Formula Eval",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Formula probe: `{inputs.get('formula_probe_decision')}`",
        f"- Formula top N: `{inputs.get('formula_probe_top_n')}`",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Variants evaluated: `{inputs.get('variant_count')}`",
        "",
        "## Summary",
        "",
        f"- Best variant: `{summary.get('best_variant_id')}`",
        "",
        "| Split | Rows | Balanced | MAE | Bucket | Pairwise | High Tail |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (
        ("best_calibration_primary", "calibration primary"),
        ("best_holdout_primary", "holdout primary"),
        ("best_calibration_all_numeric", "calibration all numeric"),
        ("best_holdout_all_numeric", "holdout all numeric"),
    ):
        item = _as_mapping(summary.get(key))
        lines.append(
            f"| {label} | {item.get('count', '')} | {_fmt(item.get('balanced_score'))} | "
            f"{_fmt(item.get('mae'))} | {_fmt(item.get('bucket_accuracy'))} | "
            f"{_fmt(item.get('pairwise_accuracy'))} | {_fmt(item.get('high_tail_score'))} |"
        )
    lines.extend(
        [
            "",
            "## Leaderboard",
            "",
            "| Variant | Cal Balanced | Holdout Balanced | Cal MAE | Holdout MAE | Cal Pairwise | Holdout Pairwise |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for raw in _as_sequence(report.get("variants"))[:20]:
        row = _as_mapping(raw)
        cal = _compact_eval(row.get("calibration_primary"))
        hold = _compact_eval(row.get("holdout_primary"))
        lines.append(
            f"| `{row.get('variant_id')}` | {_fmt(cal.get('balanced_score'))} | "
            f"{_fmt(hold.get('balanced_score'))} | {_fmt(cal.get('mae'))} | "
            f"{_fmt(hold.get('mae'))} | {_fmt(cal.get('pairwise_accuracy'))} | "
            f"{_fmt(hold.get('pairwise_accuracy'))} |"
        )
    best = _as_mapping(
        _as_sequence(report.get("variants"))[0] if _as_sequence(report.get("variants")) else {}
    )
    if best:
        lines.extend(["", "## Best Variant Largest Primary Errors", ""])
        for key, title in (
            ("calibration_primary", "Calibration"),
            ("holdout_primary", "Holdout"),
        ):
            lines.extend(
                [
                    f"### {title}",
                    "",
                    "| Lemma | Expected | Observed | Abs Error |",
                    "| --- | ---: | ---: | ---: |",
                ]
            )
            for error in _as_sequence(_as_mapping(best.get(key)).get("largest_errors"))[:12]:
                item = _as_mapping(error)
                lines.append(
                    f"| `{_escape(item.get('lemma'))}` | {_fmt(item.get('expected'))} | "
                    f"{_fmt(item.get('observed'))} | {_fmt(item.get('abs_error'))} |"
                )
            lines.append("")
    return "\n".join(lines)


def _variant_record(
    *,
    variant_id: str,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "variant_id": variant_id,
        "calibration_primary": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            variant_id=variant_id,
            primary_only=True,
        ),
        "holdout_primary": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            variant_id=variant_id,
            primary_only=True,
        ),
        "calibration_all_numeric": _evaluate_labels(
            labels=calibration_labels,
            rows_by_lemma=rows_by_lemma,
            variant_id=variant_id,
            primary_only=False,
        ),
        "holdout_all_numeric": _evaluate_labels(
            labels=holdout_labels,
            rows_by_lemma=rows_by_lemma,
            variant_id=variant_id,
            primary_only=False,
        ),
    }


def _evaluate_labels(
    *,
    labels: Sequence[Mapping[str, object]],
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    variant_id: str,
    primary_only: bool,
) -> dict[str, object]:
    selected = [
        label
        for label in labels
        if _safe_float(label.get("expected_learner_difficulty")) is not None
        and (not primary_only or str(label.get("expected_candidate_state") or "") == PRIMARY_STATE)
    ]
    expected_values = []
    observed_values = []
    expected_bands = []
    label_names = []
    expected_states = []
    observed_states = []
    row_pairs = []
    missing = []
    for label in selected:
        lemma = str(label.get("lemma") or "")
        row = rows_by_lemma.get(lemma.lower())
        observed = None
        if row is not None:
            observed = _safe_float(_as_mapping(row.get("variant_scores")).get(variant_id))
        if observed is None:
            missing.append(lemma)
            observed = float("nan")
        expected = _safe_float(label.get("expected_learner_difficulty"))
        expected_values.append(expected if expected is not None else float("nan"))
        observed_values.append(observed)
        expected_bands.append(str(label.get("expected_difficulty_band") or ""))
        label_names.append(lemma)
        expected_states.append(str(label.get("expected_candidate_state") or ""))
        observed_states.append(str(_as_mapping(row).get("candidate_state") or ""))
        row_pairs.append((label, row, observed))
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected_values, dtype=np.float32),
        observed_values=np.asarray(observed_values, dtype=np.float32),
        expected_bands=expected_bands,
        labels=label_names,
        expected_candidate_states=np.asarray(expected_states, dtype="<U64"),
        observed_candidate_states=np.asarray(observed_states, dtype="<U64"),
    )
    return {
        "label_count": len(selected),
        "missing_count": len(missing),
        "missing": missing[:20],
        "scores": metrics["scores"],
        "metrics": _summary_metrics(metrics),
        "largest_errors": _largest_errors(row_pairs, limit=20),
    }


def _largest_errors(
    row_pairs: Sequence[tuple[Mapping[str, object], Mapping[str, object] | None, float]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    errors = []
    for label, row, observed in row_pairs:
        expected = _safe_float(label.get("expected_learner_difficulty"))
        if expected is None or not np.isfinite(observed):
            continue
        errors.append(
            {
                "lemma": label.get("lemma"),
                "expected": _round(expected),
                "observed": _round(observed),
                "abs_error": _round(abs(observed - expected)),
                "expected_candidate_state": label.get("expected_candidate_state"),
                "source_spalex_rank": label.get("source_spalex_rank"),
                "pos": _as_mapping(row).get("pos") if row is not None else None,
            }
        )
    return sorted(errors, key=lambda item: _safe_float(item.get("abs_error")) or -1, reverse=True)[
        :limit
    ]


def _variant_ids(rows: Sequence[Mapping[str, object]]) -> list[str]:
    ids: set[str] = set()
    for row in rows:
        ids.update(str(key) for key in _as_mapping(row.get("variant_scores")).keys())
    preferred = [
        "spalex_blend_frequency",
        "rank_frequency_only",
        "zipf_frequency_only",
        "pos_guard_light",
        "dictionary_guard_light",
        "cognate_rescue_light",
        "transfer_all_light",
        "transfer_all_medium",
        "tail_guard_medium",
    ]
    return [item for item in preferred if item in ids] + sorted(ids - set(preferred))


def _compact_eval(value: object) -> dict[str, object]:
    item = _as_mapping(value)
    scores = _as_mapping(item.get("scores"))
    metrics = _as_mapping(item.get("metrics"))
    return {
        "count": item.get("label_count"),
        "balanced_score": scores.get("balanced_score"),
        "mae": metrics.get("mae"),
        "bucket_accuracy": metrics.get("bucket_accuracy"),
        "pairwise_accuracy": metrics.get("pairwise_accuracy"),
        "high_tail_score": scores.get("high_tail_score"),
        "missing_count": item.get("missing_count"),
    }


def _score_at(row: Mapping[str, object], eval_key: str, score_key: str) -> float:
    return (
        _safe_float(_as_mapping(_as_mapping(row.get(eval_key)).get("scores")).get(score_key))
        or -1.0
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None else None


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
