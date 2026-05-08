# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-08T20:38:08Z`
- Selected families: `24`
- Admitted generated items: `48`
- Waived generated items: `0`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 91 | 0.5055 | 0.0833 | 1 | 44 | 0.7015 |
| `generated_active_only` | 91 | 0.7363 | 0.5208 | 1 | 23 | 0.8060 |
| `generated_shadow_existing_only` | 91 | 0.5055 | 0.0833 | 1 | 44 | 0.7015 |
| `generated_shadow_synthetic_only` | 91 | 0.5055 | 0.0833 | 1 | 44 | 0.7015 |
| `generated_existing_shadows` | 91 | 0.7363 | 0.5208 | 1 | 23 | 0.8060 |
| `generated_synthetic_shadows` | 91 | 0.7363 | 0.5208 | 1 | 23 | 0.8060 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.2308 | 0.4375 | 0 | -21 | 0.1045 |
| `generated_shadow_existing_only` | 0.0000 | 0.0000 | 0 | 0 | 0.0000 |
| `generated_shadow_synthetic_only` | 0.0000 | 0.0000 | 0 | 0 | 0.0000 |
| `generated_existing_shadows` | 0.2308 | 0.4375 | 0 | -21 | 0.1045 |
| `generated_synthetic_shadows` | 0.2308 | 0.4375 | 0 | -21 | 0.1045 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `generated_shadow_existing_only` | 0.0500 | 0.0200 | `off` | `off` | 0.5165 | 0.0833 | 0 | 44 | 0.7015 |
| 1 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.7363 | 0.5208 | 1 | 23 | 0.8060 |
| 2 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.7363 | 0.5208 | 1 | 23 | 0.8060 |

## Application Summary

### `generated_active_only`
- Active evidence items applied: `48`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_shadow_existing_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `48`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_shadow_synthetic_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `48`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_existing_shadows`
- Active evidence items applied: `48`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_synthetic_shadows`
- Active evidence items applied: `48`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

## Changed Cases

| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `generated_active_only` | `en-es:full-family-repaired-full:break:quebrar:003` | `abstain` | `abstain` | `abstain` | 0.0221 | -0.0016 | A news alert can break the broadcast without warning. |
| `generated_active_only` | `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | 0.0697 | 0.0000 | The rancher used wire panels to bar the cattle inside the field. |
| `generated_active_only` | `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `abstain` | `replace` | 0.0348 | 0.0000 | Set the image offset to twelve pixels from the left edge. |
| `generated_active_only` | `en-es:full-family-repaired-full:offset:distancia:004` | `abstain` | `abstain` | `abstain` | 0.0125 | -0.0124 | The invoice showed a small offset for the returned item. |
| `generated_active_only` | `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `abstain` | `replace` | 0.2362 | -0.0002 | She tried to bridle her anger during the meeting. |
| `generated_active_only` | `en-es:full-family-repaired-full:bridle:reprimir:002` | `replace` | `abstain` | `replace` | 0.0935 | 0.0000 | The lawyer had to bridle his frustration after the ruling. |
| `generated_active_only` | `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `abstain` | `replace` | 0.1916 | 0.0000 | She booked an appointment with a dentist near the station. |
| `generated_active_only` | `en-es:full-family-repaired-full:bouillon:caldo:001` | `replace` | `abstain` | `replace` | 0.0566 | 0.0000 | Add bouillon to the rice for a richer flavor. |
| `generated_active_only` | `en-es:full-family-repaired-full:bouillon:caldo:002` | `replace` | `abstain` | `replace` | 0.1593 | 0.0000 | The recipe starts with bouillon and fresh herbs. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | 0.0795 | 0.0000 | The coalition hoped to control parliament after the election. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `abstain` | `replace` | 0.0572 | -0.0013 | A small council continued to control the territory after the coup. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `replace` | `abstain` | -0.0094 | -0.0003 | The study included a control group and a treatment group. |
| `generated_active_only` | `en-es:full-family-repaired-full:salesman:vendedor:001` | `replace` | `abstain` | `replace` | 0.1498 | 0.0000 | The salesman explained the warranty in detail. |
| `generated_active_only` | `en-es:full-family-repaired-full:begin:comenzar:001` | `replace` | `abstain` | `replace` | 0.1182 | 0.0000 | The lecture will begin at nine. |
| `generated_active_only` | `en-es:full-family-repaired-full:chic:elegante:001` | `replace` | `abstain` | `abstain` | 0.0364 | -0.0013 | She chose a chic black coat for the dinner. |
| `generated_active_only` | `en-es:full-family-repaired-full:chic:elegante:002` | `replace` | `abstain` | `replace` | 0.0622 | -0.0014 | The hotel lobby has a chic modern style. |
| `generated_active_only` | `en-es:full-family-repaired-full:among:entre:001` | `replace` | `abstain` | `replace` | 0.0874 | 0.0000 | The letter was hidden among the old books. |
| `generated_active_only` | `en-es:full-family-repaired-full:heart:coraz-n:001` | `replace` | `abstain` | `replace` | 0.1040 | 0.0000 | Her heart was beating quickly after the race. |
| `generated_active_only` | `en-es:full-family-repaired-full:american:americano:001` | `replace` | `abstain` | `replace` | 0.0507 | 0.0000 | The museum displayed American quilts. |
| `generated_active_only` | `en-es:full-family-repaired-full:rebate:descuento:002` | `replace` | `abstain` | `replace` | 0.0521 | -0.0017 | Customers receive a rebate after mailing the form. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `replace` | 0.0759 | 0.0000 | He tried to smile for the camera. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `replace` | 0.1286 | 0.0000 | Her smile returned after the good news. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:004` | `abstain` | `abstain` | `abstain` | 0.0284 | -0.0027 | She used a smile to thank the nurse. |
| `generated_active_only` | `en-es:full-family-repaired-full:govern:gobernar:001` | `replace` | `abstain` | `replace` | 0.1758 | 0.0000 | The elected council will govern the province. |
| `generated_active_only` | `en-es:full-family-repaired-full:govern:gobernar:002` | `replace` | `abstain` | `replace` | 0.1187 | -0.0011 | A coalition tried to govern after the election. |
| `generated_active_only` | `en-es:full-family-repaired-full:brother:hermano:001` | `replace` | `abstain` | `replace` | 0.0506 | 0.0000 | My brother still lives near our parents. |
| `generated_active_only` | `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | 0.0833 | 0.0000 | She was entirely satisfied with the meal. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:break:quebrar:003` | `abstain` | `abstain` | `abstain` | 0.0221 | -0.0016 | A news alert can break the broadcast without warning. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | 0.0697 | 0.0000 | The rancher used wire panels to bar the cattle inside the field. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `abstain` | `replace` | 0.0348 | 0.0000 | Set the image offset to twelve pixels from the left edge. |
## Next Steps

- Treat this as the one-shot active-only PoC follow-through reading.
- If the harmful-replace budget is acceptable, package the active-only generated-evidence direction instead of running another veto research loop.
- Keep shadow and no-winner generation paused unless a later product decision requires a broader semantic-veto batch.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
