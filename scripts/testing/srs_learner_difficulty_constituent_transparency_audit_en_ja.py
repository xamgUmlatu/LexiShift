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
from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PAIR_JSON,
    component_lookup,
    row_component_index,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _utc_now,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
)
from srs_learner_difficulty_stitch_validation_eval_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    score_arrays_for_models,
)
from srs_learner_difficulty_transparent_wago_audit_en_ja import (  # noqa: E402
    DATASET_ORDER,
    ROW_SIGNALS,
    source_pair_review,
    surface_features,
    wago_tail,
)


PAIR = "en-ja"
ANCHOR_MODEL = "ordinary_cap"
FULL_MATRIX_CHANGE_CAP = 250
GUARD_SIGNALS = (
    "bccwj_domain_profile_risk",
    "common_register_domain_risk",
    "jmdict_field_marked_risk",
    "jmdict_marked_usage_risk",
    "jmdict_reading_form_marked_risk",
    "jmdict_register_domain_risk",
    "jmdict_register_marked_risk",
    "jmdict_sense_info_risk",
    "jmdict_sense_restricted_risk",
    "rare_wago_marked_usage_risk",
)
ALL_ROW_SIGNALS = tuple(dict.fromkeys((*ROW_SIGNALS, *GUARD_SIGNALS)))
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_audit_en_ja_latest.md"
)


@dataclass(frozen=True)
class MatrixSupport:
    component_names: tuple[str, ...]
    name_to_index: Mapping[str, int]
    values: np.ndarray
    present: np.ndarray
    current_values: np.ndarray
    lemmas: list[str]
    readings: list[str]
    candidate_states: list[str]
    problem_classes: list[str]
    core_ranks: np.ndarray

    @classmethod
    def from_npz(cls, payload: object) -> "MatrixSupport":
        names = tuple(str(value) for value in payload["component_names"])
        return cls(
            component_names=names,
            name_to_index={name: index for index, name in enumerate(names)},
            values=np.asarray(payload["component_values"], dtype=np.float32),
            present=np.asarray(payload["component_present"], dtype=bool),
            current_values=np.asarray(payload["current_values"], dtype=np.float32),
            lemmas=[str(value) for value in payload["lemmas"]],
            readings=[str(value) for value in payload["readings"]],
            candidate_states=[str(value) for value in payload["candidate_states"]],
            problem_classes=[str(value) for value in payload["problem_classes"]],
            core_ranks=np.asarray(payload["core_ranks"], dtype=np.float32),
        )

    def signal(self, index: int, name: str, *, fill: float = 0.0) -> float:
        column = self.name_to_index.get(name)
        if column is None or not bool(self.present[index, column]):
            return fill
        return float(self.values[index, column])

    def signal_present(self, index: int, name: str) -> bool:
        column = self.name_to_index.get(name)
        return column is not None and bool(self.present[index, column])


@dataclass(frozen=True)
class ConstituentProfile:
    lemma: str
    reading: str
    index: int
    knownness: float
    knownness_no_priority: float
    source_flags: tuple[str, ...]


@dataclass(frozen=True)
class ChunkMatch:
    surface: str
    matched_lemma: str
    reading: str
    score: float
    match_type: str
    source_flags: tuple[str, ...]


@dataclass(frozen=True)
class TransparencySpec:
    spec_id: str
    family: str
    ceiling: float
    tail_min: float
    written_max: float
    coverage_min: float
    score_min: float
    min_known_min: float
    reading_min: float
    domain_risk_max: float
    protect_beginner_core: bool
    protect_source_pair_review: bool
    entity_max: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether source-backed constituent coverage can narrow the "
            "transparent rare-wago downshift problem."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--leaderboard-limit", type=int, default=30)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        anchor_model=str(args.anchor_model),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
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
    source_pair_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    leaderboard_limit: int,
    detail_limit: int,
) -> dict[str, object]:
    raw_component = np.load(component_matrix_path)
    matrix = MatrixSupport.from_npz(raw_component)
    component_view = ComponentView.from_npz(raw_component)
    score_arrays, resolved_ids = score_arrays_for_models(
        view=component_view,
        parts=family_parts(component_view),
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=None,
        cap_candidate_id=None,
        stitch_candidate_id=None,
    )
    if anchor_model not in score_arrays:
        raise ValueError(f"Unknown anchor model: {anchor_model}")
    anchor_scores = np.asarray(score_arrays[anchor_model], dtype=np.float32)
    inventory = build_constituent_inventory(matrix)
    source_pair = _load_json(source_pair_json_path)
    lookup = component_lookup(raw_component)
    scalar_rows = [
        row
        for row in source_pair.get("rows", ())
        if isinstance(row, Mapping) and row.get("target") == "scalar_vocab"
    ]
    labeled_rows = rows_with_transparency(
        scalar_rows,
        lookup=lookup,
        matrix=matrix,
        inventory=inventory,
        anchor_scores=anchor_scores,
    )
    full_rows = full_matrix_rows(
        matrix=matrix,
        inventory=inventory,
        anchor_scores=anchor_scores,
    )
    candidates = [candidate_report(labeled_rows, full_rows, spec) for spec in transparency_specs()]
    ranked = sorted(candidates, key=candidate_rank_key, reverse=True)
    best = next((row for row in ranked if row.get("passes_guardrails")), ranked[0])
    best_spec = spec_from_payload(_mapping(best.get("spec")))
    best_labeled_rows = adjusted_rows_for_spec(labeled_rows, best_spec)
    review_pack = full_matrix_review_pack(
        full_rows,
        best_spec,
        detail_limit=detail_limit,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": True,
        "method": {
            "purpose": (
                "Test whether existing source-backed constituent coverage can "
                "separate transparent native compounds from opaque rare wago."
            ),
            "anchor_model": anchor_model,
            "full_matrix_change_cap": FULL_MATRIX_CHANGE_CAP,
            "constituent_signal": constituent_signal_description(),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "anchor_model": anchor_model,
            "labeled_rows": len(labeled_rows),
            "full_matrix_rows": len(full_rows),
            "inventory_lemmas": len(inventory),
            **resolved_ids,
        },
        "candidate_space": candidate_space_summary(),
        "dataset_summary": dataset_summary(labeled_rows),
        "transparency_segments": transparency_segment_summary(labeled_rows),
        "summary": {
            "candidate_count": len(candidates),
            "best_candidate_id": best.get("candidate_id"),
            "best_passes_guardrails": best.get("passes_guardrails"),
            "best_labeled_passes_guardrails": best.get("labeled_passes_guardrails"),
            "best": best,
            "interpretation": interpretation(best),
        },
        "leaderboard": ranked[:leaderboard_limit],
        "labeled_transparent_rows": labeled_transparent_rows(
            labeled_rows,
            detail_limit=detail_limit,
        ),
        "best_changed_rows": changed_rows_by_dataset(
            best_labeled_rows,
            detail_limit=detail_limit,
        ),
        "best_regression_rows": regression_rows_by_dataset(
            best_labeled_rows,
            detail_limit=detail_limit,
        ),
        "review_pack": review_pack,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "source_pair_json": source_pair_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "constituent_transparency_audit": Path(__file__),
                "transparent_wago_audit": SCRIPT_DIR
                / "srs_learner_difficulty_transparent_wago_audit_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def build_constituent_inventory(
    matrix: MatrixSupport,
) -> dict[str, ConstituentProfile]:
    profiles: dict[str, ConstituentProfile] = {}
    for index, lemma in enumerate(matrix.lemmas):
        if matrix.candidate_states[index] != "normal_vocab":
            continue
        if matrix.problem_classes[index] != "normal_vocab":
            continue
        profile = constituent_profile(index, matrix=matrix)
        previous = profiles.get(lemma)
        if previous is None or profile.knownness > previous.knownness:
            profiles[lemma] = profile
    return profiles


