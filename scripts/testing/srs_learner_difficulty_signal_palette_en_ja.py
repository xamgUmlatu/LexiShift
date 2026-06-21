#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402


PAIR = "en-ja"
DEFAULT_SOURCE_PY = SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"
DEFAULT_SWEEP_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "srs" / "srs_learner_difficulty_signal_palette_en_ja.md"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_ja_latest.json"
)


ROLE_DESCRIPTIONS = {
    "presentation_priority": (
        "General pressure for when a word should appear on the learner ladder."
    ),
    "pedagogical_anchor": (
        "Outside learner/curriculum source that can intentionally pull useful words earlier."
    ),
    "native_exposure": (
        "Frequency, corpus, or priority evidence for likely native exposure/usefulness."
    ),
    "evidence_quality": (
        "Knownness, coverage, or missingness signals used to control source trust."
    ),
    "orthographic_burden": (
        "Kanji, written-form, stroke, visual, or script burden after exposure signals."
    ),
    "ordinary_ladder_admission": (
        "Evidence that an item is or is not ordinary general vocabulary."
    ),
    "topic_register_policy": (
        "Topic, domain, register, entity, acronym, or specialist-use routing cue."
    ),
    "lexical_complexity": (
        "JMDict ambiguity, restrictions, source/form notes, or reading complexity."
    ),
    "word_origin_lane": ("Morphology or origin lane such as kango, wago, gairaigo, POS, or sahen."),
    "tail_shape": ("Late-vocabulary, unranked, rare-reading, or upper-tail shaping signal."),
    "calibration_transform": (
        "Nonlinear transform or interaction useful in sweeps, not an independent source."
    ),
}


SOURCE_FAMILY_DESCRIPTIONS = {
    "Acronym/code classifier": "Acronym/code metadata derived from script shape, dictionary, name, and corpus evidence.",
    "BCCWJ frequency": "BCCWJ rank/pmw/profile evidence from the local frequency pack.",
    "Candidate classifier": "Current candidate-state/problem-class signals emitted before learner difficulty scoring.",
    "Composite admission/topic": "Composite routing cues built from dictionary, frequency, name, and topic evidence.",
    "Internal script analyzer": "Built-in Japanese script-shape analyzer.",
    "JLPT vocabulary": "Tanos/Bluskyo JLPT vocabulary level data.",
    "JMDict lexical": "JMDict priority, POS, misc, field, form, reading, source, and sense metadata.",
    "JMnedict names": "JMnedict proper-name type metadata.",
    "KANJIDIC2": "KANJIDIC2 kanji grade, old JLPT, stroke, frequency, reading, radical, variant, and reference metadata.",
    "KanjiVG": "KanjiVG visual/component/position/variant metadata.",
    "Lesson vocabulary": "Step-by-Step Japanese lesson-order vocabulary metadata.",
    "Morphology/origin": "BCCWJ/UniDic-style word type and POS lanes plus kango/wago interactions.",
    "TUBELEX frequency": "TUBELEX spoken/video frequency evidence when available.",
    "Cross-source coverage": "Knownness and source-coverage evidence across multiple signal families.",
}


SUPPORTING_SIGNAL_ENTRIES: tuple[dict[str, object], ...] = (
    {
        "name": "jlpt_vocab_levels",
        "source_family": "JLPT vocabulary",
        "signal_kind": "raw_level_array",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": (
            "Per-row raw JLPT vocabulary level array stored in the component matrix; "
            "values are 1-5 where 5=N5/easiest and 1=N1/hardest."
        ),
        "model_surface": "supporting_matrix_field",
    },
    {
        "name": "jlpt_vocab_levels_raw",
        "source_family": "JLPT vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": (
            "Raw set of JLPT vocabulary levels attached to the source record before "
            "collapsing to easiest/hardest level."
        ),
        "model_surface": "available_source_metadata",
    },
    {
        "name": "jlpt_vocab_easiest_level",
        "source_family": "JLPT vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": (
            "Easiest available JLPT vocabulary level for the row; used to compute "
            "`jlpt_vocab_difficulty` and `jlpt_vocab_beginner_core`."
        ),
        "model_surface": "available_source_metadata",
    },
    {
        "name": "jlpt_vocab_hardest_level",
        "source_family": "JLPT vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": "Hardest available JLPT vocabulary level for rows with multiple source matches.",
        "model_surface": "available_source_metadata",
    },
    {
        "name": "jlpt_vocab_source_count",
        "source_family": "JLPT vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor"],
        "description": "Count of JLPT vocabulary source records merged into this row.",
        "model_surface": "available_source_metadata",
    },
    *(
        {
            "name": f"jlpt_vocab_is_n{level}",
            "source_family": "JLPT vocabulary",
            "signal_kind": "derived_binary_gate",
            "roles": ["pedagogical_anchor", "presentation_priority"],
            "description": (
                f"Derivable binary indicator that the JLPT vocabulary record includes N{level}. "
                "Not currently a difficulty component, but directly supported by raw `levels` metadata."
            ),
            "model_surface": "derivable_source_feature",
        }
        for level in (5, 4, 3, 2, 1)
    ),
    {
        "name": "jlpt_vocab_curve_grid",
        "source_family": "JLPT vocabulary",
        "signal_kind": "sweep_control",
        "roles": ["pedagogical_anchor", "calibration_transform"],
        "description": (
            "Sweep mode that remaps raw JLPT N5-N1 levels through candidate monotonic "
            "difficulty curves instead of using the baked source mapping."
        ),
        "model_surface": "sweep_parameter",
    },
    *(
        {
            "name": f"jlpt_vocab_n{level}_curve_value",
            "source_family": "JLPT vocabulary",
            "signal_kind": "sweep_control",
            "roles": ["pedagogical_anchor", "calibration_transform"],
            "description": (
                f"Sweepable numeric difficulty value for JLPT vocabulary N{level}; "
                "fed by the corresponding `--jlpt-vocab-n*-values` argument."
            ),
            "model_surface": "sweep_parameter",
        }
        for level in (5, 4, 3, 2, 1)
    ),
    {
        "name": "jlpt_kanji_dampening_strength",
        "source_family": "KANJIDIC2",
        "signal_kind": "sweep_control",
        "roles": ["orthographic_burden", "pedagogical_anchor", "calibration_transform"],
        "description": (
            "Sweepable strength for pulling selected kanji/orthographic burden components "
            "down toward a JLPT vocabulary anchor when a word has one."
        ),
        "model_surface": "sweep_parameter",
    },
    {
        "name": "kanjidic_old_jlpt_hardest_level",
        "source_family": "KANJIDIC2",
        "signal_kind": "raw_source_field",
        "roles": ["orthographic_burden"],
        "description": (
            "Raw hardest old-JLPT kanji level over the row's kanji; collapsed into "
            "`old_jlpt_kanji` for the active component surface."
        ),
        "model_surface": "available_source_metadata",
    },
    {
        "name": "kanjidic_old_jlpt_easiest_level",
        "source_family": "KANJIDIC2",
        "signal_kind": "raw_source_field",
        "roles": ["orthographic_burden"],
        "description": "Raw easiest old-JLPT kanji level over the row's kanji.",
        "model_surface": "available_source_metadata",
    },
    {
        "name": "lesson_vocab_earliest_lesson",
        "source_family": "Lesson vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": (
            "Raw earliest Step-by-Step Japanese lesson index; collapsed into "
            "`lesson_vocab_difficulty` and `lesson_vocab_beginner_core`."
        ),
        "model_surface": "available_source_metadata",
    },
    {
        "name": "lesson_vocab_lesson_indices",
        "source_family": "Lesson vocabulary",
        "signal_kind": "raw_source_field",
        "roles": ["pedagogical_anchor", "presentation_priority"],
        "description": "Raw set of Step-by-Step Japanese lesson indices for the row.",
        "model_surface": "available_source_metadata",
    },
)


