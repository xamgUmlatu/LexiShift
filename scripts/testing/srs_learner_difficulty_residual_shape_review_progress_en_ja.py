#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    _escape,
    _load_json,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)


PAIR = "en-ja"
DEFAULT_REVIEW_PACK_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_pack_en_ja_latest.json"
)
DEFAULT_TRIAGE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_triage_en_ja_latest.json"
)
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_residual_shape_review_labels_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_progress_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_progress_en_ja_latest.md"
)
NEXT_BATCH_LIMIT = 16
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
ROUTE_ORDER = {
    "possible_overhard_general_vocab": 0,
    "tail_topic_or_omit_review": 1,
    "wago_form_policy_review": 2,
    "usage_register_policy_review": 3,
    "burden_shape_review": 4,
    "source_review_first": 5,
    "ordinary_shape_review": 6,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Join reviewed residual-shape labels back to the blind review pack and triage routes."
        )
    )
    parser.add_argument("--review-pack-json", type=Path, default=DEFAULT_REVIEW_PACK_JSON)
    parser.add_argument("--triage-json", type=Path, default=DEFAULT_TRIAGE_JSON)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--next-batch-limit", type=int, default=NEXT_BATCH_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        review_pack_path=_resolve_path(args.review_pack_json),
        triage_path=_resolve_path(args.triage_json),
        labels_path=_resolve_path(args.labels_json),
        next_batch_limit=max(1, int(args.next_batch_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
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
    review_pack_path: Path,
    triage_path: Path,
    labels_path: Path,
    next_batch_limit: int,
) -> dict[str, object]:
    review_pack = _load_json(review_pack_path)
    triage = _load_json(triage_path)
    labels_payload = _load_json(labels_path)
    labels_by_key = _labels_by_key(labels_payload)
    triage_by_number = {
        int(row.get("row_number") or 0): _mapping(row)
        for row in triage.get("triage_rows") or ()
        if _optional_float(_mapping(row).get("row_number")) is not None
    }
    rows = []
    for row_number, review_row in enumerate(review_pack.get("review_rows") or (), start=1):
        pack_row = _mapping(review_row)
        key = _label_key(pack_row.get("lemma"), pack_row.get("reading"))
        label = _mapping(labels_by_key.get(key))
        triage_row = _mapping(triage_by_number.get(row_number))
        rows.append(_progress_row(row_number, pack_row, triage_row, label))
    reviewed_rows = [row for row in rows if row["review_status"] == "reviewed"]
    remaining_rows = [row for row in rows if row["review_status"] != "reviewed"]
    next_batch = sorted(
        remaining_rows,
        key=lambda row: (
            PRIORITY_ORDER.get(str(row.get("review_priority") or ""), 99),
            ROUTE_ORDER.get(str(row.get("review_route") or ""), 99),
            int(row.get("row_number") or 0),
        ),
    )[:next_batch_limit]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "calibration_labels_changed": False,
        "method": {
            "purpose": (
                "Track partial human review progress over the residual-shape "
                "review pack without promoting rows into canonical calibration."
            ),
            "promotion_policy": (
                "Only rows with treatment `vocab` and expected_learner_difficulty "
                "are numeric calibration candidates. Topic/source-policy rows "
                "should inform admission or source normalization first."
            ),
        },
        "inputs": {
            "review_pack_json": _repo_or_home_path(review_pack_path),
            "triage_json": _repo_or_home_path(triage_path),
            "labels_json": _repo_or_home_path(labels_path),
            "review_pack_rows": len(rows),
            "label_rows": len(labels_payload.get("labels") or ()),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "review_pack_json": review_pack_path,
                "triage_json": triage_path,
                "labels_json": labels_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "review_pack": SCRIPT_DIR
                / "srs_learner_difficulty_residual_shape_review_pack_en_ja.py",
                "triage": SCRIPT_DIR
                / "srs_learner_difficulty_residual_shape_review_triage_en_ja.py",
            },
            version_constants={},
            argv=sys.argv,
        ),
        "counts": _counts(rows),
        "reviewed_rows": reviewed_rows,
        "remaining_rows": remaining_rows,
        "next_suggested_batch": next_batch,
    }