def constituent_profile(index: int, *, matrix: MatrixSupport) -> ConstituentProfile:
    flags: list[str] = []
    ease_scores: list[float] = []
    no_priority_scores: list[float] = []

    if matrix.signal_present(index, "frequency"):
        frequency_ease = 1.0 - matrix.signal(index, "frequency", fill=1.0)
        ease_scores.append(frequency_ease)
        no_priority_scores.append(frequency_ease)
        if frequency_ease >= 0.25:
            flags.append("frequency_common")

    if matrix.signal_present(index, "jlpt_vocab_difficulty"):
        jlpt_ease = 1.0 - matrix.signal(index, "jlpt_vocab_difficulty", fill=1.0)
        ease_scores.append(jlpt_ease)
        no_priority_scores.append(jlpt_ease)
        flags.append("jlpt_vocab")

    if matrix.signal_present(index, "jlpt_vocab_beginner_core"):
        beginner = matrix.signal(index, "jlpt_vocab_beginner_core")
        ease_scores.append(beginner)
        no_priority_scores.append(beginner)
        if beginner > 0.0:
            flags.append("jlpt_beginner_core")

    if matrix.signal_present(index, "lesson_vocab_difficulty"):
        lesson_ease = 1.0 - matrix.signal(index, "lesson_vocab_difficulty", fill=1.0)
        ease_scores.append(lesson_ease)
        no_priority_scores.append(lesson_ease)
        flags.append("lesson_vocab")

    if matrix.signal_present(index, "lesson_vocab_beginner_core"):
        lesson_beginner = matrix.signal(index, "lesson_vocab_beginner_core")
        ease_scores.append(lesson_beginner)
        no_priority_scores.append(lesson_beginner)
        if lesson_beginner > 0.0:
            flags.append("lesson_beginner_core")

    if matrix.signal_present(index, "jmdict_priority"):
        priority_ease = 1.0 - matrix.signal(index, "jmdict_priority", fill=1.0)
        ease_scores.append(priority_ease)
        if priority_ease >= 0.5:
            flags.append("jmdict_priority")

    return ConstituentProfile(
        lemma=matrix.lemmas[index],
        reading=matrix.readings[index],
        index=index,
        knownness=_clamp(max(ease_scores, default=0.0)),
        knownness_no_priority=_clamp(max(no_priority_scores, default=0.0)),
        source_flags=tuple(sorted(set(flags))),
    )


def constituent_signal_description() -> dict[str, object]:
    return {
        "inventory": (
            "Existing normal-vocab matrix lemmas with normal problem class. "
            "The full lemma itself is excluded when segmenting a word."
        ),
        "knownness": (
            "Maximum ease from source-backed frequency, JLPT vocab, lesson vocab, "
            "beginner-core, and JMDict priority signals. Single-character chunks "
            "ignore JMDict priority to avoid overtrusting opaque kanji forms."
        ),
        "derivational_variants": (
            "Small Japanese morphology heuristic maps nominalized chunks such as "
            "乗り and 込み to supported matrix lemmas such as 乗る and 込む. "
            "These matches are marked separately in the review output."
        ),
        "transparency_score": ("coverage_ratio * mean_knownness * (0.75 + 0.25 * min_knownness)."),
        "reading_compositionality": (
            "Longest-common-subsequence overlap between the target reading and "
            "the concatenated chunk readings after kana normalization. This "
            "penalizes opaque spellings such as 紙魚/しみ and 水水母/みずくらげ."
        ),
        "bad_segmentation_guards": (
            "Automatic downshift is blocked for repeated kana chunks, one-kana "
            "chunks, and short all-kana chunks that usually indicate accidental "
            "segmentation rather than real morphemes."
        ),
        "domain_marked_guard": (
            "Existing JMDict/domain/marked-risk component signals are combined "
            "as a max risk and swept as a candidate threshold."
        ),
    }


def rows_with_transparency(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    matrix: MatrixSupport,
    inventory: Mapping[str, ConstituentProfile],
    anchor_scores: np.ndarray,
) -> list[dict[str, object]]:
    result = []
    for row in rows:
        expected = _optional_float(row.get("expected_learner_difficulty"))
        index = row_component_index(row, lookup)
        if expected is None or index is None:
            continue
        result.append(
            row_payload(
                index,
                matrix=matrix,
                inventory=inventory,
                anchor_scores=anchor_scores,
                dataset_id=row.get("dataset_id"),
                expected=expected,
                primary_pair_status=row.get("primary_pair_status"),
                label=row.get("label") or f"{row.get('lemma')}/{row.get('reading')}",
            )
        )
    return result


def full_matrix_rows(
    *,
    matrix: MatrixSupport,
    inventory: Mapping[str, ConstituentProfile],
    anchor_scores: np.ndarray,
) -> list[dict[str, object]]:
    rows = []
    for index, state in enumerate(matrix.candidate_states):
        if state != "normal_vocab":
            continue
        rows.append(
            row_payload(
                index,
                matrix=matrix,
                inventory=inventory,
                anchor_scores=anchor_scores,
                dataset_id="full_matrix",
                expected=None,
                primary_pair_status=None,
                label=f"{matrix.lemmas[index]}/{matrix.readings[index]}",
            )
        )
    return rows


