# en-ja Learner Difficulty Acceptance Candidate

Status: packaged en-ja SRS learner-difficulty resource for product acceptance review
Recorded: 2026-06-30 JST

## Final Ranking Candidate

Final overlay variant ID:

`exgate_orth_ec06_fl044_fh058_mr022_xcr0_ts04_te06_sp05`

Base source-arbitration candidate ID:

`srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap`

Final ranking artifacts:

- Manual correction layer: `docs/test_inputs/srs_learner_difficulty_manual_corrections_en_ja.json`
- Packaged runtime CSV ranking: `core/lexishift_core/resources/srs/en_ja/learner_difficulty_corrected.csv`
- Packaged runtime correction metadata: `core/lexishift_core/resources/srs/en_ja/learner_difficulty_manual_corrections.json`
- Corrected first-200/manual-watchlist review JSON: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_review_en_ja_latest.json`
- Corrected first-200/manual-watchlist review Markdown: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_review_en_ja_latest.md`
- Full-range sample review Markdown: `docs/test_outputs/srs_learner_difficulty_full_range_sample_review_en_ja_latest.md`
- JMDict family admission review Markdown: `docs/test_outputs/srs_learner_difficulty_jmdict_family_admission_review_en_ja_latest.md`
- First-200 agent review: `docs/test_outputs/srs_learner_difficulty_first200_agent_review_en_ja_latest.md`
- Early flagged review through score `0.20`: `docs/test_outputs/srs_learner_difficulty_early_flagged_review_en_ja_latest.md`
- Product admission acceptance pack: `docs/test_outputs/srs_admission_product_acceptance_en_ja_latest.md`
- Product full-range sample pack: `docs/test_outputs/srs_learner_difficulty_product_full_range_sample_en_ja_latest.md`

Latest final-ranking sidecar metrics:

| Metric | Value |
| --- | ---: |
| Selection score | `0.616400` |
| MAE | `0.129196` |
| Pairwise accuracy | `0.844103` |
| Bucket accuracy | `0.716157` |
| Improved/regressed labels >=0.01 | `45 / 1` |
| Manual correction rows | `152` |
| Active/review/watch correction rows | `147 / 3 / 2` |

First-100 review notes:

- The first `100` exact-score rows are broadly coherent as an early learner
  pool.
- The main remaining texture is written-form presentation, not scalar placement:
  many early rows are flagged as kana-preferred kanji forms, but the corrected
  ranking can now carry display-form metadata for accepted cases such as
  `居る/いる` -> `いる`, `何処/どこ` -> `どこ`, `成る/なる` -> `なる`,
  `所/ところ` -> `ところ`, and `奇麗/きれい` -> `きれい`.
- The manual correction layer removes the reviewed first-page/first-200
  outliers without changing the model formula itself. Active score floors now
  cover rows such as `ワイシャツ/わいしゃつ`, `居る/おる`, `後/ご`, `道/どう`,
  `前/ぜん`, `村/そん`, `下/もと`, `明日/あす`, `来たる/きたる`, and
  `良い/よい`. The correction layer also supports direct score overrides for
  cross-row presentation fixes such as promoting `いい/いい`, and standalone
  admission exclusion for overloaded kana rows such as `つく/つく`.
- The latest compound-leak cleanup adds active admission routing for reviewed
  on-reading/component rows such as `火/か`, `西/せい`, `東/とう`, `訳/やく`,
  `北/ほく`, `見/けん`, `朝/ちょう`, `地/じ`, `徒/と`, `密/みつ`, and
  `印/いん`; it also adds small floors for `半/はん`, `門/もん`, `角/かく`,
  and `用/よう`.
- The final small sample queue now has active corrections for `必用/ひつよう`,
  `市/いち`, `山/さん`, and `高/こう`, plus admission routing for the sampled
  vulgar/adult tail row. These are treated as manual/content-polish decisions,
  not as evidence for another model-shape search.
- The scalar matrix is not a complete first-lesson curriculum by itself. In the
  final export, ultra-basic kana items such as `私/わたし`, `これ`, `それ`, and
  `彼/かれ` are absent while some kanji/literary variants are present. Runtime
  promotion should verify that seed/admission inventory supplies these basics
  through another lane before relying on the ranking alone.
