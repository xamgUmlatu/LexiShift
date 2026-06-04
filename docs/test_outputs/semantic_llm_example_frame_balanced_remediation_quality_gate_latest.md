# en-es Example-Frame Generation Quality Gate

- Status: `ok`
- Decision: `promotion_candidate`
- Generated: `2026-04-24T22:56:50Z`
- Run batch: `en-es:example-frame-missing-rows:example-frame-balanced-remediation-v1-20260425a-rekeyed:replay`
- Contract batch: `en-es:example-frame-composite:reverse-aux-plus-llm-missing-rows-plus-balanced-remediation-latest`

## Summary

- Run accepted: `6` / `6`
- Contract complete: `8` / `8`
- Best config: `prototype_reviewed_examples_surface_pos_rescue_guard`
- Best metrics: `95.0%` accuracy / `87.5%` recall / `0` harmful / `2` false abstains

## Prototype Configs

| Config | Mode | Gate | Accuracy | Recall | Harmful | False Abstain |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `prototype_reviewed_examples_family_guard` | `runtime_phrase_guard_only` | `fail` | 67.5% | 56.2% | 6 | 7 |
| `prototype_reviewed_examples_active_guard` | `runtime_phrase_guard_only` | `fail` | 77.5% | 56.2% | 2 | 7 |
| `prototype_reviewed_examples_phrase_containment_guard` | `local_containment_patterns` | `fail` | 77.5% | 56.2% | 2 | 7 |
| `prototype_reviewed_examples_surface_pos_rescue_guard` | `local_containment_patterns_plus_surface_pos` | `pass` | 95.0% | 87.5% | 0 | 2 |
| `prototype_reviewed_examples_phrase_prototype_guard` | `semantic_prototype_competition` | `fail` | 72.5% | 43.8% | 2 | 9 |

## Diagnostics

- Phrase-overreach pressure false-abstains: `9`
- Incremental phrase-prototype false-abstains: `2`
- Containment false-abstains: `0`
- Incremental containment false-abstains: `0`
- Containment overreach reduction: `2`
- Phrase containment hits: `2`
- Harmful replace residuals: `0`

### Phrase Overreach Samples

| Case | Phrase Prototype | Active Evidence |
| --- | --- | --- |
| `en-es:sentence-veto:plant:001` | The plan will plant itself in their minds by morning. | organism capable of photosynthesis |
| `en-es:sentence-veto:plant:002` | The plan will plant itself in their minds by morning. | organism capable of photosynthesis |
| `en-es:sentence-veto:play:001` | play it by ear and see how things go | The school staged a play about climate change in the auditorium. |
| `en-es:sentence-veto:check:002` | The rain check is still valid for next week. | She mailed the rent check with the signed lease renewal. |
| `en-es:sentence-veto:order:001` | in order to keep things simple, we left early | I placed an order for two laptops and a printer online. |
| `en-es:sentence-veto:order:002` | in order to keep things simple, we left early | request for some product or service |
| `en-es:sentence-veto:trip:002` | The trip wire snapped before anyone reached the gate. | We planned a quick trip to the coast for lunch. |
| `en-es:sentence-veto:report:001` | The report card came home with a smiley sticker. | information describing events |

### Incremental Phrase False-Abstain Samples

| Case | Phrase Prototype | Active Evidence |
| --- | --- | --- |
| `en-es:sentence-veto:order:001` | in order to keep things simple, we left early | I placed an order for two laptops and a printer online. |
| `en-es:sentence-veto:trip:002` | The trip wire snapped before anyone reached the gate. | We planned a quick trip to the coast for lunch. |

### Harmful Replace Samples

| Case | Predicted Winner | Active Evidence | Shadow Evidence |
| --- | --- | --- | --- |

## Recommendation

- This generated batch clears the structural contract and the prototype-quality gate; it can proceed to the next no-spend source/insertion checks before any runtime claim.
