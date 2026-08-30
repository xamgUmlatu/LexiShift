#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_acceptance_review_pack_en_ja import (  # noqa: E402
    DEFAULT_VALIDATION_EVAL_JSON,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_COMPONENT_MATRIX,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_qualitative_failure_hypotheses_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_qualitative_failure_hypotheses_en_ja_latest.md"
)
ANCHOR_MODEL = "ordinary_cap"
SELECTED_SIGNALS = (
    "frequency",
    "frequency_unranked_risk",
    "jmdict_priority",
    "jlpt_vocab_difficulty",
    "lesson_vocab_difficulty",
    "max_written_form_burden",
    "max_kanji_burden",
    "rare_non_standard_reading_risk",
    "non_standard_reading_risk",
    "rare_wago_tail_risk",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "jmdict_loanword_source_risk",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
    "jmdict_reading_form_marked_risk",
    "candidate_deprioritized_vocab_risk",
    "named_entity_risk",
    "acronym_surface_confidence",
)


@dataclass(frozen=True)
class MatrixView:
    lemmas: list[str]
    readings: list[str]
    candidate_states: list[str]
    problem_classes: list[str]
    core_ranks: np.ndarray
    component_names: list[str]
    component_values: np.ndarray

    @classmethod
    def from_npz(cls, payload: object) -> MatrixView:
        return cls(
            lemmas=[str(value) for value in payload["lemmas"]],
            readings=[str(value) for value in payload["readings"]],
            candidate_states=[str(value) for value in payload["candidate_states"]],
            problem_classes=[str(value) for value in payload["problem_classes"]],
            core_ranks=np.asarray(payload["core_ranks"], dtype=np.float32),
            component_names=[str(value) for value in payload["component_names"]],
            component_values=np.asarray(payload["component_values"], dtype=np.float32),
        )

    def row_index_by_pair(self) -> dict[tuple[str, str], int]:
        return {
            (lemma, reading): index
            for index, (lemma, reading) in enumerate(zip(self.lemmas, self.readings))
        }

    def component_index(self) -> dict[str, int]:
        return {name: index for index, name in enumerate(self.component_names)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a qualitative failure-hypothesis workbench for the latest "
            "en-ja learner-difficulty validation errors."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--validation-eval-json", type=Path, default=DEFAULT_VALIDATION_EVAL_JSON)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        validation_eval_json_path=_resolve_path(args.validation_eval_json),
        anchor_model=str(args.anchor_model),
        detail_limit=max(1, int(args.detail_limit)),
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
    component_matrix_path: Path,
    validation_eval_json_path: Path,
    anchor_model: str,
    detail_limit: int,
) -> dict[str, object]:
    matrix = MatrixView.from_npz(np.load(component_matrix_path))
    validation_eval = _load_json(validation_eval_json_path)
    rows = [
        error_row_with_signals(row, matrix=matrix, anchor_model=anchor_model)
        for row in validation_largest_errors(
            validation_eval, anchor_model=anchor_model, detail_limit=detail_limit
        )
    ]
    rows = [row for row in rows if row]
    grouped = group_rows(rows)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "purpose": (
            "Qualitative workbench for converting visible validation failures "
            "into source-computable model hypotheses."
        ),
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "validation_eval_json": _repo_or_home_path(validation_eval_json_path),
            "anchor_model": anchor_model,
            "selected_signals": list(SELECTED_SIGNALS),
            "detail_limit": detail_limit,
        },
        "rows": rows,
        "groups": grouped,
        "hypotheses": hypothesis_summaries(grouped),
        "recommended_analysis_order": recommended_analysis_order(),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "validation_eval_json": validation_eval_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "qualitative_failure_hypotheses": Path(__file__),
                "acceptance_review_pack": SCRIPT_DIR
                / "srs_learner_difficulty_acceptance_review_pack_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def validation_largest_errors(
    validation_eval: Mapping[str, object],
    *,
    anchor_model: str,
    detail_limit: int,
) -> list[Mapping[str, object]]:
    model = _mapping(_mapping(validation_eval.get("results")).get(anchor_model))
    return _rows(model.get("largest_errors"))[:detail_limit]


