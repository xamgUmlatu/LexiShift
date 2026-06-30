#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import unicodedata
from xml.etree import ElementTree

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)


PAIR = "en-ja"
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz"
)
DEFAULT_CURRENT_JLPT_CSV = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "jlpt-tanos-vocab-ja"
    / "JLPT_vocab_ALL.csv"
)
DEFAULT_STEPHENMK_ROOT = (
    Path("/tmp") / "lexishift-jlpt-source-audit" / "stephenmk_yomichan-jlpt-vocab"
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
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_jlpt_reference_compare_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_jlpt_reference_compare_en_ja_latest.md"
)
JLPT_DIFFICULTY_BY_LEVEL = {5: 0.08, 4: 0.22, 3: 0.42, 2: 0.65, 1: 0.85}
FOCUS_ROWS = (
    ("明日", "あした"),
    ("明日", "あす"),
    ("辛い", "つらい"),
    ("辛い", "からい"),
    ("外国", "とつくに"),
    ("外国", "がいこく"),
    ("誘う", "いざなう"),
    ("誘う", "さそう"),
    ("真", "まこと"),
    ("真", "しん"),
    ("枝", "え"),
    ("僕", "やつがれ"),
    ("外", "げ"),
    ("海", "あま"),
)


@dataclass(frozen=True)
class SourceRow:
    surface: str
    reading: str
    level: int
    source: str
    sequence: str = ""
    definition: str = ""
    raw_surface: str = ""
    raw_reading: str = ""


@dataclass(frozen=True)
class MatrixContext:
    lemmas: tuple[str, ...]
    readings: tuple[str, ...]
    candidate_states: tuple[str, ...]
    problem_classes: tuple[str, ...]
    core_ranks: np.ndarray
    target_positions: np.ndarray
    frequency_values: np.ndarray
    jlpt_vocab_levels: np.ndarray
    names: tuple[str, ...]
    values: np.ndarray
    present: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare current en-ja JLPT vocabulary exact coverage against a "
            "CC BY-SA reference source without changing runtime behavior."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--current-jlpt-csv", type=Path, default=DEFAULT_CURRENT_JLPT_CSV)
    parser.add_argument("--stephenmk-root", type=Path, default=DEFAULT_STEPHENMK_ROOT)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        current_jlpt_csv_path=_resolve_path(args.current_jlpt_csv),
        stephenmk_root_path=_resolve_path(args.stephenmk_root),
        jmdict_path=_resolve_path(args.jmdict),
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
    current_jlpt_csv_path: Path,
    stephenmk_root_path: Path,
    jmdict_path: Path,
    detail_limit: int,
) -> dict[str, object]:
    matrix = _matrix_context(np.load(component_matrix_path))
    current_rows = tuple(_iter_current_jlpt_rows(current_jlpt_csv_path))
    stephen_original_rows = tuple(_iter_stephenmk_original_rows(stephenmk_root_path))
    stephen_yomitan_rows = tuple(_iter_stephenmk_yomitan_rows(stephenmk_root_path))
    stephen_sequences = {row.sequence for row in stephen_original_rows if row.sequence.strip()}
    jmdict_sequence_pairs = _jmdict_sequence_pairs(jmdict_path, stephen_sequences)

    current_pair_levels = _pair_levels(current_rows)
    current_surface_levels = _surface_levels(current_rows)
    stephen_original_pair_levels = _pair_levels(stephen_original_rows)
    stephen_yomitan_pair_levels = _pair_levels(stephen_yomitan_rows)
    stephen_original_surface_levels = _surface_levels(stephen_original_rows)
    stephen_yomitan_surface_levels = _surface_levels(stephen_yomitan_rows)
    full_sequence_pair_levels = _sequence_pair_levels(
        rows=stephen_original_rows,
        jmdict_sequence_pairs=jmdict_sequence_pairs,
        same_reading_only=False,
    )
    same_reading_sequence_pair_levels = _sequence_pair_levels(
        rows=stephen_original_rows,
        jmdict_sequence_pairs=jmdict_sequence_pairs,
        same_reading_only=True,
    )
    same_reading_sequence_pair_sources = _sequence_pair_source_rows(
        rows=stephen_original_rows,
        jmdict_sequence_pairs=jmdict_sequence_pairs,
        same_reading_only=True,
    )

    row_flags = _matrix_row_flags(
        matrix=matrix,
        current_pair_levels=current_pair_levels,
        current_surface_levels=current_surface_levels,
        stephen_original_pair_levels=stephen_original_pair_levels,
        stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
        sequence_pair_levels=same_reading_sequence_pair_levels,
    )
    source_summary = _source_summary(
        current_pair_levels=current_pair_levels,
        current_surface_levels=current_surface_levels,
        stephen_original_pair_levels=stephen_original_pair_levels,
        stephen_original_surface_levels=stephen_original_surface_levels,
        stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
        stephen_yomitan_surface_levels=stephen_yomitan_surface_levels,
        current_rows=current_rows,
        stephen_original_rows=stephen_original_rows,
        stephen_yomitan_rows=stephen_yomitan_rows,
        jmdict_sequence_pairs=jmdict_sequence_pairs,
        full_sequence_pair_levels=full_sequence_pair_levels,
        same_reading_sequence_pair_levels=same_reading_sequence_pair_levels,
    )
    matrix_summary = _matrix_summary(matrix, row_flags)
    candidate_rows = _candidate_rows(
        matrix=matrix,
        row_flags=row_flags,
        current_pair_levels=current_pair_levels,
        current_surface_levels=current_surface_levels,
        stephen_original_pair_levels=stephen_original_pair_levels,
        stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
        sequence_pair_levels=same_reading_sequence_pair_levels,
        sequence_pair_sources=same_reading_sequence_pair_sources,
        detail_limit=detail_limit,
    )
    focus_rows = _focus_rows(
        matrix=matrix,
        row_flags=row_flags,
        current_pair_levels=current_pair_levels,
        current_surface_levels=current_surface_levels,
        stephen_original_pair_levels=stephen_original_pair_levels,
        stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
        sequence_pair_levels=same_reading_sequence_pair_levels,
    )
    source_trust = _source_trust_checks(
        rows=stephen_original_rows,
        jmdict_sequence_pairs=jmdict_sequence_pairs,
        stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "product_data_ingested": False,
        "method": {
            "purpose": (
                "Estimate whether the stephenmk CC BY-SA JLPT vocabulary source "
                "is useful as a reference for repairing current effective-exact JLPT "
                "surface+reading matching, before deciding whether to ingest any "
                "additional source."
            ),
            "reference_use_policy": (
                "The comparison uses stephenmk rows and JMdict sequence IDs only "
                "as diagnostic evidence. It does not modify installed language "
                "packs, the JLPT importer, or model scoring."
            ),
            "exactness_policy": (
                "A candidate row is counted as exact only when normalized surface "
                "and normalized reading both match. JMdict sequence repair counts "
                "only same-reading form normalization; full same-sequence alternate "
                "readings are reported as risk, not exact repair evidence."
            ),
            "license_note": (
                "stephenmk/yomichan-jlpt-vocab is recorded in the earlier source "
                "audit as CC BY-SA 4.0 and Tanos-derived. Direct product ingestion "
                "would need explicit attribution and share-alike handling; this "
                "artifact is a research comparison."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "current_jlpt_csv": _repo_or_home_path(current_jlpt_csv_path),
            "stephenmk_root": _repo_or_home_path(stephenmk_root_path),
            "jmdict": _repo_or_home_path(jmdict_path),
        },
        "source_summary": source_summary,
        "source_trust_checks": source_trust,
        "matrix_summary": matrix_summary,
        "candidate_rows": candidate_rows,
        "remaining_repair_audit": _remaining_repair_audit(
            matrix=matrix,
            row_flags=row_flags,
        ),
        "focus_rows": focus_rows,
        "conclusion": _conclusion(source_summary, matrix_summary, source_trust),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "current_jlpt_csv": current_jlpt_csv_path,
                "stephenmk_root": stephenmk_root_path,
                "jmdict": jmdict_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
            },
            argv=sys.argv,
        ),
    }


