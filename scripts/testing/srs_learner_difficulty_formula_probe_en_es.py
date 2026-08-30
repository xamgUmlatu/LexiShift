#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
for import_path in (CORE_ROOT, SCRIPT_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from lexishift_core.helper.lp_capabilities import default_frequency_db_path  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from srs_learner_difficulty_signal_palette_en_es import (  # noqa: E402
    build_report as build_palette_report,
)


PAIR = "en-es"
DEFAULT_TOP_N = 10000
DEFAULT_SAMPLE_LIMIT = 8
DEFAULT_SOURCE_LABEL = "freq-es-spalex-v1"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_formula_probe_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_formula_probe_en_es_latest.md"
)
DEFAULT_LEARNER_SOURCE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_learner_source_audit_en_es_latest.json"
)
DEFAULT_WORDFREQ_LANGUAGE = "es"
WORDFREQ_MIN_ZIPF = 1.0
WORDFREQ_MAX_ZIPF = 6.0
DEFAULT_LEXCOMSPAL2_TSV = PROJECT_ROOT / "data" / "external" / "lexcomspal2" / "LexComSpaL2_all.tsv"

FUNCTION_POS = frozenset(
    {
        "adposition",
        "article",
        "auxiliary",
        "conjunction",
        "determiner",
        "interjection",
        "numeral",
        "particle",
        "preposition",
        "pronoun",
    }
)
CONTENT_BUCKETS = frozenset({"noun", "verb", "adjective", "adverb"})
MARKED_HIGH_RISK_TERMS = frozenset(
    {
        "archaic",
        "dated",
        "dialectal",
        "literary",
        "obsolete",
        "rare",
        "regional",
        "vulgar",
    }
)
ENGLISH_STOPWORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "because",
        "become",
        "being",
        "between",
        "from",
        "group",
        "having",
        "indicates",
        "into",
        "other",
        "people",
        "person",
        "related",
        "someone",
        "something",
        "standard",
        "that",
        "their",
        "them",
        "then",
        "there",
        "thing",
        "things",
        "this",
        "those",
        "used",
        "with",
        "without",
    }
)
TOKEN_RE = re.compile(r"[a-z][a-z'-]*", re.IGNORECASE)


@dataclass(frozen=True)
class FormulaVariant:
    variant_id: str
    description: str
    base_component: str
    up_weights: Mapping[str, float]
    down_weights: Mapping[str, float]
    up_cap: float | None = None
    down_cap: float | None = None


@dataclass(frozen=True)
class ComponentContext:
    frequency_stats: Mapping[str, float]
    translations_by_lemma: Mapping[str, tuple[str, ...]]
    translation_entries_by_lemma: Mapping[str, tuple[Mapping[str, str], ...]]
    english_commonness: Mapping[str, float]
    wordfreq_zipf_by_lemma: Mapping[str, float]
    lexcom_by_token: Mapping[str, Mapping[str, object]]


