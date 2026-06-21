#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from xml.etree import ElementTree

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    _select_old_trace_record,
)
from srs_learner_difficulty_proficiency_ordering_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_MATRIX,
    DEFAULT_COMPONENT_MATRIX,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_TRACE_JSON,
    _component_context,
    _escape,
    _load_json,
    _mapping,
    _normalized_values_for_trace_record,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_structured_failure_groups_en_ja import (  # noqa: E402
    _signal_arrays,
)


PAIR = "en-ja"
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_JMDICT_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "jmdict-ja-en"
    / "JMdict_e"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_pack_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_review_pack_en_ja_latest.md"
)
DEFAULT_REVIEW_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_shape_blind_review_en_ja.md"
)
DEFAULT_SAMPLE_PER_BUCKET = 15
DISPLAY_SIGNALS = (
    "frequency",
    "jmdict_priority",
    "jlpt_vocab_beginner_core",
    "kango_mid_signal",
    "wtype_kango_risk",
    "wtype_wago_ease",
    "max_written_form_burden",
    "written_form_burden",
    "max_kanji_burden",
    "kanji_burden",
    "non_standard_reading_risk",
    "rare_wago_tail_risk",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
)
REVIEW_STATES = frozenset({"normal_vocab"})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a blind review pack for source-visible residual-shape cells "
            "that looked promising but are not yet promotion-safe."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--jmdict-path", type=Path, default=DEFAULT_JMDICT_PATH)
    parser.add_argument("--old-score-key", default="balanced_score")
    parser.add_argument("--sample-per-bucket", type=int, default=DEFAULT_SAMPLE_PER_BUCKET)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--review-markdown-out", type=Path, default=DEFAULT_REVIEW_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        component_matrix_path=_resolve_path(args.component_matrix),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        calibration_json_path=_resolve_path(args.calibration_json),
        holdout_json_path=_resolve_path(args.holdout_json),
        jmdict_path=Path(args.jmdict_path).expanduser(),
        old_score_key=str(args.old_score_key),
        sample_per_bucket=max(1, int(args.sample_per_bucket)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    review_markdown_out = _resolve_path(args.review_markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    review_markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_diagnostic_markdown(report), encoding="utf-8")
    review_markdown_out.write_text(render_blind_review_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote blind review Markdown artifact to {review_markdown_out}")
    return 0


def build_report(
    *,
    trace_json: Path,
    component_matrix_path: Path,
    calibration_matrix_path: Path,
    calibration_json_path: Path,
    holdout_json_path: Path,
    jmdict_path: Path,
    old_score_key: str,
    sample_per_bucket: int,
) -> dict[str, object]:
    trace = _load_json(trace_json)
    component = np.load(component_matrix_path)
    component_context = _component_context(component)
    old_record = _select_old_trace_record(trace, score_key=old_score_key)
    old_values = np.asarray(
        _normalized_values_for_trace_record(old_record, component_context),
        dtype=np.float32,
    )
    signal_arrays = _signal_arrays(component_context)
    blocked = _blocked_labels(
        _load_json(calibration_json_path),
        _load_json(holdout_json_path),
    )
    buckets = _review_bucket_specs()
    selected_rows = _select_rows(
        component=component,
        component_context=component_context,
        signal_arrays=signal_arrays,
        old_values=old_values,
        blocked=blocked,
        buckets=buckets,
        sample_per_bucket=sample_per_bucket,
    )
    gloss_lookup = _jmdict_lookup(
        jmdict_path,
        keys={(str(row["lemma"]), str(row["reading"])) for row in selected_rows},
    )
    rows = [_review_row(row, gloss_lookup=gloss_lookup) for row in selected_rows]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "holdout_used_for_selection": False,
        "review_surface_blind": True,
        "method": {
            "purpose": (
                "Create fresh human-review candidates for the residual-shape cells "
                "where mid/high written, kanji, and kango burden may be misordered."
            ),
            "blind_review_policy": (
                "The reviewer-facing Markdown omits old scores, residual direction, "
                "calibration deltas, holdout deltas, and suggested correction signs. "
                "It shows identity, short JMDict context, candidate state, problem "
                "class, and source signals only."
            ),
            "selection_policy": (
                "Rows are selected from source-visible bucket masks and old-score "
                "bands, excluding existing calibration and holdout labels. This pack "
                "is not a calibration file until reviewed values are manually promoted."
            ),
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "jmdict_path": _repo_or_home_path(jmdict_path),
            "normalization_population_count": len(component_context.lemmas),
            "old_score_key": old_score_key,
            "sample_per_bucket": int(sample_per_bucket),
        },
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "component_matrix": component_matrix_path,
                "calibration_matrix": calibration_matrix_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "jmdict": jmdict_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "proficiency_ordering": SCRIPT_DIR
                / "srs_learner_difficulty_proficiency_ordering_en_ja.py",
                "structured_failure_groups": SCRIPT_DIR
                / "srs_learner_difficulty_structured_failure_groups_en_ja.py",
            },
            version_constants={},
            argv=sys.argv,
        ),
        "anchor_candidate": {
            "candidate_id": old_record.get("variant_id"),
            "selector": f"max:{old_score_key}",
            "weights": old_record.get("weights") or {},
        },
        "bucket_specs": [_public_bucket_spec(bucket) for bucket in buckets],
        "counts": {
            "selected_rows": len(rows),
            "by_bucket": _counts_by_key(rows, "review_bucket"),
            "existing_label_blocks": len(blocked["exact_keys"]) + len(blocked["lemma_blocks"]),
        },
        "review_rows": rows,
    }


