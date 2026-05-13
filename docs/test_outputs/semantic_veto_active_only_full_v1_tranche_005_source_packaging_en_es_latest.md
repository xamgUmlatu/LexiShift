# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-13T05:10:05Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:active-only-full-v1-tranche-005`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `74`
- Packaged evidence rows: `74`
- Excluded rows: `0`
- Family count: `37`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 74}`
- Exclusion reasons: `{}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Model: `gpt-5.4-mini`
- Input/output tokens: `19644` / `6827`
- Source packaging mutates raw LLM output: `operator_repaired_after_generation`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:srs-source-target:adjacent:adyacente:4d8b8ba6` | 2 | 0 | `adyacente` |
| `en-es:srs-source-target:afar:lejos:b001ef21` | 2 | 0 | `lejos` |
| `en-es:srs-source-target:african:africano:bffdb36a` | 2 | 0 | `africano` |
| `en-es:srs-source-target:anonymous:anonimo:fa0192c0` | 2 | 0 | `anónimo` |
| `en-es:srs-source-target:australian:australiano:a28c76bb` | 2 | 0 | `australiano` |
| `en-es:srs-source-target:back:reverso:16db1377` | 2 | 0 | `reverso` |
| `en-es:srs-source-target:baker:panadero:7cede4ac` | 2 | 0 | `panadero` |
| `en-es:srs-source-target:bar:taberna:c8ebdb94` | 2 | 0 | `taberna` |
| `en-es:srs-source-target:base:basar:4d72460f` | 2 | 0 | `basar` |
| `en-es:srs-source-target:basket:cesto:267cb6a1` | 2 | 0 | `cesto` |
| `en-es:srs-source-target:bed:cauce:35138744` | 2 | 0 | `cauce` |
| `en-es:srs-source-target:bee:abeja:e7913c38` | 2 | 0 | `abeja` |
| `en-es:srs-source-target:blow:soplar:80e76972` | 2 | 0 | `soplar` |
| `en-es:srs-source-target:book:reservar:de7e11a6` | 2 | 0 | `reservar` |
| `en-es:srs-source-target:brush:cepillo:02913134` | 2 | 0 | `cepillo` |
| `en-es:srs-source-target:check:reprimir:56a101ec` | 2 | 0 | `reprimir` |
| `en-es:srs-source-target:commencement:principio:f4eeec84` | 2 | 0 | `principio` |
| `en-es:srs-source-target:commonplace:comun:9a2ae8bf` | 2 | 0 | `común` |
| `en-es:srs-source-target:cover:forrar:79548204` | 2 | 0 | `forrar` |
| `en-es:srs-source-target:cross:atravesar:37f67d2d` | 2 | 0 | `atravesar` |
| `en-es:srs-source-target:diminutive:pequeno:c72bf9f8` | 2 | 0 | `pequeño` |
| `en-es:srs-source-target:drive:propulsion:fd0fa8d5` | 2 | 0 | `propulsión` |
| `en-es:srs-source-target:envelope:sobre:cf91b697` | 2 | 0 | `sobre` |
| `en-es:srs-source-target:figure:calcular:710b79be` | 2 | 0 | `calcular` |
| `en-es:srs-source-target:form:formulario:ab99a63f` | 2 | 0 | `formulario` |
| `en-es:srs-source-target:future:porvenir:ab93f50c` | 2 | 0 | `porvenir` |
| `en-es:srs-source-target:happen:acontecer:55a2e5bf` | 2 | 0 | `acontecer` |
| `en-es:srs-source-target:last:durar:d35f884c` | 2 | 0 | `durar` |
| `en-es:srs-source-target:manufacture:produccion:942e8aa5` | 2 | 0 | `producción` |
| `en-es:srs-source-target:metropolis:capital:f45bfe12` | 2 | 0 | `capital` |
| `en-es:srs-source-target:necessity:necesidad:9d1fad28` | 2 | 0 | `necesidad` |
| `en-es:srs-source-target:note:anotacion:a97dc3f7` | 2 | 0 | `anotación` |
| `en-es:srs-source-target:quite:enteramente:a472c713` | 2 | 0 | `enteramente` |
| `en-es:srs-source-target:round:redondo:220b4688` | 2 | 0 | `redondo` |
| `en-es:srs-source-target:single:soltero:566e52cf` | 2 | 0 | `soltero` |
| `en-es:srs-source-target:wolf:lobo:d67308cc` | 2 | 0 | `lobo` |
| `en-es:srs-source-target:yard:patio:62abba0d` | 2 | 0 | `patio` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
