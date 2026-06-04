# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T17:51:25Z`
- Denominator source-target families: `570`
- Current active-only covered families: `300` (52.6%)
- Uncovered active-only families: `270`
- Runnable request packet families: `38`
- Runnable request packet expected items: `76`
- Runnable request packet estimated input tokens: `20811`
- Runnable request packet output-token budget: `10640`
- Source-target review: `approved:38, excluded:61, unreviewed:171`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 175 | 74.5% | 60 | `adjacent` -> `contiguo`, `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio` |
| `zipf_3_to_4_mid` | 152 | 22 | 14.5% | 130 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 147 | 67.1% | 72 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 82 | 39.8% | 124 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 5 | 8.2% | 56 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27144 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26405 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26363 | 14000 | P2_exposure_first:40, P3_exposure_first:10 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26566 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 9 | 9 | 18 | 4807 | 2520 | P3_exposure_first:9 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 51 | `P2_exposure_first` | `sentence` | `condenar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 52 | `P2_exposure_first` | `separate` | `apartar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 53 | `P2_exposure_first` | `ski` | `esquí` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 54 | `P2_exposure_first` | `stable` | `cuadra` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 55 | `P2_exposure_first` | `storm` | `tempestad` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 57 | `P2_exposure_first` | `supplement` | `suplemento` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 58 | `P2_exposure_first` | `swedish` | `sueco` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 60 | `P2_exposure_first` | `transport` | `transportar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 61 | `P2_exposure_first` | `yield` | `ceder` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 62 | `P2_exposure_first` | `abiding` | `continuo` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 64 | `P2_exposure_first` | `accountable` | `responsable` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 65 | `P2_exposure_first` | `argentine` | `argentino` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 66 | `P2_exposure_first` | `axle` | `eje` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 68 | `P2_exposure_first` | `baton` | `palo` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 69 | `P2_exposure_first` | `cane` | `palo` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 71 | `P2_exposure_first` | `colleague` | `colega` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 72 | `P2_exposure_first` | `commence` | `comenzar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 73 | `P2_exposure_first` | `continual` | `continuo` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 74 | `P2_exposure_first` | `courtyard` | `patio` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 75 | `P2_exposure_first` | `cramped` | `estrecho` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 77 | `P2_exposure_first` | `dial` | `marcar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 78 | `P2_exposure_first` | `elegant` | `elegante` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 79 | `P2_exposure_first` | `exploit` | `explotar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 80 | `P2_exposure_first` | `faint` | `débil` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 81 | `P2_exposure_first` | `grease` | `grasa` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 82 | `P2_exposure_first` | `haste` | `prisa` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 83 | `P2_exposure_first` | `invoke` | `llamar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 85 | `P2_exposure_first` | `lump` | `bola` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 86 | `P2_exposure_first` | `nationality` | `nacionalidad` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 88 | `P2_exposure_first` | `supper` | `cena` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 89 | `P2_exposure_first` | `tasty` | `rico` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 90 | `P2_exposure_first` | `thief` | `ladrón` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_direct_mapping` |
| 91 | `P2_exposure_first` | `tidy` | `arreglar` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 92 | `P2_exposure_first` | `urgency` | `prisa` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 0.5935 | `approve_narrow_active_mapping` |
| 95 | `P2_exposure_first` | `adjacent` | `contiguo` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 96 | `P2_exposure_first` | `cap` | `birrete` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_narrow_active_mapping` |
| 97 | `P2_exposure_first` | `command` | `capitanear` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_narrow_active_mapping` |
| 98 | `P2_exposure_first` | `decrease` | `decrecer` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_007_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-007-approved \
  --max-requests 38 \
  --require-selected-request-count 38 \
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