SIGNAL_OVERRIDES = {
    "frequency": "BCCWJ rank-derived difficulty proxy; higher means weaker corpus frequency evidence and usually later presentation.",
    "frequency_ease": "Inverse of BCCWJ difficulty; higher means stronger commonness/ease evidence.",
    "frequency_sqrt": "Square-root transform of BCCWJ difficulty that amplifies lower/mid frequency difficulty.",
    "frequency_power2": "Squared BCCWJ difficulty that emphasizes upper-tail rarity.",
    "frequency_power3": "Cubed BCCWJ difficulty that strongly emphasizes upper-tail rarity.",
    "jmdict_priority": "Inverse JMDict priority signal; higher means weaker JMDict commonness/priority evidence.",
    "jmdict_non_vocab_raw_class_score": "Raw legacy JMDict non-vocab class score before ordinary-vocabulary protection; this bundles function, numeric, affix/counter, proper-noun, and marked-usage evidence.",
    "jmdict_particle_auxiliary_class": "JMDict POS overlap flag for particle or auxiliary-verb classes; raw source evidence, not direct difficulty.",
    "jmdict_numeric_class": "JMDict POS overlap flag for numeric classes; raw source evidence, not direct difficulty.",
    "jmdict_affix_counter_class": "JMDict POS overlap flag for prefix, suffix, or counter classes; raw source evidence, not direct difficulty.",
    "jmdict_function_discourse_class": "JMDict POS overlap flag for pronoun/interjection-style function or discourse words; raw source evidence, not direct difficulty.",
    "jmdict_proper_noun_overlap": "JMDict POS overlap flag for proper-noun classes; raw source evidence, not direct ladder-suppression risk.",
    "jmdict_non_ladder_entry_risk": "JMDict non-ladder risk after ordinary-vocabulary protection is applied to raw non-vocab class evidence.",
    "jmdict_non_vocab_risk": "Compatibility alias for `jmdict_non_ladder_entry_risk`; no longer the raw JMDict non-vocab class score.",
    "jmnedict_name_risk": "Compatibility alias for the raw JMnedict name-overlap score; use `jmnedict_name_overlap` for the clearer name.",
    "jmnedict_name_overlap": "Raw JMnedict name-overlap score; higher means stronger name evidence, not automatic ladder-suppression risk.",
    "jlpt_vocab_difficulty": "JLPT vocabulary level anchor; lower for N5/N4 and higher for N2/N1.",
    "jlpt_vocab_beginner_core": "Beginner-core strength from JLPT vocabulary data.",
    "lesson_vocab_difficulty": "Lesson-order difficulty anchor from Step-by-Step Japanese vocabulary.",
    "lesson_vocab_beginner_core": "Beginner-core strength from Step-by-Step Japanese lesson vocabulary.",
    "script_complexity": "Built-in script-complexity proxy from the Japanese script analyzer.",
    "kanji_grade": "KANJIDIC2 school-grade difficulty proxy over the word's kanji.",
    "kanji_frequency_rank": "KANJIDIC2 kanji frequency-rank difficulty proxy.",
    "old_jlpt_kanji": "Old JLPT kanji-level difficulty proxy over the word's kanji.",
    "stroke_count": "KANJIDIC2 stroke-count difficulty proxy.",
    "kanjivg_visual_complexity": "KanjiVG visual-complexity proxy for the written form.",
    "kanji_curriculum_burden": "Mean kanji curriculum burden from grade, old JLPT, and frequency-rank evidence.",
    "kanji_shape_burden": "Mean kanji shape burden from visual complexity and stroke count.",
    "max_kanji_shape_burden": "Maximum kanji shape burden across visual complexity and stroke-count signals.",
    "kanji_curriculum_missing_risk": "Risk that the word's kanji have shape evidence but weak curriculum-level evidence.",
    "kanji_burden": "Mean kanji burden combining curriculum, visual, and stroke evidence.",
    "max_kanji_burden": "Maximum kanji burden across curriculum, visual, and stroke evidence.",
    "written_form_burden": "Mean written-form burden from visual, stroke, and script-complexity signals.",
    "max_written_form_burden": "Maximum written-form burden from visual, stroke, and script-complexity signals.",
    "non_standard_reading_risk": "Risk that the observed reading does not match KANJIDIC2 character reading options.",
    "rare_non_standard_reading_risk": "Nonstandard-reading risk gated to upper-frequency-difficulty rows.",
    "jmnedict_person_name_overlap": "Raw JMnedict person-name overlap flag.",
    "jmnedict_place_name_overlap": "Raw JMnedict place-name overlap flag.",
    "jmnedict_org_product_name_overlap": "Raw JMnedict organization/product-name overlap flag.",
    "jmnedict_creative_or_special_name_overlap": "Raw JMnedict creative-work, character, mythic, or special-name overlap flag.",
    "proper_noun_pos_flag": "Raw POS flag for proper-noun classification.",
    "proper_place_pos_flag": "Raw POS flag for proper-place classification.",
    "proper_country_pos_flag": "Raw POS flag for proper-country classification.",
    "problem_class_proper_flag": "Raw candidate-classifier flag for proper-noun problem class.",
    "proper_place_entity_overlap": "Raw place-entity overlap from POS and JMnedict evidence before ordinary-vocabulary protection.",
    "proper_country_entity_overlap": "Raw country/geopolitical entity overlap before ordinary-vocabulary protection.",
    "proper_org_entity_overlap": "Raw organization/product entity overlap before ordinary-vocabulary protection.",
    "named_entity_overlap": "Raw named-entity overlap from POS, candidate class, JMnedict, and acronym evidence before ordinary-vocabulary protection.",
    "ordinary_vocab_protection": "Commonness and pedagogical-anchor protection used to keep ordinary vocabulary from becoming entity/non-ladder risk.",
    "entity_suppression_gate": "Gate that allows entity overlap to become ladder-suppression risk only when ordinary-vocabulary protection is weak or candidate evidence says deprioritized.",
    "ordinary_ladder_entity_suppression_risk": "Named-entity ladder-suppression risk after ordinary-vocabulary protection.",
    "named_entity_risk": "Compatibility alias for gated entity-suppression risk, not raw JMnedict/POS name overlap.",
    "news_or_policy_topic_risk": "Business, economics, law, or politics field/domain risk; JMDict `news` priority tags no longer create this signal.",
    "news_or_policy_frequency_risk": "News/policy topic risk multiplied by BCCWJ frequency difficulty.",
    "news_named_entity_risk": "News/policy topic risk combined with named-entity risk.",
    "news_named_frequency_risk": "News/policy named-entity risk multiplied by frequency difficulty.",
    "news_abbreviation_entity_risk": "News/policy abbreviation/entity risk for acronym-like topic rows.",
    "geopolitical_entity_risk": "Country/place entity risk, especially when tied to news/policy topics.",
    "geopolitical_frequency_risk": "Geopolitical entity risk multiplied by frequency difficulty.",
    "candidate_deprioritized_vocab_risk": "Current candidate classifier says the row is deprioritized vocabulary.",
    "candidate_deprioritized_named_entity_risk": "Candidate deprioritization combined with named-entity evidence.",
    "candidate_deprioritized_named_frequency_risk": "Candidate deprioritized named-entity risk multiplied by frequency difficulty.",
    "lesson_name_contamination_risk": "Lesson-vocabulary row also has named-entity evidence.",
    "lesson_name_contamination_frequency_risk": "Lesson name-contamination risk multiplied by frequency difficulty.",
    "kango_mid_signal": "Composite kango mid/upper-mid signal using kango origin, frequency, and kanji burden.",
    "kango_common_priority_risk": "Kango origin combined with weaker JMDict priority and frequency difficulty.",
    "sahen_kango_ease_gate": "Gate for sahen-noun kango rows that may behave like productive learner vocabulary.",
    "sahen_kango_risk": "Same underlying sahen-kango gate exposed as a risk-shaped component.",
    "rare_wago_risk": "Wago origin combined with rarity and weak JMDict priority.",
    "rare_wago_obscure_written_risk": "Rare-wago composite for obscure written forms, marked usage, missing curriculum, and rare readings.",
    "rare_wago_tail_risk": "Upper-tail rare-wago risk for late-ladder or non-general vocabulary pressure.",
    "written_wago_tail_risk": "Wago tail risk driven by frequency difficulty and written-form burden.",
    "jmdict_news_priority_risk": "Compatibility alias for the JMDict `news` priority tag; this is commonness/source evidence, not topic or difficulty risk.",
    "jmdict_news_priority_commonness": "Binary JMDict `news` priority tag used as source/commonness evidence, not as topic risk.",
    "bccwj_domain_rank_variability": "BCCWJ domain rank variability alias for domain rank spread; distribution-shape evidence, not direct difficulty.",
    "bccwj_domain_profile_variability": "BCCWJ domain profile variability from domain-rank coverage and spread; distribution-shape evidence, not direct topic risk.",
    "bccwj_domain_profile_risk": "Compatibility alias for BCCWJ domain profile variability; no longer used inside JMDict register/domain risk.",
    "bccwj_rank_variability": "BCCWJ rank variability alias for rank spread; distribution-shape evidence, not direct difficulty.",
    "bccwj_fixed_variable_rank_delta": "Signed BCCWJ fixed-vs-variable rank delta transformed into a normalized component.",
}