def row_payload(
    index: int,
    *,
    matrix: MatrixSupport,
    inventory: Mapping[str, ConstituentProfile],
    anchor_scores: np.ndarray,
    dataset_id: object,
    expected: float | None,
    primary_pair_status: object,
    label: object,
) -> dict[str, object]:
    observed = float(anchor_scores[index])
    payload: dict[str, object] = {
        "dataset_id": dataset_id,
        "label": label,
        "lemma": matrix.lemmas[index],
        "reading": matrix.readings[index],
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(float(matrix.core_ranks[index])),
        "primary_pair_status": primary_pair_status,
        "anchor_observed": _rounded(observed),
        "signals": signal_snapshot(index, matrix=matrix),
        "surface_features": surface_features(matrix.lemmas[index]),
        "transparency": constituent_analysis(
            matrix.lemmas[index],
            matrix.readings[index],
            inventory,
        ),
    }
    if expected is not None:
        payload.update(
            {
                "expected": _rounded(expected),
                "expected_band": _difficulty_band(expected),
                "anchor_abs_error": _rounded(abs(expected - observed)),
                "anchor_direction": "too_low" if observed < expected else "too_high",
            }
        )
    payload["segments"] = segment_memberships(payload)
    return payload


def signal_snapshot(index: int, *, matrix: MatrixSupport) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for signal in ALL_ROW_SIGNALS:
        column = matrix.name_to_index.get(signal)
        snapshot[signal] = (
            None
            if column is None or not bool(matrix.present[index, column])
            else _rounded(float(matrix.values[index, column]))
        )
    return snapshot


def constituent_analysis(
    lemma: str,
    reading: str,
    inventory: Mapping[str, ConstituentProfile],
) -> dict[str, object]:
    best = best_constituent_path(lemma, inventory)
    covered = sum(len(chunk.surface) for chunk in best)
    weighted = sum(len(chunk.surface) * chunk.score for chunk in best)
    mean_known = weighted / covered if covered else 0.0
    min_known = min((chunk.score for chunk in best), default=0.0)
    coverage = covered / len(lemma) if lemma else 0.0
    score = coverage * mean_known * (0.75 + 0.25 * min_known)
    guard = transparency_guard(lemma=lemma, reading=reading, chunks=best, raw_score=score)
    return {
        "coverage_ratio": _rounded(coverage),
        "covered_chars": covered,
        "mean_knownness": _rounded(mean_known),
        "min_knownness": _rounded(min_known),
        "transparency_score": _rounded(score),
        "guarded_transparency_score": _rounded(guard["guarded_score"]),
        "reading_compositionality": _rounded(guard["reading_compositionality"]),
        "auto_downshift_eligible": guard["auto_downshift_eligible"],
        "guard_flags": guard["guard_flags"],
        "chunk_count": len(best),
        "chunks": [chunk_payload(chunk) for chunk in best],
    }


def transparency_guard(
    *,
    lemma: str,
    reading: str,
    chunks: Sequence[ChunkMatch],
    raw_score: float,
) -> dict[str, object]:
    flags = guard_flags(lemma=lemma, chunks=chunks)
    reading_score = reading_compositionality(chunks, reading)
    if reading_score < 0.67 and chunks:
        flags.append("reading_noncompositional")
    bad_segmentation = any(
        flag
        in {
            "repeated_kana_chunk",
            "one_kana_chunk",
            "short_kana_chunk",
            "derivational_short_kana_chunk",
        }
        for flag in flags
    )
    reading_factor = 0.25 + 0.75 * reading_score
    segmentation_factor = 0.35 if bad_segmentation else 1.0
    guarded_score = raw_score * reading_factor * segmentation_factor
    return {
        "guarded_score": _clamp(guarded_score),
        "reading_compositionality": _clamp(reading_score),
        "auto_downshift_eligible": chunks and not bad_segmentation and reading_score >= 0.67,
        "guard_flags": sorted(set(flags)),
    }


def guard_flags(*, lemma: str, chunks: Sequence[ChunkMatch]) -> list[str]:
    flags: list[str] = []
    surfaces = [chunk.surface for chunk in chunks]
    kana_surfaces = [surface for surface in surfaces if surface and is_kana_only(surface)]
    if len(set(kana_surfaces)) < len(kana_surfaces):
        flags.append("repeated_kana_chunk")
    if any(len(surface) == 1 and is_kana_only(surface) for surface in surfaces):
        flags.append("one_kana_chunk")
    if len(lemma) > 2 and any(
        1 < len(surface) <= 2 and is_kana_only(surface) for surface in surfaces
    ):
        flags.append("short_kana_chunk")
    if any(
        chunk.match_type == "derivational_variant"
        and len(chunk.surface) <= 2
        and is_kana_only(chunk.surface)
        for chunk in chunks
    ):
        flags.append("derivational_short_kana_chunk")
    return flags


def reading_compositionality(chunks: Sequence[ChunkMatch], target_reading: str) -> float:
    target = normalize_kana(target_reading)
    if not chunks or not target:
        return 0.0
    composed = normalize_kana("".join(chunk.reading for chunk in chunks))
    if not composed:
        return 0.0
    return _clamp(lcs_length(target, composed) / len(target))


def lcs_length(left: str, right: str) -> int:
    previous = [0] * (len(right) + 1)
    for left_char in left:
        current = [0]
        for index, right_char in enumerate(right, start=1):
            if left_char == right_char:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def normalize_kana(value: str) -> str:
    chars: list[str] = []
    for char in value:
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        elif char != "ー":
            chars.append(char)
    return "".join(chars)


def is_kana_only(value: str) -> bool:
    return bool(value) and all(is_hiragana(char) or is_katakana(char) for char in value)


def is_hiragana(char: str) -> bool:
    return "\u3040" <= char <= "\u309f"


def is_katakana(char: str) -> bool:
    return "\u30a0" <= char <= "\u30ff"


def best_constituent_path(
    lemma: str,
    inventory: Mapping[str, ConstituentProfile],
) -> list[ChunkMatch]:
    states: list[list[ChunkMatch] | None] = [None] * (len(lemma) + 1)
    states[0] = []
    for start in range(len(lemma)):
        current = states[start]
        if current is None:
            continue
        if better_path(current, states[start + 1], lemma):
            states[start + 1] = list(current)
        for end in range(start + 1, len(lemma) + 1):
            surface = lemma[start:end]
            if surface == lemma:
                continue
            match = best_chunk_match(surface, inventory)
            if match is None:
                continue
            proposed = [*current, match]
            if better_path(proposed, states[end], lemma):
                states[end] = proposed
    return states[-1] or []


