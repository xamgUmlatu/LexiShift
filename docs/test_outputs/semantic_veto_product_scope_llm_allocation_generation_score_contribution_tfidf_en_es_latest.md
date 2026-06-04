# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-09T05:42:54Z`
- Selected families: `20`
- Admitted generated items: `84`
- Waived generated items: `10`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 60 | 0.4167 | 0.1250 | 0 | 35 | 0.6167 |
| `generated_active_only` | 60 | 0.7000 | 0.5500 | 0 | 18 | 0.7000 |
| `generated_shadow_existing_only` | 60 | 0.3833 | 0.0750 | 0 | 37 | 0.5500 |
| `generated_shadow_synthetic_only` | 60 | 0.3833 | 0.0750 | 0 | 37 | 0.5167 |
| `generated_existing_shadows` | 60 | 0.6500 | 0.4750 | 0 | 21 | 0.7167 |
| `generated_synthetic_shadows` | 60 | 0.6333 | 0.4500 | 0 | 22 | 0.6833 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.2833 | 0.4250 | 0 | -17 | 0.0833 |
| `generated_shadow_existing_only` | -0.0333 | -0.0500 | 0 | 2 | -0.0667 |
| `generated_shadow_synthetic_only` | -0.0333 | -0.0500 | 0 | 2 | -0.1000 |
| `generated_existing_shadows` | 0.2333 | 0.3500 | 0 | -14 | 0.1000 |
| `generated_synthetic_shadows` | 0.2167 | 0.3250 | 0 | -13 | 0.0667 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.7000 | 0.5500 | 0 | 18 | 0.7000 |
| 1 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.7000 | 0.5500 | 0 | 18 | 0.7000 |
| 2 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.7000 | 0.5500 | 0 | 18 | 0.7000 |

## Application Summary

### `generated_active_only`
- Active evidence items applied: `40`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `24`
- Ignored no-winner items: `20`

### `generated_shadow_existing_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `40`
- Existing shadow evidence items applied: `20`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `20`

### `generated_shadow_synthetic_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `40`
- Existing shadow evidence items applied: `22`
- Synthetic shadow evidence items applied: `2`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `20`

### `generated_existing_shadows`
- Active evidence items applied: `40`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `20`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `20`

### `generated_synthetic_shadows`
- Active evidence items applied: `40`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `22`
- Synthetic shadow evidence items applied: `2`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `20`

## Changed Cases

| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `generated_active_only` | `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `abstain` | `replace` | 0.0251 | 0.0000 | Set the image offset to twelve pixels from the left edge. |
| `generated_active_only` | `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `abstain` | `replace` | 0.1497 | -0.0032 | She tried to bridle her anger during the meeting. |
| `generated_active_only` | `en-es:full-family-repaired-full:bridle:reprimir:002` | `replace` | `abstain` | `replace` | 0.0827 | 0.0000 | The lawyer had to bridle his frustration after the ruling. |
| `generated_active_only` | `en-es:full-family-repaired-full:bouillon:caldo:001` | `replace` | `abstain` | `replace` | 0.1685 | 0.0000 | Add bouillon to the rice for a richer flavor. |
| `generated_active_only` | `en-es:full-family-repaired-full:stall:cuadra:001` | `replace` | `abstain` | `replace` | 0.0591 | 0.0000 | The horse returned to its stall after training. |
| `generated_active_only` | `en-es:full-family-repaired-full:handiwork:artesan-a:002` | `replace` | `abstain` | `replace` | 0.0659 | 0.0000 | Each carved bowl showed careful handiwork. |
| `generated_active_only` | `en-es:full-family-repaired-full:begin:comenzar:001` | `replace` | `abstain` | `replace` | 0.1237 | 0.0000 | The lecture will begin at nine. |
| `generated_active_only` | `en-es:full-family-repaired-full:chic:elegante:001` | `replace` | `abstain` | `abstain` | 0.0349 | -0.0016 | She chose a chic black coat for the dinner. |
| `generated_active_only` | `en-es:full-family-repaired-full:billow:oleaje:001` | `replace` | `abstain` | `replace` | 0.1594 | 0.0000 | A dark billow rolled across the harbor. |
| `generated_active_only` | `en-es:full-family-repaired-full:billow:oleaje:004` | `abstain` | `abstain` | `abstain` | 0.0471 | -0.0175 | The curtain started to billow in the wind. |
| `generated_active_only` | `en-es:full-family-repaired-full:snore:roncar:001` | `replace` | `abstain` | `replace` | 0.1475 | -0.0017 | He started to snore as soon as the flight took off. |
| `generated_active_only` | `en-es:full-family-repaired-full:snore:roncar:002` | `replace` | `abstain` | `abstain` | 0.0184 | -0.0021 | She could hear her roommate snore through the wall. |
| `generated_active_only` | `en-es:full-family-repaired-full:current:contempor-neo:002` | `replace` | `abstain` | `replace` | 0.1248 | 0.0000 | Current research focuses on smaller batteries. |
| `generated_active_only` | `en-es:full-family-repaired-full:parrot:loro:001` | `replace` | `abstain` | `replace` | 0.0601 | -0.0031 | A green parrot perched above the doorway. |
| `generated_active_only` | `en-es:full-family-repaired-full:parrot:loro:002` | `replace` | `abstain` | `replace` | 0.1045 | 0.0000 | The parrot repeated the visitor's greeting. |
| `generated_active_only` | `en-es:full-family-repaired-full:parrot:loro:004` | `abstain` | `abstain` | `abstain` | 0.0099 | -0.0029 | The critic called him a parrot of older writers. |
| `generated_active_only` | `en-es:full-family-repaired-full:rebate:descuento:002` | `replace` | `abstain` | `replace` | 0.0943 | -0.0016 | Customers receive a rebate after mailing the form. |
| `generated_active_only` | `en-es:full-family-repaired-full:adder:v-bora:001` | `replace` | `abstain` | `replace` | 0.1956 | 0.0000 | An adder slid through the grass near the path. |
| `generated_active_only` | `en-es:full-family-repaired-full:acceptable:razonable:001` | `replace` | `abstain` | `replace` | 0.0665 | 0.0000 | The committee considered the compromise acceptable. |
| `generated_active_only` | `en-es:full-family-repaired-full:entirely:enteramente:001` | `replace` | `abstain` | `replace` | 0.0756 | 0.0000 | The decision was entirely voluntary. |
| `generated_active_only` | `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | 0.0889 | 0.0000 | She was entirely satisfied with the meal. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:offset:distancia:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1273 | The rebate helped offset the higher shipping cost. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bridle:reprimir:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0586 | The lawyer had to bridle his frustration after the ruling. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bridle:reprimir:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.2096 | The rider checked the bridle before the parade. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bridle:reprimir:004` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0369 | He began to bridle at the accusation. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:stall:cuadra:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0247 | The horse returned to its stall after training. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:stall:cuadra:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0110 | She cleaned each stall before feeding the animals. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:stall:cuadra:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0578 | The committee tried to stall the vote until Friday. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:stall:cuadra:004` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0226 | The old truck may stall on the hill. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:current:contempor-neo:003` | `abstain` | `abstain` | `abstain` | -0.0014 | 0.0805 | The current was measured in amperes. |
## Next Steps

- Inspect the family-level deltas and review queued non-active generated rows.
- If review does not find role pollution, run the full 72-request pilot.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
