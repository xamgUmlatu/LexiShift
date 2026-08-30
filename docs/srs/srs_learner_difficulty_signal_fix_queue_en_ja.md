# en-ja Learner-Difficulty Signal Fix Queue

Status: active review queue; second semantic cleanup pass implemented

This document separates endpoint-audit concerns into work items. The goal is to
decide which signals are actually encoded incorrectly, which are correctly
encoded but badly named, and which are simply dormant or too sparse to rely on
yet.

## Implementation Update

Implemented in the first cleanup pass:

- `jmdict_news_priority_risk` remains as a compatibility alias, but
  `news_or_policy_topic_risk` no longer uses JMDict `news` priority tags.
- Raw JMnedict/POS/candidate entity evidence is now exposed separately from gated
  entity-suppression risk.
- `jmdict_non_vocab_risk` now points at a gated non-ladder risk, while the old
  raw class score is exposed as `jmdict_non_vocab_raw_class_score`.
- BCCWJ rank/domain spread is exposed as variability evidence and no longer feeds
  `jmdict_register_domain_risk` directly.
- The palette generator now describes compatibility aliases and cleaned signal
  names explicitly.

Coverage note: new columns will show `0` latest coverage in the palette until a
new signal sweep/component matrix is generated from the updated code.

Implemented in the second cleanup pass:

- Raw JMDict/JMnedict/POS/source facts now have clearer canonical aliases such
  as `jmdict_marked_usage_flag`, `jmdict_field_marked_flag`,
  `jmdict_abbreviation_flag`, `jmnedict_person_name_overlap`, and
  `wtype_proper_flag`. Legacy `*_risk` names remain as compatibility aliases.
- Dictionary complexity aggregates now have clearer score aliases, including
  `jmdict_ambiguity_score`, `jmdict_reading_complexity_score`,
  `common_jmdict_ambiguity_score`, `common_register_domain_score`,
  `common_kango_complexity_score`, `kanjidic_nanori_reading_count_score`, and
  `kanjidic_variant_type_count_score`.
- Cross-source knownness/coverage companions are exposed for major sparse
  families: frequency, JMDict priority/lexical, JMnedict, JLPT vocabulary,
  lesson vocabulary, KANJIDIC2, KanjiVG, acronym, TUBELEX, BCCWJ domain rank,
  and cross-family source coverage.
- The sidecar family/meta/tree search defaults now prefer the canonical
  `*_flag`, `*_score`, and `*_known` names instead of the misleading raw
  `*_risk` compatibility aliases.
- The generated palette marks compatibility aliases as `source_flag_compat`,
  `overlap_compat`, or `score_compat`, and gives knownness signals an explicit
  `evidence_quality` role.

Coverage note: the regenerated palette now lists `282` component names from
code. Many new aliases show `0` latest coverage because the current coverage
artifact predates this cleanup; that is expected until the next intentional
component-matrix regeneration.

## Validation Update

Validated with the sidecar sweep/audit prefix `semantic_fix_validation_s010`.
This validation predates the second-pass alias/knownness additions above. The
current palette intentionally has more code-exposed component names than that
validated component matrix, so a new reconciliation check should wait until the
next intentional matrix regeneration.

Artifacts:

- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_trace_latest.json`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_calibration_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_component_matrix_latest.npz`
- `docs/test_outputs/srs_learner_difficulty_signal_endpoint_audit_en_ja_semantic_fix_validation_s010_latest.{json,md}`
- `docs/test_outputs/srs_learner_difficulty_holdout_eval_en_ja_semantic_fix_validation_s010_latest.{json,md}`

What changed as intended:

- Palette/matrix reconciliation is now clean: `227` palette signals and `227`
  component-matrix columns, with no palette signals missing from the refreshed
  matrix.
- `jmdict_news_priority_commonness` and compatibility
  `jmdict_news_priority_risk` still hit core common words, but they are now
  classified as native-exposure/source flags and no longer create
  `news_or_policy_topic_risk`.
- `news_or_policy_topic_risk` coverage dropped to actual field/domain evidence
  (`7,556` rows, `10.2451%` matrix coverage), instead of mostly mirroring JMDict
  `news` priority commonness.