def better_path(
    proposed: Sequence[ChunkMatch],
    existing: Sequence[ChunkMatch] | None,
    lemma: str,
) -> bool:
    if existing is None:
        return True
    return path_rank(proposed, lemma) > path_rank(existing, lemma)


def path_rank(path: Sequence[ChunkMatch], lemma: str) -> tuple[float, float, float, float]:
    covered = sum(len(chunk.surface) for chunk in path)
    weighted = sum(len(chunk.surface) * chunk.score for chunk in path)
    mean = weighted / covered if covered else 0.0
    minimum = min((chunk.score for chunk in path), default=0.0)
    score = (covered / len(lemma) if lemma else 0.0) * mean
    return (covered, score, minimum, -float(len(path)))


def best_chunk_match(
    surface: str,
    inventory: Mapping[str, ConstituentProfile],
) -> ChunkMatch | None:
    matches = exact_chunk_matches(surface, inventory)
    matches.extend(variant_chunk_matches(surface, inventory))
    if not matches:
        return None
    return max(matches, key=lambda match: (match.score, len(match.surface)))


def exact_chunk_matches(
    surface: str,
    inventory: Mapping[str, ConstituentProfile],
) -> list[ChunkMatch]:
    profile = inventory.get(surface)
    if profile is None:
        return []
    score = profile.knownness_no_priority if len(surface) == 1 else profile.knownness
    return [
        ChunkMatch(
            surface=surface,
            matched_lemma=profile.lemma,
            reading=profile.reading,
            score=_clamp(score),
            match_type="exact_matrix_lemma",
            source_flags=profile.source_flags,
        )
    ]


def variant_chunk_matches(
    surface: str,
    inventory: Mapping[str, ConstituentProfile],
) -> list[ChunkMatch]:
    matches = []
    for variant in derivational_variants(surface):
        profile = inventory.get(variant)
        if profile is None:
            continue
        matches.append(
            ChunkMatch(
                surface=surface,
                matched_lemma=profile.lemma,
                reading=profile.reading,
                score=_clamp(profile.knownness * 0.92),
                match_type="derivational_variant",
                source_flags=profile.source_flags,
            )
        )
    return matches


def derivational_variants(surface: str) -> list[str]:
    variants: list[str] = []
    replacements = {
        "い": "う",
        "き": "く",
        "ぎ": "ぐ",
        "し": "す",
        "ち": "つ",
        "び": "ぶ",
        "み": "む",
        "り": "る",
    }
    if len(surface) >= 2:
        replacement = replacements.get(surface[-1])
        if replacement is not None:
            variants.append(surface[:-1] + replacement)
        if surface[-1] in {"け", "げ", "め"}:
            variants.append(surface + "る")
    return sorted(set(variants))


def chunk_payload(chunk: ChunkMatch) -> dict[str, object]:
    return {
        "surface": chunk.surface,
        "matched_lemma": chunk.matched_lemma,
        "reading": chunk.reading,
        "score": _rounded(chunk.score),
        "match_type": chunk.match_type,
        "source_flags": list(chunk.source_flags),
    }


def segment_memberships(row: Mapping[str, object]) -> list[str]:
    transparency = _mapping(row.get("transparency"))
    segments: list[str] = []
    if wago_tail(row):
        segments.append("wago_tail_any")
    if transparent_wago_failure(row):
        segments.append("transparent_wago_failure")
    if broad_low_written_proxy(row):
        segments.append("broad_low_written_proxy")
    if float(transparency.get("coverage_ratio") or 0.0) >= 0.67:
        segments.append("constituent_covered")
    if float(transparency.get("transparency_score") or 0.0) >= 0.35:
        segments.append("constituent_transparent")
    if float(transparency.get("guarded_transparency_score") or 0.0) >= 0.35:
        segments.append("guarded_constituent_transparent")
    if "reading_noncompositional" in _sequence(transparency.get("guard_flags")):
        segments.append("reading_noncompositional")
    if any(
        flag
        in {
            "repeated_kana_chunk",
            "one_kana_chunk",
            "short_kana_chunk",
            "derivational_short_kana_chunk",
        }
        for flag in _sequence(transparency.get("guard_flags"))
    ):
        segments.append("bad_segmentation_guard")
    if has_derivational_variant(row):
        segments.append("derivational_variant_match")
    if source_pair_review(row):
        segments.append("source_pair_review")
    return segments


def transparent_wago_failure(row: Mapping[str, object]) -> bool:
    return (
        wago_tail(row)
        and row.get("anchor_direction") == "too_high"
        and float(row.get("anchor_abs_error") or 0.0) >= 0.12
    )


def broad_low_written_proxy(row: Mapping[str, object]) -> bool:
    signals = _mapping(row.get("signals"))
    return (
        wago_tail(row)
        and not source_pair_review(row)
        and not beginner_core(row)
        and _float_signal(signals, "rare_wago_tail_risk") >= 0.5
        and _float_signal(signals, "max_written_form_burden") <= 0.45
        and _float_signal(signals, "named_entity_risk") <= 0.95
    )


def has_derivational_variant(row: Mapping[str, object]) -> bool:
    chunks = _sequence(_mapping(row.get("transparency")).get("chunks"))
    return any(_mapping(chunk).get("match_type") == "derivational_variant" for chunk in chunks)


def beginner_core(row: Mapping[str, object]) -> bool:
    signals = _mapping(row.get("signals"))
    return (
        max(
            _float_signal(signals, "jlpt_vocab_beginner_core"),
            _float_signal(signals, "lesson_vocab_beginner_core"),
        )
        >= 0.1
    )


