# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-11T22:27:26Z`
- Denominator source-target families: `570`
- Current active-only covered families: `49` (8.6%)
- Uncovered active-only families: `521`
- Runnable request packet families: `42`
- Runnable request packet expected items: `84`
- Runnable request packet estimated input tokens: `21898`
- Runnable request packet output-token budget: `11760`
- Source-target review: `approved:42, excluded:8, unreviewed:471`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 16 | 14.7% | 93 | `access` -> `entrada`, `action` -> `batalla`, `ask` -> `demandar`, `ask` -> `preguntar`, `away` -> `lejos`, `back` -> `reverso` |
| `zipf_4_to_5_common` | 235 | 11 | 4.7% | 224 | `absence` -> `falta`, `academy` -> `academia`, `adjacent` -> `adyacente`, `adjacent` -> `contiguo`, `adjacent` -> `vecino`, `african` -> `africano` |
| `zipf_3_to_4_mid` | 152 | 14 | 9.2% | 138 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 10 | 11.9% | 74 | `absence` -> `falta`, `afar` -> `lejos`, `afternoon` -> `tarde`, `author` -> `autor`, `away` -> `lejos`, `background` -> `fondo` |
| `zipf_4_to_5_common` | 219 | 18 | 8.2% | 201 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `academy` -> `academia`, `access` -> `entrada`, `accountable` -> `responsable` |
| `zipf_3_to_4_mid` | 206 | 18 | 8.7% | 188 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 3 | 4.9% | 58 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 26088 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26112 | 14000 | P0_exposure_first:36, P1_exposure_first:14 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26288 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26171 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26342 | 14000 | P1_exposure_first:29, P2_exposure_first:21 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 26307 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 26332 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-008` | 50 | 50 | 100 | 26460 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-009` | 50 | 50 | 100 | 26413 | 14000 | P2_exposure_first:44, P3_exposure_first:6 |
| `en-es-active-only-full-v1-tranche-010` | 50 | 50 | 100 | 26598 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-011` | 13 | 13 | 26 | 6949 | 3640 | P3_exposure_first:13 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 1 | `P0_exposure_first` | `away` | `lejos` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 2 | `P0_exposure_first` | `beginning` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 3 | `P0_exposure_first` | `between` | `entre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 5 | `P0_exposure_first` | `century` | `siglo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 6 | `P0_exposure_first` | `chief` | `jefe` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 8 | `P0_exposure_first` | `even` | `par` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 9 | `P0_exposure_first` | `far` | `lejos` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 10 | `P0_exposure_first` | `hour` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 11 | `P0_exposure_first` | `inside` | `dentro` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 12 | `P0_exposure_first` | `just` | `sólo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 13 | `P0_exposure_first` | `light` | `luz` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 14 | `P0_exposure_first` | `little` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 15 | `P0_exposure_first` | `making` | `producción` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 16 | `P0_exposure_first` | `more` | `más` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 17 | `P0_exposure_first` | `morning` | `mañana` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 18 | `P0_exposure_first` | `music` | `música` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 19 | `P0_exposure_first` | `national` | `nacional` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 20 | `P0_exposure_first` | `need` | `necesidad` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 21 | `P0_exposure_first` | `now` | `actualmente` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 22 | `P0_exposure_first` | `official` | `oficial` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 23 | `P0_exposure_first` | `only` | `sólo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 24 | `P0_exposure_first` | `read` | `leer` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 25 | `P0_exposure_first` | `room` | `espacio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 26 | `P0_exposure_first` | `section` | `departamento` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 27 | `P0_exposure_first` | `small` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 28 | `P0_exposure_first` | `space` | `espacio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 29 | `P0_exposure_first` | `stand` | `puesto` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 31 | `P0_exposure_first` | `start` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 32 | `P0_exposure_first` | `time` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 34 | `P0_exposure_first` | `work` | `trabajar` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 35 | `P0_exposure_first` | `access` | `entrada` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 37 | `P0_exposure_first` | `ask` | `preguntar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 38 | `P0_exposure_first` | `break` | `romper` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 39 | `P0_exposure_first` | `car` | `automóvil` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 41 | `P0_exposure_first` | `close` | `estrecho` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 42 | `P0_exposure_first` | `court` | `patio` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 43 | `P0_exposure_first` | `cup` | `taza` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 44 | `P0_exposure_first` | `double` | `doble` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 45 | `P0_exposure_first` | `eight` | `ocho` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 46 | `P0_exposure_first` | `exactly` | `justamente` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 47 | `P0_exposure_first` | `face` | `rostro` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 49 | `P0_exposure_first` | `ice` | `hielo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-001-approved \
  --max-requests 42 \
  --require-selected-request-count 42 \
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
