# en-es Non-v10 Source Wave Admission Sweep

- Status: `ok`
- Decision: `semantic_complete_variant_found`
- Generated: `2026-04-29T00:21:08Z`
- Variants: `12`
- Best variant: `min0p12-definition_and_example-rows2`
- Pool size: `64`
- Selection size: `16`
- Translation support mode: `forward_only_upper_bound`
- Best semantic contract: `55` / `64`
- Admission-selected families: `16` / `16`
- Best admitted rows: `221`
- Best phrase contract: `0` / `64`
- Selection strategy: `single_variant`
- Portfolio semantic families: `76`

## Best Variant

- Variant: `min0p12-definition_and_example-rows2`
- Selected triggers: `leave, black, serve, fit, low, part, feel, still, bear, finish, throw, upset, piece, fair, show, advance, rank, like, gross, cast, fix, act, full, walk, waste, issue, firm, even, wrong, meet, stretch, rule, ride, score, crash, trim, squeeze, foul, push, air, try, single, burn, force, flush, time, subject, spare, gain, smooth, help, idle, spot, tie, slack, hand, escape, cross, view, design, better, separate, flash, split`
- Admission-selected triggers: `leave, black, serve, low, part, feel, still, bear, finish, throw, upset, piece, fair, show, advance, rank`
- WordNet rows: `303`
- Final admitted rows: `221`
- Semantic contract: `55`
- Phrase contract: `0`
- Semantic gaps: `en-es:sentence-veto:act:acto, en-es:sentence-veto:fit:acceso, en-es:sentence-veto:issue:flujo, en-es:sentence-veto:ride:m-quina, en-es:sentence-veto:single:soltero, en-es:sentence-veto:subject:sujeto, en-es:sentence-veto:walk:andar, en-es:sentence-veto:escape:escape, en-es:sentence-veto:rule:regla`

## Variant Grid

| Variant | Best | Selected | Extract Min | WordNet Rows | Admitted | Sense Rejects | Semantic | Phrase |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `min0p12-definition_preferred-rows1` | `False` | `64` | `0.12` | `161` | `138` | `23` | `48` | `0` |
| `min0p12-definition_and_example-rows2` | `True` | `64` | `0.12` | `303` | `221` | `81` | `55` | `0` |
| `min0p12-extract0-definition_and_example-rows2` | `False` | `64` | `0` | `328` | `197` | `130` | `49` | `0` |
| `min0p12-example_preferred-rows1` | `False` | `64` | `0.12` | `161` | `102` | `59` | `29` | `0` |
| `min0p16-definition_preferred-rows1` | `False` | `60` | `0.16` | `150` | `131` | `18` | `49` | `0` |
| `min0p16-definition_and_example-rows2` | `False` | `60` | `0.16` | `279` | `209` | `68` | `53` | `0` |
| `min0p16-extract0-definition_and_example-rows2` | `False` | `60` | `0` | `306` | `185` | `119` | `46` | `0` |
| `min0p16-example_preferred-rows1` | `False` | `60` | `0.16` | `150` | `98` | `52` | `29` | `0` |
| `min0p2-definition_preferred-rows1` | `False` | `49` | `0.2` | `116` | `106` | `9` | `42` | `0` |
| `min0p2-definition_and_example-rows2` | `False` | `49` | `0.2` | `214` | `172` | `40` | `44` | `0` |
| `min0p2-extract0-definition_and_example-rows2` | `False` | `49` | `0` | `242` | `157` | `83` | `39` | `0` |
| `min0p2-example_preferred-rows1` | `False` | `49` | `0.2` | `116` | `83` | `33` | `29` | `0` |

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
