# en-ja Learner Difficulty Signal Palette

Status: generated model-design palette
Generated: `2026-06-18T23:06:29+00:00`

Purpose: enumerate every component signal currently exposed by the en-ja learner-difficulty sweep surface. Treat this as the palette for model-shape design: not every signal is a scalar difficulty signal, and several are better understood as admission, topic, burden, or calibration-shape cues.

## Inputs

- Source code: `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py`
- Coverage artifact: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_news_entity_refine_new_s005_r010_latest.json`
- Coverage denominator: `78316`
- Latest sweep generated at: `2026-06-17T22:59:04Z`

## Summary

- Component names in code: `282`
- Components with latest non-null coverage: `158`
- Components without latest non-null coverage: `124`
- Supporting raw/derived/sweep signals: `21`

## Modeling Roles

| Role | Count | Meaning |
| --- | ---: | --- |
| `calibration_transform` | 38 | Nonlinear transform or interaction useful in sweeps, not an independent source. |
| `evidence_quality` | 17 | Knownness, coverage, or missingness signals used to control source trust. |
| `lexical_complexity` | 101 | JMDict ambiguity, restrictions, source/form notes, or reading complexity. |
| `native_exposure` | 58 | Frequency, corpus, or priority evidence for likely native exposure/usefulness. |
| `ordinary_ladder_admission` | 59 | Evidence that an item is or is not ordinary general vocabulary. |
| `orthographic_burden` | 44 | Kanji, written-form, stroke, visual, or script burden after exposure signals. |
| `pedagogical_anchor` | 8 | Outside learner/curriculum source that can intentionally pull useful words earlier. |
| `presentation_priority` | 59 | General pressure for when a word should appear on the learner ladder. |
| `tail_shape` | 34 | Late-vocabulary, unranked, rare-reading, or upper-tail shaping signal. |
| `topic_register_policy` | 30 | Topic, domain, register, entity, acronym, or specialist-use routing cue. |
| `word_origin_lane` | 50 | Morphology or origin lane such as kango, wago, gairaigo, POS, or sahen. |

## Source Families

| Source family | Count | Meaning |
| --- | ---: | --- |
| Acronym/code classifier | 15 | Acronym/code metadata derived from script shape, dictionary, name, and corpus evidence. |
| BCCWJ frequency | 36 | BCCWJ rank/pmw/profile evidence from the local frequency pack. |
| Candidate classifier | 5 | Current candidate-state/problem-class signals emitted before learner difficulty scoring. |
| Composite admission/topic | 42 | Composite routing cues built from dictionary, frequency, name, and topic evidence. |
| Cross-source coverage | 5 | Knownness and source-coverage evidence across multiple signal families. |
| Internal script analyzer | 1 | Built-in Japanese script-shape analyzer. |
| JLPT vocabulary | 3 | Tanos/Bluskyo JLPT vocabulary level data. |
| JMDict lexical | 85 | JMDict priority, POS, misc, field, form, reading, source, and sense metadata. |
| JMnedict names | 11 | JMnedict proper-name type metadata. |
| KANJIDIC2 | 20 | KANJIDIC2 kanji grade, old JLPT, stroke, frequency, reading, radical, variant, and reference metadata. |
| KanjiVG | 5 | KanjiVG visual/component/position/variant metadata. |
| Lesson vocabulary | 5 | Step-by-Step Japanese lesson-order vocabulary metadata. |
| Morphology/origin | 35 | BCCWJ/UniDic-style word type and POS lanes plus kango/wago interactions. |
| TUBELEX frequency | 14 | TUBELEX spoken/video frequency evidence when available. |

## Signals

| Signal | Source family | Kind | Roles | Latest coverage | Description |
| --- | --- | --- | --- | ---: | --- |
| `acronym_default_suppress_risk` | Acronym/code classifier | `risk` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_domain_concentration` | Acronym/code classifier | `signal` | `ordinary_ladder_admission`, `topic_register_policy` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_expanded_gloss` | Acronym/code classifier | `signal` | `ordinary_ladder_admission`, `lexical_complexity` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_identity_gloss` | Acronym/code classifier | `signal` | `ordinary_ladder_admission`, `lexical_complexity` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_japanese_specific_gate` | Acronym/code classifier | `gate` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_japanese_specific_usage` | Acronym/code classifier | `signal` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_mixed_code_confidence` | Acronym/code classifier | `evidence_confidence` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_proper_name_risk` | Acronym/code classifier | `risk` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_real_usage_confidence` | Acronym/code classifier | `evidence_confidence` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_shared_exact_risk` | Acronym/code classifier | `risk` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_signal_known` | Acronym/code classifier | `knownness` | `evidence_quality`, `ordinary_ladder_admission` | 0 (0.0%) | Knownness indicator for acronym signal; 1 means the source evidence is present and 0 means it is absent. |
| `acronym_spellout_reading` | Acronym/code classifier | `signal` | `ordinary_ladder_admission`, `lexical_complexity` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_surface_confidence` | Acronym/code classifier | `evidence_confidence` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `acronym_topic_only_risk` | Acronym/code classifier | `risk` | `ordinary_ladder_admission` | 548 (0.7%) | Acronym/code classifier component; useful for acronym, code, topic-only, or suppress-default routing. |
| `proper_acronym_entity_risk` | Acronym/code classifier | `risk` | `ordinary_ladder_admission` | 548 (0.7%) | Composite proper-name/entity cue for ordinary-ladder admission and topic routing. |
| `bccwj_domain_profile_risk` | BCCWJ frequency | `variability_compat` | `native_exposure`, `presentation_priority` | 0 (0.0%) | Compatibility alias for BCCWJ domain profile variability; no longer used inside JMDict register/domain risk. |
| `bccwj_domain_profile_variability` | BCCWJ frequency | `variability` | `native_exposure`, `presentation_priority` | 0 (0.0%) | BCCWJ domain profile variability from domain-rank coverage and spread; distribution-shape evidence, not direct topic risk. |
| `bccwj_domain_rank_coverage` | BCCWJ frequency | `evidence_confidence` | `native_exposure`, `presentation_priority`, `topic_register_policy` | 78316 (100.0%) | bccwj domain rank coverage component exposed to learner-difficulty model sweeps. |
| `bccwj_domain_rank_known` | BCCWJ frequency | `knownness` | `evidence_quality`, `native_exposure`, `presentation_priority` | 0 (0.0%) | Knownness indicator for bccwj domain rank; 1 means the source evidence is present and 0 means it is absent. |
| `bccwj_domain_rank_spread` | BCCWJ frequency | `signal` | `native_exposure`, `presentation_priority`, `topic_register_policy` | 78316 (100.0%) | bccwj domain rank spread component exposed to learner-difficulty model sweeps. |
| `bccwj_domain_rank_variability` | BCCWJ frequency | `variability` | `native_exposure`, `presentation_priority` | 0 (0.0%) | BCCWJ domain rank variability alias for domain rank spread; distribution-shape evidence, not direct difficulty. |
| `bccwj_fixed_variable_rank_delta` | BCCWJ frequency | `signal` | `native_exposure`, `presentation_priority` | 64178 (81.9%) | Signed BCCWJ fixed-vs-variable rank delta transformed into a normalized component. |
| `bccwj_pmw_spread` | BCCWJ frequency | `signal` | `native_exposure`, `presentation_priority` | 78316 (100.0%) | bccwj pmw spread component exposed to learner-difficulty model sweeps. |
| `bccwj_rank_spread` | BCCWJ frequency | `signal` | `native_exposure`, `presentation_priority` | 78316 (100.0%) | bccwj rank spread component exposed to learner-difficulty model sweeps. |
| `bccwj_rank_variability` | BCCWJ frequency | `variability` | `native_exposure`, `presentation_priority` | 0 (0.0%) | BCCWJ rank variability alias for rank spread; distribution-shape evidence, not direct difficulty. |
| `frequency` | BCCWJ frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 78316 (100.0%) | BCCWJ rank-derived difficulty proxy; higher means weaker corpus frequency evidence and usually later presentation. |
| `frequency_ease` | BCCWJ frequency | `ease_or_beginner_anchor` | `native_exposure`, `presentation_priority` | 0 (0.0%) | Inverse of BCCWJ difficulty; higher means stronger commonness/ease evidence. |
| `frequency_power2` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Squared BCCWJ difficulty that emphasizes upper-tail rarity. |
| `frequency_power3` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Cubed BCCWJ difficulty that strongly emphasizes upper-tail rarity. |
| `frequency_rank_known` | BCCWJ frequency | `knownness` | `evidence_quality`, `native_exposure`, `presentation_priority` | 0 (0.0%) | Knownness indicator for frequency rank; 1 means the source evidence is present and 0 means it is absent. |
| `frequency_sqrt` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `calibration_transform` | 78316 (100.0%) | Square-root transform of BCCWJ difficulty that amplifies lower/mid frequency difficulty. |
| `frequency_tail50` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | BCCWJ difficulty ramp that activates above roughly 50% frequency difficulty; useful for upper-tail shaping. |
| `frequency_tail65` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | BCCWJ difficulty ramp that activates above roughly 65% frequency difficulty; useful for upper-tail shaping. |
| `frequency_tail80` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | BCCWJ difficulty ramp that activates above roughly 80% frequency difficulty; useful for upper-tail shaping. |
| `frequency_tail90` | BCCWJ frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | BCCWJ difficulty ramp that activates above roughly 90% frequency difficulty; useful for upper-tail shaping. |
| `frequency_unranked_floor60_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 60% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_floor70_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 70% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_floor80_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 80% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_floor90_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 90% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_floor95_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 95% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_floor99_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk with an enforced 99% floor when BCCWJ rank evidence is missing. |
| `frequency_unranked_power2_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk multiplied by BCCWJ difficulty to power 2. |
| `frequency_unranked_power3_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk multiplied by BCCWJ difficulty to power 3. |
| `frequency_unranked_priority_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape` | 78316 (100.0%) | Risk/interaction for rows missing usable BCCWJ rank evidence. |
| `frequency_unranked_rare_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape` | 78316 (100.0%) | Risk/interaction for rows missing usable BCCWJ rank evidence. |
| `frequency_unranked_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape` | 78316 (100.0%) | Risk/interaction for rows missing usable BCCWJ rank evidence. |
| `frequency_unranked_tail65_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk gated by a BCCWJ upper-tail rarity ramp. |
| `frequency_unranked_tail80_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk gated by a BCCWJ upper-tail rarity ramp. |
| `frequency_unranked_tail90_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk gated by a BCCWJ upper-tail rarity ramp. |
| `frequency_unranked_tail_risk` | BCCWJ frequency | `risk` | `native_exposure`, `presentation_priority`, `tail_shape`, `calibration_transform` | 78316 (100.0%) | Unranked-frequency risk gated by a BCCWJ upper-tail rarity ramp. |
| `frequency_value_known` | BCCWJ frequency | `knownness` | `evidence_quality`, `native_exposure`, `presentation_priority` | 0 (0.0%) | Knownness indicator for frequency value; 1 means the source evidence is present and 0 means it is absent. |
| `candidate_deprioritized_named_entity_risk` | Candidate classifier | `risk` | `ordinary_ladder_admission` | 78316 (100.0%) | Candidate deprioritization combined with named-entity evidence. |
| `candidate_deprioritized_named_frequency_risk` | Candidate classifier | `risk` | `ordinary_ladder_admission`, `calibration_transform` | 78316 (100.0%) | Candidate deprioritized named-entity risk multiplied by frequency difficulty. |
| `candidate_deprioritized_vocab_risk` | Candidate classifier | `risk` | `ordinary_ladder_admission` | 78316 (100.0%) | Current candidate classifier says the row is deprioritized vocabulary. |
| `problem_class_proper_flag` | Candidate classifier | `source_flag` | `ordinary_ladder_admission` | 0 (0.0%) | Raw candidate-classifier flag for proper-noun problem class. |
| `problem_class_proper_risk` | Candidate classifier | `source_flag_compat` | `ordinary_ladder_admission` | 78316 (100.0%) | Compatibility alias for `problem_class_proper_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_jmdict_ambiguity_risk` | Composite admission/topic | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `common_jmdict_ambiguity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_jmdict_ambiguity_score` | Composite admission/topic | `score` | `lexical_complexity` | 0 (0.0%) | common jmdict ambiguity score; inspect roles before treating it as direct presentation difficulty. |
| `common_kango_ambiguity_risk` | Composite admission/topic | `score_compat` | `lexical_complexity`, `word_origin_lane` | 0 (0.0%) | Compatibility alias for `common_kango_ambiguity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_kango_ambiguity_score` | Composite admission/topic | `score` | `lexical_complexity`, `word_origin_lane` | 0 (0.0%) | common kango ambiguity score; inspect roles before treating it as direct presentation difficulty. |
| `common_kango_complexity_risk` | Composite admission/topic | `score_compat` | `word_origin_lane` | 0 (0.0%) | Compatibility alias for `common_kango_complexity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_kango_complexity_score` | Composite admission/topic | `score` | `word_origin_lane` | 0 (0.0%) | common kango complexity score; inspect roles before treating it as direct presentation difficulty. |
| `common_kango_register_domain_risk` | Composite admission/topic | `score_compat` | `topic_register_policy`, `word_origin_lane` | 0 (0.0%) | Compatibility alias for `common_kango_register_domain_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_kango_register_domain_score` | Composite admission/topic | `score` | `topic_register_policy`, `word_origin_lane` | 0 (0.0%) | common kango register domain score; inspect roles before treating it as direct presentation difficulty. |
| `common_kango_written_burden` | Composite admission/topic | `burden` | `orthographic_burden`, `word_origin_lane` | 0 (0.0%) | common kango written burden signal; higher means more learner burden. |
| `common_reading_complexity_risk` | Composite admission/topic | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `common_reading_complexity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_reading_complexity_score` | Composite admission/topic | `score` | `lexical_complexity` | 0 (0.0%) | common reading complexity score; inspect roles before treating it as direct presentation difficulty. |
| `common_register_domain_risk` | Composite admission/topic | `score_compat` | `topic_register_policy` | 0 (0.0%) | Compatibility alias for `common_register_domain_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_register_domain_score` | Composite admission/topic | `score` | `topic_register_policy` | 0 (0.0%) | common register domain score; inspect roles before treating it as direct presentation difficulty. |
| `common_restriction_complexity_risk` | Composite admission/topic | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `common_restriction_complexity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `common_restriction_complexity_score` | Composite admission/topic | `score` | `lexical_complexity` | 0 (0.0%) | common restriction complexity score; inspect roles before treating it as direct presentation difficulty. |
| `entity_suppression_gate` | Composite admission/topic | `gate` | `ordinary_ladder_admission` | 0 (0.0%) | Gate that allows entity overlap to become ladder-suppression risk only when ordinary-vocabulary protection is weak or candidate evidence says deprioritized. |
| `geopolitical_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission`, `topic_register_policy` | 78316 (100.0%) | Country/place entity risk, especially when tied to news/policy topics. |
| `geopolitical_frequency_risk` | Composite admission/topic | `risk` | `topic_register_policy`, `calibration_transform` | 78316 (100.0%) | Geopolitical entity risk multiplied by frequency difficulty. |
| `kanjidic2_known` | Composite admission/topic | `knownness` | `evidence_quality`, `orthographic_burden` | 0 (0.0%) | Knownness indicator for kanjidic2; 1 means the source evidence is present and 0 means it is absent. |
| `named_entity_frequency_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission`, `calibration_transform` | 78316 (100.0%) | named entity frequency risk signal; higher means stronger evidence for that property. |
| `named_entity_overlap` | Composite admission/topic | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw named-entity overlap from POS, candidate class, JMnedict, and acronym evidence before ordinary-vocabulary protection. |
| `named_entity_risk` | Composite admission/topic | `risk_compat` | `ordinary_ladder_admission` | 78316 (100.0%) | Compatibility alias for gated entity-suppression risk, not raw JMnedict/POS name overlap. |
| `news_abbreviation_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission`, `topic_register_policy` | 6700 (8.6%) | News/policy abbreviation/entity risk for acronym-like topic rows. |
| `news_named_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission`, `topic_register_policy` | 34019 (43.4%) | News/policy topic risk combined with named-entity risk. |
| `news_named_frequency_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission`, `topic_register_policy`, `calibration_transform` | 34019 (43.4%) | News/policy named-entity risk multiplied by frequency difficulty. |
| `news_or_policy_frequency_risk` | Composite admission/topic | `risk` | `topic_register_policy`, `calibration_transform` | 34019 (43.4%) | News/policy topic risk multiplied by BCCWJ frequency difficulty. |
| `news_or_policy_topic_risk` | Composite admission/topic | `risk` | `topic_register_policy` | 34019 (43.4%) | Business, economics, law, or politics field/domain risk; JMDict `news` priority tags no longer create this signal. |
| `ordinary_ladder_entity_suppression_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission` | 0 (0.0%) | Named-entity ladder-suppression risk after ordinary-vocabulary protection. |
| `ordinary_vocab_protection` | Composite admission/topic | `protection` | `ordinary_ladder_admission`, `pedagogical_anchor`, `native_exposure` | 0 (0.0%) | Commonness and pedagogical-anchor protection used to keep ordinary vocabulary from becoming entity/non-ladder risk. |
| `proper_country_entity_overlap` | Composite admission/topic | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw country/geopolitical entity overlap before ordinary-vocabulary protection. |
| `proper_country_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission` | 78316 (100.0%) | Composite proper-name/entity cue for ordinary-ladder admission and topic routing. |
| `proper_country_pos_flag` | Composite admission/topic | `source_flag` | `ordinary_ladder_admission`, `word_origin_lane` | 0 (0.0%) | Raw POS flag for proper-country classification. |
| `proper_country_pos_risk` | Composite admission/topic | `source_flag_compat` | `ordinary_ladder_admission`, `word_origin_lane` | 78316 (100.0%) | Compatibility alias for `proper_country_pos_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `proper_noun_pos_flag` | Composite admission/topic | `source_flag` | `ordinary_ladder_admission`, `word_origin_lane` | 0 (0.0%) | Raw POS flag for proper-noun classification. |
| `proper_noun_pos_risk` | Composite admission/topic | `source_flag_compat` | `ordinary_ladder_admission`, `word_origin_lane` | 78316 (100.0%) | Compatibility alias for `proper_noun_pos_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `proper_org_entity_overlap` | Composite admission/topic | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw organization/product entity overlap before ordinary-vocabulary protection. |
| `proper_org_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission` | 27906 (35.6%) | Composite proper-name/entity cue for ordinary-ladder admission and topic routing. |
| `proper_place_entity_overlap` | Composite admission/topic | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw place-entity overlap from POS and JMnedict evidence before ordinary-vocabulary protection. |
| `proper_place_entity_risk` | Composite admission/topic | `risk` | `ordinary_ladder_admission` | 78316 (100.0%) | Composite proper-name/entity cue for ordinary-ladder admission and topic routing. |
| `proper_place_pos_flag` | Composite admission/topic | `source_flag` | `ordinary_ladder_admission`, `word_origin_lane` | 0 (0.0%) | Raw POS flag for proper-place classification. |
| `proper_place_pos_risk` | Composite admission/topic | `source_flag_compat` | `ordinary_ladder_admission`, `word_origin_lane` | 78316 (100.0%) | Compatibility alias for `proper_place_pos_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `rare_non_standard_reading_risk` | Composite admission/topic | `risk` | `lexical_complexity`, `tail_shape` | 58093 (74.2%) | Nonstandard-reading risk gated to upper-frequency-difficulty rows. |
| `frequency_source_known` | Cross-source coverage | `knownness` | `evidence_quality`, `native_exposure`, `presentation_priority` | 0 (0.0%) | Knownness indicator for frequency source; 1 means the source evidence is present and 0 means it is absent. |
| `lexical_source_known` | Cross-source coverage | `knownness` | `evidence_quality`, `lexical_complexity` | 0 (0.0%) | Knownness indicator for lexical source; 1 means the source evidence is present and 0 means it is absent. |
| `orthographic_source_known` | Cross-source coverage | `knownness` | `evidence_quality`, `orthographic_burden` | 0 (0.0%) | Knownness indicator for orthographic source; 1 means the source evidence is present and 0 means it is absent. |
| `pedagogical_source_known` | Cross-source coverage | `knownness` | `evidence_quality`, `pedagogical_anchor`, `presentation_priority` | 0 (0.0%) | Knownness indicator for pedagogical source; 1 means the source evidence is present and 0 means it is absent. |
| `source_coverage_count` | Cross-source coverage | `coverage_count` | `evidence_quality` | 0 (0.0%) | Scaled count of major source families with known evidence for the row. |
| `script_complexity` | Internal script analyzer | `difficulty_proxy` | `orthographic_burden` | 78316 (100.0%) | Built-in script-complexity proxy from the Japanese script analyzer. |
| `jlpt_vocab_beginner_core` | JLPT vocabulary | `ease_or_beginner_anchor` | `pedagogical_anchor`, `presentation_priority` | 8562 (10.9%) | Beginner-core strength from JLPT vocabulary data. |
| `jlpt_vocab_difficulty` | JLPT vocabulary | `difficulty_proxy` | `pedagogical_anchor`, `presentation_priority` | 8562 (10.9%) | JLPT vocabulary level anchor; lower for N5/N4 and higher for N2/N1. |
| `jlpt_vocab_known` | JLPT vocabulary | `knownness` | `evidence_quality`, `pedagogical_anchor`, `presentation_priority` | 0 (0.0%) | Knownness indicator for jlpt vocab; 1 means the source evidence is present and 0 means it is absent. |
| `jmdict_abbreviation_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict abbreviation source flag; source evidence, not direct learner difficulty. |
| `jmdict_abbreviation_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 16521 (21.1%) | Compatibility alias for `jmdict_abbreviation_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_affix_counter_class` | JMDict lexical | `signal` | `lexical_complexity` | 0 (0.0%) | JMDict POS overlap flag for prefix, suffix, or counter classes; raw source evidence, not direct difficulty. |
| `jmdict_ambiguity_risk` | JMDict lexical | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `jmdict_ambiguity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_ambiguity_score` | JMDict lexical | `score` | `lexical_complexity` | 0 (0.0%) | jmdict ambiguity score; inspect roles before treating it as direct presentation difficulty. |
| `jmdict_cross_reference_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict cross reference source flag; source evidence, not direct learner difficulty. |
| `jmdict_cross_reference_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_cross_reference_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_dialect_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict dialect source flag; source evidence, not direct learner difficulty. |
| `jmdict_dialect_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_dialect_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_entry_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_entry_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | Scaled JMDict count signal over entries, POS values, fields, forms, senses, or glosses. |
| `jmdict_field_count` | JMDict lexical | `count_or_ambiguity` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | JMDict register, dialect, or field/domain signal for routing and presentation policy. |
| `jmdict_field_marked_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict field marked source flag; source evidence, not direct learner difficulty. |
| `jmdict_field_marked_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Compatibility alias for `jmdict_field_marked_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_foreign_priority_commonness` | JMDict lexical | `source_flag` | `native_exposure`, `lexical_complexity` | 0 (0.0%) | JMDict lexical signal for priority, usage, source, field, form, or sense structure. |
| `jmdict_foreign_priority_risk` | JMDict lexical | `source_flag_compat` | `native_exposure`, `lexical_complexity` | 28708 (36.7%) | Compatibility alias for `jmdict_foreign_priority_commonness`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_form_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_form_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict kanji/reading/form marker or count signal. |
| `jmdict_function_discourse_class` | JMDict lexical | `signal` | `lexical_complexity` | 0 (0.0%) | JMDict POS overlap flag for pronoun/interjection-style function or discourse words; raw source evidence, not direct difficulty. |
| `jmdict_gloss_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_gloss_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 78316 (100.0%) | Scaled JMDict count signal over entries, POS values, fields, forms, senses, or glosses. |
| `jmdict_kana_preferred_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict kana preferred source flag; source evidence, not direct learner difficulty. |
| `jmdict_kana_preferred_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_kana_preferred_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_kanji_form_ambiguity` | JMDict lexical | `count_or_ambiguity` | `orthographic_burden`, `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_kanji_form_count` | JMDict lexical | `count_or_ambiguity` | `orthographic_burden`, `lexical_complexity` | 0 (0.0%) | JMDict kanji/reading/form marker or count signal. |
| `jmdict_kanji_form_marked_flag` | JMDict lexical | `source_flag` | `orthographic_burden`, `lexical_complexity` | 0 (0.0%) | Raw jmdict kanji form marked source flag; source evidence, not direct learner difficulty. |
| `jmdict_kanji_form_marked_risk` | JMDict lexical | `source_flag_compat` | `orthographic_burden`, `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_kanji_form_marked_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_lexical_known` | JMDict lexical | `knownness` | `evidence_quality`, `lexical_complexity` | 0 (0.0%) | Knownness indicator for jmdict lexical; 1 means the source evidence is present and 0 means it is absent. |
| `jmdict_loanword_source_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict loanword source source flag; source evidence, not direct learner difficulty. |
| `jmdict_loanword_source_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_loanword_source_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_marked_usage_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict marked usage source flag; source evidence, not direct learner difficulty. |
| `jmdict_marked_usage_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_marked_usage_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_news_or_policy_domain_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 8767 (11.2%) | Compatibility alias for `jmdict_news_or_policy_field_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_news_or_policy_field_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict news or policy field source flag; source evidence, not direct learner difficulty. |
| `jmdict_news_priority_commonness` | JMDict lexical | `source_flag` | `native_exposure` | 0 (0.0%) | Binary JMDict `news` priority tag used as source/commonness evidence, not as topic risk. |
| `jmdict_news_priority_risk` | JMDict lexical | `source_flag_compat` | `native_exposure` | 28708 (36.7%) | Compatibility alias for the JMDict `news` priority tag; this is commonness/source evidence, not topic or difficulty risk. |
| `jmdict_no_kanji_reading_flag` | JMDict lexical | `source_flag` | `orthographic_burden`, `lexical_complexity` | 0 (0.0%) | Raw jmdict no kanji reading source flag; source evidence, not direct learner difficulty. |
| `jmdict_no_kanji_reading_risk` | JMDict lexical | `source_flag_compat` | `orthographic_burden`, `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_no_kanji_reading_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_non_ladder_entry_risk` | JMDict lexical | `risk` | `ordinary_ladder_admission`, `lexical_complexity` | 0 (0.0%) | JMDict non-ladder risk after ordinary-vocabulary protection is applied to raw non-vocab class evidence. |
| `jmdict_non_vocab_raw_class_score` | JMDict lexical | `raw_class_score` | `ordinary_ladder_admission`, `lexical_complexity` | 0 (0.0%) | Raw legacy JMDict non-vocab class score before ordinary-vocabulary protection; this bundles function, numeric, affix/counter, proper-noun, and marked-usage evidence. |
| `jmdict_non_vocab_risk` | JMDict lexical | `risk_compat` | `ordinary_ladder_admission`, `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_non_ladder_entry_risk`; no longer the raw JMDict non-vocab class score. |
| `jmdict_numeric_class` | JMDict lexical | `signal` | `lexical_complexity` | 0 (0.0%) | JMDict POS overlap flag for numeric classes; raw source evidence, not direct difficulty. |
| `jmdict_organization_misc_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict organization misc source flag; source evidence, not direct learner difficulty. |
| `jmdict_organization_misc_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 16521 (21.1%) | Compatibility alias for `jmdict_organization_misc_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_particle_auxiliary_class` | JMDict lexical | `signal` | `lexical_complexity` | 0 (0.0%) | JMDict POS overlap flag for particle or auxiliary-verb classes; raw source evidence, not direct difficulty. |
| `jmdict_polysemy_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict polysemy source flag; source evidence, not direct learner difficulty. |
| `jmdict_polysemy_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_polysemy_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_pos_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity`, `word_origin_lane` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_pos_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity`, `word_origin_lane` | 0 (0.0%) | Scaled JMDict count signal over entries, POS values, fields, forms, senses, or glosses. |
| `jmdict_priority` | JMDict lexical | `difficulty_proxy` | `native_exposure`, `lexical_complexity` | 78316 (100.0%) | Inverse JMDict priority signal; higher means weaker JMDict commonness/priority evidence. |
| `jmdict_priority_known` | JMDict lexical | `knownness` | `evidence_quality`, `lexical_complexity` | 0 (0.0%) | Knownness indicator for jmdict priority; 1 means the source evidence is present and 0 means it is absent. |
| `jmdict_proper_noun_overlap` | JMDict lexical | `overlap` | `ordinary_ladder_admission`, `lexical_complexity` | 0 (0.0%) | JMDict POS overlap flag for proper-noun classes; raw source evidence, not direct ladder-suppression risk. |
| `jmdict_reading_complexity_risk` | JMDict lexical | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `jmdict_reading_complexity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_reading_complexity_score` | JMDict lexical | `score` | `lexical_complexity` | 0 (0.0%) | jmdict reading complexity score; inspect roles before treating it as direct presentation difficulty. |
| `jmdict_reading_form_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_reading_form_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict reading/form restriction or reading-complexity signal. |
| `jmdict_reading_form_marked_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict reading form marked source flag; source evidence, not direct learner difficulty. |
| `jmdict_reading_form_marked_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_reading_form_marked_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_reading_restricted_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict reading restricted source flag; source evidence, not direct learner difficulty. |
| `jmdict_reading_restricted_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_reading_restricted_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_register_domain_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict register domain source flag; source evidence, not direct learner difficulty. |
| `jmdict_register_domain_risk` | JMDict lexical | `score_compat` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Compatibility alias for `jmdict_register_domain_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_register_domain_score` | JMDict lexical | `score` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | jmdict register domain score; inspect roles before treating it as direct presentation difficulty. |
| `jmdict_register_marked_flag` | JMDict lexical | `source_flag` | `topic_register_policy`, `lexical_complexity` | 0 (0.0%) | Raw jmdict register marked source flag; source evidence, not direct learner difficulty. |
| `jmdict_register_marked_risk` | JMDict lexical | `source_flag_compat` | `topic_register_policy`, `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_register_marked_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_restriction_complexity_risk` | JMDict lexical | `score_compat` | `lexical_complexity` | 0 (0.0%) | Compatibility alias for `jmdict_restriction_complexity_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_restriction_complexity_score` | JMDict lexical | `score` | `lexical_complexity` | 0 (0.0%) | jmdict restriction complexity score; inspect roles before treating it as direct presentation difficulty. |
| `jmdict_restriction_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | Scaled JMDict count signal over entries, POS values, fields, forms, senses, or glosses. |
| `jmdict_search_only_form_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict search only form source flag; source evidence, not direct learner difficulty. |
| `jmdict_search_only_form_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_search_only_form_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_sense_ambiguity` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 0 (0.0%) | JMDict ambiguity signal from entry, POS, form, sense, or gloss multiplicity. |
| `jmdict_sense_count` | JMDict lexical | `count_or_ambiguity` | `lexical_complexity` | 78316 (100.0%) | JMDict sense-count, sense-info, or sense-restriction signal. |
| `jmdict_sense_info_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict sense info source flag; source evidence, not direct learner difficulty. |
| `jmdict_sense_info_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_sense_info_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_sense_restricted_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict sense restricted source flag; source evidence, not direct learner difficulty. |
| `jmdict_sense_restricted_risk` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_sense_restricted_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_sinitic_source` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_sinitic_source_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_sinitic_source_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict sinitic source source flag; source evidence, not direct learner difficulty. |
| `jmdict_source_text_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict source text source flag; source evidence, not direct learner difficulty. |
| `jmdict_source_text_present` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_source_text_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_source_type_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict source type source flag; source evidence, not direct learner difficulty. |
| `jmdict_source_type_marked` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_source_type_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_wasei_source` | JMDict lexical | `source_flag_compat` | `lexical_complexity` | 78316 (100.0%) | Compatibility alias for `jmdict_wasei_source_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmdict_wasei_source_flag` | JMDict lexical | `source_flag` | `lexical_complexity` | 0 (0.0%) | Raw jmdict wasei source source flag; source evidence, not direct learner difficulty. |
| `non_standard_reading_risk` | JMDict lexical | `risk` | `lexical_complexity` | 58093 (74.2%) | Risk that the observed reading does not match KANJIDIC2 character reading options. |
| `jmnedict_creative_or_special_name_overlap` | JMnedict names | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw JMnedict creative-work, character, mythic, or special-name overlap flag. |
| `jmnedict_creative_or_special_name_risk` | JMnedict names | `overlap_compat` | `ordinary_ladder_admission` | 16969 (21.7%) | Compatibility alias for `jmnedict_creative_or_special_name_overlap`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmnedict_name_known` | JMnedict names | `knownness` | `evidence_quality`, `ordinary_ladder_admission` | 0 (0.0%) | Knownness indicator for jmnedict name; 1 means the source evidence is present and 0 means it is absent. |
| `jmnedict_name_overlap` | JMnedict names | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw JMnedict name-overlap score; higher means stronger name evidence, not automatic ladder-suppression risk. |
| `jmnedict_name_risk` | JMnedict names | `overlap_compat` | `ordinary_ladder_admission` | 16969 (21.7%) | Compatibility alias for the raw JMnedict name-overlap score; use `jmnedict_name_overlap` for the clearer name. |
| `jmnedict_org_product_name_overlap` | JMnedict names | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw JMnedict organization/product-name overlap flag. |
| `jmnedict_org_product_name_risk` | JMnedict names | `overlap_compat` | `ordinary_ladder_admission` | 16969 (21.7%) | Compatibility alias for `jmnedict_org_product_name_overlap`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmnedict_person_name_overlap` | JMnedict names | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw JMnedict person-name overlap flag. |
| `jmnedict_person_name_risk` | JMnedict names | `overlap_compat` | `ordinary_ladder_admission` | 16969 (21.7%) | Compatibility alias for `jmnedict_person_name_overlap`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `jmnedict_place_name_overlap` | JMnedict names | `overlap` | `ordinary_ladder_admission` | 0 (0.0%) | Raw JMnedict place-name overlap flag. |
| `jmnedict_place_name_risk` | JMnedict names | `overlap_compat` | `ordinary_ladder_admission` | 16969 (21.7%) | Compatibility alias for `jmnedict_place_name_overlap`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `kanji_burden` | KANJIDIC2 | `burden` | `orthographic_burden` | 58094 (74.2%) | Mean kanji burden combining curriculum, visual, and stroke evidence. |
| `kanji_curriculum_burden` | KANJIDIC2 | `burden` | `orthographic_burden` | 56881 (72.6%) | Mean kanji curriculum burden from grade, old JLPT, and frequency-rank evidence. |
| `kanji_curriculum_missing_risk` | KANJIDIC2 | `risk` | `orthographic_burden` | 58094 (74.2%) | Risk that the word's kanji have shape evidence but weak curriculum-level evidence. |
| `kanji_frequency_rank` | KANJIDIC2 | `difficulty_proxy` | `orthographic_burden` | 56379 (72.0%) | KANJIDIC2 kanji frequency-rank difficulty proxy. |
| `kanji_grade` | KANJIDIC2 | `difficulty_proxy` | `orthographic_burden` | 56755 (72.5%) | KANJIDIC2 school-grade difficulty proxy over the word's kanji. |
| `kanji_shape_burden` | KANJIDIC2 | `burden` | `orthographic_burden` | 58094 (74.2%) | Mean kanji shape burden from visual complexity and stroke count. |
| `kanjidic_meaning_count` | KANJIDIC2 | `count_or_ambiguity` | `orthographic_burden` | 58094 (74.2%) | KANJIDIC2 aggregate count or risk signal over the word's kanji. |
| `kanjidic_nanori_reading_count_score` | KANJIDIC2 | `score` | `orthographic_burden`, `lexical_complexity` | 0 (0.0%) | kanjidic nanori reading count score; inspect roles before treating it as direct presentation difficulty. |
| `kanjidic_nanori_reading_risk` | KANJIDIC2 | `score_compat` | `orthographic_burden`, `lexical_complexity` | 58094 (74.2%) | Compatibility alias for `kanjidic_nanori_reading_count_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `kanjidic_query_code_coverage` | KANJIDIC2 | `evidence_confidence` | `orthographic_burden` | 58094 (74.2%) | KANJIDIC2 aggregate count or risk signal over the word's kanji. |
| `kanjidic_radical_value_count` | KANJIDIC2 | `count_or_ambiguity` | `orthographic_burden` | 58094 (74.2%) | KANJIDIC2 aggregate count or risk signal over the word's kanji. |
| `kanjidic_reference_depth` | KANJIDIC2 | `signal` | `orthographic_burden` | 58094 (74.2%) | KANJIDIC2 aggregate count or risk signal over the word's kanji. |
| `kanjidic_variant_type_count_score` | KANJIDIC2 | `score` | `orthographic_burden` | 0 (0.0%) | kanjidic variant type count score; inspect roles before treating it as direct presentation difficulty. |
| `kanjidic_variant_type_risk` | KANJIDIC2 | `score_compat` | `orthographic_burden` | 58094 (74.2%) | Compatibility alias for `kanjidic_variant_type_count_score`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `max_kanji_burden` | KANJIDIC2 | `burden` | `orthographic_burden`, `calibration_transform` | 58094 (74.2%) | Maximum kanji burden across curriculum, visual, and stroke evidence. |
| `max_kanji_shape_burden` | KANJIDIC2 | `burden` | `orthographic_burden`, `calibration_transform` | 58094 (74.2%) | Maximum kanji shape burden across visual complexity and stroke-count signals. |
| `max_written_form_burden` | KANJIDIC2 | `burden` | `orthographic_burden`, `lexical_complexity`, `calibration_transform` | 78316 (100.0%) | Maximum written-form burden from visual, stroke, and script-complexity signals. |
| `old_jlpt_kanji` | KANJIDIC2 | `difficulty_proxy` | `orthographic_burden` | 55789 (71.2%) | Old JLPT kanji-level difficulty proxy over the word's kanji. |
| `stroke_count` | KANJIDIC2 | `difficulty_proxy` | `orthographic_burden` | 58094 (74.2%) | KANJIDIC2 stroke-count difficulty proxy. |
| `written_form_burden` | KANJIDIC2 | `burden` | `orthographic_burden`, `lexical_complexity` | 78316 (100.0%) | Mean written-form burden from visual, stroke, and script-complexity signals. |
| `kanjivg_known` | KanjiVG | `knownness` | `evidence_quality`, `orthographic_burden` | 0 (0.0%) | Knownness indicator for kanjivg; 1 means the source evidence is present and 0 means it is absent. |
| `kanjivg_phonetic_component` | KanjiVG | `signal` | `orthographic_burden` | 58079 (74.2%) | KanjiVG visual/component structure signal over the word's written form. |
| `kanjivg_position_detail` | KanjiVG | `transform_or_interaction` | `orthographic_burden`, `tail_shape`, `calibration_transform` | 58079 (74.2%) | KanjiVG visual/component structure signal over the word's written form. |
| `kanjivg_variant_structure` | KanjiVG | `signal` | `orthographic_burden` | 58079 (74.2%) | KanjiVG visual/component structure signal over the word's written form. |
| `kanjivg_visual_complexity` | KanjiVG | `difficulty_proxy` | `orthographic_burden` | 58079 (74.2%) | KanjiVG visual-complexity proxy for the written form. |
| `lesson_name_contamination_frequency_risk` | Lesson vocabulary | `risk` | `calibration_transform` | 78316 (100.0%) | Lesson name-contamination risk multiplied by frequency difficulty. |
| `lesson_name_contamination_risk` | Lesson vocabulary | `risk` | `presentation_priority` | 78316 (100.0%) | Lesson-vocabulary row also has named-entity evidence. |
| `lesson_vocab_beginner_core` | Lesson vocabulary | `ease_or_beginner_anchor` | `pedagogical_anchor`, `presentation_priority` | 440 (0.6%) | Beginner-core strength from Step-by-Step Japanese lesson vocabulary. |
| `lesson_vocab_difficulty` | Lesson vocabulary | `difficulty_proxy` | `pedagogical_anchor`, `presentation_priority` | 440 (0.6%) | Lesson-order difficulty anchor from Step-by-Step Japanese vocabulary. |
| `lesson_vocab_known` | Lesson vocabulary | `knownness` | `evidence_quality`, `pedagogical_anchor`, `presentation_priority` | 0 (0.0%) | Knownness indicator for lesson vocab; 1 means the source evidence is present and 0 means it is absent. |
| `kango_common_priority_risk` | Morphology/origin | `risk` | `native_exposure`, `word_origin_lane` | 77836 (99.4%) | Kango origin combined with weaker JMDict priority and frequency difficulty. |
| `kango_kanji_burden` | Morphology/origin | `burden` | `orthographic_burden`, `word_origin_lane` | 58087 (74.2%) | Kango-specific interaction signal for origin-conditioned presentation-level modeling. |
| `kango_kanji_grade` | Morphology/origin | `signal` | `orthographic_burden`, `word_origin_lane` | 56748 (72.5%) | Kango-specific interaction signal for origin-conditioned presentation-level modeling. |
| `kango_mid_signal` | Morphology/origin | `signal` | `word_origin_lane` | 58087 (74.2%) | Composite kango mid/upper-mid signal using kango origin, frequency, and kanji burden. |
| `kango_old_jlpt_kanji` | Morphology/origin | `signal` | `orthographic_burden`, `word_origin_lane` | 55785 (71.2%) | Kango-specific interaction signal for origin-conditioned presentation-level modeling. |
| `kango_uncommon_kanji_burden` | Morphology/origin | `burden` | `orthographic_burden`, `word_origin_lane` | 58087 (74.2%) | Kango-specific interaction signal for origin-conditioned presentation-level modeling. |
| `kango_visual_complexity` | Morphology/origin | `signal` | `word_origin_lane` | 58072 (74.2%) | Kango-specific interaction signal for origin-conditioned presentation-level modeling. |
| `pos_adjective_gate` | Morphology/origin | `gate` | `word_origin_lane` | 78316 (100.0%) | POS gate from the seed row; useful for lane-specific model shapes. |
| `pos_common_noun_gate` | Morphology/origin | `gate` | `word_origin_lane` | 78316 (100.0%) | POS gate from the seed row; useful for lane-specific model shapes. |
| `pos_plain_verb_gate` | Morphology/origin | `gate` | `word_origin_lane` | 78316 (100.0%) | POS gate from the seed row; useful for lane-specific model shapes. |
| `pos_sahen_noun_risk` | Morphology/origin | `risk` | `word_origin_lane` | 78316 (100.0%) | POS gate from the seed row; useful for lane-specific model shapes. |
| `rare_wago_marked_usage_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 77836 (99.4%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_max_kanji_burden` | Morphology/origin | `burden` | `orthographic_burden`, `word_origin_lane`, `tail_shape`, `calibration_transform` | 58087 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_max_written_burden` | Morphology/origin | `burden` | `orthographic_burden`, `word_origin_lane`, `tail_shape`, `calibration_transform` | 77836 (99.4%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_missing_curriculum_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 58087 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_missing_curriculum_shape_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 58087 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_non_standard_reading_risk` | Morphology/origin | `risk` | `lexical_complexity`, `word_origin_lane`, `tail_shape` | 58086 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `rare_wago_obscure_written_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 77836 (99.4%) | Rare-wago composite for obscure written forms, marked usage, missing curriculum, and rare readings. |
| `rare_wago_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 77836 (99.4%) | Wago origin combined with rarity and weak JMDict priority. |
| `rare_wago_tail_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape`, `calibration_transform` | 77836 (99.4%) | Upper-tail rare-wago risk for late-ladder or non-general vocabulary pressure. |
| `rare_wago_written_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape` | 77836 (99.4%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `sahen_kango_ease_gate` | Morphology/origin | `gate` | `word_origin_lane` | 77836 (99.4%) | Gate for sahen-noun kango rows that may behave like productive learner vocabulary. |
| `sahen_kango_risk` | Morphology/origin | `risk` | `word_origin_lane` | 77836 (99.4%) | Same underlying sahen-kango gate exposed as a risk-shaped component. |
| `wago_kanji_burden` | Morphology/origin | `burden` | `orthographic_burden`, `word_origin_lane` | 58087 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `wago_kanji_grade` | Morphology/origin | `signal` | `orthographic_burden`, `word_origin_lane` | 56748 (72.5%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `wago_old_jlpt_kanji` | Morphology/origin | `signal` | `orthographic_burden`, `word_origin_lane` | 55785 (71.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `wago_visual_complexity` | Morphology/origin | `signal` | `word_origin_lane` | 58072 (74.2%) | Wago-specific interaction signal for origin-conditioned and tail modeling. |
| `written_wago_tail_risk` | Morphology/origin | `risk` | `word_origin_lane`, `tail_shape`, `calibration_transform` | 77836 (99.4%) | Wago tail risk driven by frequency difficulty and written-form burden. |
| `wtype_gairaigo_risk` | Morphology/origin | `risk` | `word_origin_lane` | 77836 (99.4%) | Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes. |
| `wtype_kango_risk` | Morphology/origin | `risk` | `word_origin_lane` | 77836 (99.4%) | Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes. |
| `wtype_mixed_risk` | Morphology/origin | `risk` | `word_origin_lane` | 77836 (99.4%) | Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes. |
| `wtype_non_wago_risk` | Morphology/origin | `risk` | `word_origin_lane` | 77836 (99.4%) | Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes. |
| `wtype_proper_flag` | Morphology/origin | `source_flag` | `ordinary_ladder_admission`, `word_origin_lane` | 0 (0.0%) | Raw wtype proper source flag; source evidence, not direct learner difficulty. |
| `wtype_proper_risk` | Morphology/origin | `source_flag_compat` | `ordinary_ladder_admission`, `word_origin_lane` | 77836 (99.4%) | Compatibility alias for `wtype_proper_flag`; kept for older artifacts, but the target name is the clearer semantic surface. |
| `wtype_wago_ease` | Morphology/origin | `ease_or_beginner_anchor` | `word_origin_lane` | 77836 (99.4%) | Word-origin/type gate from the frequency row; useful for kango/wago/gairaigo/proper lanes. |
| `tubelex_bccwj_agreement_hard` | TUBELEX frequency | `signal` | `native_exposure`, `presentation_priority`, `calibration_transform` | 0 (0.0%) | Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency. |
| `tubelex_bccwj_gap_abs` | TUBELEX frequency | `signal` | `native_exposure`, `presentation_priority`, `calibration_transform` | 0 (0.0%) | Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency. |
| `tubelex_bccwj_max_frequency` | TUBELEX frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `calibration_transform` | 0 (0.0%) | Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency. |
| `tubelex_bccwj_mean_frequency` | TUBELEX frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `calibration_transform` | 0 (0.0%) | Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency. |
| `tubelex_bccwj_min_frequency` | TUBELEX frequency | `transform_or_interaction` | `native_exposure`, `presentation_priority`, `calibration_transform` | 0 (0.0%) | Composite comparing TUBELEX spoken/video frequency with BCCWJ written/balanced frequency. |
| `tubelex_channels_difficulty` | TUBELEX frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_count_difficulty` | TUBELEX frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_dispersion_difficulty` | TUBELEX frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_frequency` | TUBELEX frequency | `signal` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_frequency_known` | TUBELEX frequency | `knownness` | `evidence_quality`, `native_exposure`, `presentation_priority` | 0 (0.0%) | Knownness indicator for tubelex frequency; 1 means the source evidence is present and 0 means it is absent. |
| `tubelex_rank_difficulty` | TUBELEX frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_spoken_rescue` | TUBELEX frequency | `signal` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_videos_difficulty` | TUBELEX frequency | `difficulty_proxy` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |
| `tubelex_written_only_risk` | TUBELEX frequency | `risk` | `native_exposure`, `presentation_priority` | 0 (0.0%) | TUBELEX spoken/video frequency component; useful as an alternate exposure perspective. |

## Supporting Source And Sweep Signals

These are not all active component columns, but they are available raw metadata, derived gates, or sweep controls that can be promoted into future model shapes.

| Signal | Source family | Kind | Model surface | Roles | Description |
| --- | --- | --- | --- | --- | --- |
| `jlpt_vocab_curve_grid` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweep mode that remaps raw JLPT N5-N1 levels through candidate monotonic difficulty curves instead of using the baked source mapping. |
| `jlpt_vocab_easiest_level` | JLPT vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor`, `presentation_priority` | Easiest available JLPT vocabulary level for the row; used to compute `jlpt_vocab_difficulty` and `jlpt_vocab_beginner_core`. |
| `jlpt_vocab_hardest_level` | JLPT vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor`, `presentation_priority` | Hardest available JLPT vocabulary level for rows with multiple source matches. |
| `jlpt_vocab_is_n1` | JLPT vocabulary | `derived_binary_gate` | `derivable_source_feature` | `pedagogical_anchor`, `presentation_priority` | Derivable binary indicator that the JLPT vocabulary record includes N1. Not currently a difficulty component, but directly supported by raw `levels` metadata. |
| `jlpt_vocab_is_n2` | JLPT vocabulary | `derived_binary_gate` | `derivable_source_feature` | `pedagogical_anchor`, `presentation_priority` | Derivable binary indicator that the JLPT vocabulary record includes N2. Not currently a difficulty component, but directly supported by raw `levels` metadata. |
| `jlpt_vocab_is_n3` | JLPT vocabulary | `derived_binary_gate` | `derivable_source_feature` | `pedagogical_anchor`, `presentation_priority` | Derivable binary indicator that the JLPT vocabulary record includes N3. Not currently a difficulty component, but directly supported by raw `levels` metadata. |
| `jlpt_vocab_is_n4` | JLPT vocabulary | `derived_binary_gate` | `derivable_source_feature` | `pedagogical_anchor`, `presentation_priority` | Derivable binary indicator that the JLPT vocabulary record includes N4. Not currently a difficulty component, but directly supported by raw `levels` metadata. |
| `jlpt_vocab_is_n5` | JLPT vocabulary | `derived_binary_gate` | `derivable_source_feature` | `pedagogical_anchor`, `presentation_priority` | Derivable binary indicator that the JLPT vocabulary record includes N5. Not currently a difficulty component, but directly supported by raw `levels` metadata. |
| `jlpt_vocab_levels` | JLPT vocabulary | `raw_level_array` | `supporting_matrix_field` | `pedagogical_anchor`, `presentation_priority` | Per-row raw JLPT vocabulary level array stored in the component matrix; values are 1-5 where 5=N5/easiest and 1=N1/hardest. |
| `jlpt_vocab_levels_raw` | JLPT vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor`, `presentation_priority` | Raw set of JLPT vocabulary levels attached to the source record before collapsing to easiest/hardest level. |
| `jlpt_vocab_n1_curve_value` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweepable numeric difficulty value for JLPT vocabulary N1; fed by the corresponding `--jlpt-vocab-n*-values` argument. |
| `jlpt_vocab_n2_curve_value` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweepable numeric difficulty value for JLPT vocabulary N2; fed by the corresponding `--jlpt-vocab-n*-values` argument. |
| `jlpt_vocab_n3_curve_value` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweepable numeric difficulty value for JLPT vocabulary N3; fed by the corresponding `--jlpt-vocab-n*-values` argument. |
| `jlpt_vocab_n4_curve_value` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweepable numeric difficulty value for JLPT vocabulary N4; fed by the corresponding `--jlpt-vocab-n*-values` argument. |
| `jlpt_vocab_n5_curve_value` | JLPT vocabulary | `sweep_control` | `sweep_parameter` | `pedagogical_anchor`, `calibration_transform` | Sweepable numeric difficulty value for JLPT vocabulary N5; fed by the corresponding `--jlpt-vocab-n*-values` argument. |
| `jlpt_vocab_source_count` | JLPT vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor` | Count of JLPT vocabulary source records merged into this row. |
| `jlpt_kanji_dampening_strength` | KANJIDIC2 | `sweep_control` | `sweep_parameter` | `orthographic_burden`, `pedagogical_anchor`, `calibration_transform` | Sweepable strength for pulling selected kanji/orthographic burden components down toward a JLPT vocabulary anchor when a word has one. |
| `kanjidic_old_jlpt_easiest_level` | KANJIDIC2 | `raw_source_field` | `available_source_metadata` | `orthographic_burden` | Raw easiest old-JLPT kanji level over the row's kanji. |
| `kanjidic_old_jlpt_hardest_level` | KANJIDIC2 | `raw_source_field` | `available_source_metadata` | `orthographic_burden` | Raw hardest old-JLPT kanji level over the row's kanji; collapsed into `old_jlpt_kanji` for the active component surface. |
| `lesson_vocab_earliest_lesson` | Lesson vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor`, `presentation_priority` | Raw earliest Step-by-Step Japanese lesson index; collapsed into `lesson_vocab_difficulty` and `lesson_vocab_beginner_core`. |
| `lesson_vocab_lesson_indices` | Lesson vocabulary | `raw_source_field` | `available_source_metadata` | `pedagogical_anchor`, `presentation_priority` | Raw set of Step-by-Step Japanese lesson indices for the row. |
