# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T01:27:30Z`
- Denominator source-target families: `570`
- Current active-only covered families: `178` (31.2%)
- Uncovered active-only families: `392`
- Runnable request packet families: `46`
- Runnable request packet expected items: `92`
- Runnable request packet estimated input tokens: `24061`
- Runnable request packet output-token budget: `12880`
- Source-target review: `approved:46, excluded:25, unreviewed:321`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 78 | 71.6% | 31 | `action` -> `batalla`, `ask` -> `demandar`, `back` -> `reverso`, `base` -> `basar`, `become` -> `acontecer`, `bed` -> `cauce` |
| `zipf_4_to_5_common` | 235 | 78 | 33.2% | 157 | `adjacent` -> `adyacente`, `adjacent` -> `contiguo`, `african` -> `africano`, `anonymous` -> `anónimo`, `australian` -> `australiano`, `baker` -> `panadero` |
| `zipf_3_to_4_mid` | 152 | 14 | 9.2% | 138 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 58 | 69.0% | 26 | `afar` -> `lejos`, `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `commencement` -> `principio`, `commonplace` -> `común` |
| `zipf_4_to_5_common` | 219 | 99 | 45.2% | 120 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 18 | 8.7% | 188 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 3 | 4.9% | 58 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 26136 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26263 | 14000 | P1_exposure_first:33, P2_exposure_first:17 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26234 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26292 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26430 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 26365 | 14000 | P2_exposure_first:48, P3_exposure_first:2 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 26523 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-008` | 17 | 17 | 34 | 9058 | 4760 | P3_exposure_first:17 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 22 | `P1_exposure_first` | `jack` | `gato` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 23 | `P1_exposure_first` | `japanese` | `japonés` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 24 | `P1_exposure_first` | `journalist` | `periodista` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 25 | `P1_exposure_first` | `judge` | `juzgar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 26 | `P1_exposure_first` | `knock` | `llamar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 27 | `P1_exposure_first` | `latin` | `latino` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 29 | `P1_exposure_first` | `lie` | `mentir` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 30 | `P1_exposure_first` | `load` | `cargar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 31 | `P1_exposure_first` | `male` | `masculino` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 32 | `P1_exposure_first` | `measure` | `medir` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 33 | `P1_exposure_first` | `mention` | `mencionar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 34 | `P1_exposure_first` | `musician` | `músico` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 35 | `P1_exposure_first` | `naked` | `desnudo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 36 | `P1_exposure_first` | `narrow` | `estrecho` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 37 | `P1_exposure_first` | `nasty` | `feo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 38 | `P1_exposure_first` | `nearby` | `vecino` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 39 | `P1_exposure_first` | `nude` | `desnudo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 40 | `P1_exposure_first` | `obligation` | `deber` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 41 | `P1_exposure_first` | `orange` | `naranja` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 42 | `P1_exposure_first` | `parallel` | `paralelo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 43 | `P1_exposure_first` | `portal` | `entrada` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 44 | `P1_exposure_first` | `presence` | `presencia` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 45 | `P1_exposure_first` | `protest` | `protesta` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 46 | `P1_exposure_first` | `quiet` | `silencio` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 48 | `P1_exposure_first` | `regulation` | `regla` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 49 | `P1_exposure_first` | `representative` | `diputado` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 50 | `P1_exposure_first` | `responsible` | `responsable` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 51 | `P1_exposure_first` | `restaurant` | `restaurante` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 52 | `P1_exposure_first` | `rule` | `regla` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 53 | `P1_exposure_first` | `shade` | `sombra` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 54 | `P1_exposure_first` | `shadow` | `sombra` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 56 | `P1_exposure_first` | `shout` | `grito` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 57 | `P1_exposure_first` | `silence` | `silencio` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 58 | `P1_exposure_first` | `skin` | `piel` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 59 | `P1_exposure_first` | `smile` | `sonrisa` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 61 | `P1_exposure_first` | `stick` | `palo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 62 | `P1_exposure_first` | `stomach` | `estómago` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 63 | `P1_exposure_first` | `sweet` | `dulce` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 64 | `P1_exposure_first` | `taste` | `gusto` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 65 | `P1_exposure_first` | `tea` | `té` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 66 | `P1_exposure_first` | `theatre` | `teatro` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 67 | `P1_exposure_first` | `theft` | `robo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 68 | `P1_exposure_first` | `throat` | `garganta` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 69 | `P1_exposure_first` | `train` | `tren` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 70 | `P1_exposure_first` | `ugly` | `feo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 71 | `P1_exposure_first` | `weak` | `débil` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_004_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-004-approved \
  --max-requests 46 \
  --require-selected-request-count 46 \
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