SIGNAL_KIND_OVERRIDES = {
    "jmdict_news_priority_risk": "source_flag_compat",
    "jmdict_news_priority_commonness": "source_flag",
    "jmdict_non_vocab_raw_class_score": "raw_class_score",
    "jmdict_non_vocab_risk": "risk_compat",
    "jmnedict_name_risk": "overlap_compat",
    "named_entity_risk": "risk_compat",
    "bccwj_domain_profile_risk": "variability_compat",
    "ordinary_vocab_protection": "protection",
    "entity_suppression_gate": "gate",
}

COMPATIBILITY_ALIASES = {
    "jmdict_marked_usage_risk": "jmdict_marked_usage_flag",
    "jmdict_kana_preferred_risk": "jmdict_kana_preferred_flag",
    "jmdict_register_marked_risk": "jmdict_register_marked_flag",
    "jmdict_dialect_risk": "jmdict_dialect_flag",
    "jmdict_loanword_source_risk": "jmdict_loanword_source_flag",
    "jmdict_sinitic_source": "jmdict_sinitic_source_flag",
    "jmdict_source_text_present": "jmdict_source_text_flag",
    "jmdict_source_type_marked": "jmdict_source_type_flag",
    "jmdict_wasei_source": "jmdict_wasei_source_flag",
    "jmdict_kanji_form_marked_risk": "jmdict_kanji_form_marked_flag",
    "jmdict_reading_form_marked_risk": "jmdict_reading_form_marked_flag",
    "jmdict_search_only_form_risk": "jmdict_search_only_form_flag",
    "jmdict_sense_restricted_risk": "jmdict_sense_restricted_flag",
    "jmdict_reading_restricted_risk": "jmdict_reading_restricted_flag",
    "jmdict_no_kanji_reading_risk": "jmdict_no_kanji_reading_flag",
    "jmdict_polysemy_risk": "jmdict_polysemy_flag",
    "jmdict_sense_info_risk": "jmdict_sense_info_flag",
    "jmdict_cross_reference_risk": "jmdict_cross_reference_flag",
    "jmdict_foreign_priority_risk": "jmdict_foreign_priority_commonness",
    "jmdict_abbreviation_risk": "jmdict_abbreviation_flag",
    "jmdict_organization_misc_risk": "jmdict_organization_misc_flag",
    "jmdict_news_or_policy_domain_risk": "jmdict_news_or_policy_field_flag",
    "jmdict_field_marked_risk": "jmdict_field_marked_flag",
    "jmnedict_person_name_risk": "jmnedict_person_name_overlap",
    "jmnedict_place_name_risk": "jmnedict_place_name_overlap",
    "jmnedict_org_product_name_risk": "jmnedict_org_product_name_overlap",
    "jmnedict_creative_or_special_name_risk": "jmnedict_creative_or_special_name_overlap",
    "proper_noun_pos_risk": "proper_noun_pos_flag",
    "proper_place_pos_risk": "proper_place_pos_flag",
    "proper_country_pos_risk": "proper_country_pos_flag",
    "problem_class_proper_risk": "problem_class_proper_flag",
    "wtype_proper_risk": "wtype_proper_flag",
    "jmdict_ambiguity_risk": "jmdict_ambiguity_score",
    "jmdict_reading_complexity_risk": "jmdict_reading_complexity_score",
    "jmdict_restriction_complexity_risk": "jmdict_restriction_complexity_score",
    "common_jmdict_ambiguity_risk": "common_jmdict_ambiguity_score",
    "common_reading_complexity_risk": "common_reading_complexity_score",
    "common_restriction_complexity_risk": "common_restriction_complexity_score",
    "jmdict_register_domain_risk": "jmdict_register_domain_score",
    "common_register_domain_risk": "common_register_domain_score",
    "common_kango_register_domain_risk": "common_kango_register_domain_score",
    "common_kango_ambiguity_risk": "common_kango_ambiguity_score",
    "common_kango_complexity_risk": "common_kango_complexity_score",
    "kanjidic_nanori_reading_risk": "kanjidic_nanori_reading_count_score",
    "kanjidic_variant_type_risk": "kanjidic_variant_type_count_score",
}


