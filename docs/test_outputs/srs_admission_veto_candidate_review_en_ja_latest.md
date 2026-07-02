# en-ja SRS Admission Veto Candidate Review

Source: `core/lexishift_core/resources/srs/en_ja/learner_difficulty_corrected.csv`
Generated: `2026-07-02T21:47:53.005150+00:00`

This pack is a review queue, not an automatic correction list. It is built from the runtime corrected learner-difficulty CSV.

## Summary

| Metric | Value |
| --- | ---: |
| Runtime rows | 73752 |
| Active/handled correction rows | 185 |
| Active hard-veto rows | 96 |
| Review-pack rows | 132 |
| Unique review-pack rows | 132 |
| Product-visible review-pack rows | 10 |
| Random-visible review-pack rows | 9 |
| Product exact-visible review-pack rows | 0 |
| Random exact-visible review-pack rows | 0 |
| Product lemma-fallback visible rows | 10 |
| Random lemma-fallback visible rows | 9 |

## Hypothesis Tracking

| Category | Posture | Certainty | Candidates | Shown | Visible | Dominant Bands | Dominant Shapes |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| `manual_watchlist` | `manual_resolution` | `review_required` | 2 | 2 | exact_p=0; exact_r=0; lemma_p=0; lemma_r=0; topic=0 | 0.00-0.20:1, 0.40-0.60:1 | kanji_compound_or_phrase:1, single_kanji:1 |
| `active_hard_veto` | `already_hard_gated` | `high` | 96 | 24 | exact_p=0; exact_r=0; lemma_p=5; lemma_r=5; topic=0 | 0.20-0.40:42, 0.40-0.60:34, 0.00-0.20:10 | single_kanji:64, kanji_compound_or_phrase:30, hiragana:2 |
| `unhandled_review_flags` | `review_only` | `medium` | 339 | 24 | exact_p=0; exact_r=0; lemma_p=0; lemma_r=0; topic=0 | 0.20-0.40:172, 0.00-0.20:167 | kanji_compound_or_phrase:226, single_kanji:111, hiragana:2 |
| `same_surface_rare_reading` | `review_only` | `medium_high` | 273 | 24 | exact_p=0; exact_r=0; lemma_p=3; lemma_r=2; topic=0 | 0.40-0.60:271, 0.20-0.40:2 | kanji_compound_or_phrase:156, single_kanji:117 |
| `single_kanji_component_like` | `review_only` | `medium` | 390 | 24 | exact_p=0; exact_r=0; lemma_p=0; lemma_r=0; topic=0 | 0.40-0.60:354, 0.20-0.40:36 | single_kanji:390 |
| `kana_preferred_kanji_display` | `review_only` | `medium_high` | 1120 | 24 | exact_p=0; exact_r=0; lemma_p=2; lemma_r=2; topic=0 | 0.40-0.60:569, 0.20-0.40:401, 0.00-0.20:150 | kanji_compound_or_phrase:801, single_kanji:319 |
| `low_support_early_rows` | `review_only` | `low_medium` | 10 | 10 | exact_p=0; exact_r=0; lemma_p=0; lemma_r=0; topic=0 | 0.20-0.40:10 | hiragana:7, single_kanji:3 |


## Manual watchlist

Rows already marked review/watch in the correction layer. These are included so the current open queue stays visible.

Hypothesis: `manual_open_queue`; posture: `manual_resolution`; certainty: `review_required`.

Expected accuracy: `depends_on_existing_manual_note`.

Known failure mode: `stale watch rows may no longer be actionable`.

Candidates found: `2`; shown: `2`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 2.070 | 1256 | 0.175169 | `0.00-0.20` | `kanji_compound_or_phrase` | `或いは` | `あるいは` | `resolve_existing_review_status` | not_observed; p=0; r=0; topic=0 | exact=0.993; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=0.000; generated flags: manual_watchlist,early_kana_preferred_kanji; kana-preferred kanji surface; manual status: watch |
| 1.682 | 10336 | 0.415226 | `0.40-0.60` | `single_kanji` | `猶` | `なお` | `resolve_existing_review_status` | not_observed; p=0; r=0; topic=0 | exact=0.975; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=0.000; generated flags: manual_watchlist; kana-preferred kanji surface; manual status: watch |

