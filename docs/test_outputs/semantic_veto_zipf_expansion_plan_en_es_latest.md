# en-es Semantic Veto Zipf Expansion Plan

- Status: `ok`
- Decision: `zipf_expansion_plan_established`
- Generated: `2026-05-05T21:59:32Z`
- Represented Zipf bands: `2` / `4`
- P0 bands: `3`
- Recommended manual/observed rows: `96`
- Recommended LLM discovery rows: `84`
- Recommended locked-eval rows: `42`

## Expansion Rows

| Priority | Zipf Band | Rep Cases | Pos Allow | Neg Abstain | False Abstain | Manual/Observed | LLM Discovery | Locked Eval | Reason | Example Triggers |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `P0` | `zipf_3_to_4_mid` | `0` | `n/a` | `n/a` | `0` | `40` | `24` | `12` | `missing_representative_control_band` |  |
| `P0` | `zipf_below_3_rare` | `0` | `n/a` | `n/a` | `0` | `40` | `24` | `12` | `missing_representative_control_band` |  |
| `P0` | `zipf_5_plus_very_common` | `68` | `13.3%` | `100.0%` | `26` | `16` | `24` | `12` | `very_common_positive_false_abstain_mass` | ball, park, bank, play, board, match, table, watch |
| `P1` | `zipf_4_to_5_common` | `52` | `39.1%` | `100.0%` | `14` | `0` | `12` | `6` | `maintain_as_curve_control` | plant, drink, branch, spring |

## Interpretation

- The very-common band is not underfilled by raw row count, but it is the clearest false-abstain problem for good replacements.
- The mid and rare bands are absent from the representative-proxy lane, so they are controls for the frequency-curve hypothesis.
- This plan separates row collection from LLM generation: representative rows first, generated discovery and locked-eval rows second.

## Limitations

- `zipf_band_plan_is_not_a_runtime_policy_change`
- `representative_proxy_still_needs_human_review_and_observed_context_refresh`
- `zipf_frequency_is_not_cefr_or_user_known_word_level`
- `llm_rows_should_be_generated_after_prompt_contract_review_not_from_this_report_alone`

## Next Steps

- Human-review the current representative gap rows before promotion claims.
- Add representative observed or corpus-like rows for underrepresented Zipf bands before claiming a full curve.
- Use P0 very-common positive-active failures to design LLM source/evidence generation prompts.
- Keep generated discovery rows separate from locked evaluation rows.