def error_row_with_signals(
    row: Mapping[str, object],
    *,
    matrix: MatrixView,
    anchor_model: str,
) -> dict[str, object]:
    label = str(row.get("label", ""))
    if "/" not in label:
        return {}
    lemma, reading = label.split("/", 1)
    index = matrix.row_index_by_pair().get((lemma, reading))
    if index is None:
        return {}
    signals = signal_snapshot(index, matrix=matrix)
    model_payload = {
        "label": label,
        "lemma": lemma,
        "reading": reading,
        "expected": _rounded(_optional_float(row.get("expected"))),
        "observed": _rounded(_optional_float(row.get("observed"))),
        "absolute_error": _rounded(_optional_float(row.get("absolute_error"))),
        "direction": str(row.get("direction")),
        "anchor_model": anchor_model,
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(float(matrix.core_ranks[index])),
        "signals": signals,
    }
    hypothesis = classify_failure(model_payload)
    return model_payload | hypothesis


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    snapshot: dict[str, object] = {}
    for signal in SELECTED_SIGNALS:
        column = component_index.get(signal)
        if column is None:
            snapshot[signal] = None
        else:
            value = float(matrix.component_values[index, column])
            snapshot[signal] = _rounded(value)
    return snapshot


def classify_failure(row: Mapping[str, object]) -> dict[str, object]:
    signals = _mapping(row.get("signals"))
    direction = str(row.get("direction"))
    state = str(row.get("candidate_state"))
    gairaigo = _float_signal(signals, "wtype_gairaigo_risk")
    wago = _float_signal(signals, "wtype_wago_ease")
    kango = _float_signal(signals, "wtype_kango_risk")
    rare_wago = _float_signal(signals, "rare_wago_tail_risk")
    rare_reading = _float_signal(signals, "rare_non_standard_reading_risk")
    nonstandard = _float_signal(signals, "non_standard_reading_risk")
    marked = max(
        _float_signal(signals, "jmdict_marked_usage_risk"),
        _float_signal(signals, "jmdict_reading_form_marked_risk"),
        _float_signal(signals, "jmdict_register_marked_risk"),
    )
    entity = _float_signal(signals, "named_entity_risk")
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    if state != "normal_vocab":
        return {
            "hypothesis_id": "admission_or_source_lane",
            "fix_direction": "route_or_review_before_scalar",
            "computability": "high",
            "rationale": "Candidate is already outside the normal-vocab lane.",
        }
    if direction == "too_low" and gairaigo >= 0.75 and frequency >= 0.8:
        return {
            "hypothesis_id": "rare_or_domain_gairaigo_too_early",
            "fix_direction": "bounded_upshift",
            "computability": "medium_high",
            "rationale": (
                "Katakana/gairaigo row with weak exposure is placed too early; "
                "a rarity-gated loanword floor is directly computable."
            ),
        }
    if direction == "too_high" and wago >= 0.75 and rare_wago >= 0.5:
        return {
            "hypothesis_id": "transparent_wago_tail_too_late",
            "fix_direction": "bounded_downshift_or_needs_signal",
            "computability": "low_medium",
            "rationale": (
                "Wago/compound tail pressure fires, but labels suggest the item "
                "is more transparent or ordinary than the signals know."
            ),
        }
    if direction == "too_low" and kango >= 0.75 and marked >= 0.5:
        return {
            "hypothesis_id": "marked_kango_or_reading_too_early",
            "fix_direction": "bounded_upshift",
            "computability": "medium",
            "rationale": (
                "Kango or kanji-heavy row has marked reading/usage evidence but "
                "the anchor leaves it too early."
            ),
        }
    if direction == "too_low" and (nonstandard >= 0.75 or rare_reading >= 0.5):
        return {
            "hypothesis_id": "reading_specific_item_too_early",
            "fix_direction": "bounded_upshift",
            "computability": "medium",
            "rationale": (
                "Reading-specific difficulty is visible, but the model does not "
                "raise the row enough."
            ),
        }
    if direction == "too_high" and rare_reading >= 0.5:
        return {
            "hypothesis_id": "reading_tail_over_penalty",
            "fix_direction": "bounded_downshift_or_needs_signal",
            "computability": "low_medium",
            "rationale": (
                "Rare-reading/tail risk may be over-penalizing an otherwise recognizable item."
            ),
        }
    if direction == "too_low" and entity >= 0.5 and unranked >= 0.5:
        return {
            "hypothesis_id": "entity_or_name_like_too_early",
            "fix_direction": "route_or_bounded_upshift",
            "computability": "medium",
            "rationale": (
                "Name/entity overlap and missing frequency point to a possible "
                "lane issue or late-placement correction."
            ),
        }
    return {
        "hypothesis_id": "unclassified_or_underidentified",
        "fix_direction": "manual_review",
        "computability": "unknown",
        "rationale": "The selected source signals do not cleanly explain the error.",
    }


