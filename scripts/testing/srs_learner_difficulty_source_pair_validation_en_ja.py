#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
import gzip
import json
from pathlib import Path
import sys
import unicodedata
from typing import Iterator, Mapping, Sequence
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)
from srs_learner_difficulty_validation_failure_group_audit_en_ja import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_HOLDOUT_JSON,
    DEFAULT_VALIDATION_JSON,
    load_json,
)


PAIR = "en-ja"
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
DEFAULT_JMNEDICT_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "jmnedict-ja"
    / "JMnedict.xml"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_pair_validation_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_pair_validation_en_ja_latest.md"
)
SCALAR_TREATMENTS = frozenset({"", "vocab"})
SOURCE_MISMATCH_CLASSES = frozenset({"source_reading_mismatch"})


@dataclass(frozen=True)
class PairKey:
    lemma: str
    reading: str
    normalized_reading: str


@dataclass(frozen=True)
class ReadingEntry:
    reading: str
    normalized: str
    restrictions: tuple[str, ...] = ()


@dataclass
class SourceEvidence:
    source: str
    exact: bool = False
    surface_seen: bool = False
    reading_seen: bool = False
    restriction_mismatch: bool = False
    exact_samples: list[dict[str, object]] = field(default_factory=list)
    surface_samples: list[dict[str, object]] = field(default_factory=list)
    reading_samples: list[dict[str, object]] = field(default_factory=list)
    restriction_samples: list[dict[str, object]] = field(default_factory=list)

    def status(self) -> str:
        if self.exact:
            return "exact"
        if self.restriction_mismatch:
            return "restriction_mismatch"
        if self.surface_seen and self.reading_seen:
            return "surface_and_reading_unpaired"
        if self.surface_seen:
            return "surface_only"
        if self.reading_seen:
            return "reading_only"
        return "no_evidence"

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "status": self.status(),
            "exact": bool(self.exact),
            "surface_seen": bool(self.surface_seen),
            "reading_seen": bool(self.reading_seen),
            "restriction_mismatch": bool(self.restriction_mismatch),
            "exact_samples": self.exact_samples,
            "surface_samples": self.surface_samples,
            "reading_samples": self.reading_samples,
            "restriction_samples": self.restriction_samples,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate en-ja learner-difficulty lemma/reading pairs directly "
            "against JMDict and JMnedict entry structure."
        )
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--jmdict-path", type=Path, default=DEFAULT_JMDICT_PATH)
    parser.add_argument("--jmnedict-path", type=Path, default=DEFAULT_JMNEDICT_PATH)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        calibration_json_path=_resolve_path(args.calibration_json),
        holdout_json_path=_resolve_path(args.holdout_json),
        validation_json_path=_resolve_path(args.validation_json),
        jmdict_path=_resolve_path(args.jmdict_path),
        jmnedict_path=_resolve_path(args.jmnedict_path),
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
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
    jmdict_path: Path,
    jmnedict_path: Path,
    detail_limit: int,
) -> dict[str, object]:
    rows = all_label_rows(
        calibration_payload=load_json(calibration_json_path),
        holdout_payload=load_json(holdout_json_path),
        validation_payload=load_json(validation_json_path),
    )
    pairs = sorted(
        {pair_key_for_row(row) for row in rows if pair_key_for_row(row) is not None},
        key=lambda key: (key.lemma, key.reading),
    )
    jmdict_evidence = collect_source_evidence(
        jmdict_path,
        pairs=pairs,
        source="jmdict",
        include_name_types=False,
    )
    jmnedict_evidence = collect_source_evidence(
        jmnedict_path,
        pairs=pairs,
        source="jmnedict",
        include_name_types=True,
    )
    evaluated_rows = [
        evaluate_label_row(
            row,
            jmdict_evidence=jmdict_evidence,
            jmnedict_evidence=jmnedict_evidence,
        )
        for row in rows
    ]
    rows_with_pairs = [row for row in evaluated_rows if row.get("has_reading")]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Validate whether reviewed learner-difficulty lemma/reading rows are "
                "licensed by exact JMDict entry-pair structure, and whether unsupported "
                "pairs line up with source-reading-mismatch labels."
            ),
            "source_semantics": (
                "JMDict exact pairs support normal vocabulary source correctness. "
                "JMnedict exact pairs support name/entity source correctness but do not "
                "by themselves make an item global ladder vocabulary."
            ),
            "restriction_policy": (
                "JMDict readings with re_restr are exact only for the restricted written "
                "forms. A surface and reading in the same entry can still be invalid "
                "for a specific pair when restrictions exclude that surface."
            ),
        },
        "inputs": {
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
            "jmdict_path": _repo_or_home_path(jmdict_path),
            "jmnedict_path": _repo_or_home_path(jmnedict_path),
        },
        "summary": source_pair_summary(rows_with_pairs, detail_limit=detail_limit),
        "rows": rows_with_pairs,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
                "jmdict_path": jmdict_path,
                "jmnedict_path": jmnedict_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "validation_failure_group_audit": SCRIPT_DIR
                / "srs_learner_difficulty_validation_failure_group_audit_en_ja.py",
                **_srs_difficulty_code_paths(),
            },
            argv=sys.argv,
        ),
    }


