# en-ja Signal Endpoint Audit Concerns

Status: review artifact, no signal corrections applied
Generated: `2026-06-18T22:52:57+00:00`

This audit checks endpoint behavior for the learner-difficulty signal palette. It is intentionally diagnostic: concerns below are discussion points, not fixes.

## Inputs

- Component matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_component_matrix_latest.npz`
- Palette JSON: `docs/test_outputs/srs_learner_difficulty_signal_palette_en_ja_latest.json`
- Sweep JSON: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_semantic_fix_validation_s010_latest.json`
- Matrix rows: `73752`
- Matrix components: `227`
- Palette signals: `227`
- Supporting signals: `21`

## Summary

- Audited active signals: `227`
- Palette signals not in latest matrix: `0`
- Total concerns: `167`
- Severity counts: `high=34, medium=41, review=92`
- Category counts: `absence_encoded_as_zero=15, active_vs_palette_surface=1, admission_endpoint_hits_core_vocab=20, audit_limit=1, burden_not_priority=37, count_signal_semantics=18, coverage_denominator_mismatch=1, derived_from_collapsed_jlpt_level=5, frequency_scale_compression=1, jlpt_levels_compressed=2, jlpt_transform_layering=1, low_coverage=1, mostly_maxed_out=4, no_observed_variation=5, non_difficulty_polarity=15, supporting_not_active_component=15, topic_endpoint_hits_core_vocab=9, very_low_coverage=16`

## Concern Groups

| Category | Count | Example signals |
| --- | ---: | --- |
| `burden_not_priority` | 37 | `script_complexity`, `kanji_grade`, `kanji_frequency_rank`, `old_jlpt_kanji`, `stroke_count`, `kanjivg_visual_complexity`, `kanji_curriculum_burden`, `kanji_shape_burden`, ... +29 |
| `admission_endpoint_hits_core_vocab` | 20 | `jmdict_non_vocab_raw_class_score`, `jmnedict_name_risk`, `jmnedict_name_overlap`, `jmnedict_person_name_risk`, `jmnedict_person_name_overlap`, `jmnedict_place_name_risk`, `jmnedict_place_name_overlap`, `proper_noun_pos_risk`, ... +12 |
| `count_signal_semantics` | 18 | `jmdict_entry_count`, `jmdict_pos_count`, `jmdict_field_count`, `jmdict_kanji_form_count`, `jmdict_reading_form_count`, `jmdict_form_count`, `jmdict_gloss_count`, `jmdict_sense_count`, ... +10 |
| `very_low_coverage` | 16 | `lesson_vocab_difficulty`, `lesson_vocab_beginner_core`, `acronym_surface_confidence`, `acronym_mixed_code_confidence`, `acronym_spellout_reading`, `acronym_identity_gloss`, `acronym_expanded_gloss`, `acronym_japanese_specific_usage`, ... +8 |
| `absence_encoded_as_zero` | 15 | `jmdict_numeric_class`, `jmdict_function_discourse_class`, `jmdict_proper_noun_overlap`, `jmdict_register_marked_risk`, `jmdict_dialect_risk`, `jmdict_sinitic_source`, `jmdict_source_text_present`, `jmdict_source_type_marked`, ... +7 |
| `non_difficulty_polarity` | 15 | `frequency_ease`, `jlpt_vocab_beginner_core`, `lesson_vocab_beginner_core`, `acronym_surface_confidence`, `acronym_mixed_code_confidence`, `acronym_real_usage_confidence`, `acronym_japanese_specific_gate`, `entity_suppression_gate`, ... +7 |
| `supporting_not_active_component` | 15 | `jlpt_vocab_levels_raw`, `jlpt_vocab_easiest_level`, `jlpt_vocab_hardest_level`, `jlpt_vocab_source_count`, `jlpt_vocab_curve_grid`, `jlpt_vocab_n5_curve_value`, `jlpt_vocab_n4_curve_value`, `jlpt_vocab_n3_curve_value`, ... +7 |
| `topic_endpoint_hits_core_vocab` | 9 | `jmdict_register_marked_risk`, `jmdict_dialect_risk`, `jmdict_abbreviation_risk`, `jmdict_news_or_policy_domain_risk`, `jmdict_field_marked_risk`, `news_or_policy_topic_risk`, `jmdict_field_count`, `jmdict_register_domain_risk`, ... +1 |
| `derived_from_collapsed_jlpt_level` | 5 | `jlpt_vocab_is_n5`, `jlpt_vocab_is_n4`, `jlpt_vocab_is_n3`, `jlpt_vocab_is_n2`, `jlpt_vocab_is_n1` |
| `no_observed_variation` | 5 | `jmdict_proper_noun_overlap`, `acronym_mixed_code_confidence`, `acronym_default_suppress_risk`, `acronym_topic_only_risk`, `acronym_shared_exact_risk` |
| `mostly_maxed_out` | 4 | `acronym_surface_confidence`, `kanjidic_query_code_coverage`, `bccwj_rank_spread`, `bccwj_rank_variability` |
| `jlpt_levels_compressed` | 2 | `jlpt_vocab_difficulty`, `jlpt_vocab_beginner_core` |
| `active_vs_palette_surface` | 1 | `global` |
| `audit_limit` | 1 | `global` |
| `coverage_denominator_mismatch` | 1 | `global` |
| `frequency_scale_compression` | 1 | `frequency` |
| `jlpt_transform_layering` | 1 | `global` |
| `low_coverage` | 1 | `news_abbreviation_entity_risk` |