FORMULA_VARIANTS: tuple[FormulaVariant, ...] = (
    FormulaVariant(
        variant_id="rank_frequency_only",
        description="Pure log-normalized SPALEX rank difficulty.",
        base_component="rank_base",
        up_weights={},
        down_weights={},
    ),
    FormulaVariant(
        variant_id="zipf_frequency_only",
        description="Pure SPALEX Zipf difficulty.",
        base_component="zipf_base",
        up_weights={},
        down_weights={},
    ),
    FormulaVariant(
        variant_id="spalex_blend_frequency",
        description="Blend of SPALEX rank, log-frequency, Zipf, and percent/prevalence.",
        base_component="spalex_blend",
        up_weights={},
        down_weights={},
    ),
    FormulaVariant(
        variant_id="pos_guard_light",
        description="Frequency blend with a small function/POS/admission suitability guard.",
        base_component="spalex_blend",
        up_weights={
            "pos_function_risk": 0.08,
            "pos_other_risk": 0.06,
            "admission_suitability_risk": 0.08,
        },
        down_weights={"pos_content_gate": 0.02},
        up_cap=0.08,
        down_cap=0.02,
    ),
    FormulaVariant(
        variant_id="dictionary_guard_light",
        description="Frequency blend with marked-use, variant, ambiguity, and form guards.",
        base_component="spalex_blend",
        up_weights={
            "gated_dict_marked_usage_risk": 0.12,
            "dict_variant_risk": 0.10,
            "tail_dict_ambiguity": 0.05,
            "weak_form_risk": 0.04,
        },
        down_weights={},
        up_cap=0.12,
    ),
    FormulaVariant(
        variant_id="dictionary_detail_probe",
        description=(
            "Frequency blend with structured Kaikki region/register/domain features. "
            "Rare/dated/domain evidence can raise; regional-colloquial evidence is only "
            "a small diagnostic lowering probe."
        ),
        base_component="spalex_blend",
        up_weights={
            "tail_rare_dated_register": 0.070,
            "tail_domain_specificity": 0.040,
            "dict_register_sensitive_score": 0.020,
        },
        down_weights={"regional_colloquial_gate": 0.050},
        up_cap=0.075,
        down_cap=0.035,
    ),
    FormulaVariant(
        variant_id="unsupported_ease_probe",
        description=(
            "Frequency blend with an en-ja-style unsupported-ease gate. It raises "
            "only easy placements that lack broad learner-source support and have "
            "weak independent support for being easy."
        ),
        base_component="spalex_blend",
        up_weights={
            "unsupported_ease_floor050": 1.00,
            "unsupported_ease_structural_floor060": 0.80,
        },
        down_weights={},
        up_cap=0.120,
    ),
    FormulaVariant(
        variant_id="cognate_rescue_light",
        description="Frequency blend with a capped English-Spanish cognate/transparency rescue.",
        base_component="spalex_blend",
        up_weights={"false_friend_caution": 0.03},
        down_weights={"cognate_rescue": 0.10},
        up_cap=0.03,
        down_cap=0.06,
    ),
    FormulaVariant(
        variant_id="learner_source_zipf_light",
        description=(
            "SPALEX Zipf base with a capped rescue for rows present in audited "
            "learner/core source overlays."
        ),
        base_component="zipf_base",
        up_weights={},
        down_weights={"learner_core_gap_zipf_confident": 0.55},
        down_cap=0.12,
    ),
    FormulaVariant(
        variant_id="learner_source_zipf_medium",
        description=("Same learner-source shape as light, but with a larger cap for diagnostics."),
        base_component="zipf_base",
        up_weights={},
        down_weights={"learner_core_gap_zipf_confident": 0.80},
        down_cap=0.18,
    ),
    FormulaVariant(
        variant_id="wordfreq_rescue_probe",
        description=(
            "Frequency blend with an optional multi-source wordfreq rescue. It lowers "
            "only rows where wordfreq says the word is more common than SPALEX implies, "
            "with a stronger effect in the tail."
        ),
        base_component="spalex_blend",
        up_weights={"wordfreq_tail_caution": 0.06},
        down_weights={
            "wordfreq_source_rescue": 0.10,
            "wordfreq_tail_rescue": 0.35,
        },
        up_cap=0.03,
        down_cap=0.10,
    ),
    FormulaVariant(
        variant_id="lexcom_complexity_probe",
        description=(
            "Frequency blend with a direct LexComSpaL2 learner-complexity correction. "
            "It lowers rows that LexCom annotators found easier than SPALEX implies and "
            "raises rows they found harder."
        ),
        base_component="spalex_blend",
        up_weights={"lexcom_learner_caution": 0.16},
        down_weights={"lexcom_learner_rescue": 0.55},
        up_cap=0.07,
        down_cap=0.12,
    ),
    FormulaVariant(
        variant_id="transfer_all_light",
        description=(
            "Light combined transfer model: frequency blend plus bounded POS, dictionary, "
            "form, and cognate corrections."
        ),
        base_component="spalex_blend",
        up_weights={
            "pos_function_risk": 0.04,
            "pos_other_risk": 0.04,
            "gated_dict_marked_usage_risk": 0.08,
            "dict_variant_risk": 0.08,
            "tail_dict_ambiguity": 0.04,
            "weak_form_risk": 0.03,
            "false_friend_caution": 0.02,
        },
        down_weights={
            "cognate_rescue": 0.08,
            "pos_content_gate": 0.015,
        },
        up_cap=0.10,
        down_cap=0.06,
    ),
    FormulaVariant(
        variant_id="transfer_all_medium",
        description=(
            "Medium combined transfer model for review: same shape as light, but with "
            "larger caps to make qualitative effects easier to inspect."
        ),
        base_component="spalex_blend",
        up_weights={
            "pos_function_risk": 0.07,
            "pos_other_risk": 0.06,
            "gated_dict_marked_usage_risk": 0.12,
            "dict_variant_risk": 0.12,
            "tail_dict_ambiguity": 0.07,
            "weak_form_risk": 0.05,
            "false_friend_caution": 0.03,
        },
        down_weights={
            "cognate_rescue": 0.12,
            "pos_content_gate": 0.02,
        },
        up_cap=0.14,
        down_cap=0.09,
    ),
    FormulaVariant(
        variant_id="tail_guard_medium",
        description=(
            "Tail-focused guard: lets marked/variant/ambiguity evidence matter mostly "
            "where SPALEX already says the row is non-core."
        ),
        base_component="spalex_blend",
        up_weights={
            "gated_dict_marked_usage_risk": 0.16,
            "tail_variant_risk": 0.12,
            "tail_dict_ambiguity": 0.10,
            "weak_form_risk": 0.04,
        },
        down_weights={"rare_cognate_tail_rescue": 0.08},
        up_cap=0.16,
        down_cap=0.06,
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an isolated en-es learner-difficulty formula probe. This script uses "
            "the current en-es signal palette to generate candidate formula rankings and "
            "qualitative samples; it does not change production scoring or add manual labels."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--pos-overlay-path", type=Path)
    parser.add_argument("--kaikki-forward-db", type=Path)
    parser.add_argument("--english-frequency-db", type=Path)
    parser.add_argument("--learner-source-json", type=Path, default=DEFAULT_LEARNER_SOURCE_JSON)
    parser.add_argument("--lexcomspal2-tsv", type=Path, default=DEFAULT_LEXCOMSPAL2_TSV)
    parser.add_argument(
        "--disable-wordfreq",
        action="store_true",
        help=(
            "Do not load the optional Python wordfreq package. By default the probe "
            "uses it when available and degrades gracefully when it is missing."
        ),
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--include-rows",
        action="store_true",
        help="Embed all per-row component values and variant scores in the JSON artifact.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        pos_overlay_path=args.pos_overlay_path,
        kaikki_forward_db=args.kaikki_forward_db,
        english_frequency_db=args.english_frequency_db,
        learner_source_json=args.learner_source_json,
        lexcomspal2_tsv=args.lexcomspal2_tsv,
        wordfreq_enabled=not bool(args.disable_wordfreq),
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        include_rows=bool(args.include_rows),
    )
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
    english_frequency_db: Path | None = None,
    learner_source_json: Path | None = DEFAULT_LEARNER_SOURCE_JSON,
    lexcomspal2_tsv: Path | None = DEFAULT_LEXCOMSPAL2_TSV,
    wordfreq_enabled: bool = True,
    wordfreq_zipf_by_lemma: Mapping[str, float] | None = None,
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    include_rows: bool = False,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    palette = build_palette_report(
        frequency_db=frequency_db,
        pos_overlay_path=pos_overlay_path,
        kaikki_forward_db=kaikki_forward_db,
        learner_source_json=learner_source_json,
        top_n=top_n,
        sample_limit=sample_limit,
        generated_at=generated_at,
        include_rows=True,
    )
    palette_rows = [_as_mapping(row) for row in _as_sequence(palette.get("signal_rows"))]
    paths = build_helper_paths()
    frequency_path = _path_or_none(_as_mapping(palette.get("inputs")).get("frequency_db"))
    kaikk_path = _resolve_kaikki_forward_db(
        kaikki_forward_db,
        _path_or_none(_as_mapping(palette.get("inputs")).get("kaikki_forward_db")),
        paths.data_root,
    )
    english_path = _resolve_english_frequency_db(
        english_frequency_db,
        paths.frequency_packs_dir,
    )
    translation_entries_by_lemma = _load_translation_entries(
        kaikk_path,
        [str(row.get("lemma") or "") for row in palette_rows],
    )
    translations_by_lemma = {
        key: tuple(
            dict.fromkeys(
                str(entry.get("translation") or "")
                for entry in entries
                if str(entry.get("translation") or "").strip()
            )
        )
        for key, entries in translation_entries_by_lemma.items()
    }
    translation_tokens = sorted(
        {
            token
            for translations in translations_by_lemma.values()
            for text in translations
            for token in _translation_tokens(text)
        }
    )
    english_commonness = _load_english_commonness(english_path, translation_tokens)
    resolved_wordfreq_zipf = (
        {
            str(key).strip().lower(): _round_float(value)
            for key, value in wordfreq_zipf_by_lemma.items()
            if str(key).strip() and (_safe_float(value) or 0.0) > 0.0
        }
        if wordfreq_zipf_by_lemma is not None
        else _load_wordfreq_zipf(
            [str(row.get("lemma") or "") for row in palette_rows],
            enabled=wordfreq_enabled,
            language=DEFAULT_WORDFREQ_LANGUAGE,
        )
    )
    lexcom_by_token = _load_lexcomspal2(lexcomspal2_tsv)
    context = ComponentContext(
        frequency_stats=_frequency_stats(frequency_path, palette_rows),
        translations_by_lemma=translations_by_lemma,
        translation_entries_by_lemma=translation_entries_by_lemma,
        english_commonness=english_commonness,
        wordfreq_zipf_by_lemma=resolved_wordfreq_zipf,
        lexcom_by_token=lexcom_by_token,
    )
    scored_rows = [
        _scored_row(row, context=context, variants=FORMULA_VARIANTS) for row in palette_rows
    ]
    variants = [
        _variant_report(
            variant,
            scored_rows=scored_rows,
            base_variant_id="spalex_blend_frequency",
            sample_limit=sample_limit,
        )
        for variant in FORMULA_VARIANTS
    ]
    findings = _build_findings(
        palette=palette,
        rows=scored_rows,
        translations_by_lemma=translations_by_lemma,
        english_commonness=english_commonness,
        wordfreq_zipf_by_lemma=resolved_wordfreq_zipf,
        lexcom_by_token=lexcom_by_token,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_es_formula_probe_ready" if status == "ok" else "en_es_formula_probe_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "frequency_db": str(frequency_path) if frequency_path else None,
            "pos_overlay": _as_mapping(palette.get("inputs")).get("pos_overlay"),
            "kaikki_forward_db": str(kaikk_path) if kaikk_path else None,
            "english_frequency_db": str(english_path) if english_path else None,
            "learner_source_json": str(learner_source_json) if learner_source_json else None,
            "lexcomspal2_tsv": str(lexcomspal2_tsv) if lexcomspal2_tsv else None,
            "wordfreq_enabled": bool(wordfreq_enabled),
            "wordfreq_language": DEFAULT_WORDFREQ_LANGUAGE,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "manual_corrections": "none",
            "production_ranking_change": "none",
            "purpose": (
                "Sidecar formula probe for en-es. It materializes the transferable en-ja "
                "model roles as source-backed en-es components and produces qualitative "
                "rank/band diagnostics before any calibration labels exist."
            ),
            "scoring_note": (
                "No candidate is declared globally best here because en-es reviewed "
                "learner-difficulty labels do not yet exist. The artifact is for sample "
                "review, component inspection, and later calibration-set bootstrapping."
            ),
        },
        "palette_summary": _as_mapping(palette.get("summary")),
        "frequency_stats": dict(context.frequency_stats),
        "component_summary": _component_summary(scored_rows),
        "translation_signal": {
            "rows_with_translations": sum(
                1 for translations in translations_by_lemma.values() if translations
            ),
            "unique_translation_tokens": len(translation_tokens),
            "english_tokens_with_frequency": len(english_commonness),
            "cognate_rescue_rows": sum(
                1
                for row in scored_rows
                if _as_mapping(row.get("components")).get("cognate_rescue", 0.0) > 0.0
            ),
        },
        "wordfreq_signal": _wordfreq_signal_summary(resolved_wordfreq_zipf, len(scored_rows)),
        "lexcom_signal": _lexcom_signal_summary(lexcom_by_token, scored_rows),
        "variants": variants,
        "findings": findings,
        "limitations": [
            "This is not an accuracy sweep because there is no reviewed en-es difficulty calibration set yet.",
            "Cognate/transparency is estimated from Wiktionary English translations plus local English frequency; it is a learner-facing ease hypothesis, not proof of semantic simplicity.",
            "Learner-source rescue uses a small sidecar overlay from audited source candidates. It is bounded and diagnostic, not a hard CEFR floor.",
            "wordfreq is optional sidecar evidence. It is used as multi-source commonness, not as a pedagogical source or product-bundled corpus commitment.",
            "LexComSpaL2 is direct learner-complexity evidence, but it is token-level and domain-limited, so it is used as capped sidecar evidence rather than a replacement target.",
            "Dictionary markedness, ambiguity, and topic metadata are treated as capped diagnostic signals only.",
            "Spanish form features are intentionally weak; they are not analogous to Japanese kanji burden.",
            "Piecewise/grid search should come after this probe produces reviewable examples and at least a small calibration set.",
        ],
    }
    if include_rows:
        report["rows"] = scored_rows
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    lines: list[str] = []
    lines.append("# en-es Learner Difficulty Formula Probe")
    lines.append("")
    lines.append(f"Status: `{report.get('status')}`")
    lines.append(f"Decision: `{report.get('decision')}`")
    lines.append(f"Generated: `{report.get('generated_at')}`")
    lines.append("")
    lines.append(
        "Purpose: generate source-backed candidate en-es difficulty rankings without "
        "changing production scoring or adding manual labels."
    )
    lines.append("")
    inputs = _as_mapping(report.get("inputs"))
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Frequency DB: `{inputs.get('frequency_db')}`")
    lines.append(f"- Kaikki/Wiktionary DB: `{inputs.get('kaikki_forward_db')}`")
    lines.append(f"- English frequency DB: `{inputs.get('english_frequency_db')}`")
    lines.append(f"- Learner-source overlay: `{inputs.get('learner_source_json')}`")
    lines.append(f"- LexComSpaL2 TSV: `{inputs.get('lexcomspal2_tsv')}`")
    lines.append(f"- wordfreq enabled: `{inputs.get('wordfreq_enabled')}`")
    lines.append(f"- Top N: `{inputs.get('top_n')}`")
    lines.append("")

    translation = _as_mapping(report.get("translation_signal"))
    lines.append("## Translation / Cognate Signal")
    lines.append("")
    lines.append(f"- Rows with translations: `{translation.get('rows_with_translations', 0)}`")
    lines.append(
        f"- Unique English translation tokens: `{translation.get('unique_translation_tokens', 0)}`"
    )
    lines.append(
        f"- Tokens with English frequency: `{translation.get('english_tokens_with_frequency', 0)}`"
    )
    lines.append(f"- Rows with cognate rescue > 0: `{translation.get('cognate_rescue_rows', 0)}`")
    lines.append("")

    wordfreq = _as_mapping(report.get("wordfreq_signal"))
    lines.append("## wordfreq Signal")
    lines.append("")
    lines.append(f"- Language: `{wordfreq.get('language')}`")
    lines.append(f"- Rows with Zipf: `{wordfreq.get('rows_with_zipf', 0)}`")
    lines.append(f"- Coverage: `{_pct(wordfreq.get('coverage'))}`")
    lines.append(f"- Mean Zipf: `{_fmt_float(wordfreq.get('mean_zipf'))}`")
    lines.append("")

    lexcom = _as_mapping(report.get("lexcom_signal"))
    lines.append("## LexComSpaL2 Signal")
    lines.append("")
    lines.append(f"- Source token rows: `{lexcom.get('source_token_count', 0)}`")
    lines.append(f"- Probe rows with hit: `{lexcom.get('probe_rows_with_hit', 0)}`")
    lines.append(f"- Probe coverage: `{_pct(lexcom.get('probe_coverage'))}`")
    lines.append(f"- Mean complexity: `{_fmt_float(lexcom.get('mean_complexity'))}`")
    lines.append("")

    lines.append("## Component Summary")
    lines.append("")
    lines.append("| Component | Mean | Nonzero rows | Nonzero share |")
    lines.append("| --- | ---: | ---: | ---: |")
    for raw in _as_sequence(_as_mapping(report.get("component_summary")).get("components")):
        row = _as_mapping(raw)
        lines.append(
            f"| `{row.get('component')}` | {_fmt_float(row.get('mean'))} | "
            f"{row.get('nonzero_count', 0)} | {_pct(row.get('nonzero_share'))} |"
        )
    lines.append("")

    lines.append("## Variants")
    lines.append("")
    lines.append("| Variant | Mean score | Mean delta | Raised | Lowered | Max raise | Max lower |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for raw in _as_sequence(report.get("variants")):
        variant = _as_mapping(raw)
        summary = _as_mapping(variant.get("summary"))
        lines.append(
            f"| `{variant.get('variant_id')}` | {_fmt_float(summary.get('mean_score'))} | "
            f"{_fmt_float(summary.get('mean_delta_from_base'))} | "
            f"{summary.get('raised_count', 0)} | {summary.get('lowered_count', 0)} | "
            f"{_fmt_float(summary.get('max_raise'))} | {_fmt_float(summary.get('max_lower'))} |"
        )
    lines.append("")

    for raw in _as_sequence(report.get("variants")):
        variant = _as_mapping(raw)
        variant_id = str(variant.get("variant_id") or "")
        if variant_id not in {
            "spalex_blend_frequency",
            "dictionary_detail_probe",
            "unsupported_ease_probe",
            "learner_source_zipf_light",
            "learner_source_zipf_medium",
            "wordfreq_rescue_probe",
            "lexcom_complexity_probe",
            "transfer_all_light",
            "transfer_all_medium",
            "tail_guard_medium",
        }:
            continue
        lines.append(f"## `{variant_id}`")
        lines.append("")
        lines.append(str(variant.get("description") or ""))
        lines.append("")
        for title, key in (
            ("Largest Raises", "largest_raises"),
            ("Largest Lowers", "largest_lowers"),
        ):
            rows = _as_sequence(_as_mapping(variant.get("change_samples")).get(key))
            if not rows:
                continue
            lines.append(f"### {title}")
            lines.append("")
            lines.append("| Lemma | Score | Base | Delta | Rank | POS | Signals |")
            lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
            for row in rows:
                item = _as_mapping(row)
                lines.append(
                    f"| `{item.get('lemma')}` | {_fmt_float(item.get('score'))} | "
                    f"{_fmt_float(item.get('base_score'))} | {_fmt_signed(item.get('delta'))} | "
                    f"{_fmt_rank(item.get('spalex_rank'))} | `{item.get('pos') or ''}` | "
                    f"{_signal_text(item)} |"
                )
            lines.append("")
        lines.append("### Band Samples")
        lines.append("")
        for band in _as_sequence(variant.get("band_samples")):
            band_map = _as_mapping(band)
            rows = _as_sequence(band_map.get("rows"))
            if not rows:
                continue
            lines.append(f"Band `{band_map.get('band')}`")
            lines.append("")
            lines.append("| Lemma | Score | Base | Delta | Rank | POS | Translations |")
            lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
            for row in rows:
                item = _as_mapping(row)
                lines.append(
                    f"| `{item.get('lemma')}` | {_fmt_float(item.get('score'))} | "
                    f"{_fmt_float(item.get('base_score'))} | {_fmt_signed(item.get('delta'))} | "
                    f"{_fmt_rank(item.get('spalex_rank'))} | `{item.get('pos') or ''}` | "
                    f"{_escape(', '.join(str(t) for t in _as_sequence(item.get('translations'))[:3])) or '-'} |"
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


def _scored_row(
    row: Mapping[str, object],
    *,
    context: ComponentContext,
    variants: Sequence[FormulaVariant],
) -> dict[str, object]:
    components = _components(row, context=context)
    variant_scores = {
        variant.variant_id: _score_variant(variant, components) for variant in variants
    }
    lemma = str(row.get("lemma") or "")
    dictionary = _as_mapping(row.get("dictionary"))
    raw_frequency = _as_mapping(row.get("raw_frequency"))
    learner_source = _as_mapping(row.get("learner_source"))
    return {
        "lemma": lemma,
        "spalex_rank": _safe_float(raw_frequency.get("spalex_rank") or row.get("core_rank")),
        "pos": row.get("pos_canonical") or row.get("pos_raw") or row.get("pos_bucket"),
        "pos_bucket": row.get("pos_bucket"),
        "candidate_state": row.get("candidate_state"),
        "frequency_difficulty": row.get("frequency_difficulty"),
        "dictionary": {
            "entry_count": dictionary.get("entry_count"),
            "sense_count": dictionary.get("sense_count"),
            "translation_count": dictionary.get("translation_count"),
            "marked_usage_flag": dictionary.get("marked_usage_flag"),
            "marked_terms": dictionary.get("marked_terms"),
            "region_terms": dictionary.get("region_terms"),
            "region_tag_count": dictionary.get("region_tag_count"),
            "register_terms": dictionary.get("register_terms"),
            "register_colloquial_flag": dictionary.get("register_colloquial_flag"),
            "register_sensitive_flag": dictionary.get("register_sensitive_flag"),
            "register_rare_dated_flag": dictionary.get("register_rare_dated_flag"),
            "domain_terms": dictionary.get("domain_terms"),
            "domain_topic_count": dictionary.get("domain_topic_count"),
            "form_of_count": dictionary.get("form_of_count"),
            "alt_of_count": dictionary.get("alt_of_count"),
            "topics": dictionary.get("topics"),
        },
        "learner_source": dict(learner_source),
        "learner_source_context": dict(_as_mapping(row.get("learner_source_context"))),
        "translations": list(context.translations_by_lemma.get(lemma.lower(), ()))[:8],
        "components": components,
        "variant_scores": variant_scores,
    }


def _components(row: Mapping[str, object], *, context: ComponentContext) -> dict[str, float]:
    raw = _as_mapping(row.get("raw_frequency"))
    dictionary = _as_mapping(row.get("dictionary"))
    form = _as_mapping(row.get("form"))
    learner_source = _as_mapping(row.get("learner_source"))
    learner_source_context = _as_mapping(row.get("learner_source_context"))
    stats = context.frequency_stats
    rank_base = _rank_difficulty(
        raw.get("spalex_rank") or raw.get("source_rank") or row.get("core_rank"),
        stats.get("max_rank"),
    )
    freq_base = _inverse_log_difficulty(
        raw.get("spalex_freq") or raw.get("source_frequency") or raw.get("freq") or row.get("pmw"),
        stats.get("min_freq"),
        stats.get("max_freq"),
    )
    zipf_base = _inverse_linear_difficulty(
        raw.get("spalex_zipf"),
        stats.get("min_zipf"),
        stats.get("max_zipf"),
    )
    prevalence_base = _inverse_linear_difficulty(
        raw.get("spalex_prevalence_total"),
        stats.get("min_prevalence"),
        stats.get("max_prevalence"),
    )
    percent_base = 1.0 - _clamp01((_safe_float(raw.get("spalex_percent_total")) or 0.0) / 100.0)
    frequency = _weighted_mean(
        (
            (rank_base, 0.45),
            (freq_base, 0.25),
            (zipf_base, 0.20),
            (percent_base, 0.06),
            (prevalence_base, 0.04),
        )
    )

    pos_canonical = str(row.get("pos_canonical") or row.get("pos_raw") or "").strip().lower()
    pos_bucket = str(row.get("pos_bucket") or "").strip().lower()
    pos_function_risk = 1.0 if pos_canonical in FUNCTION_POS else 0.0
    if not pos_function_risk and pos_bucket == "other":
        pos_function_risk = 0.65
    pos_other_risk = 1.0 if pos_bucket in {"other", "unknown", ""} else 0.0
    pos_content_gate = 1.0 if pos_bucket in CONTENT_BUCKETS else 0.0
    if pos_bucket == "adverb":
        pos_content_gate = 0.70
    admission_suitability = _safe_float(row.get("admission_suitability"))
    admission_suitability_risk = 1.0 - _clamp01(
        admission_suitability if admission_suitability is not None else 1.0
    )
    candidate_non_normal_risk = (
        0.0
        if str(row.get("candidate_state") or "") == "normal_vocab"
        and str(row.get("problem_class") or "") == "normal_vocab"
        else 1.0
    )

    entry_count_score = _log_score(dictionary.get("entry_count"), ceiling=4.0)
    sense_count_score = _log_score(dictionary.get("sense_count"), ceiling=10.0)
    gloss_count_score = _log_score(dictionary.get("gloss_count"), ceiling=18.0)
    translation_count_score = _log_score(dictionary.get("translation_count"), ceiling=12.0)
    pos_count_score = _log_score(dictionary.get("pos_count"), ceiling=5.0)
    dict_ambiguity = _weighted_mean(
        (
            (entry_count_score, 0.20),
            (sense_count_score, 0.25),
            (gloss_count_score, 0.20),
            (translation_count_score, 0.20),
            (pos_count_score, 0.15),
        )
    )
    marked_terms = {
        str(item).strip().lower()
        for item in _as_sequence(dictionary.get("marked_terms"))
        if str(item).strip()
    }
    dict_marked_usage_risk = 1.0 if dictionary.get("marked_usage_flag") else 0.0
    dict_high_marked_usage_risk = 1.0 if marked_terms & MARKED_HIGH_RISK_TERMS else 0.0
    frequency_tail50 = _tail(frequency, 0.50)
    frequency_tail65 = _tail(frequency, 0.65)
    frequency_tail80 = _tail(frequency, 0.80)
    region_tag_count_score = _log_score(dictionary.get("region_tag_count"), ceiling=5.0)
    domain_topic_count_score = _log_score(dictionary.get("domain_topic_count"), ceiling=5.0)
    register_colloquial_score = 1.0 if dictionary.get("register_colloquial_flag") else 0.0
    register_sensitive_score = 1.0 if dictionary.get("register_sensitive_flag") else 0.0
    register_rare_dated_score = 1.0 if dictionary.get("register_rare_dated_flag") else 0.0
    regional_colloquial_gate = region_tag_count_score * max(
        register_colloquial_score,
        0.80 * register_sensitive_score,
    )
    tail_domain_specificity = frequency_tail65 * domain_topic_count_score
    tail_rare_dated_register = frequency_tail65 * register_rare_dated_score
    dict_variant_risk = _clamp01(
        _safe_int(dictionary.get("form_of_count")) + _safe_int(dictionary.get("alt_of_count"))
    )
    weak_form_risk = _weak_form_risk(form)
    cognate = _cognate_signals(
        row,
        context=context,
        dict_ambiguity=dict_ambiguity,
        base_frequency=frequency,
    )
    lemma_key = str(row.get("lemma") or "").strip().lower()
    wordfreq_zipf = _safe_float(context.wordfreq_zipf_by_lemma.get(lemma_key)) or 0.0
    wordfreq_known = 1.0 if wordfreq_zipf > 0.0 else 0.0
    wordfreq_commonness = _wordfreq_commonness(wordfreq_zipf) if wordfreq_known else 0.0
    wordfreq_difficulty = 1.0 - wordfreq_commonness if wordfreq_known else 0.0
    wordfreq_source_rescue = wordfreq_known * max(0.0, frequency - wordfreq_difficulty)
    wordfreq_source_caution = wordfreq_known * max(0.0, wordfreq_difficulty - frequency)
    wordfreq_tail_rescue = frequency_tail65 * wordfreq_source_rescue
    wordfreq_tail_caution = frequency_tail65 * wordfreq_source_caution
    wordfreq_positive_ease_support = wordfreq_known * wordfreq_commonness
    wordfreq_regional_rescue = wordfreq_tail_rescue * max(
        regional_colloquial_gate,
        register_colloquial_score,
        0.50 * region_tag_count_score,
    )
    lexcom = _as_mapping(context.lexcom_by_token.get(lemma_key))
    lexcom_known = 1.0 if lexcom else 0.0
    lexcom_complexity = _safe_float(lexcom.get("overall")) or 0.0
    lexcom_pl1_complexity = _safe_float(lexcom.get("pl1")) or 0.0
    lexcom_pl2_complexity = _safe_float(lexcom.get("pl2")) or 0.0
    lexcom_pl3_complexity = _safe_float(lexcom.get("pl3")) or 0.0
    lexcom_ease_support = lexcom_known * (1.0 - lexcom_complexity)
    lexcom_learner_rescue = lexcom_known * max(0.0, frequency - lexcom_complexity)
    lexcom_learner_caution = lexcom_known * max(0.0, lexcom_complexity - frequency)
    lexcom_rescue_after020 = _tail(frequency, 0.20) * lexcom_learner_rescue
    lexcom_rescue_after030 = _tail(frequency, 0.30) * lexcom_learner_rescue
    lexcom_rescue_after040 = _tail(frequency, 0.40) * lexcom_learner_rescue
    lexcom_tail_rescue = frequency_tail65 * lexcom_learner_rescue
    lexcom_tail_caution = frequency_tail65 * lexcom_learner_caution
    learner_core_score = _safe_float(learner_source.get("learner_core_score"))
    learner_core_confidence = _safe_float(learner_source.get("confidence")) or 0.0
    learner_core_score = _clamp01(learner_core_score if learner_core_score is not None else 1.0)
    learner_core_confidence = _clamp01(learner_core_confidence)
    learner_core_gap_blend = max(0.0, frequency - learner_core_score)
    learner_core_gap_zipf = max(0.0, zipf_base - learner_core_score)
    learner_source_count = min(_safe_int(learner_source.get("source_count")), 3) / 3.0
    learner_broad_source_available = (
        1.0 if learner_source_context.get("broad_source_available") else 0.0
    )
    learner_broad_source_known = 1.0 if learner_source_context.get("broad_source_known") else 0.0
    learner_broad_source_absent = 1.0 if learner_source_context.get("broad_source_absent") else 0.0
    native_easy_support = _early_gate(frequency, ceiling=0.45)
    dict_entry_known = 1.0 if _safe_int(dictionary.get("entry_count")) > 0 else 0.0
    dictionary_normal_support = (
        0.15 * dict_entry_known * (1.0 - dict_marked_usage_risk) * (1.0 - dict_variant_risk)
    )
    dictionary_teachable_support = (
        dict_entry_known
        * (1.0 - dict_variant_risk)
        * max(0.25, 1.0 - 0.75 * dict_high_marked_usage_risk)
    )
    learner_source_known = 1.0 if learner_source else 0.0
    learner_source_reliability = learner_source_known * _clamp01(
        0.20 + 0.45 * learner_source_count + 0.35 * learner_core_confidence
    )
    learner_independent_vocab_support = max(
        pos_content_gate,
        dictionary_teachable_support,
        0.35 * wordfreq_positive_ease_support,
    )
    learner_rescue_quality_gate = learner_source_reliability * max(
        0.20,
        learner_independent_vocab_support,
    )
    learner_rescue_strict_gate = learner_source_reliability * learner_independent_vocab_support
    positive_ease_support = max(
        learner_broad_source_known,
        learner_source_count,
        learner_core_confidence,
        _clamp01((_safe_float(cognate.get("cognate_rescue")) or 0.0) * 1.25),
        wordfreq_positive_ease_support,
        lexcom_ease_support,
        native_easy_support,
        dictionary_normal_support,
    )
    easy_expectation50 = _early_gate(frequency, ceiling=0.50)
    easy_expectation65 = _early_gate(frequency, ceiling=0.65)
    unsupported_ease50 = learner_broad_source_absent * max(
        0.0,
        easy_expectation50 - positive_ease_support,
    )
    unsupported_ease65 = learner_broad_source_absent * max(
        0.0,
        easy_expectation65 - positive_ease_support,
    )
    unsupported_ease_marked_suspicion = max(
        admission_suitability_risk,
        dict_marked_usage_risk,
        dict_variant_risk,
        weak_form_risk,
        0.85 * register_rare_dated_score,
        0.75 * register_sensitive_score,
        0.65 * domain_topic_count_score,
    )
    unsupported_ease_usage_suspicion = max(
        admission_suitability_risk,
        dict_marked_usage_risk,
        dict_variant_risk,
        weak_form_risk,
        0.85 * register_rare_dated_score,
        0.75 * register_sensitive_score,
    )
    unsupported_ease_suspicion = max(
        0.70 * pos_function_risk,
        pos_other_risk,
        unsupported_ease_marked_suspicion,
    )
    unsupported_ease_content = unsupported_ease65 * pos_content_gate
    unsupported_ease_structural = unsupported_ease65 * unsupported_ease_suspicion
    unsupported_ease_marked = unsupported_ease65 * unsupported_ease_marked_suspicion
    unsupported_ease_usage = unsupported_ease65 * unsupported_ease_usage_suspicion
    unsupported_ease_floor040 = unsupported_ease65 * max(0.0, 0.40 - frequency)
    unsupported_ease_floor050 = unsupported_ease65 * max(0.0, 0.50 - frequency)
    unsupported_ease_content_floor050 = unsupported_ease_content * max(0.0, 0.50 - frequency)
    unsupported_ease_marked_floor060 = unsupported_ease_marked * max(0.0, 0.60 - frequency)
    unsupported_ease_usage_floor060 = unsupported_ease_usage * max(0.0, 0.60 - frequency)
    unsupported_ease_structural_floor060 = unsupported_ease_structural * max(
        0.0,
        0.60 - frequency,
    )

    components = {
        "rank_base": rank_base,
        "freq_log_base": freq_base,
        "zipf_base": zipf_base,
        "prevalence_base": prevalence_base,
        "percent_base": percent_base,
        "spalex_blend": frequency,
        "frequency": frequency,
        "frequency_sqrt": math.sqrt(frequency),
        "frequency_power2": frequency * frequency,
        "frequency_power3": frequency * frequency * frequency,
        "frequency_tail50": frequency_tail50,
        "frequency_tail65": frequency_tail65,
        "frequency_tail80": frequency_tail80,
        "frequency_tail90": _tail(frequency, 0.90),
        "wordfreq_known": wordfreq_known,
        "wordfreq_zipf": wordfreq_zipf,
        "wordfreq_commonness": wordfreq_commonness,
        "wordfreq_difficulty": wordfreq_difficulty,
        "wordfreq_positive_ease_support": wordfreq_positive_ease_support,
        "wordfreq_source_rescue": wordfreq_source_rescue,
        "wordfreq_tail_rescue": wordfreq_tail_rescue,
        "wordfreq_regional_rescue": wordfreq_regional_rescue,
        "wordfreq_source_caution": wordfreq_source_caution,
        "wordfreq_tail_caution": wordfreq_tail_caution,
        "lexcom_known": lexcom_known,
        "lexcom_complexity": lexcom_complexity,
        "lexcom_pl1_complexity": lexcom_pl1_complexity,
        "lexcom_pl2_complexity": lexcom_pl2_complexity,
        "lexcom_pl3_complexity": lexcom_pl3_complexity,
        "lexcom_ease_support": lexcom_ease_support,
        "lexcom_learner_rescue": lexcom_learner_rescue,
        "lexcom_rescue_after020": lexcom_rescue_after020,
        "lexcom_rescue_after030": lexcom_rescue_after030,
        "lexcom_rescue_after040": lexcom_rescue_after040,
        "lexcom_tail_rescue": lexcom_tail_rescue,
        "lexcom_learner_caution": lexcom_learner_caution,
        "lexcom_tail_caution": lexcom_tail_caution,
        "pos_known": 1.0 if pos_canonical else 0.0,
        "pos_function_risk": pos_function_risk,
        "pos_other_risk": pos_other_risk,
        "pos_content_gate": pos_content_gate,
        "candidate_non_normal_risk": candidate_non_normal_risk,
        "admission_suitability_risk": admission_suitability_risk,
        "dict_entry_known": dict_entry_known,
        "dict_entry_count_score": entry_count_score,
        "dict_sense_count_score": sense_count_score,
        "dict_gloss_count_score": gloss_count_score,
        "dict_translation_count_score": translation_count_score,
        "dict_pos_count_score": pos_count_score,
        "dict_ambiguity": dict_ambiguity,
        "common_dict_ambiguity": (1.0 - frequency) * dict_ambiguity,
        "tail_dict_ambiguity": frequency_tail65 * dict_ambiguity,
        "dict_marked_usage_risk": dict_marked_usage_risk,
        "dict_high_marked_usage_risk": dict_high_marked_usage_risk,
        "gated_dict_marked_usage_risk": dict_marked_usage_risk * max(0.25, frequency_tail50),
        "dict_region_tag_count_score": region_tag_count_score,
        "dict_domain_topic_count_score": domain_topic_count_score,
        "dict_register_colloquial_score": register_colloquial_score,
        "dict_register_sensitive_score": register_sensitive_score,
        "dict_register_rare_dated_score": register_rare_dated_score,
        "regional_colloquial_gate": regional_colloquial_gate,
        "tail_domain_specificity": tail_domain_specificity,
        "tail_rare_dated_register": tail_rare_dated_register,
        "dict_variant_risk": dict_variant_risk,
        "tail_variant_risk": dict_variant_risk * max(0.25, frequency_tail65),
        "weak_form_risk": weak_form_risk,
        "char_length_difficulty": _char_length_difficulty(form),
        "multiword_risk": 1.0 if form.get("has_space") else 0.0,
        "punctuation_or_digit_risk": 1.0
        if form.get("has_hyphen") or form.get("has_punctuation") or form.get("has_digit")
        else 0.0,
        "diacritic_burden_light": 0.20 if form.get("has_diacritic") else 0.0,
        "learner_source_known": learner_source_known,
        "learner_source_count": learner_source_count,
        "learner_source_reliability": learner_source_reliability,
        "learner_independent_vocab_support": learner_independent_vocab_support,
        "learner_rescue_quality_gate": learner_rescue_quality_gate,
        "learner_rescue_strict_gate": learner_rescue_strict_gate,
        "learner_broad_source_available": learner_broad_source_available,
        "learner_broad_source_known": learner_broad_source_known,
        "learner_broad_source_absent": learner_broad_source_absent,
        "learner_broad_absence_tail50": learner_broad_source_absent * frequency_tail50,
        "learner_broad_absence_tail65": learner_broad_source_absent * frequency_tail65,
        "learner_broad_absence_tail80": learner_broad_source_absent * frequency_tail80,
        "native_easy_support": native_easy_support,
        "dictionary_normal_support": dictionary_normal_support,
        "positive_ease_support": positive_ease_support,
        "easy_expectation50": easy_expectation50,
        "easy_expectation65": easy_expectation65,
        "unsupported_ease50": unsupported_ease50,
        "unsupported_ease65": unsupported_ease65,
        "unsupported_ease_marked_suspicion": unsupported_ease_marked_suspicion,
        "unsupported_ease_usage_suspicion": unsupported_ease_usage_suspicion,
        "unsupported_ease_suspicion": unsupported_ease_suspicion,
        "unsupported_ease_content": unsupported_ease_content,
        "unsupported_ease_marked": unsupported_ease_marked,
        "unsupported_ease_usage": unsupported_ease_usage,
        "unsupported_ease_structural": unsupported_ease_structural,
        "unsupported_ease_floor040": unsupported_ease_floor040,
        "unsupported_ease_floor050": unsupported_ease_floor050,
        "unsupported_ease_content_floor050": unsupported_ease_content_floor050,
        "unsupported_ease_marked_floor060": unsupported_ease_marked_floor060,
        "unsupported_ease_usage_floor060": unsupported_ease_usage_floor060,
        "unsupported_ease_structural_floor060": unsupported_ease_structural_floor060,
        "learner_core_score": learner_core_score,
        "learner_core_confidence": learner_core_confidence,
        "learner_core_gap_blend": learner_core_gap_blend,
        "learner_core_gap_zipf": learner_core_gap_zipf,
        "learner_core_gap_blend_confident": learner_core_gap_blend * learner_core_confidence,
        "learner_core_gap_zipf_confident": learner_core_gap_zipf * learner_core_confidence,
        "learner_core_gap_blend_quality": learner_core_gap_blend * learner_rescue_quality_gate,
        "learner_core_gap_zipf_quality": learner_core_gap_zipf * learner_rescue_quality_gate,
        "learner_core_gap_blend_strict": learner_core_gap_blend * learner_rescue_strict_gate,
        "learner_core_gap_zipf_strict": learner_core_gap_zipf * learner_rescue_strict_gate,
    }
    components.update(cognate)
    return {key: _round_float(value) for key, value in components.items()}


def _score_variant(variant: FormulaVariant, components: Mapping[str, float]) -> float:
    base = _safe_float(components.get(variant.base_component))
    if base is None:
        base = _safe_float(components.get("spalex_blend")) or 0.0
    up_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in variant.up_weights.items()
    )
    down_raw = sum(
        float(weight) * (_safe_float(components.get(component)) or 0.0)
        for component, weight in variant.down_weights.items()
    )
    up = min(up_raw, variant.up_cap) if variant.up_cap is not None else up_raw
    down = min(down_raw, variant.down_cap) if variant.down_cap is not None else down_raw
    return _round_float(_clamp01(base + up - down))


def _variant_report(
    variant: FormulaVariant,
    *,
    scored_rows: Sequence[Mapping[str, object]],
    base_variant_id: str,
    sample_limit: int,
) -> dict[str, object]:
    rows = [
        _variant_row(row, variant_id=variant.variant_id, base_variant_id=base_variant_id)
        for row in scored_rows
    ]
    deltas = [_safe_float(row.get("delta")) or 0.0 for row in rows]
    scores = [_safe_float(row.get("score")) or 0.0 for row in rows]
    largest_raises = sorted(
        rows, key=lambda row: _safe_float(row.get("delta")) or 0.0, reverse=True
    )[:sample_limit]
    largest_lowers = sorted(rows, key=lambda row: _safe_float(row.get("delta")) or 0.0)[
        :sample_limit
    ]
    return {
        "variant_id": variant.variant_id,
        "description": variant.description,
        "base_component": variant.base_component,
        "up_weights": dict(variant.up_weights),
        "down_weights": dict(variant.down_weights),
        "up_cap": variant.up_cap,
        "down_cap": variant.down_cap,
        "summary": {
            "row_count": len(rows),
            "mean_score": _mean(scores),
            "mean_delta_from_base": _mean(deltas),
            "raised_count": sum(1 for delta in deltas if delta > 0.0005),
            "lowered_count": sum(1 for delta in deltas if delta < -0.0005),
            "max_raise": max(deltas) if deltas else 0.0,
            "max_lower": min(deltas) if deltas else 0.0,
            "band_counts": _band_counts(scores),
        },
        "change_samples": {
            "largest_raises": largest_raises,
            "largest_lowers": largest_lowers,
        },
        "band_samples": _band_samples(rows, sample_limit=sample_limit),
    }


def _variant_row(
    row: Mapping[str, object],
    *,
    variant_id: str,
    base_variant_id: str,
) -> dict[str, object]:
    scores = _as_mapping(row.get("variant_scores"))
    components = _as_mapping(row.get("components"))
    score = _safe_float(scores.get(variant_id)) or 0.0
    base_score = _safe_float(scores.get(base_variant_id)) or score
    return {
        "lemma": row.get("lemma"),
        "score": _round_float(score),
        "base_score": _round_float(base_score),
        "delta": _round_float(score - base_score),
        "spalex_rank": row.get("spalex_rank"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "translations": row.get("translations"),
        "signals": _salient_signals(components),
    }


def _salient_signals(components: Mapping[str, object]) -> list[dict[str, object]]:
    keys = (
        "pos_function_risk",
        "pos_other_risk",
        "gated_dict_marked_usage_risk",
        "dict_region_tag_count_score",
        "dict_domain_topic_count_score",
        "dict_register_colloquial_score",
        "dict_register_sensitive_score",
        "dict_register_rare_dated_score",
        "regional_colloquial_gate",
        "tail_domain_specificity",
        "tail_rare_dated_register",
        "dict_variant_risk",
        "tail_dict_ambiguity",
        "weak_form_risk",
        "cognate_rescue",
        "false_friend_caution",
        "learner_core_gap_zipf_confident",
        "learner_core_gap_blend_confident",
        "learner_core_confidence",
        "wordfreq_commonness",
        "wordfreq_source_rescue",
        "wordfreq_tail_rescue",
        "wordfreq_regional_rescue",
        "wordfreq_source_caution",
        "wordfreq_tail_caution",
        "lexcom_complexity",
        "lexcom_learner_rescue",
        "lexcom_rescue_after020",
        "lexcom_rescue_after030",
        "lexcom_rescue_after040",
        "lexcom_tail_rescue",
        "lexcom_learner_caution",
        "lexcom_tail_caution",
        "learner_broad_source_absent",
        "learner_broad_absence_tail65",
        "positive_ease_support",
        "unsupported_ease50",
        "unsupported_ease65",
        "unsupported_ease_content",
        "unsupported_ease_marked",
        "unsupported_ease_usage",
        "unsupported_ease_structural",
        "unsupported_ease_floor050",
        "unsupported_ease_marked_floor060",
        "unsupported_ease_usage_floor060",
        "unsupported_ease_structural_floor060",
    )
    rows = [
        {"component": key, "value": _round_float(components.get(key))}
        for key in keys
        if (_safe_float(components.get(key)) or 0.0) > 0.01
    ]
    return sorted(rows, key=lambda row: float(row["value"]), reverse=True)[:5]


def _band_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    sample_limit: int,
    band_width: float = 0.10,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index in range(int(round(1.0 / band_width))):
        low = round(index * band_width, 6)
        high = round((index + 1) * band_width, 6)
        center = (low + high) / 2.0
        band_rows = [
            row
            for row in rows
            if (_safe_float(row.get("score")) or 0.0) >= low
            and (
                (_safe_float(row.get("score")) or 0.0) < high
                or (
                    index == int(round(1.0 / band_width)) - 1
                    and (_safe_float(row.get("score")) or 0.0) <= 1.0
                )
            )
        ]
        selected = sorted(
            band_rows,
            key=lambda row: (
                abs((_safe_float(row.get("score")) or 0.0) - center),
                _safe_float(row.get("spalex_rank")) or 0.0,
            ),
        )[:sample_limit]
        result.append(
            {
                "band": f"{low:.2f}-{high:.2f}",
                "count": len(band_rows),
                "rows": selected,
            }
        )
    return result


def _component_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    component_names = sorted(
        {key for row in rows for key in _as_mapping(row.get("components")).keys()}
    )
    summary_rows = []
    for component in component_names:
        values = [
            _safe_float(_as_mapping(row.get("components")).get(component)) or 0.0 for row in rows
        ]
        nonzero = sum(1 for value in values if abs(value) > 0.0005)
        summary_rows.append(
            {
                "component": component,
                "mean": _mean(values),
                "nonzero_count": nonzero,
                "nonzero_share": _ratio(nonzero, len(values)),
            }
        )
    priority = {
        "spalex_blend": 0,
        "rank_base": 1,
        "zipf_base": 2,
        "pos_function_risk": 3,
        "dict_ambiguity": 4,
        "gated_dict_marked_usage_risk": 5,
        "dict_variant_risk": 6,
        "weak_form_risk": 7,
        "cognate_rescue": 8,
        "wordfreq_commonness": 9,
        "wordfreq_source_rescue": 10,
        "wordfreq_tail_rescue": 11,
        "lexcom_complexity": 12,
        "lexcom_learner_rescue": 13,
        "lexcom_rescue_after030": 14,
        "lexcom_learner_caution": 15,
    }
    return {
        "components": sorted(
            summary_rows,
            key=lambda row: (
                priority.get(str(row.get("component")), 100),
                str(row.get("component")),
            ),
        )
    }


def _build_findings(
    *,
    palette: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    translations_by_lemma: Mapping[str, Sequence[str]],
    english_commonness: Mapping[str, float],
    wordfreq_zipf_by_lemma: Mapping[str, float],
    lexcom_by_token: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if palette.get("status") != "ok":
        findings.append(
            _finding("FAIL", "palette_not_ok", "Underlying en-es signal palette is not OK.")
        )
    if not rows:
        findings.append(
            _finding("FAIL", "rows_empty", "No rows were available for formula probing.")
        )
    if not any(translations_by_lemma.values()):
        findings.append(
            _finding("WARN", "translations_missing", "No Wiktionary translations were available.")
        )
    if not english_commonness:
        findings.append(
            _finding(
                "WARN",
                "english_frequency_missing",
                "No English frequency values were available for translation tokens.",
            )
        )
    if not wordfreq_zipf_by_lemma:
        findings.append(
            _finding(
                "WARN",
                "wordfreq_missing",
                "No optional wordfreq Spanish Zipf values were available.",
            )
        )
    if not lexcom_by_token:
        findings.append(
            _finding(
                "WARN",
                "lexcom_missing",
                "No optional LexComSpaL2 learner-complexity rows were available.",
            )
        )
    if not findings or not any(row["level"] == "FAIL" for row in findings):
        findings.append(
            _finding(
                "OK",
                "formula_probe_ready",
                "Candidate en-es difficulty formula shapes were generated without production changes.",
            )
        )
    return findings


def _frequency_stats(
    frequency_db: Path | None,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, float]:
    fallback_ranks = [
        _safe_float(
            _as_mapping(row.get("raw_frequency")).get("spalex_rank") or row.get("core_rank")
        )
        for row in rows
    ]
    stats = {
        "max_rank": max(
            (value for value in fallback_ranks if value is not None), default=float(len(rows) or 1)
        ),
        "min_freq": 0.0,
        "max_freq": 1.0,
        "min_zipf": 0.0,
        "max_zipf": 1.0,
        "min_prevalence": 0.0,
        "max_prevalence": 1.0,
    }
    if frequency_db is None or not frequency_db.is_file():
        return stats
    with sqlite3.connect(frequency_db) as conn:
        columns = _column_names(conn, "frequency")
        if "spalex_rank" in columns:
            stats["max_rank"] = (
                _safe_float(conn.execute("SELECT MAX(spalex_rank) FROM frequency").fetchone()[0])
                or stats["max_rank"]
            )
        elif "core_rank" in columns:
            stats["max_rank"] = (
                _safe_float(conn.execute("SELECT MAX(core_rank) FROM frequency").fetchone()[0])
                or stats["max_rank"]
            )
        for key, column in (
            ("freq", "spalex_freq"),
            ("zipf", "spalex_zipf"),
            ("prevalence", "spalex_prevalence_total"),
        ):
            if column not in columns:
                continue
            row = conn.execute(
                f"SELECT MIN({_quote_ident(column)}), MAX({_quote_ident(column)}) "
                "FROM frequency WHERE "
                f"{_quote_ident(column)} IS NOT NULL"
            ).fetchone()
            if row:
                minimum = _safe_float(row[0])
                maximum = _safe_float(row[1])
                if minimum is not None:
                    stats[f"min_{key}"] = minimum
                if maximum is not None:
                    stats[f"max_{key}"] = maximum
    return {key: _round_float(value) for key, value in stats.items()}


def _load_translation_entries(
    path: Path | None,
    lemmas: Sequence[str],
) -> dict[str, tuple[Mapping[str, str], ...]]:
    keys = [str(lemma).strip().lower() for lemma in dict.fromkeys(lemmas) if str(lemma).strip()]
    index = {key: () for key in keys}
    if path is None or not path.is_file() or not keys:
        return index
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        if not _table_exists(conn, "sense_glosses"):
            return index
        columns = _column_names(conn, "sense_glosses")
        if "headword_lc" not in columns or "translation_lc" not in columns:
            return index
        translations: dict[str, list[dict[str, str]]] = {key: [] for key in keys}
        for chunk in _chunks(keys, size=500):
            placeholders = ", ".join("?" for _ in chunk)
            query = (
                "SELECT headword_lc, translation_lc, pos FROM sense_glosses "
                f"WHERE headword_lc IN ({placeholders}) "
                "AND TRIM(COALESCE(translation_lc, '')) != ''"
            )
            for row in conn.execute(query, chunk):
                key = str(row["headword_lc"]).strip().lower()
                text = str(row["translation_lc"]).strip()
                pos = str(row["pos"] or "").strip().lower()
                entry = {"translation": text, "pos": pos}
                if text and entry not in translations.setdefault(key, []):
                    translations[key].append(entry)
        return {key: tuple(values[:12]) for key, values in translations.items()}


def _load_english_commonness(
    path: Path | None,
    tokens: Sequence[str],
) -> dict[str, float]:
    keys = [str(token).strip().lower() for token in dict.fromkeys(tokens) if str(token).strip()]
    if path is None or not path.is_file() or not keys:
        return {}
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        if not _table_exists(conn, "frequency"):
            return {}
        columns = _column_names(conn, "frequency")
        if "lemma" not in columns or "core_rank" not in columns:
            return {}
        max_rank = (
            _safe_float(
                conn.execute(
                    "SELECT MAX(core_rank) FROM frequency WHERE core_rank IS NOT NULL"
                ).fetchone()[0]
            )
            or 1.0
        )
        result: dict[str, float] = {}
        for chunk in _chunks(keys, size=500):
            placeholders = ", ".join("?" for _ in chunk)
            query = f"SELECT lemma, core_rank FROM frequency WHERE lemma IN ({placeholders})"
            for row in conn.execute(query, chunk):
                rank = _safe_float(row["core_rank"])
                if rank is None:
                    continue
                result[str(row["lemma"]).strip().lower()] = _round_float(
                    1.0 - _rank_difficulty(rank, max_rank)
                )
        return result


def _load_wordfreq_zipf(
    lemmas: Sequence[str],
    *,
    enabled: bool,
    language: str,
) -> dict[str, float]:
    if not enabled:
        return {}
    keys = [str(lemma).strip().lower() for lemma in dict.fromkeys(lemmas) if str(lemma).strip()]
    if not keys:
        return {}
    try:
        from wordfreq import zipf_frequency
    except Exception:
        return {}
    result: dict[str, float] = {}
    for key in keys:
        try:
            value = _safe_float(zipf_frequency(key, language)) or 0.0
        except Exception:
            value = 0.0
        if value > 0.0:
            result[key] = _round_float(value)
    return result


def _wordfreq_commonness(zipf: object) -> float:
    value = _safe_float(zipf) or 0.0
    if value <= 0.0:
        return 0.0
    span = WORDFREQ_MAX_ZIPF - WORDFREQ_MIN_ZIPF
    return _clamp01((value - WORDFREQ_MIN_ZIPF) / span)


def _wordfreq_signal_summary(
    wordfreq_zipf_by_lemma: Mapping[str, float],
    row_count: int,
) -> dict[str, object]:
    values = [
        _safe_float(value) or 0.0
        for value in wordfreq_zipf_by_lemma.values()
        if (_safe_float(value) or 0.0) > 0.0
    ]
    return {
        "language": DEFAULT_WORDFREQ_LANGUAGE,
        "rows_with_zipf": len(values),
        "coverage": _ratio(len(values), row_count),
        "mean_zipf": _mean(values),
        "min_zipf": min(values) if values else 0.0,
        "max_zipf": max(values) if values else 0.0,
        "normalization": {
            "min_zipf": WORDFREQ_MIN_ZIPF,
            "max_zipf": WORDFREQ_MAX_ZIPF,
            "formula": "commonness = clamp((zipf - min_zipf) / (max_zipf - min_zipf))",
        },
    }


def _load_lexcomspal2(path: Path | None) -> dict[str, Mapping[str, object]]:
    if path is None or not path.is_file():
        return {}
    grouped: dict[str, list[dict[str, object]]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            token = str(row.get("token") or "").strip().lower()
            if not token:
                continue
            complexity = _parse_complexity_dict(row.get("complexity"))
            overall = _safe_float(complexity.get("overall"))
            if overall is None:
                continue
            grouped.setdefault(token, []).append(
                {
                    "overall": _clamp01(overall),
                    "pl1": _clamp01(_safe_float(complexity.get("PL1")) or overall),
                    "pl2": _clamp01(_safe_float(complexity.get("PL2")) or overall),
                    "pl3": _clamp01(_safe_float(complexity.get("PL3")) or overall),
                    "domain": str(row.get("corpus") or "").strip(),
                }
            )
    result: dict[str, Mapping[str, object]] = {}
    for token, values in grouped.items():
        domains = sorted(
            {str(value.get("domain") or "") for value in values if str(value.get("domain") or "")}
        )
        result[token] = {
            "overall": _mean([_safe_float(value.get("overall")) or 0.0 for value in values]),
            "pl1": _mean([_safe_float(value.get("pl1")) or 0.0 for value in values]),
            "pl2": _mean([_safe_float(value.get("pl2")) or 0.0 for value in values]),
            "pl3": _mean([_safe_float(value.get("pl3")) or 0.0 for value in values]),
            "row_count": len(values),
            "domains": domains,
        }
    return result


def _parse_complexity_dict(value: object) -> Mapping[str, object]:
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _lexcom_signal_summary(
    lexcom_by_token: Mapping[str, Mapping[str, object]],
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    complexities = [
        _safe_float(row.get("overall")) or 0.0
        for row in lexcom_by_token.values()
        if _safe_float(row.get("overall")) is not None
    ]
    probe_hits = [
        row
        for row in rows
        if (_safe_float(_as_mapping(row.get("components")).get("lexcom_known")) or 0.0) > 0.0
    ]
    return {
        "source_token_count": len(lexcom_by_token),
        "probe_rows_with_hit": len(probe_hits),
        "probe_coverage": _ratio(len(probe_hits), len(rows)),
        "mean_complexity": _mean(complexities),
        "min_complexity": min(complexities) if complexities else 0.0,
        "max_complexity": max(complexities) if complexities else 0.0,
        "note": "LexComSpaL2 complexity is already on a 0-1 learner difficulty scale.",
    }


def _cognate_signals(
    row: Mapping[str, object],
    *,
    context: ComponentContext,
    dict_ambiguity: float,
    base_frequency: float,
) -> dict[str, float]:
    lemma = str(row.get("lemma") or "")
    surface = _latin_key(lemma)
    if not surface:
        return {
            "english_translation_similarity_ease": 0.0,
            "english_translation_frequency_ease": 0.0,
            "cognate_rescue": 0.0,
            "rare_cognate_tail_rescue": 0.0,
            "false_friend_caution": 0.0,
        }
    row_pos = _normalize_dictionary_pos(row.get("pos_canonical") or row.get("pos_raw"))
    if row_pos not in {"adjective", "adverb", "noun", "verb"}:
        return {
            "english_translation_similarity_ease": 0.0,
            "english_translation_frequency_ease": 0.0,
            "cognate_rescue": 0.0,
            "rare_cognate_tail_rescue": 0.0,
            "false_friend_caution": 0.0,
        }
    best_similarity = 0.0
    best_commonness = 0.0
    best_score = 0.0
    for entry in context.translation_entries_by_lemma.get(lemma.lower(), ()):
        entry_pos = _normalize_dictionary_pos(entry.get("pos"))
        if entry_pos and entry_pos != row_pos:
            continue
        translation = str(entry.get("translation") or "")
        for token in _translation_tokens(translation):
            if min(len(surface), len(token)) < 4 and surface != token:
                continue
            ratio = SequenceMatcher(None, surface, token).ratio()
            if ratio < 0.62:
                continue
            similarity = _clamp01((ratio - 0.62) / 0.38)
            commonness = context.english_commonness.get(token, 0.0)
            score = similarity * (0.25 + 0.75 * commonness)
            if score > best_score:
                best_score = score
                best_similarity = similarity
                best_commonness = commonness
    return {
        "english_translation_similarity_ease": best_similarity,
        "english_translation_frequency_ease": best_commonness,
        "cognate_rescue": best_score,
        "rare_cognate_tail_rescue": _tail(base_frequency, 0.50) * best_score,
        "false_friend_caution": best_similarity * dict_ambiguity * 0.50,
    }


def _normalize_dictionary_pos(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"adj", "adjective"}:
        return "adjective"
    if text in {"adv", "adverb"}:
        return "adverb"
    if text in {"n", "noun", "proper noun"}:
        return "noun"
    if text in {"v", "verb"}:
        return "verb"
    if text in {"conj", "conjunction"}:
        return "conjunction"
    if text in {"det", "determiner", "article"}:
        return "determiner"
    if text in {"prep", "preposition", "adp", "adposition"}:
        return "adposition"
    if text in {"pron", "pronoun"}:
        return "pronoun"
    return text


def _translation_tokens(value: str) -> tuple[str, ...]:
    normalized = _latin_key(value.replace("'", " "))
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(normalized):
        token = raw.strip("-'")
        if len(token) < 3 or token in ENGLISH_STOPWORDS:
            continue
        if token not in tokens:
            tokens.append(token)
    return tuple(tokens[:10])


def _weak_form_risk(form: Mapping[str, object]) -> float:
    return _weighted_mean(
        (
            (_char_length_difficulty(form), 0.40),
            (1.0 if form.get("has_space") else 0.0, 0.25),
            (
                1.0
                if form.get("has_hyphen") or form.get("has_punctuation") or form.get("has_digit")
                else 0.0,
                0.20,
            ),
            (0.20 if form.get("has_diacritic") else 0.0, 0.10),
            (0.20 if form.get("has_spanish_specific_letter") else 0.0, 0.05),
        )
    )


def _char_length_difficulty(form: Mapping[str, object]) -> float:
    char_count = _safe_float(form.get("char_count")) or 0.0
    return _clamp01((char_count - 7.0) / 12.0)


def _rank_difficulty(rank: object, max_rank: object) -> float:
    numeric = _safe_float(rank)
    maximum = _safe_float(max_rank)
    if numeric is None or maximum is None or numeric <= 1.0 or maximum <= 1.0:
        return 0.0
    return _clamp01(math.log(numeric) / math.log(maximum))


def _inverse_log_difficulty(value: object, minimum: object, maximum: object) -> float:
    numeric = _safe_float(value)
    low = _safe_float(minimum)
    high = _safe_float(maximum)
    if numeric is None or low is None or high is None or high <= low or numeric <= 0:
        return 0.0
    low = max(low, 1e-12)
    normalized = (math.log(max(numeric, low)) - math.log(low)) / (math.log(high) - math.log(low))
    return 1.0 - _clamp01(normalized)


def _inverse_linear_difficulty(value: object, minimum: object, maximum: object) -> float:
    numeric = _safe_float(value)
    low = _safe_float(minimum)
    high = _safe_float(maximum)
    if numeric is None or low is None or high is None or high <= low:
        return 0.0
    return 1.0 - _clamp01((numeric - low) / (high - low))


def _log_score(value: object, *, ceiling: float) -> float:
    numeric = _safe_float(value)
    if numeric is None or numeric <= 1.0:
        return 0.0
    return _clamp01(math.log1p(numeric - 1.0) / math.log1p(ceiling))


def _tail(value: object, threshold: float) -> float:
    numeric = _safe_float(value) or 0.0
    if numeric <= threshold:
        return 0.0
    return _clamp01((numeric - threshold) / (1.0 - threshold))


def _early_gate(value: object, *, ceiling: float) -> float:
    numeric = _safe_float(value) or 0.0
    if numeric >= ceiling:
        return 0.0
    return _clamp01((ceiling - numeric) / max(ceiling, 1e-6))


def _weighted_mean(values: Sequence[tuple[object, float]]) -> float:
    numerator = 0.0
    denominator = 0.0
    for raw_value, raw_weight in values:
        value = _safe_float(raw_value)
        weight = float(raw_weight)
        if value is None or weight <= 0.0:
            continue
        numerator += value * weight
        denominator += weight
    return _clamp01(numerator / denominator) if denominator else 0.0


def _band_counts(scores: Sequence[float]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for score in scores:
        bucket = min(9, int(_clamp01(score) * 10.0))
        counts[f"{bucket / 10.0:.1f}-{(bucket + 1) / 10.0:.1f}"] += 1
    return dict(sorted(counts.items()))


def _resolve_kaikki_forward_db(
    requested: Path | None,
    palette_resolved: Path | None,
    data_root: Path,
) -> Path | None:
    candidates: list[Path] = []
    for value in (requested, palette_resolved):
        if value is None:
            continue
        resolved = Path(value).expanduser().resolve(strict=False)
        candidates.extend((resolved, resolved / "main.sqlite" if resolved.is_dir() else resolved))
    candidates.extend(
        (
            data_root / "language_packs" / "wiktionary-es-en" / "main.sqlite",
            data_root / "language_packs" / "wiktionary-es-en.sqlite",
        )
    )
    for candidate in _unique_paths(candidates):
        if candidate.is_file():
            return candidate
    return requested.expanduser().resolve(strict=False) if requested else palette_resolved


def _resolve_english_frequency_db(
    requested: Path | None,
    frequency_packs_dir: Path,
) -> Path | None:
    if requested is not None:
        resolved = requested.expanduser().resolve(strict=False)
        if resolved.is_file():
            return resolved
        if resolved.is_dir() and (resolved / "main.sqlite").is_file():
            return (resolved / "main.sqlite").resolve(strict=False)
        return resolved
    resolved = default_frequency_db_path("es-en", frequency_packs_dir=frequency_packs_dir)
    return Path(resolved).expanduser().resolve(strict=False) if resolved else None


def _path_or_none(value: object) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    return Path(text).expanduser().resolve(strict=False) if text else None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    if not _table_exists(conn, table):
        return []
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({_quote_ident(table)})")]


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


def _latin_key(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value or "").lower())
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return "".join(
        char for char in stripped if char.isascii() and (char.isalpha() or char.isspace())
    )


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


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


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None else 0.0


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _mean(values: Sequence[object]) -> float:
    numerics = [_safe_float(value) for value in values]
    filtered = [value for value in numerics if value is not None]
    return _round_float(sum(filtered) / len(filtered)) if filtered else 0.0


def _ratio(count: int, total: int) -> float:
    return _round_float(float(count) / float(total)) if total else 0.0


def _pct(value: object) -> str:
    numeric = _safe_float(value) or 0.0
    return f"{numeric * 100.0:.1f}%"


def _fmt_float(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.3f}"


def _fmt_signed(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return ""
    return f"{numeric:+.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return ""
    return f"{int(round(numeric))}"


def _signal_text(row: Mapping[str, object]) -> str:
    signals = _as_sequence(row.get("signals"))
    if not signals:
        return "-"
    return ", ".join(
        f"`{_escape(_as_mapping(signal).get('component'))}={_fmt_float(_as_mapping(signal).get('value'))}`"
        for signal in signals
    )


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
