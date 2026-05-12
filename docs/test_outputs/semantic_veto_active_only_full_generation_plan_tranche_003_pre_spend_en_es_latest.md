# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-12T02:29:32Z`
- Denominator source-target families: `570`
- Current active-only covered families: `135` (23.7%)
- Uncovered active-only families: `435`
- Runnable request packet families: `43`
- Runnable request packet expected items: `86`
- Runnable request packet estimated input tokens: `22570`
- Runnable request packet output-token budget: `12040`
- Source-target review: `approved:43, excluded:21, unreviewed:371`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 78 | 71.6% | 31 | `action` -> `batalla`, `ask` -> `demandar`, `back` -> `reverso`, `base` -> `basar`, `become` -> `acontecer`, `bed` -> `cauce` |
| `zipf_4_to_5_common` | 235 | 35 | 14.9% | 200 | `adjacent` -> `adyacente`, `adjacent` -> `contiguo`, `african` -> `africano`, `anonymous` -> `anónimo`, `australian` -> `australiano`, `baker` -> `panadero` |
| `zipf_3_to_4_mid` | 152 | 14 | 9.2% | 138 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 58 | 69.0% | 26 | `afar` -> `lejos`, `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `commencement` -> `principio`, `commonplace` -> `común` |
| `zipf_4_to_5_common` | 219 | 56 | 25.6% | 163 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 18 | 8.7% | 188 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 3 | 4.9% | 58 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 26226 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26113 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26285 | 14000 | P1_exposure_first:30, P2_exposure_first:20 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26243 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26290 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 26435 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 26356 | 14000 | P2_exposure_first:45, P3_exposure_first:5 |
| `en-es-active-only-full-v1-tranche-008` | 50 | 50 | 100 | 26542 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-009` | 14 | 14 | 28 | 7467 | 3920 | P3_exposure_first:14 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 15 | `P1_exposure_first` | `bird` | `ave` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 16 | `P1_exposure_first` | `blind` | `ciego` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 17 | `P1_exposure_first` | `boat` | `barco` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 18 | `P1_exposure_first` | `boss` | `amo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 19 | `P1_exposure_first` | `brazilian` | `brasileño` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 20 | `P1_exposure_first` | `burden` | `cargar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 21 | `P1_exposure_first` | `burn` | `quemar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 23 | `P1_exposure_first` | `castle` | `castillo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 24 | `P1_exposure_first` | `cat` | `gato` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 25 | `P1_exposure_first` | `chair` | `silla` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 26 | `P1_exposure_first` | `communist` | `comunista` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 27 | `P1_exposure_first` | `competition` | `competencia` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 28 | `P1_exposure_first` | `constant` | `continuo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 29 | `P1_exposure_first` | `corruption` | `corrupción` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 30 | `P1_exposure_first` | `cousin` | `primo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 31 | `P1_exposure_first` | `cry` | `grito` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 33 | `P1_exposure_first` | `debt` | `deuda` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 34 | `P1_exposure_first` | `defeat` | `derrota` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 35 | `P1_exposure_first` | `deputy` | `diputado` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 36 | `P1_exposure_first` | `determine` | `determinar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 37 | `P1_exposure_first` | `diameter` | `diámetro` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 38 | `P1_exposure_first` | `dictionary` | `diccionario` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 39 | `P1_exposure_first` | `dinner` | `cena` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 40 | `P1_exposure_first` | `discount` | `descuento` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 41 | `P1_exposure_first` | `distance` | `distancia` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 42 | `P1_exposure_first` | `dual` | `doble` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 43 | `P1_exposure_first` | `duty` | `deber` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 44 | `P1_exposure_first` | `earthquake` | `terremoto` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 45 | `P1_exposure_first` | `entrance` | `entrada` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 46 | `P1_exposure_first` | `experienced` | `experto` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 47 | `P1_exposure_first` | `expert` | `experto` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 48 | `P1_exposure_first` | `faithful` | `fiel` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 49 | `P1_exposure_first` | `famous` | `famoso` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 50 | `P1_exposure_first` | `fat` | `grasa` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 51 | `P1_exposure_first` | `fix` | `determinar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 52 | `P1_exposure_first` | `flow` | `correr` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 57 | `P1_exposure_first` | `guilty` | `culpable` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 58 | `P1_exposure_first` | `height` | `altura` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 59 | `P1_exposure_first` | `hide` | `piel` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_polysemic_active_mapping` |
| 60 | `P1_exposure_first` | `horizon` | `horizonte` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 62 | `P1_exposure_first` | `impossible` | `imposible` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 63 | `P1_exposure_first` | `indicate` | `mostrar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 64 | `P1_exposure_first` | `inform` | `informar` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_003_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-003-approved \
  --max-requests 43 \
  --require-selected-request-count 43 \
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
