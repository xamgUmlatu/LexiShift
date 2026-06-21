# en-ja Proficiency Ordering Roadmap

Tiny checklist for the sidecar methodology.

- [x] Build a sidecar evaluator that does not change runtime behavior.
- [x] Separate lane/default-admission diagnostics from scalar difficulty placement.
- [x] Score normal-vocab-only proficiency placement against calibration and holdout.
- [x] Add frontier-window diagnostics for a single user proficiency value `p`.
- [x] Run the sidecar and compare winners against the older balanced-score winners.
- [x] Add a follow-up sidecar search optimized for the proficiency-ordering objective.
- [x] Add a calibration-internal stability selector before treating search winners as promotable.
- [x] Use stability evidence to decide whether internal calibration stability is enough.
- [x] Generate an old-vs-new disagreement review before doing more model sweeps.
- [x] Test bounded old-anchor/new-delta hybrid corrections as a sidecar.
- [x] Add a calibration-fold stability selector for bounded hybrid policies.
- [x] Add a source-backed structured failure group sidecar.
- [x] Add stricter structured-group selector profiles for scope and MAE safety.
- [x] Investigate calibration-vs-holdout distribution mismatch before broadening runtime use.
- [x] Add a source-quality guardrail audit for non-scalar validation rows.
- [x] Add deterministic source-pair validation for lemma/reading mismatches.
- [x] Generate a non-JMDict-exact source-pair decision pack.
- [x] Evaluate scalar models on the cleaned JMDict-exact normal-vocab lane.
- [x] Document acceptance criteria and the realistic improvement envelope.
- [x] Generate a compact current-model band review pack aligned to the acceptance criteria.
- [x] Generate a qualitative failure-hypothesis workbench with source-signal snapshots.
- [x] Audit a protected gairaigo floor against rare/domain failures and gairaigo successes.
- [x] Sweep protected gairaigo floor curves on the fresh validation set.
- [x] Cross-check the validation-best gairaigo curve across labeled scalar splits.
- [x] Audit reading-specific failures and probe bounded reading upshift floors.
- [x] Add a targeted same-surface reading/form sample diagnostic from band-review failures.
- [x] Test a same-surface alternate-reading floor as a source-arbitration sidecar family.
- [x] Test exact-reading guarded source attenuation for same-surface rare variants.
- [x] Run a combined same-surface floor/attenuation sweep around the ordinary-cap winner.
- [x] Regenerate a current-best band/failure review pack after the same-surface combo pass.
- [x] Audit transparent rare-wago downshift ceilings with existing proxy signals.
- [x] Add a constituent/transparency sidecar over existing matrix lemmas.
- [x] Add guarded constituent-transparency scoring for opaque readings and bad segmentation.
- [x] Review and label the guarded constituent-transparency would-change set.
- [x] Evaluate whether existing scalar fields separate accepted from held/blocked transparency rows.
- [x] Test source-backed opacity gates over the reviewed transparency labels.
- [ ] Decide whether JMDict exact-pair validation should become a hard pre-scalar gate or review lane.
- [ ] Use disagreement structure to decide whether to keep old, add bounded corrections, or add targeted labels.
- [ ] Only after holdout evidence is clean, decide whether any winner should be promoted into runtime SRS ordering.