SIGNAL_ROLE_OVERRIDES = {
    "jmdict_news_priority_risk": ("native_exposure",),
    "jmdict_news_priority_commonness": ("native_exposure",),
    "jmdict_non_vocab_raw_class_score": ("ordinary_ladder_admission", "lexical_complexity"),
    "jmdict_non_ladder_entry_risk": ("ordinary_ladder_admission", "lexical_complexity"),
    "jmdict_non_vocab_risk": ("ordinary_ladder_admission", "lexical_complexity"),
    "jmnedict_name_risk": ("ordinary_ladder_admission",),
    "jmnedict_name_overlap": ("ordinary_ladder_admission",),
    "named_entity_overlap": ("ordinary_ladder_admission",),
    "ordinary_vocab_protection": (
        "ordinary_ladder_admission",
        "pedagogical_anchor",
        "native_exposure",
    ),
    "entity_suppression_gate": ("ordinary_ladder_admission",),
    "ordinary_ladder_entity_suppression_risk": ("ordinary_ladder_admission",),
    "named_entity_risk": ("ordinary_ladder_admission",),
    "bccwj_domain_rank_variability": ("native_exposure", "presentation_priority"),
    "bccwj_domain_profile_variability": ("native_exposure", "presentation_priority"),
    "bccwj_domain_profile_risk": ("native_exposure", "presentation_priority"),
    "bccwj_rank_variability": ("native_exposure", "presentation_priority"),
}


