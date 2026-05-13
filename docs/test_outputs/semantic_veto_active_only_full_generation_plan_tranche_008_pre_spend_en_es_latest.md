# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T18:28:27Z`
- Denominator source-target families: `570`
- Current active-only covered families: `338` (59.3%)
- Uncovered active-only families: `232`
- Runnable request packet families: `40`
- Runnable request packet expected items: `80`
- Runnable request packet estimated input tokens: `21892`
- Runnable request packet output-token budget: `11200`
- Source-target review: `approved:40, excluded:71, unreviewed:121`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 188 | 80.0% | 47 | `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio`, `chase` -> `cazar` |
| `zipf_3_to_4_mid` | 152 | 47 | 30.9% | 105 | `abandonment` -> `cesión`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar`, `acquaintance` -> `notoriedad` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 172 | 78.5% | 47 | `abatement` -> `descuento`, `abstraction` -> `robo`, `acquaint` -> `informar`, `action` -> `batalla`, `affable` -> `gracioso`, `alternation` -> `alternativa` |
| `zipf_3_to_4_mid` | 206 | 91 | 44.2% | 115 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 9 | 14.8% | 52 | `abate` -> `decrecer`, `aberration` -> `yerro`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer`, `begrudge` -> `deplorar` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27129 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26388 | 14000 | P2_exposure_first:42, P3_exposure_first:8 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26561 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 11 | 11 | 22 | 5860 | 3080 | P3_exposure_first:11 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 62 | `P2_exposure_first` | `error` | `yerro` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 65 | `P2_exposure_first` | `lighter` | `mechero` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 66 | `P2_exposure_first` | `mistake` | `yerro` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 68 | `P2_exposure_first` | `regret` | `deplorar` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 69 | `P2_exposure_first` | `scale` | `incrustación` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_narrow_active_mapping` |
| 70 | `P2_exposure_first` | `separate` | `segregar` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_narrow_active_mapping` |
| 71 | `P2_exposure_first` | `severe` | `inclemente` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_narrow_active_mapping` |
| 73 | `P2_exposure_first` | `sweat` | `transpirar` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 0.5785 | `approve_direct_mapping` |
| 77 | `P2_exposure_first` | `abolish` | `abolir` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 78 | `P2_exposure_first` | `accompaniment` | `acompañamiento` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 79 | `P2_exposure_first` | `accuse` | `acusar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 81 | `P2_exposure_first` | `adjective` | `adjetivo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 82 | `P2_exposure_first` | `adjoining` | `adyacente` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 83 | `P2_exposure_first` | `ankle` | `tobillo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 84 | `P2_exposure_first` | `appease` | `calmar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 85 | `P2_exposure_first` | `asphalt` | `asfalto` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 86 | `P2_exposure_first` | `ballet` | `ballet` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 87 | `P2_exposure_first` | `barbarian` | `bárbaro` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 88 | `P2_exposure_first` | `beggar` | `mendigo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 89 | `P2_exposure_first` | `bore` | `aburrir` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 90 | `P2_exposure_first` | `bracelet` | `pulsera` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 92 | `P2_exposure_first` | `butterfly` | `mariposa` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 93 | `P2_exposure_first` | `calculate` | `calcular` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 94 | `P2_exposure_first` | `capsule` | `cápsula` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 95 | `P2_exposure_first` | `chemist` | `farmacéutico` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 96 | `P2_exposure_first` | `citadel` | `ciudadela` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 97 | `P2_exposure_first` | `claw` | `garra` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 98 | `P2_exposure_first` | `cockroach` | `cucaracha` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 99 | `P2_exposure_first` | `cocoa` | `cacao` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 100 | `P2_exposure_first` | `condemn` | `condenar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 101 | `P2_exposure_first` | `cylinder` | `cilindro` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 102 | `P2_exposure_first` | `delegate` | `delegar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 103 | `P2_exposure_first` | `denounce` | `acusar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 104 | `P2_exposure_first` | `detain` | `retener` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 105 | `P2_exposure_first` | `distract` | `distraer` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 106 | `P2_exposure_first` | `divert` | `distraer` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 107 | `P2_exposure_first` | `entertain` | `distraer` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 108 | `P2_exposure_first` | `exaggerate` | `exagerar` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 110 | `P2_exposure_first` | `feather` | `pluma` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 111 | `P2_exposure_first` | `fog` | `niebla` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_008_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-008-approved \
  --max-requests 40 \
  --require-selected-request-count 40 \
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
