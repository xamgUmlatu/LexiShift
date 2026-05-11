# en-es Semantic Veto Product-Scope Top-Heavy Band Grading

- Status: `ok`
- Decision: `product_scope_top_heavy_band_grading_established`
- Generated: `2026-05-09T21:18:41Z`
- Formula scopes evaluated: `2001 / 15670`
- Strategy scopes: `48024`
- Band strategies: `6`
- Ranking modes: `4`

## Methodology

Check whether semantic-veto evidence need is better represented by a concentrated top slice than by equal thirds, and whether source-exposure weighting surfaces product-important daily-language families.

Primary ordering uses base_product_prior measured-only failure. The top-heavy grade emphasizes high_need minus rest failure rate, then multiplies by monotonic high>=middle>=low order and measured target coverage.

## Band Strategies

| Strategy | High | Middle | Low | Description |
|---|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | 33.3% | 33.3% | 33.3% | Control: approximate equal thirds by predicted need. |
| `top_05_next_15_rest` | 5.0% | 15.0% | 80.0% | Very concentrated product hypothesis: top 5%, next 15%, rest. |
| `top_10_next_20_rest` | 10.0% | 20.0% | 70.0% | Concentrated product hypothesis: top 10%, next 20%, rest. |
| `top_15_next_25_rest` | 15.0% | 25.0% | 60.0% | Moderately concentrated product hypothesis: top 15%, next 25%, rest. |
| `top_20_next_30_rest` | 20.0% | 30.0% | 50.0% | Broad top-heavy product hypothesis: top 20%, next 30%, rest. |
| `top_25_next_25_rest` | 25.0% | 25.0% | 50.0% | Wide high-priority hypothesis: top 25%, next 25%, rest. |

## Ranking Modes

| Ranking mode | Formula | Description |
|---|---|---|
| `algorithm_need` | `need_score` | Control: use the formula score directly. |
| `source_exposure_product` | `need_score * source_zipf_risk` | Product-impact hypothesis: a hard rare family may matter less than a moderately hard common family. |
| `source_exposure_blend_25` | `0.75 * need_score + 0.25 * source_zipf_risk` | Light exposure weighting while mostly preserving algorithmic need. |
| `source_exposure_blend_50` | `0.50 * need_score + 0.50 * source_zipf_risk` | Balanced need/exposure ranking for the daily-language concentration hypothesis. |

## Best By Top-Heavy Grade

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 27.4% | 6.5% | 20.9% | 1.9927 | 0.1856 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_1007` | `tfidf_best_by_scorer_tfidf_a0000_mneg0005` | `{"high_need": 14, "low_need": 24, "middle_need": 11}` | 21.3% | 11.5% | 9.8% | 1.9162 | 0.0867 | bar->cercar:0.8429, break->quebrar:0.7929, smile->sonreír:0.7571, continue->durar:0.7429, region->comarca:0.7429, parrot->loro:0.7143, stall->cuadra:0.7143, snore->roncar:0.7071 |
| `equal_tertiles_33_33_34` | `algorithm_need` | `shadow_coverage_only` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_20_next_30_rest` | `algorithm_need` | `shadow_coverage_only` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_25_next_25_rest` | `algorithm_need` | `shadow_coverage_only` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_0001` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_20_next_30_rest` | `algorithm_need` | `sweep_linear_0001` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_0001` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_0002` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_20_next_30_rest` | `algorithm_need` | `sweep_linear_0002` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_0002` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_0003` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_20_next_30_rest` | `algorithm_need` | `sweep_linear_0003` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_0003` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_0004` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_20_next_30_rest` | `algorithm_need` | `sweep_linear_0004` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_0004` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_05_next_15_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9 |
| `top_05_next_15_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8 |
| `top_05_next_15_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9604 | 0.0864 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85 |

## Accepted Candidate Takeaway

- Decision: `top_heavy_has_signal_but_does_not_beat_equal_tertile_control`
- Top-heavy/control grade ratio: `0.4655`

Control:

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 27.4% | 6.5% | 20.9% | 1.9927 | 0.1856 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |

Best top-heavy alternative:

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `top_05_next_15_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9 |

