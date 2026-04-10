# en-es Semantic Shadow Campaign A Conclusion

- Campaign scope: early-node admission ablations on the manifest-driven semantic-shadow matrix
- Evidence artifacts:
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.json`
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md`

## Winning rows

- `source_only_borrowed`
  - best source-only early-node row in this campaign
  - gold candidate precision / recall: `84.0%` / `42.0%`
  - veto accuracy / abstain recall / harmful allow: `89.1%` / `51.5%` / `48.5%`
  - harmful-allow miss counts: `seed_missing=5`, `candidate_missing=1`, `promotion_miss=6`

## Losing rows

- `admission_threshold_4`
  - trigger filtering is too aggressive at this level
  - seed keep rate falls to `9.8%`
  - veto abstain recall drops to `27.3%`
  - harmful allow rises to `72.7%`

- `admission_forward_gloss_off`
- `admission_forward_gloss_half`
- `admission_reverse_shadow_off`
  - these all reduce seed keep rate and abstain recall relative to the unfiltered baseline
  - they improve gold precision slightly, but the trade is unfavorable because recall and veto usefulness both fall

## Flat rows

- `admission_threshold_2`
- `source_only_trigger_filtered`
- `admission_forward_gloss_high`
- `admission_multi_source_off`
- `admission_multi_source_high`
- `admission_reverse_shadow_high`
- `admission_multiword_penalty_off`
- `admission_multiword_penalty_strong`

These rows are effectively flat versus the base source-only baseline on the main gold and veto surfaces.
They do not produce a new frontier point.

## Borrowed-plus-filter check

- `source_only_borrowed_threshold_2`
- `source_only_borrowed_threshold_3`

Both rows collapse back to the weaker non-borrowed baseline behavior.
This means the current trigger-filtering setup removes most of the benefit created by neighbor-borrowed seeds.

## Node conclusions

- Neighbor-borrowed seed expansion is a real upstream improvement.
- Trigger filtering is not currently a productive frontier.
- Forward-gloss and reverse-shadow trigger support matter as permissive admission signals, but only enough to recover baseline behavior under filtering.
- Multi-source reward and multiword penalty appear inert in the current campaign.

## Frontier decision

- Upstream expansion remains viable.
- Upstream pruning appears saturated or counterproductive with the current trigger-support formulation.
- The next campaign should pivot to late promotion ablations, using `source_only_borrowed` as the working baseline.
