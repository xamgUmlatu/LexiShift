# en-ja Source-Arbitration Learner-Difficulty Search

Status: generated sidecar experiment
Generated: `2026-06-23T21:34:46Z`

## Method

base = source-arbitrated pedagogical/native spine; burden, entity, topic, optional same-surface alternate-reading floors, and optional same-surface source attenuation are gated and bounded.

## Inputs

- Component matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz`
- Calibration matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_calibration_matrix_latest.npz`
- Calibration labels: `docs/test_inputs/srs_learner_difficulty_calibration_en_ja.json`
- Holdout review: `docs/test_outputs/srs_learner_difficulty_holdout_review_en_ja.md`
- Holdout labels: `docs/test_inputs/srs_learner_difficulty_holdout_en_ja.json`
- Component count: `73752`
- Signal count: `307`
- Candidate count: `2`
- Target curve override: `warp_p60_g155`

## Best Candidates

| View | Candidate | Calibration balanced | Holdout balanced | Holdout pairwise | Holdout MAE score | Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Best holdout | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap` | 0.800838 | 0.914576 | 0.899363 | 0.914376 | 0.113738 |
| Best calibration | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0_bfrs0_bfrgnone` | 0.800838 | 0.913207 | 0.897769 | 0.912863 | 0.112369 |
| Reference holdout | `` |  |  |  |  |  |

## Holdout Leaderboard

| Rank | Candidate | Calibration balanced | Holdout balanced | Pairwise | Params |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap` | 0.800838 | 0.914576 | 0.899363 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |
| 2 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0_bfrs0_bfrgnone` | 0.800838 | 0.913207 | 0.897769 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |

## Guardrail Leaderboard

Requires holdout pairwise >= `0.88`, beginner-core >= `0.9`, and high-tail >= `0.5`.

| Rank | Candidate | Calibration balanced | Holdout balanced | Pairwise | Params |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap` | 0.800838 | 0.914576 | 0.899363 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |
| 2 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0_bfrs0_bfrgnone` | 0.800838 | 0.913207 | 0.897769 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |

## Calibration Leaderboard

