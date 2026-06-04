# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T17:30:18Z`
- Denominator source-target families: `570`
- Current active-only covered families: `261` (45.8%)
- Uncovered active-only families: `309`
- Runnable request packet families: `39`
- Runnable request packet expected items: `78`
- Runnable request packet estimated input tokens: `21302`
- Runnable request packet output-token budget: `10920`
- Source-target review: `approved:39, excluded:49, unreviewed:221`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 136 | 57.9% | 99 | `adjacent` -> `contiguo`, `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `calmar` |
| `zipf_3_to_4_mid` | 152 | 22 | 14.5% | 130 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 147 | 67.1% | 72 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 43 | 20.9% | 163 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 5 | 8.2% | 56 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27115 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26281 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26391 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26383 | 14000 | P2_exposure_first:41, P3_exposure_first:9 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26568 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 10 | 10 | 20 | 5329 | 2800 | P3_exposure_first:10 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 40 | `P2_exposure_first` | `calm` | `calmar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 42 | `P2_exposure_first` | `clay` | `arcilla` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 43 | `P2_exposure_first` | `climb` | `trepar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 46 | `P2_exposure_first` | `counter` | `mostrador` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 47 | `P2_exposure_first` | `crack` | `grieta` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 49 | `P2_exposure_first` | `divide` | `apartar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 50 | `P2_exposure_first` | `drunk` | `ebrio` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 51 | `P2_exposure_first` | `ear` | `oreja` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 52 | `P2_exposure_first` | `eighth` | `octavo` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 53 | `P2_exposure_first` | `error` | `equivocación` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 55 | `P2_exposure_first` | `extract` | `extracto` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 56 | `P2_exposure_first` | `farmer` | `campesino` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 57 | `P2_exposure_first` | `feed` | `alimentar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 58 | `P2_exposure_first` | `fly` | `mosca` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 59 | `P2_exposure_first` | `guest` | `huésped` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 60 | `P2_exposure_first` | `heat` | `calentar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 61 | `P2_exposure_first` | `height` | `elevación` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 62 | `P2_exposure_first` | `hip` | `cadera` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 63 | `P2_exposure_first` | `honest` | `honrado` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 64 | `P2_exposure_first` | `hunt` | `cazar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 66 | `P2_exposure_first` | `joke` | `bromear` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 67 | `P2_exposure_first` | `kick` | `patada` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 68 | `P2_exposure_first` | `kiss` | `besar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 69 | `P2_exposure_first` | `lamb` | `cordero` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 70 | `P2_exposure_first` | `mistake` | `equivocación` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 72 | `P2_exposure_first` | `pepper` | `pimienta` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 73 | `P2_exposure_first` | `petty` | `mezquino` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 74 | `P2_exposure_first` | `pink` | `rosado` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 75 | `P2_exposure_first` | `plain` | `llanura` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 76 | `P2_exposure_first` | `plane` | `cepillo` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 77 | `P2_exposure_first` | `pleasure` | `agrado` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 78 | `P2_exposure_first` | `prefer` | `preferir` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 80 | `P2_exposure_first` | `quiet` | `calmar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 81 | `P2_exposure_first` | `refuse` | `rechazar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 82 | `P2_exposure_first` | `reject` | `rechazar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 85 | `P2_exposure_first` | `reserve` | `reservar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 86 | `P2_exposure_first` | `retain` | `retener` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 87 | `P2_exposure_first` | `reverse` | `reverso` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 88 | `P2_exposure_first` | `salad` | `ensalada` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_006_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-006-approved \
  --max-requests 39 \
  --require-selected-request-count 39 \
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
