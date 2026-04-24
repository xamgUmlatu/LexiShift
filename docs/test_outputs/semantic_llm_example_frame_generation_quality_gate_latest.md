# en-es Example-Frame Generation Quality Gate

- Status: `reject`
- Decision: `analysis_only`
- Generated: `2026-04-24T21:36:05Z`
- Run batch: `en-es:example-frame-missing-rows:example-frame-missing-rows-v1-20260425a`
- Contract batch: `en-es:example-frame-composite:reverse-aux-plus-llm-missing-rows-latest`

## Summary

- Run accepted: `11` / `11`
- Contract complete: `8` / `8`
- Best config: `prototype_reviewed_examples_active_guard`
- Best metrics: `67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains

## Prototype Configs

| Config | Gate | Accuracy | Recall | Harmful | False Abstain |
| --- | --- | ---: | ---: | ---: | ---: |
| `prototype_reviewed_examples_family_guard` | `fail` | 60.0% | 31.2% | 5 | 11 |
| `prototype_reviewed_examples_active_guard` | `fail` | 67.5% | 31.2% | 2 | 11 |
| `prototype_reviewed_examples_phrase_prototype_guard` | `fail` | 62.5% | 18.8% | 2 | 13 |

## Diagnostics

- Phrase overreach false-abstains: `12`
- Harmful replace residuals: `2`

### Phrase Overreach Samples

| Case | Phrase Prototype | Active Evidence |
| --- | --- | --- |
| `en-es:sentence-veto:plant:001` | The plan will plant itself in their minds by morning. | organism capable of photosynthesis |
| `en-es:sentence-veto:plant:002` | The plan will plant itself in their minds by morning. | organism capable of photosynthesis |
| `en-es:sentence-veto:play:001` | play it by ear and see how things go | The school staged a play about climate change in the auditorium. |
| `en-es:sentence-veto:play:002` | play it by ear and see how things go | The school staged a play about climate change in the auditorium. |
| `en-es:sentence-veto:check:001` | The rain check is still valid for next week. | mark used as an indicator |
| `en-es:sentence-veto:check:002` | The rain check is still valid for next week. | mark used as an indicator |
| `en-es:sentence-veto:order:001` | in order to keep things simple, we left early | request for some product or service |
| `en-es:sentence-veto:order:002` | in order to keep things simple, we left early | request for some product or service |

### Harmful Replace Samples

| Case | Predicted Winner | Active Evidence | Shadow Evidence |
| --- | --- | --- | --- |
| `en-es:sentence-veto:report:003` | `en-es:sentence-veto:report:informe:active` | information describing events | to relate details of |
| `en-es:sentence-veto:report:004` | `en-es:sentence-veto:report:informe:active` | information describing events | to relate details of |

## Recommendation

- Keep this generated batch analysis-only. It clears the row contract but fails the prototype-quality gate: best config `prototype_reviewed_examples_active_guard` is `67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains. Diagnostics show `12` phrase-overreach false abstains and `2` harmful active wins. The next source pass should not merely fill missing rows; it should generate balanced active/shadow exemplars and treat phrase-control rows as containment patterns or separately gated abstain evidence, not broad semantic competitors.
