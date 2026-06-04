# en-es Non-v10 Source Wave Admission Sweep

- Status: `ok`
- Decision: `semantic_complete_variant_found`
- Generated: `2026-04-28T01:19:28Z`
- Variants: `9`
- Best variant: `min0p2-definition_and_example-rows2`
- Pool size: `32`
- Selection size: `16`
- Translation support mode: `forward_only_upper_bound`
- Best semantic contract: `31` / `32`
- Admission-selected families: `16` / `16`
- Best admitted rows: `111`
- Best phrase contract: `0` / `32`

## Best Variant

- Variant: `min0p2-definition_and_example-rows2`
- Selected triggers: `leave, black, change, serve, look, dry, fit, low, part, feel, use, still, bear, finish, fast, train, land, mean, advance, end, like, gross, cast, fix, offer, present, walk, firm, even, wrong, stretch, rule`
- Admission-selected triggers: `leave, black, change, serve, look, dry, fit, low, part, feel, use, still, bear, finish, fast, train`
- WordNet rows: `143`
- Final admitted rows: `111`
- Semantic contract: `31`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:end:fin`

## Variant Grid

| Variant | Best | Selected | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `32` | `81` | `70` | `11` | `26` | `0` |
| `min0p12-definition_and_example-rows2` | `False` | `32` | `155` | `119` | `35` | `29` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `32` | `81` | `57` | `24` | `18` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `32` | `81` | `72` | `9` | `28` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `32` | `156` | `118` | `37` | `30` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `32` | `81` | `54` | `27` | `18` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `32` | `75` | `68` | `7` | `30` | `0` |
| `min0p2-definition_and_example-rows2` | `True` | `32` | `143` | `111` | `31` | `31` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `32` | `75` | `51` | `24` | `18` | `0` |

## Limitations

- `draft_waves_are_unreviewed_and_not_promotion_candidates`
- `phrase_control_rows_are_not_generated_by_the_wordnet_adapter`
- `heldout_validation_is_not_included_in_this_screening_sweep`
- `admission_selected_wave_is_a_control_selection_not_a_reviewed_dataset`
- `forward_only_translations_are_upper_bound_not_promotion_evidence`

## Next Steps

- use the best semantic variant as the source-coverage control
- convert upper-bound families into supported rows through reverse or reviewed source evidence
- materialize the admission-selected wave as a draft dataset
- build phrase-containment rows through a separate containment-only lane
- add independent held-out cases before any promotion claim
