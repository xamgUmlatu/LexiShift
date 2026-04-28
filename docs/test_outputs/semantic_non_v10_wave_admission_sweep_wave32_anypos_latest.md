# en-es Non-v10 Source Wave Admission Sweep

- Status: `review`
- Decision: `semantic_gaps_remain`
- Generated: `2026-04-28T01:18:12Z`
- Variants: `9`
- Best variant: `min0p12-definition_and_example-rows2`
- Pool size: `32`
- Selection size: `16`
- Translation support mode: `reverse_or_freedict_required`
- Best semantic contract: `14` / `32`
- Admission-selected families: `14` / `16`
- Best admitted rows: `51`
- Best phrase contract: `0` / `32`

## Best Variant

- Variant: `min0p12-definition_and_example-rows2`
- Selected triggers: `change, look, dry, use, plain, fast, train, land, mean, end, offer, rest, present, sign, answer, quiet`
- Admission-selected triggers: `look, dry, use, plain, fast, train, land, mean, offer, rest, present, sign, answer, quiet`
- WordNet rows: `72`
- Final admitted rows: `51`
- Semantic contract: `14`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:change:cambio, en-es:sentence-veto:end:fin`

## Variant Grid

| Variant | Best | Selected | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `16` | `36` | `30` | `6` | `11` | `0` |
| `min0p12-definition_and_example-rows2` | `True` | `16` | `72` | `51` | `21` | `14` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `16` | `36` | `22` | `14` | `7` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `15` | `33` | `28` | `5` | `11` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `15` | `66` | `47` | `19` | `13` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `15` | `33` | `20` | `13` | `6` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `11` | `23` | `21` | `2` | `9` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `11` | `46` | `36` | `10` | `10` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `11` | `23` | `15` | `8` | `5` | `0` |

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
