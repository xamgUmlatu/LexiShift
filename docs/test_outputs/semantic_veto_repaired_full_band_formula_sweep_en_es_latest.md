# en-es Semantic Veto Repaired-Full Band Formula Sweep

- Status: `ok`
- Decision: `repaired_full_band_formula_sweep_established`
- Generated: `2026-05-07T19:55:26Z`
- Families: `49`
- Observations: `98`
- Fixed formulas: `10`
- Sweep formulas: `3124`
- Split counts: `{"discovery_proxy": 70, "locked_eval_proxy": 28}`

## Methodology

Compare programmatic family-level heuristics for ranking the source-target families most likely to benefit from LLM-generated semantic evidence.

Formula inputs are family-level signals that can be computed before seeing the test outcomes. Gold labels and predicted outcomes are used only for evaluation.

## Best Formula By Scope

| scope | formula | family | scorer | discovery rho | locked rho | top-k lift | brier | top triggers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_formulas::sentence_transformer_cosine | sweep_linear_0040 | sweep_linear | sentence_transformer_cosine | 0.1558 | -0.6103 | 0.7656 | 0.1750 | bar->cercar, break->quebrar, control->gobernar, offset->distancia, stall->cuadra |
| fixed_formulas::sentence_transformer_cosine | pos_shape_only | fixed_single_signal | sentence_transformer_cosine | 0.1044 | -0.4988 | 0.8981 | 0.2147 | american->americano, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::tfidf_cosine | source_zipf_only | fixed_single_signal | tfidf_cosine | 0.1915 | -0.1225 | 0.9630 | 0.1194 | american->americano, among->entre, break->quebrar, brother->hermano, continue->durar |
| fixed_formulas::tfidf_cosine | source_zipf_only | fixed_single_signal | tfidf_cosine | 0.1915 | -0.1225 | 0.9630 | 0.1194 | american->americano, among->entre, break->quebrar, brother->hermano, continue->durar |

## Top Need Rows

| scorer | rank | trigger | target | need | observed failure | cases | formula |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sentence_transformer_cosine | 1 | bar | cercar | 0.9250 | 0.0% | 0 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 2 | break | quebrar | 0.9250 | 20.0% | 1 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 3 | control | gobernar | 0.9250 | 40.0% | 2 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 4 | offset | distancia | 0.9250 | 20.0% | 1 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 5 | stall | cuadra | 0.9250 | 20.0% | 1 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 6 | american | americano | 0.8250 | 33.3% | 1 / 3 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 7 | billow | oleaje | 0.8250 | 0.0% | 0 / 5 | sweep_linear_0040_selected |
| sentence_transformer_cosine | 8 | bridle | reprimir | 0.8250 | 40.0% | 2 / 5 | sweep_linear_0040_selected |
| tfidf_cosine | 1 | american | americano | 1.0000 | 66.7% | 2 / 3 | sweep_linear_0625_selected |
| tfidf_cosine | 2 | among | entre | 1.0000 | 66.7% | 2 / 3 | sweep_linear_0625_selected |
| tfidf_cosine | 3 | break | quebrar | 1.0000 | 20.0% | 1 / 5 | sweep_linear_0625_selected |
| tfidf_cosine | 4 | brother | hermano | 1.0000 | 66.7% | 2 / 3 | sweep_linear_0625_selected |
| tfidf_cosine | 5 | continue | durar | 1.0000 | 40.0% | 2 / 5 | sweep_linear_0625_selected |
| tfidf_cosine | 6 | control | gobernar | 1.0000 | 60.0% | 3 / 5 | sweep_linear_0625_selected |
| tfidf_cosine | 7 | current | contemporáneo | 1.0000 | 20.0% | 1 / 5 | sweep_linear_0625_selected |
| tfidf_cosine | 8 | december | diciembre | 1.0000 | 66.7% | 2 / 3 | sweep_linear_0625_selected |

## Formula Definitions

| Formula family | Description |
| --- | --- |
| `fixed_single_signal` | One feature at a time: source band, target band, polysemy, POS shape, or shadow coverage. |
| `fixed_linear` | Hand-authored additive formulas to compare intuitive compositions. |
| `fixed_max` | Risk is the largest single warning signal. |
| `fixed_interaction` | Additive formula with a source-frequency by polysemy product term. |
| `sweep_linear` | Discrete normalized weight sweep across the five family-level signals. |

## Limitations

- `only_49_user_approved_repaired_families_so_correlation_is_still_fragile`
- `zipf_values_are_bands_not_exact_frequency_ranks_in_this_lane`
- `internal_locked_eval_proxy_is_not_a_future_heldout_set`
- `shadow_coverage_is_available_for_this_dataset_but_needs_full_inventory_equivalent`
- `ranking_quality_must_be_rechecked_after_llm_evidence_generation`

## Next Steps

- Use the best stable formula family to choose a small top-N LLM evidence pilot.
- Include low-ranked controls in that pilot so the ranking can be falsified.
- Do not tune runtime thresholds from this report alone.