@dataclass(frozen=True)
class SignalEntry:
    name: str
    source_family: str
    signal_kind: str
    roles: tuple[str, ...]
    coverage_count: int
    coverage_rate: float | None
    in_latest_sweep: bool
    description: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the en-ja learner-difficulty signal palette."
    )
    parser.add_argument("--source-py", type=Path, default=DEFAULT_SOURCE_PY)
    parser.add_argument("--sweep-json", type=Path, default=DEFAULT_SWEEP_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        source_py=_resolve_path(args.source_py),
        sweep_json=_resolve_path(args.sweep_json),
    )
    markdown_out = _resolve_path(args.markdown_out)
    json_out = _resolve_path(args.json_out)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote Markdown palette to {markdown_out}")
    print(f"Wrote JSON palette to {json_out}")
    return 0


def build_report(*, source_py: Path, sweep_json: Path) -> dict[str, object]:
    component_names = component_names_from_source(source_py)
    sweep_payload = _load_json(sweep_json)
    coverage = _mapping(sweep_payload.get("signal_coverage"))
    component_counts = {
        str(key): int(value)
        for key, value in _mapping(coverage.get("component_counts")).items()
        if isinstance(value, int | float)
    }
    denominator = max(component_counts.values(), default=0)
    entries = build_entries(
        component_names,
        component_counts=component_counts,
        coverage_denominator=denominator,
    )
    source_counts = Counter(entry.source_family for entry in entries)
    role_counts: Counter[str] = Counter()
    for entry in entries:
        role_counts.update(entry.roles)
    supporting_signals = supporting_signal_entries()
    supporting_role_counts: Counter[str] = Counter()
    for entry in supporting_signals:
        supporting_role_counts.update(_sequence(entry.get("roles")))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "canonical_model_changed": False,
        "method": {
            "purpose": (
                "Enumerate every learner-difficulty component signal exposed by "
                "difficulty_components(...) as a model-design palette."
            ),
            "value_policy": (
                "Components are normalized 0-1 when present, but higher does not "
                "always mean harder. Use signal_kind and roles before treating a "
                "component as a scalar difficulty input."
            ),
        },
        "inputs": {
            "source_py": _repo_path(source_py),
            "sweep_json": _repo_path(sweep_json),
            "coverage_denominator": denominator,
            "latest_sweep_generated_at": sweep_payload.get("generated_at"),
        },
        "summary": {
            "component_count_from_code": len(component_names),
            "component_count_with_latest_coverage": sum(
                1 for entry in entries if entry.in_latest_sweep
            ),
            "component_count_without_latest_coverage": sum(
                1 for entry in entries if not entry.in_latest_sweep
            ),
            "supporting_signal_count": len(supporting_signals),
            "source_family_counts": dict(sorted(source_counts.items())),
            "role_counts": dict(sorted(role_counts.items())),
            "supporting_role_counts": dict(sorted(supporting_role_counts.items())),
        },
        "source_family_descriptions": SOURCE_FAMILY_DESCRIPTIONS,
        "role_descriptions": ROLE_DESCRIPTIONS,
        "signals": [
            {
                "name": entry.name,
                "source_family": entry.source_family,
                "signal_kind": entry.signal_kind,
                "roles": list(entry.roles),
                "coverage_count": entry.coverage_count,
                "coverage_rate": entry.coverage_rate,
                "in_latest_sweep": entry.in_latest_sweep,
                "description": entry.description,
            }
            for entry in entries
        ],
        "supporting_signals": supporting_signals,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "signal_sweep_source": source_py,
                "latest_sweep_json": sweep_json,
            },
            code_paths={"signal_palette_generator": Path(__file__)},
        ),
    }


def supporting_signal_entries() -> list[dict[str, object]]:
    return [
        {
            "name": str(entry["name"]),
            "source_family": str(entry["source_family"]),
            "signal_kind": str(entry["signal_kind"]),
            "roles": list(_sequence(entry.get("roles"))),
            "model_surface": str(entry["model_surface"]),
            "description": str(entry["description"]),
        }
        for entry in SUPPORTING_SIGNAL_ENTRIES
    ]


def component_names_from_source(source_py: Path) -> tuple[str, ...]:
    tree = ast.parse(source_py.read_text(encoding="utf-8"), filename=str(source_py))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "difficulty_components":
            return _return_dict_keys(node)
    raise ValueError(f"Could not find difficulty_components(...) in {source_py}")


def _return_dict_keys(function: ast.FunctionDef) -> tuple[str, ...]:
    for node in ast.walk(function):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            names: list[str] = []
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    names.append(key.value)
            if names:
                return tuple(dict.fromkeys(names))
    raise ValueError("difficulty_components(...) does not return a literal dict")


