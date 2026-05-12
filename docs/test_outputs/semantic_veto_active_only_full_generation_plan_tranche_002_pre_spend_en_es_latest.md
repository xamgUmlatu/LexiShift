# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-11T23:26:02Z`
- Denominator source-target families: `570`
- Current active-only covered families: `91` (16.0%)
- Uncovered active-only families: `479`
- Runnable request packet families: `44`
- Runnable request packet expected items: `88`
- Runnable request packet estimated input tokens: `23006`
- Runnable request packet output-token budget: `12320`
- Source-target review: `approved:44, excluded:14, unreviewed:421`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 58 | 53.2% | 51 | `action` -> `batalla`, `ask` -> `demandar`, `back` -> `reverso`, `base` -> `basar`, `become` -> `acontecer`, `bed` -> `cauce` |
| `zipf_4_to_5_common` | 235 | 11 | 4.7% | 224 | `absence` -> `falta`, `academy` -> `academia`, `adjacent` -> `adyacente`, `adjacent` -> `contiguo`, `adjacent` -> `vecino`, `african` -> `africano` |
| `zipf_3_to_4_mid` | 152 | 14 | 9.2% | 138 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 40 | 47.6% | 44 | `absence` -> `falta`, `afar` -> `lejos`, `afternoon` -> `tarde`, `author` -> `autor`, `background` -> `fondo`, `barn` -> `puesto` |
| `zipf_4_to_5_common` | 219 | 30 | 13.7% | 189 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `academy` -> `academia`, `accountable` -> `responsable`, `acquaint` -> `informar` |
| `zipf_3_to_4_mid` | 206 | 18 | 8.7% | 188 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 3 | 4.9% | 58 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 26122 | 14000 | P0_exposure_first:38, P1_exposure_first:12 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26298 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26165 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26321 | 14000 | P1_exposure_first:31, P2_exposure_first:19 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26293 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 26340 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 26487 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-008` | 50 | 50 | 100 | 26407 | 14000 | P2_exposure_first:46, P3_exposure_first:4 |
| `en-es-active-only-full-v1-tranche-009` | 50 | 50 | 100 | 26586 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-010` | 15 | 15 | 30 | 8004 | 4200 | P3_exposure_first:15 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 9 | `P0_exposure_first` | `light` | `débil` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 10 | `P0_exposure_first` | `maybe` | `quizás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 11 | `P0_exposure_first` | `million` | `millón` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 12 | `P0_exposure_first` | `never` | `jamás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 13 | `P0_exposure_first` | `nice` | `rico` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 14 | `P0_exposure_first` | `officer` | `funcionario` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 15 | `P0_exposure_first` | `official` | `funcionario` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 16 | `P0_exposure_first` | `old` | `anciano` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 17 | `P0_exposure_first` | `present` | `contemporáneo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 18 | `P0_exposure_first` | `race` | `correr` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 19 | `P0_exposure_first` | `red` | `rojo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 20 | `P0_exposure_first` | `report` | `informar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 21 | `P0_exposure_first` | `rest` | `descansar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 22 | `P0_exposure_first` | `run` | `correr` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 23 | `P0_exposure_first` | `show` | `mostrar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 25 | `P0_exposure_first` | `start` | `comenzar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 26 | `P0_exposure_first` | `tax` | `imponer` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 27 | `P0_exposure_first` | `visit` | `visita` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 28 | `P0_exposure_first` | `west` | `oeste` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 29 | `P0_exposure_first` | `wife` | `esposa` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 30 | `P0_exposure_first` | `absence` | `falta` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 31 | `P0_exposure_first` | `afternoon` | `tarde` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 32 | `P0_exposure_first` | `author` | `autor` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 33 | `P0_exposure_first` | `background` | `fondo` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_polysemic_active_mapping` |
| 34 | `P0_exposure_first` | `boss` | `jefe` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 38 | `P0_exposure_first` | `exclusively` | `sólo` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 40 | `P0_exposure_first` | `favour` | `favor` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 41 | `P0_exposure_first` | `lack` | `falta` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_polysemic_active_mapping` |
| 42 | `P0_exposure_first` | `lay` | `poner` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_polysemic_active_mapping` |
| 43 | `P0_exposure_first` | `leader` | `jefe` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 44 | `P0_exposure_first` | `majority` | `mayoría` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 45 | `P0_exposure_first` | `manager` | `director` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_narrow_active_mapping` |
| 46 | `P0_exposure_first` | `politician` | `político` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 47 | `P0_exposure_first` | `republic` | `república` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 49 | `P0_exposure_first` | `sun` | `sol` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 50 | `P0_exposure_first` | `thousand` | `mil` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 51 | `P0_exposure_first` | `writer` | `autor` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 52 | `P0_exposure_first` | `yesterday` | `ayer` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 53 | `P1_exposure_first` | `academy` | `academia` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 54 | `P1_exposure_first` | `adjacent` | `vecino` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 55 | `P1_exposure_first` | `arrange` | `arreglar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 56 | `P1_exposure_first` | `axis` | `eje` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 57 | `P1_exposure_first` | `bare` | `desnudo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 58 | `P1_exposure_first` | `battle` | `batalla` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_002_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-002-approved \
  --max-requests 44 \
  --require-selected-request-count 44 \
  --expected-output-tokens 280 \
  --input-rate-per-1m <current-input-rate> \
  --output-rate-per-1m <current-output-rate> \
  --max-estimated-cost-usd <small-tranche-budget> \
  --max-estimated-cost-ceiling-usd <small-tranche-ceiling> \
  --execute-live --resume
```

## Guardrails

| Check | Value |
| --- | --- |
| `denominator_present` | `True` |
| `selected_rows_do_not_overlap_existing_coverage` | `True` |
| `request_ids_unique` | `True` |
| `request_family_ids_unique` | `True` |
| `all_requests_active_only` | `True` |
| `all_requests_have_prompt_text` | `True` |
| `all_requests_have_target` | `True` |
| `selected_rows_review_approved_or_review_inactive` | `True` |

## Limitations

- `full denominator is current installed SRS rulegen output, not all possible en-es words`
- `active-only rows do not add repaired shadows or phrase/no-winner controls`
- `Zipf ordering is an exposure queue, not proof of veto difficulty`
- `source-target-only rows have weaker sense hints than manually reviewed families`
- `manual pre-spend source-target review covers only rows present in the review manifest`
- `live generation must be run in small resumable tranches with explicit spend guards`

## Next Steps

- Run the first request tranche only, with --max-requests and --require-selected-request-count matching the selected request count.
- Run postprocess, admission, source packaging, inventory replay, helper smoke, and live-page scan on that tranche before continuing.
- Append admitted rows to the product-smoke active-only pack only after replay shows the same soft-assist behavior.
- Generate shadows only for high-need or observed-harm families after active-only coverage has been measured.
