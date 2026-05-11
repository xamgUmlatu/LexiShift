# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-09T20:44:31Z`
- Selected families: `18`
- Admitted generated items: `67`
- Waived generated items: `10`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 70 | 0.4714 | 0.0000 | 1 | 36 | 0.7115 |
| `generated_active_only` | 70 | 0.6571 | 0.3889 | 2 | 22 | 0.7500 |
| `generated_shadow_existing_only` | 70 | 0.4714 | 0.0000 | 1 | 36 | 0.6346 |
| `generated_shadow_synthetic_only` | 70 | 0.4714 | 0.0000 | 1 | 36 | 0.5962 |
| `generated_existing_shadows` | 70 | 0.6286 | 0.3333 | 2 | 24 | 0.7692 |
| `generated_synthetic_shadows` | 70 | 0.6429 | 0.3611 | 2 | 23 | 0.7500 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.1857 | 0.3889 | 1 | -14 | 0.0385 |
| `generated_shadow_existing_only` | 0.0000 | 0.0000 | 0 | 0 | -0.0769 |
| `generated_shadow_synthetic_only` | 0.0000 | 0.0000 | 0 | 0 | -0.1154 |
| `generated_existing_shadows` | 0.1571 | 0.3333 | 1 | -12 | 0.0577 |
| `generated_synthetic_shadows` | 0.1714 | 0.3611 | 1 | -13 | 0.0385 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `generated_existing_shadows` | 0.1250 | 0.0000 | `off` | `off` | 0.5429 | 0.1111 | 0 | 32 | 0.7692 |
| 1 | `generated_active_only` | 0.0750 | 0.0000 | `off` | `off` | 0.6000 | 0.2500 | 1 | 27 | 0.7500 |
| 2 | `generated_active_only` | 0.0500 | 0.0000 | `off` | `off` | 0.6571 | 0.3889 | 2 | 22 | 0.7500 |

## Application Summary

### `generated_active_only`
- Active evidence items applied: `36`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `14`
- Ignored no-winner items: `17`

### `generated_shadow_existing_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `36`
- Existing shadow evidence items applied: `13`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `17`

### `generated_shadow_synthetic_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `36`
- Existing shadow evidence items applied: `13`
- Synthetic shadow evidence items applied: `1`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `17`

### `generated_existing_shadows`
- Active evidence items applied: `36`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `13`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `17`

### `generated_synthetic_shadows`
- Active evidence items applied: `36`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `13`
- Synthetic shadow evidence items applied: `1`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `17`

## Changed Cases

| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `generated_active_only` | `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | 0.0516 | 0.0000 | The rancher used wire panels to bar the cattle inside the field. |
| `generated_active_only` | `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `abstain` | `replace` | 0.1559 | 0.0000 | She booked an appointment with a dentist near the station. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | 0.0887 | 0.0000 | The coalition hoped to control parliament after the election. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `abstain` | `replace` | 0.0528 | -0.0006 | A small council continued to control the territory after the coup. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `replace` | `abstain` | -0.0264 | -0.0064 | The study included a control group and a treatment group. |
| `generated_active_only` | `en-es:full-family-repaired-full:rumanian:rumano:001` | `replace` | `abstain` | `replace` | 0.0732 | 0.0000 | The museum displayed Rumanian folk costumes. |
| `generated_active_only` | `en-es:full-family-repaired-full:pub:taberna:002` | `replace` | `abstain` | `replace` | 0.0358 | 0.0000 | The old pub serves soup and local beer. |
| `generated_active_only` | `en-es:full-family-repaired-full:cite:mencionar:001` | `replace` | `abstain` | `replace` | 0.0862 | 0.0000 | The report will cite several local witnesses. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:002` | `replace` | `abstain` | `replace` | 0.0821 | 0.0000 | He tried to smile for the camera. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `replace` | 0.1243 | 0.0000 | Her smile returned after the good news. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:004` | `abstain` | `abstain` | `abstain` | 0.0288 | -0.0006 | She used a smile to thank the nurse. |
| `generated_active_only` | `en-es:full-family-repaired-full:govern:gobernar:001` | `replace` | `abstain` | `replace` | 0.1525 | 0.0000 | The elected council will govern the province. |
| `generated_active_only` | `en-es:full-family-repaired-full:govern:gobernar:002` | `replace` | `abstain` | `abstain` | 0.0129 | -0.0007 | A coalition tried to govern after the election. |
| `generated_active_only` | `en-es:full-family-repaired-full:shortage:falta:001` | `replace` | `abstain` | `replace` | 0.0357 | 0.0000 | The town faced a water shortage during summer. |
| `generated_active_only` | `en-es:full-family-repaired-full:shortage:falta:002` | `replace` | `abstain` | `replace` | 0.1763 | 0.0000 | A shortage of nurses delayed the clinic opening. |
| `generated_active_only` | `en-es:full-family-repaired-full:except:excepto:002` | `replace` | `abstain` | `replace` | 0.1058 | 0.0000 | The office is open every day except Sunday. |
| `generated_active_only` | `en-es:full-family-repaired-full:except:excepto:004` | `abstain` | `abstain` | `replace` | 0.0574 | 0.0000 | The report will except incomplete surveys from the total. |
| `generated_active_only` | `en-es:full-family-repaired-full:region:comarca:002` | `replace` | `abstain` | `replace` | 0.1052 | -0.0019 | Local officials met with leaders from the mountain region. |
| `generated_active_only` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | 0.0379 | -0.0044 | The scan showed swelling in the abdominal region. |
| `generated_active_only` | `en-es:full-family-repaired-full:owe:deber:002` | `replace` | `abstain` | `replace` | 0.0416 | 0.0000 | We owe our success to careful planning. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0224 | The rancher used wire panels to bar the cattle inside the field. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bar:cercar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1700 | They met at the bar after work. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:bar:cercar:004` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0396 | The violin enters on the second bar of the song. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0308 | The coalition hoped to control parliament after the election. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:control:gobernar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0364 | Use the slider to control the volume. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0358 | The report will cite several local witnesses. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.2011 | The officer may cite the driver for speeding. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:004` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0483 | The department will cite her for bravery. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:005` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.0087 | The dashboard listed Cite as an internal project code. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:endure:durar:001` | `replace` | `abstain` | `abstain` | 0.0000 | 0.0557 | The stone bridge may endure for centuries. |
## Next Steps

- Inspect the family-level deltas and review queued non-active generated rows.
- If review does not find role pollution, run the full 72-request pilot.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