def build_entries(
    component_names: Sequence[str],
    *,
    component_counts: Mapping[str, int],
    coverage_denominator: int,
) -> tuple[SignalEntry, ...]:
    entries: list[SignalEntry] = []
    for name in component_names:
        coverage_count = int(component_counts.get(name, 0))
        coverage_rate = (
            round(coverage_count / coverage_denominator, 6) if coverage_denominator > 0 else None
        )
        entries.append(
            SignalEntry(
                name=name,
                source_family=source_family_for_signal(name),
                signal_kind=signal_kind_for_signal(name),
                roles=roles_for_signal(name),
                coverage_count=coverage_count,
                coverage_rate=coverage_rate,
                in_latest_sweep=name in component_counts,
                description=description_for_signal(name),
            )
        )
    return tuple(entries)


def source_family_for_signal(name: str) -> str:
    if name.startswith("acronym_") or name == "proper_acronym_entity_risk":
        return "Acronym/code classifier"
    if name == "source_coverage_count" or name.endswith("_source_known"):
        return "Cross-source coverage"
    if name.startswith("tubelex_"):
        return "TUBELEX frequency"
    if name.startswith("frequency") or name.startswith("bccwj_"):
        return "BCCWJ frequency"
    if name.startswith("jlpt_vocab_"):
        return "JLPT vocabulary"
    if name.startswith("lesson_"):
        return "Lesson vocabulary"
    if name.startswith("jmdict_") or name == "non_standard_reading_risk":
        return "JMDict lexical"
    if name.startswith("jmnedict_"):
        return "JMnedict names"
    if (
        name.startswith("kanjidic_")
        or name.startswith("kanji_")
        or name.startswith("max_kanji_")
        or name.startswith("old_jlpt_")
        or name.startswith("stroke_")
    ):
        return "KANJIDIC2"
    if name.startswith("kanjivg_"):
        return "KanjiVG"
    if name.startswith("candidate_") or name.startswith("problem_class_"):
        return "Candidate classifier"
    if (
        name.startswith("proper_")
        or name.startswith("named_")
        or name.startswith("news_")
        or name.startswith("geopolitical_")
    ):
        return "Composite admission/topic"
    if (
        name.startswith("wtype_")
        or name.startswith("pos_")
        or name.startswith("kango_")
        or name.startswith("wago_")
        or name.startswith("rare_wago_")
        or name.startswith("written_wago_")
        or name.startswith("sahen_")
    ):
        return "Morphology/origin"
    if name.startswith("rare_non_standard_"):
        return "Composite admission/topic"
    if name.startswith("script_"):
        return "Internal script analyzer"
    if name.startswith("written_") or name.startswith("max_written_"):
        return "KANJIDIC2"
    return "Composite admission/topic"


def signal_kind_for_signal(name: str) -> str:
    if name in SIGNAL_KIND_OVERRIDES:
        return SIGNAL_KIND_OVERRIDES[name]
    if name in COMPATIBILITY_ALIASES:
        target = COMPATIBILITY_ALIASES[name]
        if target.endswith("_flag") or target.endswith("_commonness"):
            return "source_flag_compat"
        if target.endswith("_overlap"):
            return "overlap_compat"
        return "score_compat"
    if name.endswith("_known"):
        return "knownness"
    if name == "source_coverage_count":
        return "coverage_count"
    if name.endswith("_flag"):
        return "source_flag"
    if name.endswith("_score"):
        return "score"
    if name.endswith("_overlap"):
        return "overlap"
    if name.endswith("_variability"):
        return "variability"
    if name.endswith("_commonness"):
        return "source_flag"
    if name.endswith("_protection"):
        return "protection"
    if name.endswith("_beginner_core") or name.endswith("_ease"):
        return "ease_or_beginner_anchor"
    if name.endswith("_confidence") or name.endswith("_coverage"):
        return "evidence_confidence"
    if name.endswith("_gate"):
        return "gate"
    if name.endswith("_risk"):
        return "risk"
    if name.endswith("_burden") or "burden" in name:
        return "burden"
    if "difficulty" in name or name in {
        "frequency",
        "jmdict_priority",
        "kanji_grade",
        "kanji_frequency_rank",
        "old_jlpt_kanji",
        "stroke_count",
        "kanjivg_visual_complexity",
        "script_complexity",
    }:
        return "difficulty_proxy"
    if name.endswith("_count") or name.endswith("_ambiguity"):
        return "count_or_ambiguity"
    if any(token in name for token in ("sqrt", "power", "tail", "floor", "min_", "mean_", "max_")):
        return "transform_or_interaction"
    return "signal"