Latest note: the direct proficiency-ordering search improved the calibration
selector score but did not generalize cleanly to holdout, so the current result
is research evidence, not a runtime promotion candidate. The fold-training
selector chose the same calibration winner in every fold and still failed
holdout, so internal calibration stability is not sufficient evidence. The
next diagnostic artifact is an old-vs-new disagreement review: it should decide
whether the apparent value is a narrow correction target, a label/data problem,
or simply not useful enough to pursue. The bounded-hybrid sidecar keeps the old
model as the anchor and only tests clipped corrections derived from structured
old/new disagreements. The bounded-hybrid stability sidecar then checks whether
those policies are selectable from calibration folds without using holdout. The
structured failure group sidecar turns the residual-group question into
source-computable masks, bounded calibration residual corrections, and
fold-training selection evidence before any holdout comparison. Its stricter
selector profiles show that most holdout-attractive corrections are too broad
or validation-negative; the current narrow validation-positive MAE-safe lead is
`kanji_burden__gte075`, with small but positive validation and holdout movement.
The follow-up validation failure-group audit compares calibration, holdout, and
the 96-row stitch-validation label set. It shows major distribution mismatch
between calibration and fresh/holdout labels, especially around frequency tail,
loanword/domain rows, written burden, and curriculum-core coverage. A simple
one-group bounded correction fit on calibration did not improve both validation
and holdout balanced score, so the remaining decision should avoid broad scalar
corrections unless a narrower, source-quality-aware target is identified. The
source-quality guardrail audit shows that broad review masks can catch all 13
validation non-scalar rows, but only with heavy scalar collateral: the review
union catches 41 of 83 scalar validation rows and 141 of 420 scalar rows across
all labeled sets. This supports review/deprioritization lanes and source-pair
validation, not blunt automatic deletion from scalar difficulty ranking. The
source-pair validation audit is much sharper for the source-reading mismatch
class: requiring JMDict exact lemma/reading support catches all three reviewed
validation source mismatches (`枚/ばい`, `聖/しょう`, `形付け/かたちづけ`) while
flagging only one of 83 scalar validation rows (`厚口/あつくち`). `聖/しょう`
does have JMnedict name support, which reinforces the lane distinction: it is
not JMDict-backed normal ladder vocabulary even if it is source-supported as a
name/entity. The cleaned-lane evaluation then reuses existing v1, ordinary-cap,
and stitch scores on only rows with reviewed readings. The JMDict-exact filter
does not change the winning scalar model on calibration (`v1`), holdout
(`stitch`), or stitch-validation (`ordinary_cap`), but it cleanly isolates a
small decision pack: four scalar holdout rows, one scalar validation row, one
holdout review row, and the three validation source-mismatch rows. This makes
source-pair validation a candidate-hygiene improvement, not a replacement for
the scalar ordering model. The gairaigo guarded-floor audit then isolated a
narrow scalar issue: rare/domain loanwords are often too early because katakana
has low written burden, while common learner loanwords must stay protected. The
follow-up gairaigo curve sweep keeps that protection fixed and searches only the
floor shape. On the fresh validation set, a more aggressive `tail80` floor
improves the gairaigo subset beyond the first hand-built rule without changing
common protected successes. The cross-split check then showed the current
calibration and holdout scalar rows contain zero rows flagged as gairaigo, so
they cannot validate or refute this gairaigo-specific curve. The curve remains
useful as validation evidence and as a candidate targeted correction, but it is
not promotable until we either create independent gairaigo holdout labels or run
a broader backtest that can expose common-loanword regressions outside the
reviewed stitch-validation rows. The next reading-specific audit found a more
interesting but still non-promotable pattern: broad nonstandard-reading signals
are dirty because they fire on common learner words and rare wago rows whose
direction is often too late. A narrow hybrid floor
(`read_hybrid_f62_r75_t90_c60_pbc1`) improved labeled validation, holdout, and
calibration rows without changed-row regressions. The source-pair-protected
rerun removes the earlier source-review change and still improves the labeled
splits on five clean rows (`攪拌/かくはん`, `宙乗り/ちゅうのり`, `老松/おいまつ`,
`彼奴/きゃつ`, `我/が`), but the full-matrix review shows the same floor would
match 15,200 normal-vocab rows and actually raise 2,609 of them under the
ordinary-cap anchor. That is too broad for runtime promotion as-is; the useful
next question is whether marked alternate readings should override lemma-level
common/beginner protection, or whether this hypothesis should remain a
review/labeling clue rather than a model rule.

