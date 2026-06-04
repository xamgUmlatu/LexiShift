# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-09T22:31:02Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:product-scope-band-grading-v1-active-only-source-packaging-latest`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `67`
- Packaged evidence rows: `35`
- Excluded rows: `1`
- Family count: `18`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 35}`
- Exclusion reasons: `{'high_eval_overlap': 1}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Model: `gpt-5.4-mini`
- Input/output tokens: `36840` / `11899`
- Source packaging mutates raw LLM output: `none`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:full-family-repaired-full:american:americano` | 2 | 0 | `americano` |
| `en-es:full-family-repaired-full:argentinean:argentino` | 2 | 0 | `argentino` |
| `en-es:full-family-repaired-full:bar:cercar` | 2 | 0 | `cercar` |
| `en-es:full-family-repaired-full:cite:mencionar` | 2 | 0 | `mencionar` |
| `en-es:full-family-repaired-full:control:gobernar` | 2 | 0 | `gobernar` |
| `en-es:full-family-repaired-full:dentist:dentista` | 2 | 0 | `dentista` |
| `en-es:full-family-repaired-full:endure:durar` | 2 | 0 | `durar` |
| `en-es:full-family-repaired-full:except:excepto` | 2 | 0 | `excepto` |
| `en-es:full-family-repaired-full:german:alem-n` | 2 | 0 | `alemán` |
| `en-es:full-family-repaired-full:govern:gobernar` | 2 | 0 | `gobernar` |
| `en-es:full-family-repaired-full:owe:deber` | 2 | 0 | `deber` |
| `en-es:full-family-repaired-full:pub:taberna` | 2 | 0 | `taberna` |
| `en-es:full-family-repaired-full:region:comarca` | 2 | 0 | `comarca` |
| `en-es:full-family-repaired-full:rumanian:rumano` | 2 | 0 | `rumano` |
| `en-es:full-family-repaired-full:russian:ruso` | 2 | 0 | `ruso` |
| `en-es:full-family-repaired-full:shortage:falta` | 2 | 0 | `falta` |
| `en-es:full-family-repaired-full:smile:sonre-r` | 1 | 1 | `sonreír` |
| `en-es:full-family-repaired-full:tomorrow:ma-ana` | 2 | 0 | `mañana` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
