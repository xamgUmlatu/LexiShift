# en-es Phrase Policy Signal Audit

- Status: `ok`
- Decision: `phrase_signal_pass`
- Generated: `2026-04-26T02:37:35Z`
- Dataset: `en_es_phrase_policy_signal_non_v10_v1`
- Case scope: `phrase_policy_signal_only`

## Summary

- Cases: `16`
- Passed: `16`
- Failed: `0`
- False positives: `0`
- False negatives: `0`

## Rows

| Case | Expected | Hit | Reason | Signals | Pass |
| --- | ---: | ---: | --- | --- | ---: |
| `en-es:phrase-signal:non-v10:v1:rock:001` | `true` | `true` | `modal_trigger_frame` | `modal_trigger_frame, subject_trigger_object_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:rock:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:draft:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:draft:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:case:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:case:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:scale:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:scale:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:line:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:line:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:point:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:point:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:ring:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:ring:002` | `false` | `false` | `none` | `none` | `true` |
| `en-es:phrase-signal:non-v10:v1:date:001` | `true` | `true` | `trigger_particle_frame` | `trigger_particle_frame, modal_trigger_frame, subject_trigger_particle_frame` | `true` |
| `en-es:phrase-signal:non-v10:v1:date:002` | `false` | `false` | `none` | `none` | `true` |

## Limitations

- `signal_only_not_end_to_end_scoring`
- `non_v10_family_senses_are_minimal`
- `does_not_validate_translation_target_quality`

## Next Steps

- promote useful non-v10 signal rows into end-to-end held-out suites once source evidence exists
- add active literal counterexamples before broadening any phrase pattern
- rerun the margin sweep when signal rows become end-to-end source cases