- Raw entity/name overlap still hits common words, as expected, but gated
  `named_entity_risk` / `ordinary_ladder_entity_suppression_risk` no longer has
  core ordinary vocabulary at the high endpoint. Its high endpoint is now
  dominated by deprioritized entity rows such as era/country/region names.
- Raw `jmdict_non_vocab_raw_class_score` still hits common verbs/forms, as
  expected for the legacy class score, but gated `jmdict_non_ladder_entry_risk`
  no longer does.
- `bccwj_domain_profile_variability` still has broad high endpoints, as expected
  for variability evidence, but no longer feeds `jmdict_register_domain_risk`
  directly.

What did not improve:

- The same local-grid calibration-best variant remains top with the same score:
  balanced `0.922986`, MAE `0.107987`, pairwise `0.899806`.
- Holdout still does not favor that calibration-best trace. The primary trace
  candidate scores holdout balanced `0.699736`, while the best holdout candidate
  remains the older family/meta rare-wago-tail candidate at holdout balanced
  `0.823692`.
- Remaining high endpoint concerns are now mostly post-cleanup modeling choices:
  whether to use raw flags directly, how to gate sparse acronym signals, how to
  use count/ambiguity scores, and what fill policy to use when knownness is 0.

## Classification

- `encoded_fix`: the current numeric component does not mean what its model-facing
  name claims, or a composite combines valid inputs into an invalid learner-priority
  signal.
- `rename_or_metadata`: the value is probably source-faithful, but the current
  name/kind makes it too easy to misuse as direct difficulty.
- `activation_or_coverage`: the signal is not wrong, but is absent from the latest
  component matrix, has low variation, or needs a source/coverage decision before
  modeling.
- `source_spot_check`: the endpoint audit found suspicious behavior, but the next
  step is checking raw source evidence before changing parser code.

## Work Queue

