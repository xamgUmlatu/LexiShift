# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-08T20:40:32Z`
- Selected families: `3`
- Admitted generated items: `13`
- Waived generated items: `2`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 11 | 0.4545 | 0.0000 | 0 | 6 | 0.7500 |
| `generated_active_only` | 11 | 0.6364 | 0.6667 | 2 | 2 | 0.7500 |
| `generated_shadow_existing_only` | 11 | 0.4545 | 0.0000 | 0 | 6 | 0.6250 |
| `generated_shadow_synthetic_only` | 11 | 0.4545 | 0.0000 | 0 | 6 | 0.5000 |
| `generated_existing_shadows` | 11 | 0.6364 | 0.6667 | 2 | 2 | 0.7500 |
| `generated_synthetic_shadows` | 11 | 0.7273 | 0.8333 | 2 | 1 | 0.6250 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.1818 | 0.6667 | 2 | -4 | 0.0000 |
| `generated_shadow_existing_only` | 0.0000 | 0.0000 | 0 | 0 | -0.1250 |
| `generated_shadow_synthetic_only` | 0.0000 | 0.0000 | 0 | 0 | -0.2500 |
| `generated_existing_shadows` | 0.1818 | 0.6667 | 2 | -4 | 0.0000 |
| `generated_synthetic_shadows` | 0.2727 | 0.8333 | 2 | -5 | -0.1250 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `generated_shadow_existing_only` | 0.0500 | 0.0000 | `off` | `off` | 0.4545 | 0.0000 | 0 | 6 | 0.6250 |
| 1 | `generated_active_only` | 0.0500 | 0.0500 | `off` | `off` | 0.7273 | 0.6667 | 1 | 2 | 0.7500 |
| 2 | `generated_synthetic_shadows` | 0.0500 | 0.0000 | `off` | `off` | 0.7273 | 0.8333 | 2 | 1 | 0.6250 |

## Application Summary

### `generated_active_only`
- Active evidence items applied: `6`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `4`
- Ignored no-winner items: `3`

### `generated_shadow_existing_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `6`
- Existing shadow evidence items applied: `2`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `3`

### `generated_shadow_synthetic_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `6`
- Existing shadow evidence items applied: `3`
- Synthetic shadow evidence items applied: `1`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `3`

### `generated_existing_shadows`
- Active evidence items applied: `6`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `2`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `3`

### `generated_synthetic_shadows`
- Active evidence items applied: `6`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `3`
- Synthetic shadow evidence items applied: `1`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `3`

## Changed Cases

| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `abstain` | `replace` | 0.0594 | 0.0000 | She began to smile when the child waved. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `replace` | 0.1178 | 0.0000 | He tried to smile for the camera. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `replace` | 0.1284 | 0.0000 | Her smile returned after the good news. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `replace` | 0.0430 | 0.0014 | The dashboard listed Smile as an internal project code. |
| `generated_active_only` | `en-es:full-family-repaired-full:entirely:enteramente:001` | `replace` | `abstain` | `replace` | 0.0644 | 0.0000 | The decision was entirely voluntary. |
| `generated_active_only` | `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | 0.1082 | 0.0000 | She was entirely satisfied with the meal. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0256 | She began to smile when the child waved. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0479 | He tried to smile for the camera. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0361 | Her smile returned after the good news. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0237 | She began to smile when the child waved. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0472 | He tried to smile for the camera. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0357 | Her smile returned after the good news. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:brother:hermano:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0693 | The monks called each brother to the chapel. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:brother:hermano:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0162 | The dashboard listed Brother as an internal project code. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `abstain` | `replace` | 0.0564 | 0.0203 | She began to smile when the child waved. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `replace` | 0.1080 | 0.0397 | He tried to smile for the camera. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `replace` | 0.1289 | 0.0321 | Her smile returned after the good news. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `replace` | 0.0388 | 0.0084 | The dashboard listed Smile as an internal project code. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:entirely:enteramente:001` | `replace` | `abstain` | `replace` | 0.0625 | 0.0000 | The decision was entirely voluntary. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | 0.1072 | 0.0000 | She was entirely satisfied with the meal. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `abstain` | `replace` | 0.0550 | 0.0191 | She began to smile when the child waved. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `replace` | 0.1086 | 0.0394 | He tried to smile for the camera. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `replace` | 0.1286 | 0.0319 | Her smile returned after the good news. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `replace` | 0.0386 | 0.0091 | The dashboard listed Smile as an internal project code. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:brother:hermano:001` | `replace` | `abstain` | `replace` | 0.0502 | 0.0000 | My brother still lives near our parents. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:brother:hermano:002` | `replace` | `abstain` | `abstain` | 0.0344 | 0.0593 | The monks called each brother to the chapel. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:brother:hermano:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0129 | The dashboard listed Brother as an internal project code. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:entirely:enteramente:001` | `replace` | `abstain` | `replace` | 0.0622 | 0.0000 | The decision was entirely voluntary. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | 0.1077 | 0.0000 | She was entirely satisfied with the meal. |
## Next Steps

- Inspect the family-level deltas and review queued non-active generated rows.
- If review does not find role pollution, run the full 72-request pilot.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