def all_label_rows(
    *,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    validation_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(json_rows(calibration_payload, dataset_id="calibration"))
    rows.extend(json_rows(holdout_payload, dataset_id="holdout"))
    rows.extend(json_rows(validation_payload, dataset_id="stitch_validation"))
    return rows


def json_rows(payload: Mapping[str, object], *, dataset_id: str) -> list[dict[str, object]]:
    rows = []
    for index, row in enumerate(payload.get("labels", ())):
        if not isinstance(row, Mapping):
            continue
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("expected_reading") or row.get("reading") or "").strip()
        if not lemma:
            continue
        expected_value = _optional_float(row.get("expected_learner_difficulty"))
        treatment = str(row.get("treatment") or "")
        problem_class = str(row.get("expected_problem_class") or "")
        state = str(row.get("expected_candidate_state") or "")
        rows.append(
            {
                "dataset_id": dataset_id,
                "row_index": index + 1,
                "lemma": lemma,
                "reading": reading,
                "label": f"{lemma}/{reading}" if reading else lemma,
                "has_reading": bool(reading),
                "treatment": treatment,
                "expected_candidate_state": state,
                "expected_problem_class": problem_class,
                "expected_presentation_mode": str(row.get("expected_presentation_mode") or ""),
                "expected_learner_difficulty": _rounded(expected_value),
                "target": (
                    "scalar_vocab"
                    if expected_value is not None
                    and treatment in SCALAR_TREATMENTS
                    and (not state or state in {"normal_vocab", "deprioritized_vocab"})
                    else "source_mismatch_review"
                    if problem_class in SOURCE_MISMATCH_CLASSES
                    else "non_scalar"
                ),
                "rationale": str(row.get("rationale") or "")[:220],
            }
        )
    return rows


def pair_key_for_row(row: Mapping[str, object]) -> PairKey | None:
    lemma = str(row.get("lemma") or "").strip()
    reading = str(row.get("reading") or "").strip()
    if not lemma or not reading:
        return None
    return PairKey(
        lemma=lemma,
        reading=reading,
        normalized_reading=normalize_reading(reading),
    )