| Order | Signal family | Classification | Current problem | Proposed fix | Verification |
| ---: | --- | --- | --- | --- | --- |
| 1 | `jmdict_news_priority_risk`, `news_or_policy_topic_risk`, `news_or_policy_frequency_risk`, `news_named_entity_risk`, `news_named_frequency_risk`, `news_abbreviation_entity_risk` | `encoded_fix` | JMDict `news` priority tags are being treated as topic/policy risk. The endpoint includes core common words such as `居る`, `有る`, `事`, `言う`, and `成る`, which is expected for a priority/commonness tag and wrong for a topic-risk signal. | Rename the raw priority tag to something like `jmdict_news_priority_tag` or `jmdict_news_priority_commonness`. Rebuild `news_or_policy_topic_risk` from actual field/domain evidence only, such as business/economics/law/politics fields, and do not let priority tags supply topic risk. | Endpoint check should show `jmdict_news_priority_*` still hits common words, while `news_or_policy_topic_risk` no longer mostly mirrors common frequency words. Sweep candidate formulas should not treat the priority tag as a positive difficulty/risk signal. |
| 2 | `jmnedict_name_risk`, `jmnedict_person_name_risk`, `jmnedict_place_name_risk`, `jmnedict_org_product_name_risk`, `jmnedict_creative_or_special_name_risk`, `named_entity_risk`, `proper_place_entity_risk`, `proper_country_entity_risk`, `proper_org_entity_risk`, `geopolitical_entity_risk`, `named_entity_frequency_risk`, `geopolitical_frequency_risk`, `candidate_deprioritized_named_entity_risk`, `candidate_deprioritized_named_frequency_risk`, `lesson_name_contamination_risk`, `lesson_name_contamination_frequency_risk` | mixed: raw `rename_or_metadata`, composite `encoded_fix` | JMnedict overlap is real evidence, but the composite promotes overlap into full entity risk without enough ordinary-vocabulary protection. Endpoint examples include `事`, `様`, `物`, `日本`, `人`, `成る`, and `中` at the high end. | Split raw overlap from ladder-admission risk. Keep raw signals as `jmnedict_*_overlap`. Create a separate gated risk such as `ordinary_ladder_entity_suppression_risk` that requires entity evidence plus weak ordinary-vocab evidence, tail frequency, deprioritized candidate state, or a true proper/acronym class. | Endpoint check should allow raw overlaps on common rows, but the gated entity-suppression component should not put core ordinary vocabulary at 1.0. Holdout/calibration review should compare the gated component against the current broad composite. |
| 3 | `jmdict_non_vocab_risk` and source field `non_vocab_signal_score` | `encoded_fix` plus `source_spot_check` | The name says non-vocabulary/non-ladder, but the score currently bundles particles/auxiliaries, numeric, affix/counter, function/discourse words, proper nouns, and marked usage. That catches many normal presentation-order items, including common verbs/forms at the endpoint. | Replace the single score with narrower components: `jmdict_function_word_class`, `jmdict_affix_counter_class`, `jmdict_numeric_class`, `jmdict_proper_noun_overlap`, `jmdict_marked_usage_flag`, and, only if source-backed, `jmdict_non_ladder_entry_risk`. The old model-facing name should not survive unless it is narrowed to true non-ladder entries. | Raw-source spot check the high-end examples. Then endpoint check each split signal separately and confirm true non-ladder risk no longer fires on ordinary core vocabulary. |
| 4 | `proper_noun_pos_risk`, `proper_place_pos_risk`, `proper_country_pos_risk`, `problem_class_proper_risk`, `wtype_proper_risk` | raw `rename_or_metadata`, downstream `encoded_fix` if used as exclusion | These are often source-faithful POS or classifier overlaps, but names imply difficulty/admission risk. Common geopolitical vocabulary such as `日本`, `中国`, and `米国` can legitimately be proper/place/country items while still belonging early or mid ladder. | Rename raw signals to `*_overlap` or `*_pos_flag`. Use them only inside gated entity/admission composites that respect frequency, learner sources, and candidate state. | Endpoint check should preserve raw flags on country/place words, while any suppressive risk should avoid demoting common countries solely because they are proper nouns. |
| 5 | `bccwj_domain_rank_spread`, `bccwj_rank_spread`, `bccwj_pmw_spread`, `bccwj_fixed_variable_rank_delta`, `bccwj_domain_rank_coverage`, `bccwj_domain_profile_risk`, `jmdict_register_domain_risk`, `common_register_domain_risk`, `common_kango_register_domain_risk` | mostly `rename_or_metadata`; composite use may need `encoded_fix` | Rank spread and domain coverage are distribution-shape evidence, not direct topic difficulty. `bccwj_domain_rank_spread` is high for most rows and includes core words. The current `jmdict_register_domain_risk` can inherit a broad domain-profile value. | Rename spread signals as variability/dispersion evidence. Keep coverage as evidence confidence. If a topic/register risk is needed, require actual field/register/domain evidence plus a concentration or tail condition, not broad spread alone. | Endpoint check should show spread remains broad but no longer acts as direct topic risk. Any new concentration/tail composite should have a smaller, interpretable high endpoint. |
| 6 | `frequency`, `frequency_power2`, `frequency_power3`, `frequency_sqrt`, `frequency_tail*`, `frequency_unranked_*`, `tubelex_frequency`, `tubelex_*_difficulty`, `tubelex_spoken_rescue`, `tubelex_written_only_risk`, `tubelex_bccwj_*` | mostly `rename_or_metadata` and `activation_or_coverage` | The values are frequency-derived difficulty proxies, not literal human difficulty percentiles. The active BCCWJ frequency scale is compressed high in the matrix. Tubelex adds a useful second perspective but is not in every current matrix. | Rename model-facing descriptions toward `bccwj_rank_difficulty_proxy` and `tubelex_spoken_frequency_difficulty`. Keep transforms available, but make the proxy/scale explicit in palette docs and sweep labels. Decide which Tubelex components belong in the active matrix. | Endpoint check should document scale shape. Sweeps should compare BCCWJ-only, Tubelex-only, min/mean/max/agreement, spoken-rescue, and written-only variants with holdout validation. |
| 7 | `jlpt_vocab_difficulty`, `jlpt_vocab_beginner_core`, `jlpt_vocab_levels_raw`, `jlpt_vocab_easiest_level`, `jlpt_vocab_hardest_level`, `jlpt_vocab_is_n5`...`jlpt_vocab_is_n1`, `jlpt_vocab_n5_curve_value`...`jlpt_vocab_n1_curve_value` | mostly `rename_or_metadata`; optional `activation_or_coverage` | The base scalar mapping is coherent, but active components compress levels into one or two scalars while supporting one-hot/level metadata exists outside the latest active matrix. | Keep the scalar, but expose level gates in active experiments when testing shape. Label `beginner_core` as an ease/anchor signal, not difficulty. Keep curve remapping visible in artifacts because the final candidate may use transformed values. | Endpoint check by JLPT level should remain monotone. Formula artifacts should state whether they used base scalar, remapped curve, or one-hot levels. |
| 8 | `script_complexity`, `kanji_grade`, `kanji_frequency_rank`, `old_jlpt_kanji`, `stroke_count`, `kanjivg_visual_complexity`, `kanji_curriculum_burden`, `kanji_shape_burden`, `max_kanji_shape_burden`, `kanji_curriculum_missing_risk`, `kanji_burden`, `max_kanji_burden`, `written_form_burden`, `max_written_form_burden`, `wago_*`, `kango_*`, `rare_wago_*`, `written_wago_tail_risk`, `non_standard_reading_risk`, `rare_non_standard_reading_risk` | mostly `rename_or_metadata` | These are orthographic, curriculum, script, or word-origin burden signals. They are useful as tail/tiebreaker features, but are not primary presentation priority by themselves. | Keep them, but label them as burden/tail features. Avoid formulas where kanji burden can override strong learner/frequency evidence in the early ladder unless explicitly gated. | Band samples should show burden mostly changing order within comparable frequency/source regions, not pushing useful common words too late. |
| 9 | `jmdict_register_marked_risk`, `jmdict_dialect_risk`, `jmdict_abbreviation_risk`, `jmdict_organization_misc_risk`, `jmdict_foreign_priority_risk`, `jmdict_field_marked_risk`, `jmdict_loanword_source_risk`, `jmdict_sinitic_source`, `jmdict_source_text_present`, `jmdict_source_type_marked`, `jmdict_wasei_source`, `jmdict_kanji_form_marked_risk`, `jmdict_reading_form_marked_risk`, `jmdict_search_only_form_risk`, `jmdict_sense_restricted_risk`, `jmdict_reading_restricted_risk`, `jmdict_no_kanji_reading_risk`, `jmdict_polysemy_risk`, `jmdict_sense_info_risk`, `jmdict_cross_reference_risk` | mostly `rename_or_metadata`; some `source_spot_check` | These generally appear to be source-faithful flags, but many names say `risk` even when the source fact is only "has at least one marked/abbreviation/dialect/source/form/sense property." Common words can legitimately have such marked senses or alternate forms. | Rename toward `*_flag`, `*_overlap`, or `*_complexity_flag` unless the signal has been gated into a true priority-risk component. Keep separate raw source flags and modeled risk composites. | Spot-check flagged common examples, then ensure raw flags can fire on common rows while risk composites require tail/frequency/source conditions. |
| 10 | `acronym_surface_confidence`, `acronym_mixed_code_confidence`, `acronym_spellout_reading`, `acronym_identity_gloss`, `acronym_expanded_gloss`, `acronym_japanese_specific_usage`, `acronym_domain_concentration`, `acronym_proper_name_risk`, `acronym_real_usage_confidence`, `acronym_default_suppress_risk`, `acronym_topic_only_risk`, `acronym_shared_exact_risk`, `acronym_japanese_specific_gate`, `proper_acronym_entity_risk` | mostly `activation_or_coverage`; some `rename_or_metadata` | Coverage is low and several latest-matrix columns have no observed variation. Confidence/gate fields are not direct difficulty. | Keep as side evidence for acronym-specific admission/topic logic. Do not let zero-variation fields participate in broad sweeps until coverage improves or a targeted acronym set is used. | Run endpoint/coverage checks on an acronym-focused sample, not only the global matrix. |
| 11 | `lesson_vocab_difficulty`, `lesson_vocab_beginner_core`, `lesson_name_contamination_*` | `activation_or_coverage`; contamination composites depend on entity fix | Lesson evidence is valuable pedagogical ordering evidence but sparse. The name-contamination composites inherit the broad entity-risk problem. | Keep lesson difficulty/beginner-core as strong anchors where present. Rebuild name-contamination only after entity gating is fixed. | Coverage report should distinguish sparse-but-strong anchors from globally weak features. |
| 12 | Count and ambiguity signals: `jmdict_entry_count`, `jmdict_pos_count`, `jmdict_field_count`, `jmdict_kanji_form_count`, `jmdict_reading_form_count`, `jmdict_form_count`, `jmdict_gloss_count`, `jmdict_sense_count`, `jmdict_restriction_count`, `jmdict_*_ambiguity`, `kanjidic_meaning_count`, `kanjidic_radical_value_count` | mostly `rename_or_metadata` and `activation_or_coverage` | Counts measure dictionary-entry complexity or ambiguity, not direct learner difficulty. Several are dormant in the latest matrix. | Keep them as ambiguity/complexity evidence, not standalone risk. Decide whether dormant count-derived components should re-enter active sweeps after the larger semantic fixes. | Endpoint samples should show whether high counts represent useful ambiguity or just common polysemy. |
| 13 | Cross-cutting missingness and knownness | `encoded_fix` for sweep semantics | Some binaries correctly return `None` when the evidence source is absent, but the broader matrix/formula layer can still make absence behave like a true zero after normalization or filling. That can reward "not observed" as "confirmed absent." | Add or expose knownness/coverage companions for sparse sources and make fill policy explicit per component family. Avoid comparing sparse confidence signals to full-coverage BCCWJ/JMDict features without a missingness strategy. | Component matrix audit should report coverage, fill behavior, and endpoint examples after fill. Holdout sweeps should compare missing-as-zero versus knownness-aware variants. |
| 14 | Palette-only / not-latest-matrix signals, including `frequency_ease`, `tubelex_*`, `bccwj_domain_profile_risk`, `common_jmdict_ambiguity_risk`, `common_reading_complexity_risk`, `common_restriction_complexity_risk`, `common_register_domain_risk`, `common_kango_*`, `jmdict_*_ambiguity`, and related count components | `activation_or_coverage` | These are code-exposed or supporting signals, but not all appear in the current main component matrix. That is not a correctness failure, but it makes the palette look broader than the latest active sweep. | Decide per family: activate in the next controlled sweep, leave as supporting-only, or remove from the palette's active-looking section. | Palette and matrix counts should reconcile cleanly, with active, supporting, and dormant surfaces clearly separated. |

## Recommended Order Of Fixes

1. Fix `news_or_policy_topic_risk` first because it is the clearest derived-signal
   bug: a commonness/priority tag is being used as topic risk.
2. Split raw entity overlap from gated entity/admission risk. This is the biggest
   practical admission problem and affects many composite signals.
3. Split or rename `jmdict_non_vocab_risk`. This is likely a semantic encoding
   problem, but it needs raw-source spot checks before parser surgery.
4. Reframe BCCWJ spread/domain signals as variability evidence, not topic risk.
5. Sweep only after these semantic fixes, so model competition is not optimizing
   over mislabeled dimensions.

## Current Non-Fixes

- Do not change JLPT scalar mappings yet. They look internally coherent; the open
  question is shape/activation, not source correctness.
- Do not remove kanji or written-form burden signals. They are useful, but should
  be treated as burden/tail/tiebreaker evidence.
- Do not treat sparse lesson/acronym coverage as a failure. They are high-value
  anchors when present, but poor global standalone dimensions.
- Do not treat raw proper-name, register, dialect, abbreviation, or field flags as
  parser bugs solely because they hit common words. Common words can have marked
  senses, alternate forms, or name overlaps.