The transparent-wago audit then tested whether existing source-computable proxy
signals can safely identify rare but semantically transparent native/wago rows
that the ordinary-cap anchor places too late. The best strict-guardrail policy
is a conservative low-written-burden ceiling
(`wago_low_written_c74_t50_w45_o75`). It improves the fresh validation
transparent-wago subset by `0.027313` MAE, validation overall by `0.003203`
MAE, and holdout overall by only `0.000235` MAE, with no labeled changed-row
regressions. However, the same proxy would match 931 full-matrix normal-vocab
rows and change 657 of them; even the stricter tail-threshold variant would
still change 374 rows. This makes the result useful as evidence that a
transparent-native-word issue exists, but not promotable as a scalar runtime
correction using only the current proxy signals. The likely next improvement is
a real constituent/transparency or morpheme-commonness signal, or a targeted
review-label pack, rather than another broad ceiling over rare-wago tail risk.

The constituent/transparency sidecar then added the missing shape directly,
without adding new external data. It builds a constituent inventory from
existing normal-vocab matrix lemmas and scores each possible sublemma by
source-backed frequency, JLPT vocab, lesson vocab, beginner-core, and JMDict
priority signals; single-character chunks deliberately ignore JMDict priority
so opaque one-kanji rows do not self-explain. A small marked derivational
variant heuristic lets nominalized chunks such as `乗り` and `込み` resolve to
supported matrix lemmas such as `乗る` and `込む`. The best bounded policy,
`ctrans_low_written_t75_w45_cov1p00_s55_mk20`, keeps the same validation
transparent-wago MAE gain as the broad low-written proxy (`0.027313`) while
reducing the full-matrix would-change set from 657 rows to 103 rows. That is a
real improvement in shape: the model now has a mechanically calculable way to
say "rare tail, but built from known pieces" rather than "rare wago tail with
low written burden." The review pack still shows residual semantic-opacity
risks (`紙魚`, `雨雪`, `くいくい`, etc.), so this is now a promising follow-up
validation candidate, not a runtime promotion. The next useful work is to
review the 103 would-change rows and the 554 blocked broad-proxy rows, then use
those labels to decide whether constituent transparency needs an opacity guard,
stricter chunk-source weighting, or a smaller hand-audited correction lane.

The guarded constituent pass then implemented the first concrete robustness
layer from that review. It keeps the raw constituent score visible, but adds a
guarded score based on target-reading compositionality, automatic bad
segmentation blockers for repeated/short kana chunks, and a swept ceiling over
existing marked/domain risk components. This blocks the clearest false-positive
families from the 103-row review (`紙魚/しみ`, `水水母/みずくらげ`,
`赤水母/あかくらげ`, `石女/うまずめ`, `くいくい/くいくい`,
`いとど/いとど`, `赤む/あかむ`, `長たらしい/ながたらしい`) while preserving
the same labeled validation fixes (`田舎侍/いなかざむらい`,
`黒百合/くろゆり`). The best guarded candidate,
`ctrans_guard_low_written_t75_w45_cov1p00_s45_mk20_r80_d1p01`, keeps the
validation transparent-wago MAE gain at `0.027313`, keeps validation overall
MAE gain at `0.002962`, changes zero holdout rows, and reduces the full-matrix
would-change set from 103 to 47. The remaining 47 are now a narrower and more
interpretable review target: mainly reading-compositional compounds whose
semantic/domain transparency is still debatable (`左団扇`, plant/species names,
specialized object/material terms). That suggests the next robustness layer, if
needed, should target semantic/domain opacity rather than reading or
segmentation.

A guarded 47-row qualitative review now exists at
`docs/test_outputs/srs_learner_difficulty_constituent_transparency_guarded_review_en_ja_latest.md`.
Its provisional split is 25 acceptable automatic downshifts, 18 review-needed
rows, and 4 likely false positives. This confirms the guarded pass is a real
cleanup, not just a metric artifact, but it also argues against immediate
promotion: the remaining uncertainty is not numerical tuning, but whether the
model can distinguish transparent everyday compounds from transparent
species/material/cultural terms. The recommended decision is to keep the
correction as a sidecar until those 47 rows are reviewed or a semantic/domain
opacity lane is added.