def _review_bucket_specs() -> list[dict[str, object]]:
    return [
        {
            "review_bucket": "cell_a",
            "public_focus": "compound written-form burden",
            "terms": (
                ("wtype_kango_risk", 0.75, None),
                ("max_written_form_burden", 0.70, None),
            ),
            "old_band": (0.60, 0.80),
        },
        {
            "review_bucket": "cell_b",
            "public_focus": "mid/high written-form burden",
            "terms": (("max_written_form_burden", 0.50, None),),
            "old_band": (0.60, 0.80),
        },
        {
            "review_bucket": "cell_c",
            "public_focus": "mid/high kanji burden",
            "terms": (("kanji_burden", 0.25, None),),
            "old_band": (0.60, 0.80),
        },
        {
            "review_bucket": "cell_d",
            "public_focus": "upper written-form burden",
            "terms": (("max_written_form_burden", 0.90, None),),
            "old_band": (0.80, 1.00),
            "old_band_is_last": True,
        },
    ]


def _select_rows(
    *,
    component: object,
    component_context: object,
    signal_arrays: Mapping[str, object],
    old_values: object,
    blocked: Mapping[str, set[str]],
    buckets: Sequence[Mapping[str, object]],
    sample_per_bucket: int,
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    for bucket in buckets:
        bucket_rows = _bucket_candidates(
            component=component,
            component_context=component_context,
            signal_arrays=signal_arrays,
            old_values=old_values,
            blocked=blocked,
            bucket=bucket,
            seen=seen,
        )
        sampled = _spread_sample(bucket_rows, sample_per_bucket)
        for row in sampled:
            seen.add(str(row["label_key"]))
            selected.append(row)
    return selected


def _bucket_candidates(
    *,
    component: object,
    component_context: object,
    signal_arrays: Mapping[str, object],
    old_values: object,
    blocked: Mapping[str, set[str]],
    bucket: Mapping[str, object],
    seen: set[str],
) -> list[dict[str, object]]:
    old = np.asarray(old_values, dtype=np.float32)
    low, high = tuple(float(value) for value in bucket.get("old_band") or (0.0, 1.0))
    if bool(bucket.get("old_band_is_last")):
        mask = (old >= low) & (old <= high)
    else:
        mask = (old >= low) & (old < high)
    for signal, minimum, maximum in bucket.get("terms") or ():
        values = np.asarray(signal_arrays.get(str(signal), np.zeros(len(old))), dtype=np.float32)
        if minimum is not None:
            mask &= values >= float(minimum)
        if maximum is not None:
            mask &= values <= float(maximum)
    rows = []
    candidate_states = component_context.candidate_states
    problem_classes = [str(value) for value in component["problem_classes"]]
    core_ranks = np.asarray(component["core_ranks"], dtype=np.float32)
    for index in np.where(mask)[0]:
        lemma = str(component_context.lemmas[int(index)])
        reading = str(component_context.readings[int(index)])
        label_key = f"{lemma}\t{reading}"
        if label_key in seen or _is_blocked_label(lemma, reading, blocked):
            continue
        candidate_state = str(candidate_states[int(index)])
        if candidate_state not in REVIEW_STATES:
            continue
        rows.append(
            {
                "index": int(index),
                "review_bucket": str(bucket.get("review_bucket") or ""),
                "public_focus": str(bucket.get("public_focus") or ""),
                "candidate_identity_key": str(
                    component_context.candidate_identity_keys[int(index)]
                ),
                "label_key": label_key,
                "lemma": lemma,
                "reading": reading,
                "candidate_state": candidate_state,
                "problem_class": str(problem_classes[int(index)]),
                "core_rank": _rounded(_optional_float(core_ranks[int(index)])),
                "jlpt_vocab_level": _rounded(
                    _optional_index(component_context, "jlpt_vocab_levels", int(index))
                ),
                "signals": _display_signals(signal_arrays, int(index)),
                "_old_score": float(old[int(index)]),
                "_selection_strength": _selection_strength(bucket, signal_arrays, int(index)),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["_selection_strength"]),
            _none_as_large(row.get("core_rank")),
            str(row["lemma"]),
            str(row["reading"]),
        ),
    )


