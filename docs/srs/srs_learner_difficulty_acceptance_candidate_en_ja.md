# en-ja Learner Difficulty Acceptance Candidate

Status: frozen working candidate for acceptance review, not runtime default
Recorded: 2026-06-21 JST

## Frozen Candidate

Candidate ID:

`srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0p34_ssfmrare_source_rank_gap_ssa0_ssamnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1`

Selection basis:

- Use the latest `jlpt_guard_refine` source-arbitration sidecar.
- Select the best holdout-balanced candidate, not the best calibration-only candidate.
- Treat JLPT exact surface+reading fixes as signal cleanup, but do not promote a JLPT-bound variant unless it wins acceptance review.

Latest metrics from `docs/test_outputs/srs_learner_difficulty_source_arbitration_jlpt_guard_refine_en_ja_latest.json`:

| Metric | Value |
| --- | ---: |
| Calibration balanced | `0.776952` |
| Holdout balanced | `0.887388` |
| Holdout pairwise | `0.881391` |
| Holdout MAE score | `0.910768` |

Reference holdout candidate for context:

| Candidate | Holdout balanced | Holdout pairwise | Holdout MAE score |
| --- | ---: | ---: | ---: |
| `rare_wago_curriculum_gap_probe` | `0.824374` | `0.851187` | `0.885574` |

## Frozen Inputs

- Source-arbitration report: `docs/test_outputs/srs_learner_difficulty_source_arbitration_jlpt_guard_refine_en_ja_latest.json`
- Source-arbitration summary: `docs/test_outputs/srs_learner_difficulty_source_arbitration_jlpt_guard_refine_en_ja_latest.md`
- Component matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz`
- Calibration matrix: `docs/test_outputs/srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_calibration_matrix_latest.npz`

## Acceptance Review Pack

Focused first-60-percent review pack:

- JSON: `docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.json`
- Markdown: `docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.md`

Review scope:

- Predicted score bands through the current candidate's 60th-percentile score cutoff.
- Current 60th-percentile cutoff: `0.7074947953224182`.
- Rows covered by that cutoff: `44,251 / 73,752`.
- Labeled rows where either expected score or observed candidate score is at or below the cutoff.
- Suspect buckets restricted to rows scored at or below the cutoff.

Generated command:

```bash
python3 scripts/testing/srs_learner_difficulty_current_best_band_review_en_ja.py \
  --combo-json docs/test_outputs/srs_learner_difficulty_source_arbitration_jlpt_guard_refine_en_ja_latest.json \
  --review-max-score 0.7074947953224182 \
  --sample-count 16 \
  --detail-limit 24 \
  --json-out docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.md
```

## Blocker Review Rule

During acceptance review, mark a row or pattern as a blocker only when it is:

- clearly wrong for learner presentation priority;
- likely to affect ordinary users before or around N1-level vocabulary;
- recurring or source-explainable, not a one-off taste dispute;
- fixable without destabilizing a larger band.

Everything else should be recorded as accepted noise or deferred tail work.
