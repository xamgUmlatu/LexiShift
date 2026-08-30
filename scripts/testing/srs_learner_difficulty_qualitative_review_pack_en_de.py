#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_sweep_en_de import (  # noqa: E402
    _candidate_by_id,
    _score_row,
    generate_candidates,
)


PAIR = "en-de"
DEFAULT_BAND_SAMPLE_COUNT = 10
DEFAULT_BEGINNER_COUNT = 50
DEFAULT_RESIDUAL_COUNT = 40
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_REFINED_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_en_de_refined_latest.json"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_de.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_de.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_qualitative_review_pack_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_qualitative_review_pack_en_de_latest.md"
)
PRIMARY_STATE = "normal_vocab"
SAMPLE_SEED = "en-de-learner-difficulty-qualitative-v1"
SIGNAL_KEYS = (
    "frequency_blend",
    "rank_base",
    "pmw_base",
    "learner_core_score",
    "learner_source_confidence",
    "goethe_official_a1_learner_source_known",
    "goethe_stem_learner_source_known",
    "odenet_basis_learner_source_known",
    "wordfreq_de_commonness_score",
    "opensubtitles_cistem_frequency_score",
    "klexikon_title_known",
    "wiktionary_rare_dated_flag",
    "wiktionary_form_variant_score",
    "wiktionary_sense_count_score",
    "length_risk",
    "compound_like",
    "translation_count_score",
    "reverse_support_score",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an en-de learner-difficulty qualitative review pack from the "
            "current signal palette and selected formula-sweep candidate. This is "
            "a sidecar diagnostic artifact only."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_REFINED_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id")
    parser.add_argument(
        "--candidate-grid",
        choices=("refined", "broad", "floor_refined"),
        default="refined",
    )
    parser.add_argument("--band-sample-count", type=int, default=DEFAULT_BAND_SAMPLE_COUNT)
    parser.add_argument("--beginner-count", type=int, default=DEFAULT_BEGINNER_COUNT)
    parser.add_argument("--residual-count", type=int, default=DEFAULT_RESIDUAL_COUNT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        signal_rows=_load_jsonl(Path(args.rows_jsonl).expanduser()),
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        calibration_payload=_load_optional_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_optional_json(Path(args.holdout_json).expanduser()),
        candidate_id=args.candidate_id,
        candidate_grid=str(args.candidate_grid),
        band_sample_count=max(1, int(args.band_sample_count)),
        beginner_count=max(1, int(args.beginner_count)),
        residual_count=max(1, int(args.residual_count)),
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


def build_report(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    sweep_payload: Mapping[str, object] | None = None,
    calibration_payload: Mapping[str, object] | None = None,
    holdout_payload: Mapping[str, object] | None = None,
    candidate_id: str | None = None,
    candidate_grid: str = "refined",
    band_sample_count: int = DEFAULT_BAND_SAMPLE_COUNT,
    beginner_count: int = DEFAULT_BEGINNER_COUNT,
    residual_count: int = DEFAULT_RESIDUAL_COUNT,
    generated_at: str | None = None,
) -> dict[str, object]:
    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
    candidate = _candidate_by_id(generate_candidates(candidate_grid), selected_candidate_id)
    if candidate is None and candidate_grid != "broad":
        candidate = _candidate_by_id(generate_candidates("broad"), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")

    labels_by_lemma = _labels_by_lemma(
        calibration_payload=calibration_payload or {},
        holdout_payload=holdout_payload or {},
    )
    scored_rows = [
        _scored_row(row=row, candidate=candidate, labels_by_lemma=labels_by_lemma)
        for row in signal_rows
        if str(row.get("lemma") or "").strip()
    ]
    scored_rows = [row for row in scored_rows if _safe_float(row.get("score")) is not None]
    scored_rows = sorted(
        scored_rows,
        key=lambda row: (_safe_float(row.get("score")) or 0.0, _rank(row)),
    )
    thin_bands = _thin_band_samples(scored_rows, per_band=band_sample_count)
    beginner_rows = _beginner_rows(scored_rows, limit=beginner_count)
    residual_rows = _labeled_residual_rows(scored_rows, limit=residual_count)
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_qualitative_review_pack_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Qualitative review pack for the selected en-de difficulty contender: "
                "thin score bands, beginner-zone feel, and largest labeled residuals."
            ),
            "candidate_id": selected_candidate_id,
            "candidate_grid": candidate_grid,
            "sample_seed": SAMPLE_SEED,
            "sampling_policy": (
                "Band rows are deterministic hash samples within each score band, "
                "not handpicked. This keeps artifacts reproducible while avoiding "
                "rank-order cherry-picking."
            ),
        },
        "inputs": {
            "signal_row_count": len(scored_rows),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "formula_sweep_grid": _as_mapping(_as_mapping(sweep_payload).get("method")).get(
                "candidate_grid"
            ),
            "calibration_count": len(_as_sequence(_as_mapping(calibration_payload).get("labels"))),
            "holdout_count": len(_as_sequence(_as_mapping(holdout_payload).get("labels"))),
        },
        "summary": {
            "candidate_rows_scanned": len(scored_rows),
            "labeled_rows_joined": sum(1 for row in scored_rows if row.get("label")),
            "thin_band_count": len(thin_bands),
            "thin_band_sample_count": sum(
                len(_as_sequence(band.get("rows"))) for band in thin_bands
            ),
            "beginner_row_count": len(beginner_rows),
            "labeled_residual_row_count": len(residual_rows),
            "score_band_counts": _score_band_counts(scored_rows),
        },
        "thin_band_samples": thin_bands,
        "beginner_zone_rows": beginner_rows,
        "labeled_residual_errors": residual_rows,
        "limitations": [
            "This artifact is qualitative and diagnostic; it does not promote a formula or add labels.",
            "Band samples are deterministic for diffability, so they are representative probes rather than statistical estimates.",
            "Manual corrections, admission restrictions, and display fixes remain separate layers from scalar difficulty.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Learner Difficulty Qualitative Review Pack",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate: `{method.get('candidate_id')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        f"- Manual labels added: `{report.get('manual_labels_added')}`",
        "",
        "## Summary",
        "",
        f"- Candidate rows scanned: `{summary.get('candidate_rows_scanned')}`",
        f"- Labeled rows joined: `{summary.get('labeled_rows_joined')}`",
        f"- Thin-band sampled rows: `{summary.get('thin_band_sample_count')}`",
        f"- Beginner-zone rows: `{summary.get('beginner_row_count')}`",
        f"- Labeled residual rows: `{summary.get('labeled_residual_row_count')}`",
        "",
        "Score-band counts:",
        "",
        "| Band | Rows |",
        "| --- | ---: |",
    ]
    for band, count in _as_mapping(summary.get("score_band_counts")).items():
        lines.append(f"| `{band}` | {count} |")
    lines.extend(["", "## Thin-Band Samples", ""])
    for raw_band in _as_sequence(report.get("thin_band_samples")):
        band = _as_mapping(raw_band)
        lines.extend(
            [
                f"### `{band.get('band')}`",
                f"Rows in band: `{band.get('row_count')}`",
                "",
                _row_table(_as_sequence(band.get("rows")), include_label=True),
                "",
            ]
        )
    lines.extend(
        [
            "## Beginner-Zone Rows",
            "",
            _row_table(_as_sequence(report.get("beginner_zone_rows")), include_label=True),
            "",
            "## Largest Labeled Residuals",
            "",
            "| # | Lemma | Split | Expected | Score | Error | Direction | POS | Flags | Translations |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for index, raw in enumerate(_as_sequence(report.get("labeled_residual_errors")), start=1):
        row = _as_mapping(raw)
        label = _as_mapping(row.get("label"))
        lines.append(
            f"| {index} | `{_escape(row.get('lemma'))}` | `{_escape(label.get('split'))}` | "
            f"{_fmt(row.get('expected'))} | {_fmt(row.get('score'))} | "
            f"{_fmt(row.get('abs_error'))} | `{_escape(row.get('direction'))}` | "
            f"`{_escape(row.get('pos_bucket'))}` | "
            f"{_escape(', '.join(str(item) for item in _as_sequence(label.get('review_flags')))) or '-'} | "
            f"{_escape('; '.join(str(item) for item in _as_sequence(row.get('translations'))[:3])) or '-'} |"
        )
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["", "## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _row_table(rows: Sequence[object], *, include_label: bool) -> str:
    lines = [
        "| # | Lemma | Score | POS | Rank | Label | Translations | Signals |",
        "| ---: | --- | ---: | --- | ---: | --- | --- | --- |",
    ]
    for index, raw in enumerate(rows, start=1):
        row = _as_mapping(raw)
        label = _as_mapping(row.get("label"))
        label_cell = "-"
        if include_label and label:
            label_cell = (
                f"{_fmt(label.get('expected_learner_difficulty'))} `{_escape(label.get('split'))}`"
            )
        lines.append(
            f"| {index} | `{_escape(row.get('lemma'))}` | {_fmt(row.get('score'))} | "
            f"`{_escape(row.get('pos_bucket'))}` | {_fmt_rank(row.get('core_rank'))} | "
            f"{label_cell} | "
            f"{_escape('; '.join(str(item) for item in _as_sequence(row.get('translations'))[:3])) or '-'} | "
            f"{_escape(_compact_signal_text(_as_mapping(row.get('signals')))) or '-'} |"
        )
    return "\n".join(lines)


def _thin_band_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    per_band: int,
) -> list[dict[str, object]]:
    result = []
    for low, high in _bands():
        candidates = [
            row
            for row in rows
            if _in_band(_safe_float(row.get("score")) or 0.0, low=low, high=high)
            and row.get("candidate_state") == PRIMARY_STATE
        ]
        result.append(
            {
                "band": f"{low:.2f}-{high:.2f}",
                "row_count": len(candidates),
                "rows": _deterministic_sample(candidates, per_band),
            }
        )
    return result


def _beginner_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[Mapping[str, object]]:
    candidates = [
        row
        for row in rows
        if (_safe_float(row.get("score")) or 0.0) <= 0.25
        and row.get("candidate_state") == PRIMARY_STATE
    ]
    return candidates[:limit]


def _labeled_residual_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    result = []
    for row in rows:
        label = _as_mapping(row.get("label"))
        expected = _safe_float(label.get("expected_learner_difficulty"))
        score = _safe_float(row.get("score"))
        if expected is None or score is None:
            continue
        expected_state = str(label.get("expected_candidate_state") or PRIMARY_STATE)
        if expected_state != PRIMARY_STATE:
            continue
        error = abs(score - expected)
        item = dict(row)
        item["expected"] = _round_float(expected)
        item["abs_error"] = _round_float(error)
        item["direction"] = "too_hard" if score > expected else "too_easy"
        result.append(item)
    return sorted(
        result,
        key=lambda row: (
            _safe_float(row.get("abs_error")) or 0.0,
            _safe_float(row.get("score")) or 0.0,
        ),
        reverse=True,
    )[:limit]


def _scored_row(
    *,
    row: Mapping[str, object],
    candidate: object,
    labels_by_lemma: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    lemma = str(row.get("lemma") or "")
    label = _as_mapping(labels_by_lemma.get(lemma.lower()))
    return {
        "lemma": lemma,
        "score": _round_float(_score_row(candidate, row)),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "candidate_state": PRIMARY_STATE,
        "core_rank": row.get("core_rank"),
        "pmw": row.get("pmw"),
        "translations": list(_as_sequence(row.get("translations")))[:5],
        "signals": {
            key: _round_float(row.get(key))
            for key in SIGNAL_KEYS
            if abs(_round_float(row.get(key))) > 0.000001
        },
        "label": label,
    }


def _labels_by_lemma(
    *,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for split, payload in (("calibration", calibration_payload), ("holdout", holdout_payload)):
        for raw in _as_sequence(payload.get("labels")):
            label = dict(_as_mapping(raw))
            lemma = str(label.get("lemma") or "").lower()
            if not lemma:
                continue
            label["split"] = split
            result[lemma] = label
    return result


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return "rw075_rg120_pg100_wg118_wf22_pedmix_modtail_long16_poly04"


def _deterministic_sample(
    rows: Sequence[Mapping[str, object]],
    limit: int,
) -> list[Mapping[str, object]]:
    return sorted(rows, key=lambda row: _sample_key(row))[:limit]


def _sample_key(row: Mapping[str, object]) -> tuple[str, float]:
    lemma = str(row.get("lemma") or "")
    digest = hashlib.sha256(f"{SAMPLE_SEED}:{lemma}".encode("utf-8")).hexdigest()
    return (digest, _safe_float(row.get("score")) or 0.0)


def _score_band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for low, high in _bands():
        label = f"{low:.2f}-{high:.2f}"
        counts[label] = sum(
            1 for row in rows if _in_band(_safe_float(row.get("score")) or 0.0, low=low, high=high)
        )
    return counts


def _bands() -> list[tuple[float, float]]:
    return [(index / 10.0, (index + 1) / 10.0) for index in range(10)]


def _in_band(value: float, *, low: float, high: float) -> bool:
    if high >= 1.0:
        return low <= value <= high
    return low <= value < high


def _rank(row: Mapping[str, object]) -> float:
    return _safe_float(row.get("core_rank")) or 999999999.0


def _load_optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return _load_json(path)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if isinstance(row, Mapping):
                rows.append(row)
    return rows


def _compact_signal_text(signals: Mapping[str, object]) -> str:
    parts = []
    for key, value in signals.items():
        numeric = _safe_float(value)
        if numeric is None:
            continue
        parts.append(f"{key}={numeric:.3f}")
    return "; ".join(parts[:8])


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.0f}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