def roles_for_signal(name: str) -> tuple[str, ...]:
    if name in SIGNAL_ROLE_OVERRIDES:
        return SIGNAL_ROLE_OVERRIDES[name]
    if name in COMPATIBILITY_ALIASES:
        return roles_for_signal(COMPATIBILITY_ALIASES[name])
    if name == "source_coverage_count":
        return ("evidence_quality",)
    if name.endswith("_known"):
        roles = ["evidence_quality"]
        if name.startswith(("frequency", "bccwj_", "tubelex_")):
            roles.extend(["native_exposure", "presentation_priority"])
        if name.startswith(("jlpt_vocab_", "lesson_vocab_", "pedagogical_")):
            roles.extend(["pedagogical_anchor", "presentation_priority"])
        if name.startswith(("kanji", "kanjidic", "kanjivg", "orthographic_")):
            roles.append("orthographic_burden")
        if name.startswith(("jmdict_", "lexical_")):
            roles.append("lexical_complexity")
        if name.startswith(("jmnedict_", "acronym_")):
            roles.append("ordinary_ladder_admission")
        return tuple(dict.fromkeys(roles))
    roles: list[str] = []
    if name.startswith("jlpt_vocab_") or name.startswith("lesson_vocab_"):
        roles.extend(["pedagogical_anchor", "presentation_priority"])
    if name.startswith("frequency") or name.startswith("bccwj_") or name.startswith("tubelex_"):
        roles.extend(["native_exposure", "presentation_priority"])
    if name == "jmdict_priority" or "priority" in name:
        roles.append("native_exposure")
    if any(
        token in name
        for token in (
            "kanji",
            "stroke",
            "kanjivg",
            "script_complexity",
            "written_form",
            "written_burden",
        )
    ):
        roles.append("orthographic_burden")
    if any(
        token in name
        for token in (
            "candidate_",
            "proper_",
            "named_",
            "entity",
            "non_vocab",
            "acronym_",
            "problem_class",
            "jmnedict_",
        )
    ):
        roles.append("ordinary_ladder_admission")
    if any(
        token in name
        for token in (
            "news",
            "policy",
            "geopolitical",
            "register",
            "dialect",
            "field",
            "domain",
            "abbreviation",
            "organization",
        )
    ):
        roles.append("topic_register_policy")
    if name.startswith("jmdict_") or any(
        token in name
        for token in (
            "reading",
            "sense",
            "gloss",
            "ambiguity",
            "polysemy",
            "restriction",
            "source",
            "form",
        )
    ):
        roles.append("lexical_complexity")
    if any(token in name for token in ("wtype_", "kango", "wago", "sahen", "pos_", "gairaigo")):
        roles.append("word_origin_lane")
    if any(token in name for token in ("rare", "tail", "unranked", "floor", "power")):
        roles.append("tail_shape")
    if any(
        token in name
        for token in (
            "sqrt",
            "power",
            "tail",
            "floor",
            "min_",
            "mean_",
            "max_",
            "agreement",
            "gap",
            "frequency_risk",
        )
    ):
        roles.append("calibration_transform")
    if not roles:
        roles.append("presentation_priority")
    return tuple(dict.fromkeys(roles))


def description_for_signal(name: str) -> str:
    if name in SIGNAL_OVERRIDES:
        return SIGNAL_OVERRIDES[name]
    if name in COMPATIBILITY_ALIASES:
        target = COMPATIBILITY_ALIASES[name]
        return (
            f"Compatibility alias for `{target}`; kept for older artifacts, "
            "but the target name is the clearer semantic surface."
        )
    if name.endswith("_known"):
        return (
            f"Knownness indicator for {_humanize(name.removesuffix('_known'))}; "
            "1 means the source evidence is present and 0 means it is absent."
        )
    if name == "source_coverage_count":
        return "Scaled count of major source families with known evidence for the row."
    if name.endswith("_flag"):
        return (
            f"Raw {_humanize(name.removesuffix('_flag'))} source flag; "
            "source evidence, not direct learner difficulty."
        )
    if name.endswith("_score"):
        return (
            f"{_humanize(name.removesuffix('_score'))} score; inspect roles before "
            "treating it as direct presentation difficulty."
        )
    if name.startswith("frequency_tail"):
        threshold = name.removeprefix("frequency_tail")
        return (
            f"BCCWJ difficulty ramp that activates above roughly {threshold}% "
            "frequency difficulty; useful for upper-tail shaping."
        )
    if name.startswith("frequency_unranked_floor"):
        floor = name.removeprefix("frequency_unranked_floor").removesuffix("_risk")
        return (
            f"Unranked-frequency risk with an enforced {floor}% floor when "
            "BCCWJ rank evidence is missing."
        )
    if name.startswith("frequency_unranked_tail"):
        return "Unranked-frequency risk gated by a BCCWJ upper-tail rarity ramp."
    if name.startswith("frequency_unranked_power"):
        power = name.removeprefix("frequency_unranked_power").removesuffix("_risk")
        return f"Unranked-frequency risk multiplied by BCCWJ difficulty to power {power}."
    if name.startswith("frequency_unranked"):
        return "Risk/interaction for rows missing usable BCCWJ rank evidence."
    if name.startswith("tubelex_bccwj_"):
        return "Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency."
    if name.startswith("tubelex_"):
        return (
            "TUBELEX spoken/video frequency component; useful as an alternate exposure perspective."
        )
    if name.startswith("acronym_"):
        return "Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing."
    if name.startswith("jmdict_"):
        return _jmdict_description(name)
    if name.startswith("jmnedict_"):
        return "JMnedict proper-name type risk for admission and entity routing."
    if name.startswith("kanjidic_"):
        return "KANJIDIC2 aggregate count or risk signal over the word's kanji."
    if name.startswith("kanjivg_"):
        return "KanjiVG visual/component structure signal over the word's written form."
    if name.startswith("proper_"):
        return "Composite proper-name/entity cue for ordinary-ladder admission and topic routing."
    if name.startswith("pos_"):
        return "POS gate from the seed row; useful for lane-specific model shapes."
    if name.startswith("wtype_"):
        return "Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes."
    if name.startswith("kango_"):
        return (
            "Kango-specific interaction signal for origin-conditioned presentation-level modeling."
        )
    if name.startswith("wago_") or name.startswith("rare_wago_"):
        return "Wago-specific interaction signal for origin-conditioned and tail modeling."
    if name.endswith("_risk"):
        return f"{_humanize(name.removesuffix('_risk'))} risk signal; higher means stronger evidence for that property."
    if name.endswith("_gate"):
        return f"{_humanize(name.removesuffix('_gate'))} gate; higher means the gate is active."
    if name.endswith("_burden"):
        return f"{_humanize(name.removesuffix('_burden'))} burden signal; higher means more learner burden."
    if name.endswith("_count"):
        return f"Scaled {_humanize(name.removesuffix('_count'))} count signal."
    return f"{_humanize(name)} component exposed to learner-difficulty model sweeps."


