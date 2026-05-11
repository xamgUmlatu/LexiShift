# en-es Semantic Veto Evidence-Gap Score Contribution

- Status: `ok`
- Decision: `score_contribution_ready_for_interpretation`
- Generated: `2026-05-09T21:50:57Z`
- Selected families: `5`
- Admitted generated items: `10`
- Waived generated items: `0`

## Overall Metrics

| Mode | Cases | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 25 | 0.8400 | 0.8000 | 2 | 2 | 0.8500 |
| `generated_active_only` | 25 | 0.8400 | 0.8000 | 2 | 2 | 0.8500 |
| `generated_shadow_existing_only` | 25 | 0.7600 | 0.7000 | 3 | 3 | 0.8500 |
| `generated_shadow_synthetic_only` | 25 | 0.7600 | 0.7000 | 3 | 3 | 0.8500 |
| `generated_existing_shadows` | 25 | 0.7600 | 0.7000 | 3 | 3 | 0.8500 |
| `generated_synthetic_shadows` | 25 | 0.7600 | 0.7000 | 3 | 3 | 0.8500 |

## Deltas

| Mode | Decision accuracy Δ | Replace recall Δ | Harmful replace Δ | False abstain Δ | Winner accuracy Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | 0.0000 | 0.0000 | 0 | 0 | 0.0000 |
| `generated_shadow_existing_only` | -0.0800 | -0.1000 | 1 | 1 | 0.0000 |
| `generated_shadow_synthetic_only` | -0.0800 | -0.1000 | 1 | 1 | 0.0000 |
| `generated_existing_shadows` | -0.0800 | -0.1000 | 1 | 1 | 0.0000 |
| `generated_synthetic_shadows` | -0.0800 | -0.1000 | 1 | 1 | 0.0000 |

## Policy Sweep Best By Harmful Budget

| Budget | Mode | Min active | Min margin | Phrase guard | Active rescue | Decision accuracy | Replace recall | Harmful replaces | False abstains | Winner accuracy |
| ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |

## Application Summary

### `generated_active_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `0`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `10`
- Ignored no-winner items: `0`

### `generated_shadow_existing_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `10`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_shadow_synthetic_only`
- Active evidence items applied: `0`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `10`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_existing_shadows`
- Active evidence items applied: `0`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `10`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

### `generated_synthetic_shadows`
- Active evidence items applied: `0`
- Active evidence items ignored: `0`
- Existing shadow evidence items applied: `10`
- Synthetic shadow evidence items applied: `0`
- Shadow evidence items ignored: `0`
- Ignored no-winner items: `0`

## Changed Cases

| Mode | Case | Gold | Base | Candidate | Active Δ | Shadow Δ | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0201 | She began to smile when the child waved. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_shadow_existing_only` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0201 | She began to smile when the child waved. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_shadow_synthetic_only` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0201 | She began to smile when the child waved. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_existing_shadows` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:cite:mencionar:003` | `abstain` | `abstain` | `abstain` | 0.0000 | 0.1439 | The officer may cite the driver for speeding. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:001` | `replace` | `replace` | `abstain` | -0.0000 | 0.0201 | She began to smile when the child waved. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:smile:sonre-r:005` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0027 | The dashboard listed Smile as an internal project code. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:region:comarca:003` | `abstain` | `abstain` | `abstain` | -0.0000 | -0.0398 | The scan showed swelling in the abdominal region. |
| `generated_synthetic_shadows` | `en-es:full-family-repaired-full:region:comarca:005` | `abstain` | `abstain` | `replace` | 0.0000 | -0.0197 | The dashboard listed Region as an internal project code. |
## Next Steps

- The selected generated evidence did not show immediate score lift on frozen manual cases.
- Before full spend, inspect whether thresholds are too conservative or whether generated evidence is not being applied in the right representation.

## Limitations

- `offline score-contribution probe only`
- `generated no-winner contexts are not used as runtime evidence in this probe`
- `synthetic shadow mode is diagnostic until new competitor targets are reviewed`
- `policy sweep reuses the same generated evidence batch and is not promotion evidence by itself`
- `selected batch is not broad enough to prove the full en-es heuristic curve`