def collect_source_evidence(
    path: Path,
    *,
    pairs: Sequence[PairKey],
    source: str,
    include_name_types: bool,
) -> dict[PairKey, SourceEvidence]:
    evidence_by_pair = {key: SourceEvidence(source=source) for key in pairs}
    if not path.exists() or not path.is_file() or not pairs:
        return evidence_by_pair
    surface_to_pairs: dict[str, list[PairKey]] = {}
    reading_to_pairs: dict[str, list[PairKey]] = {}
    for key in pairs:
        surface_to_pairs.setdefault(key.lemma, []).append(key)
        if not contains_kanji(key.lemma):
            surface_to_pairs.setdefault(normalize_reading(key.lemma), []).append(key)
        reading_to_pairs.setdefault(key.normalized_reading, []).append(key)
    try:
        with xml_text_stream(path) as source_stream:
            context = ElementTree.iterparse(source_stream, events=("end",))
            for _event, elem in context:
                if elem.tag != "entry":
                    continue
                kanji_forms = collect_texts(elem.findall("k_ele/keb"))
                reading_entries = reading_entries_for_xml(elem)
                reading_forms = tuple(entry.reading for entry in reading_entries)
                candidate_pairs = candidate_pairs_for_entry(
                    kanji_forms=kanji_forms,
                    reading_entries=reading_entries,
                    surface_to_pairs=surface_to_pairs,
                    reading_to_pairs=reading_to_pairs,
                )
                if candidate_pairs:
                    name_types = (
                        collect_texts(elem.findall("trans/name_type")) if include_name_types else ()
                    )
                    update_evidence_for_entry(
                        candidate_pairs,
                        evidence_by_pair=evidence_by_pair,
                        kanji_forms=kanji_forms,
                        reading_entries=reading_entries,
                        reading_forms=reading_forms,
                        source=source,
                        name_types=name_types,
                    )
                elem.clear()
    except (ElementTree.ParseError, OSError):
        return evidence_by_pair
    return evidence_by_pair


def candidate_pairs_for_entry(
    *,
    kanji_forms: Sequence[str],
    reading_entries: Sequence[ReadingEntry],
    surface_to_pairs: Mapping[str, Sequence[PairKey]],
    reading_to_pairs: Mapping[str, Sequence[PairKey]],
) -> list[PairKey]:
    found: dict[PairKey, None] = {}
    for form in kanji_forms:
        for key in surface_to_pairs.get(form, ()):
            found[key] = None
    for entry in reading_entries:
        for key in surface_to_pairs.get(entry.reading, ()):
            found[key] = None
        for key in surface_to_pairs.get(entry.normalized, ()):
            found[key] = None
        for key in reading_to_pairs.get(entry.normalized, ()):
            found[key] = None
    return list(found)


def update_evidence_for_entry(
    pairs: Sequence[PairKey],
    *,
    evidence_by_pair: Mapping[PairKey, SourceEvidence],
    kanji_forms: Sequence[str],
    reading_entries: Sequence[ReadingEntry],
    reading_forms: Sequence[str],
    source: str,
    name_types: Sequence[str],
) -> None:
    kanji_set = set(kanji_forms)
    reading_set = set(reading_forms)
    normalized_reading_set = {normalize_reading(value) for value in reading_forms}
    for key in pairs:
        evidence = evidence_by_pair[key]
        surface_in_kanji = key.lemma in kanji_set
        surface_in_reading = key.lemma in reading_set or (
            not contains_kanji(key.lemma) and normalize_reading(key.lemma) in normalized_reading_set
        )
        matched_readings = [
            entry for entry in reading_entries if entry.normalized == key.normalized_reading
        ]
        if surface_in_kanji or surface_in_reading:
            evidence.surface_seen = True
            add_sample(
                evidence.surface_samples,
                sample_for_entry(
                    source=source,
                    kanji_forms=kanji_forms,
                    reading_forms=reading_forms,
                    matched_readings=matched_readings,
                    name_types=name_types,
                ),
            )
        if matched_readings:
            evidence.reading_seen = True
            add_sample(
                evidence.reading_samples,
                sample_for_entry(
                    source=source,
                    kanji_forms=kanji_forms,
                    reading_forms=reading_forms,
                    matched_readings=matched_readings,
                    name_types=name_types,
                ),
            )
        if surface_in_reading and normalize_reading(key.lemma) == key.normalized_reading:
            evidence.exact = True
            add_sample(
                evidence.exact_samples,
                sample_for_entry(
                    source=source,
                    kanji_forms=kanji_forms,
                    reading_forms=reading_forms,
                    matched_readings=matched_readings,
                    name_types=name_types,
                    match_type="reading_form",
                ),
            )
            continue
        if not surface_in_kanji or not matched_readings:
            continue
        allowed = [
            entry
            for entry in matched_readings
            if not entry.restrictions or key.lemma in entry.restrictions
        ]
        if allowed:
            evidence.exact = True
            add_sample(
                evidence.exact_samples,
                sample_for_entry(
                    source=source,
                    kanji_forms=kanji_forms,
                    reading_forms=reading_forms,
                    matched_readings=allowed,
                    name_types=name_types,
                    match_type="kanji_reading_pair",
                ),
            )
        else:
            evidence.restriction_mismatch = True
            add_sample(
                evidence.restriction_samples,
                sample_for_entry(
                    source=source,
                    kanji_forms=kanji_forms,
                    reading_forms=reading_forms,
                    matched_readings=matched_readings,
                    name_types=name_types,
                    match_type="reading_restricted_to_other_forms",
                ),
            )


