# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T05:04:13Z`
- Denominator source-target families: `570`
- Current active-only covered families: `224` (39.3%)
- Uncovered active-only families: `346`
- Runnable request packet families: `37`
- Runnable request packet expected items: `74`
- Runnable request packet estimated input tokens: `20540`
- Runnable request packet output-token budget: `10360`
- Source-target review: `approved:37, excluded:38, unreviewed:271`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 78 | 71.6% | 31 | `action` -> `batalla`, `ask` -> `demandar`, `back` -> `reverso`, `base` -> `basar`, `become` -> `acontecer`, `bed` -> `cauce` |
| `zipf_4_to_5_common` | 235 | 124 | 52.8% | 111 | `adjacent` -> `adyacente`, `adjacent` -> `contiguo`, `african` -> `africano`, `anonymous` -> `anónimo`, `australian` -> `australiano`, `baker` -> `panadero` |
| `zipf_3_to_4_mid` | 152 | 14 | 9.2% | 138 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 58 | 69.0% | 26 | `afar` -> `lejos`, `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `commencement` -> `principio`, `commonplace` -> `común` |
| `zipf_4_to_5_common` | 219 | 145 | 66.2% | 74 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 18 | 8.7% | 188 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 3 | 4.9% | 58 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27317 | 14000 | P1_exposure_first:27, P2_exposure_first:23 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26293 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26282 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26424 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 26351 | 14000 | P2_exposure_first:39, P3_exposure_first:11 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 26580 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 8 | 8 | 16 | 4269 | 2240 | P3_exposure_first:8 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 26 | `P1_exposure_first` | `wolf` | `lobo` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_direct_mapping` |
| 28 | `P1_exposure_first` | `yard` | `patio` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 0.8160 | `approve_narrow_active_mapping` |
| 30 | `P1_exposure_first` | `back` | `reverso` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 31 | `P1_exposure_first` | `base` | `basar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 32 | `P1_exposure_first` | `bed` | `cauce` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 33 | `P1_exposure_first` | `book` | `reservar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 34 | `P1_exposure_first` | `check` | `reprimir` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 35 | `P1_exposure_first` | `cross` | `atravesar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 36 | `P1_exposure_first` | `drive` | `propulsión` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 37 | `P1_exposure_first` | `figure` | `calcular` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 38 | `P1_exposure_first` | `form` | `formulario` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 39 | `P1_exposure_first` | `future` | `porvenir` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 40 | `P1_exposure_first` | `last` | `durar` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 41 | `P1_exposure_first` | `note` | `anotación` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 43 | `P1_exposure_first` | `quite` | `enteramente` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_narrow_active_mapping` |
| 44 | `P1_exposure_first` | `round` | `redondo` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 46 | `P1_exposure_first` | `single` | `soltero` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 0.7625 | `approve_polysemic_active_mapping` |
| 48 | `P1_exposure_first` | `cover` | `forrar` | `zipf_5_plus_very_common` | `zipf_below_3_rare` | 0.6925 | `approve_narrow_active_mapping` |
| 50 | `P1_exposure_first` | `happen` | `acontecer` | `zipf_5_plus_very_common` | `zipf_below_3_rare` | 0.6925 | `approve_direct_mapping` |
| 51 | `P1_exposure_first` | `afar` | `lejos` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_direct_mapping` |
| 54 | `P1_exposure_first` | `commencement` | `principio` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_narrow_active_mapping` |
| 55 | `P1_exposure_first` | `commonplace` | `común` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_narrow_active_mapping` |
| 57 | `P1_exposure_first` | `diminutive` | `pequeño` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_narrow_active_mapping` |
| 59 | `P1_exposure_first` | `envelope` | `sobre` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_direct_mapping` |
| 60 | `P1_exposure_first` | `manufacture` | `producción` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_narrow_active_mapping` |
| 61 | `P1_exposure_first` | `metropolis` | `capital` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_narrow_active_mapping` |
| 62 | `P1_exposure_first` | `necessity` | `necesidad` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 0.6635 | `approve_direct_mapping` |
| 63 | `P2_exposure_first` | `adjacent` | `adyacente` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 64 | `P2_exposure_first` | `african` | `africano` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 65 | `P2_exposure_first` | `anonymous` | `anónimo` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 66 | `P2_exposure_first` | `australian` | `australiano` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 67 | `P2_exposure_first` | `baker` | `panadero` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 68 | `P2_exposure_first` | `bar` | `taberna` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |
| 69 | `P2_exposure_first` | `basket` | `cesto` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 70 | `P2_exposure_first` | `bee` | `abeja` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_direct_mapping` |
| 74 | `P2_exposure_first` | `blow` | `soplar` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_polysemic_active_mapping` |
| 75 | `P2_exposure_first` | `brush` | `cepillo` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 0.6485 | `approve_narrow_active_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_005_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-005-approved \
  --max-requests 37 \
  --require-selected-request-count 37 \
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