def group_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("hypothesis_id")), []).append(row)
    return {
        group_id: {
            "count": len(group_rows),
            "rows": list(group_rows),
        }
        for group_id, group_rows in sorted(grouped.items())
    }


def hypothesis_summaries(groups: Mapping[str, object]) -> list[dict[str, object]]:
    definitions = {
        "rare_or_domain_gairaigo_too_early": {
            "question": (
                "Should rare/domain katakana loanwords get a bounded late floor "
                "when they lack pedagogical/commonness protection?"
            ),
            "possible_predicate": (
                "wtype_gairaigo_risk high AND frequency high AND weak pedagogy; "
                "optionally require anchor score below the expected domain band."
            ),
            "risk": (
                "Common loanwords such as camera/schedule must remain protected; "
                "a blunt katakana penalty would be wrong."
            ),
        },
        "transparent_wago_tail_too_late": {
            "question": (
                "Can we distinguish rare-but-transparent native compounds from "
                "genuinely obscure wago tail rows?"
            ),
            "possible_predicate": (
                "Current matrix sees wago and rare-tail risk, but does not expose "
                "semantic transparency directly."
            ),
            "risk": (
                "This may require new labels or a constituent/common-morpheme "
                "signal before it is safe to correct."
            ),
        },
        "marked_kango_or_reading_too_early": {
            "question": (
                "Should marked usage/reading evidence override commonness for a "
                "small set of kango or kanji-heavy readings?"
            ),
            "possible_predicate": (
                "wtype_kango_risk high AND marked-reading/usage risk high AND "
                "weak pedagogical evidence."
            ),
            "risk": (
                "Marked JMDict flags sometimes hit ordinary vocabulary, so this "
                "needs ordinary-vocab protection."
            ),
        },
        "reading_specific_item_too_early": {
            "question": (
                "Are alternate readings being treated like the easy/common reading "
                "of the same written form?"
            ),
            "possible_predicate": (
                "non_standard_reading_risk or reading_form_marked risk high, "
                "especially on single-kanji or multi-reading surfaces."
            ),
            "risk": (
                "The current source-pair work helps hygiene, but true reading "
                "familiarity may still be underidentified."
            ),
        },
        "reading_tail_over_penalty": {
            "question": (
                "Is rare-reading or tail pressure pushing recognizable native rows too late?"
            ),
            "possible_predicate": (
                "rare_non_standard_reading_risk high on wago/native rows, but "
                "without a direct transparency/common-morpheme signal."
            ),
            "risk": (
                "Likely overlaps with truly obscure native-tail vocabulary; review "
                "before using as an automatic downshift."
            ),
        },
        "admission_or_source_lane": {
            "question": "Should this row be reviewed or routed before scalar scoring?",
            "possible_predicate": "candidate_state is not normal_vocab.",
            "risk": "This improves hygiene, not scalar ordering.",
        },
        "unclassified_or_underidentified": {
            "question": (
                "Is this a real pattern, or does the current palette simply lack "
                "the necessary source?"
            ),
            "possible_predicate": "none yet",
            "risk": "Do not sweep this without a sharper predicate.",
        },
    }
    summaries: list[dict[str, object]] = []
    for group_id, payload in groups.items():
        row = definitions.get(str(group_id), definitions["unclassified_or_underidentified"])
        summaries.append(
            {"hypothesis_id": group_id, "count": _mapping(payload).get("count", 0)} | row
        )
    return summaries