The 47-row review was then converted into approved labels at
`docs/test_inputs/srs_learner_difficulty_constituent_transparency_review_labels_en_ja.json`
and evaluated in
`docs/test_outputs/srs_learner_difficulty_constituent_transparency_label_eval_en_ja_latest.md`.
The reviewed labels preserve 25 automatic downshift candidates, hold 18 rows in
review lanes, and block 4 likely false positives. This makes the current
candidate's strict review precision only `0.531915` if all 47 rows are
promoted automatically. Six existing scalar fields were tested for simple
threshold separation, and none perfectly separates accepted rows from
held/blocked rows. That means the next productive shape is not another scalar
tightening pass over the existing constituent score; it is a semantic/domain
opacity lane for plant/species, material/object, cultural-object, idiom, and
register-sensitive rows.

The opacity-gate sidecar then tested that direction directly at
`docs/test_outputs/srs_learner_difficulty_constituent_transparency_opacity_gate_eval_en_ja_latest.md`.
The best reviewed-set gate raises strict review precision from `0.531915` to
`0.814815`, keeps recall at `0.88`, removes all 4 hard-block rows, and reduces
full-matrix would-change rows from 47 to 27. The tradeoff is real: it loses
accepted review rows (`黒百合/くろゆり`, `家兎/いえうさぎ`,
`茎若布/くきわかめ`), including `黒百合/くろゆり`, one of the labeled
validation fixes. As a result, validation transparent-failure MAE reduction
drops from `0.027313` to `0.020563` and validation all-row MAE reduction drops
from `0.002962` to `0.00223`. This is still promising as a safety knob, but it
should be treated as a precision/safety tradeoff rather than a strict
improvement over the ungated constituent sidecar.

The same-surface reading/form sample diagnostic then narrowed the suspicious
band-review failures without changing runtime behavior. It compares rows such
as `辛い/つらい`, `真/まこと`, `誘う/いざなう`, `否/いや`, and `ゲロ/げろ`
against same-written-form siblings and existing reading/form source signals.
The result is intentionally mixed: `辛い/つらい` and `誘う/いざなう` have
source-backed reading/form evidence, `真/まこと` has only same-surface rank
competition and no explicit marked-reading signal, and `ゲロ/げろ` is an
opposite-direction candidate-classification issue. Narrow same-surface probes
reduce the broad reading audit's blast radius substantially, but every tested
policy remains review-only: marked floors hurt existing scalar labels, while
rank-gap floors touch the `火/か` false-positive probe. The useful next step is
not promotion. The same sidecar now emits a focused review pack with unlabeled
candidate buckets: source-plus-rank-gap alternate readings, rank-gap-only
ambiguous readings, source-marked common caveats, ordinary-variant false-positive
controls, and existing scalar anchors. This makes the immediate question
labelable: which same-surface alternate readings should be moved later, and
which are ordinary variants that a rank-gap rule must protect?

The same-surface alternate-reading sidecar then promoted that hypothesis from a
review diagnostic into a competing source-arbitration candidate family at
`docs/test_outputs/srs_learner_difficulty_source_arbitration_same_surface_alt_en_ja_latest.md`.
The shape is intentionally narrow: after ordinary protection, it applies an
optional floor only when the row has a same-written-form sibling, source-backed
reading/form markedness, and an unranked or rank-disadvantaged reading relative
to a common sibling. This correctly leaves controls such as `外国/がいこく`,
`火/か`, `否/いや`, `居る/いる`, and `呉れる/くれる` with zero direct risk,
while flagging rows such as `外国/とつくに`, `誘う/いざなう`, `上/へ`,
`海/あま`, and `厳しい/いつくしい`. The metric result is not a clean
promotion. Holdout chooses only a very mild `0.28` floor, improving holdout
balanced score from `0.885092` to `0.885097` and moving `外国/とつくに` only
from `0.114619` to `0.162684`; calibration prefers a much stronger `0.74`
floor, moving the same rows to about `0.57`, but holdout balanced drops to
`0.881062`. The corrected matched-baseline blast-radius report shows the mild
floor changes 109 rows, while the strong calibration floor changes 402 rows.
This is useful field evidence and a better labeling/review target, but not yet
a runtime scalar correction.

