#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from rulegen_probe_words_support import (  # noqa: E402
    build_ja_word_packages,
    build_pair_resources_payload,
    collect_rows_for_target,
    load_store,
    parse_csv_words,
    parse_reading_overrides,
    print_resource_identity_block,
    print_target_block,
    resolve_required_file,
)
from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_reverse_translation_dictionary_path,
)
from lexishift_core.helper.pair_resources import resolve_pair_resources  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.rulegen.generation import RuleGenerationResult  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleScoreWeights,
    RuleScoringConfig,
)
from lexishift_core.rulegen.pairs.en_de import (  # noqa: E402
    EnDeKaikkiPolicyConfig,
    EnDeRulegenConfig,
    generate_en_de_results,
)
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsKaikkiPolicyConfig,
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.en_ja import (  # noqa: E402
    EnJaRulegenConfig,
    generate_en_ja_results,
)
from lexishift_core.rulegen.ranking import (  # noqa: E402
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Probe rulegen outputs for fixed words and print uncapped vs capped ranking views. "
            "Useful for tracking scoring behavior changes over time."
        )
    )
    parser.add_argument(
        "--spanish-targets",
        default="hora,trabajo",
        help="Comma-separated Spanish target lemmas for en-es probe.",
    )
    parser.add_argument(
        "--german-targets",
        default="",
        help="Comma-separated German target lemmas for en-de probe.",
    )
    parser.add_argument(
        "--japanese-targets",
        default="様,時",
        help="Comma-separated Japanese target lemmas for en-ja probe.",
    )
    parser.add_argument(
        "--ja-readings",
        default="様=よう,時=とき",
        help="Comma-separated lemma=reading overrides used when SRS store lacks word_package.",
    )
    parser.add_argument(
        "--max-definitions",
        type=int,
        default=3,
        help="Top-K definitions per target in capped run.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.0,
        help="Minimum confidence threshold for both runs.",
    )
    parser.add_argument(
        "--max-rules-per-target",
        type=int,
        help="Optional final cap on emitted rules per target in capped run.",
    )
    parser.add_argument(
        "--no-variants",
        action="store_true",
        help="Disable variant expansion in probes.",
    )
    parser.add_argument(
        "--disable-pos-scoring",
        action="store_true",
        help="Disable POS congruence scoring in both runs.",
    )
    parser.add_argument(
        "--pos-exact-match-bonus",
        type=float,
        default=1.0,
        help="POS exact-match bonus used in both runs.",
    )
    parser.add_argument(
        "--pos-compatible-match-bonus",
        type=float,
        default=0.5,
        help="POS compatibility-class bonus used in both runs.",
    )
    parser.add_argument(
        "--score-weight-pos-match",
        type=float,
        default=0.1,
        help="Weight of POS signal in confidence scoring.",
    )
    parser.add_argument(
        "--profile-id",
        default="default",
        help="Profile ID to read SRS word packages from (for ja targets).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override LexiShift data root (default: platform data dir or LEXISHIFT_DATA_DIR).",
    )
    parser.add_argument(
        "--translation-dict-en-es",
        dest="translation_dict_en_es",
        type=Path,
        help=(
            "Optional manual translation-dictionary override for en-es probe. "
            "Installed language packs are used by default."
        ),
    )
    parser.add_argument(
        "--translation-dict-en-de",
        dest="translation_dict_en_de",
        type=Path,
        help=(
            "Optional manual translation-dictionary override for en-de probe. "
            "Installed language packs are used by default."
        ),
    )
    parser.add_argument(
        "--translation-dict-en-de-reverse",
        dest="translation_dict_en_de_reverse",
        type=Path,
        help=(
            "Optional manual reverse translation-dictionary override used for en-de "
            "reverse-check metadata. Installed language packs are used by default."
        ),
    )
    parser.add_argument(
        "--translation-dict-es-en-reverse",
        dest="translation_dict_es_en_reverse",
        type=Path,
        help=(
            "Optional manual reverse translation-dictionary override used for en-es "
            "reverse-check metadata. Installed language packs are used by default."
        ),
    )
    parser.add_argument(
        "--jmdict",
        type=Path,
        help="Optional manual JMDict override for en-ja probe. Installed packs are used by default.",
    )
    parser.add_argument(
        "--reverse-check-enabled",
        action="store_true",
        help="Enable reverse-check ranking adjustments for the en-es / en-de probe.",
    )
    parser.add_argument(
        "--reverse-check-match-bonus",
        type=float,
        default=0.2,
        help="Score bonus when reverse-check finds an exact match.",
    )
    parser.add_argument(
        "--reverse-check-near-bonus",
        type=float,
        default=0.1,
        help="Score bonus when reverse-check finds a near match within the rank window.",
    )
    parser.add_argument(
        "--reverse-check-near-rank-max",
        type=int,
        default=2,
        help="Maximum reverse rank treated as a near match.",
    )
    parser.add_argument(
        "--reverse-check-far-hit-penalty",
        type=float,
        default=0.0,
        help="Score penalty applied when reverse-check hits beyond the near-rank window.",
    )
    parser.add_argument(
        "--reverse-check-miss-penalty",
        type=float,
        default=0.2,
        help="Score penalty when reverse-check is supported but misses.",
    )
    parser.add_argument(
        "--reverse-check-exact-hit-ambiguity-threshold",
        type=int,
        default=0,
        help="Reverse candidate-count threshold above which exact hits start getting ambiguity penalty.",
    )
    parser.add_argument(
        "--reverse-check-exact-hit-ambiguity-penalty",
        type=float,
        default=0.0,
        help="Maximum score penalty applied to exact reverse hits with high ambiguity.",
    )
    parser.add_argument(
        "--reverse-check-exact-hit-specificity-bonus",
        type=float,
        default=0.0,
        help="Additional bonus applied to exact reverse hits, scaled down by reverse fanout.",
    )
    parser.add_argument(
        "--kaikki-policy-late-sense-penalty",
        type=float,
        default=0.0,
        help="Additive semantic demotion for late Kaikki senses when clean earlier competition exists.",
    )
    parser.add_argument(
        "--kaikki-policy-live-demotion",
        action="store_true",
        help="Enable live Kaikki risk-family demotion when Kaikki/Wiktionary metadata is present.",
    )
    parser.add_argument(
        "--kaikki-policy-register-demotion",
        action="store_true",
        help="Enable Kaikki register/region demotion when usage metadata is present.",
    )
    parser.add_argument(
        "--enable-exact-gloss-demotion",
        action="store_true",
        help="Enable exact phrase-level gloss demotion overrides in probe runs.",
    )
    parser.add_argument(
        "--enable-source-frequency-prior",
        action="store_true",
        help="Enable English source-frequency prior for en-de probe runs.",
    )
    parser.add_argument(
        "--cleaner-later-competition-penalty",
        type=float,
        default=0.0,
        help="Semantic demotion applied to earlier en-de candidates when a cleaner later competitor exists.",
    )
    parser.add_argument(
        "--source-frequency-db-en-de",
        type=Path,
        help=(
            "Optional manual English source-frequency SQLite override for en-de probe runs. "
            "Installed frequency packs are used by default when source-frequency prior is enabled."
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to save full probe output as JSON.",
    )
    args = parser.parse_args()

    include_variants = not args.no_variants
    spanish_targets = parse_csv_words(args.spanish_targets)
    german_targets = parse_csv_words(args.german_targets)
    japanese_targets = parse_csv_words(args.japanese_targets)
    reading_overrides = parse_reading_overrides(args.ja_readings)
    max_definitions = max(1, int(args.max_definitions))
    max_rules_per_target = (
        max(1, int(args.max_rules_per_target)) if args.max_rules_per_target is not None else None
    )
    scoring = RuleScoringConfig(
        weights=RuleScoreWeights(pos_match=float(args.score_weight_pos_match)),
        pos_match=PosMatchScoringConfig(
            enabled=not args.disable_pos_scoring,
            exact_match_bonus=float(args.pos_exact_match_bonus),
            compatible_match_bonus=float(args.pos_compatible_match_bonus),
        ),
    )
    reverse_check = ReverseCheckScoringConfig(
        enabled=bool(args.reverse_check_enabled),
        match_bonus=max(0.0, float(args.reverse_check_match_bonus)),
        near_bonus=max(0.0, float(args.reverse_check_near_bonus)),
        near_rank_max=max(0, int(args.reverse_check_near_rank_max)),
        far_hit_penalty=max(0.0, float(args.reverse_check_far_hit_penalty)),
        miss_penalty=max(0.0, float(args.reverse_check_miss_penalty)),
        exact_hit_ambiguity_threshold=max(
            0,
            int(args.reverse_check_exact_hit_ambiguity_threshold),
        ),
        exact_hit_ambiguity_penalty=max(
            0.0,
            float(args.reverse_check_exact_hit_ambiguity_penalty),
        ),
        exact_hit_specificity_bonus=max(
            0.0,
            float(args.reverse_check_exact_hit_specificity_bonus),
        ),
    )

    paths = build_helper_paths(args.data_root)
    store_path = paths.srs_store_path_for(args.profile_id)
    store = load_store(store_path)

    resolved_translation_dict_en_es: Optional[Path] = None
    resolved_reverse_translation_dict_en_es: Optional[Path] = None
    resolved_translation_dict_en_de: Optional[Path] = None
    resolved_reverse_translation_dict_en_de: Optional[Path] = None
    resolved_source_frequency_db_en_de: Optional[Path] = None
    if spanish_targets:
        _resolved_jmdict, _resolved_translation_dict_en_es, _ = resolve_pair_resources(
            paths,
            pair="en-es",
            jmdict_path=args.jmdict,
            translation_dict_path=args.translation_dict_en_es,
            set_source_db=None,
        )
        resolved_translation_dict_en_es = resolve_required_file(
            "Translation dictionary ES->EN",
            _resolved_translation_dict_en_es,
        )
        resolved_reverse_translation_dict_en_es = resolve_required_file(
            "Reverse translation dictionary EN->ES",
            args.translation_dict_es_en_reverse
            or default_reverse_translation_dictionary_path(
                "en-es",
                language_packs_dir=paths.language_packs_dir,
            ),
        )
    if german_targets:
        _resolved_jmdict, _resolved_translation_dict_en_de, _ = resolve_pair_resources(
            paths,
            pair="en-de",
            jmdict_path=args.jmdict,
            translation_dict_path=args.translation_dict_en_de,
            set_source_db=None,
        )
        resolved_translation_dict_en_de = resolve_required_file(
            "Translation dictionary DE->EN",
            _resolved_translation_dict_en_de,
        )
        if args.reverse_check_enabled:
            resolved_reverse_translation_dict_en_de = resolve_required_file(
                "Reverse translation dictionary EN->DE",
                args.translation_dict_en_de_reverse
                or default_reverse_translation_dictionary_path(
                    "en-de",
                    language_packs_dir=paths.language_packs_dir,
                ),
            )
        if args.enable_source_frequency_prior:
            resolved_source_frequency_db_en_de = resolve_required_file(
                "Source frequency DB EN",
                args.source_frequency_db_en_de
                or default_frequency_db_path(
                    "en-en", frequency_packs_dir=paths.frequency_packs_dir
                ),
            )

    resolved_jmdict: Optional[Path] = None
    if japanese_targets:
        _resolved_jmdict, _unused_translation_dict, _ = resolve_pair_resources(
            paths,
            pair="en-ja",
            jmdict_path=args.jmdict,
            translation_dict_path=args.translation_dict_en_es,
            set_source_db=None,
        )
        resolved_jmdict = resolve_required_file("JMDict", _resolved_jmdict)

    ja_word_packages, missing_ja_targets, notes = build_ja_word_packages(
        targets=japanese_targets,
        store=store,
        reading_overrides=reading_overrides,
    )
    resolved_japanese_targets = [lemma for lemma in japanese_targets if lemma in ja_word_packages]

    es_ranking = DictionaryEntryOrderRankingMechanism(reverse_check=reverse_check)
    de_ranking = DictionaryEntryOrderRankingMechanism(reverse_check=reverse_check)
    ja_ranking = DictionaryEntryOrderRankingMechanism()
    resource_payload = {
        "en-es": build_pair_resources_payload(
            pair="en-es",
            jmdict_path=None,
            translation_dict_path=resolved_translation_dict_en_es,
            reverse_translation_dict_path=resolved_reverse_translation_dict_en_es,
        ),
        "en-de": build_pair_resources_payload(
            pair="en-de",
            jmdict_path=None,
            translation_dict_path=resolved_translation_dict_en_de,
            reverse_translation_dict_path=resolved_reverse_translation_dict_en_de,
            source_frequency_db_path=resolved_source_frequency_db_en_de,
        ),
        "en-ja": build_pair_resources_payload(
            pair="en-ja",
            jmdict_path=resolved_jmdict,
            translation_dict_path=None,
            reverse_translation_dict_path=None,
        ),
    }

    # Uncapped baseline run.
    es_uncapped: list[RuleGenerationResult] = []
    if spanish_targets:
        es_uncapped = generate_en_es_results(
            spanish_targets,
            config=EnEsRulegenConfig(
                freedict_es_en_path=resolve_required_file(
                    "Translation dictionary ES->EN", resolved_translation_dict_en_es
                ),
                reverse_freedict_en_es_path=resolve_required_file(
                    "Reverse translation dictionary EN->ES",
                    resolved_reverse_translation_dict_en_es,
                ),
                reverse_check=reverse_check,
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                max_definitions_per_target=None,
                max_rules_per_target=None,
                scoring=scoring,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
                kaikki_policy=EnEsKaikkiPolicyConfig(
                    late_sense_clean_earlier_competition_penalty=max(
                        0.0,
                        float(args.kaikki_policy_late_sense_penalty),
                    )
                ),
            ),
        )
    de_uncapped: list[RuleGenerationResult] = []
    if german_targets:
        de_uncapped = generate_en_de_results(
            german_targets,
            config=EnDeRulegenConfig(
                freedict_de_en_path=resolve_required_file(
                    "Translation dictionary DE->EN",
                    resolved_translation_dict_en_de,
                ),
                reverse_freedict_en_de_path=resolved_reverse_translation_dict_en_de,
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                max_definitions_per_target=None,
                max_rules_per_target=None,
                scoring=scoring,
                reverse_check=reverse_check,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
                enable_source_frequency_prior=bool(args.enable_source_frequency_prior),
                source_frequency_db_path=resolved_source_frequency_db_en_de,
                cleaner_later_competition_penalty=max(
                    0.0,
                    float(args.cleaner_later_competition_penalty),
                ),
                kaikki_policy=EnDeKaikkiPolicyConfig(
                    enable_live_demotion=bool(args.kaikki_policy_live_demotion),
                    enable_register_demotion=bool(args.kaikki_policy_register_demotion),
                    late_sense_clean_earlier_competition_penalty=max(
                        0.0,
                        float(args.kaikki_policy_late_sense_penalty),
                    ),
                ),
            ),
        )
    ja_uncapped: list[RuleGenerationResult] = []
    if resolved_japanese_targets:
        ja_uncapped = generate_en_ja_results(
            resolved_japanese_targets,
            config=EnJaRulegenConfig(
                jmdict_path=resolve_required_file("JMDict", resolved_jmdict),
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                word_packages_by_target=ja_word_packages,
                max_definitions_per_target=None,
                max_rules_per_target=None,
                scoring=scoring,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
            ),
        )

    # Capped run (top-K definitions).
    es_capped: list[RuleGenerationResult] = []
    if spanish_targets:
        es_capped = generate_en_es_results(
            spanish_targets,
            config=EnEsRulegenConfig(
                freedict_es_en_path=resolve_required_file(
                    "Translation dictionary ES->EN", resolved_translation_dict_en_es
                ),
                reverse_freedict_en_es_path=resolve_required_file(
                    "Reverse translation dictionary EN->ES",
                    resolved_reverse_translation_dict_en_es,
                ),
                reverse_check=reverse_check,
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                max_definitions_per_target=max_definitions,
                max_rules_per_target=max_rules_per_target,
                scoring=scoring,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
                kaikki_policy=EnEsKaikkiPolicyConfig(
                    late_sense_clean_earlier_competition_penalty=max(
                        0.0,
                        float(args.kaikki_policy_late_sense_penalty),
                    )
                ),
            ),
        )
    de_capped: list[RuleGenerationResult] = []
    if german_targets:
        de_capped = generate_en_de_results(
            german_targets,
            config=EnDeRulegenConfig(
                freedict_de_en_path=resolve_required_file(
                    "Translation dictionary DE->EN",
                    resolved_translation_dict_en_de,
                ),
                reverse_freedict_en_de_path=resolved_reverse_translation_dict_en_de,
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                max_definitions_per_target=max_definitions,
                max_rules_per_target=max_rules_per_target,
                scoring=scoring,
                reverse_check=reverse_check,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
                enable_source_frequency_prior=bool(args.enable_source_frequency_prior),
                source_frequency_db_path=resolved_source_frequency_db_en_de,
                cleaner_later_competition_penalty=max(
                    0.0,
                    float(args.cleaner_later_competition_penalty),
                ),
                kaikki_policy=EnDeKaikkiPolicyConfig(
                    enable_live_demotion=bool(args.kaikki_policy_live_demotion),
                    enable_register_demotion=bool(args.kaikki_policy_register_demotion),
                    late_sense_clean_earlier_competition_penalty=max(
                        0.0,
                        float(args.kaikki_policy_late_sense_penalty),
                    ),
                ),
            ),
        )
    ja_capped: list[RuleGenerationResult] = []
    if resolved_japanese_targets:
        ja_capped = generate_en_ja_results(
            resolved_japanese_targets,
            config=EnJaRulegenConfig(
                jmdict_path=resolve_required_file("JMDict", resolved_jmdict),
                include_variants=include_variants,
                confidence_threshold=args.confidence_threshold,
                word_packages_by_target=ja_word_packages,
                max_definitions_per_target=max_definitions,
                max_rules_per_target=max_rules_per_target,
                scoring=scoring,
                enable_exact_gloss_demotions=bool(args.enable_exact_gloss_demotion),
            ),
        )

    print("Rulegen Probe")
    print(f"  data_root: {paths.data_root}")
    print(f"  profile_id: {args.profile_id}")
    print(f"  srs_store: {store_path}")
    print(f"  translation_dict_en_es: {resolved_translation_dict_en_es}")
    print(f"  translation_dict_es_en_reverse: {resolved_reverse_translation_dict_en_es}")
    print(f"  translation_dict_en_de: {resolved_translation_dict_en_de}")
    print(f"  translation_dict_en_de_reverse: {resolved_reverse_translation_dict_en_de}")
    print(f"  source_frequency_db_en_de: {resolved_source_frequency_db_en_de}")
    print(f"  jmdict: {resolved_jmdict}")
    print_resource_identity_block(resource_payload)
    print(
        f"  config: max_definitions={max_definitions}, "
        f"max_rules_per_target={max_rules_per_target}, "
        f"confidence_threshold={args.confidence_threshold}, include_variants={include_variants}, "
        f"pos_scoring_enabled={not args.disable_pos_scoring}, "
        f"pos_exact={args.pos_exact_match_bonus}, pos_compatible={args.pos_compatible_match_bonus}, "
        f"score_weight_pos_match={args.score_weight_pos_match}, "
        f"reverse_check_enabled={reverse_check.enabled}, "
        f"reverse_match={reverse_check.match_bonus}, "
        f"reverse_near={reverse_check.near_bonus}, "
        f"reverse_near_rank_max={reverse_check.near_rank_max}, "
        f"reverse_far_hit_penalty={reverse_check.far_hit_penalty}, "
        f"reverse_miss_penalty={reverse_check.miss_penalty}, "
        f"reverse_exact_hit_ambiguity_threshold={reverse_check.exact_hit_ambiguity_threshold}, "
        f"reverse_exact_hit_ambiguity_penalty={reverse_check.exact_hit_ambiguity_penalty}, "
        f"reverse_exact_hit_specificity_bonus={reverse_check.exact_hit_specificity_bonus}, "
        f"kaikki_policy_late_sense_penalty={max(0.0, float(args.kaikki_policy_late_sense_penalty))}, "
        f"kaikki_policy_register_demotion={bool(args.kaikki_policy_register_demotion)}, "
        f"kaikki_policy_live_demotion={bool(args.kaikki_policy_live_demotion)}, "
        f"enable_exact_gloss_demotion={bool(args.enable_exact_gloss_demotion)}, "
        f"enable_source_frequency_prior={bool(args.enable_source_frequency_prior)}, "
        f"cleaner_later_competition_penalty={max(0.0, float(args.cleaner_later_competition_penalty))}"
    )
    for note in notes:
        print(f"  note: {note}")
    for missing in missing_ja_targets:
        print(
            f"  warning: Missing word_package/reading for Japanese target '{missing}'. "
            "Add to SRS store or pass via --ja-readings."
        )

    output_payload: dict[str, object] = {
        "config": {
            "max_definitions": max_definitions,
            "max_rules_per_target": max_rules_per_target,
            "confidence_threshold": args.confidence_threshold,
            "include_variants": include_variants,
            "pos_scoring_enabled": (not args.disable_pos_scoring),
            "pos_exact_match_bonus": args.pos_exact_match_bonus,
            "pos_compatible_match_bonus": args.pos_compatible_match_bonus,
            "score_weight_pos_match": args.score_weight_pos_match,
            "enable_exact_gloss_demotion": bool(args.enable_exact_gloss_demotion),
            "enable_source_frequency_prior": bool(args.enable_source_frequency_prior),
            "cleaner_later_competition_penalty": max(
                0.0,
                float(args.cleaner_later_competition_penalty),
            ),
            "reverse_check": {
                "enabled": reverse_check.enabled,
                "match_bonus": reverse_check.match_bonus,
                "near_bonus": reverse_check.near_bonus,
                "near_rank_max": reverse_check.near_rank_max,
                "far_hit_penalty": reverse_check.far_hit_penalty,
                "miss_penalty": reverse_check.miss_penalty,
                "exact_hit_ambiguity_threshold": reverse_check.exact_hit_ambiguity_threshold,
                "exact_hit_ambiguity_penalty": reverse_check.exact_hit_ambiguity_penalty,
                "exact_hit_specificity_bonus": reverse_check.exact_hit_specificity_bonus,
            },
            "kaikki_policy_late_sense_penalty": max(
                0.0,
                float(args.kaikki_policy_late_sense_penalty),
            ),
            "kaikki_policy_register_demotion": bool(args.kaikki_policy_register_demotion),
            "kaikki_policy_live_demotion": bool(args.kaikki_policy_live_demotion),
        },
        "paths": {
            "data_root": str(paths.data_root),
            "profile_id": args.profile_id,
            "srs_store": str(store_path),
            "translation_dict_en_es": (
                str(resolved_translation_dict_en_es) if resolved_translation_dict_en_es else None
            ),
            "translation_dict_es_en_reverse": (
                str(resolved_reverse_translation_dict_en_es)
                if resolved_reverse_translation_dict_en_es
                else None
            ),
            "translation_dict_en_de": (
                str(resolved_translation_dict_en_de) if resolved_translation_dict_en_de else None
            ),
            "translation_dict_en_de_reverse": (
                str(resolved_reverse_translation_dict_en_de)
                if resolved_reverse_translation_dict_en_de
                else None
            ),
            "source_frequency_db_en_de": (
                str(resolved_source_frequency_db_en_de)
                if resolved_source_frequency_db_en_de
                else None
            ),
            "jmdict": str(resolved_jmdict) if resolved_jmdict else None,
        },
        "resources": resource_payload,
        "notes": notes,
        "warnings": [
            (
                f"Missing word_package/reading for Japanese target '{missing}'. "
                "Add to SRS store or pass via --ja-readings."
            )
            for missing in missing_ja_targets
        ],
        "pairs": {},
    }

    es_pair_payload: dict[str, object] = {}
    for target in spanish_targets:
        uncapped_rows = collect_rows_for_target(
            es_uncapped,
            target=target,
            mechanism=es_ranking,
        )
        capped_rows = collect_rows_for_target(
            es_capped,
            target=target,
            mechanism=es_ranking,
        )
        print_target_block(
            pair="en-es",
            target=target,
            uncapped_rows=uncapped_rows,
            capped_rows=capped_rows,
        )
        es_pair_payload[target] = {
            "uncapped": uncapped_rows,
            "capped": capped_rows,
        }
    output_payload["pairs"] = {"en-es": es_pair_payload}

    de_pair_payload: dict[str, object] = {}
    for target in german_targets:
        uncapped_rows = collect_rows_for_target(
            de_uncapped,
            target=target,
            mechanism=de_ranking,
        )
        capped_rows = collect_rows_for_target(
            de_capped,
            target=target,
            mechanism=de_ranking,
        )
        print_target_block(
            pair="en-de",
            target=target,
            uncapped_rows=uncapped_rows,
            capped_rows=capped_rows,
        )
        de_pair_payload[target] = {
            "uncapped": uncapped_rows,
            "capped": capped_rows,
        }
    output_payload["pairs"]["en-de"] = de_pair_payload

    ja_pair_payload: dict[str, object] = {}
    for target in japanese_targets:
        uncapped_rows = collect_rows_for_target(
            ja_uncapped,
            target=target,
            mechanism=ja_ranking,
        )
        capped_rows = collect_rows_for_target(
            ja_capped,
            target=target,
            mechanism=ja_ranking,
        )
        print_target_block(
            pair="en-ja",
            target=target,
            uncapped_rows=uncapped_rows,
            capped_rows=capped_rows,
        )
        ja_pair_payload[target] = {
            "uncapped": uncapped_rows,
            "capped": capped_rows,
        }
    output_payload["pairs"]["en-ja"] = ja_pair_payload

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON output written: {args.json_output}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "hint: the probe uses installed packs by default; pass explicit manual overrides "
            "with --jmdict, --translation-dict-en-es, --translation-dict-es-en-reverse, "
            "--translation-dict-en-de, --translation-dict-en-de-reverse, "
            "or ensure the needed packs are installed in the LexiShift data directory.",
            file=sys.stderr,
        )
        raise SystemExit(2)