def recommended_analysis_order() -> list[dict[str, object]]:
    return [
        {
            "rank": 1,
            "hypothesis_id": "rare_or_domain_gairaigo_too_early",
            "reason": (
                "Most directly computable and visible in fresh validation; test a "
                "small protected floor/upshift before touching wago."
            ),
        },
        {
            "rank": 2,
            "hypothesis_id": "reading_specific_item_too_early",
            "reason": (
                "Likely product-relevant, but may require better reading-specific "
                "knownness or source-pair detail."
            ),
        },
        {
            "rank": 3,
            "hypothesis_id": "transparent_wago_tail_too_late",
            "reason": (
                "Large qualitative issue, but current signals may not identify transparency safely."
            ),
        },
    ]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Qualitative Failure Hypotheses",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Anchor model: `{_escape(inputs.get('anchor_model'))}`",
        f"- Rows inspected: `{len(_rows(report.get('rows')))}`",
        "",
        "## Recommended Analysis Order",
        "",
    ]
    lines.extend(_analysis_order_table(_rows(report.get("recommended_analysis_order"))))
    lines.extend(["", "## Hypothesis Summary", ""])
    lines.extend(_hypothesis_table(_rows(report.get("hypotheses"))))
    lines.extend(["", "## Rows By Hypothesis", ""])
    for group_id, payload in _mapping(report.get("groups")).items():
        lines.append(f"### `{_escape(group_id)}`")
        lines.extend(_row_table(_rows(_mapping(payload).get("rows"))))
        lines.append("")
    lines.extend(["## Signal Legend", ""])
    lines.append(
        "Selected signals are normalized `0..1` component values from the latest "
        "component matrix. They are review clues, not raw source truth."
    )
    lines.append("")
    lines.append(", ".join(f"`{signal}`" for signal in SELECTED_SIGNALS))
    return "\n".join(lines).rstrip() + "\n"


def _analysis_order_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = ["| Rank | Hypothesis | Reason |", "| ---: | --- | --- |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("rank")),
                    f"`{_escape(row.get('hypothesis_id'))}`",
                    _escape(row.get("reason")),
                ]
            )
            + " |"
        )
    return lines


def _hypothesis_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Hypothesis | Count | Question | Possible predicate | Risk |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape(row.get('hypothesis_id'))}`",
                    _escape(row.get("count")),
                    _escape(row.get("question")),
                    _escape(row.get("possible_predicate")),
                    _escape(row.get("risk")),
                ]
            )
            + " |"
        )
    return lines


def _row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    headers = [
        "Label",
        "Expected",
        "Observed",
        "Err",
        "Dir",
        "Fix",
        "Computable",
        "Rank",
        "Freq",
        "Unranked",
        "JLPT",
        "Written",
        "WagoTail",
        "Wago",
        "Kango",
        "Gairaigo",
        "Marked",
        "Reading",
        "Entity",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        marked = max(
            _float_signal(signals, "jmdict_marked_usage_risk"),
            _float_signal(signals, "jmdict_reading_form_marked_risk"),
            _float_signal(signals, "jmdict_register_marked_risk"),
        )
        reading = max(
            _float_signal(signals, "non_standard_reading_risk"),
            _float_signal(signals, "rare_non_standard_reading_risk"),
        )
        values = [
            _escape(row.get("label")),
            _escape(row.get("expected")),
            _escape(row.get("observed")),
            _escape(row.get("absolute_error")),
            f"`{_escape(row.get('direction'))}`",
            f"`{_escape(row.get('fix_direction'))}`",
            f"`{_escape(row.get('computability'))}`",
            _escape(row.get("core_rank")),
            _escape(signals.get("frequency")),
            _escape(signals.get("frequency_unranked_risk")),
            _escape(signals.get("jlpt_vocab_difficulty")),
            _escape(signals.get("max_written_form_burden")),
            _escape(signals.get("rare_wago_tail_risk")),
            _escape(signals.get("wtype_wago_ease")),
            _escape(signals.get("wtype_kango_risk")),
            _escape(signals.get("wtype_gairaigo_risk")),
            _escape(_rounded(marked)),
            _escape(_rounded(reading)),
            _escape(signals.get("named_entity_risk")),
        ]
        lines.append("| " + " | ".join(str(value) for value in values) + " |")
    return lines


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = signals.get(signal)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _optional_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float("nan")


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