- Manual review rows such as `吐く/つく`, `時々/じじ`, and `何人/なにびと`
  remain outside the first `100` and are tracked in the correction JSON as
  review/admission-routing candidates rather than active score overrides.
- The first-200 and early-flagged reviews found a compact but real polish queue.
  The largest reviewed score problems now have active sidecar corrections; the
  remaining early-band work is mostly display policy, admission routing, and
  manually reviewing a small number of rare readings or compound-only readings
  before runtime promotion.

## Compound-Leak Closure

The guarded compound-leak sidecar is now treated as a closed review pass for
the current candidate, not as an automatic model overlay. It found a useful
source-computable pattern: rows whose direct surface+reading support is
overstated by heavy usage inside compounds.

Current artifacts:

- Guard probe: `docs/test_outputs/srs_learner_difficulty_compound_leak_guard_probe_en_ja_latest.md`
- Candidate review: `docs/test_outputs/srs_learner_difficulty_compound_leak_candidate_review_en_ja_latest.md`
- Broad audit: `docs/test_outputs/srs_learner_difficulty_standalone_independence_broad_audit_en_ja_latest.md`

Accepted from this pass:

- Restrict/admission-route: `火/か`, `西/せい`, `東/とう`, `訳/やく`,
  `北/ほく`, `見/けん`, `朝/ちょう`, `地/じ`, `徒/と`, `密/みつ`,
  `印/いん`.
- Add floors: `半/はん` -> `0.10`, `門/もん` -> `0.13`,
  `角/かく` -> `0.14`, `用/よう` -> `0.19`.

Intentional non-actions:

- Keep `縁/えん` and `陸/りく` as normal vocabulary.
- Keep `線/せん` and `服/ふく` as normal beginner-ish vocabulary without score
  floors or restricted admission.

After refreshing the corrected ranking and audit artifacts, the open
compound-leak candidate review contains only these intentional non-actions:
`縁/えん`, `線/せん`, and `服/ふく`. That is expected and should not reopen the
pass unless a new qualitative review finds a concrete user-facing problem.

## Full-Range Sample Review

Fresh full-range sample artifact:

- Markdown: `docs/test_outputs/srs_learner_difficulty_full_range_sample_review_en_ja_latest.md`
- JSON: `docs/test_outputs/srs_learner_difficulty_full_range_sample_review_en_ja_latest.json`

Generation scope:

- Deterministic seed: `20260630`
- Random rows per `0.05` band: `12`
- Mechanical risk rows per `0.05` band: `8`

High-level read:

- The `0.00-0.30` sample is broadly coherent for early learner presentation.
  The visible risk rows are mostly accepted display/admission corrections such
  as kana-preferred written forms, `つく/つく` standalone exclusion, and
  compound/on-reading admission routing.
- The latest compound-leak decisions show up as intended: `火/か`, `訳/やく`,
  `東/とう`, `西/せい`, and `北/ほく` are no longer ordinary topic-stretchable
  standalone vocabulary, while `服/ふく`, `線/せん`, `縁/えん`, and `陸/りく`
  remain normal vocabulary.
- The `0.35-0.60` bands still contain some source-backed texture around rare
  readings, marked forms, and domain/gairaigo rows. In the current sample this
  looks like acceptable review noise rather than a new broad model-shape
  blocker.
- The `0.60-1.00` bands look qualitatively like advanced/tail material: rare
  compounds, literary forms, domain terms, obscure gairaigo, and
  low-direct-support entries. The ordering is not perfect, but the errors are
  much less likely to affect first-N1 learner experience.

Small polish queue addressed from this sample:

- `必用/ひつよう` is raised and routed as an uncommon spelling variant against
  ordinary `必要/ひつよう`.
- `市/いち` is moved later within ordinary vocabulary.
- `山/さん` and `高/こう` are raised and routed as compound/on-reading material.
- The sampled vulgar/adult tail row keeps its tail score but is routed away
  from ordinary default standalone SRS admission.

Acceptance stance:

The corrected ranking is product-plausible for scalar presentation priority
through the learner-facing range we have been targeting. Remaining issues are
better handled as occasional manual/content-admission polish if encountered
during product use, not by continuing to search for broad new model failures.

## JMDict Family Admission Sidecar

Fresh source-backed family artifact:

- Markdown: `docs/test_outputs/srs_learner_difficulty_jmdict_family_admission_review_en_ja_latest.md`
- JSON: `docs/test_outputs/srs_learner_difficulty_jmdict_family_admission_review_en_ja_latest.json`

This sidecar uses JMDict `ent_seq` as a dictionary-entry family ID. It does not
merge by same surface, same reading, same kanji, or score proximity. A ranked
row is assigned to a family only when its exact surface+reading pair maps
unambiguously to one JMDict entry; ambiguous pairs and same-surface rows from
different JMDict entries are reported but not merged.

Current summary against the corrected ranking:

| Metric | Value |
| --- | ---: |
| Ranking rows | `73,752` |
| Rows mapped to one JMDict family | `70,964` |
| Visible top-5000 multirow families | `37` |
| Safe visible families | `4` |
| Caution visible families | `33` |
| Visible suppressible sibling rows | `40` |
| Ambiguous visible rows left unmerged | `220` |

Interpretation:

- This is a good candidate for the next admission-sample pass because it can
  suppress duplicate/alternate family rows without changing scalar scores.
- The sidecar is deliberately conservative. Rows such as kana-only ambiguous
  readings stay unmerged when JMDict has multiple possible entries.
- Caution families include source restrictions, marked forms/readings, multiple
  readings, or already restricted siblings. They are useful diagnostics, but
  should be reviewed before becoming automatic runtime suppression.

## Base Source-Arbitration Candidate

Base candidate ID:

`srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap`

Selection basis:

- Use the `same_surface_exact_protected_floor_refine` source-arbitration
  sidecar as a narrow follow-up to the effective-JLPT sweep.
- Keep the same holdout-balanced score as the previous `0.42` protected
  family floor, but prefer the exact-protected variant because it prevents
  lesson-surface family evidence from raising effective-exact JLPT rows such
  as `明日/あした`.
- Treat stricter same-surface floors as review candidates only; do not promote
  them unless a qualitative blocker review accepts the rare-reading repair
  tradeoff.
- Add the accepted base-family rescue as a normalized-score overlay: if Sudachi
  reduces a single content-token surface to an easier dictionary base already
  present in the matrix, cap the surface toward `base_score + 0.06` with a
  full-strength score-gap gate.
- Reject the newer gairaigo source/origin-ease scalar for now. The targeted
  bakeoff showed no holdout gain and over-lowered ordinary gairaigo rows.

Latest metrics from `docs/test_outputs/srs_learner_difficulty_source_arbitration_base_family_rescue_refine_warp_p60_g155_en_ja_latest.json`:

| Metric | Value |
| --- | ---: |
| Calibration balanced | `0.800838` |
| Holdout balanced | `0.914576` |
| Holdout pairwise | `0.899363` |
| Holdout MAE score | `0.914376` |

Near-tie and stricter-floor candidates rejected for default product context:

| Candidate | Calibration balanced | Holdout balanced | Reason not selected |
| --- | ---: | ---: | --- |
| `best_calibration_balanced` from the broad effective-JLPT sweep | `0.779174` | `0.886585` | It raises some rare same-surface rows, but also pushes ordinary rows such as `明日/あした` to about `0.50`; this is not acceptable as a default product shape. |
| `exact_protected_floor_0.62` / `0.74` | up to `0.778551` | up to `0.886882` | These repair more rare same-surface readings, but the global holdout score no longer wins and the repair strength needs qualitative acceptance before it becomes default. |
| `gairaigo_origin_ease` targeted overlay | `0.800838` | `0.913207` | The simple origin-frequency ease overlay did not improve holdout and slightly degraded first-60/all-label MAE in the targeted bakeoff. |

## Frozen Inputs

- Source-arbitration report: `docs/test_outputs/srs_learner_difficulty_source_arbitration_base_family_rescue_refine_warp_p60_g155_en_ja_latest.json`
- Source-arbitration summary: `docs/test_outputs/srs_learner_difficulty_source_arbitration_base_family_rescue_refine_warp_p60_g155_en_ja_latest.md`
- Targeted signal bakeoff: `docs/test_outputs/srs_learner_difficulty_targeted_signal_bakeoff_en_ja_latest.md`
- Same-surface exact-protected audit: `docs/test_outputs/srs_learner_difficulty_same_surface_exact_protected_floor_audit_en_ja_latest.md`

