#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import default_frequency_db_path  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.admission_features import normalize_topic_string_list  # noqa: E402
from lexishift_core.srs.pos_overlay import (  # noqa: E402
    pos_overlay_resource_payload,
    resolve_pair_pos_overlay,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402


PAIR = "en-es"
DEFAULT_TOP_N = 10000
DEFAULT_SAMPLE_LIMIT = 20
DEFAULT_SOURCE_LABEL = "freq-es-spalex-v1"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_signal_palette_en_es_latest.md"
)
DEFAULT_LEARNER_SOURCE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_es_latest.json"
)
BROAD_LEARNER_SOURCE_IDS = frozenset({"openlingo_mit_spanish_dictionary"})

TOPIC_COLUMNS = ("sense_topics", "topics", "topic", "profile_topics")
RAW_FREQUENCY_SIGNAL_COLUMNS = (
    "id",
    "core_rank",
    "rank",
    "pmw",
    "freq",
    "frequency",
    "core_frequency",
    "source_family",
    "source_rank",
    "source_frequency",
    "spalex_rank",
    "spalex_freq",
    "spalex_zipf",
    "spalex_prevalence_total",
    "spalex_percent_total",
    "cde_rank",
    "cde_freq",
    "cde_pos",
    "pos",
    "pos_source",
    "pos_canonical",
    "topics",
    "topic_source",
)
DICTIONARY_MARKED_TERMS = frozenset(
    {
        "archaic",
        "dated",
        "dialectal",
        "formal",
        "informal",
        "literary",
        "obsolete",
        "rare",
        "regional",
        "slang",
        "vulgar",
    }
)
DICTIONARY_REGION_TERMS = frozenset(
    {
        "andalusia",
        "andean",
        "argentina",
        "argentine",
        "bolivia",
        "bolivian",
        "canary-islands",
        "central-america",
        "chile",
        "chilean",
        "colombia",
        "colombian",
        "costa-rica",
        "costa-rican",
        "cuba",
        "cuban",
        "dominican-republic",
        "ecuador",
        "ecuadorian",
        "el-salvador",
        "guatemala",
        "guatemalan",
        "honduras",
        "honduran",
        "latin-america",
        "latin-american",
        "mexican",
        "mexico",
        "nicaragua",
        "nicaraguan",
        "panama",
        "paraguay",
        "peru",
        "peruvian",
        "peninsular",
        "rioplatense",
        "salvadoran",
        "south-america",
        "spain",
        "uruguay",
        "venezuelan",
        "venezuela",
    }
)
DICTIONARY_COLLOQUIAL_TERMS = frozenset({"colloquial", "informal", "slang"})
DICTIONARY_SENSITIVE_TERMS = frozenset({"derogatory", "offensive", "vulgar"})
DICTIONARY_RARE_DATED_TERMS = frozenset(
    {"archaic", "dated", "dialectal", "literary", "obsolete", "rare", "uncommon"}
)
SPANISH_DIACRITICS = frozenset("áéíóúüñÁÉÍÓÚÜÑ")
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", re.UNICODE)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a read-only signal palette for en-es learner-difficulty model design. "
            "This inventories currently available signals; it does not add manual labels "
            "or change production scoring."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--pos-overlay-path", type=Path)
    parser.add_argument("--kaikki-forward-db", type=Path)
    parser.add_argument("--learner-source-json", type=Path, default=DEFAULT_LEARNER_SOURCE_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--rows-jsonl-out",
        type=Path,
        help="Optional row-level signal export for downstream formula sweeps.",
    )
    parser.add_argument(
        "--include-rows-in-json",
        action="store_true",
        help="Embed row-level signals in the main JSON report. Defaults off to keep reports compact.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        pos_overlay_path=args.pos_overlay_path,
        kaikki_forward_db=args.kaikki_forward_db,
        learner_source_json=args.learner_source_json,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        include_rows=bool(args.include_rows_in_json or args.rows_jsonl_out),
    )
    signal_rows = _as_sequence(report.get("signal_rows"))
    if args.rows_jsonl_out:
        args.rows_jsonl_out.parent.mkdir(parents=True, exist_ok=True)
        with args.rows_jsonl_out.open("w", encoding="utf-8") as handle:
            for row in signal_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Wrote row-level signal artifact to {args.rows_jsonl_out}")
    if not args.include_rows_in_json:
        report.pop("signal_rows", None)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    frequency_db: Path | None = None,
    pos_overlay_path: Path | None = None,
    kaikki_forward_db: Path | None = None,
    learner_source_json: Path | None = DEFAULT_LEARNER_SOURCE_JSON,
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    include_rows: bool = False,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    paths = build_helper_paths()
    resolved_frequency_db = _resolve_frequency_db(frequency_db, paths.frequency_packs_dir)
    pos_ref = resolve_pair_pos_overlay(
        paths,
        pair=PAIR,
        pos_overlay_path=pos_overlay_path,
    )
    resolved_kaikki_forward_db = _resolve_kaikki_forward_db(kaikki_forward_db, paths.data_root)
    learner_source_index = _load_learner_source_index(learner_source_json)
    frequency_summary = _sqlite_table_summary(resolved_frequency_db, table="frequency")
    base_inputs = {
        "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
        "pos_overlay": pos_overlay_resource_payload(pos_ref),
        "kaikki_forward_db": str(resolved_kaikki_forward_db)
        if resolved_kaikki_forward_db
        else None,
        "learner_source_json": str(learner_source_json) if learner_source_json else None,
        "top_n": int(top_n),
        "sample_limit": int(sample_limit),
    }
    if not frequency_summary["exists"]:
        return _review_report(
            generated_at=generated_at,
            inputs=base_inputs,
            frequency_summary=frequency_summary,
            issues=("frequency_db_missing",),
        )
    if not frequency_summary["table_exists"]:
        return _review_report(
            generated_at=generated_at,
            inputs=base_inputs,
            frequency_summary=frequency_summary,
            issues=("frequency_table_missing",),
        )

    try:
        seeds = build_seed_candidates(
            frequency_db=resolved_frequency_db,
            config=SeedSelectionConfig(
                language_pair=PAIR,
                top_n=top_n,
                require_jmdict=False,
                source_label=DEFAULT_SOURCE_LABEL,
                sort_by_admission_weight=False,
                pos_overlay_path=pos_ref.path if pos_ref else None,
            ),
        )
    except Exception as exc:  # pragma: no cover - defensive path for corrupt local packs.
        return _review_report(
            generated_at=generated_at,
            inputs=base_inputs,
            frequency_summary=frequency_summary,
            issues=("seed_build_failed",),
            extra_findings=(_finding("FAIL", "seed_build_failed", f"Seed build failed: {exc}"),),
        )

    raw_rows_by_lemma = _raw_frequency_rows_by_lemma(
        resolved_frequency_db,
        [seed.lemma for seed in seeds],
        columns=frequency_summary["columns"],
    )
    dictionary_index = _load_kaikki_signal_index(
        resolved_kaikki_forward_db,
        [seed.lemma for seed in seeds],
    )
    rows = [
        _palette_row(
            seed=seed,
            raw_frequency_row=raw_rows_by_lemma.get(seed.lemma, {}),
            dictionary_signals=dictionary_index["by_lemma"].get(seed.lemma.lower(), {}),
            learner_source_signals=_learner_source_for(seed.lemma, learner_source_index),
            learner_source_context=_learner_source_context(seed.lemma, learner_source_index),
        )
        for seed in seeds
    ]
    coverage = _coverage_summary(
        rows=rows,
        frequency_columns=frequency_summary["columns"],
        pos_overlay_present=bool(pos_ref),
        dictionary_index=dictionary_index,
        learner_source_index=learner_source_index,
    )
    findings = _build_findings(
        rows=rows,
        frequency_summary=frequency_summary,
        coverage=coverage,
        dictionary_index=dictionary_index,
        pos_overlay_present=bool(pos_ref),
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    report = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_es_signal_palette_ready" if status == "ok" else "en_es_signal_palette_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": base_inputs,
        "methodology": {
            "runtime_policy_change": "none",
            "manual_corrections": "none",
            "formula_selection": "none",
            "seed_path": (
                "Uses build_seed_candidates for en-es so the palette reflects signals "
                "available to SRS admission and future learner-difficulty formulas."
            ),
            "raw_sqlite_inspection": (
                "Also inspects frequency SQLite columns directly so existing SPALEX and "
                "source-profile fields are visible even before formulas consume them."
            ),
            "dictionary_metadata": (
                "Optionally inspects installed wiktionary-es-en/Kaikki auxiliary tables "
                "for POS, sense/gloss counts, topics, tags, categories, and form-of/alt-of flags."
            ),
            "learner_source_overlay": (
                "Optionally joins the en-es learner-source audit overlay when present. "
                "Those signals are sidecar evidence only; formulas must choose whether "
                "and how to weight them."
            ),
        },
        "frequency_pack": frequency_summary,
        "dictionary_pack": {
            key: value for key, value in dictionary_index.items() if key != "by_lemma"
        },
        "learner_source_pack": {
            key: value for key, value in learner_source_index.items() if key != "by_lemma"
        },
        "summary": {
            "selected_count": len(rows),
            "unique_lemma_count": len({row["lemma"] for row in rows}),
            "issues": [row["code"] for row in findings if row["level"] != "OK"],
            "coverage": coverage["headline"],
        },
        "coverage": coverage,
        "samples": _sample_groups(rows, sample_limit=sample_limit),
        "findings": findings,
        "limitations": [
            "This is signal inventory only; it does not assert that any signal should receive positive or negative formula weight.",
            "No CEFR, school-grade, or learner-curriculum Spanish source is currently wired here.",
            "The optional learner-source overlay is weak curriculum/core evidence. It is not authoritative CEFR truth.",
            "Kaikki/Wiktionary tags and categories are source metadata. They need precision checks before acting as hard difficulty signals.",
            "Spanish orthographic/form features are weak internal cues and should be treated as tie-breaker or interaction candidates, not a primary ladder.",
        ],
    }
    if include_rows:
        report["signal_rows"] = rows
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    lines: list[str] = []
    lines.append("# en-es Learner Difficulty Signal Palette")
    lines.append("")
    lines.append(f"Status: `{report.get('status')}`")
    lines.append(f"Generated: `{report.get('generated_at')}`")
    lines.append("")
    lines.append(
        "Purpose: enumerate the evidence currently available for en-es learner-difficulty "
        "formula design without adding manual corrections or changing production scoring."
    )
    lines.append("")
    inputs = _as_mapping(report.get("inputs"))
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Frequency DB: `{inputs.get('frequency_db')}`")
    pos_overlay = _as_mapping(inputs.get("pos_overlay"))
    lines.append(
        "- POS overlay: "
        f"`{pos_overlay.get('pos_overlay_id') or 'missing'}` "
        f"({pos_overlay.get('pos_overlay_resolution')})"
    )
    lines.append(f"- Kaikki/Wiktionary DB: `{inputs.get('kaikki_forward_db')}`")
    lines.append(f"- Learner-source overlay: `{inputs.get('learner_source_json')}`")
    lines.append(f"- Top N: `{inputs.get('top_n')}`")
    lines.append("")

    summary = _as_mapping(report.get("summary"))
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Selected rows: `{summary.get('selected_count', 0)}`")
    lines.append(f"- Unique lemmas: `{summary.get('unique_lemma_count', 0)}`")
    issues = summary.get("issues") or []
    lines.append(f"- Issues: `{', '.join(str(item) for item in issues) if issues else 'none'}`")
    lines.append("")

    coverage = _as_mapping(report.get("coverage"))
    lines.append("## Headline Coverage")
    lines.append("")
    lines.append("| Signal group | Covered rows | Coverage |")
    lines.append("| --- | ---: | ---: |")
    for row in _as_sequence(_as_mapping(coverage.get("headline")).get("rows")):
        item = _as_mapping(row)
        lines.append(
            f"| {item.get('label')} | {item.get('count', 0)} | {_pct(item.get('ratio', 0.0))} |"
        )
    lines.append("")

    lines.append("## Raw Frequency Columns")
    lines.append("")
    lines.append("| Column | Present | Non-null rows | Coverage |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in _as_sequence(coverage.get("raw_frequency_columns")):
        item = _as_mapping(row)
        lines.append(
            f"| `{item.get('column')}` | {item.get('present')} | "
            f"{item.get('non_null_count', 0)} | {_pct(item.get('coverage_ratio', 0.0))} |"
        )
    lines.append("")

    lines.append("## POS / Classification")
    lines.append("")
    lines.append("Top POS buckets:")
    lines.append("")
    lines.append("| Bucket | Rows |")
    lines.append("| --- | ---: |")
    for bucket, count in _as_mapping(coverage.get("pos_bucket_counts")).items():
        lines.append(f"| `{bucket}` | {count} |")
    lines.append("")
    lines.append("Candidate states:")
    lines.append("")
    lines.append("| State | Rows |")
    lines.append("| --- | ---: |")
    for state, count in _as_mapping(coverage.get("candidate_state_counts")).items():
        lines.append(f"| `{state}` | {count} |")
    lines.append("")

    lines.append("## Learner/Core Source Overlay")
    lines.append("")
    learner_pack = _as_mapping(report.get("learner_source_pack"))
    lines.append(f"- Exists: `{learner_pack.get('exists')}`")
    lines.append(f"- Status: `{learner_pack.get('status')}`")
    lines.append(f"- Overlay terms: `{learner_pack.get('overlay_term_count', 0)}`")
    lines.append(
        f"- Rows with learner-source evidence: `{coverage.get('learner_source_count', 0)}`"
    )
    source_counts = _as_mapping(coverage.get("learner_source_counts"))
    if source_counts:
        lines.append("")
        lines.append("| Source | Rows |")
        lines.append("| --- | ---: |")
        for source_id, count in source_counts.items():
            lines.append(f"| `{source_id}` | {count} |")
    lines.append("")

    lines.append("## Dictionary Metadata")
    lines.append("")
    dictionary_pack = _as_mapping(report.get("dictionary_pack"))
    lines.append(f"- Exists: `{dictionary_pack.get('exists')}`")
    lines.append(f"- Entry table present: `{dictionary_pack.get('entry_meta_table_exists')}`")
    lines.append(f"- Sense table present: `{dictionary_pack.get('sense_glosses_table_exists')}`")
    lines.append(
        f"- Rows with dictionary entry evidence: `{coverage.get('dictionary_entry_count', 0)}`"
    )
    lines.append(f"- Rows with sense/gloss evidence: `{coverage.get('dictionary_sense_count', 0)}`")
    lines.append(f"- Rows with dictionary topics: `{coverage.get('dictionary_topic_count', 0)}`")
    dictionary_topics = _as_sequence(coverage.get("top_dictionary_topics"))
    if dictionary_topics:
        lines.append("")
        lines.append("Top dictionary topics:")
        lines.append("")
        lines.append("| Topic | Rows | Coverage |")
        lines.append("| --- | ---: | ---: |")
        for raw in dictionary_topics[:15]:
            item = _as_mapping(raw)
            lines.append(
                f"| `{item.get('topic')}` | {item.get('count', 0)} | "
                f"{_pct(item.get('coverage_ratio', 0.0))} |"
            )
    lines.append("")

    samples = _as_mapping(report.get("samples"))
    for title, key in (
        ("Rank-order Sample", "rank_order"),
        ("Topic Sample", "with_topics"),
        ("Dictionary Sample", "with_dictionary"),
        ("Dictionary Topic Sample", "with_dictionary_topics"),
        ("Learner Source Sample", "with_learner_source"),
    ):
        rows = _as_sequence(samples.get(key))
        if not rows:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append(
            "| Lemma | Rank | Freq diff | POS | Topics | Learner source | Dict senses | Form cues |"
        )
        lines.append("| --- | ---: | ---: | --- | --- | --- | ---: | --- |")
        for raw in rows:
            row = _as_mapping(raw)
            dictionary = _as_mapping(row.get("dictionary"))
            learner = _as_mapping(row.get("learner_source"))
            form = _as_mapping(row.get("form"))
            form_cues = ", ".join(
                key
                for key in (
                    "has_diacritic",
                    "has_space",
                    "has_hyphen",
                    "ends_with_mente",
                    "verb_infinitive_like",
                )
                if form.get(key)
            )
            topics = ", ".join(str(item) for item in _as_sequence(row.get("topics"))) or "-"
            learner_text = "-"
            if learner:
                learner_text = (
                    f"{_fmt_float(learner.get('learner_core_score'))}/"
                    f"{_fmt_float(learner.get('confidence'))} "
                    f"{','.join(str(item) for item in _as_sequence(learner.get('source_ids'))[:3])}"
                )
            lines.append(
                f"| `{row.get('lemma')}` | {row.get('core_rank') or ''} | "
                f"{_fmt_float(row.get('frequency_difficulty'))} | "
                f"`{row.get('pos_canonical') or row.get('pos_raw') or ''}` | "
                f"{topics} | {learner_text} | {dictionary.get('sense_count', 0)} | "
                f"{form_cues or '-'} |"
            )
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| Level | Code | Message |")
    lines.append("| --- | --- | --- |")
    for raw in _as_sequence(report.get("findings")):
        item = _as_mapping(raw)
        lines.append(f"| {item.get('level')} | `{item.get('code')}` | {item.get('message')} |")
    lines.append("")

    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _palette_row(
    *,
    seed,
    raw_frequency_row: Mapping[str, object],
    dictionary_signals: Mapping[str, object],
    learner_source_signals: Mapping[str, object],
    learner_source_context: Mapping[str, object],
) -> dict[str, object]:
    metadata = _as_mapping(seed.metadata)
    topics: list[str] = []
    for column in TOPIC_COLUMNS:
        topics.extend(normalize_topic_string_list(metadata.get(column)))
    topics.extend(normalize_topic_string_list(raw_frequency_row.get("topics")))
    topics = sorted(dict.fromkeys(topics))
    raw_frequency = {
        column: _jsonable(raw_frequency_row.get(column))
        for column in RAW_FREQUENCY_SIGNAL_COLUMNS
        if column in raw_frequency_row
    }
    base_weight = _safe_float(seed.base_weight)
    return {
        "lemma": seed.lemma,
        "core_rank": _safe_float(seed.core_rank),
        "pmw": _safe_float(seed.pmw),
        "frequency_difficulty": _round_or_none(
            1.0 - base_weight if base_weight is not None else None
        ),
        "base_weight": _round_or_none(base_weight),
        "admission_weight": _round_or_none(seed.admission_weight),
        "pos_raw": seed.pos_raw,
        "pos_canonical": seed.pos_canonical,
        "pos_bucket": seed.pos_bucket,
        "pos_weight": _round_or_none(seed.pos_weight),
        "pos_mapped": bool(seed.pos_mapped),
        "pos_source_kind": metadata.get("pos_source_kind"),
        "pos_source_profile": seed.pos_source_profile,
        "pos_matched_rule": seed.pos_matched_rule,
        "pos_overlay_id": metadata.get("pos_overlay_id"),
        "pos_overlay_confidence": _round_or_none(metadata.get("pos_overlay_confidence")),
        "candidate_state": seed.candidate_state,
        "presentation_mode": seed.presentation_mode,
        "problem_class": seed.problem_class,
        "classification_confidence": seed.classification_confidence,
        "classification_reasons": list(seed.classification_reasons),
        "admission_suitability": _round_or_none(seed.admission_suitability),
        "topics": topics,
        "raw_frequency": raw_frequency,
        "dictionary": dict(dictionary_signals),
        "learner_source": dict(learner_source_signals),
        "learner_source_context": dict(learner_source_context),
        "form": _spanish_form_features(seed.lemma),
    }


def _coverage_summary(
    *,
    rows: Sequence[Mapping[str, object]],
    frequency_columns: Sequence[str],
    pos_overlay_present: bool,
    dictionary_index: Mapping[str, object],
    learner_source_index: Mapping[str, object],
) -> dict[str, object]:
    total = len(rows)
    raw_column_rows = []
    for column in RAW_FREQUENCY_SIGNAL_COLUMNS:
        present = column in frequency_columns
        count = sum(
            1 for row in rows if _present_value(_as_mapping(row.get("raw_frequency")).get(column))
        )
        raw_column_rows.append(
            {
                "column": column,
                "present": present,
                "non_null_count": count,
                "coverage_ratio": _ratio(count, total),
            }
        )
    pos_bucket_counts = Counter(str(row.get("pos_bucket") or "unknown") for row in rows)
    candidate_state_counts = Counter(str(row.get("candidate_state") or "unknown") for row in rows)
    problem_class_counts = Counter(str(row.get("problem_class") or "unknown") for row in rows)
    source_family_counts = Counter(
        str(_as_mapping(row.get("raw_frequency")).get("source_family") or "unknown") for row in rows
    )
    topic_counter: Counter[str] = Counter()
    dictionary_topic_counter: Counter[str] = Counter()
    for row in rows:
        topic_counter.update(str(item) for item in _as_sequence(row.get("topics")))
        dictionary_topic_counter.update(
            str(item) for item in _as_sequence(_as_mapping(row.get("dictionary")).get("topics"))
        )
    dictionary_entry_count = sum(
        1 for row in rows if _safe_int(_as_mapping(row.get("dictionary")).get("entry_count")) > 0
    )
    dictionary_sense_count = sum(
        1 for row in rows if _safe_int(_as_mapping(row.get("dictionary")).get("sense_count")) > 0
    )
    dictionary_marked_count = sum(
        1 for row in rows if bool(_as_mapping(row.get("dictionary")).get("marked_usage_flag"))
    )
    learner_source_count = sum(1 for row in rows if _as_mapping(row.get("learner_source")))
    broad_source_available = bool(learner_source_index.get("broad_source_available"))
    broad_source_known_count = sum(
        1
        for row in rows
        if bool(_as_mapping(row.get("learner_source_context")).get("broad_source_known"))
    )
    learner_source_counter: Counter[str] = Counter()
    for row in rows:
        learner = _as_mapping(row.get("learner_source"))
        learner_source_counter.update(str(item) for item in _as_sequence(learner.get("source_ids")))
    form_diacritic_count = sum(
        1 for row in rows if bool(_as_mapping(row.get("form")).get("has_diacritic"))
    )
    headline_rows = [
        _coverage_row("SPALEX rank/commonness", _column_count(rows, "spalex_rank"), total),
        _coverage_row("SPALEX Zipf", _column_count(rows, "spalex_zipf"), total),
        _coverage_row("Effective POS", sum(1 for row in rows if row.get("pos_raw")), total),
        _coverage_row(
            "POS overlay filled",
            sum(1 for row in rows if row.get("pos_source_kind") == "pos_overlay"),
            total,
        ),
        _coverage_row("Seed topic hints", sum(1 for row in rows if row.get("topics")), total),
        _coverage_row(
            "Dictionary topics",
            sum(1 for row in rows if _as_mapping(row.get("dictionary")).get("topics")),
            total,
        ),
        _coverage_row("Candidate classification", len(rows), total),
        _coverage_row("Dictionary entry metadata", dictionary_entry_count, total),
        _coverage_row("Dictionary sense/gloss metadata", dictionary_sense_count, total),
        _coverage_row("Dictionary marked-use cue", dictionary_marked_count, total),
        _coverage_row("Learner/core source overlay", learner_source_count, total),
        _coverage_row("Broad learner source coverage", broad_source_known_count, total),
        _coverage_row("Spanish diacritic/form cue", form_diacritic_count, total),
    ]
    return {
        "headline": {
            "total": total,
            "rows": headline_rows,
        },
        "raw_frequency_columns": raw_column_rows,
        "pos_overlay_present": pos_overlay_present,
        "pos_bucket_counts": dict(pos_bucket_counts.most_common()),
        "candidate_state_counts": dict(candidate_state_counts.most_common()),
        "problem_class_counts": dict(problem_class_counts.most_common()),
        "source_family_counts": dict(source_family_counts.most_common()),
        "top_topics": [
            {"topic": topic, "count": count, "coverage_ratio": _ratio(count, total)}
            for topic, count in topic_counter.most_common(30)
        ],
        "top_dictionary_topics": [
            {"topic": topic, "count": count, "coverage_ratio": _ratio(count, total)}
            for topic, count in dictionary_topic_counter.most_common(30)
        ],
        "dictionary_entry_count": dictionary_entry_count,
        "dictionary_sense_count": dictionary_sense_count,
        "dictionary_marked_count": dictionary_marked_count,
        "dictionary_topic_count": sum(
            1 for row in rows if _as_mapping(row.get("dictionary")).get("topics")
        ),
        "dictionary_pack_exists": bool(dictionary_index.get("exists")),
        "learner_source_count": learner_source_count,
        "learner_source_counts": dict(learner_source_counter.most_common()),
        "learner_source_pack_exists": bool(learner_source_index.get("exists")),
        "learner_source_broad_available": broad_source_available,
        "learner_source_broad_known_count": broad_source_known_count,
        "learner_source_broad_absent_count": (
            total - broad_source_known_count if broad_source_available else 0
        ),
        "form_diacritic_count": form_diacritic_count,
    }


def _sample_groups(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_limit: int,
) -> dict[str, object]:
    return {
        "rank_order": [dict(row) for row in rows[:sample_limit]],
        "with_topics": [dict(row) for row in rows if row.get("topics")][:sample_limit],
        "with_dictionary": [
            dict(row)
            for row in rows
            if _safe_int(_as_mapping(row.get("dictionary")).get("entry_count")) > 0
        ][:sample_limit],
        "with_dictionary_topics": [
            dict(row) for row in rows if _as_mapping(row.get("dictionary")).get("topics")
        ][:sample_limit],
        "with_learner_source": [
            dict(row) for row in rows if _as_mapping(row.get("learner_source"))
        ][:sample_limit],
        "marked_dictionary": [
            dict(row)
            for row in rows
            if bool(_as_mapping(row.get("dictionary")).get("marked_usage_flag"))
        ][:sample_limit],
    }


def _build_findings(
    *,
    rows: Sequence[Mapping[str, object]],
    frequency_summary: Mapping[str, object],
    coverage: Mapping[str, object],
    dictionary_index: Mapping[str, object],
    pos_overlay_present: bool,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not rows:
        findings.append(_finding("FAIL", "seed_rows_empty", "No seed candidates were selected."))
    if not frequency_summary.get("exists"):
        findings.append(_finding("FAIL", "frequency_db_missing", "Frequency SQLite is missing."))
    if not frequency_summary.get("table_exists"):
        findings.append(_finding("FAIL", "frequency_table_missing", "Frequency table is missing."))
    if not pos_overlay_present:
        findings.append(
            _finding(
                "WARN",
                "pos_overlay_missing",
                "No Spanish POS overlay was resolved; formulas can still use frequency POS if present.",
            )
        )
    if not dictionary_index.get("exists"):
        findings.append(
            _finding(
                "WARN",
                "kaikki_dictionary_missing",
                "No wiktionary-es-en/Kaikki metadata DB was resolved.",
            )
        )
    if _safe_int(coverage.get("dictionary_entry_count")) == 0:
        findings.append(
            _finding(
                "WARN",
                "dictionary_metadata_zero",
                "No selected rows had dictionary entry metadata.",
            )
        )
    if not _as_sequence(coverage.get("top_topics")) and not _as_sequence(
        coverage.get("top_dictionary_topics")
    ):
        findings.append(
            _finding("WARN", "topic_coverage_zero", "No selected rows had topic hints.")
        )
    if not any(item["level"] == "FAIL" for item in findings):
        findings.append(
            _finding(
                "OK",
                "signal_palette_ready",
                "Available en-es signals are inventoried without changing ranking behavior.",
            )
        )
    return findings


def _review_report(
    *,
    generated_at: str,
    inputs: Mapping[str, object],
    frequency_summary: Mapping[str, object],
    issues: Sequence[str],
    extra_findings: Sequence[dict[str, str]] = (),
) -> dict[str, object]:
    findings = list(extra_findings)
    for issue in issues:
        if any(row["code"] == issue for row in findings):
            continue
        findings.append(_finding("FAIL", issue, issue.replace("_", " ")))
    return {
        "schema_version": 1,
        "pair": PAIR,
        "status": "review",
        "decision": "en_es_signal_palette_needs_review",
        "generated_at": generated_at,
        "inputs": dict(inputs),
        "frequency_pack": dict(frequency_summary),
        "dictionary_pack": {},
        "summary": {
            "selected_count": 0,
            "unique_lemma_count": 0,
            "issues": list(issues),
        },
        "coverage": {},
        "samples": {},
        "findings": findings,
    }


def _resolve_frequency_db(value: Path | None, frequency_packs_dir: Path) -> Path | None:
    if value is not None:
        return Path(value).expanduser().resolve(strict=False)
    resolved = default_frequency_db_path(PAIR, frequency_packs_dir=frequency_packs_dir)
    return Path(resolved).expanduser().resolve(strict=False) if resolved else None


def _resolve_kaikki_forward_db(value: Path | None, data_root: Path) -> Path | None:
    candidates: list[Path] = []
    if value is not None:
        requested = Path(value).expanduser().resolve(strict=False)
        candidates.extend(
            (requested, requested / "main.sqlite" if requested.is_dir() else requested)
        )
        if requested.suffix == ".sqlite":
            candidates.append(requested.parent / requested.stem / "main.sqlite")
    candidates.extend(
        (
            data_root / "language_packs" / "wiktionary-es-en" / "main.sqlite",
            data_root / "language_packs" / "wiktionary-es-en.sqlite",
        )
    )
    for candidate in _unique_paths(candidates):
        if candidate.is_file():
            return candidate.expanduser().resolve(strict=False)
    return Path(value).expanduser().resolve(strict=False) if value is not None else None


def _sqlite_table_summary(path: Path | None, *, table: str) -> dict[str, object]:
    if path is None:
        return {
            "path": None,
            "exists": False,
            "table_exists": False,
            "columns": [],
            "row_count": 0,
            "distinct_lemma_count": 0,
            "metadata": {},
        }
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.is_file():
        return {
            "path": str(resolved),
            "exists": False,
            "table_exists": False,
            "columns": [],
            "row_count": 0,
            "distinct_lemma_count": 0,
            "metadata": {},
        }
    with sqlite3.connect(resolved) as conn:
        conn.row_factory = sqlite3.Row
        table_exists = _table_exists(conn, table)
        if not table_exists:
            return {
                "path": str(resolved),
                "exists": True,
                "table_exists": False,
                "columns": [],
                "row_count": 0,
                "distinct_lemma_count": 0,
                "metadata": _metadata(conn),
            }
        columns = _column_names(conn, table)
        row_count = conn.execute(f"SELECT COUNT(*) FROM {_quote_ident(table)}").fetchone()[0]
        distinct_lemma_count = 0
        if "lemma" in columns:
            distinct_lemma_count = conn.execute(
                f"SELECT COUNT(DISTINCT lemma) FROM {_quote_ident(table)} "
                "WHERE TRIM(COALESCE(lemma, '')) != ''"
            ).fetchone()[0]
        return {
            "path": str(resolved),
            "exists": True,
            "table_exists": True,
            "columns": columns,
            "row_count": int(row_count),
            "distinct_lemma_count": int(distinct_lemma_count),
            "metadata": _metadata(conn),
        }


def _raw_frequency_rows_by_lemma(
    path: Path,
    lemmas: Sequence[str],
    *,
    columns: Sequence[str],
) -> dict[str, dict[str, object]]:
    if not lemmas:
        return {}
    resolved_columns = [column for column in RAW_FREQUENCY_SIGNAL_COLUMNS if column in columns]
    if "lemma" not in columns:
        return {}
    selected = ["lemma", *resolved_columns]
    rows: dict[str, dict[str, object]] = {}
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        for chunk in _chunks([lemma for lemma in dict.fromkeys(lemmas) if lemma], size=500):
            placeholders = ", ".join("?" for _ in chunk)
            query = (
                "SELECT "
                + ", ".join(_quote_ident(column) for column in selected)
                + f" FROM frequency WHERE lemma IN ({placeholders})"
            )
            for row in conn.execute(query, chunk):
                lemma = str(row["lemma"])
                rows.setdefault(
                    lemma,
                    {column: _jsonable(row[column]) for column in selected if column != "lemma"},
                )
    return rows


def _load_kaikki_signal_index(
    path: Path | None,
    lemmas: Sequence[str],
) -> dict[str, object]:
    base = {
        "path": str(path) if path else None,
        "exists": False,
        "entry_meta_table_exists": False,
        "sense_glosses_table_exists": False,
        "by_lemma": {},
    }
    if path is None or not Path(path).is_file():
        return base
    lemma_keys = [lemma.lower() for lemma in dict.fromkeys(lemmas) if str(lemma).strip()]
    if not lemma_keys:
        base["exists"] = True
        return base
    entry_rows: dict[str, list[sqlite3.Row]] = defaultdict(list)
    sense_rows: dict[str, list[sqlite3.Row]] = defaultdict(list)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        base["exists"] = True
        entry_exists = _table_exists(conn, "entry_meta")
        sense_exists = _table_exists(conn, "sense_glosses")
        base["entry_meta_table_exists"] = entry_exists
        base["sense_glosses_table_exists"] = sense_exists
        if entry_exists and "headword_lc" in _column_names(conn, "entry_meta"):
            entry_columns = _column_names(conn, "entry_meta")
            selected = [
                column
                for column in (
                    "entry_ord",
                    "headword_lc",
                    "pos",
                    "pos_title",
                    "categories_json",
                    "forms_json",
                    "sounds_json",
                    "synonyms_json",
                    "tags_json",
                    "etymology_text",
                )
                if column in entry_columns
            ]
            for chunk in _chunks(lemma_keys, size=500):
                placeholders = ", ".join("?" for _ in chunk)
                query = (
                    "SELECT "
                    + ", ".join(_quote_ident(column) for column in selected)
                    + f" FROM entry_meta WHERE headword_lc IN ({placeholders})"
                )
                for row in conn.execute(query, chunk):
                    entry_rows[str(row["headword_lc"])].append(row)
        if sense_exists and "headword_lc" in _column_names(conn, "sense_glosses"):
            sense_columns = _column_names(conn, "sense_glosses")
            selected = [
                column
                for column in (
                    "entry_ord",
                    "sense_ord",
                    "gloss_ord",
                    "headword_lc",
                    "translation_lc",
                    "pos",
                    "tags_json",
                    "topics_json",
                    "categories_json",
                    "form_of_json",
                    "alt_of_json",
                )
                if column in sense_columns
            ]
            for chunk in _chunks(lemma_keys, size=500):
                placeholders = ", ".join("?" for _ in chunk)
                query = (
                    "SELECT "
                    + ", ".join(_quote_ident(column) for column in selected)
                    + f" FROM sense_glosses WHERE headword_lc IN ({placeholders})"
                )
                for row in conn.execute(query, chunk):
                    sense_rows[str(row["headword_lc"])].append(row)
    by_lemma: dict[str, dict[str, object]] = {}
    for key in lemma_keys:
        by_lemma[key] = _dictionary_signals(entry_rows.get(key, ()), sense_rows.get(key, ()))
    base["by_lemma"] = by_lemma
    base["entry_coverage_count"] = sum(
        1 for signals in by_lemma.values() if _safe_int(signals.get("entry_count")) > 0
    )
    base["sense_coverage_count"] = sum(
        1 for signals in by_lemma.values() if _safe_int(signals.get("sense_count")) > 0
    )
    return base


def _load_learner_source_index(path: Path | None) -> dict[str, object]:
    base: dict[str, object] = {
        "path": str(path) if path else None,
        "exists": False,
        "status": "missing",
        "overlay_term_count": 0,
        "included_source_ids": [],
        "broad_source_ids": [],
        "broad_source_available": False,
        "by_lemma": {},
    }
    if path is None or not Path(path).is_file():
        return base
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["status"] = "unreadable"
        base["error"] = str(exc)
        return base
    overlay = _as_mapping(payload.get("source_overlay"))
    sources = [
        _as_mapping(source)
        for source in _as_sequence(_as_mapping(payload.get("source_summary")).get("sources"))
    ]
    included_source_ids = sorted(
        {
            str(source.get("source_id") or "")
            for source in sources
            if source.get("decision") == "included_sidecar" and str(source.get("source_id") or "")
        }
    )
    broad_source_ids = sorted(set(included_source_ids) & BROAD_LEARNER_SOURCE_IDS)
    by_lemma = {
        _normalize_learner_source_key(key): dict(_as_mapping(value))
        for key, value in overlay.items()
        if _normalize_learner_source_key(key)
    }
    base.update(
        {
            "exists": True,
            "status": str(payload.get("status") or "unknown"),
            "decision": payload.get("decision"),
            "overlay_term_count": len(by_lemma),
            "included_source_ids": included_source_ids,
            "broad_source_ids": broad_source_ids,
            "broad_source_available": bool(broad_source_ids),
            "by_lemma": by_lemma,
        }
    )
    return base


def _learner_source_for(
    lemma: str,
    learner_source_index: Mapping[str, object],
) -> Mapping[str, object]:
    by_lemma = _as_mapping(learner_source_index.get("by_lemma"))
    key = _normalize_learner_source_key(lemma)
    if key in by_lemma:
        return _as_mapping(by_lemma.get(key))
    return {}


def _learner_source_context(
    lemma: str,
    learner_source_index: Mapping[str, object],
) -> Mapping[str, object]:
    learner = _learner_source_for(lemma, learner_source_index)
    source_ids = {str(item) for item in _as_sequence(learner.get("source_ids"))}
    broad_source_ids = {
        str(item) for item in _as_sequence(learner_source_index.get("broad_source_ids"))
    }
    broad_available = bool(learner_source_index.get("broad_source_available"))
    broad_known_ids = sorted(source_ids & broad_source_ids)
    return {
        "broad_source_available": broad_available,
        "broad_source_ids": sorted(broad_source_ids),
        "broad_source_known": bool(broad_known_ids),
        "broad_source_known_ids": broad_known_ids,
        "broad_source_absent": bool(broad_available and not broad_known_ids),
    }


def _normalize_learner_source_key(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _dictionary_signals(
    entry_rows: Sequence[sqlite3.Row],
    sense_rows: Sequence[sqlite3.Row],
) -> dict[str, object]:
    pos_values = sorted(
        {
            value
            for row in (*entry_rows, *sense_rows)
            for value in (str(row["pos"]).strip() if "pos" in row.keys() and row["pos"] else "",)
            if value
        }
    )
    tags: set[str] = set()
    categories: set[str] = set()
    topics: set[str] = set()
    forms_count = 0
    sounds_count = 0
    synonyms_count = 0
    has_etymology = False
    for row in entry_rows:
        tags.update(_json_string_set(row["tags_json"] if "tags_json" in row.keys() else None))
        categories.update(
            _json_string_set(row["categories_json"] if "categories_json" in row.keys() else None)
        )
        forms_count += len(_json_array(row["forms_json"] if "forms_json" in row.keys() else None))
        sounds_count += len(
            _json_array(row["sounds_json"] if "sounds_json" in row.keys() else None)
        )
        synonyms_count += len(
            _json_array(row["synonyms_json"] if "synonyms_json" in row.keys() else None)
        )
        has_etymology = has_etymology or bool(
            str(row["etymology_text"]).strip()
            if "etymology_text" in row.keys() and row["etymology_text"]
            else ""
        )
    form_of_count = 0
    alt_of_count = 0
    for row in sense_rows:
        tags.update(_json_string_set(row["tags_json"] if "tags_json" in row.keys() else None))
        categories.update(
            _json_string_set(row["categories_json"] if "categories_json" in row.keys() else None)
        )
        topics.update(_json_string_set(row["topics_json"] if "topics_json" in row.keys() else None))
        form_of_count += len(
            _json_array(row["form_of_json"] if "form_of_json" in row.keys() else None)
        )
        alt_of_count += len(
            _json_array(row["alt_of_json"] if "alt_of_json" in row.keys() else None)
        )
    sense_keys = {
        (
            row["entry_ord"] if "entry_ord" in row.keys() else None,
            row["sense_ord"] if "sense_ord" in row.keys() else None,
        )
        for row in sense_rows
    }
    translations = {
        str(row["translation_lc"]).strip()
        for row in sense_rows
        if "translation_lc" in row.keys() and str(row["translation_lc"] or "").strip()
    }
    marked_terms = sorted(
        item for item in tags | categories if str(item).strip().lower() in DICTIONARY_MARKED_TERMS
    )
    region_terms = sorted({_region_term(item) for item in tags | categories if _region_term(item)})
    register_terms = sorted(
        {term for term in (_register_term(item) for item in tags | categories) if term}
    )
    domain_terms = sorted(
        {
            term
            for term in (
                *(_normalize_feature_term(item) for item in topics),
                *(_domain_term(item) for item in categories),
            )
            if term
        }
    )
    return {
        "entry_count": len(entry_rows),
        "sense_count": len(sense_keys),
        "gloss_count": len(sense_rows),
        "translation_count": len(translations),
        "pos_values": pos_values,
        "pos_count": len(pos_values),
        "topics": sorted(topics),
        "topic_count": len(topics),
        "tags_sample": sorted(tags)[:12],
        "tag_count": len(tags),
        "categories_sample": sorted(categories)[:12],
        "category_count": len(categories),
        "marked_usage_flag": bool(marked_terms),
        "marked_terms": marked_terms,
        "region_terms": region_terms,
        "region_tag_count": len(region_terms),
        "register_terms": register_terms,
        "register_colloquial_flag": bool(set(register_terms) & DICTIONARY_COLLOQUIAL_TERMS),
        "register_sensitive_flag": bool(set(register_terms) & DICTIONARY_SENSITIVE_TERMS),
        "register_rare_dated_flag": bool(set(register_terms) & DICTIONARY_RARE_DATED_TERMS),
        "domain_terms": domain_terms,
        "domain_topic_count": len(domain_terms),
        "form_of_count": form_of_count,
        "alt_of_count": alt_of_count,
        "forms_count": forms_count,
        "sounds_count": sounds_count,
        "synonyms_count": synonyms_count,
        "has_etymology": has_etymology,
    }


def _normalize_feature_term(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[_\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _region_term(value: object) -> str:
    text = _normalize_feature_term(value)
    if not text:
        return ""
    if text in DICTIONARY_REGION_TERMS:
        return text
    if text.endswith("-spanish"):
        prefix = text[: -len("-spanish")]
        return prefix if prefix in DICTIONARY_REGION_TERMS else ""
    return ""


def _register_term(value: object) -> str:
    text = _normalize_feature_term(value)
    if text.startswith("spanish-"):
        text = text.removeprefix("spanish-")
    category_aliases = {
        "colloquialisms": "colloquial",
        "dated-terms": "dated",
        "derogatory-terms": "derogatory",
        "offensive-terms": "offensive",
        "rare-senses": "rare",
        "slang": "slang",
        "terms-with-archaic-senses": "archaic",
        "terms-with-rare-senses": "rare",
        "terms-with-uncommon-senses": "uncommon",
        "vulgarities": "vulgar",
    }
    if text in category_aliases:
        return category_aliases[text]
    if text.endswith("-terms"):
        text = text[: -len("-terms")]
    if (
        text
        in DICTIONARY_COLLOQUIAL_TERMS | DICTIONARY_SENSITIVE_TERMS | DICTIONARY_RARE_DATED_TERMS
    ):
        return text
    if text.endswith("-senses") and text[: -len("-senses")] in DICTIONARY_RARE_DATED_TERMS:
        return text[: -len("-senses")]
    return ""


def _domain_term(value: object) -> str:
    text = _normalize_feature_term(value)
    if not text.startswith("es:"):
        return ""
    return text.removeprefix("es:")


def _spanish_form_features(lemma: str) -> dict[str, object]:
    text = str(lemma or "").strip()
    tokens = TOKEN_RE.findall(text)
    normalized = unicodedata.normalize("NFD", text)
    has_combining_mark = any(unicodedata.combining(char) for char in normalized)
    lowered = text.lower()
    return {
        "char_count": len(text),
        "token_count": len(tokens),
        "has_space": any(char.isspace() for char in text),
        "has_hyphen": "-" in text,
        "has_apostrophe": "'" in text or "’" in text,
        "has_digit": any(char.isdigit() for char in text),
        "has_punctuation": any(not char.isalnum() and not char.isspace() for char in text),
        "has_uppercase": any(char.isupper() for char in text),
        "is_lowercase": text == lowered,
        "has_diacritic": has_combining_mark or any(char in SPANISH_DIACRITICS for char in text),
        "has_spanish_specific_letter": any(char in "ñÑüÜ" for char in text),
        "ends_with_mente": lowered.endswith("mente"),
        "noun_suffix_like": lowered.endswith(("ción", "sión", "dad", "tad", "aje", "ismo")),
        "agent_or_field_suffix_like": lowered.endswith(("ista", "ero", "era", "dor", "dora")),
        "adjective_suffix_like": lowered.endswith(("able", "ible", "oso", "osa", "ico", "ica")),
        "verb_infinitive_like": lowered.endswith(("ar", "er", "ir")),
        "participle_like": lowered.endswith(("ado", "ada", "ido", "ida")),
        "gerund_like": lowered.endswith(("ando", "iendo")),
    }


def _column_count(rows: Sequence[Mapping[str, object]], column: str) -> int:
    return sum(
        1 for row in rows if _present_value(_as_mapping(row.get("raw_frequency")).get(column))
    )


def _coverage_row(label: str, count: int, total: int) -> dict[str, object]:
    return {"label": label, "count": count, "ratio": _ratio(count, total)}


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_ident(table)})").fetchall()
    return [str(row[1]) for row in rows if len(row) > 1]


def _metadata(conn: sqlite3.Connection) -> dict[str, object]:
    if not _table_exists(conn, "meta"):
        return {}
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'metadata' LIMIT 1").fetchone()
    except sqlite3.Error:
        return {}
    if not row:
        return {}
    try:
        decoded = json.loads(str(row[0] or "{}"))
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _json_array(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return []
    return decoded if isinstance(decoded, list) else []


def _json_string_set(value: object) -> set[str]:
    result: set[str] = set()
    for item in _json_array(value):
        text = str(item or "").strip()
        if text:
            result.add(text)
    return result


def _quote_ident(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _unique_paths(paths: Sequence[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _chunks(values: Sequence[str], *, size: int) -> list[list[str]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: object) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _round_or_none(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None else None


def _present_value(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def _ratio(count: int, total: int) -> float:
    return round(float(count) / float(total), 6) if total else 0.0


def _pct(value: object) -> str:
    numeric = _safe_float(value) or 0.0
    return f"{numeric * 100.0:.1f}%"


def _fmt_float(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.3f}"


def _jsonable(value: object) -> object:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
