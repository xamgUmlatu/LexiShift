# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-09T02:04:33Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:active-only-poc-v5-source-packaging-latest`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `48`
- Packaged evidence rows: `45`
- Excluded rows: `3`
- Family count: `24`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 45}`
- Exclusion reasons: `{'high_eval_overlap': 3}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v5`
- Model: `gpt-5.4-mini`
- Input/output tokens: `11421` / `4177`
- Source packaging mutates raw LLM output: `none`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:full-family-repaired-full:acceptable:razonable` | 2 | 0 | `razonable` |
| `en-es:full-family-repaired-full:adjoining:vecino` | 2 | 0 | `vecino` |
| `en-es:full-family-repaired-full:american:americano` | 2 | 0 | `americano` |
| `en-es:full-family-repaired-full:among:entre` | 2 | 0 | `entre` |
| `en-es:full-family-repaired-full:bar:cercar` | 2 | 0 | `cercar` |
| `en-es:full-family-repaired-full:begin:comenzar` | 2 | 0 | `comenzar` |
| `en-es:full-family-repaired-full:bouillon:caldo` | 2 | 0 | `caldo` |
| `en-es:full-family-repaired-full:break:quebrar` | 2 | 0 | `quebrar` |
| `en-es:full-family-repaired-full:bridle:reprimir` | 1 | 1 | `reprimir` |
| `en-es:full-family-repaired-full:brother:hermano` | 2 | 0 | `hermano` |
| `en-es:full-family-repaired-full:chic:elegante` | 2 | 0 | `elegante` |
| `en-es:full-family-repaired-full:control:gobernar` | 2 | 0 | `gobernar` |
| `en-es:full-family-repaired-full:december:diciembre` | 2 | 0 | `diciembre` |
| `en-es:full-family-repaired-full:dentist:dentista` | 2 | 0 | `dentista` |
| `en-es:full-family-repaired-full:entirely:enteramente` | 2 | 0 | `enteramente` |
| `en-es:full-family-repaired-full:german:alem-n` | 2 | 0 | `alemán` |
| `en-es:full-family-repaired-full:govern:gobernar` | 1 | 1 | `gobernar` |
| `en-es:full-family-repaired-full:heart:coraz-n` | 2 | 0 | `corazón` |
| `en-es:full-family-repaired-full:offset:distancia` | 2 | 0 | `distancia` |
| `en-es:full-family-repaired-full:rebate:descuento` | 2 | 0 | `descuento` |
| `en-es:full-family-repaired-full:rumanian:rumano` | 2 | 0 | `rumano` |
| `en-es:full-family-repaired-full:salesman:vendedor` | 2 | 0 | `vendedor` |
| `en-es:full-family-repaired-full:smile:sonre-r` | 1 | 1 | `sonreír` |
| `en-es:full-family-repaired-full:tomorrow:ma-ana` | 2 | 0 | `mañana` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
