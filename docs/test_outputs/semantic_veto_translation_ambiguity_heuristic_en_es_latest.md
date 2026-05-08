# en-es Semantic Veto Translation-Ambiguity Heuristic Bakeoff

- Status: `ok`
- Decision: `translation_ambiguity_heuristic_bakeoff_established`
- Generated: `2026-05-07T20:45:20Z`
- Inventory sources: `536`
- Families: `49`
- Observations: `98`
- Fixed formulas: `15`
- Sweep formulas: `16383`
- Split counts: `{"discovery_proxy": 70, "locked_eval_proxy": 28}`

## Methodology

Test whether inventory-available ambiguity, evidence-separability, and exposure features can rank source-target families by observed semantic-veto failure rate.

Formula inputs are programmatic pre-outcome signals. Gold labels and predicted veto outcomes are used only to evaluate whether a heuristic actually ranks hard families higher.

## Signal Read

- Best stable formula: `evidence_gap_only`
- Best stable scorer: `tfidf_cosine`
- Best stable locked rho: `0.8084`
- Best stable top-k lift: `1.1840`
- Strong allocator found: `False`

## Best Formula By Scope

| scope | formula | family | scorer | discovery rho | locked rho | top-k lift | top triggers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_formulas::sentence_transformer_cosine | sweep_linear_01265 | sweep_linear | sentence_transformer_cosine | 0.1881 | -0.7347 | 0.7509 | smile->sonreír, break->quebrar, pair->par, bar->cercar, control->gobernar |
| fixed_formulas::sentence_transformer_cosine | wordnet_pos_only | fixed_single_signal | sentence_transformer_cosine | 0.1798 | -0.7911 | 0.8981 | american->americano, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::tfidf_cosine | evidence_gap_only | fixed_single_signal | tfidf_cosine | 0.5934 | 0.8084 | 1.1840 | adjoining->vecino, entirely->enteramente, bouillon->caldo, december->diciembre, american->americano |
| fixed_formulas::tfidf_cosine | evidence_gap_only | fixed_single_signal | tfidf_cosine | 0.5934 | 0.8084 | 1.1840 | adjoining->vecino, entirely->enteramente, bouillon->caldo, december->diciembre, american->americano |

## Top Need Rows

| scorer | rank | trigger | target | need | observed failure | cases | formula |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sentence_transformer_cosine | 1 | american | americano | 0.6657 | 33.3% | 1 / 3 | sweep_linear_08258 |
| sentence_transformer_cosine | 2 | break | quebrar | 0.6647 | 20.0% | 1 / 5 | sweep_linear_08258 |
| sentence_transformer_cosine | 3 | among | entre | 0.6610 | 33.3% | 1 / 3 | sweep_linear_08258 |
| sentence_transformer_cosine | 4 | control | gobernar | 0.6567 | 40.0% | 2 / 5 | sweep_linear_08258 |
| sentence_transformer_cosine | 5 | current | contemporáneo | 0.6437 | 40.0% | 2 / 5 | sweep_linear_08258 |
| sentence_transformer_cosine | 6 | upon | sobre | 0.6420 | 33.3% | 1 / 3 | sweep_linear_08258 |
| sentence_transformer_cosine | 7 | tomorrow | mañana | 0.6187 | 33.3% | 1 / 3 | sweep_linear_08258 |
| sentence_transformer_cosine | 8 | russian | ruso | 0.6177 | 33.3% | 1 / 3 | sweep_linear_08258 |
| tfidf_cosine | 1 | adjoining | vecino | 0.8750 | 33.3% | 1 / 3 | evidence_gap_only |
| tfidf_cosine | 2 | entirely | enteramente | 0.8750 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 3 | bouillon | caldo | 0.8438 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 4 | december | diciembre | 0.8438 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 5 | american | americano | 0.8125 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 6 | among | entre | 0.8125 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 7 | begin | comenzar | 0.8125 | 66.7% | 2 / 3 | evidence_gap_only |
| tfidf_cosine | 8 | dentist | dentista | 0.8125 | 66.7% | 2 / 3 | evidence_gap_only |

## Formula Definitions

| Formula family | Description |
| --- | --- |
| `fixed_single_signal` | One signal at a time: exposure, translation fanout/entropy, WordNet ambiguity, evidence overlap/gap, shadow competition, or surface no-winner risk. |
| `fixed_linear` | Hand-authored formulas for translation ambiguity, semantic separability, expected LLM value, and fixability. |
| `fixed_max` | Risk is the largest inventory-available warning signal. |
| `sweep_linear` | Discrete normalized weight sweep over exposure, fanout, WordNet, evidence-overlap, shadow, and surface-risk features. |

## Limitations

- `only_49_user_approved_repaired_families_so_correlations_are_fragile`
- `translation_entropy_is_uniform_over_current_rule_targets_not_true_usage_entropy`
- `evidence_overlap_uses_static_evidence_text_not_runtime_contexts`
- `internal_locked_eval_proxy_is_not_a_future_heldout_set`
- `strong_allocator_claims_require_a_control_bearing_llm_or_context_pilot`

## Next Steps

- Promote only formulas that show positive discovery and locked-proxy correlation.
- If no formula is strong, use top/middle/low controls in the next LLM data pilot.
- Replace uniform translation entropy with observed translation/context entropy when data exists.