def _matrix_context(payload: object) -> MatrixContext:
    count = len(payload["lemmas"])
    candidate_states = (
        tuple(str(value) for value in payload["candidate_states"])
        if "candidate_states" in payload.files
        else tuple("normal_vocab" for _ in range(count))
    )
    problem_classes = (
        tuple(str(value) for value in payload["problem_classes"])
        if "problem_classes" in payload.files
        else tuple("" for _ in range(count))
    )
    core_ranks = (
        np.asarray(payload["core_ranks"], dtype=np.float32)
        if "core_ranks" in payload.files
        else np.full(count, np.nan, dtype=np.float32)
    )
    return MatrixContext(
        lemmas=tuple(str(value) for value in payload["lemmas"]),
        readings=tuple(str(value) for value in payload["readings"]),
        candidate_states=candidate_states,
        problem_classes=problem_classes,
        core_ranks=core_ranks,
        target_positions=np.asarray(payload["target_curve_positions"], dtype=np.float32),
        frequency_values=np.asarray(payload["frequency_values"], dtype=np.float32),
        jlpt_vocab_levels=np.asarray(payload["jlpt_vocab_levels"], dtype=np.float32),
        names=tuple(str(value) for value in payload["component_names"]),
        values=np.asarray(payload["component_values"], dtype=np.float32),
        present=np.asarray(payload["component_present"], dtype=bool),
    )