def transparency_specs() -> list[TransparencySpec]:
    specs: list[TransparencySpec] = []
    for tail_min in (0.5, 0.75, 0.85):
        for written_max in (0.45, 0.55):
            for coverage_min in (0.67, 1.0):
                for score_min in (0.35, 0.45, 0.55):
                    for min_known_min in (0.0, 0.2):
                        for reading_min in (0.67, 0.8):
                            for domain_risk_max in (0.75, 1.01):
                                specs.append(
                                    TransparencySpec(
                                        spec_id=spec_id(
                                            tail_min=tail_min,
                                            written_max=written_max,
                                            coverage_min=coverage_min,
                                            score_min=score_min,
                                            min_known_min=min_known_min,
                                            reading_min=reading_min,
                                            domain_risk_max=domain_risk_max,
                                        ),
                                        family="low_written",
                                        ceiling=0.74,
                                        tail_min=tail_min,
                                        written_max=written_max,
                                        coverage_min=coverage_min,
                                        score_min=score_min,
                                        min_known_min=min_known_min,
                                        reading_min=reading_min,
                                        domain_risk_max=domain_risk_max,
                                        protect_beginner_core=True,
                                        protect_source_pair_review=True,
                                        entity_max=0.95,
                                    )
                                )
    return specs


def spec_id(
    *,
    tail_min: float,
    written_max: float,
    coverage_min: float,
    score_min: float,
    min_known_min: float,
    reading_min: float,
    domain_risk_max: float,
) -> str:
    return (
        f"ctrans_guard_low_written_t{id_float(tail_min)}_w{id_float(written_max)}"
        f"_cov{id_float(coverage_min)}_s{id_float(score_min)}"
        f"_mk{id_float(min_known_min)}_r{id_float(reading_min)}"
        f"_d{id_float(domain_risk_max)}"
    )


def id_float(value: float) -> str:
    return f"{value:.2f}".replace("0.", "").replace(".", "p")