def _labels_by_key(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    labels = {}
    for row in payload.get("labels") or ():
        label = _mapping(row)
        key = _label_key(label.get("lemma"), label.get("expected_reading") or label.get("reading"))
        if key:
            labels[key] = label
    return labels


def _progress_row(
    row_number: int,
    pack_row: Mapping[str, object],
    triage_row: Mapping[str, object],
    label: Mapping[str, object],
) -> dict[str, object]:
    expected = _optional_float(label.get("expected_learner_difficulty"))
    reference = _optional_float(label.get("reference_difficulty"))
    return {
        "row_number": row_number,
        "review_status": "reviewed" if label else "unreviewed",
        "review_bucket": pack_row.get("review_bucket"),
        "lemma": pack_row.get("lemma"),
        "reading": pack_row.get("reading"),
        "gloss": "; ".join(str(value) for value in pack_row.get("jmdict_glosses") or ()),
        "review_route": triage_row.get("review_route"),
        "review_priority": triage_row.get("review_priority"),
        "treatment": label.get("treatment"),
        "expected_learner_difficulty": _rounded(expected),
        "reference_difficulty": _rounded(reference),
        "expected_candidate_state": label.get("expected_candidate_state"),
        "expected_problem_class": label.get("expected_problem_class"),
        "rationale": label.get("rationale"),
        "promotion_candidate": (
            label.get("treatment") == "vocab"
            and expected is not None
            and label.get("expected_candidate_state") == "normal_vocab"
        ),
    }


def _counts(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    reviewed = [row for row in rows if row.get("review_status") == "reviewed"]
    remaining = [row for row in rows if row.get("review_status") != "reviewed"]
    by_treatment = Counter(str(row.get("treatment") or "") for row in reviewed)
    by_remaining_route = Counter(str(row.get("review_route") or "") for row in remaining)
    by_reviewed_route = Counter(str(row.get("review_route") or "") for row in reviewed)
    numeric = [
        row
        for row in reviewed
        if row.get("promotion_candidate")
        and _optional_float(row.get("expected_learner_difficulty")) is not None
    ]
    return {
        "total_rows": len(rows),
        "reviewed_rows": len(reviewed),
        "remaining_rows": len(remaining),
        "numeric_vocab_labels": len(numeric),
        "policy_or_source_labels": len(reviewed) - len(numeric),
        "by_treatment": dict(sorted(by_treatment.items())),
        "reviewed_by_route": dict(sorted(by_reviewed_route.items())),
        "remaining_by_route": dict(sorted(by_remaining_route.items())),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    counts = _mapping(report.get("counts"))
    lines = [
        "# en-ja Residual-Shape Review Progress",
        "",
        (
            "This is a progress tracker for labels gathered from the residual-shape "
            "review pack. It does not promote labels into the canonical calibration "
            "set by itself."
        ),
        "",
        "## Summary",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Reviewed rows: `{_escape(counts.get('reviewed_rows'))}` / `{_escape(counts.get('total_rows'))}`",
        f"- Numeric vocab labels: `{_escape(counts.get('numeric_vocab_labels'))}`",
        f"- Policy/source labels: `{_escape(counts.get('policy_or_source_labels'))}`",
        f"- Remaining rows: `{_escape(counts.get('remaining_rows'))}`",
        "- Canonical calibration changed: `False`",
        "",
        "## Treatment Counts",
        "",
        "| Treatment | Count |",
        "| --- | ---: |",
    ]
    for treatment, count in _mapping(counts.get("by_treatment")).items():
        lines.append(f"| `{_escape(treatment)}` | `{_escape(count)}` |")
    lines.extend(
        [
            "",
            "## Reviewed Rows",
            "",
            _rows_table(report.get("reviewed_rows") or (), include_label=True),
            "",
            "## Remaining By Route",
            "",
            "| Route | Count |",
            "| --- | ---: |",
        ]
    )
    for route, count in _mapping(counts.get("remaining_by_route")).items():
        lines.append(f"| `{_escape(route)}` | `{_escape(count)}` |")
    lines.extend(
        [
            "",
            "## Suggested Next Batch",
            "",
            _rows_table(report.get("next_suggested_batch") or (), include_label=False),
            "",
        ]
    )
    return "\n".join(lines)


def _rows_table(rows: Sequence[Mapping[str, object]], *, include_label: bool) -> str:
    if include_label:
        header = (
            "| # | word | route | treatment | difficulty | reference | rationale |\n"
            "|---:|---|---|---|---:|---:|---|"
        )
    else:
        header = "| # | word | route | priority | gloss |\n|---:|---|---|---|---|"
    body = []
    for row in rows:
        word = f"{row.get('lemma') or ''} / {row.get('reading') or ''}"
        if include_label:
            body.append(
                "| "
                + " | ".join(
                    [
                        _escape(row.get("row_number")),
                        _escape(word),
                        _escape(row.get("review_route")),
                        _escape(row.get("treatment")),
                        _escape(row.get("expected_learner_difficulty")),
                        _escape(row.get("reference_difficulty")),
                        _escape(row.get("rationale")),
                    ]
                )
                + " |"
            )
        else:
            body.append(
                "| "
                + " | ".join(
                    [
                        _escape(row.get("row_number")),
                        _escape(word),
                        _escape(row.get("review_route")),
                        _escape(row.get("review_priority")),
                        _escape(row.get("gloss")),
                    ]
                )
                + " |"
            )
    return "\n".join([header, *body])


def _label_key(lemma: object, reading: object) -> str:
    lemma_text = str(lemma or "").strip()
    reading_text = str(reading or "").strip()
    return f"{lemma_text}\t{reading_text}" if lemma_text else ""


if __name__ == "__main__":
    raise SystemExit(main())