## Already active hard vetoes

Rows already carrying an explicit runtime-suppression correction. These are not new candidates; they are the high-confidence gate set we use as calibration examples for later review.

Hypothesis: `explicit_product_gate`; posture: `already_hard_gated`; certainty: `high`.

Expected accuracy: `very_high`.

Known failure mode: `manual correction may be overly conservative`.

Candidates found: `96`; shown: `24`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 3.416 | 2163 | 0.220000 | `0.20-0.40` | `single_kanji` | `君` | `くん` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.016; jlpt=1; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk; low exact commonness |
| 3.358 | 2316 | 0.226526 | `0.20-0.40` | `single_kanji` | `東` | `とう` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.085; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 3.316 | 2161 | 0.220000 | `0.20-0.40` | `kanji_compound_or_phrase` | `入り口` | `いりくち` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=1; lesson=0; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk,normalized_only_jlpt; high same-surface risk; low exact commonness |
| 3.307 | 2343 | 0.227601 | `0.20-0.40` | `single_kanji` | `西` | `せい` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk; low exact commonness |
| 3.250 | 9216 | 0.400000 | `0.40-0.60` | `single_kanji` | `山` | `さん` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.159 | 23126 | 0.550000 | `0.40-0.60` | `single_kanji` | `紫` | `し` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.005; jlpt=0; lesson=0; same=0.990; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.134 | 26673 | 0.580000 | `0.40-0.60` | `single_kanji` | `曲` | `くせ` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.130 | 17942 | 0.500000 | `0.40-0.60` | `single_kanji` | `間` | `あい` | `already_hard_vetoed` | lemma_any_reading; p=3; r=2; topic=0; neutral_p100,neutral_p20,sports_fitness_p25 | exact=0.003; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.130 | 17944 | 0.500000 | `0.40-0.60` | `single_kanji` | `間` | `あわい` | `already_hard_vetoed` | lemma_any_reading; p=3; r=2; topic=0; neutral_p100,neutral_p20,sports_fitness_p25 | exact=0.004; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.070 | 23123 | 0.550000 | `0.40-0.60` | `single_kanji` | `家` | `や` | `already_hard_vetoed` | lemma_any_reading; p=2; r=1; topic=0; neutral_p00,neutral_p10 | exact=0.003; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.058 | 2322 | 0.226745 | `0.20-0.40` | `single_kanji` | `朝` | `ちょう` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.090; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 3.056 | 2365 | 0.228380 | `0.20-0.40` | `single_kanji` | `北` | `ほく` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.072; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 3.054 | 16044 | 0.480000 | `0.40-0.60` | `single_kanji` | `面` | `おも` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.010; jlpt=1; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.050 | 33421 | 0.650000 | `0.60-0.80` | `single_kanji` | `共` | `むた` | `already_hard_vetoed` | lemma_any_reading; p=13; r=19; topic=0; anime_manga_p45,computing_internet_p45,games_p45 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.050 | 33423 | 0.650000 | `0.60-0.80` | `single_kanji` | `鯨` | `いさな` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.007; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.050 | 38326 | 0.700000 | `0.60-0.80` | `single_kanji` | `己` | `つちのと` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.021; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.966 | 2159 | 0.220000 | `0.20-0.40` | `single_kanji` | `塩` | `えん` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.098; jlpt=1; lesson=0; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 2.954 | 16042 | 0.480000 | `0.40-0.60` | `kanji_compound_or_phrase` | `何時` | `なんどき` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.025; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.866 | 2162 | 0.220000 | `0.20-0.40` | `single_kanji` | `南` | `なん` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.046; jlpt=1; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 2.850 | 9223 | 0.400000 | `0.40-0.60` | `single_kanji` | `鼠` | `ねず` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.011; jlpt=1; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.790 | 13138 | 0.450000 | `0.40-0.60` | `single_kanji` | `仏` | `ぶつ` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.030; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk |
| 2.784 | 26674 | 0.580000 | `0.40-0.60` | `single_kanji` | `君` | `きんじ` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.784 | 26676 | 0.580000 | `0.40-0.60` | `single_kanji` | `海` | `あま` | `already_hard_vetoed` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.770 | 4193 | 0.300000 | `0.20-0.40` | `single_kanji` | `上` | `かみ` | `already_hard_vetoed` | lemma_any_reading; p=2; r=4; topic=0; neutral_p00,neutral_p10 | exact=0.179; jlpt=1; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |

