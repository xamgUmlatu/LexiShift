# en-es Non-v10 Source Wave Admission Sweep

- Status: `review`
- Decision: `semantic_gaps_remain`
- Generated: `2026-04-27T22:31:50Z`
- Variants: `9`
- Best variant: `min0p2-definition_and_example-rows2`
- Pool size: `8`
- Selection size: `8`
- Best semantic contract: `7` / `8`
- Admission-selected families: `7` / `8`
- Best admitted rows: `27`
- Best phrase contract: `0` / `8`

## Best Variant

- Variant: `min0p2-definition_and_example-rows2`
- Selected triggers: `look, use, train, land, end, offer, sign, quiet`
- Admission-selected triggers: `look, use, train, land, offer, sign, quiet`
- WordNet rows: `34`
- Final admitted rows: `27`
- Semantic contract: `7`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:end:fin`

## Variant Grid

| Variant | Best | Selected | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `8` | `18` | `14` | `4` | `4` | `0` |
| `min0p12-definition_and_example-rows2` | `False` | `8` | `36` | `26` | `10` | `6` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `8` | `18` | `13` | `5` | `5` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `8` | `17` | `14` | `3` | `5` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `8` | `34` | `26` | `8` | `6` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `8` | `17` | `13` | `4` | `5` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `8` | `17` | `15` | `2` | `6` | `0` |
| `min0p2-definition_and_example-rows2` | `True` | `8` | `34` | `27` | `7` | `7` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `8` | `17` | `12` | `5` | `5` | `0` |

## Limitations

- `draft_waves_are_unreviewed_and_not_promotion_candidates`
- `phrase_control_rows_are_not_generated_by_the_wordnet_adapter`
- `heldout_validation_is_not_included_in_this_screening_sweep`
- `admission_selected_wave_is_a_control_selection_not_a_reviewed_dataset`

## Next Steps

- use the best semantic variant as the source-coverage control
- materialize the admission-selected wave as a draft dataset
- build phrase-containment rows through a separate containment-only lane
- add independent held-out cases before any promotion claim