def evaluate_label_row(
    row: Mapping[str, object],
    *,
    jmdict_evidence: Mapping[PairKey, SourceEvidence],
    jmnedict_evidence: Mapping[PairKey, SourceEvidence],
) -> dict[str, object]:
    key = pair_key_for_row(row)
    if key is None:
        return dict(row)
    jmdict = jmdict_evidence.get(key, SourceEvidence(source="jmdict"))
    jmnedict = jmnedict_evidence.get(key, SourceEvidence(source="jmnedict"))
    primary_status = primary_pair_status(jmdict, jmnedict)
    gate_recommendation = gate_recommendation_for_status(primary_status)
    evaluated = dict(row)
    evaluated.update(
        {
            "normalized_reading": key.normalized_reading,
            "jmdict_status": jmdict.status(),
            "jmnedict_status": jmnedict.status(),
            "jmdict_vocab_pair_supported": bool(jmdict.exact),
            "primary_pair_status": primary_status,
            "gate_recommendation": gate_recommendation,
            "jmdict": jmdict.to_dict(),
            "jmnedict": jmnedict.to_dict(),
            "validator_supports_source_mismatch": not jmdict.exact,
        }
    )
    return evaluated


def primary_pair_status(jmdict: SourceEvidence, jmnedict: SourceEvidence) -> str:
    if jmdict.exact:
        return "jmdict_exact"
    if jmnedict.exact:
        return "jmnedict_exact_name"
    if jmdict.restriction_mismatch:
        return "jmdict_restriction_mismatch"
    jmdict_status = jmdict.status()
    if jmdict_status in {"surface_and_reading_unpaired", "surface_only", "reading_only"}:
        return f"jmdict_{jmdict_status}"
    jmnedict_status = jmnedict.status()
    if jmnedict_status in {"surface_and_reading_unpaired", "surface_only", "reading_only"}:
        return f"jmnedict_{jmnedict_status}"
    return "unsupported_pair"


def gate_recommendation_for_status(status: str) -> str:
    if status == "jmdict_exact":
        return "source_pair_ok_for_vocab_lane"
    if status == "jmnedict_exact_name":
        return "name_or_entity_lane_review"
    if status in {
        "jmdict_restriction_mismatch",
        "jmdict_surface_and_reading_unpaired",
        "jmdict_surface_only",
        "jmdict_reading_only",
    }:
        return "source_pair_review"
    return "missing_source_pair_review"