## Best By Strategy

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 27.4% | 6.5% | 20.9% | 1.9927 | 0.1856 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_1007` | `tfidf_best_by_scorer_tfidf_a0000_mneg0005` | `{"high_need": 14, "low_need": 24, "middle_need": 11}` | 21.3% | 11.5% | 9.8% | 1.9162 | 0.0867 | bar->cercar:0.8429, break->quebrar:0.7929, smile->sonreír:0.7571, continue->durar:0.7429, region->comarca:0.7429, parrot->loro:0.7143, stall->cuadra:0.7143, snore->roncar:0.7071 |
| `top_20_next_30_rest` | `algorithm_need` | `shadow_coverage_only` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 19, "low_need": 26, "middle_need": 4}` | 24.5% | 6.9% | 17.6% | 1.7388 | 0.0865 | acceptable->razonable:0.85, bar->cercar:0.85, billow->oleaje:0.85, break->quebrar:0.85, bridle->reprimir:0.85, cite->mencionar:0.85, continue->durar:0.85, control->gobernar:0.85 |
| `top_05_next_15_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9 |
| `top_10_next_20_rest` | `algorithm_need` | `sweep_linear_0412` | `high_recall_soft_assist_tfidf_a0000_mneg0050` | `{"high_need": 5, "low_need": 32, "middle_need": 12}` | 23.5% | 14.8% | 8.7% | 1.7143 | 0.0776 | bar->cercar:0.8812, break->quebrar:0.8063, stall->cuadra:0.8063, billow->oleaje:0.7562, bridle->reprimir:0.7562 |
| `top_15_next_25_rest` | `algorithm_need` | `sweep_linear_0263` | `tfidf_best_by_scorer_tfidf_a0000_mneg0005` | `{"high_need": 8, "low_need": 27, "middle_need": 14}` | 22.3% | 14.5% | 7.9% | 2.0937 | 0.07 | bar->cercar:0.8643, billow->oleaje:0.8071, break->quebrar:0.8071, bridle->reprimir:0.8071, parrot->loro:0.8071, smile->sonreír:0.8071, stall->cuadra:0.8071, snore->roncar:0.7786 |

## Best By Ranking Mode

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 27.4% | 6.5% | 20.9% | 1.9927 | 0.1856 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_05_next_15_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9 |
| `top_05_next_15_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8 |
| `top_05_next_15_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9604 | 0.0864 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85 |

## Accepted Candidate Strategy Rows

| Strategy | Ranking | Formula | Scorer | Counts | High fail | Rest fail | High-rest | Lift | Grade | High samples |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `equal_tertiles_33_33_34` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 27.4% | 6.5% | 20.9% | 1.9927 | 0.1856 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_05_next_15_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9 |
| `top_05_next_15_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9715 | 0.0864 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8 |
| `top_05_next_15_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 39, "middle_need": 7}` | 27.7% | 13.1% | 14.6% | 1.9604 | 0.0864 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85 |
| `top_15_next_25_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 7, "low_need": 29, "middle_need": 13}` | 17.8% | 13.4% | 4.4% | 1.2604 | 0.0389 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9, continue->durar:0.8981, region->comarca:0.8827, except->excepto:0.8442, american->americano:0.8154 |
| `top_25_next_25_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 13, "low_need": 24, "middle_need": 12}` | 16.8% | 12.7% | 4.1% | 1.2197 | 0.0366 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85, continue->durar:0.8471, bar->cercar:0.825, region->comarca:0.824, except->excepto:0.7663, smile->sonreír:0.7558 |
| `top_10_next_20_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 5, "low_need": 34, "middle_need": 10}` | 16.6% | 13.8% | 2.9% | 1.2009 | 0.0255 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85, continue->durar:0.8471, bar->cercar:0.825 |
| `top_10_next_20_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 5, "low_need": 34, "middle_need": 10}` | 16.6% | 13.8% | 2.9% | 1.1854 | 0.017 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9, continue->durar:0.8981, region->comarca:0.8827 |
| `top_10_next_20_rest` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 5, "low_need": 35, "middle_need": 9}` | 16.6% | 13.8% | 2.9% | 1.1518 | 0.017 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962 |
| `top_15_next_25_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 8, "low_need": 28, "middle_need": 13}` | 15.6% | 13.8% | 1.8% | 1.0972 | 0.0161 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, except->excepto:0.6885, bar->cercar:0.6375, american->americano:0.6308 |
| `top_10_next_20_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 5, "low_need": 33, "middle_need": 11}` | 16.6% | 13.8% | 2.9% | 1.1838 | 0.0085 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654 |
| `top_15_next_25_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 8, "low_need": 29, "middle_need": 12}` | 15.6% | 13.8% | 1.8% | 1.1105 | 0.0052 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85, continue->durar:0.8471, bar->cercar:0.825, region->comarca:0.824, except->excepto:0.7663, smile->sonreír:0.7558 |
| `top_05_next_15_rest` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 3, "low_need": 40, "middle_need": 6}` | 13.9% | 14.0% | -0.2% | 0.9795 | 0.0 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308 |
| `top_25_next_25_rest` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 12, "low_need": 24, "middle_need": 13}` | 13.9% | 14.4% | -0.6% | 1.0014 | 0.0 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `equal_tertiles_33_33_34` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 15, "middle_need": 17}` | 13.0% | 14.3% | -1.3% | 0.9378 | 0.0 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85, continue->durar:0.8471, bar->cercar:0.825, region->comarca:0.824, except->excepto:0.7663, smile->sonreír:0.7558 |
| `top_20_next_30_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 10, "low_need": 24, "middle_need": 15}` | 12.5% | 14.5% | -2.0% | 0.8713 | 0.0 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9, continue->durar:0.8981, region->comarca:0.8827, except->excepto:0.8442, american->americano:0.8154, bar->cercar:0.8 |
| `top_20_next_30_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 10, "low_need": 24, "middle_need": 15}` | 12.5% | 14.5% | -2.0% | 0.8713 | 0.0 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, except->excepto:0.6885, bar->cercar:0.6375, american->americano:0.6308 |
| `top_20_next_30_rest` | `source_exposure_blend_25` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 10, "low_need": 24, "middle_need": 15}` | 12.5% | 14.6% | -2.1% | 0.8926 | 0.0 | break->quebrar:0.9077, control->gobernar:0.8731, current->contemporáneo:0.85, continue->durar:0.8471, bar->cercar:0.825, region->comarca:0.824, except->excepto:0.7663, smile->sonreír:0.7558 |
| `top_15_next_25_rest` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 8, "low_need": 29, "middle_need": 12}` | 10.4% | 14.8% | -4.5% | 0.7551 | 0.0 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_25_next_25_rest` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 12, "low_need": 24, "middle_need": 13}` | 10.4% | 15.2% | -4.8% | 0.7312 | 0.0 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9, continue->durar:0.8981, region->comarca:0.8827, except->excepto:0.8442, american->americano:0.8154, bar->cercar:0.8 |
| `top_20_next_30_rest` | `algorithm_need` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 9, "low_need": 24, "middle_need": 16}` | 9.2% | 15.2% | -6.0% | 0.6684 | 0.0 | break->quebrar:0.8769, bar->cercar:0.85, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, smile->sonreír:0.7577, stall->cuadra:0.75 |
| `top_25_next_25_rest` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 13, "low_need": 24, "middle_need": 12}` | 9.6% | 15.7% | -6.1% | 0.6664 | 0.0 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, except->excepto:0.6885, bar->cercar:0.6375, american->americano:0.6308 |
| `equal_tertiles_33_33_34` | `source_exposure_blend_50` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 17, "low_need": 16, "middle_need": 16}` | 9.8% | 16.3% | -6.5% | 0.7014 | 0.0 | break->quebrar:0.9385, control->gobernar:0.9154, current->contemporáneo:0.9, continue->durar:0.8981, region->comarca:0.8827, except->excepto:0.8442, american->americano:0.8154, bar->cercar:0.8 |
| `equal_tertiles_33_33_34` | `source_exposure_product` | `sweep_linear_2169` | `safest_80pct_positive_sentence_transformer_a0000_m0015` | `{"high_need": 16, "low_need": 16, "middle_need": 17}` | 7.8% | 17.1% | -9.3% | 0.558 | 0.0 | break->quebrar:0.8769, control->gobernar:0.8308, current->contemporáneo:0.8, continue->durar:0.7962, region->comarca:0.7654, except->excepto:0.6885, bar->cercar:0.6375, american->americano:0.6308 |

## Detail Rows

```json
[
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_2169",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.1856,
    "primary_high_rest_failure_delta": 0.2089,
    "band_family_counts": {
      "high_need": 17,
      "middle_need": 16,
      "low_need": 16
    },
    "high_sample_triggers": [
      "break->quebrar:0.8769",
      "bar->cercar:0.85",
      "control->gobernar:0.8308",
      "current->contemporáneo:0.8",
      "continue->durar:0.7962",
      "region->comarca:0.7654",
      "smile->sonreír:0.7577",
      "stall->cuadra:0.75"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_1007",
    "scorer_id": "tfidf_best_by_scorer_tfidf_a0000_mneg0005",
    "top_heavy_grade_score": 0.0867,
    "primary_high_rest_failure_delta": 0.0976,
    "band_family_counts": {
      "high_need": 14,
      "middle_need": 11,
      "low_need": 24
    },
    "high_sample_triggers": [
      "bar->cercar:0.8429",
      "break->quebrar:0.7929",
      "smile->sonreír:0.7571",
      "continue->durar:0.7429",
      "region->comarca:0.7429",
      "parrot->loro:0.7143",
      "stall->cuadra:0.7143",
      "snore->roncar:0.7071"
    ]
  },
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "shadow_coverage_only",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_20_next_30_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "shadow_coverage_only",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "shadow_coverage_only",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0001",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_20_next_30_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0001",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0001",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0002",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_20_next_30_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0002",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0002",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0003",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_20_next_30_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0003",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0003",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "equal_tertiles_33_33_34",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0004",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_20_next_30_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0004",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0004",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0865,
    "primary_high_rest_failure_delta": 0.1758,
    "band_family_counts": {
      "high_need": 19,
      "middle_need": 4,
      "low_need": 26
    },
    "high_sample_triggers": [
      "acceptable->razonable:0.85",
      "bar->cercar:0.85",
      "billow->oleaje:0.85",
      "break->quebrar:0.85",
      "bridle->reprimir:0.85",
      "cite->mencionar:0.85",
      "continue->durar:0.85",
      "control->gobernar:0.85"
    ]
  },
  {
    "band_strategy_id": "top_05_next_15_rest",
    "ranking_mode_id": "source_exposure_blend_50",
    "formula_id": "sweep_linear_2169",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0864,
    "primary_high_rest_failure_delta": 0.1458,
    "band_family_counts": {
      "high_need": 3,
      "middle_need": 7,
      "low_need": 39
    },
    "high_sample_triggers": [
      "break->quebrar:0.9385",
      "control->gobernar:0.9154",
      "current->contemporáneo:0.9"
    ]
  },
  {
    "band_strategy_id": "top_05_next_15_rest",
    "ranking_mode_id": "source_exposure_product",
    "formula_id": "sweep_linear_2169",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0864,
    "primary_high_rest_failure_delta": 0.1458,
    "band_family_counts": {
      "high_need": 3,
      "middle_need": 7,
      "low_need": 39
    },
    "high_sample_triggers": [
      "break->quebrar:0.8769",
      "control->gobernar:0.8308",
      "current->contemporáneo:0.8"
    ]
  },
  {
    "band_strategy_id": "top_05_next_15_rest",
    "ranking_mode_id": "source_exposure_blend_25",
    "formula_id": "sweep_linear_2169",
    "scorer_id": "safest_80pct_positive_sentence_transformer_a0000_m0015",
    "top_heavy_grade_score": 0.0864,
    "primary_high_rest_failure_delta": 0.1458,
    "band_family_counts": {
      "high_need": 3,
      "middle_need": 7,
      "low_need": 39
    },
    "high_sample_triggers": [
      "break->quebrar:0.9077",
      "control->gobernar:0.8731",
      "current->contemporáneo:0.85"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_1138",
    "scorer_id": "tfidf_best_by_scorer_tfidf_a0000_mneg0005",
    "top_heavy_grade_score": 0.08,
    "primary_high_rest_failure_delta": 0.09,
    "band_family_counts": {
      "high_need": 13,
      "middle_need": 12,
      "low_need": 24
    },
    "high_sample_triggers": [
      "bar->cercar:0.85",
      "break->quebrar:0.795",
      "smile->sonreír:0.77",
      "parrot->loro:0.74",
      "stall->cuadra:0.74",
      "snore->roncar:0.735",
      "continue->durar:0.725",
      "region->comarca:0.725"
    ]
  },
  {
    "band_strategy_id": "top_25_next_25_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_1012",
    "scorer_id": "tfidf_best_by_scorer_tfidf_a0000_mneg0005",
    "top_heavy_grade_score": 0.08,
    "primary_high_rest_failure_delta": 0.09,
    "band_family_counts": {
      "high_need": 13,
      "middle_need": 13,
      "low_need": 23
    },
    "high_sample_triggers": [
      "bar->cercar:0.85",
      "break->quebrar:0.8063",
      "smile->sonreír:0.775",
      "parrot->loro:0.7375",
      "stall->cuadra:0.7375",
      "snore->roncar:0.7312",
      "continue->durar:0.7188",
      "region->comarca:0.7188"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0412",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 12,
      "low_need": 32
    },
    "high_sample_triggers": [
      "bar->cercar:0.8812",
      "break->quebrar:0.8063",
      "stall->cuadra:0.8063",
      "billow->oleaje:0.7562",
      "bridle->reprimir:0.7562"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0413",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 12,
      "low_need": 32
    },
    "high_sample_triggers": [
      "bar->cercar:0.8778",
      "break->quebrar:0.8111",
      "stall->cuadra:0.8111",
      "billow->oleaje:0.7667",
      "bridle->reprimir:0.7667"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0414",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 12,
      "low_need": 32
    },
    "high_sample_triggers": [
      "bar->cercar:0.875",
      "break->quebrar:0.815",
      "stall->cuadra:0.815",
      "billow->oleaje:0.775",
      "bridle->reprimir:0.775"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0286",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 11,
      "low_need": 33
    },
    "high_sample_triggers": [
      "bar->cercar:0.8917",
      "break->quebrar:0.825",
      "stall->cuadra:0.825",
      "billow->oleaje:0.7583",
      "bridle->reprimir:0.7583"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0287",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 11,
      "low_need": 33
    },
    "high_sample_triggers": [
      "bar->cercar:0.8857",
      "break->quebrar:0.8286",
      "stall->cuadra:0.8286",
      "billow->oleaje:0.7714",
      "bridle->reprimir:0.7714"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0288",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 11,
      "low_need": 33
    },
    "high_sample_triggers": [
      "bar->cercar:0.8812",
      "break->quebrar:0.8312",
      "stall->cuadra:0.8312",
      "billow->oleaje:0.7812",
      "bridle->reprimir:0.7812"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0292",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 11,
      "low_need": 33
    },
    "high_sample_triggers": [
      "bar->cercar:0.8875",
      "break->quebrar:0.8375",
      "stall->cuadra:0.8375",
      "billow->oleaje:0.7875",
      "bridle->reprimir:0.7875"
    ]
  },
  {
    "band_strategy_id": "top_10_next_20_rest",
    "ranking_mode_id": "algorithm_need",
    "formula_id": "sweep_linear_0293",
    "scorer_id": "high_recall_soft_assist_tfidf_a0000_mneg0050",
    "top_heavy_grade_score": 0.0776,
    "primary_high_rest_failure_delta": 0.0873,
    "band_family_counts": {
      "high_need": 5,
      "middle_need": 11,
      "low_need": 33
    },
    "high_sample_triggers": [
      "bar->cercar:0.8833",
      "break->quebrar:0.8389",
      "stall->cuadra:0.8389",
      "billow->oleaje:0.7944",
      "bridle->reprimir:0.7944"
    ]
  }
]
```

## Limitations

- `top_heavy_report_reuses_49_repaired_families_so_small_slice_results_are_fragile`
- `source_exposure_is_a_zipf_band_proxy_not_observed_browser_impression_frequency`
- `scores_are_allocation_rankings_not_calibrated_failure_probabilities`
- `product_scope_surface_currently_has_no_phrase_no_winner_rows`
- `this report can guide the next LLM allocation hypothesis but cannot promote runtime policy`

## Next Steps

- Compare accepted-candidate equal-tertile rows against top-heavy source-exposure rows.
- If top-heavy rows concentrate failure and generated-evidence lift, use top-N budget curves for allocation instead of thirds.
- Keep low and middle controls in the next generation batch so the concentrated-ranking hypothesis remains falsifiable.