def _review_row(
    row: Mapping[str, object],
    *,
    gloss_lookup: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
    lexical = _mapping(gloss_lookup.get(key))
    return {
        "review_bucket": row.get("review_bucket"),
        "public_focus": row.get("public_focus"),
        "candidate_identity_key": row.get("candidate_identity_key"),
        "label_key": row.get("label_key"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "core_rank": row.get("core_rank"),
        "jlpt_vocab_level": row.get("jlpt_vocab_level"),
        "jmdict_glosses": lexical.get("glosses") or [],
        "jmdict_pos": lexical.get("pos") or [],
        "jmdict_fields": lexical.get("fields") or [],
        "jmdict_match": lexical.get("match") or "missing",
        "source_signals": row.get("signals") or {},
        "review_fields": {
            "expected_difficulty": "",
            "treatment": "",
            "notes": "",
        },
    }


def _public_bucket_spec(bucket: Mapping[str, object]) -> dict[str, object]:
    return {
        "review_bucket": bucket.get("review_bucket"),
        "public_focus": bucket.get("public_focus"),
        "sample_role": (
            "Human review candidates for checking whether this source-visible "
            "region belongs in its apparent proficiency band."
        ),
    }


def _blocked_labels(*payloads: Mapping[str, object]) -> dict[str, set[str]]:
    exact_keys: set[str] = set()
    lemma_blocks: set[str] = set()
    for payload in payloads:
        for row in payload.get("labels") or ():
            if not isinstance(row, Mapping):
                continue
            lemma = str(row.get("lemma") or "").strip()
            reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
            if not lemma:
                continue
            if reading:
                exact_keys.add(f"{lemma}\t{reading}")
            else:
                lemma_blocks.add(lemma)
    return {"exact_keys": exact_keys, "lemma_blocks": lemma_blocks}


def _is_blocked_label(
    lemma: str,
    reading: str,
    blocked: Mapping[str, set[str]],
) -> bool:
    return f"{lemma}\t{reading}" in blocked["exact_keys"] or str(lemma) in blocked["lemma_blocks"]


def _spread_sample(
    rows: Sequence[Mapping[str, object]],
    sample_count: int,
) -> list[Mapping[str, object]]:
    if len(rows) <= sample_count:
        return [dict(row) for row in rows]
    ordered = sorted(rows, key=lambda row: (float(row["_old_score"]), str(row["lemma"])))
    sampled = []
    used: set[int] = set()
    for index in range(sample_count):
        position = int(((index + 0.5) / sample_count) * len(ordered))
        position = min(len(ordered) - 1, max(0, position))
        while position in used and position + 1 < len(ordered):
            position += 1
        while position in used and position > 0:
            position -= 1
        used.add(position)
        sampled.append(dict(ordered[position]))
    return sampled


def _display_signals(
    signal_arrays: Mapping[str, object],
    index: int,
) -> dict[str, object]:
    signals = {}
    for name in DISPLAY_SIGNALS:
        values = signal_arrays.get(name)
        if values is None:
            continue
        value = _optional_float(np.asarray(values)[index])
        if value is not None and (name == "frequency" or abs(value) > 1e-9):
            signals[name] = _rounded(value)
    return signals


def _selection_strength(
    bucket: Mapping[str, object],
    signal_arrays: Mapping[str, object],
    index: int,
) -> float:
    values = []
    for signal, _minimum, _maximum in bucket.get("terms") or ():
        array = signal_arrays.get(str(signal))
        if array is not None:
            parsed = _optional_float(np.asarray(array)[index])
            if parsed is not None:
                values.append(parsed)
    return float(sum(values) / len(values)) if values else 0.0


def _jmdict_lookup(
    path: Path,
    *,
    keys: set[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, object]]:
    if not keys or not path.exists():
        return {}
    wanted_lemmas = {lemma for lemma, _reading in keys}
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for _event, elem in ElementTree.iterparse(path, events=("end",)):
        if elem.tag != "entry":
            continue
        kanji_forms = [node.text.strip() for node in elem.findall("k_ele/keb") if node.text]
        reading_forms = [node.text.strip() for node in elem.findall("r_ele/reb") if node.text]
        forms = set(kanji_forms) | set(reading_forms)
        if not forms & wanted_lemmas:
            elem.clear()
            continue
        glosses = _unique_limited(
            node.text.strip()
            for node in elem.findall("sense/gloss")
            if node.text and _is_english_gloss(node)
        )
        pos = _unique_limited(node.text.strip() for node in elem.findall("sense/pos") if node.text)
        fields = _unique_limited(
            node.text.strip() for node in elem.findall("sense/field") if node.text
        )
        payload = {
            "glosses": glosses[:6],
            "pos": pos[:4],
            "fields": fields[:4],
        }
        for lemma, reading in keys:
            if lemma not in forms:
                continue
            exact_match = not reading or reading in reading_forms or reading in forms
            match_payload = {
                **payload,
                "match": "exact_reading" if exact_match else "lemma_only",
            }
            existing = lookup.get((lemma, reading))
            if existing is None or _lexical_payload_is_better(match_payload, existing):
                lookup[(lemma, reading)] = match_payload
        elem.clear()
        if len(lookup) >= len(keys) and all(
            str(value.get("match") or "") == "exact_reading" for value in lookup.values()
        ):
            break
    return lookup


def _is_english_gloss(node: ElementTree.Element) -> bool:
    lang = (
        node.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
        or node.attrib.get("xml:lang")
        or node.attrib.get("lang")
        or ""
    )
    return lang in {"", "eng", "en"}


def _lexical_payload_is_better(
    candidate: Mapping[str, object],
    existing: Mapping[str, object],
) -> bool:
    candidate_glosses = candidate.get("glosses") or []
    existing_glosses = existing.get("glosses") or []
    candidate_pos = candidate.get("pos") or []
    existing_pos = existing.get("pos") or []
    candidate_match = _lexical_match_rank(candidate)
    existing_match = _lexical_match_rank(existing)
    if candidate_match != existing_match:
        return candidate_match > existing_match
    return (not existing_glosses and bool(candidate_glosses)) or (
        not existing_pos and bool(candidate_pos)
    )


def _lexical_match_rank(payload: Mapping[str, object]) -> int:
    match = str(payload.get("match") or "")
    if match == "exact_reading":
        return 2
    if match == "lemma_only":
        return 1
    return 0


def _unique_limited(values: object, *, limit: int = 24) -> list[str]:
    result = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def render_diagnostic_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    counts = _mapping(report.get("counts"))
    lines = [
        "# en-ja Residual-Shape Review Pack",
        "",
        "This is review-only material. It is not an accepted calibration set and no sweeps were run to create it.",
        "",
        "## Summary",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Reviewer-facing surface blind: `{_escape(report.get('review_surface_blind'))}`",
        f"- Selected rows: `{_escape(counts.get('selected_rows'))}`",
        f"- Sample per bucket: `{_escape(inputs.get('sample_per_bucket'))}`",
        f"- Existing label blocks: `{_escape(counts.get('existing_label_blocks'))}`",
        "",
        "## Buckets",
        "",
        "| Bucket | Focus | Count |",
        "| --- | --- | ---: |",
    ]
    by_bucket = _mapping(counts.get("by_bucket"))
    for bucket in report.get("bucket_specs") or ():
        row = _mapping(bucket)
        bucket_id = str(row.get("review_bucket") or "")
        lines.append(
            "| "
            f"`{_escape(bucket_id)}` | "
            f"{_escape(row.get('public_focus'))} | "
            f"`{_escape(by_bucket.get(bucket_id))}` |"
        )
    lines.extend(
        [
            "",
            "## Reviewer Table",
            "",
            _review_table(report.get("review_rows") or ()),
            "",
        ]
    )
    return "\n".join(lines)


def render_blind_review_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-ja targeted learner difficulty blind review",
        "",
        (
            "Fill `expected_difficulty` with a `0.00`-`1.00` value when the row "
            "should be admitted as vocabulary. Use `treatment` for non-vocab "
            "decisions such as `omit`, `topic_only`, `pattern`, or `unsure`."
        ),
        "",
        (
            "This table intentionally omits model scores, model-error direction, "
            "and suggested correction signs."
        ),
        "",
        _review_table(report.get("review_rows") or ()),
        "",
    ]
    return "\n".join(lines)


def _review_table(rows: Sequence[Mapping[str, object]]) -> str:
    header = (
        "| # | bucket | lemma | reading | gloss | pos | jmdict match | state | class | jlpt | source signals | expected_difficulty | treatment | notes |\n"
        "|---:|---|---|---|---|---|---|---|---|---:|---|---:|---|---|"
    )
    body = []
    for index, row in enumerate(rows, start=1):
        body.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _escape(str(row.get("review_bucket") or "")),
                    _escape(str(row.get("lemma") or "")),
                    _escape(str(row.get("reading") or "")),
                    _escape("; ".join(str(value) for value in row.get("jmdict_glosses") or ())),
                    _escape("; ".join(str(value) for value in row.get("jmdict_pos") or ())),
                    _escape(str(row.get("jmdict_match") or "")),
                    _escape(str(row.get("candidate_state") or "")),
                    _escape(str(row.get("problem_class") or "")),
                    _escape(row.get("jlpt_vocab_level")),
                    _escape(_compact_signals(_mapping(row.get("source_signals")))),
                    "",
                    "",
                    "",
                ]
            )
            + " |"
        )
    return "\n".join([header, *body])


def _compact_signals(signals: Mapping[str, object]) -> str:
    cells = []
    for key in DISPLAY_SIGNALS:
        value = signals.get(key)
        if value not in (None, 0, 0.0, ""):
            cells.append(f"{key}={value}")
    return "; ".join(cells)


def _counts_by_key(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _optional_index(context: object, field: str, index: int) -> float | None:
    values = getattr(context, field, None)
    if values is None:
        return None
    return _optional_float(np.asarray(values)[index])


def _none_as_large(value: object) -> float:
    parsed = _optional_float(value)
    return 1_000_000_000.0 if parsed is None else parsed


if __name__ == "__main__":
    raise SystemExit(main())
