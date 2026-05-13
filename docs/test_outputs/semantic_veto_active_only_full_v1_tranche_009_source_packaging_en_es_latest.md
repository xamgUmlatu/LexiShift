# en-es Semantic Veto Active-Only Source Packaging

- Status: `ok`
- Decision: `active_only_source_packaging_ready_for_inventory_compile`
- Generated: `2026-05-13T19:30:06Z`
- View: `no_high_eval_overlap_sentence_only`
- Intake batch: `en-es:semantic-veto:active-only-full-v1-tranche-009`
- Normalization: `semantic_evidence_v1`

## Summary

- Admitted input items: `76`
- Packaged evidence rows: `76`
- Excluded rows: `0`
- Family count: `38`
- Runtime publishable rows: `0`
- Relation types: `{'anchor_cue': 76}`
- Exclusion reasons: `{}`

## Provenance

- Prompt: `semantic_veto_evidence_gap_generation_v7_shadow_target_correctness`
- Model: `gpt-5.4-mini`
- Input/output tokens: `21009` / `7211`
- Source packaging mutates raw LLM output: `operator_repaired_after_generation`

## Family Rows

| Family | Packaged | Excluded | Targets |
| --- | ---: | ---: | --- |
| `en-es:srs-source-target:abatement:descuento:8ec99746` | 2 | 0 | `descuento` |
| `en-es:srs-source-target:acquaint:informar:48d3e377` | 2 | 0 | `informar` |
| `en-es:srs-source-target:barque:barco:5b3c803d` | 2 | 0 | `barco` |
| `en-es:srs-source-target:depository:deposito:0c2e4143` | 2 | 0 | `depósito` |
| `en-es:srs-source-target:glove:guante:898c0a5b` | 2 | 0 | `guante` |
| `en-es:srs-source-target:goose:ganso:6f61cd68` | 2 | 0 | `ganso` |
| `en-es:srs-source-target:idol:idolo:f73701e0` | 2 | 0 | `ídolo` |
| `en-es:srs-source-target:inflammation:inflamacion:642fc467` | 2 | 0 | `inflamación` |
| `en-es:srs-source-target:intoxicated:ebrio:9307c97f` | 2 | 0 | `ebrio` |
| `en-es:srs-source-target:jest:bromear:55d79731` | 2 | 0 | `bromear` |
| `en-es:srs-source-target:lick:lamer:ec658c72` | 2 | 0 | `lamer` |
| `en-es:srs-source-target:mayhap:quizas:f7426c37` | 2 | 0 | `quizás` |
| `en-es:srs-source-target:mist:niebla:b7b6f5af` | 2 | 0 | `niebla` |
| `en-es:srs-source-target:mosaic:mosaico:a3468e64` | 2 | 0 | `mosaico` |
| `en-es:srs-source-target:nameless:anonimo:c9e71255` | 2 | 0 | `anónimo` |
| `en-es:srs-source-target:offspring:descendiente:5e3ee01c` | 2 | 0 | `descendiente` |
| `en-es:srs-source-target:patriarch:patriarca:06c74e78` | 2 | 0 | `patriarca` |
| `en-es:srs-source-target:perchance:quizas:4ed5b37e` | 2 | 0 | `quizás` |
| `en-es:srs-source-target:phenomenal:fenomenal:856698e7` | 2 | 0 | `fenomenal` |
| `en-es:srs-source-target:pigeon:paloma:ac24415a` | 2 | 0 | `paloma` |
| `en-es:srs-source-target:protestant:protestante:d26b0ede` | 2 | 0 | `protestante` |
| `en-es:srs-source-target:relinquish:ceder:0ecd236b` | 2 | 0 | `ceder` |
| `en-es:srs-source-target:repose:descansar:42429a75` | 2 | 0 | `descansar` |
| `en-es:srs-source-target:restrain:reprimir:991f7bb9` | 2 | 0 | `reprimir` |
| `en-es:srs-source-target:romanian:rumano:8319ecf3` | 2 | 0 | `rumano` |
| `en-es:srs-source-target:satisfy:complacer:a006be45` | 2 | 0 | `complacer` |
| `en-es:srs-source-target:skirt:falda:f8e36e29` | 2 | 0 | `falda` |
| `en-es:srs-source-target:subscriber:abonado:aa293bd4` | 2 | 0 | `abonado` |
| `en-es:srs-source-target:swede:sueco:37f9f298` | 2 | 0 | `sueco` |
| `en-es:srs-source-target:terrace:terraza:443fe232` | 2 | 0 | `terraza` |
| `en-es:srs-source-target:unmarried:soltero:cf105107` | 2 | 0 | `soltero` |
| `en-es:srs-source-target:urine:orina:cab34771` | 2 | 0 | `orina` |
| `en-es:srs-source-target:viper:vibora:f4742aaa` | 2 | 0 | `víbora` |
| `en-es:srs-source-target:wasp:avispa:c4a7f83a` | 2 | 0 | `avispa` |
| `en-es:srs-source-target:wholly:enteramente:98f796f3` | 2 | 0 | `enteramente` |
| `en-es:srs-source-target:widower:viudo:48deec53` | 2 | 0 | `viudo` |
| `en-es:srs-source-target:willow:sauce:a4b9514b` | 2 | 0 | `sauce` |
| `en-es:srs-source-target:zinc:zinc:40042c08` | 2 | 0 | `zinc` |

## Runtime Boundary

- `normalized rows remain runtime_publishable=false`
- `this output is canonical source evidence, not a semantic inventory sidecar`
- `the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views`
- `runtime policy and thresholds remain unchanged`
