# en-es Non-v10 Source Wave Admission Sweep

- Status: `ok`
- Decision: `semantic_complete_variant_found`
- Generated: `2026-04-30T17:56:26Z`
- Variants: `12`
- Best variant: `min0p12-definition_and_example-rows2`
- Pool size: `64`
- Selection size: `16`
- Translation support mode: `forward_only_upper_bound`
- Best semantic contract: `52` / `64`
- Admission-selected families: `16` / `16`
- Best admitted rows: `214`
- Best phrase contract: `0` / `64`
- Selection strategy: `single_variant`
- Portfolio semantic families: `72`

## Best Variant

- Variant: `min0p12-definition_and_example-rows2`
- Selected triggers: `fit, like, gross, cast, fix, act, full, walk, waste, issue, firm, even, wrong, meet, stretch, rule, ride, score, crash, trim, squeeze, foul, push, air, try, single, burn, force, flush, time, subject, spare, gain, smooth, help, idle, spot, tie, slack, hand, escape, cross, view, design, better, separate, flash, split, out, drag, trace, die, trouble, slick, kill, shake, stuff, approach, cry, stir, exercise, demand, strain, strip`
- Admission-selected triggers: `like, gross, cast, fix, full, waste, firm, even, wrong, meet, stretch, score, crash, trim, squeeze, foul`
- WordNet rows: `305`
- Final admitted rows: `214`
- Semantic contract: `52`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:act:acto, en-es:sentence-veto:exercise:ejercicio, en-es:sentence-veto:fit:acceso, en-es:sentence-veto:issue:flujo, en-es:sentence-veto:kill:matanza, en-es:sentence-veto:ride:m-quina, en-es:sentence-veto:single:soltero, en-es:sentence-veto:stir:revuelo, en-es:sentence-veto:subject:sujeto, en-es:sentence-veto:walk:andar, en-es:sentence-veto:escape:escape, en-es:sentence-veto:rule:regla`

## Variant Grid

| Variant | Best | Selected | Extract Min | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `64` | `0.12` | `164` | `135` | `28` | `45` | `0` |
| `min0p12-definition_and_example-rows2` | `True` | `64` | `0.12` | `305` | `214` | `89` | `52` | `0` |
| `min0p12-extract0-definition_and_example-rows2` | `False` | `64` | `0` | `332` | `196` | `134` | `47` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `64` | `0.12` | `164` | `99` | `65` | `27` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `57` | `0.16` | `145` | `124` | `20` | `46` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `57` | `0.16` | `270` | `198` | `70` | `49` | `0` |
| `min0p16-extract0-definition_and_example-rows2` | `False` | `57` | `0` | `294` | `178` | `114` | `43` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `57` | `0.16` | `145` | `92` | `53` | `25` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `46` | `0.2` | `107` | `98` | `8` | `40` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `46` | `0.2` | `196` | `155` | `39` | `41` | `0` |
| `min0p2-extract0-definition_and_example-rows2` | `False` | `46` | `0` | `222` | `143` | `77` | `37` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `46` | `0.2` | `107` | `73` | `34` | `25` | `0` |

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