## Main Concerns

- **high** `admission_endpoint_hits_core_vocab` `jmdict_non_vocab_raw_class_score`: High admission/entity endpoint includes common normal-vocab rows: 居る/いる=1.0 (rank=13.0, state=normal_vocab); 有る/ある=1.0 (rank=15.0, state=normal_vocab); 成る/なる=1.0 (rank=23.0, state=normal_vocab); 来る/くる=1.0 (rank=46.0, state=normal_vocab); 見る/みる=1.0 (rank=49.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_name_overlap`: High admission/entity endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 人/ひと=1.0 (rank=64.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_name_risk`: High admission/entity endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 人/ひと=1.0 (rank=64.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_person_name_overlap`: High admission/entity endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 人/ひと=1.0 (rank=64.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_person_name_risk`: High admission/entity endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 人/ひと=1.0 (rank=64.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_place_name_overlap`: High admission/entity endpoint includes common normal-vocab rows: 成る/なる=1.0 (rank=23.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab); 市/し=1.0 (rank=105.0, state=normal_vocab); 今/いま=1.0 (rank=106.0, state=normal_vocab); 県/けん=1.0 (rank=140.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `jmnedict_place_name_risk`: High admission/entity endpoint includes common normal-vocab rows: 成る/なる=1.0 (rank=23.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab); 市/し=1.0 (rank=105.0, state=normal_vocab); 今/いま=1.0 (rank=106.0, state=normal_vocab); 県/けん=1.0 (rank=140.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `named_entity_overlap`: High admission/entity endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 成る/なる=1.0 (rank=23.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `ordinary_vocab_protection`: High admission/entity endpoint includes common normal-vocab rows: 居る/いる=1.0 (rank=13.0, state=normal_vocab); 有る/ある=1.0 (rank=15.0, state=normal_vocab); 事/こと=1.0 (rank=18.0, state=normal_vocab); 言う/いう=1.0 (rank=19.0, state=normal_vocab); 成る/なる=1.0 (rank=23.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `problem_class_proper_flag`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `problem_class_proper_risk`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_country_entity_overlap`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab); 米/べい=1.0 (rank=380.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_country_pos_flag`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_country_pos_risk`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_noun_pos_flag`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_noun_pos_risk`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_place_entity_overlap`: High admission/entity endpoint includes common normal-vocab rows: 成る/なる=1.0 (rank=23.0, state=normal_vocab); 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab); 市/し=1.0 (rank=105.0, state=normal_vocab); 今/いま=1.0 (rank=106.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_place_pos_flag`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `proper_place_pos_risk`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `admission_endpoint_hits_core_vocab` `wtype_proper_risk`: High admission/entity endpoint includes common normal-vocab rows: 日本/にっぽん=1.0 (rank=63.0, state=normal_vocab); 中国/ちゅうごく=1.0 (rank=258.0, state=normal_vocab); 米国/べいこく=1.0 (rank=288.0, state=normal_vocab). Check for name/entity overlap with ordinary vocabulary.
- **high** `no_observed_variation` `acronym_default_suppress_risk`: Signal has no endpoint variation in the latest matrix.
- **high** `no_observed_variation` `acronym_mixed_code_confidence`: Signal has no endpoint variation in the latest matrix.
- **high** `no_observed_variation` `acronym_shared_exact_risk`: Signal has no endpoint variation in the latest matrix.
- **high** `no_observed_variation` `acronym_topic_only_risk`: Signal has no endpoint variation in the latest matrix.
- **high** `no_observed_variation` `jmdict_proper_noun_overlap`: Signal has no endpoint variation in the latest matrix.
- **high** `topic_endpoint_hits_core_vocab` `bccwj_domain_rank_spread`: High endpoint includes common normal-vocab rows: 来る/くる=1.0 (rank=46.0, state=normal_vocab); 良い/よい=1.0 (rank=58.0, state=normal_vocab); 思う/おもう=1.0 (rank=62.0, state=normal_vocab); 何/なに=1.0 (rank=75.0, state=normal_vocab); つく/つく=1.0 (rank=79.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_abbreviation_risk`: High endpoint includes common normal-vocab rows: どう/どう=1.0 (rank=95.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab); そう/そう=1.0 (rank=110.0, state=normal_vocab); 社会/しゃかい=1.0 (rank=146.0, state=normal_vocab); 活動/かつどう=1.0 (rank=152.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_dialect_risk`: High endpoint includes common normal-vocab rows: 又/また=1.0 (rank=91.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab); 自分/じぶん=1.0 (rank=99.0, state=normal_vocab); 内/うち=1.0 (rank=223.0, state=normal_vocab); 強い/つよい=1.0 (rank=325.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_field_count`: High endpoint includes common normal-vocab rows: そう/そう=1.0 (rank=110.0, state=normal_vocab); こう/こう=1.0 (rank=195.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_field_marked_risk`: High endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 成る/なる=1.0 (rank=23.0, state=normal_vocab); 時/とき=1.0 (rank=84.0, state=normal_vocab); どう/どう=1.0 (rank=95.0, state=normal_vocab); 中/なか=1.0 (rank=96.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_news_or_policy_domain_risk`: High endpoint includes common normal-vocab rows: こう/こう=1.0 (rank=195.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_register_domain_risk`: High endpoint includes common normal-vocab rows: 事/こと=1.0 (rank=18.0, state=normal_vocab); 成る/なる=1.0 (rank=23.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); 時/とき=1.0 (rank=84.0, state=normal_vocab); 又/また=1.0 (rank=91.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `jmdict_register_marked_risk`: High endpoint includes common normal-vocab rows: 成る/なる=1.0 (rank=23.0, state=normal_vocab); 様/よう=1.0 (rank=39.0, state=normal_vocab); そう/そう=1.0 (rank=110.0, state=normal_vocab); 下さる/くださる=1.0 (rank=170.0, state=normal_vocab); 方/ほう=1.0 (rank=186.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **high** `topic_endpoint_hits_core_vocab` `news_or_policy_topic_risk`: High endpoint includes common normal-vocab rows: こう/こう=1.0 (rank=195.0, state=normal_vocab). This may be a broad priority/domain cue rather than true topic-only evidence.
- **medium** `audit_limit` `global`: The component matrix supports endpoint/value checks, but it does not carry all raw source evidence. JMDict/JMnedict/KANJIDIC/KanjiVG parser truth still needs source-backed spot checks for flagged endpoints.
- **medium** `derived_from_collapsed_jlpt_level` `jlpt_vocab_is_n1`: This audit can derive the gate from the stored easiest JLPT level only. Checking whether a raw multi-level record includes this level requires source metadata beyond the component matrix.
- **medium** `derived_from_collapsed_jlpt_level` `jlpt_vocab_is_n2`: This audit can derive the gate from the stored easiest JLPT level only. Checking whether a raw multi-level record includes this level requires source metadata beyond the component matrix.
- **medium** `derived_from_collapsed_jlpt_level` `jlpt_vocab_is_n3`: This audit can derive the gate from the stored easiest JLPT level only. Checking whether a raw multi-level record includes this level requires source metadata beyond the component matrix.
- **medium** `derived_from_collapsed_jlpt_level` `jlpt_vocab_is_n4`: This audit can derive the gate from the stored easiest JLPT level only. Checking whether a raw multi-level record includes this level requires source metadata beyond the component matrix.
- **medium** `derived_from_collapsed_jlpt_level` `jlpt_vocab_is_n5`: This audit can derive the gate from the stored easiest JLPT level only. Checking whether a raw multi-level record includes this level requires source metadata beyond the component matrix.
- **medium** `frequency_scale_compression` `frequency`: Median frequency difficulty is above 0.90 in the normalization matrix. Treat this as a corpus-rank/target-curve scale, not a literal human difficulty percentile.
- **medium** `jlpt_levels_compressed` `jlpt_vocab_beginner_core`: Active component compresses N5-N1 into one scalar. Individual JLPT level gates are derivable but not active component columns.
- **medium** `jlpt_levels_compressed` `jlpt_vocab_difficulty`: Active component compresses N5-N1 into one scalar. Individual JLPT level gates are derivable but not active component columns.
- **medium** `jlpt_transform_layering` `global`: The component matrix stores base `jlpt_vocab_difficulty` values, while the latest sweep may remap JLPT levels through `jlpt_vocab_curves`=[{'N1': 0.94, 'N2': 0.72, 'N3': 0.5, 'N4': 0.28, 'N5': 0.06}]. Auditing the base component alone does not prove the final candidate formula's transformed endpoints.
- **medium** `non_difficulty_polarity` `acronym_japanese_specific_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `acronym_mixed_code_confidence`: Signal kind is `evidence_confidence`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `acronym_real_usage_confidence`: Signal kind is `evidence_confidence`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `acronym_surface_confidence`: Signal kind is `evidence_confidence`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `bccwj_domain_rank_coverage`: Signal kind is `evidence_confidence`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `entity_suppression_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `frequency_ease`: Signal kind is `ease_or_beginner_anchor`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `jlpt_vocab_beginner_core`: Signal kind is `ease_or_beginner_anchor`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `kanjidic_query_code_coverage`: Signal kind is `evidence_confidence`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `lesson_vocab_beginner_core`: Signal kind is `ease_or_beginner_anchor`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `pos_adjective_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `pos_common_noun_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `pos_plain_verb_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `sahen_kango_ease_gate`: Signal kind is `gate`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `non_difficulty_polarity` `wtype_wago_ease`: Signal kind is `ease_or_beginner_anchor`; higher values should not be blindly treated as higher learner difficulty.
- **medium** `very_low_coverage` `acronym_default_suppress_risk`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_domain_concentration`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_expanded_gloss`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_identity_gloss`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_japanese_specific_gate`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_japanese_specific_usage`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_mixed_code_confidence`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_proper_name_risk`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_real_usage_confidence`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_shared_exact_risk`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_spellout_reading`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_surface_confidence`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `acronym_topic_only_risk`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `lesson_vocab_beginner_core`: Only 0.399% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `lesson_vocab_difficulty`: Only 0.399% of matrix rows have this signal; endpoint examples are fragile.
- **medium** `very_low_coverage` `proper_acronym_entity_risk`: Only 0.210% of matrix rows have this signal; endpoint examples are fragile.
- **review** `absence_encoded_as_zero` `jmdict_dialect_risk`: Binary-like full-coverage signal is almost always zero. Confirm that 0 means negative evidence rather than missing/unknown evidence.
- **review** `absence_encoded_as_zero` `jmdict_function_discourse_class`: Binary-like full-coverage signal is almost always zero. Confirm that 0 means negative evidence rather than missing/unknown evidence.
- **review** `absence_encoded_as_zero` `jmdict_numeric_class`: Binary-like full-coverage signal is almost always zero. Confirm that 0 means negative evidence rather than missing/unknown evidence.
- **review** `absence_encoded_as_zero` `jmdict_proper_noun_overlap`: Binary-like full-coverage signal is almost always zero. Confirm that 0 means negative evidence rather than missing/unknown evidence.
- **review** `absence_encoded_as_zero` `jmdict_register_marked_risk`: Binary-like full-coverage signal is almost always zero. Confirm that 0 means negative evidence rather than missing/unknown evidence.
- ... `87` more concerns are in the JSON/full audit artifact.

## Special Checks

- `jlpt_vocab_difficulty_by_level`: `{"1": [0.85], "2": [0.65], "3": [0.42], "4": [0.22], "5": [0.08]}`
- `jlpt_vocab_beginner_core_by_level`: `{"1": [0.0], "2": [0.1], "3": [0.35], "4": [0.75], "5": [1.0]}`
- `latest_sweep_jlpt_vocab_curves`: `[{"N1": 0.94, "N2": 0.72, "N3": 0.5, "N4": 0.28, "N5": 0.06}]`
- `jlpt_vocab_level_counts`: `{"1": 3089, "2": 1536, "3": 1725, "4": 562, "5": 615}`

## Endpoint Samples For Discussion

### `frequency`

| Endpoint | Examples |
| --- | --- |
| low | 居る/いる=0.139726 (rank=13.0, state=normal_vocab); 有る/ある=0.154413 (rank=15.0, state=normal_vocab); 言う/いう=0.170649 (rank=19.0, state=normal_vocab); 事/こと=0.178121 (rank=18.0, state=normal_vocab); 成る/なる=0.203406 (rank=23.0, state=normal_vocab) |
| median | 林木/りんぼく=0.971926 (rank=5551.0, state=normal_vocab); 持ち合う/もちあう=0.971926 (rank=9024.0, state=normal_vocab); フライ/ふらい=0.971926 (rank=12560.0, state=normal_vocab); プラ板/ぷらばん=0.971926 (rank=12560.0, state=normal_vocab); 雛豆/ひよこまめ=0.971926 (rank=12560.0, state=normal_vocab) |
| high | かむなび/かむなび=0.999118 (rank=23544.0, state=deprioritized_vocab); ごうごう/ごうごう=0.999118 (rank=23544.0, state=normal_vocab); ごふ/ごふ=0.999118 (rank=23544.0, state=normal_vocab); たむろう/たむろう=0.999118 (rank=23544.0, state=normal_vocab); どじっ娘/どじっこ=0.999118 (rank=23544.0, state=normal_vocab) |

### `jlpt_vocab_difficulty`

| Endpoint | Examples |
| --- | --- |
| low | 居る/いる=0.08 (rank=13.0, state=normal_vocab); 言う/いう=0.08 (rank=19.0, state=normal_vocab); 来る/くる=0.08 (rank=46.0, state=normal_vocab); 物/もの=0.08 (rank=52.0, state=normal_vocab); 行く/いく=0.08 (rank=57.0, state=normal_vocab) |
| median | 因る/よる=0.65 (rank=56.0, state=normal_vocab); 整備/せいび=0.65 (rank=141.0, state=normal_vocab); 対策/たいさく=0.65 (rank=165.0, state=normal_vocab); 年度/ねんど=0.65 (rank=172.0, state=normal_vocab); 森林/しんりん=0.65 (rank=310.0, state=normal_vocab) |
| high | 良い/よい=0.85 (rank=58.0, state=normal_vocab); 事業/じぎょう=0.85 (rank=107.0, state=normal_vocab); 仕舞う/しまう=0.85 (rank=110.0, state=normal_vocab); 遣る/やる=0.85 (rank=126.0, state=normal_vocab); 推進/すいしん=0.85 (rank=159.0, state=normal_vocab) |

### `jlpt_vocab_beginner_core`

| Endpoint | Examples |
| --- | --- |
| low | 良い/よい=0.0 (rank=58.0, state=normal_vocab); 事業/じぎょう=0.0 (rank=107.0, state=normal_vocab); 仕舞う/しまう=0.0 (rank=110.0, state=normal_vocab); 遣る/やる=0.0 (rank=126.0, state=normal_vocab); 推進/すいしん=0.0 (rank=159.0, state=normal_vocab) |
| median | 因る/よる=0.1 (rank=56.0, state=normal_vocab); 整備/せいび=0.1 (rank=141.0, state=normal_vocab); 対策/たいさく=0.1 (rank=165.0, state=normal_vocab); 年度/ねんど=0.1 (rank=172.0, state=normal_vocab); 森林/しんりん=0.1 (rank=310.0, state=normal_vocab) |
| high | 居る/いる=1.0 (rank=13.0, state=normal_vocab); 言う/いう=1.0 (rank=19.0, state=normal_vocab); 来る/くる=1.0 (rank=46.0, state=normal_vocab); 物/もの=1.0 (rank=52.0, state=normal_vocab); 行く/いく=1.0 (rank=57.0, state=normal_vocab) |

### `named_entity_risk`

| Endpoint | Examples |
| --- | --- |
| low | 居る/いる=0.0 (rank=13.0, state=normal_vocab); 有る/ある=0.0 (rank=15.0, state=normal_vocab); 事/こと=0.0 (rank=18.0, state=normal_vocab); 言う/いう=0.0 (rank=19.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab) |
| median | 居る/いる=0.0 (rank=13.0, state=normal_vocab); 有る/ある=0.0 (rank=15.0, state=normal_vocab); 事/こと=0.0 (rank=18.0, state=normal_vocab); 言う/いう=0.0 (rank=19.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab) |
| high | 平成/へいせい=1.0 (rank=123.0, state=deprioritized_vocab); 北朝鮮/きたちょうせん=1.0 (rank=462.0, state=deprioritized_vocab); イラク/いらく=1.0 (rank=549.0, state=deprioritized_vocab); アジア/あじあ=1.0 (rank=574.0, state=deprioritized_vocab); 昭和/しょうわ=1.0 (rank=574.0, state=deprioritized_vocab) |

### `news_or_policy_topic_risk`

| Endpoint | Examples |
| --- | --- |
| low | 事/こと=0.0 (rank=18.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab); 時/とき=0.0 (rank=84.0, state=normal_vocab); どう/どう=0.0 (rank=95.0, state=normal_vocab); 中/なか=0.0 (rank=96.0, state=normal_vocab) |
| median | 事/こと=0.0 (rank=18.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab); 時/とき=0.0 (rank=84.0, state=normal_vocab); どう/どう=0.0 (rank=95.0, state=normal_vocab); 中/なか=0.0 (rank=96.0, state=normal_vocab) |
| high | こう/こう=1.0 (rank=195.0, state=normal_vocab); 展開/てんかい=1.0 (rank=795.0, state=normal_vocab); 表示/ひょうじ=1.0 (rank=944.0, state=normal_vocab); ビル/びる=1.0 (rank=985.0, state=normal_vocab); 需要/じゅよう=1.0 (rank=1256.0, state=normal_vocab) |

### `max_written_form_burden`

| Endpoint | Examples |
| --- | --- |
| low | む/む=0.03125 (rank=23544.0, state=normal_vocab); あ/あ=0.03125 (rank=None, state=normal_vocab); ぐ/ぐ=0.03125 (rank=None, state=normal_vocab); け/け=0.03125 (rank=None, state=normal_vocab); じ/じ=0.03125 (rank=None, state=normal_vocab) |
| median | 無い/ない=0.5 (rank=29.0, state=normal_vocab); 対策/たいさく=0.5 (rank=165.0, state=normal_vocab); 人間/にんげん=0.5 (rank=278.0, state=normal_vocab); 買う/かう=0.5 (rank=294.0, state=normal_vocab); 結果/けっか=0.5 (rank=298.0, state=normal_vocab) |
| high | 驚く/おどろく=1.0 (rank=1440.0, state=normal_vocab); 襲う/おそう=1.0 (rank=2664.0, state=normal_vocab); 軈て/やがて=1.0 (rank=3087.0, state=normal_vocab); 鰹/かつお=1.0 (rank=4556.0, state=normal_vocab); 矢鱈/やたら=1.0 (rank=5331.0, state=normal_vocab) |

### `rare_wago_tail_risk`

| Endpoint | Examples |
| --- | --- |
| low | 居る/いる=0.0 (rank=13.0, state=normal_vocab); 有る/ある=0.0 (rank=15.0, state=normal_vocab); 事/こと=0.0 (rank=18.0, state=normal_vocab); 言う/いう=0.0 (rank=19.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab) |
| median | 居る/いる=0.0 (rank=13.0, state=normal_vocab); 有る/ある=0.0 (rank=15.0, state=normal_vocab); 事/こと=0.0 (rank=18.0, state=normal_vocab); 言う/いう=0.0 (rank=19.0, state=normal_vocab); 成る/なる=0.0 (rank=23.0, state=normal_vocab) |
| high | 白張り/しらはり=0.990306 (rank=23544.0, state=normal_vocab); 組み分ける/くみわける=0.990306 (rank=23544.0, state=normal_vocab); あやかり者/あやかりもの=0.990306 (rank=None, state=normal_vocab); かりこ/かりこ=0.990306 (rank=None, state=normal_vocab); しめじめ/しめじめ=0.990306 (rank=None, state=normal_vocab) |