## Unhandled generated review flags

Rows with generated warning flags but no active manual correction. These are high-priority because the exporter already noticed a risk.

Hypothesis: `exporter_warning`; posture: `review_only`; certainty: `medium`.

Expected accuracy: `high_for_queueing_low_for_automatic_veto`.

Known failure mode: `flags mix display-only issues with true admission vetoes`.

Candidates found: `339`; shown: `24`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 3.404 | 2419 | 0.230395 | `0.20-0.40` | `kanji_compound_or_phrase` | `一時` | `ひととき` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.191; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji,early_same_surface_risk; high same-surface risk; kana-preferred kanji surface |
| 3.396 | 3549 | 0.278560 | `0.20-0.40` | `single_kanji` | `骨` | `こつ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=1; lesson=0; same=1.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji,early_same_surface_risk; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.325 | 4048 | 0.295426 | `0.20-0.40` | `kanji_compound_or_phrase` | `一時` | `いっとき` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.092; jlpt=0; lesson=1; same=1.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji,early_same_surface_risk; high same-surface risk; kana-preferred kanji surface |
| 3.102 | 460 | 0.106568 | `0.00-0.20` | `kanji_compound_or_phrase` | `明日` | `あした` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.191; jlpt=1; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 3.071 | 4148 | 0.298805 | `0.20-0.40` | `kanji_compound_or_phrase` | `明日` | `みょうにち` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.111; jlpt=0; lesson=1; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 2.982 | 3453 | 0.267555 | `0.20-0.40` | `single_kanji` | `生` | `せい` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.199; jlpt=1; lesson=0; same=0.839; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji,early_same_surface_risk; high same-surface risk; kana-preferred kanji surface |
| 2.977 | 455 | 0.106059 | `0.00-0.20` | `kanji_compound_or_phrase` | `開く` | `あく` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.271; jlpt=1; lesson=0; same=0.959; kana=1.000; susp=0.798; generated flags: early_kana_preferred_kanji,early_same_surface_risk; high same-surface risk; kana-preferred kanji surface |
| 2.902 | 3535 | 0.273351 | `0.20-0.40` | `single_kanji` | `原` | `げん` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.080; jlpt=1; lesson=0; same=1.000; kana=0.000; susp=1.000; generated flags: early_same_surface_risk; high same-surface risk |
| 2.807 | 3460 | 0.267864 | `0.20-0.40` | `single_kanji` | `縁` | `ふち` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.133; jlpt=1; lesson=0; same=0.407; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.785 | 3390 | 0.265182 | `0.20-0.40` | `single_kanji` | `仏` | `ほとけ` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.160; jlpt=1; lesson=0; same=0.612; kana=0.000; susp=1.000; generated flags: early_same_surface_risk |
| 2.625 | 1029 | 0.158446 | `0.00-0.20` | `single_kanji` | `都` | `みやこ` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.329; jlpt=1; lesson=0; same=0.841; kana=0.000; susp=0.631; generated flags: early_same_surface_risk; high same-surface risk |
| 2.606 | 3466 | 0.268110 | `0.20-0.40` | `kanji_compound_or_phrase` | `解く` | `ほどく` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.123; jlpt=1; lesson=0; same=0.407; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.552 | 1307 | 0.178164 | `0.00-0.20` | `single_kanji` | `様` | `さま` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.383; jlpt=1; lesson=0; same=0.734; kana=1.000; susp=0.351; generated flags: early_kana_preferred_kanji,early_same_surface_risk; kana-preferred kanji surface |
| 2.547 | 490 | 0.111059 | `0.00-0.20` | `single_kanji` | `嘴` | `くちばし` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.133; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.451 | 438 | 0.104449 | `0.00-0.20` | `kanji_compound_or_phrase` | `辛い` | `からい` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.429; jlpt=1; lesson=0; same=0.475; kana=1.000; susp=0.346; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.434 | 3340 | 0.263579 | `0.20-0.40` | `single_kanji` | `際` | `きわ` | `watch` | not_observed; p=0; r=0; topic=0 | exact=0.329; jlpt=1; lesson=0; same=0.841; kana=0.000; susp=0.531; generated flags: early_same_surface_risk; high same-surface risk |
| 2.377 | 3423 | 0.266477 | `0.20-0.40` | `kanji_compound_or_phrase` | `注ぐ` | `つぐ` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=1; lesson=0; same=0.242; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; low exact commonness; kana-preferred kanji surface |
| 2.362 | 3373 | 0.264658 | `0.20-0.40` | `single_kanji` | `直` | `じき` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.195; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.355 | 3521 | 0.271131 | `0.20-0.40` | `single_kanji` | `粗` | `あら` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.100; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.349 | 476 | 0.108771 | `0.00-0.20` | `kanji_compound_or_phrase` | `独り` | `ひとり` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.180; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.286 | 1074 | 0.161893 | `0.00-0.20` | `kanji_compound_or_phrase` | `木綿` | `もめん` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.170; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=1.000; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.261 | 3393 | 0.265274 | `0.20-0.40` | `single_kanji` | `兎` | `うさぎ` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.254; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=0.845; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.220 | 3351 | 0.263887 | `0.20-0.40` | `single_kanji` | `氷` | `こおり` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.277; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=0.779; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |
| 2.206 | 486 | 0.109958 | `0.00-0.20` | `single_kanji` | `陸` | `りく` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.223; jlpt=1; lesson=0; same=0.000; kana=1.000; susp=0.935; generated flags: early_kana_preferred_kanji; kana-preferred kanji surface |

## Same-surface rare readings

Common-looking written forms whose specific reading has weak exact support. These are likely to pollute early admission if left normal.

Hypothesis: `same_surface_rare_reading`; posture: `review_only`; certainty: `medium_high`.

Expected accuracy: `good_below_mid_difficulty_no_auto_veto`.

Known failure mode: `valid literary or specialized readings can be real vocabulary`.

Candidates found: `273`; shown: `24`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 3.253 | 16112 | 0.480714 | `0.40-0.60` | `single_kanji` | `形` | `かた` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.005; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.238 | 17272 | 0.493364 | `0.40-0.60` | `single_kanji` | `粗` | `そ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.007; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.237 | 17363 | 0.494165 | `0.40-0.60` | `single_kanji` | `縁` | `えにし` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.009; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.236 | 17432 | 0.494895 | `0.40-0.60` | `single_kanji` | `首` | `おびと` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.004; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.236 | 17475 | 0.495355 | `0.40-0.60` | `single_kanji` | `桜` | `おう` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.235 | 17537 | 0.495991 | `0.40-0.60` | `single_kanji` | `種` | `くさ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.234 | 17580 | 0.496395 | `0.40-0.60` | `single_kanji` | `嵐` | `らん` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.233 | 17646 | 0.497090 | `0.40-0.60` | `single_kanji` | `外` | `げ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.233 | 17651 | 0.497117 | `0.40-0.60` | `single_kanji` | `外` | `がい` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.233 | 17710 | 0.497671 | `0.40-0.60` | `single_kanji` | `内` | `ない` | `likely_restrict_or_score_floor` | lemma_any_reading; p=3; r=4; topic=0; food_cooking_p20,neutral_p20,sports_fitness_p25 | exact=0.005; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.232 | 17750 | 0.498061 | `0.40-0.60` | `single_kanji` | `僕` | `やつがれ` | `likely_restrict_or_score_floor` | lemma_any_reading; p=3; r=3; topic=0; food_cooking_p20,neutral_p20,sports_fitness_p25 | exact=0.015; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.229 | 18027 | 0.500782 | `0.40-0.60` | `single_kanji` | `元` | `がん` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.013; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.158 | 17000 | 0.490386 | `0.40-0.60` | `single_kanji` | `匙` | `かい` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=0.924; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.097 | 12700 | 0.444526 | `0.40-0.60` | `kanji_compound_or_phrase` | `所謂` | `しょい` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.089 | 13238 | 0.450942 | `0.40-0.60` | `kanji_compound_or_phrase` | `如何` | `いか` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.013; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.087 | 13367 | 0.452353 | `0.40-0.60` | `kanji_compound_or_phrase` | `彼方` | `あなた` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.011; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.086 | 13445 | 0.453156 | `0.40-0.60` | `kanji_compound_or_phrase` | `何故` | `なにゆえ` | `review_for_score_floor_or_restriction` | lemma_any_reading; p=1; r=0; topic=0; neutral_p30 | exact=0.022; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.085 | 13536 | 0.454137 | `0.40-0.60` | `kanji_compound_or_phrase` | `何方` | `いずち` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.085 | 13554 | 0.454305 | `0.40-0.60` | `kanji_compound_or_phrase` | `何方` | `いずかた` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.081 | 13844 | 0.457364 | `0.40-0.60` | `kanji_compound_or_phrase` | `薔薇` | `しょうび` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.016; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.079 | 14377 | 0.462933 | `0.40-0.60` | `single_kanji` | `斑` | `まだら` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.009; jlpt=0; lesson=0; same=0.822; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.077 | 14164 | 0.460808 | `0.40-0.60` | `kanji_compound_or_phrase` | `薔薇` | `そうび` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.077 | 14553 | 0.464762 | `0.40-0.60` | `single_kanji` | `斑` | `はん` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=0.822; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.075 | 14375 | 0.462911 | `0.40-0.60` | `kanji_compound_or_phrase` | `其奴` | `そやつ` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.007; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |

## Single-kanji component-like rows

One-character kanji rows with weak exact support and high same-surface or suspicion evidence. Many are better as components or restricted rows.

Hypothesis: `single_kanji_component_like`; posture: `review_only`; certainty: `medium`.

Expected accuracy: `medium_type_dependent`.

Known failure mode: `some single-kanji rows are legitimate standalone vocabulary`.

Candidates found: `390`; shown: `24`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 3.062 | 16728 | 0.487484 | `0.40-0.60` | `single_kanji` | `蓮` | `はちす` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.008; jlpt=0; lesson=0; same=0.834; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.052 | 12332 | 0.440135 | `0.40-0.60` | `single_kanji` | `己` | `おら` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.163; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 3.051 | 12379 | 0.440527 | `0.40-0.60` | `single_kanji` | `父` | `てて` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.011; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 3.040 | 13162 | 0.450084 | `0.40-0.60` | `single_kanji` | `某` | `それがし` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.111; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 3.034 | 13624 | 0.455014 | `0.40-0.60` | `single_kanji` | `兵` | `つわもの` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.031; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 3.031 | 13858 | 0.457537 | `0.40-0.60` | `single_kanji` | `己` | `おの` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.042; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 3.028 | 14109 | 0.460289 | `0.40-0.60` | `single_kanji` | `霊` | `りょう` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 3.007 | 13719 | 0.455981 | `0.40-0.60` | `single_kanji` | `殻` | `かく` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.073; jlpt=0; lesson=0; same=0.977; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.994 | 16795 | 0.488145 | `0.40-0.60` | `single_kanji` | `穴` | `けつ` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.109; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.993 | 16881 | 0.489087 | `0.40-0.60` | `single_kanji` | `形` | `なり` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.060; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.991 | 13103 | 0.449554 | `0.40-0.60` | `single_kanji` | `雄` | `お` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.989 | 17188 | 0.492474 | `0.40-0.60` | `single_kanji` | `星` | `せい` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.022; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.989 | 17228 | 0.492899 | `0.40-0.60` | `single_kanji` | `鶏` | `かけろ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.988 | 17278 | 0.493409 | `0.40-0.60` | `single_kanji` | `銀` | `しろがね` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.007; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.988 | 17289 | 0.493490 | `0.40-0.60` | `single_kanji` | `金` | `こん` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.025; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.988 | 17293 | 0.493517 | `0.40-0.60` | `single_kanji` | `金` | `かな` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.988 | 17297 | 0.493554 | `0.40-0.60` | `single_kanji` | `字` | `あざな` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.021; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.987 | 17343 | 0.494003 | `0.40-0.60` | `single_kanji` | `恋` | `れん` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.015; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.987 | 17350 | 0.494053 | `0.40-0.60` | `single_kanji` | `緑` | `りょく` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.987 | 17351 | 0.494056 | `0.40-0.60` | `single_kanji` | `草` | `そう` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.004; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.986 | 17420 | 0.494788 | `0.40-0.60` | `single_kanji` | `砂` | `いさご` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.986 | 17421 | 0.494796 | `0.40-0.60` | `single_kanji` | `面` | `おもて` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.034; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.985 | 17501 | 0.495606 | `0.40-0.60` | `single_kanji` | `梅` | `ばい` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |
| 2.985 | 17510 | 0.495715 | `0.40-0.60` | `single_kanji` | `札` | `さね` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=0.000; susp=1.000; high same-surface risk; low exact commonness |

## Kana-preferred kanji display

Rows whose written form is kanji but the evidence says kana is strongly preferred. These may only need display-only correction when the word is otherwise legitimate.

Hypothesis: `kana_preferred_kanji_display`; posture: `review_only`; certainty: `medium_high`.

Expected accuracy: `good_for_display_review_not_for_veto`.

Known failure mode: `kanji display may still be acceptable for non-beginner rows`.

Candidates found: `1120`; shown: `24`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 3.068 | 14929 | 0.468631 | `0.40-0.60` | `kanji_compound_or_phrase` | `発条` | `はつじょう` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.061 | 15506 | 0.474548 | `0.40-0.60` | `kanji_compound_or_phrase` | `蕎麦` | `そばむぎ` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.004; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.059 | 15597 | 0.475552 | `0.40-0.60` | `kanji_compound_or_phrase` | `此方` | `こち` | `review_for_score_floor_or_restriction` | lemma_any_reading; p=13; r=17; topic=0; anime_manga_p45,computing_internet_p45,games_p45 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.035 | 17518 | 0.495797 | `0.40-0.60` | `kanji_compound_or_phrase` | `木綿` | `もくめん` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.035 | 17563 | 0.496236 | `0.40-0.60` | `kanji_compound_or_phrase` | `所為` | `しょい` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.034 | 17583 | 0.496401 | `0.40-0.60` | `kanji_compound_or_phrase` | `従兄弟` | `じゅうけいてい` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.034 | 17643 | 0.497076 | `0.40-0.60` | `kanji_compound_or_phrase` | `悪い` | `わろい` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.005; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 3.002 | 14858 | 0.467901 | `0.40-0.60` | `kanji_compound_or_phrase` | `狡い` | `こすい` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.014; jlpt=0; lesson=0; same=0.940; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.973 | 14503 | 0.464283 | `0.40-0.60` | `single_kanji` | `鼠` | `そ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.972 | 14548 | 0.464692 | `0.40-0.60` | `single_kanji` | `頭` | `とう` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.959 | 15591 | 0.475502 | `0.40-0.60` | `single_kanji` | `陸` | `おか` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.956 | 13749 | 0.456333 | `0.40-0.60` | `single_kanji` | `貝` | `ばい` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.010; jlpt=0; lesson=0; same=0.982; kana=1.000; susp=0.990; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.956 | 15858 | 0.478203 | `0.40-0.60` | `single_kanji` | `頭` | `どたま` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.007; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.956 | 15864 | 0.478254 | `0.40-0.60` | `single_kanji` | `頭` | `こうべ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.008; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.954 | 16035 | 0.479900 | `0.40-0.60` | `single_kanji` | `端` | `はした` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.018; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.954 | 16051 | 0.480065 | `0.40-0.60` | `single_kanji` | `端` | `つま` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.003; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.948 | 16127 | 0.480884 | `0.40-0.60` | `single_kanji` | `生` | `しょう` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=0.996; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.844 | 9602 | 0.405344 | `0.40-0.60` | `single_kanji` | `科` | `しな` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.008; jlpt=1; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.840 | 13113 | 0.449682 | `0.40-0.60` | `kanji_compound_or_phrase` | `其方` | `そなた` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.197; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.839 | 13256 | 0.451148 | `0.40-0.60` | `kanji_compound_or_phrase` | `彼奴` | `きゃつ` | `review_for_score_floor_or_restriction` | lemma_any_reading; p=1; r=2; topic=0; neutral_p50 | exact=0.030; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.836 | 13685 | 0.455659 | `0.40-0.60` | `single_kanji` | `溝` | `うなて` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=0.866; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.836 | 13709 | 0.455902 | `0.40-0.60` | `single_kanji` | `溝` | `せせなぎ` | `likely_restrict_or_score_floor` | not_observed; p=0; r=0; topic=0 | exact=0.001; jlpt=0; lesson=0; same=0.866; kana=1.000; susp=1.000; high same-surface risk; low exact commonness; kana-preferred kanji surface |
| 2.835 | 13529 | 0.454094 | `0.40-0.60` | `kanji_compound_or_phrase` | `彼処` | `かしこ` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.083; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |
| 2.834 | 13626 | 0.455031 | `0.40-0.60` | `kanji_compound_or_phrase` | `放る` | `ひる` | `review_for_score_floor_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.043; jlpt=0; lesson=0; same=1.000; kana=1.000; susp=1.000; high same-surface risk; kana-preferred kanji surface |