| Rank | Candidate | Calibration balanced | Holdout balanced | Pairwise | Params |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0_bfrs0_bfrgnone` | 0.800838 | 0.913207 | 0.897769 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |
| 2 | `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap` | 0.800838 | 0.914576 | 0.899363 | `ped_mode=min,native_mode=mean,base_mode=ped_native_min,ped_strength=1.0,tail_source=base,tail_lower=0.5,tail_upper=0.85,burden_mode=mean,burden_delta=0.05,entity_delta=0.0,entity_gate_mode=weak,topic_delta=0.0,topic_gate_mode=rarity,ordinary_cap=0.58,ordinary_cap_mode=hard,ordinary_cap_strength=1.0,ordinary_gate_mode=mean,ordinary_gate_curve=linear,ordinary_exception_mode=current,ordinary_exception_curve=linear,reading_guard_delta=0.0,tail_floor=0.0,tail_floor_mode=none,same_surface_floor=0.0,same_surface_floor_mode=none,same_surface_source_attenuation=0.0,same_surface_source_attenuation_mode=none,same_surface_secondary_floor=0.42,same_surface_secondary_floor_mode=pedagogical_family_only_rare_pollution_unprotected_exact,same_surface_gradient_low_floor=0.0,same_surface_gradient_high_floor=0.0,same_surface_gradient_mode=none,same_surface_gradient_curve=linear,same_surface_gradient_commonness_cap=0.0,same_surface_gradient_lesson_rescue=0.0,same_surface_gradient_marked_boost=0.0,gairaigo_source_delta=0.05,gairaigo_source_gate_mode=marked_rarity,gairaigo_english_ease_delta=0.04,gairaigo_english_ease_mode=english_freq,gairaigo_jlpt_raise_block=False,jlpt_bound_mode=none,jlpt_bound_margin=0.0,jlpt_bound_strength=1.0,jmdict_priority_source=legacy,jmdict_pair_safe_blend=1.0,pair_leak_ped_gate_mode=none,pair_leak_ped_adjustment_mode=none,pair_leak_ped_strength=0.0,pair_leak_ped_floor=0.0,pair_leak_ped_curve=linear` |

## Detailed Samples

### `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap`

- Calibration balanced: `0.800838`
- Holdout balanced: `0.914576`
- Generalization delta: `0.113738`

Largest holdout errors:

| Label | Expected | Observed | Error | Direction |
| --- | ---: | ---: | ---: | --- |
| 耐え凌ぐ/たえしのぐ | 0.55 | 0.93065 | 0.38065 | too_high |
| 郡/こおり | 0.82 | 0.461136 | 0.358864 | too_low |
| セル画/せるが | 0.6 | 0.912157 | 0.312157 | too_high |
| 卵焼き/たまごやき | 0.2 | 0.511248 | 0.311248 | too_high |
| 筋トレ/きんとれ | 0.28 | 0.580445 | 0.300445 | too_high |
| 而して/しこうして | 0.8 | 0.505951 | 0.294049 | too_low |
| 鋸/のこぎり | 0.65 | 0.423068 | 0.226932 | too_low |
| 歴遊/れきゆう | 0.7 | 0.925342 | 0.225342 | too_high |

Band samples:

| Band | Count | Samples |
| --- | ---: | --- |
| 0.00-0.05 | 111 | 先生/せんせい (0.000225); 分かる/わかる (0.010135); 上/うえ (0.020045); 今日/きょう (0.029955); 次/つぎ (0.039865); 水/みず (0.049775) |
| 0.05-0.10 | 309 | 乗る/のる (0.050085); 電気/でんき (0.060424); 困る/こまる (0.070085); 毎年/まいとし (0.079576); 要る/いる (0.089576); 妹/いもうと (0.099915) |
| 0.10-0.15 | 620 | 涼しい/すずしい (0.100042); おおい/おおい (0.110127); ダンス/だんす (0.120212); 予定/よてい (0.130297); 落ちる/おちる (0.139958); 包む/つつむ (0.149958) |
| 0.15-0.20 | 910 | 日記/にっき (0.150028); 電灯/でんとう (0.160028); クリック/くりっく (0.170367); 施設/しせつ (0.18048); エアー/えあー (0.190367); 記事/きじ (0.199972) |
| 0.20-0.25 | 1205 | 殺す/ころす (0.200021); クライアント/くらいあんと (0.209852); パレスチナ/ぱれすちな (0.219852); 作用/さよう (0.229852); 終える/おえる (0.240021); 浴びる/あびる (0.249979) |
| 0.25-0.30 | 1636 | 犯人/はんにん (0.250015); 乗客/じょうきゃく (0.260096); 咳/せき (0.270022); ダイナミック/だいなみっく (0.28004); 転換/てんかん (0.290089); リベラル/りべらる (0.299985) |
| 0.30-0.35 | 2223 | 慌てる/あわてる (0.300011); 拒否/きょひ (0.309998); スパン/すぱん (0.319939); 唱える/となえる (0.329925); 非難/ひなん (0.339957); 上限/じょうげん (0.349989) |
| 0.35-0.40 | 2952 | 領土/りょうど (0.350008); 麻痺/まひ (0.359992); 見極める/みきわめる (0.369992); トリニトロトルエン/とりにとろとるえん (0.379975); 平方/へいほう (0.389941); 卸売り/おろしうり (0.399992) |
| 0.40-0.45 | 3689 | ビジター/びじたー (0.400007); ひっそり/ひっそり (0.410026); 命題/めいだい (0.420045); 攻防/こうぼう (0.430037); 思い遣る/おもいやる (0.440001); 例題/れいだい (0.449993) |
| 0.45-0.50 | 4412 | 法要/ほうよう (0.450006); 受け持つ/うけもつ (0.459983); 双/そう (0.46996); 思い止まる/おもいとどまる (0.479949); 陣中/じんちゅう (0.489983); 班長/はんちょう (0.499994) |
| 0.50-0.55 | 5151 | 入閣/にゅうかく (0.500005); 簿記/ぼき (0.510009); ウオン/うおん (0.520051); メタセコイア/めたせこいあ (0.530036); 激烈/げきれつ (0.54002); 盗作/とうさく (0.549995) |
| 0.55-0.60 | 5881 | 満身/まんしん (0.550004); 同朋/どうほう (0.55997); 泣き所/なきどころ (0.569953); ぶす/ぶす (0.579979); があん/があん (0.589987); 解き放つ/ときはなつ (0.599996) |
| 0.60-0.65 | 4360 | 連星/れんせい (0.600006); 取って置き/とっておき (0.61021); 除染/じょせん (0.620331); 案山子/かかし (0.630313); 青葱/あおねぎ (0.640222); ちんと/ちんと (0.649991) |
| 0.65-0.70 | 4870 | シアノバクテリア/しあのばくてりあ (0.650002); 粗々/あらあら (0.660787); 混交/こんこう (0.671452); 位田/いでん (0.681307); 円座/えんざ (0.690719); ぎょろぎょろ/ぎょろぎょろ (0.699992) |
| 0.70-0.75 | 5506 | 甘茶/あまちゃ (0.700002); 天衣/てんい (0.710375); 頑迷/がんめい (0.720599); タオルケット/たおるけっと (0.730728); カントリー/かんとりー (0.740743); コルベット/こるべっと (0.749997) |
| 0.75-0.80 | 6423 | 震わす/ふるわす (0.750005); 水こぼし/みずこぼし (0.760301); 合わせ技/あわせわざ (0.770459); 国父/こくふ (0.780452); 引き開ける/ひきあける (0.790286); 岳父/がくふ (0.799996) |
| 0.80-0.85 | 7566 | 島人/しまびと (0.800004); 内命/ないめい (0.810886); 澗/かん (0.820979); サミング/さみんぐ (0.83086); 当たり鉢/あたりばち (0.840541); 打ち見る/うちみる (0.849999) |
| 0.85-0.90 | 7569 | 承引/しょういん (0.850005); トランスアミナーゼ/とらんすあみなーぜ (0.859286); 帆綱/ほづな (0.869318); 春暖/しゅんだん (0.879872); 手戻り/てもどり (0.89008); 俗文/ぞくぶん (0.899995) |
| 0.90-0.95 | 6004 | 俗歌/ぞっか (0.900001); 苗圃/びょうほ (0.907618); 全癒/ぜんゆ (0.916706); 県史/けんし (0.928484); パルファン/ぱるふぁん (0.939584); セロハン/せろはん (0.949994) |
| 0.95-1.00 | 2355 | セントポーリア/せんとぽーりあ (0.950002); パッカー/ぱっかー (0.954944); マスコン/ますこん (0.965822); 吾妹/わぎも (0.975608); 猿猴/えんこう (0.984402); 鼹鼠/うごろもち (1.0) |

Moved earlier vs frequency:

| Word | Model | Frequency | Delta |
| --- | ---: | ---: | ---: |
| 居/い | 0.061577 | 0.990731 | -0.929154 |
| 分かり/わかり | 0.070135 | 0.999118 | -0.928983 |
| 何程/なにほど | 0.065631 | 0.983041 | -0.91741 |
| 同じい/おなじい | 0.084099 | 0.989141 | -0.905042 |
| 置き/おき | 0.078694 | 0.976626 | -0.897932 |
| 大き/おおき | 0.081847 | 0.977317 | -0.89547 |
| なな/なな | 0.110636 | 0.999118 | -0.888482 |
| みず/みず | 0.110805 | 0.998244 | -0.887439 |

Moved later vs frequency:

| Word | Model | Frequency | Delta |
| --- | ---: | ---: | ---: |
| ファー/ふぁー | 0.936739 | 0.831283 | 0.105456 |
| ピー/ぴー | 0.937982 | 0.845871 | 0.092111 |
| ノット/のっと | 0.952992 | 0.860988 | 0.092004 |
| ワルツ/わるつ | 0.972341 | 0.88324 | 0.089101 |
| 弥陀/みだ | 0.978837 | 0.893889 | 0.084948 |
| リューマチ/りゅーまち | 0.936994 | 0.856924 | 0.08007 |
| プログラミング/ぷろぐらみんぐ | 0.936985 | 0.8602 | 0.076785 |
| 御座る/ござる | 0.493384 | 0.418395 | 0.074989 |
### `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0_bfrs0_bfrgnone`

- Calibration balanced: `0.800838`
- Holdout balanced: `0.913207`
- Generalization delta: `0.112369`

Largest holdout errors:

| Label | Expected | Observed | Error | Direction |
| --- | ---: | ---: | ---: | --- |
| 耐え凌ぐ/たえしのぐ | 0.55 | 0.93065 | 0.38065 | too_high |
| 郡/こおり | 0.82 | 0.461136 | 0.358864 | too_low |
| セル画/せるが | 0.6 | 0.912157 | 0.312157 | too_high |
| 卵焼き/たまごやき | 0.2 | 0.511248 | 0.311248 | too_high |
| 筋トレ/きんとれ | 0.28 | 0.580445 | 0.300445 | too_high |
| 而して/しこうして | 0.8 | 0.505951 | 0.294049 | too_low |
| 翻って/ひるがえって | 0.6 | 0.851604 | 0.251603 | too_high |
| 鋸/のこぎり | 0.65 | 0.423068 | 0.226932 | too_low |

Band samples:

| Band | Count | Samples |
| --- | ---: | --- |
| 0.00-0.05 | 111 | 先生/せんせい (0.000225); 分かる/わかる (0.010135); 上/うえ (0.020045); 今日/きょう (0.029955); 次/つぎ (0.039865); 水/みず (0.049775) |
| 0.05-0.10 | 295 | 乗る/のる (0.050085); 忘れる/わすれる (0.059915); 絵/え (0.069915); 紙/かみ (0.079915); 並べる/ならべる (0.089915); 妹/いもうと (0.099915) |
| 0.10-0.15 | 590 | 涼しい/すずしい (0.100042); 陸/りく (0.109958); 趣味/しゅみ (0.119958); 進む/すすむ (0.129958); 落ちる/おちる (0.139958); 包む/つつむ (0.149958) |
| 0.15-0.20 | 885 | 日記/にっき (0.150028); 見物/みもの (0.159972); 県/けん (0.169972); ローン/ろーん (0.179972); 過去/かこ (0.189972); 記事/きじ (0.199972) |
| 0.20-0.25 | 1180 | 殺す/ころす (0.200021); シーズン/しーずん (0.209979); ボウル/ぼうる (0.219979); セラー/せらー (0.229979); ミラー/みらー (0.239979); 浴びる/あびる (0.249979) |
| 0.25-0.30 | 1622 | 犯人/はんにん (0.250015); スケート/すけーと (0.260003); 命/めい (0.269991); キャラクター/きゃらくたー (0.279978); ヘルシー/へるしー (0.289966); リベラル/りべらる (0.299985) |
| 0.30-0.35 | 2213 | 慌てる/あわてる (0.300011); 拒否/きょひ (0.309998); レトリック/れとりっく (0.319984); 臨時/りんじ (0.329993); ニューロン/にゅーろん (0.33998); 上限/じょうげん (0.349989) |
| 0.35-0.40 | 2950 | 領土/りょうど (0.350008); 麻痺/まひ (0.359992); 見極める/みきわめる (0.369992); トレッカー/とれっかー (0.379992); 出番/でばん (0.389992); 卸売り/おろしうり (0.399992) |
| 0.40-0.45 | 3688 | ビジター/びじたー (0.400007); 起用/きよう (0.409999); 拠出/きょしゅつ (0.419991); 最長/さいちょう (0.429996); 疑わしい/うたがわしい (0.439988); 例題/れいだい (0.449993) |
| 0.45-0.50 | 4425 | 法要/ほうよう (0.450006); 見分け/みわけ (0.459994); 縦書き/たてがき (0.469994); 駅長/えきちょう (0.479994); ふわ/ふわ (0.489994); 班長/はんちょう (0.499994) |
| 0.50-0.55 | 5163 | 入閣/にゅうかく (0.500005); 金銀/きんぎん (0.509999); 垣間見る/かいまみる (0.519993); 迎え打つ/むかえうつ (0.529997); 加勢/かせい (0.539991); 盗作/とうさく (0.549995) |
| 0.55-0.60 | 5900 | 満身/まんしん (0.550004); 曾孫/ひこ (0.559996); 焼け残る/やけのこる (0.569996); スライム/すらいむ (0.579996); ああん/ああん (0.589996); 解き放つ/ときはなつ (0.599996) |
| 0.60-0.65 | 4383 | 連星/れんせい (0.600006); 赤紫/あかむらさき (0.610187); 平伏す/ひれふす (0.620274); 孵す/かえす (0.630279); がめる/がめる (0.640177); ちんと/ちんと (0.649991) |
| 0.65-0.70 | 4874 | シアノバクテリア/しあのばくてりあ (0.650002); 粗々/あらあら (0.660787); 怒り狂う/いかりくるう (0.671463); 愛息/あいそく (0.681288); 大君/たいくん (0.69069); ぎょろぎょろ/ぎょろぎょろ (0.699992) |
| 0.70-0.75 | 5507 | 甘茶/あまちゃ (0.700002); 急き立てる/せきたてる (0.710384); ファンタ/ふぁんた (0.720636); 重砲/じゅうほう (0.730756); カントリー/かんとりー (0.740743); コルベット/こるべっと (0.749997) |
| 0.75-0.80 | 6426 | 震わす/ふるわす (0.750005); 当てずっぽう/あてずっぽう (0.760317); いかなご/いかなご (0.770475); 赤恥/あかはじ (0.780475); 教条/きょうじょう (0.790316); 岳父/がくふ (0.799996) |
| 0.80-0.85 | 7584 | 島人/しまびと (0.800004); 僧寺/そうじ (0.810859); 満ち干/みちひ (0.820946); コントラクト/こんとらくと (0.830828); 引き去る/ひきさる (0.840516); 打ち見る/うちみる (0.849999) |
| 0.85-0.90 | 7579 | 承引/しょういん (0.850005); デヒドロゲナーゼ/でひどろげなーぜ (0.859268); 巷談/こうだん (0.869303); 明け離れる/あけはなれる (0.879851); 手擦れ/てずれ (0.890087); 俗文/ぞくぶん (0.899995) |
| 0.90-0.95 | 6018 | 俗歌/ぞっか (0.900001); 苗頭/びょうとう (0.907624); 全労/ぜんろう (0.916676); 直電/ちょくでん (0.928446); パピヨン/ぱぴよん (0.939557); セロハン/せろはん (0.949994) |
| 0.95-1.00 | 2359 | セントポーリア/せんとぽーりあ (0.950002); パックス/ぱっくす (0.954968); マズルカ/まずるか (0.965866); 吾殿/わどの (0.975627); 猿猴/えんこう (0.984402); 鼹鼠/うごろもち (1.0) |

Moved earlier vs frequency:

| Word | Model | Frequency | Delta |
| --- | ---: | ---: | ---: |
| なな/なな | 0.110636 | 0.999118 | -0.888482 |
| みず/みず | 0.110805 | 0.998244 | -0.887439 |
| 西/せい | 0.112161 | 0.999118 | -0.886957 |
| きろ/きろ | 0.112839 | 0.999118 | -0.886279 |
| 家/や | 0.111398 | 0.997379 | -0.885981 |
| へた/へた | 0.113517 | 0.999118 | -0.885601 |
| キロ/きろ | 0.113941 | 0.999118 | -0.885177 |
| 毎年/まいねん | 0.102585 | 0.987578 | -0.884993 |

Moved later vs frequency:

| Word | Model | Frequency | Delta |
| --- | ---: | ---: | ---: |
| ファー/ふぁー | 0.936739 | 0.831283 | 0.105456 |
| ピー/ぴー | 0.937982 | 0.845871 | 0.092111 |
| ノット/のっと | 0.952992 | 0.860988 | 0.092004 |
| ワルツ/わるつ | 0.972341 | 0.88324 | 0.089101 |
| 弥陀/みだ | 0.978837 | 0.893889 | 0.084948 |
| リューマチ/りゅーまち | 0.936994 | 0.856924 | 0.08007 |
| プログラミング/ぷろぐらみんぐ | 0.936985 | 0.8602 | 0.076785 |
| 御座る/ござる | 0.493384 | 0.418395 | 0.074989 |