## Acceptance Review Pack

Focused first-60-percent review pack:

- JSON: `docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.json`
- Markdown: `docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.md`

Review scope:

- Predicted score bands through `0.70`, close to the current first-60 target.
- Rows covered by that cutoff: `38,329 / 73,752`.
- Labeled rows where either expected score or observed candidate score is at or below the cutoff.
- Suspect buckets restricted to rows scored at or below the cutoff.

Generated command:

```bash
python3 scripts/testing/srs_learner_difficulty_current_best_band_review_en_ja.py \
  --combo-json docs/test_outputs/srs_learner_difficulty_source_arbitration_base_family_rescue_refine_warp_p60_g155_en_ja_latest.json \
  --candidate-id srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap \
  --review-max-score 0.70 \
  --sample-count 20 \
  --detail-limit 32 \
  --json-out docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_learner_difficulty_acceptance_first60_en_ja_latest.md
```

## Current Follow-Up Findings

The effective-JLPT cleanup is useful signal hygiene, but the remaining
reference-backed JLPT exact gap is not a clean automatic-import queue:

- `docs/test_outputs/srs_learner_difficulty_jlpt_reference_compare_en_ja_latest.md`
  now categorizes all `200` remaining effective-exact gaps.
- `139` of those rows are inside the first-60-by-core-rank slice.
- Most remaining rows are guarded, kana-preferred, search-only, marked, or
  rare-reading forms. Those are intentionally not effective exact anchors under
  the current product-safety policy.
- Only `19` rows are `current_jlpt_surface_only_no_exact`; these still need an
  independent per-reading source before they should become exact learner
  anchors.

The refreshed band review still shows some rough texture around `0.45-0.60`,
especially rare readings, domain words, and obscure written forms. That is
acceptable review noise unless a pattern is recurring, source-explainable, and
fixable without pulling ordinary learner words out of place.

Known one-off/manual exceptions are tracked separately in
`docs/srs/srs_learner_difficulty_manual_adjustment_watchlist_en_ja.md`. These
include rows such as `吐く/つく`, `時々/じじ`, and `何人/なにびと`, where the
remaining issue is narrow enough that it should not drive another general model
rule before final ranking review.

The same-surface exact-protected audit found one real signal-shape cleanup:
the older `pedagogical_family_only_rare_pollution` gate could still fire on
effective-exact JLPT rows when the family evidence came from lesson vocabulary.
The selected `unprotected_exact` variant keeps the same headline holdout score
while separating those cases. In the focus rows, `明日/あした` changes from an
old-family-risk row to exact-protected-risk `0.0`, while rows such as
`外国/とつくに`, `誘う/いざなう`, `女/おみな`, and `外/がい` remain targetable by
stricter rare-reading floors.

The smooth exact-protected same-surface sweep is now available at
`docs/test_outputs/srs_learner_difficulty_source_arbitration_same_surface_gradient_floor_refine_en_ja_latest.md`.
It is mathematically a superset of the current hard floor: one swept setting
collapses to the old `floor * exact_protected_risk` behavior, while other
settings attenuate by exact-reading commonness and JMDict form evidence. The
best holdout setting is a conservative `0.42` high floor with a square curve
and improves holdout balanced by only about `0.000002`; treat it as a cleaner
review candidate, not automatic runtime promotion evidence.

The refreshed targeted-signal bakeoff now uses the accepted base-family rescue
candidate as its baseline. The simple gairaigo source/origin-ease overlay remains
rejected. The domain/marked cap remains under review: the strict
`jmdict_domain_c0p86_s1` variant changes zero first-60 rows, improves holdout
balanced by `0.000545`, and has no positive numeric labeled regression in its
top regression list, but it caps many obscure domain/marked tail rows to `0.86`.
That may be acceptable, but it is a separate product-shape decision and is not
part of the frozen candidate yet.

## Blocker Review Rule

During acceptance review, mark a row or pattern as a blocker only when it is:

- clearly wrong for learner presentation priority;
- likely to affect ordinary users before or around N1-level vocabulary;
- recurring or source-explainable, not a one-off taste dispute;
- fixable without destabilizing a larger band.

Everything else should be recorded as accepted noise or deferred tail work.