def source_pair_summary(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    validation_rows = [row for row in rows if row.get("dataset_id") == "stitch_validation"]
    scalar_rows = [row for row in rows if row.get("target") == "scalar_vocab"]
    source_mismatch_rows = [
        row for row in rows if row.get("expected_problem_class") in SOURCE_MISMATCH_CLASSES
    ]
    validation_source_mismatch_rows = [
        row
        for row in validation_rows
        if row.get("expected_problem_class") in SOURCE_MISMATCH_CLASSES
    ]
    source_mismatch_caught = [
        row for row in source_mismatch_rows if row.get("validator_supports_source_mismatch")
    ]
    validation_source_mismatch_caught = [
        row
        for row in validation_source_mismatch_rows
        if row.get("validator_supports_source_mismatch")
    ]
    scalar_not_jmdict_exact = [
        row for row in scalar_rows if row.get("primary_pair_status") != "jmdict_exact"
    ]
    non_jmdict_exact = [row for row in rows if row.get("primary_pair_status") != "jmdict_exact"]
    validation_scalar_not_jmdict_exact = [
        row
        for row in validation_rows
        if row.get("target") == "scalar_vocab" and row.get("primary_pair_status") != "jmdict_exact"
    ]
    return {
        "row_count_with_reading": len(rows),
        "by_dataset": nested_count(rows, "dataset_id", "primary_pair_status"),
        "by_target": nested_count(rows, "target", "primary_pair_status"),
        "by_gate_recommendation": count_values(row.get("gate_recommendation") for row in rows),
        "validation_primary_status_counts": count_values(
            row.get("primary_pair_status") for row in validation_rows
        ),
        "source_mismatch_support": {
            "criterion": "source-mismatch support means the pair is not JMDict-exact for the normal vocabulary lane; JMnedict exact name support is reported separately.",
            "all_source_mismatch_rows": len(source_mismatch_rows),
            "all_source_mismatch_caught": len(source_mismatch_caught),
            "all_source_mismatch_recall": _rounded(
                len(source_mismatch_caught) / len(source_mismatch_rows)
                if source_mismatch_rows
                else None
            ),
            "validation_source_mismatch_rows": len(validation_source_mismatch_rows),
            "validation_source_mismatch_caught": len(validation_source_mismatch_caught),
            "validation_source_mismatch_recall": _rounded(
                len(validation_source_mismatch_caught) / len(validation_source_mismatch_rows)
                if validation_source_mismatch_rows
                else None
            ),
        },
        "scalar_collateral_if_jmdict_exact_required": {
            "all_scalar_rows": len(scalar_rows),
            "all_scalar_not_jmdict_exact": len(scalar_not_jmdict_exact),
            "validation_scalar_rows": len(
                [row for row in validation_rows if row.get("target") == "scalar_vocab"]
            ),
            "validation_scalar_not_jmdict_exact": len(validation_scalar_not_jmdict_exact),
        },
        "non_jmdict_exact_decision_pack": compact_rows(
            non_jmdict_exact,
            limit=detail_limit,
        ),
        "source_mismatch_rows": compact_rows(source_mismatch_rows, limit=detail_limit),
        "validation_scalar_not_jmdict_exact_examples": compact_rows(
            validation_scalar_not_jmdict_exact,
            limit=detail_limit,
        ),
        "non_jmdict_exact_but_jmnedict_name_examples": compact_rows(
            [row for row in rows if row.get("primary_pair_status") == "jmnedict_exact_name"],
            limit=detail_limit,
        ),
        "interpretation": interpretation(
            source_mismatch_rows=source_mismatch_rows,
            source_mismatch_caught=source_mismatch_caught,
            scalar_rows=scalar_rows,
            scalar_not_jmdict_exact=scalar_not_jmdict_exact,
        ),
    }


def interpretation(
    *,
    source_mismatch_rows: Sequence[Mapping[str, object]],
    source_mismatch_caught: Sequence[Mapping[str, object]],
    scalar_rows: Sequence[Mapping[str, object]],
    scalar_not_jmdict_exact: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    mismatch_recall = (
        len(source_mismatch_caught) / len(source_mismatch_rows) if source_mismatch_rows else None
    )
    scalar_collateral = len(scalar_not_jmdict_exact) / len(scalar_rows) if scalar_rows else None
    return {
        "source_mismatch_recall": _rounded(mismatch_recall),
        "scalar_collateral_rate_if_hard_gate": _rounded(scalar_collateral),
        "recommendation": (
            "Use exact source-pair validation as a review/source-fix lane, then inspect "
            "scalar collateral before making it a hard admission gate."
        ),
        "why_not_scalar_tuning": (
            "This validator detects whether the pair itself is source-licensed. That is "
            "orthogonal to tuning a 0-1 presentation-priority score after the candidate "
            "has entered the normal-vocabulary lane."
        ),
    }


def compact_rows(rows: Sequence[Mapping[str, object]], *, limit: int) -> list[dict[str, object]]:
    output = []
    for row in rows[:limit]:
        output.append(
            {
                "dataset_id": row.get("dataset_id"),
                "label": row.get("label"),
                "target": row.get("target"),
                "treatment": row.get("treatment"),
                "expected_problem_class": row.get("expected_problem_class"),
                "expected_learner_difficulty": row.get("expected_learner_difficulty"),
                "primary_pair_status": row.get("primary_pair_status"),
                "gate_recommendation": row.get("gate_recommendation"),
                "jmdict_status": row.get("jmdict_status"),
                "jmnedict_status": row.get("jmnedict_status"),
                "jmdict_samples": _mapping(row.get("jmdict")).get("exact_samples")
                or _mapping(row.get("jmdict")).get("restriction_samples")
                or _mapping(row.get("jmdict")).get("surface_samples")
                or _mapping(row.get("jmdict")).get("reading_samples"),
                "rationale": row.get("rationale"),
            }
        )
    return output


def nested_count(
    rows: Sequence[Mapping[str, object]],
    outer_key: str,
    inner_key: str,
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        outer = str(row.get(outer_key) or "")
        inner = str(row.get(inner_key) or "")
        result.setdefault(outer, {})
        result[outer][inner] = result[outer].get(inner, 0) + 1
    return result


def count_values(values: Sequence[object] | Iterator[object]) -> dict[str, int]:
    return dict(sorted(Counter(str(value or "") for value in values).items()))


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    source_mismatch = _mapping(summary.get("source_mismatch_support"))
    scalar_collateral = _mapping(summary.get("scalar_collateral_if_jmdict_exact_required"))
    interpretation_row = _mapping(summary.get("interpretation"))
    lines = [
        "# en-ja Source Pair Validation Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "## Scope",
        "",
        f"- Rows with lemma/reading pairs: `{_escape(summary.get('row_count_with_reading'))}`",
        f"- Source-mismatch criterion: {_escape(source_mismatch.get('criterion'))}",
        f"- Validation source-mismatch recall: "
        f"`{_escape(source_mismatch.get('validation_source_mismatch_recall'))}` "
        f"({_escape(source_mismatch.get('validation_source_mismatch_caught'))}/"
        f"{_escape(source_mismatch.get('validation_source_mismatch_rows'))})",
        "- Validation scalar rows that are not JMDict-exact if used as hard gate: "
        f"`{_escape(scalar_collateral.get('validation_scalar_not_jmdict_exact'))}`/"
        f"`{_escape(scalar_collateral.get('validation_scalar_rows'))}`",
        "",
        "## Validation Status Counts",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in _mapping(summary.get("validation_primary_status_counts")).items():
        lines.append(f"| `{_escape(status)}` | {int(count)} |")
    lines.extend(["", "## Gate Recommendation Counts", ""])
    lines.extend(count_table(summary.get("by_gate_recommendation")))
    lines.extend(["", "## Non-JMDict-Exact Decision Pack", ""])
    lines.extend(row_table(summary.get("non_jmdict_exact_decision_pack")))
    lines.extend(["", "## Source Mismatch Rows", ""])
    lines.extend(row_table(summary.get("source_mismatch_rows")))
    lines.extend(["", "## Validation Scalar Collateral If Hard-Gated", ""])
    lines.extend(row_table(summary.get("validation_scalar_not_jmdict_exact_examples")))
    lines.extend(["", "## Name/Entity Exact Examples", ""])
    lines.extend(row_table(summary.get("non_jmdict_exact_but_jmnedict_name_examples")))
    lines.extend(["", "## Interpretation", ""])
    lines.append(
        f"- Source-mismatch recall: `{_escape(interpretation_row.get('source_mismatch_recall'))}`"
    )
    lines.append(
        "- Scalar collateral rate if hard-gated: "
        f"`{_escape(interpretation_row.get('scalar_collateral_rate_if_hard_gate'))}`"
    )
    lines.append(f"- Recommendation: {_escape(interpretation_row.get('recommendation'))}")
    lines.append(f"- Shape distinction: {_escape(interpretation_row.get('why_not_scalar_tuning'))}")
    return "\n".join(lines).rstrip() + "\n"


def count_table(payload: object) -> list[str]:
    lines = ["| Value | Count |", "| --- | ---: |"]
    for key, value in _mapping(payload).items():
        lines.append(f"| `{_escape(key)}` | {int(value)} |")
    return lines


def row_table(rows: object) -> list[str]:
    values = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []
    if not values:
        return ["None."]
    lines = [
        "| Dataset | Label | Target | Class | Status | Gate | JMDict | JMnedict | Rationale |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in values:
        lines.append(
            f"| `{_escape(row.get('dataset_id'))}` | {_escape(row.get('label'))} | "
            f"`{_escape(row.get('target'))}` | "
            f"`{_escape(row.get('expected_problem_class'))}` | "
            f"`{_escape(row.get('primary_pair_status'))}` | "
            f"`{_escape(row.get('gate_recommendation'))}` | "
            f"`{_escape(row.get('jmdict_status'))}` | "
            f"`{_escape(row.get('jmnedict_status'))}` | "
            f"{_escape(row.get('rationale'))} |"
        )
    return lines


@contextmanager
def xml_text_stream(path: Path):
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as handle:
            yield handle
        return
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        yield handle


def collect_texts(nodes: Sequence[ElementTree.Element]) -> tuple[str, ...]:
    values: list[str] = []
    for node in nodes:
        text = node_text(node)
        if text and text not in values:
            values.append(text)
    return tuple(values)


def reading_entries_for_xml(elem: ElementTree.Element) -> tuple[ReadingEntry, ...]:
    entries = []
    for r_ele in elem.findall("r_ele"):
        reading = node_text(r_ele.find("reb"))
        if not reading:
            continue
        entries.append(
            ReadingEntry(
                reading=reading,
                normalized=normalize_reading(reading),
                restrictions=collect_texts(r_ele.findall("re_restr")),
            )
        )
    return tuple(entries)


def node_text(node: ElementTree.Element | None) -> str:
    if node is None:
        return ""
    return str(node.text or "").strip()


def normalize_reading(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "").strip())
    chars = []
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def contains_kanji(value: object) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in str(value or ""))


def add_sample(samples: list[dict[str, object]], sample: dict[str, object]) -> None:
    if len(samples) >= 4:
        return
    if sample not in samples:
        samples.append(sample)


def sample_for_entry(
    *,
    source: str,
    kanji_forms: Sequence[str],
    reading_forms: Sequence[str],
    matched_readings: Sequence[ReadingEntry],
    name_types: Sequence[str],
    match_type: str = "",
) -> dict[str, object]:
    sample: dict[str, object] = {
        "source": source,
        "kanji_forms": list(kanji_forms[:8]),
        "reading_forms": list(reading_forms[:8]),
    }
    if matched_readings:
        sample["matched_readings"] = [
            {
                "reading": entry.reading,
                "restrictions": list(entry.restrictions),
            }
            for entry in matched_readings[:8]
        ]
    if name_types:
        sample["name_types"] = list(name_types[:8])
    if match_type:
        sample["match_type"] = match_type
    return sample


if __name__ == "__main__":
    raise SystemExit(main())
