# en-es Non-v10 Source Wave Admission Sweep

- Status: `review`
- Decision: `semantic_gaps_remain`
- Generated: `2026-04-27T23:06:48Z`
- Variants: `9`
- Best variant: `min0p16-definition_and_example-rows2`
- Pool size: `32`
- Selection size: `16`
- Best semantic contract: `9` / `32`
- Admission-selected families: `9` / `16`
- Best admitted rows: `35`
- Best phrase contract: `0` / `32`

## Best Variant

- Variant: `min0p16-definition_and_example-rows2`
- Selected triggers: `change, look, use, train, land, end, offer, rest, sign, answer, quiet`
- Admission-selected triggers: `look, use, train, land, offer, rest, sign, answer, quiet`
- WordNet rows: `50`
- Final admitted rows: `35`
- Semantic contract: `9`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:change:cambio, en-es:sentence-veto:end:fin`

## Variant Grid

| Variant | Best | Selected | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `11` | `26` | `20` | `6` | `6` | `0` |
| `min0p12-definition_and_example-rows2` | `False` | `11` | `52` | `35` | `17` | `9` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `11` | `26` | `16` | `10` | `6` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `11` | `25` | `20` | `5` | `7` | `0` |
| `min0p16-definition_and_example-rows2` | `True` | `11` | `50` | `35` | `15` | `9` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `11` | `25` | `16` | `9` | `6` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `8` | `17` | `15` | `2` | `6` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `8` | `34` | `27` | `7` | `7` | `0` |
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
