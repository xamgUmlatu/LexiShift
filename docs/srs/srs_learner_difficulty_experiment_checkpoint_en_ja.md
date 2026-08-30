# en-ja Learner Difficulty Experiment Checkpoint

Status: working checkpoint for reversible experiments, not runtime default
Recorded: 2026-06-23 JST

This note exists to keep the current best-known ranking state easy to recover
while we test more aggressive rare-reading and JMDict-priority repairs. New
model-shape experiments should be generated as sidecars and compared back to
this checkpoint unless we explicitly promote a new candidate.

## Return-To Checkpoint

Use this candidate as the current stable comparison anchor:

`srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0_s2fmnone_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_ccrc0p34_ccrmsoft_ccrs1_ccbl0p8_ccbu0p94_cctl0p6_cctu0p82_ccccsqrt_ccgtyped_nonkango_life_ccbs0p8_ccbbl0p9_ccbbu0p96_ccbtll0p72_ccbtu0p84_ccbrl0p88_ccbru0p98_ccskl0p62_ccsku0p88`

Artifact:

- `docs/test_outputs/srs_learner_difficulty_source_arbitration_cross_corpus_typed_rescue_refine_warp_p60_g155_en_ja_latest.json`
- `docs/test_outputs/srs_learner_difficulty_source_arbitration_cross_corpus_typed_rescue_refine_warp_p60_g155_en_ja_latest.md`

Inputs:

- Component matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz`
- Calibration matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_calibration_matrix_latest.npz`
- Calibration labels: `docs/test_inputs/srs_learner_difficulty_calibration_en_ja.json`
- Holdout labels: `docs/test_inputs/srs_learner_difficulty_holdout_en_ja.json`
- Holdout review: `docs/test_outputs/srs_learner_difficulty_holdout_review_en_ja.md`
- Target curve override: `warp_p60_g155`

Metrics:

| Metric | Value |
| --- | ---: |
| Calibration balanced | `0.802344` |
| Holdout balanced | `0.928380` |
| Holdout pairwise | `0.912734` |
| Holdout MAE score | `0.925556` |
| Holdout bucket accuracy | `0.783133` |
| Holdout rank correlation | `0.965081` |

## Latest Experimental Sidecar

The latest JMDict-priority guard sidecar is not promoted. It is useful evidence
that same-surface priority pollution is real, but it includes a blunt floor that
needs more review before becoming a product shape.

Candidate:

`srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p84_s2fmunranked_priority_pollution_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_ccrc0p34_ccrmsoft_ccrs1_ccbl0p8_ccbu0p94_cctl0p6_cctu0p82_ccccsqrt_ccgtyped_nonkango_life_ccbs0p8_ccbbl0p9_ccbbu0p96_ccbtll0p72_ccbtu0p84_ccbrl0p88_ccbru0p98_ccskl0p62_ccsku0p88_jpgmmarked_jpgs0p35_jpgos0_jpgcsmoothstep_jpgpr1`

Artifact:

- `docs/test_outputs/srs_learner_difficulty_source_arbitration_jmdict_priority_guard_refine_warp_p60_g155_en_ja_latest.json`
- `docs/test_outputs/srs_learner_difficulty_source_arbitration_jmdict_priority_guard_refine_warp_p60_g155_en_ja_latest.md`

Metric comparison against the return-to checkpoint:

| Metric | Return-to checkpoint | JMDict sidecar | Delta |
| --- | ---: | ---: | ---: |
| Holdout balanced | `0.928380` | `0.928475` | `+0.000095` |
| Holdout pairwise | `0.912734` | `0.913045` | `+0.000311` |
| Holdout MAE score | `0.925556` | `0.925831` | `+0.000275` |
| Holdout bucket accuracy | `0.783133` | `0.771084` | `-0.012049` |
| Holdout rank correlation | `0.965081` | `0.966311` | `+0.001230` |

Observed lesson:

- The target signal is real: rows such as `郡/こおり`, `外国/とつくに`, and
  `誘う/いざなう` are too easy when an easier same-surface reading lends them
  JMDict priority or broad pedagogical evidence.
- The sidecar repair is too blunt: the largest visible moves come from a
  post-base floor, not from a clean source-trust rewrite.
- The current core product concern is not the tiny metric delta. It is keeping
  obscure/marked forms such as `而して/しこうして` out of JLPT-ish presentation
  ranges without raising ordinary learner vocabulary.

## Regression Control Rules

- Do not overwrite the return-to checkpoint artifacts during exploratory model
  work.
- Add new ideas as separate candidate families or clearly named sidecar
  artifacts.
- Compare every new sidecar to the return-to checkpoint, not only to the
  immediately previous experiment.
- Track both aggregate metrics and focus-row movements for rare/marked forms.
- Treat a better global holdout score as insufficient if the first-60-percent
  qualitative review gets worse.
- Promote only after the mechanism is explainable in source-trust terms, not
  merely because a floor happens to improve one labeled slice.

## Next Hypotheses To Test

Primary target:

- Keep marked, obscure, or archaic readings out of JLPT-ish range, especially
  cases like `而して/しこうして`, without destabilizing normal N5-N1 vocabulary.

Candidate model shapes:

1. Source-trust rewrite for JMDict priority:
   replace `J = 1 - priority` with `J_eff = blend(J, mean(F, T), B_native)`,
   where `B_native` is high only when JMDict priority conflicts with corpus
   difficulty, same-surface rank evidence, or marked-reading evidence.

2. Pedagogical-source attenuation for family-only readings:
   when broad/surface JLPT evidence exists but exact reading evidence is absent,
   reduce or remove that pedagogical evidence for rows with strong same-surface
   pollution risk.

3. Corpus-shaped rare-reading floor:
   replace fixed floors such as `0.84 * risk` with a floor shaped by corpus
   difficulty, for example `risk * f(mean(F, T))`, so all rare readings do not
   collapse to the same score.

4. Marked-reading minimum outside JLPT-ish range:
   test a narrow floor for rows with strong `reading_form_source_strength` or
   `rare_reading_form_strength`, but rescue rows with exact JLPT or lesson
   evidence. This directly targets forms such as `而して/しこうして`.

Open decision:

- Whether the first promoted repair should be narrow and surgical
  (marked-reading floor/attenuation) or a more general source-trust rewrite.
  The safer first test is the narrow version because it more directly targets
  the failure class we currently care about.