def _iter_current_jlpt_rows(path: Path) -> Iterable[SourceRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            surface = _normalize_surface(row.get("Kanji") or row.get("kanji"))
            reading = _normalize_reading(row.get("Reading") or row.get("reading"))
            level = _safe_level(row.get("Level") or row.get("level"))
            if not surface and reading:
                surface = reading
            if surface and reading and level is not None:
                yield SourceRow(
                    surface=surface,
                    reading=reading,
                    level=level,
                    source="current_bluskyo_tanos",
                    raw_surface=str(row.get("Kanji") or ""),
                    raw_reading=str(row.get("Reading") or ""),
                )


def _iter_stephenmk_original_rows(root: Path) -> Iterable[SourceRow]:
    original_data = root / "original_data"
    for path in sorted(original_data.glob("n*.csv")):
        level = _level_from_filename(path)
        if level is None:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                reading = _normalize_reading(row.get("kana"))
                surface = _normalize_surface(row.get("kanji")) or reading
                if not surface or not reading:
                    continue
                yield SourceRow(
                    surface=surface,
                    reading=reading,
                    level=level,
                    source="stephenmk_original",
                    sequence=str(row.get("jmdict_seq") or "").strip(),
                    definition=str(row.get("waller_definition") or "").strip(),
                    raw_surface=str(row.get("kanji") or ""),
                    raw_reading=str(row.get("kana") or ""),
                )


def _iter_stephenmk_yomitan_rows(root: Path) -> Iterable[SourceRow]:
    yomitan = root / "yomitan-jlpt-vocab"
    for path in sorted(yomitan.glob("term_meta_bank_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            continue
        for raw in payload:
            if not isinstance(raw, list) or len(raw) < 3 or not isinstance(raw[2], Mapping):
                continue
            surface = _normalize_surface(raw[0])
            meta = raw[2]
            reading = _normalize_reading(meta.get("reading"))
            frequency = meta.get("frequency")
            display = ""
            if isinstance(frequency, Mapping):
                display = str(frequency.get("displayValue") or "")
            level = _safe_level(display)
            if surface and reading and level is not None:
                yield SourceRow(
                    surface=surface,
                    reading=reading,
                    level=level,
                    source="stephenmk_yomitan",
                    raw_surface=str(raw[0] or ""),
                    raw_reading=str(meta.get("reading") or ""),
                )


def _jmdict_sequence_pairs(
    path: Path,
    target_sequences: set[str],
) -> dict[str, set[tuple[str, str]]]:
    if not target_sequences:
        return {}
    pairs_by_sequence: dict[str, set[tuple[str, str]]] = {}
    for _event, elem in ElementTree.iterparse(path, events=("end",)):
        if _strip_namespace(elem.tag) != "entry":
            continue
        sequence = _child_text(elem, "ent_seq")
        if sequence in target_sequences:
            pairs_by_sequence[sequence] = _jmdict_entry_pairs(elem)
        elem.clear()
    return pairs_by_sequence


def _jmdict_entry_pairs(elem: ElementTree.Element) -> set[tuple[str, str]]:
    kanji_forms = [_normalize_surface(_child_text(k_ele, "keb")) for k_ele in elem.findall("k_ele")]
    kanji_forms = [value for value in kanji_forms if value]
    pairs: set[tuple[str, str]] = set()
    for r_ele in elem.findall("r_ele"):
        reading = _normalize_reading(_child_text(r_ele, "reb"))
        if not reading:
            continue
        restrictions = [
            _normalize_surface(node.text)
            for node in r_ele.findall("re_restr")
            if _normalize_surface(node.text)
        ]
        no_kanji = any(_strip_namespace(node.tag) == "re_nokanji" for node in r_ele)
        if restrictions:
            surfaces = restrictions
        elif kanji_forms and not no_kanji:
            surfaces = kanji_forms
        else:
            surfaces = [reading]
        for surface in surfaces:
            if surface:
                pairs.add((surface, reading))
    return pairs


def _pair_levels(rows: Iterable[SourceRow]) -> dict[tuple[str, str], set[int]]:
    levels: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in rows:
        levels[(row.surface, row.reading)].add(row.level)
    return dict(levels)


def _surface_levels(rows: Iterable[SourceRow]) -> dict[str, set[int]]:
    levels: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        levels[row.surface].add(row.level)
    return dict(levels)


def _sequence_pair_levels(
    *,
    rows: Iterable[SourceRow],
    jmdict_sequence_pairs: Mapping[str, set[tuple[str, str]]],
    same_reading_only: bool,
) -> dict[tuple[str, str], set[int]]:
    levels: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in rows:
        for pair in jmdict_sequence_pairs.get(row.sequence, ()):
            if same_reading_only and pair[1] != row.reading:
                continue
            levels[pair].add(row.level)
    return dict(levels)


def _sequence_pair_source_rows(
    *,
    rows: Iterable[SourceRow],
    jmdict_sequence_pairs: Mapping[str, set[tuple[str, str]]],
    same_reading_only: bool,
) -> dict[tuple[str, str], list[SourceRow]]:
    sources: dict[tuple[str, str], list[SourceRow]] = defaultdict(list)
    for row in rows:
        for pair in jmdict_sequence_pairs.get(row.sequence, ()):
            if same_reading_only and pair[1] != row.reading:
                continue
            sources[pair].append(row)
    return {pair: source_rows[:8] for pair, source_rows in sources.items()}


def _matrix_row_flags(
    *,
    matrix: MatrixContext,
    current_pair_levels: Mapping[tuple[str, str], set[int]],
    current_surface_levels: Mapping[str, set[int]],
    stephen_original_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_levels: Mapping[tuple[str, str], set[int]],
) -> dict[str, np.ndarray]:
    pairs = [_matrix_pair(matrix, index) for index in range(len(matrix.lemmas))]
    surfaces = [pair[0] for pair in pairs]
    current_source_exact = np.asarray([pair in current_pair_levels for pair in pairs], dtype=bool)
    current_source_surface = np.asarray(
        [surface in current_surface_levels for surface in surfaces],
        dtype=bool,
    )
    stephen_original_exact = np.asarray(
        [pair in stephen_original_pair_levels for pair in pairs],
        dtype=bool,
    )
    stephen_yomitan_exact = np.asarray(
        [pair in stephen_yomitan_pair_levels for pair in pairs],
        dtype=bool,
    )
    stephen_sequence_exact = np.asarray(
        [pair in sequence_pair_levels for pair in pairs],
        dtype=bool,
    )
    jlpt_known = _component_value(matrix, "jlpt_vocab_known", fill=0.0) > 0.5
    jlpt_exact_known = _component_value(matrix, "jlpt_vocab_exact_known", fill=0.0) > 0.5
    jlpt_normalized_exact_known = (
        _component_value(matrix, "jlpt_vocab_normalized_exact_known", fill=0.0) > 0.5
    )
    jlpt_guarded_normalized_exact_known = (
        _component_value(matrix, "jlpt_vocab_guarded_normalized_exact_known", fill=0.0) > 0.5
    )
    jlpt_effective_exact_known = (
        _component_value(matrix, "jlpt_vocab_effective_exact_known", fill=np.nan) > 0.5
    )
    if not np.any(jlpt_effective_exact_known):
        jlpt_effective_exact_known = jlpt_exact_known
    jlpt_surface_known = _component_value(matrix, "jlpt_vocab_surface_known", fill=0.0) > 0.5
    broad_known = np.logical_or(jlpt_known, current_source_surface)
    broad_only = np.logical_and(broad_known, np.logical_not(jlpt_effective_exact_known))
    reference_exact = np.logical_or.reduce(
        (stephen_original_exact, stephen_yomitan_exact, stephen_sequence_exact)
    )
    current_exact_or_reference = np.logical_or(jlpt_effective_exact_known, reference_exact)
    first60 = _first60_mask(matrix)
    return {
        "current_source_exact": current_source_exact,
        "current_source_surface": current_source_surface,
        "current_matrix_jlpt_known": jlpt_known,
        "current_matrix_jlpt_exact_known": jlpt_exact_known,
        "current_matrix_jlpt_normalized_exact_known": jlpt_normalized_exact_known,
        "current_matrix_jlpt_guarded_normalized_exact_known": (jlpt_guarded_normalized_exact_known),
        "current_matrix_jlpt_effective_exact_known": jlpt_effective_exact_known,
        "current_matrix_jlpt_surface_known": jlpt_surface_known,
        "current_broad_known": broad_known,
        "current_broad_only": broad_only,
        "stephen_original_exact": stephen_original_exact,
        "stephen_yomitan_exact": stephen_yomitan_exact,
        "stephen_sequence_exact": stephen_sequence_exact,
        "reference_exact": reference_exact,
        "current_exact_or_reference": current_exact_or_reference,
        "reference_exact_not_current_exact": np.logical_and(
            reference_exact,
            np.logical_not(jlpt_effective_exact_known),
        ),
        "reference_exact_not_raw_exact": np.logical_and(
            reference_exact,
            np.logical_not(jlpt_exact_known),
        ),
        "reference_exact_not_current_broad": np.logical_and(
            reference_exact,
            np.logical_not(broad_known),
        ),
        "broad_only_reference_exact": np.logical_and(broad_only, reference_exact),
        "broad_only_yomitan_exact": np.logical_and(broad_only, stephen_yomitan_exact),
        "broad_only_sequence_exact": np.logical_and(broad_only, stephen_sequence_exact),
        "first60": first60,
        "first60_reference_exact_not_current_exact": np.logical_and(
            first60,
            np.logical_and(reference_exact, np.logical_not(jlpt_effective_exact_known)),
        ),
        "first60_reference_exact_not_raw_exact": np.logical_and(
            first60,
            np.logical_and(reference_exact, np.logical_not(jlpt_exact_known)),
        ),
        "first60_reference_exact_not_current_broad": np.logical_and(
            first60,
            np.logical_and(reference_exact, np.logical_not(broad_known)),
        ),
    }


def _source_summary(
    *,
    current_pair_levels: Mapping[tuple[str, str], set[int]],
    current_surface_levels: Mapping[str, set[int]],
    stephen_original_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_original_surface_levels: Mapping[str, set[int]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_yomitan_surface_levels: Mapping[str, set[int]],
    current_rows: Sequence[SourceRow],
    stephen_original_rows: Sequence[SourceRow],
    stephen_yomitan_rows: Sequence[SourceRow],
    jmdict_sequence_pairs: Mapping[str, set[tuple[str, str]]],
    full_sequence_pair_levels: Mapping[tuple[str, str], set[int]],
    same_reading_sequence_pair_levels: Mapping[tuple[str, str], set[int]],
) -> dict[str, object]:
    current_pairs = set(current_pair_levels)
    original_pairs = set(stephen_original_pair_levels)
    yomitan_pairs = set(stephen_yomitan_pair_levels)
    full_sequence_pairs = set(full_sequence_pair_levels)
    same_reading_sequence_pairs = set(same_reading_sequence_pair_levels)
    return {
        "current_rows": len(current_rows),
        "current_unique_pairs": len(current_pairs),
        "current_unique_surfaces": len(current_surface_levels),
        "stephen_original_rows": len(stephen_original_rows),
        "stephen_original_unique_pairs": len(original_pairs),
        "stephen_original_unique_surfaces": len(stephen_original_surface_levels),
        "stephen_yomitan_rows": len(stephen_yomitan_rows),
        "stephen_yomitan_unique_pairs": len(yomitan_pairs),
        "stephen_yomitan_unique_surfaces": len(stephen_yomitan_surface_levels),
        "stephen_original_pairs_overlap_current": len(original_pairs & current_pairs),
        "stephen_original_pairs_only_in_reference": len(original_pairs - current_pairs),
        "current_pairs_only_vs_stephen_original": len(current_pairs - original_pairs),
        "stephen_yomitan_pairs_overlap_current": len(yomitan_pairs & current_pairs),
        "stephen_yomitan_pairs_only_in_reference": len(yomitan_pairs - current_pairs),
        "current_pairs_only_vs_stephen_yomitan": len(current_pairs - yomitan_pairs),
        "stephen_sequence_ids_requested": len(
            {row.sequence for row in stephen_original_rows if row.sequence}
        ),
        "stephen_sequence_ids_resolved_in_jmdict": len(jmdict_sequence_pairs),
        "stephen_sequence_expanded_unique_pairs": len(full_sequence_pairs),
        "stephen_sequence_expanded_pairs_overlap_current": len(full_sequence_pairs & current_pairs),
        "stephen_sequence_expanded_pairs_only_in_reference": len(
            full_sequence_pairs - current_pairs
        ),
        "stephen_sequence_same_reading_unique_pairs": len(same_reading_sequence_pairs),
        "stephen_sequence_same_reading_pairs_overlap_current": len(
            same_reading_sequence_pairs & current_pairs
        ),
        "stephen_sequence_same_reading_pairs_only_in_reference": len(
            same_reading_sequence_pairs - current_pairs
        ),
        "unsafe_full_sequence_extra_pairs": len(full_sequence_pairs - same_reading_sequence_pairs),
        "level_counts": {
            "current": _level_counts(current_rows),
            "stephen_original": _level_counts(stephen_original_rows),
            "stephen_yomitan": _level_counts(stephen_yomitan_rows),
        },
    }


def _matrix_summary(
    matrix: MatrixContext,
    row_flags: Mapping[str, np.ndarray],
) -> dict[str, object]:
    total = len(matrix.lemmas)
    first60 = row_flags["first60"]
    return {
        "matrix_rows": total,
        "first60_rows_by_core_rank": int(first60.sum()),
        "current_matrix_jlpt_known": _count(row_flags["current_matrix_jlpt_known"]),
        "current_matrix_jlpt_exact_known": _count(row_flags["current_matrix_jlpt_exact_known"]),
        "current_matrix_jlpt_normalized_exact_known": _count(
            row_flags["current_matrix_jlpt_normalized_exact_known"]
        ),
        "current_matrix_jlpt_guarded_normalized_exact_known": _count(
            row_flags["current_matrix_jlpt_guarded_normalized_exact_known"]
        ),
        "current_matrix_jlpt_effective_exact_known": _count(
            row_flags["current_matrix_jlpt_effective_exact_known"]
        ),
        "current_matrix_broad_only": _count(row_flags["current_broad_only"]),
        "broad_only_reference_exact": _count(row_flags["broad_only_reference_exact"]),
        "broad_only_yomitan_exact": _count(row_flags["broad_only_yomitan_exact"]),
        "broad_only_sequence_exact": _count(row_flags["broad_only_sequence_exact"]),
        "reference_exact_not_current_exact": _count(row_flags["reference_exact_not_current_exact"]),
        "reference_exact_not_raw_exact": _count(row_flags["reference_exact_not_raw_exact"]),
        "reference_exact_not_current_broad": _count(row_flags["reference_exact_not_current_broad"]),
        "first60_reference_exact_not_current_exact": _count(
            row_flags["first60_reference_exact_not_current_exact"]
        ),
        "first60_reference_exact_not_raw_exact": _count(
            row_flags["first60_reference_exact_not_raw_exact"]
        ),
        "first60_reference_exact_not_current_broad": _count(
            row_flags["first60_reference_exact_not_current_broad"]
        ),
        "current_exact_or_reference_exact": _count(row_flags["current_exact_or_reference"]),
        "possible_exact_gain_vs_current_matrix": _count(
            row_flags["reference_exact_not_current_exact"]
        ),
        "possible_total_exact_after_reference": _count(row_flags["current_exact_or_reference"]),
        "possible_exact_gain_pct_of_current_exact": _ratio(
            _count(row_flags["reference_exact_not_current_exact"]),
            _count(row_flags["current_matrix_jlpt_effective_exact_known"]),
        ),
        "possible_first60_exact_gain_pct_of_first60": _ratio(
            _count(row_flags["first60_reference_exact_not_current_exact"]),
            int(first60.sum()),
        ),
    }


def _candidate_rows(
    *,
    matrix: MatrixContext,
    row_flags: Mapping[str, np.ndarray],
    current_pair_levels: Mapping[tuple[str, str], set[int]],
    current_surface_levels: Mapping[str, set[int]],
    stephen_original_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_sources: Mapping[tuple[str, str], Sequence[SourceRow]],
    detail_limit: int,
) -> dict[str, object]:
    masks = {
        "reference_exact_not_current_exact": row_flags["reference_exact_not_current_exact"],
        "broad_only_reference_exact": row_flags["broad_only_reference_exact"],
        "broad_only_yomitan_exact": row_flags["broad_only_yomitan_exact"],
        "broad_only_sequence_exact": row_flags["broad_only_sequence_exact"],
        "reference_exact_not_current_broad": row_flags["reference_exact_not_current_broad"],
        "first60_reference_exact_not_current_exact": row_flags[
            "first60_reference_exact_not_current_exact"
        ],
    }
    return {
        name: [
            _detail_row(
                matrix=matrix,
                index=index,
                current_pair_levels=current_pair_levels,
                current_surface_levels=current_surface_levels,
                stephen_original_pair_levels=stephen_original_pair_levels,
                stephen_yomitan_pair_levels=stephen_yomitan_pair_levels,
                sequence_pair_levels=sequence_pair_levels,
                sequence_pair_sources=sequence_pair_sources,
            )
            for index in _ranked_indices(matrix, row_flags, mask, limit=detail_limit)
        ]
        for name, mask in masks.items()
    }


def _focus_rows(
    *,
    matrix: MatrixContext,
    row_flags: Mapping[str, np.ndarray],
    current_pair_levels: Mapping[tuple[str, str], set[int]],
    current_surface_levels: Mapping[str, set[int]],
    stephen_original_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_levels: Mapping[tuple[str, str], set[int]],
) -> list[dict[str, object]]:
    index_by_pair = {_matrix_pair(matrix, index): index for index in range(len(matrix.lemmas))}
    rows: list[dict[str, object]] = []
    for raw_surface, raw_reading in FOCUS_ROWS:
        pair = (_normalize_surface(raw_surface), _normalize_reading(raw_reading))
        index = index_by_pair.get(pair)
        row: dict[str, object] = {
            "surface": pair[0],
            "reading": pair[1],
            "matrix_row_present": index is not None,
            "current_source_surface_levels": _levels(current_surface_levels.get(pair[0])),
            "current_source_exact_levels": _levels(current_pair_levels.get(pair)),
            "stephen_original_exact_levels": _levels(stephen_original_pair_levels.get(pair)),
            "stephen_yomitan_exact_levels": _levels(stephen_yomitan_pair_levels.get(pair)),
            "stephen_sequence_exact_levels": _levels(sequence_pair_levels.get(pair)),
        }
        if index is not None:
            row.update(
                {
                    "current_matrix_jlpt_known": bool(
                        row_flags["current_matrix_jlpt_known"][index]
                    ),
                    "current_matrix_jlpt_exact_known": bool(
                        row_flags["current_matrix_jlpt_exact_known"][index]
                    ),
                    "current_matrix_jlpt_normalized_exact_known": bool(
                        row_flags["current_matrix_jlpt_normalized_exact_known"][index]
                    ),
                    "current_matrix_jlpt_guarded_normalized_exact_known": bool(
                        row_flags["current_matrix_jlpt_guarded_normalized_exact_known"][index]
                    ),
                    "current_matrix_jlpt_effective_exact_known": bool(
                        row_flags["current_matrix_jlpt_effective_exact_known"][index]
                    ),
                    "current_broad_only": bool(row_flags["current_broad_only"][index]),
                    "reference_exact": bool(row_flags["reference_exact"][index]),
                    "core_rank": _rounded(matrix.core_ranks[index]),
                    "jlpt_vocab_level": _rounded(matrix.jlpt_vocab_levels[index]),
                    "jlpt_vocab_difficulty": _rounded(
                        _component_value(matrix, "jlpt_vocab_difficulty")[index]
                    ),
                    "jlpt_vocab_exact_difficulty": _rounded(
                        _component_value(matrix, "jlpt_vocab_exact_difficulty")[index]
                    ),
                    "jlpt_vocab_effective_exact_difficulty": _rounded(
                        _component_value(
                            matrix,
                            "jlpt_vocab_effective_exact_difficulty",
                        )[index]
                    ),
                    "same_surface_rare_pollution_risk": _rounded(
                        _component_value(
                            matrix,
                            "same_surface_rare_pollution_risk",
                            fill=0.0,
                        )[index]
                    ),
                }
            )
        rows.append(row)
    return rows


def _remaining_repair_audit(
    *,
    matrix: MatrixContext,
    row_flags: Mapping[str, np.ndarray],
) -> dict[str, object]:
    mask = row_flags["reference_exact_not_current_exact"]
    first60 = row_flags["first60"]
    categories: Counter[str] = Counter()
    first60_categories: Counter[str] = Counter()
    for index in np.flatnonzero(mask):
        category = _repair_category_for_index(matrix, int(index), row_flags=row_flags)
        categories[category] += 1
        if first60[int(index)]:
            first60_categories[category] += 1
    return {
        "row_count": int(np.count_nonzero(mask)),
        "first60_row_count": int(np.count_nonzero(np.logical_and(mask, first60))),
        "category_counts": dict(sorted(categories.items())),
        "first60_category_counts": dict(sorted(first60_categories.items())),
        "interpretation": (
            "Rows in guarded or marked-form categories are not automatic repairs; "
            "they are exactly the cases where effective exact matching should stay "
            "conservative unless a product policy intentionally accepts rare or "
            "kana-preferred written forms as learner anchors."
        ),
    }


def _source_trust_checks(
    *,
    rows: Sequence[SourceRow],
    jmdict_sequence_pairs: Mapping[str, set[tuple[str, str]]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
) -> dict[str, object]:
    with_sequence = [row for row in rows if row.sequence]
    original_pair_in_sequence = [
        row
        for row in with_sequence
        if (row.surface, row.reading) in jmdict_sequence_pairs.get(row.sequence, set())
    ]
    original_pair_not_in_sequence = [
        row
        for row in with_sequence
        if (row.surface, row.reading) not in jmdict_sequence_pairs.get(row.sequence, set())
    ]
    yomitan_pairs = set(stephen_yomitan_pair_levels)
    sequence_pairs = {pair for pairs in jmdict_sequence_pairs.values() for pair in pairs}
    return {
        "stephen_original_rows_with_sequence": len(with_sequence),
        "original_pair_in_claimed_jmdict_sequence": len(original_pair_in_sequence),
        "original_pair_not_in_claimed_jmdict_sequence": len(original_pair_not_in_sequence),
        "original_pair_sequence_match_rate": _ratio(
            len(original_pair_in_sequence),
            len(with_sequence),
        ),
        "yomitan_pairs_in_any_referenced_sequence": len(yomitan_pairs & sequence_pairs),
        "yomitan_pairs_not_in_any_referenced_sequence": len(yomitan_pairs - sequence_pairs),
        "yomitan_pair_sequence_match_rate": _ratio(
            len(yomitan_pairs & sequence_pairs),
            len(yomitan_pairs),
        ),
        "sample_original_pairs_not_in_sequence": [
            _source_row_payload(row) for row in original_pair_not_in_sequence[:12]
        ],
    }


def _detail_row(
    *,
    matrix: MatrixContext,
    index: int,
    current_pair_levels: Mapping[tuple[str, str], set[int]],
    current_surface_levels: Mapping[str, set[int]],
    stephen_original_pair_levels: Mapping[tuple[str, str], set[int]],
    stephen_yomitan_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_levels: Mapping[tuple[str, str], set[int]],
    sequence_pair_sources: Mapping[tuple[str, str], Sequence[SourceRow]],
) -> dict[str, object]:
    pair = _matrix_pair(matrix, index)
    sequence_sources = sequence_pair_sources.get(pair, ())
    row = {
        "surface": pair[0],
        "reading": pair[1],
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(matrix.core_ranks[index]),
        "target_curve_position": _rounded(matrix.target_positions[index]),
        "frequency_difficulty": _rounded(matrix.frequency_values[index]),
        "jlpt_vocab_level": _rounded(matrix.jlpt_vocab_levels[index]),
        "current_jlpt_difficulty": _rounded(
            _component_value(matrix, "jlpt_vocab_difficulty")[index]
        ),
        "current_jlpt_exact_difficulty": _rounded(
            _component_value(matrix, "jlpt_vocab_exact_difficulty")[index]
        ),
        "current_jlpt_effective_exact_difficulty": _rounded(
            _component_value(matrix, "jlpt_vocab_effective_exact_difficulty")[index]
        ),
        "current_matrix_jlpt_raw_exact_known": bool(
            _component_value(matrix, "jlpt_vocab_exact_known", fill=0.0)[index] > 0.5
        ),
        "current_matrix_jlpt_normalized_exact_known": bool(
            _component_value(matrix, "jlpt_vocab_normalized_exact_known", fill=0.0)[index] > 0.5
        ),
        "current_matrix_jlpt_guarded_normalized_exact_known": bool(
            _component_value(
                matrix,
                "jlpt_vocab_guarded_normalized_exact_known",
                fill=0.0,
            )[index]
            > 0.5
        ),
        "current_matrix_jlpt_effective_exact_known": bool(
            _component_value(matrix, "jlpt_vocab_effective_exact_known", fill=0.0)[index] > 0.5
        ),
        "current_source_surface_levels": _levels(current_surface_levels.get(pair[0])),
        "current_source_exact_levels": _levels(current_pair_levels.get(pair)),
        "stephen_original_exact_levels": _levels(stephen_original_pair_levels.get(pair)),
        "stephen_yomitan_exact_levels": _levels(stephen_yomitan_pair_levels.get(pair)),
        "stephen_sequence_exact_levels": _levels(sequence_pair_levels.get(pair)),
        "same_surface_rare_pollution_risk": _rounded(
            _component_value(matrix, "same_surface_rare_pollution_risk", fill=0.0)[index]
        ),
        "same_surface_pedagogical_family_only_risk": _rounded(
            _component_value(
                matrix,
                "same_surface_pedagogical_family_only_risk",
                fill=0.0,
            )[index]
        ),
        "rare_reading_form_strength": _rounded(
            _component_value(matrix, "rare_reading_form_strength", fill=0.0)[index]
        ),
        "jmdict_kana_preferred_risk": _rounded(
            _component_value(matrix, "jmdict_kana_preferred_risk", fill=0.0)[index]
        ),
        "jmdict_search_only_form_risk": _rounded(
            _component_value(matrix, "jmdict_search_only_form_risk", fill=0.0)[index]
        ),
        "jmdict_kanji_form_marked_risk": _rounded(
            _component_value(matrix, "jmdict_kanji_form_marked_risk", fill=0.0)[index]
        ),
        "jmdict_reading_form_marked_risk": _rounded(
            _component_value(matrix, "jmdict_reading_form_marked_risk", fill=0.0)[index]
        ),
        "jmdict_marked_usage_risk": _rounded(
            _component_value(matrix, "jmdict_marked_usage_risk", fill=0.0)[index]
        ),
        "rare_non_standard_reading_risk": _rounded(
            _component_value(matrix, "rare_non_standard_reading_risk", fill=0.0)[index]
        ),
        "sequence_reference_rows": [_source_row_payload(row) for row in sequence_sources[:3]],
    }
    row["repair_category"] = _repair_category_from_detail(row)
    return row


def _ranked_indices(
    matrix: MatrixContext,
    row_flags: Mapping[str, np.ndarray],
    mask: np.ndarray,
    *,
    limit: int,
) -> list[int]:
    risk = _component_value(matrix, "same_surface_rare_pollution_risk", fill=0.0)
    family_risk = _component_value(
        matrix,
        "same_surface_pedagogical_family_only_risk",
        fill=0.0,
    )
    rare_strength = _component_value(matrix, "rare_reading_form_strength", fill=0.0)
    first60 = row_flags["first60"]
    indices = [int(index) for index in np.flatnonzero(mask)]
    indices.sort(
        key=lambda index: (
            1 if first60[index] else 0,
            float(risk[index]),
            float(family_risk[index]),
            float(rare_strength[index]),
            -float(_safe_sort_rank(matrix.core_ranks[index])),
            matrix.lemmas[index],
            matrix.readings[index],
        ),
        reverse=True,
    )
    return indices[:limit]


def _repair_category_for_index(
    matrix: MatrixContext,
    index: int,
    *,
    row_flags: Mapping[str, np.ndarray],
) -> str:
    row = {
        "current_matrix_jlpt_guarded_normalized_exact_known": bool(
            row_flags["current_matrix_jlpt_guarded_normalized_exact_known"][index]
        ),
        "current_source_surface_levels": (
            [1] if row_flags["current_source_surface"][index] else []
        ),
        "stephen_original_exact_levels": (
            [1] if row_flags["stephen_original_exact"][index] else []
        ),
        "stephen_yomitan_exact_levels": ([1] if row_flags["stephen_yomitan_exact"][index] else []),
        "stephen_sequence_exact_levels": (
            [1] if row_flags["stephen_sequence_exact"][index] else []
        ),
        "jmdict_kana_preferred_risk": _component_scalar(
            matrix,
            "jmdict_kana_preferred_risk",
            index,
        ),
        "jmdict_search_only_form_risk": _component_scalar(
            matrix,
            "jmdict_search_only_form_risk",
            index,
        ),
        "jmdict_kanji_form_marked_risk": _component_scalar(
            matrix,
            "jmdict_kanji_form_marked_risk",
            index,
        ),
        "jmdict_reading_form_marked_risk": _component_scalar(
            matrix,
            "jmdict_reading_form_marked_risk",
            index,
        ),
        "jmdict_marked_usage_risk": _component_scalar(
            matrix,
            "jmdict_marked_usage_risk",
            index,
        ),
        "rare_non_standard_reading_risk": _component_scalar(
            matrix,
            "rare_non_standard_reading_risk",
            index,
        ),
    }
    return _repair_category_from_detail(row)


def _repair_category_from_detail(row: Mapping[str, object]) -> str:
    if bool(row.get("current_matrix_jlpt_guarded_normalized_exact_known")):
        return "guarded_current_same_reading_normalization"
    if _positive(row.get("jmdict_search_only_form_risk")):
        return "jmdict_search_only_written_form"
    if _positive(row.get("jmdict_kana_preferred_risk")):
        return "jmdict_kana_preferred_or_rare_written_form"
    if _positive(row.get("jmdict_kanji_form_marked_risk")):
        return "jmdict_marked_kanji_form"
    if _positive(row.get("jmdict_reading_form_marked_risk")) or _positive(
        row.get("rare_non_standard_reading_risk")
    ):
        return "jmdict_marked_or_rare_reading"
    if _positive(row.get("jmdict_marked_usage_risk")):
        return "jmdict_marked_usage"
    if _as_ints(row.get("current_source_surface_levels")):
        return "current_jlpt_surface_only_no_exact"
    if _as_ints(row.get("stephen_sequence_exact_levels")):
        return "external_same_sequence_same_reading_only"
    if _as_ints(row.get("stephen_original_exact_levels")) or _as_ints(
        row.get("stephen_yomitan_exact_levels")
    ):
        return "external_pair_only"
    return "external_reference_only_unclassified"


def _component_scalar(matrix: MatrixContext, name: str, index: int) -> float:
    return float(_component_value(matrix, name, fill=0.0)[index])


def _positive(value: object) -> bool:
    try:
        return float(value or 0.0) > 0.0
    except (TypeError, ValueError):
        return False


def _conclusion(
    source_summary: Mapping[str, object],
    matrix_summary: Mapping[str, object],
    source_trust: Mapping[str, object],
) -> dict[str, object]:
    possible_gain = int(matrix_summary.get("possible_exact_gain_vs_current_matrix") or 0)
    broad_repair = int(matrix_summary.get("broad_only_reference_exact") or 0)
    first60_add = int(matrix_summary.get("first60_reference_exact_not_current_exact") or 0)
    sequence_rate = float(source_trust.get("original_pair_sequence_match_rate") or 0.0)
    if possible_gain >= 250 and sequence_rate >= 0.90:
        recommendation = "worth_mapping_repair_poc"
    elif possible_gain >= 100:
        recommendation = "limited_mapping_repair_poc"
    else:
        recommendation = "low_incremental_value"
    return {
        "recommendation": recommendation,
        "summary": (
            f"Reference evidence could add or repair {possible_gain} effective-exact "
            f"matrix "
            f"rows, including {broad_repair} current broad-only rows and "
            f"{first60_add} rows inside the first-60-by-core-rank slice."
        ),
        "interpretation": (
            "This is primarily a coverage/mapping repair opportunity, not a new "
            "independent JLPT theory. It is most useful if the candidate examples "
            "show same-surface or normalized-spelling failures we actually want "
            "to fix."
        ),
        "next_step": (
            "If accepted, inspect the remaining reference-only rows as possible "
            "safe normalization candidates, then rebuild the component matrix and "
            "compare effective-exact gain."
        ),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    source = _as_mapping(report.get("source_summary"))
    matrix = _as_mapping(report.get("matrix_summary"))
    trust = _as_mapping(report.get("source_trust_checks"))
    conclusion = _as_mapping(report.get("conclusion"))
    candidate_rows = _as_mapping(report.get("candidate_rows"))
    remaining_audit = _as_mapping(report.get("remaining_repair_audit"))
    lines = [
        "# en-ja JLPT Reference Comparison",
        "",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "Status: research-only sidecar; no runtime behavior changed and no product data ingested.",
        "",
        "## Purpose",
        "",
        (
            "Measure whether `stephenmk/yomichan-jlpt-vocab` is useful as a "
            "reference for repairing effective-exact JLPT surface+reading coverage in the "
            "current en-ja learner-difficulty matrix."
        ),
        "",
        "## Source-Level Comparison",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "current_unique_pairs",
        "stephen_original_unique_pairs",
        "stephen_original_pairs_overlap_current",
        "stephen_original_pairs_only_in_reference",
        "stephen_yomitan_unique_pairs",
        "stephen_yomitan_pairs_overlap_current",
        "stephen_yomitan_pairs_only_in_reference",
        "stephen_sequence_expanded_unique_pairs",
        "stephen_sequence_expanded_pairs_only_in_reference",
        "stephen_sequence_same_reading_unique_pairs",
        "stephen_sequence_same_reading_pairs_only_in_reference",
        "unsafe_full_sequence_extra_pairs",
    ):
        lines.append(f"| `{key}` | {_escape(source.get(key))} |")
    lines.extend(
        [
            "",
            "## Matrix Impact Estimate",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key in (
        "matrix_rows",
        "first60_rows_by_core_rank",
        "current_matrix_jlpt_known",
        "current_matrix_jlpt_exact_known",
        "current_matrix_jlpt_normalized_exact_known",
        "current_matrix_jlpt_guarded_normalized_exact_known",
        "current_matrix_jlpt_effective_exact_known",
        "current_matrix_broad_only",
        "broad_only_reference_exact",
        "broad_only_yomitan_exact",
        "broad_only_sequence_exact",
        "reference_exact_not_current_exact",
        "reference_exact_not_raw_exact",
        "reference_exact_not_current_broad",
        "first60_reference_exact_not_current_exact",
        "first60_reference_exact_not_raw_exact",
        "first60_reference_exact_not_current_broad",
        "possible_total_exact_after_reference",
        "possible_exact_gain_pct_of_current_exact",
    ):
        lines.append(f"| `{key}` | {_escape(matrix.get(key))} |")
    lines.extend(
        [
            "",
            "## Trust Checks",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key in (
        "stephen_original_rows_with_sequence",
        "original_pair_in_claimed_jmdict_sequence",
        "original_pair_not_in_claimed_jmdict_sequence",
        "original_pair_sequence_match_rate",
        "yomitan_pairs_in_any_referenced_sequence",
        "yomitan_pairs_not_in_any_referenced_sequence",
        "yomitan_pair_sequence_match_rate",
    ):
        lines.append(f"| `{key}` | {_escape(trust.get(key))} |")
    lines.extend(
        [
            "",
            "## Remaining Effective-Exact Gap Audit",
            "",
            f"- Rows: `{_escape(remaining_audit.get('row_count'))}`",
            f"- First-60 rows: `{_escape(remaining_audit.get('first60_row_count'))}`",
            "",
            "Category counts:",
            "",
            "| Category | Count | First-60 Count |",
            "| --- | ---: | ---: |",
        ]
    )
    category_counts = _as_mapping(remaining_audit.get("category_counts"))
    first60_category_counts = _as_mapping(remaining_audit.get("first60_category_counts"))
    for category, count in category_counts.items():
        lines.append(
            "| "
            f"`{_escape(category)}` | "
            f"{_escape(count)} | "
            f"{_escape(first60_category_counts.get(str(category), 0))} |"
        )
    lines.extend(
        [
            "",
            str(remaining_audit.get("interpretation") or ""),
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Candidate Examples",
            "",
        ]
    )
    for section_key, title in (
        (
            "reference_exact_not_current_exact",
            "Remaining reference exact rows not covered by effective exact",
        ),
        ("broad_only_reference_exact", "Current broad-only rows with reference exact evidence"),
        (
            "reference_exact_not_current_broad",
            "Reference exact rows absent from current broad JLPT",
        ),
        (
            "first60_reference_exact_not_current_exact",
            "First-60 rows where reference adds exact evidence",
        ),
    ):
        lines.extend(_candidate_table(title, _sequence(candidate_rows.get(section_key))))
    lines.extend(
        [
            "## Focus Rows",
            "",
            (
                "| Surface | Reading | Matrix | Raw exact | Normalized exact | "
                "Guarded normalized | Effective exact | Reference exact | "
                "Surface-only? | Risk |"
            ),
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for row in _sequence(report.get("focus_rows")):
        item = _as_mapping(row)
        reference_levels = sorted(
            {
                *_as_ints(item.get("stephen_original_exact_levels")),
                *_as_ints(item.get("stephen_yomitan_exact_levels")),
                *_as_ints(item.get("stephen_sequence_exact_levels")),
            }
        )
        lines.append(
            "| "
            f"{_escape(item.get('surface'))} | "
            f"{_escape(item.get('reading'))} | "
            f"{'yes' if item.get('matrix_row_present') else 'no'} | "
            f"{_escape(item.get('current_source_exact_levels'))} | "
            f"{'yes' if item.get('current_matrix_jlpt_normalized_exact_known') else 'no'} | "
            f"{'yes' if item.get('current_matrix_jlpt_guarded_normalized_exact_known') else 'no'} | "
            f"{'yes' if item.get('current_matrix_jlpt_effective_exact_known') else 'no'} | "
            f"{_escape(reference_levels)} | "
            f"{'yes' if item.get('current_broad_only') else 'no'} | "
            f"{_escape(item.get('same_surface_rare_pollution_risk'))} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"Recommendation: `{_escape(conclusion.get('recommendation'))}`",
            "",
            str(conclusion.get("summary") or ""),
            "",
            str(conclusion.get("interpretation") or ""),
            "",
            str(conclusion.get("next_step") or ""),
            "",
            "## License / Use Note",
            "",
            (
                "This artifact uses the stephenmk source as a diagnostic reference. "
                "The earlier source audit recorded that repository as CC BY-SA 4.0 "
                "and Tanos-derived. Direct product ingestion should be handled as a "
                "separate licensing/product decision."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _candidate_table(title: str, rows: Sequence[object]) -> list[str]:
    lines = [
        f"### {title}",
        "",
        (
            "| Surface | Reading | Core rank | Raw exact | Effective exact | "
            "Ref levels | Category | Risk | Seq source |"
        ),
        "| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for raw in rows[:12]:
        row = _as_mapping(raw)
        reference_levels = sorted(
            {
                *_as_ints(row.get("stephen_original_exact_levels")),
                *_as_ints(row.get("stephen_yomitan_exact_levels")),
                *_as_ints(row.get("stephen_sequence_exact_levels")),
            }
        )
        sequence_sources = _sequence(row.get("sequence_reference_rows"))
        sequence_text = ""
        if sequence_sources:
            source = _as_mapping(sequence_sources[0])
            sequence_text = (
                f"{source.get('sequence')} {source.get('surface')}/{source.get('reading')}"
            )
        lines.append(
            "| "
            f"{_escape(row.get('surface'))} | "
            f"{_escape(row.get('reading'))} | "
            f"{_escape(row.get('core_rank'))} | "
            f"{_escape(row.get('current_source_exact_levels'))} | "
            f"{'yes' if row.get('current_matrix_jlpt_effective_exact_known') else 'no'} | "
            f"{_escape(reference_levels)} | "
            f"`{_escape(row.get('repair_category'))}` | "
            f"{_escape(row.get('same_surface_rare_pollution_risk'))} | "
            f"{_escape(sequence_text)} |"
        )
    if not rows:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    lines.append("")
    return lines


def _component_value(
    matrix: MatrixContext,
    name: str,
    *,
    fill: float = np.nan,
) -> np.ndarray:
    try:
        index = matrix.names.index(name)
    except ValueError:
        return np.full(len(matrix.lemmas), fill, dtype=np.float32)
    return np.where(matrix.present[:, index], matrix.values[:, index], fill).astype(np.float32)


def _matrix_pair(matrix: MatrixContext, index: int) -> tuple[str, str]:
    return (
        _normalize_surface(matrix.lemmas[index]),
        _normalize_reading(matrix.readings[index]),
    )


def _first60_mask(matrix: MatrixContext) -> np.ndarray:
    cutoff = int(len(matrix.lemmas) * 0.60)
    ranks = np.asarray(matrix.core_ranks, dtype=np.float32)
    return np.isfinite(ranks) & (ranks <= float(cutoff))


def _safe_sort_rank(value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 1e12
    return result if np.isfinite(result) else 1e12


def _source_row_payload(row: SourceRow) -> dict[str, object]:
    return {
        "surface": row.surface,
        "reading": row.reading,
        "level": row.level,
        "source": row.source,
        "sequence": row.sequence,
        "definition": row.definition,
    }


def _normalize_surface(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _normalize_reading(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
    chars: list[str] = []
    for char in normalized:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def _safe_level(value: object) -> int | None:
    text = str(value or "").strip().upper()
    if text.startswith("N"):
        text = text[1:]
    try:
        level = int(text)
    except ValueError:
        return None
    if 1 <= level <= 5:
        return level
    return None


def _level_from_filename(path: Path) -> int | None:
    stem = path.stem.lower()
    if stem.startswith("n"):
        return _safe_level(stem[1:])
    return None


def _levels(values: Iterable[int] | None) -> list[int]:
    return sorted({int(value) for value in values or ()})


def _level_counts(rows: Sequence[SourceRow]) -> dict[str, int]:
    counts = Counter(row.level for row in rows)
    return {f"N{level}": counts[level] for level in sorted(counts)}


def _count(mask: np.ndarray) -> int:
    return int(np.asarray(mask, dtype=bool).sum())


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def _child_text(elem: ElementTree.Element, name: str) -> str:
    child = elem.find(name)
    return "" if child is None or child.text is None else child.text.strip()


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return []
    return list(value)


def _as_ints(value: object) -> list[int]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return []
    results: list[int] = []
    for item in value:
        try:
            results.append(int(item))
        except (TypeError, ValueError):
            continue
    return results


if __name__ == "__main__":
    raise SystemExit(main())