def candidate_report(
    rows: Sequence[Mapping[str, object]],
    full_rows: Sequence[Mapping[str, object]],
    spec: TransparencySpec,
) -> dict[str, object]:
    adjusted = adjusted_rows_for_spec(rows, spec)
    datasets = {
        dataset_id: curve_result([row for row in adjusted if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    full_counts = full_matrix_counts(full_rows, spec)
    labeled_passes = labeled_passes_guardrails(datasets)
    return {
        "candidate_id": spec.spec_id,
        "spec": spec_payload(spec),
        "labeled_passes_guardrails": labeled_passes,
        "passes_guardrails": labeled_passes
        and int(full_counts.get("would_change_count") or 0) <= FULL_MATRIX_CHANGE_CAP,
        "datasets": datasets,
        "full_matrix": full_counts,
        "summary": candidate_summary(datasets, full_counts),
    }


def adjusted_rows_for_spec(
    rows: Sequence[Mapping[str, object]],
    spec: TransparencySpec,
) -> list[dict[str, object]]:
    return [dict(row) | adjusted_payload(row, spec) for row in rows]


def adjusted_payload(
    row: Mapping[str, object],
    spec: TransparencySpec,
) -> dict[str, object]:
    observed = _float_or_nan(row.get("anchor_observed"))
    expected = _optional_float(row.get("expected"))
    ceiling = spec.ceiling if policy_matches(row, spec) else None
    adjusted = observed if ceiling is None else min(observed, ceiling)
    payload = {
        "adjusted_observed": _rounded(adjusted),
        "adjusted_band": _difficulty_band(adjusted),
        "changed": ceiling is not None and adjusted < observed - 1e-9,
        "policy_ceiling": ceiling,
        "policy_reason": "constituent_transparency_ceiling"
        if ceiling is not None
        else "not_matched",
    }
    if expected is not None:
        payload["adjusted_abs_error"] = _rounded(abs(expected - adjusted))
    return payload


def policy_matches(row: Mapping[str, object], spec: TransparencySpec) -> bool:
    if not wago_tail(row):
        return False
    if spec.protect_source_pair_review and source_pair_review(row):
        return False
    if spec.protect_beginner_core and beginner_core(row):
        return False
    signals = _mapping(row.get("signals"))
    if _float_signal(signals, "rare_wago_tail_risk") < spec.tail_min:
        return False
    if _float_signal(signals, "named_entity_risk") > spec.entity_max:
        return False
    transparency = _mapping(row.get("transparency"))
    if not bool(transparency.get("auto_downshift_eligible")):
        return False
    if float(transparency.get("coverage_ratio") or 0.0) < spec.coverage_min:
        return False
    if float(transparency.get("guarded_transparency_score") or 0.0) < spec.score_min:
        return False
    if float(transparency.get("min_knownness") or 0.0) < spec.min_known_min:
        return False
    if float(transparency.get("reading_compositionality") or 0.0) < spec.reading_min:
        return False
    if domain_marked_risk(row) > spec.domain_risk_max:
        return False
    return raw_family_matches(row, spec)


def raw_family_matches(row: Mapping[str, object], spec: TransparencySpec) -> bool:
    signals = _mapping(row.get("signals"))
    features = _mapping(row.get("surface_features"))
    low_written = _float_signal(signals, "max_written_form_burden") <= spec.written_max
    if spec.family == "low_written":
        return low_written
    if spec.family == "any_written":
        return True
    if spec.family == "mixed_surface":
        return low_written and bool(features.get("mixed_kanji_hiragana"))
    raise ValueError(f"Unknown transparency family: {spec.family}")


def domain_marked_risk(row: Mapping[str, object]) -> float:
    signals = _mapping(row.get("signals"))
    return max((_float_signal(signals, signal) for signal in GUARD_SIGNALS), default=0.0)


def curve_result(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    transparent_failures = [
        row for row in rows if "transparent_wago_failure" in row.get("segments", ())
    ]
    broad_proxy_rows = [row for row in rows if "broad_low_written_proxy" in row.get("segments", ())]
    changed_rows = [row for row in rows if row.get("changed")]
    regressions = [
        row
        for row in changed_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    success_regressions = [
        row
        for row in changed_rows
        if float(row.get("anchor_abs_error") or 0.0) <= 0.08
        and float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    return {
        "row_count": len(rows),
        "transparent_failure_count": len(transparent_failures),
        "broad_proxy_count": len(broad_proxy_rows),
        "changed_count": len(changed_rows),
        "changed_regressions": len(regressions),
        "success_regressions": len(success_regressions),
        "all_rows": metrics_for_rows(rows),
        "transparent_failure_rows": metrics_for_rows(transparent_failures),
        "broad_proxy_rows": metrics_for_rows(broad_proxy_rows),
        "changed_rows": metrics_for_rows(changed_rows),
    }


def metrics_for_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    expected = np.asarray([_float_or_nan(row.get("expected")) for row in rows], dtype=np.float32)
    anchor = np.asarray(
        [_float_or_nan(row.get("anchor_observed")) for row in rows],
        dtype=np.float32,
    )
    adjusted = np.asarray(
        [_float_or_nan(row.get("adjusted_observed", row.get("anchor_observed"))) for row in rows],
        dtype=np.float32,
    )
    labels = [str(row.get("label")) for row in rows]
    expected_bands = [str(row.get("expected_band")) for row in rows]
    anchor_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=anchor,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    adjusted_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=adjusted,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    return {
        "count": len(rows),
        "anchor": anchor_summary,
        "adjusted": adjusted_summary,
        "delta": {
            "mae_reduction": _rounded(
                float(anchor_summary.get("mae") or 0.0) - float(adjusted_summary.get("mae") or 0.0)
            ),
            "bucket_delta": _rounded(
                float(adjusted_summary.get("bucket_accuracy") or 0.0)
                - float(anchor_summary.get("bucket_accuracy") or 0.0)
            ),
            "pairwise_delta": _rounded(
                float(adjusted_summary.get("pairwise_accuracy") or 0.0)
                - float(anchor_summary.get("pairwise_accuracy") or 0.0)
            ),
        },
    }


def full_matrix_counts(
    rows: Sequence[Mapping[str, object]],
    spec: TransparencySpec,
) -> dict[str, object]:
    matched = 0
    changed = 0
    broad_proxy_matched = 0
    for row in rows:
        if broad_low_written_proxy(row):
            broad_proxy_matched += 1
        if policy_matches(row, spec):
            matched += 1
            if float(row.get("anchor_observed") or 0.0) > spec.ceiling:
                changed += 1
    return {
        "would_match_count": matched,
        "would_change_count": changed,
        "broad_proxy_would_match_count": broad_proxy_matched,
        "change_cap": FULL_MATRIX_CHANGE_CAP,
    }


def labeled_passes_guardrails(datasets: Mapping[str, Mapping[str, object]]) -> bool:
    validation = _mapping(datasets.get("stitch_validation"))
    if metric_delta(validation, "transparent_failure_rows", "mae_reduction") <= 0.0:
        return False
    for dataset_id in DATASET_ORDER:
        dataset = _mapping(datasets.get(dataset_id))
        if int(dataset.get("changed_regressions") or 0) > 0:
            return False
        if int(dataset.get("success_regressions") or 0) > 0:
            return False
        if metric_delta(dataset, "all_rows", "mae_reduction") < -0.000001:
            return False
    return True


def candidate_summary(
    datasets: Mapping[str, Mapping[str, object]],
    full_counts: Mapping[str, object],
) -> dict[str, object]:
    summary = {
        dataset_id: {
            "all_mae_reduction": metric_delta(dataset, "all_rows", "mae_reduction"),
            "transparent_failure_mae_reduction": metric_delta(
                dataset,
                "transparent_failure_rows",
                "mae_reduction",
            ),
            "broad_proxy_mae_reduction": metric_delta(
                dataset,
                "broad_proxy_rows",
                "mae_reduction",
            ),
            "changed_count": _mapping(dataset).get("changed_count"),
            "changed_regressions": _mapping(dataset).get("changed_regressions"),
            "success_regressions": _mapping(dataset).get("success_regressions"),
        }
        for dataset_id, dataset in datasets.items()
    }
    summary["full_matrix"] = {
        "would_match_count": full_counts.get("would_match_count"),
        "would_change_count": full_counts.get("would_change_count"),
    }
    return summary


def candidate_rank_key(candidate: Mapping[str, object]) -> tuple[float, ...]:
    datasets = _mapping(candidate.get("datasets"))
    validation = _mapping(datasets.get("stitch_validation"))
    holdout = _mapping(datasets.get("holdout"))
    calibration = _mapping(datasets.get("calibration"))
    full_matrix = _mapping(candidate.get("full_matrix"))
    return (
        1.0 if candidate.get("passes_guardrails") else 0.0,
        1.0 if candidate.get("labeled_passes_guardrails") else 0.0,
        metric_delta(validation, "transparent_failure_rows", "mae_reduction"),
        metric_delta(validation, "all_rows", "mae_reduction"),
        metric_delta(holdout, "all_rows", "mae_reduction"),
        metric_delta(calibration, "all_rows", "mae_reduction"),
        -float(full_matrix.get("would_change_count") or 0.0),
    )


def metric_delta(dataset: Mapping[str, object], scope: str, key: str) -> float:
    metrics = _mapping(dataset.get(scope))
    return float(_mapping(metrics.get("delta")).get(key) or 0.0)


def dataset_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        dataset_id: base_row_stats([row for row in rows if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }


def transparency_segment_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    segments = (
        "transparent_wago_failure",
        "broad_low_written_proxy",
        "constituent_covered",
        "constituent_transparent",
        "guarded_constituent_transparent",
        "reading_noncompositional",
        "bad_segmentation_guard",
        "derivational_variant_match",
    )
    return {
        segment: base_row_stats([row for row in rows if segment in row.get("segments", ())])
        for segment in segments
    }


def base_row_stats(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "count": 0,
            "mae": None,
            "mean_observed_minus_expected": None,
            "too_low": 0,
            "too_high": 0,
        }
    errors = [
        float(row.get("anchor_observed") or 0.0) - float(row.get("expected") or 0.0) for row in rows
    ]
    return {
        "count": len(rows),
        "mae": _rounded(
            sum(abs(float(row.get("anchor_abs_error") or 0.0)) for row in rows) / len(rows)
        ),
        "mean_observed_minus_expected": _rounded(sum(errors) / len(errors)),
        "too_low": len([row for row in rows if row.get("anchor_direction") == "too_low"]),
        "too_high": len([row for row in rows if row.get("anchor_direction") == "too_high"]),
    }


def labeled_transparent_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> list[Mapping[str, object]]:
    return sorted(
        [row for row in rows if "transparent_wago_failure" in row.get("segments", ())],
        key=lambda row: float(_mapping(row.get("transparency")).get("transparency_score") or 0.0),
        reverse=True,
    )[:detail_limit]


def changed_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [row for row in rows if row.get("dataset_id") == dataset_id and row.get("changed")],
            key=lambda row: float(row.get("anchor_abs_error") or 0.0),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def regression_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [
                row
                for row in rows
                if row.get("dataset_id") == dataset_id
                and row.get("changed")
                and float(row.get("adjusted_abs_error") or 0.0)
                > float(row.get("anchor_abs_error") or 0.0) + 1e-9
            ],
            key=lambda row: (
                float(row.get("adjusted_abs_error") or 0.0)
                - float(row.get("anchor_abs_error") or 0.0)
            ),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def full_matrix_review_pack(
    rows: Sequence[Mapping[str, object]],
    spec: TransparencySpec,
    *,
    detail_limit: int,
) -> dict[str, object]:
    would_change = [
        review_row(row, spec, reason="constituent_policy_would_change")
        for row in rows
        if policy_matches(row, spec) and float(row.get("anchor_observed") or 0.0) > spec.ceiling
    ]
    broad_blocked = [
        review_row(row, spec, reason="broad_proxy_blocked_by_constituents")
        for row in rows
        if broad_low_written_proxy(row)
        and not policy_matches(row, spec)
        and float(row.get("anchor_observed") or 0.0) > spec.ceiling
    ]
    would_change.sort(key=review_sort_key, reverse=True)
    broad_blocked.sort(key=review_sort_key)
    return {
        "candidate_id": spec.spec_id,
        "would_change_examples": would_change[:detail_limit],
        "broad_proxy_blocked_examples": broad_blocked[:detail_limit],
        "would_change_count": len(would_change),
        "broad_proxy_blocked_count": len(broad_blocked),
    }


def review_row(
    row: Mapping[str, object],
    spec: TransparencySpec,
    *,
    reason: str,
) -> dict[str, object]:
    signals = _mapping(row.get("signals"))
    transparency = _mapping(row.get("transparency"))
    return {
        "label": row.get("label"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "anchor_observed": row.get("anchor_observed"),
        "policy_ceiling": spec.ceiling,
        "review_reason": reason,
        "core_rank": row.get("core_rank"),
        "frequency": signals.get("frequency"),
        "tail": signals.get("rare_wago_tail_risk"),
        "written": signals.get("max_written_form_burden"),
        "coverage": transparency.get("coverage_ratio"),
        "transparency_score": transparency.get("transparency_score"),
        "guarded_transparency_score": transparency.get("guarded_transparency_score"),
        "reading_compositionality": transparency.get("reading_compositionality"),
        "min_knownness": transparency.get("min_knownness"),
        "domain_marked_risk": _rounded(domain_marked_risk(row)),
        "guard_flags": transparency.get("guard_flags"),
        "chunks": transparency.get("chunks"),
        "segments": row.get("segments"),
    }


def review_sort_key(row: Mapping[str, object]) -> tuple[float, float, float]:
    return (
        float(row.get("guarded_transparency_score") or 0.0),
        float(row.get("coverage") or 0.0),
        float(row.get("min_knownness") or 0.0),
    )


def interpretation(best: Mapping[str, object]) -> dict[str, object]:
    summary = _mapping(best.get("summary"))
    validation = _mapping(summary.get("stitch_validation"))
    holdout = _mapping(summary.get("holdout"))
    full_matrix = _mapping(summary.get("full_matrix"))
    return {
        "best_passes_guardrails": bool(best.get("passes_guardrails")),
        "best_labeled_passes_guardrails": bool(best.get("labeled_passes_guardrails")),
        "promotion_readiness": (
            "review_only_candidate_not_runtime_promotable"
            if not best.get("passes_guardrails")
            else "bounded_candidate_for_followup_validation"
        ),
        "validation_transparent_failure_delta": validation.get("transparent_failure_mae_reduction"),
        "holdout_all_delta": holdout.get("all_mae_reduction"),
        "full_matrix_would_change": full_matrix.get("would_change_count"),
        "main_caveat": (
            "The constituent signal is derived from existing matrix lemmas and "
            "source-backed knownness signals, then guarded by reading overlap, "
            "segmentation sanity, and existing marked/domain risk components. "
            "It is still an approximation of semantic transparency, so the "
            "review pack remains required before runtime promotion."
        ),
    }


def candidate_space_summary() -> dict[str, object]:
    return {
        "families": ["low_written"],
        "ceiling": 0.74,
        "tail_thresholds": [0.5, 0.75, 0.85],
        "written_max": [0.45, 0.55],
        "coverage_min": [0.67, 1.0],
        "guarded_score_min": [0.35, 0.45, 0.55],
        "min_known_min": [0.0, 0.2],
        "reading_min": [0.67, 0.8],
        "domain_risk_max": [0.75, 1.01],
        "candidate_count": len(transparency_specs()),
    }


def spec_payload(spec: TransparencySpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "family": spec.family,
        "ceiling": spec.ceiling,
        "tail_min": spec.tail_min,
        "written_max": spec.written_max,
        "coverage_min": spec.coverage_min,
        "score_min": spec.score_min,
        "min_known_min": spec.min_known_min,
        "reading_min": spec.reading_min,
        "domain_risk_max": spec.domain_risk_max,
        "protect_beginner_core": spec.protect_beginner_core,
        "protect_source_pair_review": spec.protect_source_pair_review,
        "entity_max": spec.entity_max,
    }


def spec_from_payload(payload: Mapping[str, object]) -> TransparencySpec:
    return TransparencySpec(
        spec_id=str(payload.get("spec_id") or ""),
        family=str(payload.get("family") or "low_written"),
        ceiling=float(payload.get("ceiling") or 0.74),
        tail_min=float(payload.get("tail_min") or 0.5),
        written_max=float(payload.get("written_max") or 0.45),
        coverage_min=float(payload.get("coverage_min") or 0.67),
        score_min=float(payload.get("score_min") or 0.35),
        min_known_min=float(payload.get("min_known_min") or 0.0),
        reading_min=float(payload.get("reading_min") or 0.67),
        domain_risk_max=float(payload.get("domain_risk_max") or 1.01),
        protect_beginner_core=bool(payload.get("protect_beginner_core")),
        protect_source_pair_review=bool(payload.get("protect_source_pair_review")),
        entity_max=float(payload.get("entity_max") or 0.95),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Constituent Transparency Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        f"Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        "",
        "## Interpretation",
        "",
    ]
    for key, value in _mapping(summary.get("interpretation")).items():
        lines.append(f"- `{_escape(key)}`: `{_escape(display_value(value))}`")
    lines.extend(["", "## Signal Definition", ""])
    for key, value in _mapping(_mapping(report.get("method")).get("constituent_signal")).items():
        lines.append(f"- `{_escape(key)}`: {_escape(value)}")
    lines.extend(["", "## Dataset Summary", ""])
    lines.extend(dataset_summary_table(_mapping(report.get("dataset_summary"))))
    lines.extend(["", "## Transparency Segments", ""])
    lines.extend(segment_table(_mapping(report.get("transparency_segments"))))
    lines.extend(["", "## Candidate Space", ""])
    lines.extend(candidate_space_lines(_mapping(report.get("candidate_space"))))
    lines.extend(["", "## Probe Leaderboard", ""])
    lines.extend(leaderboard_table(_rows(report.get("leaderboard"))))
    lines.extend(["", "## Labeled Transparent-Failure Rows", ""])
    lines.extend(row_table(_rows(report.get("labeled_transparent_rows"))))
    lines.extend(["", "## Best Candidate Changed Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_changed_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    lines.extend(["## Best Candidate Regression Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_regression_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    review = _mapping(report.get("review_pack"))
    lines.extend(["## Review Pack", ""])
    lines.append(f"- Candidate: `{_escape(review.get('candidate_id'))}`")
    lines.append(f"- Would-change count: `{_escape(review.get('would_change_count'))}`")
    lines.append(
        f"- Broad-proxy blocked count: `{_escape(review.get('broad_proxy_blocked_count'))}`"
    )
    lines.extend(["", "### Constituent Policy Would Change", ""])
    lines.extend(review_table(_rows(review.get("would_change_examples"))))
    lines.extend(["", "### Broad Proxy Blocked By Low Constituents", ""])
    lines.extend(review_table(_rows(review.get("broad_proxy_blocked_examples"))))
    return "\n".join(lines).rstrip() + "\n"


def dataset_summary_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | Rows | MAE | Bias obs-exp | Too low | Too high |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_id, row in summary.items():
        parsed = _mapping(row)
        lines.append(
            f"| `{_escape(dataset_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(parsed.get('mae'))} | "
            f"{_escape(parsed.get('mean_observed_minus_expected'))} | "
            f"{_escape(parsed.get('too_low'))} | "
            f"{_escape(parsed.get('too_high'))} |"
        )
    return lines


def segment_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Segment | Rows | MAE | Bias obs-exp | Too low | Too high |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for segment_id, row in summary.items():
        parsed = _mapping(row)
        lines.append(
            f"| `{_escape(segment_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(parsed.get('mae'))} | "
            f"{_escape(parsed.get('mean_observed_minus_expected'))} | "
            f"{_escape(parsed.get('too_low'))} | "
            f"{_escape(parsed.get('too_high'))} |"
        )
    return lines


def candidate_space_lines(space: Mapping[str, object]) -> list[str]:
    return [
        f"- Candidate count: `{_escape(space.get('candidate_count'))}`",
        f"- Families: `{_escape(', '.join(str(item) for item in _sequence(space.get('families'))))}`",
        f"- Ceiling: `{_escape(space.get('ceiling'))}`",
        f"- Tail thresholds: `{_escape(_sequence(space.get('tail_thresholds')))}`",
        f"- Written max thresholds: `{_escape(_sequence(space.get('written_max')))}`",
        f"- Coverage thresholds: `{_escape(_sequence(space.get('coverage_min')))}`",
        f"- Guarded score thresholds: `{_escape(_sequence(space.get('guarded_score_min')))}`",
        f"- Min-knownness thresholds: `{_escape(_sequence(space.get('min_known_min')))}`",
        f"- Reading-compositionality thresholds: `{_escape(_sequence(space.get('reading_min')))}`",
        f"- Domain-risk ceilings: `{_escape(_sequence(space.get('domain_risk_max')))}`",
    ]


def leaderboard_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Candidate | Pass | Labeled pass | Val transparent ΔMAE | Val all ΔMAE | Holdout all ΔMAE | Full would-change |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        summary = _mapping(row.get("summary"))
        validation = _mapping(summary.get("stitch_validation"))
        holdout = _mapping(summary.get("holdout"))
        full_matrix = _mapping(summary.get("full_matrix"))
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | "
            f"{_escape(row.get('passes_guardrails'))} | "
            f"{_escape(row.get('labeled_passes_guardrails'))} | "
            f"{_escape(validation.get('transparent_failure_mae_reduction'))} | "
            f"{_escape(validation.get('all_mae_reduction'))} | "
            f"{_escape(holdout.get('all_mae_reduction'))} | "
            f"{_escape(full_matrix.get('would_change_count'))} |"
        )
    return lines


def row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Expected | Anchor | Adjusted | Anchor Err | Adj Err | Raw | Guarded | Read | Flags | Chunks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        transparency = _mapping(row.get("transparency"))
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"{_escape(row.get('expected'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('adjusted_observed'))} | "
            f"{_escape(row.get('anchor_abs_error'))} | "
            f"{_escape(row.get('adjusted_abs_error'))} | "
            f"{_escape(transparency.get('transparency_score'))} | "
            f"{_escape(transparency.get('guarded_transparency_score'))} | "
            f"{_escape(transparency.get('reading_compositionality'))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(transparency.get('guard_flags'))))} | "
            f"{_escape(chunks_label(transparency.get('chunks')))} |"
        )
    return lines


def review_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Anchor | Ceiling | Raw | Guarded | Read | Domain | Tail | Written | Flags | Chunks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('policy_ceiling'))} | "
            f"{_escape(row.get('transparency_score'))} | "
            f"{_escape(row.get('guarded_transparency_score'))} | "
            f"{_escape(row.get('reading_compositionality'))} | "
            f"{_escape(row.get('domain_marked_risk'))} | "
            f"{_escape(row.get('tail'))} | "
            f"{_escape(row.get('written'))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('guard_flags'))))} | "
            f"{_escape(chunks_label(row.get('chunks')))} |"
        )
    return lines


def chunks_label(value: object) -> str:
    chunks = _sequence(value)
    if not chunks:
        return ""
    labels = []
    for chunk in chunks:
        parsed = _mapping(chunk)
        surface = parsed.get("surface")
        matched = parsed.get("matched_lemma")
        score = parsed.get("score")
        match_type = parsed.get("match_type")
        if surface == matched:
            labels.append(f"{surface}:{score}")
        else:
            labels.append(f"{surface}->{matched}:{score}:{match_type}")
    return "; ".join(str(label) for label in labels)


def display_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = _optional_float(signals.get(signal))
    return 0.0 if value is None else float(value)


def _float_or_nan(value: object) -> float:
    parsed = _optional_float(value)
    return float("nan") if parsed is None else float(parsed)


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


if __name__ == "__main__":
    raise SystemExit(main())
