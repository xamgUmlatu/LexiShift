# en-es Non-v10 Source Wave Admission Sweep

- Status: `review`
- Decision: `semantic_gaps_remain`
- Generated: `2026-04-29T00:19:52Z`
- Variants: `12`
- Best variant: `min0p12-definition_and_example-rows2`
- Pool size: `64`
- Selection size: `16`
- Translation support mode: `reverse_or_freedict_required`
- Best semantic contract: `6` / `64`
- Admission-selected families: `6` / `16`
- Best admitted rows: `19`
- Best phrase contract: `0` / `64`
- Selection strategy: `single_variant`
- Portfolio semantic families: `6`

## Best Variant

- Variant: `min0p12-definition_and_example-rows2`
- Selected triggers: `burn, force, help, hand, separate, split, trouble`
- Admission-selected triggers: `burn, force, help, hand, separate, trouble`
- WordNet rows: `27`
- Final admitted rows: `19`
- Semantic contract: `6`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:split:partido`

## Variant Grid

| Variant | Best | Selected | Extract Min | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `7` | `0.12` | `14` | `12` | `2` | `6` | `0` |
| `min0p12-definition_and_example-rows2` | `True` | `7` | `0.12` | `27` | `19` | `8` | `6` | `0` |
| `min0p12-extract0-definition_and_example-rows2` | `False` | `7` | `0` | `28` | `17` | `11` | `6` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `7` | `0.12` | `14` | `8` | `6` | `1` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `6` | `0.16` | `12` | `10` | `2` | `5` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `6` | `0.16` | `23` | `16` | `7` | `5` | `0` |
| `min0p16-extract0-definition_and_example-rows2` | `False` | `6` | `0` | `24` | `14` | `10` | `5` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `6` | `0.16` | `12` | `7` | `5` | `1` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `4` | `0.2` | `8` | `6` | `2` | `3` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `4` | `0.2` | `15` | `10` | `5` | `3` | `0` |
| `min0p2-extract0-definition_and_example-rows2` | `False` | `4` | `0` | `16` | `8` | `8` | `3` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `4` | `0.2` | `8` | `5` | `3` | `1` | `0` |

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
