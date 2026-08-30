#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
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
from srs_learner_difficulty_qualitative_review_pack_en_de import (  # noqa: E402
    _selected_candidate_id,
)


PAIR = "en-de"
DEFAULT_CANDIDATE_GRID = "floor_refined"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_REVIEW_PACK_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_qualitative_review_pack_en_de_product_latest.json"
)
DEFAULT_FORMULA_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_sweep_en_de_product_medium_latest.json"
)
DEFAULT_MANUAL_CORRECTIONS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_manual_corrections_en_de.json"
)
DEFAULT_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_de_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_review_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_review_en_de_latest.md"
)
DEFAULT_PACKAGED_CSV_OUT = (
    PROJECT_ROOT
    / "core"
    / "lexishift_core"
    / "resources"
    / "srs"
    / "en_de"
    / "learner_difficulty_corrected.csv"
)
DEFAULT_REVIEW_LIMIT = 80


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the deterministic full en-de learner-difficulty ranking for "
            "the selected formula candidate, with the narrow manual correction "
            "layer applied."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--review-pack-json", type=Path, default=DEFAULT_REVIEW_PACK_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument(
        "--manual-corrections-json", type=Path, default=DEFAULT_MANUAL_CORRECTIONS_JSON
    )
    parser.add_argument("--candidate-id")
    parser.add_argument("--candidate-grid", default=DEFAULT_CANDIDATE_GRID)
    parser.add_argument("--review-limit", type=int, default=DEFAULT_REVIEW_LIMIT)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--packaged-csv-out",
        type=Path,
        default=None,
        help=(
            "Optional runtime package output. Pass the packaged en_de resource path "
            "when intentionally changing production default ranking."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report, csv_rows = build_report(
        signal_rows=_load_jsonl(Path(args.rows_jsonl).expanduser()),
        review_pack_payload=_load_optional_json(Path(args.review_pack_json).expanduser()),
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        corrections_payload=_load_json(Path(args.manual_corrections_json).expanduser()),
        candidate_id=args.candidate_id,
        candidate_grid=str(args.candidate_grid),
        review_limit=max(1, int(args.review_limit)),
        csv_out=Path(args.csv_out).expanduser().resolve(strict=False),
        packaged_csv_out=(
            Path(args.packaged_csv_out).expanduser().resolve(strict=False)
            if args.packaged_csv_out
            else None
        ),
    )
    csv_out = Path(args.csv_out).expanduser().resolve(strict=False)
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_out, csv_rows)
    packaged_csv_out = (
        Path(args.packaged_csv_out).expanduser().resolve(strict=False)
        if args.packaged_csv_out
        else None
    )
    if packaged_csv_out is not None:
        packaged_csv_out.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(packaged_csv_out, csv_rows)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote CSV ranking to {csv_out}")
    if packaged_csv_out is not None:
        print(f"Wrote packaged CSV ranking to {packaged_csv_out}")
    print(f"Wrote JSON review artifact to {json_out}")
    print(f"Wrote Markdown review artifact to {markdown_out}")
    return 0