def _jmdict_description(name: str) -> str:
    if "ambiguity" in name:
        return "JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity."
    if "reading" in name:
        return "JMDict reading/form restriction or reading-complexity signal."
    if "sense" in name:
        return "JMDict sense-count, sense-info, or sense-restriction signal."
    if "source" in name:
        return "JMDict source-language/source-type signal for etymology and loanword policy."
    if "register" in name or "dialect" in name or "field" in name:
        return (
            "JMDict register, dialect, or field/domain signal for routing and presentation policy."
        )
    if "form" in name:
        return "JMDict kanji/reading/form marker or count signal."
    if "count" in name:
        return "Scaled JMDict count signal over entries, POS values, fields, forms, senses, or glosses."
    return "JMDict lexical signal for priority, usage, source, field, form, or sense structure."


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Learner Difficulty Signal Palette",
        "",
        "Status: generated model-design palette",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "Purpose: enumerate every component signal currently exposed by the en-ja "
        "learner-difficulty sweep surface. Treat this as the palette for model-shape "
        "design: not every signal is a scalar difficulty signal, and several are "
        "better understood as admission, topic, burden, or calibration-shape cues.",
        "",
        "## Inputs",
        "",
        f"- Source code: `{_escape(inputs.get('source_py'))}`",
        f"- Coverage artifact: `{_escape(inputs.get('sweep_json'))}`",
        f"- Coverage denominator: `{_escape(inputs.get('coverage_denominator'))}`",
        f"- Latest sweep generated at: `{_escape(inputs.get('latest_sweep_generated_at'))}`",
        "",
        "## Summary",
        "",
        f"- Component names in code: `{_escape(summary.get('component_count_from_code'))}`",
        f"- Components with latest non-null coverage: `{_escape(summary.get('component_count_with_latest_coverage'))}`",
        f"- Components without latest non-null coverage: `{_escape(summary.get('component_count_without_latest_coverage'))}`",
        f"- Supporting raw/derived/sweep signals: `{_escape(summary.get('supporting_signal_count'))}`",
        "",
        "## Modeling Roles",
        "",
        "| Role | Count | Meaning |",
        "| --- | ---: | --- |",
    ]
    role_counts = _mapping(summary.get("role_counts"))
    role_descriptions = _mapping(report.get("role_descriptions"))
    for role in sorted(role_counts):
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape(role)}`",
                    _escape(role_counts.get(role)),
                    _escape(role_descriptions.get(role, "")),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Families",
            "",
            "| Source family | Count | Meaning |",
            "| --- | ---: | --- |",
        ]
    )
    source_counts = _mapping(summary.get("source_family_counts"))
    source_descriptions = _mapping(report.get("source_family_descriptions"))
    for source in sorted(source_counts):
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape(source),
                    _escape(source_counts.get(source)),
                    _escape(source_descriptions.get(source, "")),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Signals",
            "",
            "| Signal | Source family | Kind | Roles | Latest coverage | Description |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    signals = sorted(
        (_mapping(row) for row in _sequence(report.get("signals"))),
        key=lambda row: (str(row.get("source_family") or ""), str(row.get("name") or "")),
    )
    for row in signals:
        coverage = _coverage_text(row)
        roles = ", ".join(f"`{_escape(role)}`" for role in _sequence(row.get("roles")))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape(row.get('name'))}`",
                    _escape(row.get("source_family")),
                    f"`{_escape(row.get('signal_kind'))}`",
                    roles,
                    coverage,
                    _escape(row.get("description")),
                )
            )
            + " |"
        )
    supporting = sorted(
        (_mapping(row) for row in _sequence(report.get("supporting_signals"))),
        key=lambda row: (str(row.get("source_family") or ""), str(row.get("name") or "")),
    )
    if supporting:
        lines.extend(
            [
                "",
                "## Supporting Source And Sweep Signals",
                "",
                "These are not all active component columns, but they are available raw metadata, "
                "derived gates, or sweep controls that can be promoted into future model shapes.",
                "",
                "| Signal | Source family | Kind | Model surface | Roles | Description |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in supporting:
            roles = ", ".join(f"`{_escape(role)}`" for role in _sequence(row.get("roles")))
            lines.append(
                "| "
                + " | ".join(
                    (
                        f"`{_escape(row.get('name'))}`",
                        _escape(row.get("source_family")),
                        f"`{_escape(row.get('signal_kind'))}`",
                        f"`{_escape(row.get('model_surface'))}`",
                        roles,
                        _escape(row.get("description")),
                    )
                )
                + " |"
            )
    lines.append("")
    return "\n".join(lines)


def _coverage_text(row: Mapping[str, object]) -> str:
    count = int(row.get("coverage_count") or 0)
    rate = row.get("coverage_rate")
    if rate is None:
        return str(count)
    return f"{count} ({float(rate) * 100:.1f}%)"


def _humanize(value: str) -> str:
    return value.replace("_", " ")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return value
    return ()


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