## Low-support early rows

Early rows without exact JLPT or lesson support and with low exact commonness. These are broad safety candidates, not automatic defects.

Hypothesis: `low_support_early_rows`; posture: `review_only`; certainty: `low_medium`.

Expected accuracy: `smoke_detector_only`.

Known failure mode: `many useful easy words are missing from exact support sources`.

Candidates found: `10`; shown: `10`.

| Risk | Rank | Score | Band | Shape | Word | Reading | Recommendation | Visible | Evidence |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 2.347 | 4833 | 0.315988 | `0.20-0.40` | `single_kanji` | `便` | `べん` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.010; jlpt=0; lesson=0; same=0.447; kana=1.000; susp=0.700; low exact commonness; kana-preferred kanji surface |
| 2.014 | 5753 | 0.340091 | `0.20-0.40` | `single_kanji` | `証` | `しょう` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.012; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=0.988; low exact commonness; kana-preferred kanji surface |
| 2.002 | 6432 | 0.356398 | `0.20-0.40` | `single_kanji` | `眼` | `がん` | `review_for_display_only_or_restriction` | not_observed; p=0; r=0; topic=0 | exact=0.002; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=1.000; low exact commonness; kana-preferred kanji surface |
| 1.572 | 5766 | 0.340400 | `0.20-0.40` | `hiragana` | `あな` | `あな` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.008; jlpt=0; lesson=0; same=0.000; kana=0.000; susp=1.000; low exact commonness |
| 1.571 | 5769 | 0.340424 | `0.20-0.40` | `hiragana` | `しゅう` | `しゅう` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.023; jlpt=0; lesson=0; same=0.000; kana=0.000; susp=1.000; low exact commonness |
| 1.566 | 5733 | 0.339611 | `0.20-0.40` | `hiragana` | `くう` | `くう` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.010; jlpt=0; lesson=0; same=0.000; kana=0.000; susp=0.990; low exact commonness |
| 1.562 | 5708 | 0.339049 | `0.20-0.40` | `hiragana` | `どく` | `どく` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.018; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=0.982; low exact commonness |
| 1.556 | 6300 | 0.353432 | `0.20-0.40` | `hiragana` | `ひく` | `ひく` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.010; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=1.000; low exact commonness |
| 1.552 | 6318 | 0.353686 | `0.20-0.40` | `hiragana` | `むら` | `むら` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.005; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=0.995; low exact commonness |
| 1.552 | 6311 | 0.353602 | `0.20-0.40` | `hiragana` | `ぼたん` | `ぼたん` | `review_low_support_early_placement` | not_observed; p=0; r=0; topic=0 | exact=0.006; jlpt=0; lesson=0; same=0.000; kana=1.000; susp=0.994; low exact commonness |