def build_report(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    review_pack_payload: Mapping[str, object] | None,
    sweep_payload: Mapping[str, object] | None,
    corrections_payload: Mapping[str, object],
    csv_out: Path,
    packaged_csv_out: Path | None = None,
    candidate_id: str | None = None,
    candidate_grid: str = DEFAULT_CANDIDATE_GRID,
    review_limit: int = DEFAULT_REVIEW_LIMIT,
    generated_at: str | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    selected_candidate_id = candidate_id or _resolve_candidate_id(
        review_pack_payload=review_pack_payload,
        sweep_payload=sweep_payload,
    )
    candidate = _candidate_by_id(generate_candidates(candidate_grid), selected_candidate_id)
    if candidate is None and candidate_grid != "broad":
        candidate = _candidate_by_id(generate_candidates("broad"), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")

    corrections_by_lemma = _corrections_by_lemma(corrections_payload)
    scored_rows = [
        _scored_row(
            row=row,
            candidate=candidate,
            correction=_correction_for_row(row, corrections_by_lemma),
        )
        for row in signal_rows
        if str(row.get("lemma") or "").strip()
    ]
    scored_rows = [
        row for row in scored_rows if _safe_float(row.get("effective_score")) is not None
    ]
    corrected_rows = sorted(
        scored_rows,
        key=lambda row: (
            _safe_float(row.get("effective_score")) or 0.0,
            _core_rank(row),
            str(row.get("lemma") or ""),
        ),
    )
    csv_rows = [_csv_row(row=row, rank=rank) for rank, row in enumerate(corrected_rows, start=1)]
    applications = [
        _application_row(row, rank=rank)
        for rank, row in enumerate(corrected_rows, start=1)
        if _is_active_correction(_mapping(row.get("correction")))
    ]
    production_changed = packaged_csv_out is not None
    report = {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_final_ranking_review_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": production_changed,
        "production_ranking_changed": production_changed,
        "method": {
            "purpose": (
                "Deterministic full-ranking export for en-de learner-difficulty "
                "review. The full ranking is sorted by corrected score, then "
                "core frequency rank, then lemma."
            ),
            "candidate_id": selected_candidate_id,
            "candidate_grid": candidate_grid,
            "manual_corrections_applied": bool(corrections_by_lemma),
            "manual_correction_status": corrections_payload.get("status"),
            "sort_policy": "effective_score, then core_rank, then lemma",
            "review_limit": review_limit,
        },
        "outputs": {
            "full_ranking_csv": _repo_path(csv_out),
            "packaged_ranking_csv": _repo_path(packaged_csv_out) if packaged_csv_out else None,
        },
        "inputs": {
            "signal_row_count": len(scored_rows),
            "review_pack_decision": _mapping(review_pack_payload).get("decision"),
            "review_pack_generated_at": _mapping(review_pack_payload).get("generated_at"),
            "formula_sweep_decision": _mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _mapping(sweep_payload).get("generated_at"),
            "correction_count": len(corrections_by_lemma),
        },
        "summary": {
            "candidate_rows_scanned": len(scored_rows),
            "correction_rows": len(applications),
            "restricted_admission_rows": sum(
                1 for row in applications if "restricted_admission" in row["correction_types"]
            ),
            "score_moving_rows": sum(
                1
                for row in applications
                if abs(_safe_float(row.get("correction_delta")) or 0.0) > 0.000001
            ),
            "band_counts": _band_counts(corrected_rows),
        },
        "correction_applications": applications,
        "first_rows": [
            _review_row(row, rank=rank)
            for rank, row in enumerate(corrected_rows[:review_limit], start=1)
        ],
        "corrected_restricted_rows": [
            _review_row(row, rank=rank)
            for rank, row in enumerate(corrected_rows, start=1)
            if _is_active_correction(_mapping(row.get("correction")))
        ],
        "limitations": [
            "This export applies only the narrow reviewed en-de manual correction layer.",
            "The correction layer changes admission metadata for restricted rows but does not add broad automatic candidate classification rules.",
            "Scalar score floors/overrides are intentionally unused in the initial en-de manual set.",
        ],
    }
    return report, csv_rows


def render_markdown(report: Mapping[str, object]) -> str:
    method = _mapping(report.get("method"))
    summary = _mapping(report.get("summary"))
    outputs = _mapping(report.get("outputs"))
    lines = [
        "# en-de Learner Difficulty Final Ranking Review",
        "",
        "## Summary",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate: `{_escape(method.get('candidate_id'))}`",
        f"- Candidate grid: `{_escape(method.get('candidate_grid'))}`",
        f"- Full ranking CSV: `{_escape(outputs.get('full_ranking_csv'))}`",
        f"- Packaged ranking CSV: `{_escape(outputs.get('packaged_ranking_csv'))}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        f"- Candidate rows scanned: `{summary.get('candidate_rows_scanned')}`",
        f"- Correction rows: `{summary.get('correction_rows')}`",
        f"- Restricted admission rows: `{summary.get('restricted_admission_rows')}`",
        f"- Score-moving rows: `{summary.get('score_moving_rows')}`",
        "",
        "The full ranking is sorted by corrected score, then core frequency rank, then lemma.",
        "",
        "## Band Counts",
        "",
        "| Band | Rows |",
        "| --- | ---: |",
    ]
    for band, count in _mapping(summary.get("band_counts")).items():
        lines.append(f"| `{_escape(band)}` | {count} |")
    lines.extend(["", "## Correction Applications", ""])
    lines.append(_row_table(_sequence(report.get("correction_applications"))))
    review_limit = method.get("review_limit") or DEFAULT_REVIEW_LIMIT
    lines.extend(["", f"## First {review_limit} Rows", ""])
    lines.append(_row_table(_sequence(report.get("first_rows"))))
    lines.extend(["", "## Corrected Restricted Rows", ""])
    lines.append(_row_table(_sequence(report.get("corrected_restricted_rows"))))
    lines.extend(["", "## Limitations", ""])
    for limitation in _sequence(report.get("limitations")):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _scored_row(
    *,
    row: Mapping[str, object],
    candidate: object,
    correction: Mapping[str, object],
) -> dict[str, object]:
    model_score = _safe_float(_score_row(candidate, row))
    effective_score = _apply_score_correction(model_score, correction)
    return {
        "lemma": str(row.get("lemma") or "").strip(),
        "reading": "",
        "model_score": _round_float(model_score),
        "effective_score": _round_float(effective_score),
        "correction_delta": _round_float((effective_score or 0.0) - (model_score or 0.0)),
        "core_rank": row.get("core_rank"),
        "pmw": row.get("pmw"),
        "candidate_state": "normal_vocab",
        "pos": str(row.get("pos") or ""),
        "pos_bucket": str(row.get("pos_bucket") or ""),
        "translations": list(_sequence(row.get("translations")))[:5],
        "correction": dict(correction),
        "signals": {
            "rank_base": _round_float(row.get("rank_base")),
            "frequency_blend": _round_float(row.get("frequency_blend")),
            "learner_source_confidence": _round_float(row.get("learner_source_confidence")),
            "goethe_stem_learner_source_known": _round_float(
                row.get("goethe_stem_learner_source_known")
            ),
            "openlingo_learner_source_known": _round_float(
                row.get("openlingo_learner_source_known")
            ),
            "wordfreq_de_commonness_score": _round_float(row.get("wordfreq_de_commonness_score")),
            "opensubtitles_cistem_frequency_score": _round_float(
                row.get("opensubtitles_cistem_frequency_score")
            ),
            "translation_count_score": _round_float(row.get("translation_count_score")),
            "reverse_support_score": _round_float(row.get("reverse_support_score")),
        },
    }


def _csv_row(*, row: Mapping[str, object], rank: int) -> dict[str, object]:
    correction = _mapping(row.get("correction"))
    signals = _mapping(row.get("signals"))
    return {
        "rank": rank,
        "lemma": row.get("lemma"),
        "reading": row.get("reading") or "",
        "score": row.get("effective_score"),
        "model_score": row.get("model_score"),
        "correction_delta": row.get("correction_delta"),
        "band": _score_band(_safe_float(row.get("effective_score")) or 0.0),
        "core_rank": _round_float(row.get("core_rank")),
        "pmw": _round_float(row.get("pmw")),
        "candidate_state": row.get("candidate_state"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "correction_types": ",".join(
            str(item) for item in _sequence(correction.get("correction_types"))
        ),
        "display_form": str(correction.get("display_form") or ""),
        "admission_override": str(correction.get("admission_override") or ""),
        "topic_stretch_allowed": _topic_stretch_allowed(correction),
        "correction_status": str(correction.get("status") or ""),
        "correction_rationale": str(correction.get("rationale") or ""),
        "manual_correction_active": "yes" if _is_active_correction(correction) else "",
        "translations": "; ".join(str(item) for item in _sequence(row.get("translations"))[:3]),
        "rank_base": signals.get("rank_base"),
        "frequency_blend": signals.get("frequency_blend"),
        "learner_source_confidence": signals.get("learner_source_confidence"),
        "goethe_stem_learner_source_known": signals.get("goethe_stem_learner_source_known"),
        "openlingo_learner_source_known": signals.get("openlingo_learner_source_known"),
        "wordfreq_de_commonness_score": signals.get("wordfreq_de_commonness_score"),
        "opensubtitles_cistem_frequency_score": signals.get("opensubtitles_cistem_frequency_score"),
        "translation_count_score": signals.get("translation_count_score"),
        "reverse_support_score": signals.get("reverse_support_score"),
    }


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = [
        "rank",
        "lemma",
        "reading",
        "score",
        "model_score",
        "correction_delta",
        "band",
        "core_rank",
        "pmw",
        "candidate_state",
        "pos",
        "pos_bucket",
        "correction_types",
        "display_form",
        "admission_override",
        "topic_stretch_allowed",
        "correction_status",
        "correction_rationale",
        "manual_correction_active",
        "translations",
        "rank_base",
        "frequency_blend",
        "learner_source_confidence",
        "goethe_stem_learner_source_known",
        "openlingo_learner_source_known",
        "wordfreq_de_commonness_score",
        "opensubtitles_cistem_frequency_score",
        "translation_count_score",
        "reverse_support_score",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _application_row(row: Mapping[str, object], *, rank: int) -> dict[str, object]:
    correction = _mapping(row.get("correction"))
    return {
        "rank": rank,
        "lemma": row.get("lemma"),
        "score": row.get("effective_score"),
        "model_score": row.get("model_score"),
        "correction_delta": row.get("correction_delta"),
        "core_rank": row.get("core_rank"),
        "pos_bucket": row.get("pos_bucket"),
        "correction_types": list(_sequence(correction.get("correction_types"))),
        "admission_override": correction.get("admission_override"),
        "translations": list(_sequence(row.get("translations")))[:3],
        "rationale": correction.get("rationale"),
    }


def _review_row(row: Mapping[str, object], *, rank: int) -> dict[str, object]:
    correction = _mapping(row.get("correction"))
    return {
        "rank": rank,
        "lemma": row.get("lemma"),
        "score": row.get("effective_score"),
        "model_score": row.get("model_score"),
        "core_rank": row.get("core_rank"),
        "pos_bucket": row.get("pos_bucket"),
        "correction_types": list(_sequence(correction.get("correction_types"))),
        "admission_override": correction.get("admission_override"),
        "translations": list(_sequence(row.get("translations")))[:3],
    }


def _row_table(rows: Sequence[object]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Rank | Lemma | Score | Model | Core rank | POS | Correction | Admission | Translations |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for raw in rows:
        row = _mapping(raw)
        lines.append(
            f"| {_fmt_rank(row.get('rank'))} | `{_escape(row.get('lemma'))}`"
            f" | {_fmt(row.get('score'))} | {_fmt(row.get('model_score'))}"
            f" | {_fmt_rank(row.get('core_rank'))} | `{_escape(row.get('pos_bucket'))}`"
            f" | {_escape(', '.join(str(item) for item in _sequence(row.get('correction_types'))) or '-')}"
            f" | `{_escape(row.get('admission_override'))}`"
            f" | {_escape('; '.join(str(item) for item in _sequence(row.get('translations'))) or '-')} |"
        )
    return "\n".join(lines)


def _resolve_candidate_id(
    *,
    review_pack_payload: Mapping[str, object] | None,
    sweep_payload: Mapping[str, object] | None,
) -> str:
    review_candidate = str(
        _mapping(_mapping(review_pack_payload).get("method")).get("candidate_id") or ""
    ).strip()
    if review_candidate:
        return review_candidate
    return _selected_candidate_id(sweep_payload)


def _corrections_by_lemma(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    result = {}
    for raw in _sequence(payload.get("corrections")):
        correction = _mapping(raw)
        lemma = str(correction.get("lemma") or correction.get("surface") or "").strip().lower()
        if lemma:
            result[lemma] = correction
    return result


def _correction_for_row(
    row: Mapping[str, object],
    corrections_by_lemma: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    lemma = str(row.get("lemma") or "").strip().lower()
    return corrections_by_lemma.get(lemma, {})


def _apply_score_correction(
    model_score: float | None,
    correction: Mapping[str, object],
) -> float | None:
    score = model_score
    if not _is_active_correction(correction):
        return score
    override = _safe_float(correction.get("score_override"))
    if override is not None:
        score = override
    floor = _safe_float(correction.get("min_score"))
    if floor is not None:
        score = max(score if score is not None else floor, floor)
    return _clamp01(score)


def _topic_stretch_allowed(correction: Mapping[str, object]) -> str:
    if not correction:
        return ""
    correction_types = {str(item) for item in _sequence(correction.get("correction_types"))}
    admission = str(correction.get("admission_override") or "").strip()
    if "exclude_standalone_srs" in correction_types:
        return "False"
    if "restricted_admission" in correction_types:
        return "False"
    if admission and admission != "normal_vocab":
        return "False"
    return "True"


def _is_active_correction(correction: Mapping[str, object]) -> bool:
    status = str(correction.get("status") or "active").strip().lower()
    return bool(correction) and status in {"active", "accepted"}


def _band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        band = _score_band(_safe_float(row.get("effective_score")) or 0.0)
        counts[band] = counts.get(band, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _score_band(score: float) -> str:
    bounded = min(max(score, 0.0), 1.0)
    index = min(19, int(bounded * 20.0))
    return f"{index / 20.0:.2f}-{(index + 1) / 20.0:.2f}"


def _core_rank(row: Mapping[str, object]) -> float:
    rank = _safe_float(row.get("core_rank"))
    return rank if rank is not None else 999999999.0


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, Mapping):
            rows.append(dict(payload))
    return rows


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _mapping(payload)


def _load_optional_json(path: Path) -> Mapping[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, (list, tuple)):
        return value
    return ()


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _round_float(value: object) -> float | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return round(parsed, 6)


def _clamp01(value: object) -> float | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return min(max(parsed, 0.0), 1.0)


def _fmt(value: object) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.3f}"


def _fmt_rank(value: object) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return "-"
    return str(int(parsed))


def _repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
