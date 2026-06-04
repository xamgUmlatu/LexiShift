# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-13T20:41:45Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:active-only-full-v1-tranche-011`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `18`
- Packaged evidence rows: `18`
- Excluded rows: `0`
- Family count: `9`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 18}`
- Exclusion reasons: `{}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Model: `gpt-5.4-mini`
- Input/output tokens: `5121` / `1795`
- Source packaging mutates raw LLM output: `none`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:srs-source-target:abate:decrecer:a89e2928` | 2 | 0 | `decrecer` |
| `en-es:srs-source-target:aberration:yerro:4e3d998f` | 2 | 0 | `yerro` |
| `en-es:srs-source-target:admonition:exhortacion:d75f45fe` | 2 | 0 | `exhortación` |
| `en-es:srs-source-target:confiscate:confiscar:6016e741` | 2 | 0 | `confiscar` |
| `en-es:srs-source-target:exhortation:exhortacion:219d6592` | 2 | 0 | `exhortación` |
| `en-es:srs-source-target:laggard:rezagado:59ff6b32` | 2 | 0 | `rezagado` |
| `en-es:srs-source-target:straggler:rezagado:e9269d35` | 2 | 0 | `rezagado` |
| `en-es:srs-source-target:transitive:transitivo:08c49e29` | 2 | 0 | `transitivo` |
| `en-es:srs-source-target:wrangle:renir:2f7db0f0` | 2 | 0 | `reñir` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
