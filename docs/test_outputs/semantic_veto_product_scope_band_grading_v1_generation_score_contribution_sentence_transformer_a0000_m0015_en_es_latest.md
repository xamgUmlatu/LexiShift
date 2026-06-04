# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-09T20:40:27Z`
- Selected families: `18`
- Admitted generated items: `67`
- Waived generated items: `10`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 70 | 0.7714 | 0.9167 | 13 | 3 | 0.9231 |
| `generated_active_only` | 70 | 0.7857 | 0.9722 | 14 | 1 | 0.9423 |
| `generated_shadow_existing_only` | 70 | 0.7286 | 0.8333 | 13 | 6 | 0.8846 |
| `generated_shadow_synthetic_only` | 70 | 0.7143 | 0.7778 | 12 | 8 | 0.8654 |
| `generated_existing_shadows` | 70 | 0.7571 | 0.9167 | 14 | 3 | 0.8846 |
| `generated_synthetic_shadows` | 70 | 0.7429 | 0.8611 | 13 | 5 | 0.8846 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.0143 | 0.0556 | 1 | -2 | 0.0192 |
| `generated_shadow_existing_only` | -0.0429 | -0.0833 | 0 | 3 | -0.0385 |
| `generated_shadow_synthetic_only` | -0.0571 | -0.1389 | -1 | 5 | -0.0577 |
| `generated_existing_shadows` | -0.0143 | 0.0000 | 1 | 0 | -0.0385 |
| `generated_synthetic_shadows` | -0.0286 | -0.0556 | 0 | 2 | -0.0385 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |

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
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | 0.0478 | -0.0000 | The coalition hoped to control parliament after the election. |
| `generated_active_only` | `en-es:full-family-repaired-full:control:gobernar:005` | `abstain` | `replace` | `abstain` | -0.0338 | 0.0000 | The dashboard listed Control as an internal project code. |
| `generated_active_only` | `en-es:full-family-repaired-full:cite:mencionar:002` | `replace` | `abstain` | `replace` | 0.0177 | 0.0000 | Speakers often cite this example during training. |
| `generated_active_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0011 | 0.0000 | The officer may cite the driver for speeding. |
| `generated_active_only` | `en-es:full-family-repaired-full:smile:sonre-r:003` | `abstain` | `abstain` | `abstain` | 0.0425 | 0.0000 | Her smile returned after the good news. |
| `generated_active_only` | `en-es:full-family-repaired-full:except:excepto:001` | `replace` | `abstain` | `abstain` | 0.0251 | -0.0000 | Everyone except Ana attended the meeting. |
| `generated_active_only` | `en-es:full-family-repaired-full:except:excepto:004` | `abstain` | `abstain` | `replace` | 0.0632 | 0.0000 | The report will except incomplete surveys from the total. |
| `generated_active_only` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0343 | 0.0000 | The dashboard listed Region as an internal project code. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:endure:durar:001` | `replace` | `replace` | `abstain` | 0.0000 | 0.1518 | The stone bridge may endure for centuries. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:endure:durar:002` | `replace` | `replace` | `abstain` | 0.0000 | 0.0548 | The rumor may endure long after the trial ends. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:endure:durar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | -0.0579 | She had to endure constant criticism at work. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0172 | She began to smile when the child waved. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:govern:gobernar:005` | `abstain` | `replace` | `abstain` | -0.0000 | 0.0365 | The dashboard listed Govern as an internal project code. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:american:americano:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.5261 | The museum displayed American quilts. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:american:americano:002` | `replace` | `replace` | `abstain` | 0.0000 | 0.5128 | The contract follows American legal practice. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:american:americano:003` | `abstain` | `replace` | `abstain` | 0.0000 | 0.5368 | The dashboard listed American as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:endure:durar:001` | `replace` | `replace` | `abstain` | 0.0000 | 0.1518 | The stone bridge may endure for centuries. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:endure:durar:002` | `replace` | `replace` | `abstain` | 0.0000 | 0.0548 | The rumor may endure long after the trial ends. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:endure:durar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | -0.0579 | She had to endure constant criticism at work. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0172 | She began to smile when the child waved. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:govern:gobernar:005` | `abstain` | `replace` | `abstain` | -0.0000 | 0.0365 | The dashboard listed Govern as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | 0.0478 | -0.0000 | The coalition hoped to control parliament after the election. |
## Next Steps

- The selected generated evidence did not show immediate score lift on frozen manual cases.
- Before full spend, inspect whether thresholds are too conservative or whether generated evidence is not being applied in the right representation.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