The follow-up exact-reading attenuation sidecar then tested the more principled
version of the same idea at
`docs/test_outputs/srs_learner_difficulty_source_arbitration_same_surface_attenuate_en_ja_latest.md`.
Instead of forcing a final score floor, it computes a pollution risk from:
same written form, source-backed rare/marked reading evidence, rank disadvantage
against an easier sibling, and weak exact reading evidence from frequency/core
rank. That risk can attenuate pedagogical, native, or all source easiness before
the source-arbitration base score is computed. Qualitatively, this is a better
shape: `外国/とつくに` moves from `0.114619` to `0.420262` under the best
pairwise tradeoff and to `0.573953` under the calibration-best aggressive
variant, while exact-commonness guards leave `外国/がいこく`, `誘う/さそう`,
`居る/おる`, `家/うち`, `後/のち`, and `今日/こんにち` protected. The metric
still does not support promotion: holdout balanced chooses the no-op baseline
at `0.885092`; the best non-no-op pairwise tradeoff raises holdout pairwise to
`0.881391` but lowers holdout balanced to `0.885060`, and the calibration-best
aggressive attenuation lowers holdout balanced to `0.884277`. The current
conclusion is that source attenuation is the correct structural fix for this
pollution class, but the available labels are not yet sufficient to promote its
strength automatically.

The combined same-surface sweep then searched both knobs together while also
unfreezing nearby ordinary-cap, tail, burden, and ordinary-gate values. It
evaluated 6,528 candidates at
`docs/test_outputs/srs_learner_difficulty_source_arbitration_same_surface_combo_en_ja_latest.md`.
The best holdout model is a conservative rare-source rank-gap floor of `0.34`
with no attenuation, improving holdout balanced score from `0.885092` to
`0.885103`. This is technically the best sidecar score so far, but the gain is
microscopic and only moves `外国/とつくに` from `0.114619` to `0.173192`. The
stronger attenuation candidates still look more semantically correct for the
pollution class (`外国/とつくに` to about `0.42` under the best pairwise
tradeoff, about `0.57` under the calibration-best aggressive variant), but they
lose on balanced holdout because the current holdout does not directly contain
the same-surface rare-reading targets and penalizes small numeric shifts
elsewhere. The current practical conclusion is to keep the conservative floor
as the numerical sidecar leader, keep exact-reading attenuation as the better
structural hypothesis, and require targeted labels before using attenuation as
a runtime correction.

The current-best band/failure review pack then reset the drawing board around
that conservative combo winner at
`docs/test_outputs/srs_learner_difficulty_current_best_band_review_en_ja_latest.md`.
It samples every 0.05 score band and groups labeled errors across calibration,
holdout, and stitch-validation labels. The post-same-surface picture is mixed:
the broad band texture is usable, but the remaining severe errors split into
different families rather than one obvious scalar fix. Calibration severe
errors are overwhelmingly too-low kango/common-domain rows; holdout severe
errors are more often rare transparent/wago or compositional rows placed too
late; stitch-validation shows a smaller but clearer rare/domain gairaigo
too-low cluster (`テレックス`, `ダイオード`, `ヌーボー`, `メッセ`) plus residual
same-surface rare-reading rows (`彼奴/きゃつ`). Full-matrix suspect buckets also
show that the conservative same-surface floor still leaves 253 low-band
same-surface rare-reading candidates, while low-band domain/loanword and
low-band common-kango buckets are too broad/noisy to promote as-is. The next
modeling step should therefore choose one narrow family and review it directly,
rather than sweeping a global correction over all kango, domain, or wago rows.
