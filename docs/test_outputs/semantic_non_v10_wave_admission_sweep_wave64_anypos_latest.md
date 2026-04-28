# en-es Non-v10 Source Wave Admission Sweep

- Status: `ok`
- Decision: `semantic_complete_source_portfolio_found`
- Generated: `2026-04-28T01:35:16Z`
- Variants: `12`
- Best variant: `min0p12-extract0-definition_and_example-rows2`
- Pool size: `64`
- Selection size: `16`
- Translation support mode: `reverse_or_freedict_required`
- Best semantic contract: `15` / `64`
- Admission-selected families: `16` / `16`
- Best admitted rows: `49`
- Best phrase contract: `0` / `64`
- Selection strategy: `portfolio`
- Portfolio semantic families: `17`

## Best Variant

- Variant: `min0p12-extract0-definition_and_example-rows2`
- Selected triggers: `change, look, dry, use, plain, fast, train, land, mean, end, offer, rest, present, sign, answer, quiet`
- Admission-selected triggers: `change, look, dry, use, plain, fast, train, land, mean, end, offer, present, sign, answer, quiet`
- WordNet rows: `72`
- Final admitted rows: `49`
- Semantic contract: `15`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:rest:reposo`

## Variant Grid

| Variant | Best | Selected | Extract Min | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `16` | `0.12` | `36` | `28` | `8` | `11` | `0` |
| `min0p12-definition_and_example-rows2` | `False` | `16` | `0.12` | `72` | `48` | `24` | `15` | `0` |
| `min0p12-extract0-definition_and_example-rows2` | `True` | `16` | `0` | `72` | `49` | `23` | `15` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `16` | `0.12` | `36` | `20` | `16` | `6` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `15` | `0.16` | `33` | `26` | `7` | `10` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `15` | `0.16` | `66` | `44` | `22` | `13` | `0` |
| `min0p16-extract0-definition_and_example-rows2` | `False` | `15` | `0` | `66` | `46` | `20` | `14` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `15` | `0.16` | `33` | `18` | `15` | `5` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `11` | `0.2` | `23` | `21` | `2` | `9` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `11` | `0.2` | `46` | `34` | `12` | `10` | `0` |
| `min0p2-extract0-definition_and_example-rows2` | `False` | `11` | `0` | `46` | `36` | `10` | `11` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `11` | `0.2` | `23` | `13` | `10` | `4` | `0` |

## Limitations

- `draft_waves_are_unreviewed_and_not_promotion_candidates`
- `phrase_control_rows_are_not_generated_by_the_wordnet_adapter`
- `heldout_validation_is_not_included_in_this_screening_sweep`
- `admission_selected_wave_is_a_control_selection_not_a_reviewed_dataset`
- `portfolio_selection_combines_admitted_families_across_source_variants`

## Next Steps

- use the best semantic variant as the source-coverage control
- materialize the admission-selected wave as a draft dataset
- build phrase-containment rows through a separate containment-only lane
- add independent held-out cases before any promotion claim
