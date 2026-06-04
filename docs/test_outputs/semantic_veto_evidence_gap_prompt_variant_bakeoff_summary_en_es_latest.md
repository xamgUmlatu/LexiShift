# en-es Semantic Veto Prompt Variant Bakeoff Summary

- Status: `ok`
- Decision: `prompt_variant_bakeoff_ready_for_interpretation`
- Generated: `2026-05-09T00:24:08Z`
- Primary view: `no_high_eval_overlap_sentence_only`
- Best primary variant: `v5_refresh_control`
- Total estimated API cost: `$0.1437`

## Primary Results

| Variant | Generation | Admission | Items | Rejected | Cost | Accuracy | Recall | Harmful | False abstains | Fixed | Regressed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v5_refresh_control` | `ok` | `ok` | 48 | 0 | $0.0275 | 0.7363 | 0.5000 | 0 | 24 | 21 | 0 |
| `v6_pos_only` | `ok` | `ok` | 48 | 0 | $0.0379 | 0.6813 | 0.4375 | 2 | 27 | 19 | 3 |
| `v6_diversity_only` | `ok` | `ok` | 48 | 0 | $0.0387 | 0.6703 | 0.4167 | 2 | 28 | 18 | 3 |
| `v6_pos_diversity` | `ok` | `review` | 47 | 1 | $0.0397 | 0.6813 | 0.4167 | 1 | 28 | 18 | 2 |

## Mechanical Audit Counts

| Variant | High eval overlap | POS weak | Definition-like | Target lemma in note | Model POS labels | Model topic labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `v5_refresh_control` | 2 | 6 | 1 | 0 | 0 | 0 |
| `v6_pos_only` | 2 | 3 | 0 | 0 | 48 | 48 |
| `v6_diversity_only` | 4 | 2 | 0 | 0 | 48 | 48 |
| `v6_pos_diversity` | 1 | 1 | 0 | 0 | 47 | 47 |

## Interpretation

- `v5_refresh_control` is the best primary-view candidate under the current ordering: avoid harmful replacements first, then avoid admission rejects, then maximize decision accuracy.
- The new v6 prompt constraints did not beat the simpler v5 control on downstream veto decisions in this run.
- `v6_pos_only` successfully produced model POS/topic labels and reduced POS-weak rows, but that mechanical improvement did not translate into the best veto score.
- `v6_pos_only` POS-weak rows: 3.
- `v6_pos_diversity` had one admission rejection because a generated sentence used an inflected form instead of the exact replacement trigger.

## Methodology

- `runtime_policy_change`: none
- `threshold_tuning`: none
- `raw_llm_output_mutation`: none
- `same_family_denominator`: all variants use the frozen 24 active-only PoC request packet
- `primary_comparison_view`: no_high_eval_overlap_sentence_only
- `cost_rate_source`: rates passed to the live run and this summary

## Limitations

- `active-only prompt bakeoff over 24 selected en-es families`
- `postprocess labels are mechanical diagnostics, not human semantic review`
- `this does not test shadow or no-winner generation quality`
- `one variant can have fewer admitted rows if admission rejected raw model output`
- `prompt variants should not change runtime policy without a later locked evaluation pass`
