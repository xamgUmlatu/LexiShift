# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-09T22:53:13Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:active-only-scale-tranche-v1-source-packaging-latest`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `32`
- Packaged evidence rows: `32`
- Excluded rows: `0`
- Family count: `16`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 32}`
- Exclusion reasons: `{}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Model: `gpt-5.4-mini`
- Input/output tokens: `7547` / `2742`
- Source packaging mutates raw LLM output: `none`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:full-family-repaired-full:adder:v-bora` | 2 | 0 | `víbora` |
| `en-es:full-family-repaired-full:adjoining:contiguo` | 2 | 0 | `contiguo` |
| `en-es:full-family-repaired-full:altitude:elevaci-n` | 2 | 0 | `elevación` |
| `en-es:full-family-repaired-full:billow:oleaje` | 2 | 0 | `oleaje` |
| `en-es:full-family-repaired-full:continue:durar` | 2 | 0 | `durar` |
| `en-es:full-family-repaired-full:current:contempor-neo` | 2 | 0 | `contemporáneo` |
| `en-es:full-family-repaired-full:emotion:emoci-n` | 2 | 0 | `emoción` |
| `en-es:full-family-repaired-full:handiwork:artesan-a` | 2 | 0 | `artesanía` |
| `en-es:full-family-repaired-full:health:salud` | 2 | 0 | `salud` |
| `en-es:full-family-repaired-full:june:junio` | 2 | 0 | `junio` |
| `en-es:full-family-repaired-full:pair:par` | 2 | 0 | `par` |
| `en-es:full-family-repaired-full:parrot:loro` | 2 | 0 | `loro` |
| `en-es:full-family-repaired-full:recover:sanar` | 2 | 0 | `sanar` |
| `en-es:full-family-repaired-full:snore:roncar` | 2 | 0 | `roncar` |
| `en-es:full-family-repaired-full:stall:cuadra` | 2 | 0 | `cuadra` |
| `en-es:full-family-repaired-full:upon:sobre` | 2 | 0 | `sobre` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
